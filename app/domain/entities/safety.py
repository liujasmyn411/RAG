"""安全相关领域实体"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.domain.enums import (
    SafetyCategory,
    RiskLevel,
    EscalationLevel,
    CrisisSeverity,
    CrisisStatus,
)


@dataclass
class SafetyEvent:
    """安全事件实体 (PG security_log 表)"""
    id: Optional[str] = None
    timestamp: Optional[datetime] = None
    student_id: str = ""
    teacher_id: str = ""
    category: SafetyCategory = SafetyCategory.NONE
    risk_level: int = 0
    trigger_type: str = ""  # "keyword" | "llm_semantic"
    escalation: EscalationLevel = EscalationLevel.IGNORE
    original_message_hash: str = ""
    anonymized_summary: str = ""
    new_user_status: str = ""


@dataclass
class ViolationRecord:
    """违规记录 (内嵌于 StudentProfile)"""
    b1_count: int = 0
    b2_count: int = 0
    last_violation_time: Optional[datetime] = None
    b2_window_start: Optional[datetime] = None

    def b2_warning_level(self) -> str:
        """当前 B2 违规的警告级别"""
        if self.b2_count >= 5:
            return "block"
        elif self.b2_count >= 4:
            return "limit"
        elif self.b2_count >= 3:
            return "warn_system"
        elif self.b2_count >= 1:
            return "soft_warn"
        return "none"

    def b1_warning_level(self) -> str:
        """B1 违规的警告级别 — 零容忍"""
        if self.b1_count >= 3:
            return "block"
        elif self.b1_count >= 2:
            return "limit_24h"
        elif self.b1_count >= 1:
            return "warn_and_notify"
        return "none"


@dataclass
class CrisisAlert:
    """危机通知实体"""
    id: Optional[int] = None
    student_id: str = ""
    teacher_id: str = ""
    severity: CrisisSeverity = CrisisSeverity.WARNING
    summary: str = ""
    status: CrisisStatus = CrisisStatus.PENDING
    triggered_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    confirmed_by: str = ""
    resolution: str = ""
    escalated_at: Optional[datetime] = None

    def is_overdue(self, timeout_minutes: int = 30) -> bool:
        if self.status != CrisisStatus.PENDING or self.triggered_at is None:
            return False
        return (datetime.now() - self.triggered_at).total_seconds() > timeout_minutes * 60
