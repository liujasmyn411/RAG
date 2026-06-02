"""事实自纠节点 — 教务查询场景校验 LLM 输出中的数据"""

import re

from app.agents.state import AgentState
from app.domain.enums import Intent


async def fact_verifier_node(state: AgentState) -> dict:
    """教务查询后校验 LLM 回复中的数字是否与 fact_snapshot 一致"""
    intent_raw = state.get("current_intent", "")
    if intent_raw != Intent.ACADEMIC_QUERY.value:
        return {}

    retrieved = state.get("retrieved_context") or {}
    l1 = retrieved.get("L1", {})
    if not l1:
        return {}

    messages = state["messages"]
    if not messages:
        return {}

    reply = messages[-1]
    reply_text = reply.content if hasattr(reply, "content") else str(reply)

    # 提取回复中的数字
    numbers_in_reply = re.findall(r"\d+\.?\d*", reply_text)

    # 提取 fact_snapshot 中的数字
    scores = l1.get("scores", [])
    fact_numbers = set()
    for s in scores[:5]:
        score_val = s.get("score", "")
        if score_val:
            fact_numbers.add(str(score_val))

    # 如果回复中的数字不在事实数据中 → 标记需要重生成
    for n in numbers_in_reply:
        if n in fact_numbers:
            break
    else:
        # 没有匹配到事实数字 (回复可能编造了数据)
        return {"needs_memory_update": False}

    return {}
