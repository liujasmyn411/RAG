"""后处理节点 — L3 入库 + Reflection 触发检查"""

import time
from datetime import datetime

from app.agents.state import AgentState
from app.domain.enums import Intent, SafetyCategory
from app.services.memory_service import MemoryService
from app.infrastructure.classifier import ClassifierService
from app.infrastructure.embedding import get_embedding_service
from app.repositories.pg_repo import PgRepo
from app.repositories.milvus_repo import MilvusRepo


async def post_processor_node(
    state: AgentState,
    pg_repo: PgRepo,
    milvus_repo: MilvusRepo,
) -> dict:
    """对话后处理: L3-Cold 写入 → L3-Hot 提取 → 触发检查"""
    messages = state["messages"]
    if len(messages) < 2:
        return {"needs_memory_update": False}

    student_id = state.get("student_id", "")
    intent_raw = state.get("current_intent", Intent.DAIYU_CHAT.value)
    safety = state.get("safety") or {}

    # 安全事件不入库
    if safety.get("risk_level") == "flagged":
        return {"needs_memory_update": False}

    # 仅 daiyu_chat 提取 L3-Hot
    if intent_raw != Intent.DAIYU_CHAT.value:
        return {"needs_memory_update": False}

    try:
        user_msg = messages[-2]
        agent_msg = messages[-1]
        user_text = user_msg.content if hasattr(user_msg, "content") else str(user_msg)
        agent_text = agent_msg.content if hasattr(agent_msg, "content") else str(agent_msg)

        session_id = f"sess_{datetime.now().strftime('%Y%m%d')}_{student_id}"

        # L3-Cold 写入
        cold_id = await pg_repo.insert_l3_cold(
            student_id, session_id,
            [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": agent_text},
            ],
        )

        # L3-Hot 提取
        classifier = ClassifierService()
        emotions = await classifier.classify(user_text)

        emb_service = get_embedding_service()
        embedding_text = (
            f"{emotions.get('topic','')} "
            f"{emotions.get('emotion_primary','')} "
            f"{emotions.get('key_concern','')}"
        )
        vec = emb_service.encode(embedding_text)

        l3_id = f"l3_{datetime.now().strftime('%Y%m%d')}_{student_id}_{int(time.time())}"
        await milvus_repo.insert_l3(vec, {
            "l3_id": l3_id,
            "student_id": student_id,
            "session_id": session_id,
            "timestamp": int(time.time()),
            "emotion_primary": emotions.get("emotion_primary", "calm"),
            "emotion_intensity": emotions.get("intensity", 0.5),
            "topic": emotions.get("topic", "daily_chat"),
            "importance": 0.5,
            "write_confidence": 0.50,
            "cold_ref": cold_id,
            "embedding_text": embedding_text,
        })

        # 危机 L3 → 立即触发 Reflection
        needs_reflection = emotions.get("topic") == "self_harm"
        return {"needs_memory_update": needs_reflection}

    except Exception:
        return {"needs_memory_update": False}
