"""Pydantic 请求/响应 Schema — API 层与 Service 层的契约"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.domain.enums import (
    CaseRiskLevel,
    EIATopic,
    Intent,
    SafetyCategory,
    RiskLevel,
    AccountStatus,
    CarryOverLevel,
    SourceType,
)


# ── 对话 ──

class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")


class ChatResponse(BaseModel):
    reply: str = Field(..., description="Agent 回复")
    intent: Intent = Field(..., description="情境路由结果")
    safety_flag: Optional[RiskLevel] = None


# ── L3 摘要 ──

class L3SummarySchema(BaseModel):
    """L3-Hot 案例结构化摘要, 写入 Milvus 前校验"""
    l3_id: str
    student_id: str
    session_id: str
    timestamp: int

    risk_level: CaseRiskLevel = CaseRiskLevel.MEDIUM
    risk_confidence: float = Field(ge=0, le=1, default=0.5)
    topic: EIATopic = EIATopic.GENERAL_CONSULTATION
    pollutant: Optional[str] = None
    risk_event: str = ""
    sensitive_target: str = ""
    project_description: str = ""

    importance: float = Field(ge=0, le=1)
    write_confidence: float = Field(ge=0, le=1)
    cold_ref: Optional[str] = None


# ── L2 认知 ──

class L2CognitionSchema(BaseModel):
    """L2 语义认知, Reflection 提取输出"""
    dimension: str
    target: str
    relation_type: str
    content: str
    trend: Optional[str] = None
    intensity: Optional[float] = None
    source_type: SourceType = SourceType.C_REFLECTION
    evidence_ids: list[str] = Field(default_factory=list)
    contradiction_noted: Optional[str] = None


# ── 安全 ──

class SafetyResultSchema(BaseModel):
    """安全过滤结果"""
    risk_level: RiskLevel = RiskLevel.SAFE
    category: SafetyCategory = SafetyCategory.NONE
    escalation: str = "ignore"
    confidence: float = Field(ge=0, le=1)
    response_template: Optional[str] = None
    should_block_memory: bool = False


# ── 会话 ──

class SessionBoundaryResult(BaseModel):
    """会话边界判断结果"""
    is_new_session: bool
    carry_over_level: CarryOverLevel
    time_gap_minutes: float = 0.0
    semantic_continuity: float = 0.0
    user_signal: Optional[str] = None


# ── 教师报告 ──

class StudentProfileReport(BaseModel):
    """学生画像报告"""
    student_id: str
    name: str
    class_name: str
    report_text: str
    generated_at: datetime = Field(default_factory=datetime.now)


class ClassAggregateReport(BaseModel):
    """班级群体聚合报告"""
    class_name: str
    student_count: int
    report_text: str
    generated_at: datetime = Field(default_factory=datetime.now)


# ── 管理员 ──

class AdminAuditRequest(BaseModel):
    student_id: str
    date_range_days: int = Field(default=30, ge=1, le=365)


class AccountControlRequest(BaseModel):
    student_id: str
    action: str = Field(..., description="unblock | reset_violation | force_logout | delete")
    reason: str = Field(..., description="操作原因")


# ── 记忆检索 ──

class RetrievedMemory(BaseModel):
    """统一检索返回格式"""
    source: str = Field(..., description="L0 | L1 | L2 | L3-Hot | L3-Cold")
    confidence_label: str = Field(..., description="高置信 | 中置信 | 低置信")
    confidence_score: float = Field(ge=0, le=1)
    content: str
    metadata: dict = Field(default_factory=dict)
