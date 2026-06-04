"""记忆检索节点 — 按 intent 检索三层记忆"""

from app.agents.state import AgentState
from app.domain.enums import Intent
from app.services.memory_service import MemoryService


async def memory_retrieval_node(
    state: AgentState,
    memory_service: MemoryService,
) -> dict:
    """按 intent 调度检索策略"""
    intent_raw = state.get("current_intent", Intent.EIA_CONSULTATION.value)
    intent = Intent(intent_raw)

    messages = state["messages"]
    last_msg = messages[-1] if messages else None
    query = last_msg.content if last_msg and hasattr(last_msg, "content") else ""
    student_id = state.get("student_id", "")

    # 安全事件短路: 不检索记忆
    safety = state.get("safety") or {}
    if safety.get("risk_level") == "flagged":
        return {"retrieved_context": None}

    retrieved = await memory_service.retrieve_by_intent(intent, query, student_id)
    return {"retrieved_context": retrieved}
