"""Haiku 情绪/话题分类器 — Phase 1 Query 增强 + 提取价值判断"""

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

# 第二级: 提取价值判断 (关键词未命中时使用)
MEANINGFUL_CHECK_PROMPT = """判断以下学生消息是否值得提取为长期记忆:

值得提取的情况:
- 表达了情绪 ("好烦""开心""难过""焦虑""害怕")
- 提到个人情况 ("我爸妈...""我和同学...""老师对我...")
- 自我评价 ("我觉得我...""我是不是...")
- 心理状态变化 ("最近总是睡不着")
- 涉及敏感话题 (自伤/霸凌/家庭问题)

不值得提取的情况:
- 纯教务查询 ("查成绩""多少分")
- 寒暄 ("你好""再见""谢谢")
- 极短回复 ("嗯""好的""知道了")
- 纯知识提问 ("红楼梦的作者是谁")

输出严格 JSON (仅此):
{{"is_meaningful": true|false, "topic": "daily_chat"|"self_harm"|"academic_stress"|...}}

学生消息: {query}"""


class ClassifierService:
    """Haiku 分类器 — 从 query 提取情绪/话题/学科 + 提取价值判断"""

    def __init__(self) -> None:
        self._llm = get_llm_client()

    async def classify(self, query: str) -> dict:
        """完整分类: emotion + topic + subject + intensity"""
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

    async def classify_meaningful(self, query: str) -> dict:
        """快速二分类: 这轮对话值得提取吗? (1 token 输出)"""
        messages = [{"role": "user", "content": MEANINGFUL_CHECK_PROMPT.format(query=query)}]
        try:
            result = await self._llm.haiku_json(messages)
            return {
                "is_meaningful": bool(result.get("is_meaningful", False)),
                "topic": result.get("topic", "daily_chat"),
            }
        except Exception:
            return {"is_meaningful": False, "topic": "daily_chat"}

    async def classify_with_fallback(self, query: str) -> tuple[int, dict]:
        """提取 + 质量评估 → (quality_level, result_dict)

        Level 0: 完美提取 — emotion_primary + topic + key_concern 齐全
        Level 1: 部分提取 — emotion_primary 有, 但 key_concern 空
        Level 2: 极简提取 — 仅 topic 可信, 其余为空/默认
        Level 3: 完全失败 — LLM 超时/非法JSON/全字段默认, 不入库
        """
        try:
            result = await self._llm.haiku_json([
                {"role": "user", "content": CLASSIFY_PROMPT.format(query=query)},
            ])

            emotion = result.get("emotion_primary", "")
            topic = result.get("topic", "")
            concern = result.get("key_concern", "")
            intensity = result.get("intensity", 0.5)

            # Level 3: LLM 调用失败 (返回全默认/空)
            if not emotion or emotion == "calm":
                if not concern and topic in ("", "daily_chat"):
                    return 3, _default_result()

            # Level 0: 三核心字段齐全
            if emotion and topic and concern:
                return 0, {
                    "emotion_primary": emotion,
                    "topic": topic,
                    "subject": result.get("subject"),
                    "intensity": float(intensity),
                    "key_concern": concern,
                }

            # Level 1: emotion_primary 必填, 其他可选
            if emotion:
                return 1, {
                    "emotion_primary": emotion,
                    "topic": topic or "daily_chat",
                    "subject": result.get("subject"),
                    "intensity": float(intensity),
                    "key_concern": concern or "",
                }

            # Level 2: 极简 — 仅 topic 可用
            return 2, {
                "emotion_primary": "calm",
                "topic": topic or "daily_chat",
                "subject": None,
                "intensity": 0.3,
                "key_concern": "",
            }

        except Exception:
            return 3, _default_result()


def _default_result() -> dict:
    return {
        "emotion_primary": "calm",
        "topic": "daily_chat",
        "subject": None,
        "intensity": 0.3,
        "key_concern": "",
    }
