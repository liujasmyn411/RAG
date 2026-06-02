"""Haiku 情绪/话题分类器 — Phase 1 Query 增强"""

from app.domain.enums import EmotionPrimary, Topic
from app.infrastructure.llm_client import get_llm_client

CLASSIFY_PROMPT = """分析以下学生消息, 输出严格 JSON (仅此, 无其他文字):
{
  "emotion_primary": "anxiety"|"sadness"|"frustration"|"anger"|"hopelessness"|"fear"|"calm"|"happy"|"excited"|"confused"|"shame"|"lonely",
  "topic": "academic_stress"|"peer_relationship"|"family_issue"|"self_identity"|"health_concern"|"teacher_conflict"|"future_anxiety"|"daily_chat"|"academic_inquiry"|"bullying"|"self_harm",
  "subject": "math"|"english"|"chinese"|"physics"|"chemistry"|"biology"|"history"|"geography"|"politics"|"pe"|null,
  "intensity": 0.0~1.0,
  "key_concern": "最核心的担忧, 一句话概括"
}

学生消息: {query}"""


class ClassifierService:
    """Haiku 分类器 — 从 query 中提取情绪/话题/学科"""

    def __init__(self) -> None:
        self._llm = get_llm_client()

    async def classify(self, query: str) -> dict:
        messages = [{"role": "user", "content": CLASSIFY_PROMPT.format(query=query)}]
        try:
            result = await self._llm.haiku_json(messages)
            return {
                "emotion_primary": result.get("emotion_primary", EmotionPrimary.CALM.value),
                "topic": result.get("topic", Topic.DAILY_CHAT.value),
                "subject": result.get("subject"),
                "intensity": float(result.get("intensity", 0.5)),
                "key_concern": result.get("key_concern", ""),
            }
        except Exception:
            return {
                "emotion_primary": EmotionPrimary.CALM.value,
                "topic": Topic.DAILY_CHAT.value,
                "subject": None,
                "intensity": 0.5,
                "key_concern": "",
            }
