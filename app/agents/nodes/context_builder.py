"""上下文组装节点 — 将检索结果 + 专家人设 + 认知注入 messages"""

from app.agents.state import AgentState
from app.domain.enums import Intent, get_dimension_label


async def context_builder_node(state: AgentState, persona_prompt: str) -> dict:
    """组装上下文: 将检索到的记忆注入 System Message"""
    intent_raw = state.get("current_intent", Intent.EIA_CONSULTATION.value)
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

    if intent == Intent.EIA_CONSULTATION:
        l3 = retrieved.get("L3", [])
        l2 = retrieved.get("L2", [])
        l0 = retrieved.get("L0", [])

        if l3:
            mem_lines = []
            for m in l3[:3]:
                line = (
                    f"【案例-{m.get('confidence_label','')}】"
                    f"{m.get('embedding_text','')}"
                )
                # Quick Win 4: 附加叙事上下文 (上文/下文)
                prev_ctx = m.get("_prev")
                next_ctx = m.get("_next")
                narrative_hints = []
                if prev_ctx:
                    narrative_hints.append(
                        f"上文: {prev_ctx.get('topic','')}"
                        f" {prev_ctx.get('embedding_text','')[:60]}"
                    )
                if next_ctx:
                    narrative_hints.append(
                        f"下文: {next_ctx.get('topic','')}"
                        f" {next_ctx.get('embedding_text','')[:60]}"
                    )
                if narrative_hints:
                    line += " [" + " | ".join(narrative_hints) + "]"
                mem_lines.append(line)
            context_parts.append("相关案例:\n" + "\n".join(mem_lines))
        if l2:
            trait_lines = [
                f"· {get_dimension_label(t.get('relation_type',''))}"
                f"→{t.get('target_name','')}"
                f" (置信度:{t.get('confidence',0):.2f})"
                for t in l2[:5]
            ]
            context_parts.append("专家认知:\n" + "\n".join(trait_lines))
        if l0:
            entity_lines = [
                f"· {s.get('scene_name','')} — {s.get('key_quote','')}"
                for s in l0[:2]
            ]
            context_parts.append("相关实体:\n" + "\n".join(entity_lines))

    elif intent == Intent.RISK_ASSESSMENT:
        l2 = retrieved.get("L2", [])
        l3_cold = retrieved.get("L3-Cold", [])
        if l2:
            trait_lines = [
                f"· {get_dimension_label(t.get('relation_type',''))}"
                f"→{t.get('target_name','')}"
                f" (置信度:{t.get('confidence',0):.2f})"
                for t in l2[:5]
            ]
            if trait_lines:
                context_parts.append("风险认知特征:\n" + "\n".join(trait_lines))
        if l3_cold:
            cold_lines = [
                f"· {c.get('summary','')}" for c in l3_cold[:3]
            ]
            context_parts.append("历史案例回源:\n" + "\n".join(cold_lines))

    persona_context = "\n\n".join(context_parts) if context_parts else None
    return {
        "daiyu_persona_context": persona_context,
    }
