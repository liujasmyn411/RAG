"""学生相关领域实体"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.domain.enums import AccountStatus


@dataclass
class Student:
    """学生基础实体"""
    student_id: str
    name: str
    class_name: str = ""
    teacher_id: str = ""
    account_status: AccountStatus = AccountStatus.NORMAL
    created_at: Optional[datetime] = None


@dataclass
class StudentProfile:
    """学生档案实体 (PG student_profile 表)"""
    student_id: str
    rolling_summary: str = ""
    total_sessions: int = 0
    total_messages: int = 0
    first_interaction_at: Optional[datetime] = None
    last_interaction_at: Optional[datetime] = None
    safety_status: str = ""
    violation_b1_count: int = 0
    violation_b2_count: int = 0
    account_status: AccountStatus = AccountStatus.NORMAL
    updated_at: Optional[datetime] = None
