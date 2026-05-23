import re
import json
from typing import AsyncGenerator, Dict, Any, Tuple, Optional

from app.core.llm_client import llm_client
from app.agents.lin_daiyu.prompts import load_system_prompt
from app.agents.lin_daiyu.memory import memory
from app.agents.tools.registry import registry

# 触发工具注册
import app.agents.tools  # noqa: F401


def _parse_action(text: str) -> Tuple[Optional[str], Optional[Dict]]:
    """从 ReAct 文本中解析 Action 和 Action Input"""
    # Action: xxx
    action_match = re.search(r'Action:\s*(\w+)', text)
    if not action_match:
        return None, None
    tool_name = action_match.group(1).strip()

    # Action Input: {...} 或 Action Input: xxx
    input_match = re.search(r'Action Input:\s*(\{.*?\})', text, re.DOTALL)
    if input_match:
        try:
            args = json.loads(input_match.group(1))
            return tool_name, args
        except json.JSONDecodeError:
            pass

    # 兜底：匹配单行文本
    input_match2 = re.search(r'Action Input:\s*(.*?)(?:\n|$)', text)
    if input_match2:
        arg_str = input_match2.group(1).strip()
        if arg_str:
            try:
                args = json.loads(arg_str)
                return tool_name, args
            except json.JSONDecodeError:
                return tool_name, {"query": arg_str}

    return tool_name, {}


def _extract_thought(text: str) -> str:
    """提取 Thought 内容"""
    # 匹配最后一个 Thought:（通常在 Action 之前）
    thoughts = re.findall(r'Thought:\s*(.*?)(?:\nAction:|$)', text, re.DOTALL)
    if thoughts:
        return thoughts[-1].strip()
    return ""


def _extract_final_answer(text: str) -> str:
    """提取 Final Answer 内容"""
    match = re.search(r'Final Answer:\s*(.*)', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


async def chat(session_id: str, user_message: str) -> AsyncGenerator[Dict[str, Any], None]:
    """林黛玉 Agent 主循环（手动 ReAct）
    
    流程：
    1. 检查/创建 Session
    2. 非流式调用 LLM，获取完整文本
    3. 解析是否包含 Action → 执行工具 → 加入 Observation
    4. 再次调用 LLM（流式）输出 Final Answer
    5. 如不需工具，直接输出
    """

    # 1. Session 管理
    if not session_id or not memory.has_session(session_id):
        session_id = memory.create_session()

    # 2. 保存用户消息
    memory.add_message(session_id, "user", user_message)

    system_prompt = load_system_prompt()
    MAX_ITERATIONS = 3

    for iteration in range(MAX_ITERATIONS):
        history = memory.get_history(session_id)
        messages = [{"role": "system", "content": system_prompt}] + history

        # 3. 非流式调用 LLM（需要完整文本来解析 Action）
        response_text = await llm_client.chat_complete(messages)

        if response_text.startswith("[LLM 调用出错"):
            yield {"event": "error", "data": {"message": response_text}}
            return

        # 4. 解析 Action
        tool_name, tool_args = _parse_action(response_text)

        if tool_name:
            # 需要调用工具
            thought = _extract_thought(response_text)
            if thought:
                yield {"event": "thinking", "data": {"content": thought}}

            yield {"event": "tool_call", "data": {"name": tool_name, "arguments": json.dumps(tool_args, ensure_ascii=False)}}

            # 执行工具
            try:
                result = await registry.execute(tool_name, json.dumps(tool_args, ensure_ascii=False))
            except Exception as e:
                result = f"工具执行出错: {e}"

            yield {"event": "tool_result", "data": {"name": tool_name, "result": result}}

            # 加入历史：assistant 的思考 + tool 结果
            memory.add_message(session_id, "assistant", response_text)
            memory.add_message(session_id, "user", f"Observation: {result}")

            # 继续下一轮循环
            continue

        else:
            # 5. 不需要工具，直接输出最终回答
            final_answer = _extract_final_answer(response_text)
            if not final_answer:
                final_answer = response_text.strip()

            # 流式输出 Final Answer（模拟打字机效果）
            chunk_size = 4
            for i in range(0, len(final_answer), chunk_size):
                chunk = final_answer[i:i + chunk_size]
                yield {"event": "message", "data": {"content": chunk}}

            memory.add_message(session_id, "assistant", final_answer)
            yield {"event": "done", "data": {"session_id": session_id}}
            return

    # 超过最大迭代次数
    yield {"event": "error", "data": {"message": "工具调用次数过多，请简化问题"}}
