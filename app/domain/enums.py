"""领域枚举定义 — 所有 Enum 集中管理, 零依赖"""

from enum import Enum


# ═══════════════════════════════════════════════════════════
# EIA 领域枚举
# ═══════════════════════════════════════════════════════════

class CaseRiskLevel(str, Enum):
    """案例风险等级 — 替代原 EmotionPrimary, 支撑 Type 5 风险波动冲突"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EIATopic(str, Enum):
    """EIA 案例主题分类"""
    AIR_POLLUTION_RISK = "air_pollution_risk"
    WATER_POLLUTION_RISK = "water_pollution_risk"
    NOISE_COMPLAINT_RISK = "noise_complaint_risk"
    GROUNDWATER_RISK = "groundwater_risk"
    HAZARDOUS_WASTE_RISK = "hazardous_waste_risk"
    CUMULATIVE_IMPACT = "cumulative_impact"
    PUBLIC_CONCERN = "public_concern"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    SITE_SELECTION = "site_selection"
    GENERAL_CONSULTATION = "general_consultation"


class Intent(str, Enum):
    EIA_CONSULTATION = "eia_consultation"    # EIA 专家咨询 (原 daiyu_chat)
    CASE_RETRIEVAL = "case_retrieval"        # 案例检索
    RISK_ASSESSMENT = "risk_assessment"      # 风险评估
    DATA_QUERY = "data_query"                # NL2SQL 只读查询
    DATA_MUTATE = "data_mutate"              # NL2SQL 增删改 (Phase 2)


class DataOperation(str, Enum):
    QUERY = "query"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ConflictType(str, Enum):
    TYPE_1_OPPOSE = "type_1_oppose"
    TYPE_2_SUPERSEDE = "type_2_supersede"
    TYPE_3_REFINE = "type_3_refine"
    TYPE_4_SOURCE_CONFLICT = "type_4_source_conflict"
    TYPE_5_AFFECTIVE = "type_5_affective"
    TYPE_6_OVERLAP = "type_6_overlap"


class SafetyCategory(str, Enum):
    PSYCH_CRISIS = "psych_crisis"
    POLITICAL = "political"
    VULGAR = "vulgar"
    INJECTION = "injection"
    NONE = "none"


class RiskLevel(str, Enum):
    SAFE = "safe"
    FLAGGED = "flagged"
    BLOCKED = "blocked"


class AccountStatus(str, Enum):
    NORMAL = "normal"
    LIMITED = "limited"
    BLOCKED = "blocked"


class CarryOverLevel(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    MINIMAL = "minimal"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    CLOSING = "closing"
    DORMANT = "dormant"
    CLOSED = "closed"
    EXPIRED = "expired"


class CloseReason(str, Enum):
    TIMEOUT = "timeout"
    EXPLICIT = "explicit"
    ADMIN = "admin"


# ═══════════════════════════════════════════════════════════
# L2 认知维度注册表 (Schema-flexible: 扩展只需加条目)
# ═══════════════════════════════════════════════════════════
# key → Neo4j 边类型, label → 中文显示名
# target_type: "Entity" = 实体节点(项目/污染物/法规), "Trait" = 特征节点
COGNITION_DIMENSIONS: dict[str, dict] = {
    "risk_pattern": {
        "label": "风险模式",
        "target_type": "Trait",
        "description": "某类项目/污染物的典型风险特征与规律",
        "prompt_hint": "污染物扩散风险、敏感目标影响、公众投诉风险、事故隐患、地下水/土壤风险",
    },
    "compliance_pattern": {
        "label": "合规模式",
        "target_type": "Trait",
        "description": "法规符合性相关的规律性认知",
        "prompt_hint": "某类项目常见合规问题、审批难点、法规关注重点、排放标准要求",
    },
    "impact_pattern": {
        "label": "影响模式",
        "target_type": "Trait",
        "description": "项目对环境的潜在影响规律",
        "prompt_hint": "累积影响、跨界影响、二次污染、生态影响、环境容量",
    },
    "experience_pattern": {
        "label": "经验模式",
        "target_type": "Trait",
        "description": "从业经验中沉淀的实践规律与最佳实践",
        "prompt_hint": "选址建议、公众沟通策略、常见争议点、最佳实践、风险规避经验",
    },
}


def get_dimension_label(key: str) -> str:
    """维度 key → 中文显示名"""
    return COGNITION_DIMENSIONS.get(key, {}).get("label", key)


def get_dimension_target_type(key: str) -> str:
    """维度 key → Neo4j 目标节点类型 (Entity | Trait)"""
    return COGNITION_DIMENSIONS.get(key, {}).get("target_type", "Trait")


def get_dimension_keys() -> list[str]:
    """所有已注册维度 key"""
    return list(COGNITION_DIMENSIONS.keys())


def build_dimensions_prompt() -> str:
    """动态生成 Reflection 维度列表 Prompt 片段"""
    lines = []
    for key, cfg in COGNITION_DIMENSIONS.items():
        lines.append(f"  - {key}: {cfg['prompt_hint']}")
    return "\n".join(lines)


class TraitCategory(str, Enum):
    RISK = "risk"
    COMPLIANCE = "compliance"
    IMPACT = "impact"
    EXPERIENCE = "experience"


class StreakDirection(str, Enum):
    SUPPORT = "support"
    OPPOSE = "oppose"


class CognitionStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    ARCHIVED = "archived"


class SourceType(str, Enum):
    S_SELF_REPORT = "S_self_report"
    A_SYSTEM_RECORD = "A_system_record"
    B_CANON_TEXT = "B_canon_text"
    C_REFLECTION = "C_reflection"
    D_INFERENCE = "D_inference"


class EscalationLevel(str, Enum):
    IGNORE = "ignore"
    WARN = "warn"
    REFUSE = "refuse"
    NOTIFY = "notify"
    SUSPEND = "suspend"


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class ProcessedStatus(str, Enum):
    """L3-Hot 提炼状态 (替代 bool)"""
    FALSE = "false"       # 未处理
    SKIPPED = "skipped"   # 不足2条, 攒够再处理
    BATCHED = "batched"   # 已分批, 剩余待处理
    TRUE = "true"         # 已提炼


class ConflictStatus(str, Enum):
    """L2 认知边的冲突状态"""
    ACTIVE = "active"                   # 正常 (无冲突)
    PENDING_VERIFICATION = "pending_verification"  # 有矛盾, 等待更多证据
    ARCHIVED = "archived"               # 超时归档 / 被推翻


class CrisisSeverity(str, Enum):
    URGENT = "urgent"
    WARNING = "warning"


class CrisisStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ESCALATED = "escalated"
    CLOSED = "closed"


class BoundaryTrigger(str, Enum):
    """Episode 边界触发信号"""
    FIRST_EPISODE = "first_episode"         # 首次对话, 无历史
    TOPIC_SHIFT = "topic_shift"             # 话题切换 (topic 改变)
    SESSION_BOUNDARY = "session_boundary"   # 会话边界 (新会话)
    TIME_GAP = "time_gap"                   # 时间间隔过长
