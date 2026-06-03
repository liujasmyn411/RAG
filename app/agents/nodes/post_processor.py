"""后处理节点 — L3 入库 + Reflection 触发检查

提取决策 (两级过滤):
  第一级: 关键词/正则 → 直接判定"跳过"或"必提取"
  第二级: 未命中 → Haiku 二分类 (is_meaningful?)
"""

import re
import time
from datetime import datetime

from app.agents.state import AgentState
from app.domain.enums import Intent, SafetyCategory
from app.infrastructure.classifier import ClassifierService
from app.infrastructure.embedding import get_embedding_service
from app.repositories.pg_repo import PgRepo
from app.repositories.milvus_repo import MilvusRepo

# ── 第一级: 关键词正则 ──

# 1) 必定跳过的内容 (不调用 Haiku, 直接不入库)
SKIP_PATTERNS = [
    # 纯问候/告别
    r"^(你好|您好|早上好|下午好|晚上好|再见|拜拜|明天见|晚安)[！!。.]*$",
    # 单字/极短回复
    r"^[嗯哦啊好行对是的不有没会能可以]{1,3}[！!。.]*$",
    r"^(好的|行吧|知道了|收到了|明白了|OK|ok|嗯嗯|好好)[！!。.]*$",
    # 纯教务查询 (不含情绪表达)
    r"^(我|帮我|给我)?(查|看一下|看下|查一下)(成绩|分数|排名|考勤|出勤)",
]

# 2) 必定提取的内容 (不用 Haiku, 直接标记 is_meaningful=True)
MUST_EXTRACT_PATTERNS = [
    # 情绪表达关键词
    r"(好烦|好难受|好难过|好焦虑|好紧张|好害怕|好慌|好丧|崩溃|绝望|无助|孤立|委屈|伤心|难过|害怕)",
    r"(不?开心|不?高兴|不?快乐|不?舒服|不?好受|不?满意|不?喜欢|不?想)",
    r"(我.*(烦|难受|焦虑|紧张|害怕|慌|丧|哭))",
    # 自我评价
    r"(我觉得我|我感觉我|我是不是|我可能|我好像|我应该|我不.*(行|够好|配))",
    # 个人情况
    r"(我爸|我妈|我妈妈|我爸爸|我父母|家里|同桌|同学.*(欺负|吵架|不.*(理|和好)))",
    r"(老师.*(批评|不喜欢|针对|不公平|偏心))",
    # 心理状态变化
    r"(最近.*(总|一直|老是|经常).*(想|觉得|感觉|睡不|吃不))",
    r"(睡不着|失眠|没胃口|不想.*(上学|去学校|学习))",
    # 严重信号 — 必提取 + 标记危机
    r"(不想活|自杀|自残|割腕|想死|活着.*意思|不如死)",
]

# 编译正则
SKIP_RE = [re.compile(p) for p in SKIP_PATTERNS]
MUST_RE = [re.compile(p) for p in MUST_EXTRACT_PATTERNS]
CRISIS_RE = re.compile(r"(不想活|自杀|自残|割腕|想死|活着.*意思|不如死)")


async def post_processor_node(
    state: AgentState,
    pg_repo: PgRepo,
    milvus_repo: MilvusRepo,
) -> dict:
    """对话后处理: L3-Cold 写入 → 提取决策 → L3-Hot 写入 → 触发检查"""
    messages = state["messages"]
    if len(messages) < 2:
        return {"needs_memory_update": False}

    student_id = state.get("student_id", "")
    intent_raw = state.get("current_intent", Intent.DAIYU_CHAT.value)
    safety = state.get("safety") or {}

    if safety.get("risk_level") == "flagged":
        return {"needs_memory_update": False}

    if intent_raw != Intent.DAIYU_CHAT.value:
        return {"needs_memory_update": False}

    try:
        user_msg = messages[-2]
        agent_msg = messages[-1]
        user_text = user_msg.content if hasattr(user_msg, "content") else str(user_msg)
        agent_text = agent_msg.content if hasattr(agent_msg, "content") else str(agent_msg)

        session_id = f"sess_{datetime.now().strftime('%Y%m%d')}_{student_id}"

        # ── L3-Cold 始终写入 ──
        cold_id = await pg_repo.insert_l3_cold(
            student_id, session_id,
            [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": agent_text},
            ],
        )

        # ── 提取决策: 第一级 关键词正则 ──
        is_meaningful, is_crisis = _keyword_filter(user_text)

        if is_meaningful is None:
            # 第二级: Haiku 二分类
            classifier = ClassifierService()
            is_meaningful, is_crisis = await _llm_meaningful_check(
                classifier, user_text
            )

        if is_meaningful:
            # ── L3-Hot 写入 ──
            hot_written = await _write_l3_hot(
                pg_repo, milvus_repo,
                student_id, session_id, cold_id,
                user_text, is_crisis,
            )
            if not hot_written:
                # Level 3 提取失败 → 标记 Cold 待重试
                await pg_repo.mark_cold_reprocess(cold_id)

        needs_reflection = is_crisis or False
        return {"needs_memory_update": needs_reflection}

    except Exception:
        return {"needs_memory_update": False}


def _keyword_filter(user_text: str) -> tuple[bool | None, bool]:
    """第一级: 关键词正则判断

    Returns:
        (True, False)   — 值得提取, 不调 Haiku
        (False, False)  — 跳过, 不调 Haiku
        (None, False)   — 不确定, 需调 Haiku
        (True, True)    — 危机信号
    """
    text = user_text.strip()

    # 跳过检查 (优先)
    for pat in SKIP_RE:
        if pat.search(text):
            return False, False

    # 必提取检查
    for pat in MUST_RE:
        if pat.search(text):
            crisis = bool(CRISIS_RE.search(text))
            return True, crisis

    # 太短的消息也跳过
    if len(text) <= 4:
        return False, False

    return None, False


async def _llm_meaningful_check(
    classifier, user_text: str
) -> tuple[bool, bool]:
    """第二级: Haiku 二分类"""
    try:
        result = await classifier.classify_meaningful(user_text)
        is_crisis = result.get("topic") == "self_harm"
        return result.get("is_meaningful", False), is_crisis
    except Exception:
        return False, False


async def _write_l3_hot(
    pg_repo, milvus_repo,
    student_id, session_id, cold_id,
    user_text, is_crisis,
) -> bool:
    """写入 L3-Hot Milvus — 按提取质量分级赋 write_confidence

    Returns: True=入库成功, False=Level3降级(不入库)
    """
    classifier = ClassifierService()
    quality_level, emotions = await classifier.classify_with_fallback(user_text)

    # 按质量等级赋 write_confidence
    if quality_level == 0:
        write_conf = 0.50  # 完美: emotion+ topic+ concern 齐全
    elif quality_level == 1:
        write_conf = 0.40  # 部分: emotion 有, key_concern 空
    elif quality_level == 2:
        write_conf = 0.30  # 极简: 仅 topic, 低分入库
    else:
        return False  # Level 3: 完全失败, 不入 Milvus

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
        "importance": 0.5 if not is_crisis else 1.0,
        "write_confidence": write_conf,
        "cold_ref": cold_id,
        "embedding_text": embedding_text,
    })
    return True
