"""记忆相关领域实体 — 纯数据结构, 零副作用"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.domain.enums import (
    EmotionPrimary,
    Topic,
    CognitionDimension,
    CognitionStatus,
    RelationType,
    SourceType,
    StreakDirection,
    CloseReason,
    SessionStatus,
)


@dataclass
class L3Snapshot:
    """L3-Hot 情景快照实体"""
    l3_id: str
    student_id: str
    session_id: str
    timestamp: datetime

    # 核心语义
    emotion_primary: EmotionPrimary
    emotion_secondary: Optional[EmotionPrimary] = None
    emotion_intensity: float = 0.5
    topic: Topic = Topic.DAILY_CHAT
    subject: Optional[str] = None
    trigger: str = ""
    student_self_report: str = ""
    behavioral_signal: str = ""

    # 叙事链 (Episodic Memory 演进)
    prev_l3_id: Optional[str] = None   # 上一条 L3 快照 ID
    episode_id: Optional[str] = None   # 所属 Episode ID

    # 记忆管理
    importance: float = 0.5
    write_confidence: float = 0.5
    processed_for_l2: bool = False
    archived: bool = False
    cold_ref: Optional[str] = None

    def embedding_text(self, prev_context: str = "") -> str:
        """生成用于向量化的文本。
        prev_context: 上一条 L3 的 trigger/subject, 融入叙事上下文。
        """
        base = f"{self.topic.value} {self.emotion_primary.value} {self.trigger} {self.student_self_report} {self.behavioral_signal}"
        if prev_context:
            return f"[上文情境] {prev_context} [当前] {base}"
        return base


@dataclass
class L2Cognition:
    """L2 语义认知实体 (对应 Neo4j 中的关系边)"""
    cognition_id: Optional[str] = None
    student_id: str = ""
    dimension: CognitionDimension = CognitionDimension.SUBJECT_ABILITY
    relation_type: RelationType = RelationType.WEAK_SUBJECT
    target_name: str = ""
    content: str = ""

    # 置信度三因子
    confidence: float = 0.70
    C_peak: float = 0.70
    C_trough: float = 0.70

    # 连续性追踪
    streak_count: int = 0
    streak_direction: Optional[StreakDirection] = None
    last_oppose_time: Optional[datetime] = None

    # 元信息
    source: SourceType = SourceType.C_REFLECTION
    verified_count: int = 0
    status: CognitionStatus = CognitionStatus.ACTIVE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def damage(self) -> float:
        """伤害深度: 从峰值到谷底的距离"""
        return max(0, self.C_peak - self.C_trough)

    @property
    def is_streaking(self) -> bool:
        return self.streak_count > 0 and self.streak_direction is not None


@dataclass
class DraftCandidate:
    """草稿区候选认知实体 (PG l2_draft_candidates 表)

    写入置信度 0.5 ≤ conf < 0.7 的记忆暂存于此，
    仅 Reflection 可见，不参与主检索。
    """
    draft_id: str
    student_id: str
    trait_name: str
    trait_value: str = ""
    polarity: str = "positive"
    source_type: str = ""
    write_confidence: float = 0.5
    evidence_l3_ids: list[str] = field(default_factory=list)
    drafted_at: Optional[datetime] = None
    consumed: bool = False


@dataclass
class SessionArchive:
    """会话归档实体 (PG session_archive 表)"""
    session_id: str
    student_id: str
    closed_at: datetime
    close_reason: CloseReason = CloseReason.TIMEOUT
    summary: str = ""
    safety_snapshot: dict = field(default_factory=dict)
    last_intent: str = ""
    last_topic: str = ""
    unclosed_topic: Optional[str] = None
    message_count: int = 0
