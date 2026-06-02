"""SQLAlchemy ORM 模型 — 业务表 + 记忆/安全表"""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from app.domain.enums import AccountStatus, UserRole
from app.infrastructure.database import Base


# ═══════════════════════════════════════════════════════════
# 业务表
# ═══════════════════════════════════════════════════════════


class Student(Base):
    __tablename__ = "students"

    student_id = Column(String(32), primary_key=True, comment="学号")
    name = Column(String(64), nullable=False, comment="姓名")
    class_name = Column(String(32), nullable=False, comment="班级")
    hometown = Column(String(128), default="", comment="籍贯")
    graduated_school = Column(String(128), default="", comment="毕业院校")
    major = Column(String(64), default="", comment="专业")
    enrollment_date = Column(Date, nullable=True, comment="入学时间")
    graduation_date = Column(Date, nullable=True, comment="毕业时间")
    education = Column(String(16), default="", comment="学历")
    advisor_id = Column(String(32), default="", comment="顾问编号")
    age = Column(Integer, nullable=True, comment="年龄")
    gender = Column(String(4), default="", comment="性别")
    is_deleted = Column(Boolean, default=False, comment="逻辑删除")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    scores = relationship("Score", back_populates="student", lazy="dynamic")
    employment = relationship("Employment", back_populates="student", uselist=False)


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        String(32), ForeignKey("students.student_id"), nullable=False, comment="学号"
    )
    exam_sequence = Column(Integer, nullable=False, comment="考核序次")
    score = Column(Float, nullable=False, comment="成绩")
    created_at = Column(DateTime, default=datetime.now)

    student = relationship("Student", back_populates="scores")


class Employment(Base):
    __tablename__ = "employment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        String(32), ForeignKey("students.student_id"), unique=True, comment="学号"
    )
    name = Column(String(64), default="", comment="学生姓名(冗余)")
    class_name = Column(String(32), default="", comment="学生班级(冗余)")
    employment_open_time = Column(Date, nullable=True, comment="就业开放时间")
    offer_time = Column(Date, nullable=True, comment="offer下发时间")
    company_name = Column(String(128), default="", comment="就业公司名称")
    salary = Column(Float, nullable=True, comment="就业薪资")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    student = relationship("Student", back_populates="employment")


class Class(Base):
    __tablename__ = "classes"

    class_name = Column(String(32), primary_key=True, comment="班级编号/名称")
    start_time = Column(Date, nullable=True, comment="开课时间")
    head_teacher = Column(String(64), default="", comment="班主任")
    instructor = Column(String(64), default="", comment="授课老师")
    created_at = Column(DateTime, default=datetime.now)


class Teacher(Base):
    __tablename__ = "teachers"

    teacher_id = Column(String(32), primary_key=True, comment="教师编号")
    name = Column(String(64), nullable=False, comment="姓名")
    department = Column(String(64), default="", comment="部门")
    title = Column(String(32), default="", comment="职称")
    phone = Column(String(20), default="", comment="联系电话")
    created_at = Column(DateTime, default=datetime.now)


class User(Base):
    __tablename__ = "users"

    user_id = Column(String(32), primary_key=True, comment="用户ID")
    role = Column(Enum(UserRole, values_callable=lambda x: [e.value for e in x]), nullable=False)
    password_hash = Column(String(256), nullable=False)
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)


# ═══════════════════════════════════════════════════════════
# 记忆/安全表
# ═══════════════════════════════════════════════════════════


class L3Cold(Base):
    __tablename__ = "l3_cold"

    cold_id = Column(String(128), primary_key=True)
    student_id = Column(String(32), nullable=False, index=True)
    session_id = Column(String(64), nullable=False)
    raw_dialogue = Column(JSON, nullable=False)
    crisis_flag = Column(Boolean, default=False)
    importance = Column(Float, default=0.5)
    need_reprocess = Column(Boolean, default=False)
    archive_status = Column(String(16), default="hot")
    created_at = Column(DateTime, default=datetime.now)


class SessionArchive(Base):
    __tablename__ = "session_archive"

    session_id = Column(String(64), primary_key=True)
    student_id = Column(String(32), nullable=False, index=True)
    closed_at = Column(DateTime, nullable=False)
    close_reason = Column(String(16), nullable=False)
    summary = Column(Text)
    safety_snapshot = Column(JSON)
    last_intent = Column(String(32))
    last_topic = Column(String(64))
    unclosed_topic = Column(String(256))
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


class StudentProfile(Base):
    __tablename__ = "student_profile"

    student_id = Column(String(32), primary_key=True)
    rolling_summary = Column(Text)
    total_sessions = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    first_interaction_at = Column(DateTime)
    last_interaction_at = Column(DateTime)
    safety_status = Column(String(32), default="normal")
    violation_b1_count = Column(Integer, default=0)
    violation_b2_count = Column(Integer, default=0)
    b2_window_start = Column(DateTime)
    b2_last_decay_time = Column(DateTime)
    account_status = Column(String(16), default="normal")
    updated_at = Column(DateTime, default=datetime.now)


class SecurityLog(Base):
    __tablename__ = "security_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(32), nullable=False, index=True)
    teacher_id = Column(String(32))
    category = Column(String(16), nullable=False)
    risk_level = Column(Integer, nullable=False)
    trigger_type = Column(String(16), nullable=False)
    escalation = Column(String(16), nullable=False)
    original_message_hash = Column(String(64))
    anonymized_summary = Column(String(256))
    new_user_status = Column(String(32))
    created_at = Column(DateTime, default=datetime.now)


class CrisisAlert(Base):
    __tablename__ = "crisis_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(32), nullable=False)
    teacher_id = Column(String(32), nullable=False)
    severity = Column(String(16), nullable=False)
    summary = Column(String(500), nullable=False)
    status = Column(String(16), default="pending")
    triggered_at = Column(DateTime, default=datetime.now)
    confirmed_at = Column(DateTime)
    confirmed_by = Column(String(32))
    resolution = Column(String(500))
    escalated_at = Column(DateTime)


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(String(32), nullable=False)
    action_type = Column(String(32), nullable=False)
    target_type = Column(String(32), nullable=False)
    target_id = Column(String(64))
    action_detail = Column(JSON)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.now)


class ThreadSessionMap(Base):
    __tablename__ = "thread_session_map"

    session_id = Column(String(64), primary_key=True)
    thread_id = Column(String(128), nullable=False)
    student_id = Column(String(32), nullable=False, index=True)
    user_role = Column(String(16), nullable=False)
    carry_over = Column(String(16), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    closed_at = Column(DateTime)


class L2DraftCandidate(Base):
    __tablename__ = "l2_draft_candidates"

    draft_id = Column(String(128), primary_key=True)
    student_id = Column(String(32), nullable=False, index=True)
    trait_name = Column(String(64), nullable=False)
    trait_value = Column(Text, default="")
    source_type = Column(String(32), default="llm_infer")
    write_confidence = Column(Float, default=0.5)
    evidence_l3_ids = Column(JSON)
    consumed = Column(Boolean, default=False)
    drafted_at = Column(DateTime, default=datetime.now)
