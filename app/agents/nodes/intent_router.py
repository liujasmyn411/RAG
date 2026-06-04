"""情境路由节点 — 判断当前对话意图 (关键词 + LLM 精分类)"""

from app.agents.state import AgentState
from app.domain.enums import Intent, SafetyCategory


ACADEMIC_KEYWORDS = [
    "成绩", "考了多少", "排名", "出勤", "旷课",
    "数学考", "英语考", "语文考", "期末考试",
    "多少分", "第几名", "请假",
]

LITERARY_KEYWORDS = [
    "红楼梦", "三国", "水浒", "西游", "四大名著",
    "黛玉", "宝玉", "宝钗", "曹操", "刘备", "关羽",
    "诸葛亮", "林冲", "武松", "孙悟空", "猪八戒",
    "大观园", "荣国府", "梁山", "取经",
]

CRISIS_OVERRIDE_TERMS = [
    "不想活了", "自杀", "死", "自残", "割腕",
    "活着没意思", "想死",
]

# NL2SQL 数据查询关键词 (触发 LLM 精分类)
DATA_OP_KEYWORDS = [
    "查询", "统计", "平均", "最高", "最低", "大于", "小于",
    "排名", "排行", "分组", "按班级", "男生", "女生", "共有",
    "一共有", "有几个", "哪些", "哪个", "多少分以上",
    "超过", "不足", "以上", "以下", "最多", "最少",
    "不及格", "大于等于", "小于等于", "合计",
    "薪资最高", "就业时长", "平均分", "平均薪资",
    "毕业院校", "籍贯", "专业", "学历",
    "查询所有", "列出所有", "显示所有",
]


async def intent_router_node(state: AgentState) -> dict:
    """基于 keywords + safety 结果判断 intent"""
    messages = state["messages"]
    last_msg = messages[-1] if messages else None
    content = last_msg.content if last_msg and hasattr(last_msg, "content") else ""

    safety = state.get("safety") or {}

    # 安全事件强制路由
    if safety.get("category") == SafetyCategory.PSYCH_CRISIS.value:
        return {"current_intent": Intent.RISK_ASSESSMENT.value}

    if safety.get("risk_level") == "flagged":
        # 被安全过滤拦截 → 直接生成安全回复, 不进入记忆检索
        return {"current_intent": Intent.EIA_CONSULTATION.value}

    # 教务查询检测
    for kw in ACADEMIC_KEYWORDS:
        if kw in content:
            return {"current_intent": Intent.EIA_CONSULTATION.value}

    # 危机二次检测 (安全层可能漏过的变体)
    for kw in CRISIS_OVERRIDE_TERMS:
        if kw in content:
            return {"current_intent": Intent.RISK_ASSESSMENT.value}

    # 数据查询关键词检测 → 触发 LLM 精分类
    for kw in DATA_OP_KEYWORDS:
        if kw in content:
            return {"current_intent": Intent.DATA_QUERY.value}

    # 文学知识检索
    for kw in LITERARY_KEYWORDS:
        if kw in content:
            return {"current_intent": Intent.CASE_RETRIEVAL.value}

    return {"current_intent": Intent.EIA_CONSULTATION.value}
