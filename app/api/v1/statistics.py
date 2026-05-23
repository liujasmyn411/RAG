from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.entities import User
from app.models.schemas import (
    StatisticsResponse, ClassGenderStat, ClassAvgScore, TopSalary,
)
from app.core.dependencies import get_current_user
from app.services.student_service import StudentService

router = APIRouter(prefix="/statistics", tags=["统计分析"])


@router.get("/class-gender", response_model=StatisticsResponse)
def class_gender_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """各班级人数及性别分布"""
    svc = StudentService(db)
    data = svc.get_class_gender_stats()
    return StatisticsResponse(data=data)


@router.get("/excellent-students", response_model=StatisticsResponse)
def excellent_students(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """每次考试都在80分以上的学生"""
    svc = StudentService(db)
    data = svc.get_always_excellent_students()
    return StatisticsResponse(data=data)


@router.get("/multiple-failures", response_model=StatisticsResponse)
def multiple_failures(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """两次以上不及格的学生"""
    svc = StudentService(db)
    data = svc.get_multiple_failures()
    return StatisticsResponse(data=data)


@router.get("/class-avg-score", response_model=StatisticsResponse)
def class_avg_score(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """各班级每次考试平均分"""
    svc = StudentService(db)
    data = svc.get_class_average_scores()
    return StatisticsResponse(data=data)


@router.get("/top-salary", response_model=StatisticsResponse)
def top_salary(
    limit: int = 5,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """就业薪资排行"""
    svc = StudentService(db)
    data = svc.get_top_employment_salary(limit=limit)
    return StatisticsResponse(data=data)


@router.get("/employment-duration", response_model=StatisticsResponse)
def employment_duration(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """各学生就业时长"""
    svc = StudentService(db)
    data = svc.get_student_employment_duration()
    return StatisticsResponse(data=data)


@router.get("/class-avg-employment-duration", response_model=StatisticsResponse)
def class_avg_employment_duration(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """各班级平均就业时长"""
    svc = StudentService(db)
    data = svc.get_class_average_employment_duration()
    return StatisticsResponse(data=data)


@router.get("/students-over-30", response_model=StatisticsResponse)
def students_over_30(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """超过30岁的学员"""
    svc = StudentService(db)
    data = svc.get_students_over_30()
    result = []
    for s in data:
        result.append({
            "student_no": s.student_no,
            "name": s.name,
            "age": s.age,
            "class_no": s.class_.class_no if s.class_ else None,
        })
    return StatisticsResponse(data=result)
