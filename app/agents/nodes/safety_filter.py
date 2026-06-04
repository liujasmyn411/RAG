"""安全过滤节点 — 所有消息的第一道门"""

from app.agents.state import AgentState
from app.services.safety_service import SafetyService
from app.repositories.pg_repo import PgRepo
from app.domain.enums import SafetyCategory, EscalationLevel


async def safety_filter_node(state: AgentState, safety_service: SafetyService) -> dict:
    """安全过滤: 两级检测 → 直接路由到安全处理或继续"""
    messages = state["messages"]
    if not messages:
        return {"safety": None, "needs_memory_update": False}

    last_msg = messages[-1]
    content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    student_id = state.get("student_id", "")
    teacher_id = ""  # 由 profile 获取

    event = await safety_service.filter(content, student_id, teacher_id)

    if event.category in (SafetyCategory.PSYCH_CRISIS,):
        # 危机: 绕过正常流程
        return {
            "safety": {
                "risk_level": "flagged",
                "category": event.category.value,
                "escalation": event.escalation.value,
                "response_template": _SAFETY_RESPONSES.get(event.category.value, ""),
            },
            "current_intent": "risk_assessment",
            "needs_memory_update": False,
        }

    if event.escalation in (EscalationLevel.REFUSE, EscalationLevel.SUSPEND):
        return {
            "safety": {
                "risk_level": "flagged",
                "category": event.category.value,
                "escalation": event.escalation.value,
                "response_template": _SAFETY_RESPONSES.get(event.category.value, ""),
            },
            "current_intent": "eia_consultation",
            "needs_memory_update": False,
        }

    # B2 Level 1 软性规劝: 继续正常流程, 但安全标记注入
    return {
        "safety": {
            "risk_level": "safe",
            "category": event.category.value,
            "escalation": event.escalation.value,
        },
        "needs_memory_update": False,
    }


_SAFETY_RESPONSES = {
    "risk_assessment": "我听到了你的话。请稍等, 有人会立刻联系你。你并不孤单。",
    "political": "这个问题我无法回答。请遵守使用规范。",
    "vulgar": "说话仔细些, 仔细我告诉太太去。",
    "injection": "",
}
