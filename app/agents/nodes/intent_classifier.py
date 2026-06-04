"""意图精分类节点 — LLM 二次分类 (仅关键词命中时触发)"""

from app.agents.state import AgentState
from app.domain.enums import Intent
from app.infrastructure.llm_client import get_llm_client


CLASSIFY_PROMPT = """你是一个意图分类器。判断以下用户消息的数据操作意图。

输出 JSON 格式:
{
  "intent": "data_query" | "academic_query" | "daiyu_chat",
  "operation": "query" | null,
  "target": "student" | "score" | "employment" | "class" | "teacher" | "multi" | null,
  "confidence": 0.0-1.0
}

分类规则:
- "data_query": 用户想查询/统计/分析数据库中的数据。涉及多个学生、班级聚合、排名、统计。
  例如: "查询所有超过30岁的学生"、"初二3班有多少男生"、"数学平均分最高的班级"
- "academic_query": 用户查询某个特定学生自己的成绩/考勤。关键词: "我"、"我的"、"小红考了多少"
  例如: "我数学考了多少分"、"小红上次考试排名第几"
- "daiyu_chat": 闲聊、文学知识、非数据查询
  例如: "黛玉你好"、"今天天气真好"、"红楼梦讲了什么"

置信度:
- ≥0.8: 明确的数据查询
- 0.5-0.8: 可能是数据查询
- <0.5: 不建议分类为数据查询"""


async def classify_intent_node(state: AgentState) -> dict:
    """LLM 精分类用户意图"""
    messages = state.get("messages", [])
    if not messages:
        return {"current_intent": Intent.EIA_CONSULTATION.value}

    last_msg = messages[-1]
    content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    try:
        llm = get_llm_client()
        result = await llm.chat_json(
            [
                {"role": "system", "content": CLASSIFY_PROMPT},
                {"role": "user", "content": content},
            ],
            temperature=0.1,
        )

        intent_str = result.get("intent", "daiyu_chat")
        confidence = result.get("confidence", 0.0)

        if intent_str == "data_query" and confidence >= 0.7:
            return {"current_intent": Intent.DATA_QUERY.value}
        elif intent_str == "academic_query" and confidence >= 0.7:
            return {"current_intent": Intent.EIA_CONSULTATION.value}

        return {"current_intent": Intent.EIA_CONSULTATION.value}

    except Exception:
        # LLM 调用失败 → 回退，由关键词路由决定
        return {}
