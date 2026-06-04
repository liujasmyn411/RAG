"""Haiku 案例分类器 — 从项目咨询中提取风险/话题/污染物"""

from app.domain.enums import CaseRiskLevel, EIATopic
from app.infrastructure.llm_client import get_llm_client

CLASSIFY_PROMPT = """分析以下环评咨询内容, 提取结构化信息, 输出严格 JSON (仅此, 无其他文字):
{
  "risk_level": "low"|"medium"|"high"|"critical",
  "topic": "air_pollution_risk"|"water_pollution_risk"|"noise_complaint_risk"|"groundwater_risk"|"hazardous_waste_risk"|"cumulative_impact"|"public_concern"|"regulatory_compliance"|"site_selection"|"general_consultation",
  "pollutant": "VOC"|"COD"|"氨氮"|"重金属"|"噪声"|"危废"|"SO2"|"NOx"|"PM2.5"|null,
  "risk_confidence": 0.0~1.0,
  "sensitive_target": "居民区"|"学校"|"医院"|"饮用水源"|"自然保护区"|"基本农田"|"无"|null,
  "key_concern": "最核心的环评关注点, 一句话概括"
}

环评咨询: {query}"""

# 第二级: 提取价值判断 (关键词未命中时使用)
MEANINGFUL_CHECK_PROMPT = """判断以下环评咨询是否值得提取为长期案例记忆:

值得提取的情况:
- 涉及具体建设项目信息 ("化工项目""工业园区""制药厂")
- 提到污染物排放 ("VOC""COD""重金属""噪声")
- 涉及环境风险 ("投诉""超标""事故""污染")
- 提到敏感目标 ("居民区""学校""水源地")
- 涉及法规合规 ("审批""标准""条例")
- 专家经验判断 ("建议""注意事项""常见问题")

不值得提取的情况:
- 纯寒暄 ("你好""再见""谢谢")
- 极短回复 ("嗯""好的""知道了")
- 无关闲聊

输出严格 JSON (仅此):
{{"is_meaningful": true|false, "topic": "general_consultation"|"air_pollution_risk"|...}}

环评咨询: {query}"""


class ClassifierService:
    """Haiku 分类器 — 从环评咨询中提取风险/话题/污染物"""

    def __init__(self) -> None:
        self._llm = get_llm_client()

    async def classify(self, query: str) -> dict:
        """完整分类: risk_level + topic + pollutant + sensitive_target"""
        messages = [{"role": "user", "content": CLASSIFY_PROMPT.format(query=query)}]
        try:
            result = await self._llm.haiku_json(messages)
            return {
                "risk_level": result.get("risk_level", CaseRiskLevel.MEDIUM.value),
                "topic": result.get("topic", EIATopic.GENERAL_CONSULTATION.value),
                "pollutant": result.get("pollutant"),
                "risk_confidence": float(result.get("risk_confidence", 0.5)),
                "sensitive_target": result.get("sensitive_target"),
                "key_concern": result.get("key_concern", ""),
            }
        except Exception:
            return {
                "risk_level": CaseRiskLevel.MEDIUM.value,
                "topic": EIATopic.GENERAL_CONSULTATION.value,
                "pollutant": None,
                "risk_confidence": 0.5,
                "sensitive_target": None,
                "key_concern": "",
            }

    async def classify_meaningful(self, query: str) -> dict:
        """快速二分类: 这轮对话值得提取为案例记忆吗? (1 token 输出)"""
        messages = [{"role": "user", "content": MEANINGFUL_CHECK_PROMPT.format(query=query)}]
        try:
            result = await self._llm.haiku_json(messages)
            return {
                "is_meaningful": bool(result.get("is_meaningful", False)),
                "topic": result.get("topic", EIATopic.GENERAL_CONSULTATION.value),
            }
        except Exception:
            return {"is_meaningful": False, "topic": EIATopic.GENERAL_CONSULTATION.value}

    async def classify_with_fallback(self, query: str) -> tuple[int, dict]:
        """提取 + 质量评估 → (quality_level, result_dict)

        Level 0: 完美提取 — risk_level + topic + key_concern 齐全
        Level 1: 部分提取 — risk_level 有, 但 key_concern 空
        Level 2: 极简提取 — 仅 topic 可信, 其余为空/默认
        Level 3: 完全失败 — LLM 超时/非法JSON/全字段默认, 不入库
        """
        try:
            result = await self._llm.haiku_json([
                {"role": "user", "content": CLASSIFY_PROMPT.format(query=query)},
            ])

            risk_level = result.get("risk_level", "")
            topic = result.get("topic", "")
            concern = result.get("key_concern", "")
            risk_confidence = result.get("risk_confidence", 0.5)

            # Level 3: LLM 调用失败 (返回全默认/空)
            if not risk_level or risk_level == "medium":
                if not concern and topic in ("", "general_consultation"):
                    return 3, _default_result()

            # Level 0: 三核心字段齐全
            if risk_level and topic and concern:
                return 0, {
                    "risk_level": risk_level,
                    "topic": topic,
                    "pollutant": result.get("pollutant"),
                    "risk_confidence": float(risk_confidence),
                    "sensitive_target": result.get("sensitive_target"),
                    "key_concern": concern,
                }

            # Level 1: risk_level 必填, 其他可选
            if risk_level:
                return 1, {
                    "risk_level": risk_level,
                    "topic": topic or "general_consultation",
                    "pollutant": result.get("pollutant"),
                    "risk_confidence": float(risk_confidence),
                    "sensitive_target": result.get("sensitive_target"),
                    "key_concern": concern or "",
                }

            # Level 2: 极简 — 仅 topic 可用
            return 2, {
                "risk_level": "medium",
                "topic": topic or "general_consultation",
                "pollutant": None,
                "risk_confidence": 0.3,
                "sensitive_target": None,
                "key_concern": "",
            }

        except Exception:
            return 3, _default_result()


def _default_result() -> dict:
    return {
        "risk_level": "medium",
        "topic": "general_consultation",
        "pollutant": None,
        "risk_confidence": 0.3,
        "sensitive_target": None,
        "key_concern": "",
    }
