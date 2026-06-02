"""领域枚举定义 — 所有 Enum 集中管理, 零依赖"""

from enum import Enum


class EmotionPrimary(str, Enum):
    ANXIETY = "anxiety"
    SADNESS = "sadness"
    FRUSTRATION = "frustration"
    ANGER = "anger"
    HOPELESSNESS = "hopelessness"
    FEAR = "fear"
    CALM = "calm"
    HAPPY = "happy"
    EXCITED = "excited"
    CONFUSED = "confused"
    SHAME = "shame"
    LONELY = "lonely"


class Topic(str, Enum):
    ACADEMIC_STRESS = "academic_stress"
    PEER_RELATIONSHIP = "peer_relationship"
    FAMILY_ISSUE = "family_issue"
    SELF_IDENTITY = "self_identity"
    HEALTH_CONCERN = "health_concern"
    TEACHER_CONFLICT = "teacher_conflict"
    FUTURE_ANXIETY = "future_anxiety"
    DAILY_CHAT = "daily_chat"
    ACADEMIC_INQUIRY = "academic_inquiry"
    BULLYING = "bullying"
    SELF_HARM = "self_harm"


class Intent(str, Enum):
    DAIYU_CHAT = "daiyu_chat"
    ACADEMIC_QUERY = "academic_query"
    PSYCH_CRISIS = "psych_crisis"
    LITERARY_QUERY = "literary_query"
    DATA_QUERY = "data_query"        # NL2SQL 只读查询
    DATA_MUTATE = "data_mutate"      # NL2SQL 增删改 (Phase 2)


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


class RelationType(str, Enum):
    """L2 关系边类型"""
    WEAK_SUBJECT = "偏科"
    EMOTION_TENDENCY = "情绪倾向"
    ATTITUDE_PREFERENCE = "态度偏好"
    SOCIAL_PATTERN = "社交模式"


class CognitionDimension(str, Enum):
    SUBJECT_ABILITY = "学科能力"
    EMOTION_PATTERN = "情绪模式"
    SOCIAL_PATTERN = "社交模式"
    ATTITUDE_PREFERENCE = "态度偏好"


class TraitCategory(str, Enum):
    EMOTION = "emotion"
    SOCIAL = "social"
    BEHAVIOR = "behavior"


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
