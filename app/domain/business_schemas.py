"""业务 CRUD 的 Pydantic 请求/响应 Schema"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
# 学生
# ═══════════════════════════════════════════════════════════


class StudentCreate(BaseModel):
    student_id: str = Field(..., description="学号")
    name: str = Field(..., description="姓名")
    class_name: str = Field(..., description="班级")
    hometown: str = Field(default="", description="籍贯")
    graduated_school: str = Field(default="", description="毕业院校")
    major: str = Field(default="", description="专业")
    enrollment_date: Optional[date] = Field(default=None, description="入学时间")
    graduation_date: Optional[date] = Field(default=None, description="毕业时间")
    education: str = Field(default="", description="学历")
    advisor_id: str = Field(default="", description="顾问编号")
    age: Optional[int] = Field(default=None, description="年龄")
    gender: str = Field(default="", description="性别")


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, description="姓名")
    class_name: Optional[str] = Field(default=None, description="班级")
    hometown: Optional[str] = Field(default=None, description="籍贯")
    graduated_school: Optional[str] = Field(default=None, description="毕业院校")
    major: Optional[str] = Field(default=None, description="专业")
    enrollment_date: Optional[date] = Field(default=None, description="入学时间")
    graduation_date: Optional[date] = Field(default=None, description="毕业时间")
    education: Optional[str] = Field(default=None, description="学历")
    advisor_id: Optional[str] = Field(default=None, description="顾问编号")
    age: Optional[int] = Field(default=None, description="年龄")
    gender: Optional[str] = Field(default=None, description="性别")


class StudentResponse(BaseModel):
    student_id: str
    name: str
    class_name: str
    hometown: str
    graduated_school: str
    major: str
    enrollment_date: Optional[date] = None
    graduation_date: Optional[date] = None
    education: str
    advisor_id: str
    age: Optional[int] = None
    gender: str
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class StudentListParams(BaseModel):
    student_id: Optional[str] = Field(default=None, description="按学号筛选")
    name: Optional[str] = Field(default=None, description="按姓名筛选")
    class_name: Optional[str] = Field(default=None, description="按班级筛选")
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=500)


# ═══════════════════════════════════════════════════════════
# 成绩
# ═══════════════════════════════════════════════════════════


class ScoreCreate(BaseModel):
    student_id: str = Field(..., description="学号")
    exam_sequence: int = Field(..., description="考核序次")
    score: float = Field(..., description="成绩")


class ScoreUpdate(BaseModel):
    student_id: str = Field(..., description="学号")
    exam_sequence: int = Field(..., description="考核序次")
    score: float = Field(..., description="新成绩")


class ScoreDelete(BaseModel):
    student_id: str = Field(..., description="学号")
    exam_sequence: int = Field(..., description="考核序次")


class ScoreResponse(BaseModel):
    id: int
    student_id: str
    exam_sequence: int
    score: float
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
# 就业
# ═══════════════════════════════════════════════════════════


class EmploymentCreate(BaseModel):
    student_id: str = Field(..., description="学号")
    name: str = Field(default="", description="学生姓名(冗余)")
    class_name: str = Field(default="", description="学生班级(冗余)")
    employment_open_time: Optional[date] = Field(default=None, description="就业开放时间")
    offer_time: Optional[date] = Field(default=None, description="offer下发时间")
    company_name: str = Field(default="", description="就业公司名称")
    salary: Optional[float] = Field(default=None, description="就业薪资")


class EmploymentQuery(BaseModel):
    student_id: Optional[str] = Field(default=None, description="按学号筛选")
    company_name: Optional[str] = Field(default=None, description="按公司名筛选")
    salary_min: Optional[float] = Field(default=None, description="最低薪资")
    salary_max: Optional[float] = Field(default=None, description="最高薪资")
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=500)


class EmploymentResponse(BaseModel):
    id: int
    student_id: str
    name: str
    class_name: str
    employment_open_time: Optional[date] = None
    offer_time: Optional[date] = None
    company_name: str
    salary: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
# 班级
# ═══════════════════════════════════════════════════════════


class ClassCreate(BaseModel):
    class_name: str = Field(..., description="班级编号/名称")
    start_time: Optional[date] = Field(default=None, description="开课时间")
    head_teacher: str = Field(default="", description="班主任")
    instructor: str = Field(default="", description="授课老师")


class ClassUpdate(BaseModel):
    start_time: Optional[date] = Field(default=None, description="开课时间")
    head_teacher: Optional[str] = Field(default=None, description="班主任")
    instructor: Optional[str] = Field(default=None, description="授课老师")


class ClassResponse(BaseModel):
    class_name: str
    start_time: Optional[date] = None
    head_teacher: str
    instructor: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
# 教师
# ═══════════════════════════════════════════════════════════


class TeacherCreate(BaseModel):
    teacher_id: str = Field(..., description="教师编号")
    name: str = Field(..., description="姓名")
    department: str = Field(default="", description="部门")
    title: str = Field(default="", description="职称")
    phone: str = Field(default="", description="联系电话")


class TeacherUpdate(BaseModel):
    name: Optional[str] = Field(default=None, description="姓名")
    department: Optional[str] = Field(default=None, description="部门")
    title: Optional[str] = Field(default=None, description="职称")
    phone: Optional[str] = Field(default=None, description="联系电话")


class TeacherResponse(BaseModel):
    teacher_id: str
    name: str
    department: str
    title: str
    phone: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
# 统计
# ═══════════════════════════════════════════════════════════


class ScoreStats(BaseModel):
    """每次考试每个班级的平均分"""
    class_name: str
    exam_sequence: int
    avg_score: float
    student_count: int


class FailStats(BaseModel):
    """有两次以上不及格的学生"""
    student_id: str
    name: str
    class_name: str
    fail_count: int
    fail_scores: list[float]


class HighScoreStudent(BaseModel):
    """每次考试都在80分以上的学生"""
    student_id: str
    name: str
    scores: list[dict]


class EmploymentDuration(BaseModel):
    """就业时长统计"""
    student_id: str
    name: str
    class_name: str
    open_time: Optional[date] = None
    offer_time: Optional[date] = None
    duration_days: Optional[int] = None


class TopSalaryStudent(BaseModel):
    """薪资前五"""
    student_id: str
    name: str
    class_name: str
    offer_time: Optional[date] = None
    company_name: str
    salary: float


class ClassAvgDuration(BaseModel):
    """班级平均就业时长"""
    class_name: str
    avg_duration_days: float
    student_count: int


class ClassGenderCount(BaseModel):
    """班级性别统计"""
    class_name: str
    total: int
    male: int
    female: int


class OlderStudent(BaseModel):
    """超过30岁的学生"""
    student_id: str
    name: str
    class_name: str
    age: int
    gender: str


class MessageResponse(BaseModel):
    message: str
