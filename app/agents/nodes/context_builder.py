"""上下文组装节点 — 将检索结果 + 人设 + 事实合并注入 messages"""

from app.agents.state import AgentState
from app.domain.enums import Intent


async def context_builder_node(state: AgentState, persona_prompt: str) -> dict:
    """组装上下文: 将检索到的记忆注入 System Message"""
    intent_raw = state.get("current_intent", Intent.DAIYU_CHAT.value)
    intent = Intent(intent_raw)
    retrieved = state.get("retrieved_context") or {}
    safety = state.get("safety") or {}

    # 安全事件: 直接使用预设回复
    if safety.get("risk_level") == "flagged":
        return {
            "daiyu_persona_context": None,
            "messages": state["messages"],  # 不做修改
        }

    context_parts: list[str] = []

    if intent == Intent.DAIYU_CHAT:
        l3 = retrieved.get("L3", [])
        l2 = retrieved.get("L2", [])
        l0 = retrieved.get("L0", [])

        if l3:
            mem_lines = [
                f"【记忆-{m.get('confidence_label','')}】"
                f"{m.get('embedding_text','')}"
                for m in l3[:3]
            ]
            context_parts.append("相关记忆:\n" + "\n".join(mem_lines))
        if l2:
            trait_lines = [
                f"· {t.get('relation_type','')}→{t.get('target_name','')}"
                f" (置信度:{t.get('confidence',0):.2f})"
                for t in l2[:5]
            ]
            context_parts.append("学生认知:\n" + "\n".join(trait_lines))
        if l0:
            scene_lines = [
                f"· {s.get('scene_name','')} — {s.get('key_quote','')}"
                for s in l0[:2]
            ]
            context_parts.append("红楼典故:\n" + "\n".join(scene_lines))

    elif intent == Intent.ACADEMIC_QUERY:
        l1 = retrieved.get("L1", {})
        l2 = retrieved.get("L2", [])
        if l1:
            context_parts.append(
                "【以下是必须引用的准确数据, 不可篡改】\n"
                + _format_academic_data(l1)
                + "\n【如果输出与上述数据冲突, 以数据为准】"
            )
        if l2:
            trait_lines = [
                f"· {t.get('relation_type','')}→{t.get('target_name','')}"
                for t in l2[:3]
                if t.get("relation_type") == "偏科"
            ]
            if trait_lines:
                context_parts.append("该生学科偏科:\n" + "\n".join(trait_lines))

    persona_context = "\n\n".join(context_parts) if context_parts else None
    return {
        "daiyu_persona_context": persona_context,
    }


def _format_academic_data(l1: dict) -> str:
    lines = []
    scores = l1.get("scores", [])
    if scores:
        lines.append("成绩:")
        for s in scores[:10]:
            lines.append(
                f"  {s.get('subject','')}: {s.get('score','')}分"
                f" ({s.get('exam_date','')})"
            )
    attendance = l1.get("attendance", [])
    if attendance:
        lines.append("考勤:")
        for a in attendance[:5]:
            lines.append(
                f"  {a.get('date','')}: {a.get('status','')}"
                + (f" ({a.get('reason','')})" if a.get("reason") else "")
            )
    return "\n".join(lines)
