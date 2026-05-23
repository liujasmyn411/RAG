from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date


# ============ 通用响应 ============

class ResponseBase(BaseModel):
    code: int = 200
    message: str = "ok"


class DataResponse(ResponseBase):
    data: Optional[dict] = None


# ============ 认证相关 ============

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="用户输入")
    session_id: Optional[str] = Field(None, description="会话 ID，空则新建")


class ChatEvent(BaseModel):
    event: str
    data: dict


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_type: str
    name: str


# ============ 学生相关 ============

class StudentBase(BaseModel):
    student_no: str = Field(..., min_length=1, max_length=32)
    name: str = Field(..., min_length=1, max_length=64)
    class_id: Optional[int] = None
    native_place: Optional[str] = None
    school: Optional[str] = None
    major: Optional[str] = None
    enrollment_date: Optional[date] = None
    graduation_date: Optional[date] = None
    education: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    id_card: Optional[str] = None
    status: str = "studying"


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    class_id: Optional[int] = None
    native_place: Optional[str] = None
    school: Optional[str] = None
    major: Optional[str] = None
    enrollment_date: Optional[date] = None
    graduation_date: Optional[date] = None
    education: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    id_card: Optional[str] = None
    status: Optional[str] = None


class StudentOut(StudentBase):
    id: int
    class_no: Optional[str] = None
    class_name: Optional[str] = None

    class Config:
        from_attributes = True


class StudentListResponse(ResponseBase):
    data: List[StudentOut]
    total: int


# ============ 成绩相关 ============

class ScoreBase(BaseModel):
    student_id: int
    exam_seq: int
    exam_name: Optional[str] = None
    score: float = Field(..., ge=0, le=1000)
    max_score: float = 100
    exam_date: Optional[date] = None


class ScoreCreate(ScoreBase):
    pass


class ScoreUpdate(BaseModel):
    exam_name: Optional[str] = None
    score: Optional[float] = Field(None, ge=0, le=1000)
    max_score: Optional[float] = None
    exam_date: Optional[date] = None


class ScoreOut(ScoreBase):
    id: int
    student_name: Optional[str] = None
    student_no: Optional[str] = None

    class Config:
        from_attributes = True


class ScoreListResponse(ResponseBase):
    data: List[ScoreOut]


# ============ 就业相关 ============

class EmploymentBase(BaseModel):
    student_id: int
    open_date: Optional[date] = None
    offer_date: Optional[date] = None
    company: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[float] = None
    location: Optional[str] = None
    status: str = "employed"


class EmploymentCreate(EmploymentBase):
    pass


class EmploymentUpdate(BaseModel):
    open_date: Optional[date] = None
    offer_date: Optional[date] = None
    company: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[float] = None
    location: Optional[str] = None
    status: Optional[str] = None


class EmploymentOut(BaseModel):
    id: int
    student_id: int
    student_no: Optional[str] = None
    student_name: Optional[str] = None
    student_class: Optional[str] = None
    open_date: Optional[date] = None
    offer_date: Optional[date] = None
    company: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[float] = None
    location: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class EmploymentListResponse(ResponseBase):
    data: List[EmploymentOut]


# ============ 统计相关 ============

class ClassGenderStat(BaseModel):
    class_no: str
    total: int
    male: int
    female: int


class ClassAvgScore(BaseModel):
    class_no: str
    exam_seq: int
    exam_name: Optional[str] = None
    avg_score: float


class TopSalary(BaseModel):
    name: str
    student_no: Optional[str] = None
    class_no: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[float] = None
    offer_date: Optional[str] = None


class StatisticsResponse(ResponseBase):
    data: Optional[List] = None
