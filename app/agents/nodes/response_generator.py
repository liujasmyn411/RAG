"""LLM 生成节点 — 调用 LLM 生成 Agent 回复"""

from app.agents.state import AgentState
from app.domain.enums import Intent, SafetyCategory
from app.infrastructure.llm_client import get_llm_client


async def response_generator_node(
    state: AgentState,
    persona_prompt: str,
) -> dict:
    """LLM 生成回复, 按 intent 选不同策略"""
    intent_raw = state.get("current_intent", Intent.EIA_CONSULTATION.value)
    intent = Intent(intent_raw)
    messages = state["messages"]
    safety = state.get("safety") or {}
    persona_ctx = state.get("daiyu_persona_context")

    llm = get_llm_client()

    # 安全事件: 直接使用模板回复, 不调用 LLM
    if safety.get("risk_level") == "flagged":
        template = safety.get("response_template", "请稍等。")
        return _append_reply(state, template)

    # 构建 messages 列表
    msgs = [{"role": "system", "content": persona_prompt}]

    if intent == Intent.RISK_ASSESSMENT:
        # 危机: 使用标准干预话术 System Prompt
        msgs[0] = {"role": "system", "content": _CRISIS_PROMPT}

    # 注入人设增强包 (检索到的记忆)
    if persona_ctx:
        msgs.append({"role": "system", "content": persona_ctx})

    # 追加历史消息 (最后 20 条)
    for m in messages[-20:]:
        role = "assistant" if getattr(m, "type", "") == "ai" else "user"
        content = m.content if hasattr(m, "content") else str(m)
        msgs.append({"role": role, "content": content})

    reply = await llm.chat(msgs)
    return _append_reply(state, reply)


def _append_reply(state: AgentState, reply: str) -> dict:
    return {
        "messages": [reply],
        "needs_memory_update": state.get("needs_memory_update", False),
    }


_CRISIS_PROMPT = """你是一个专业的心理危机干预助手。
学生表达了自伤或重度抑郁倾向。请:
1. 不扮演任何角色, 用标准的心理干预话术
2. 表达共情和倾听, 不要评判或说教
3. 明确告知学生会有人联系并提供帮助
4. 回复控制在 150 字以内"""
