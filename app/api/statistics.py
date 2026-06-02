"""统计分析 API — 需求 2.6 全部统计端点"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.business_schemas import (
    OlderStudent,
    ClassGenderCount,
    HighScoreStudent,
    FailStats,
    ScoreStats,
    TopSalaryStudent,
    EmploymentDuration,
    ClassAvgDuration,
)
from app.infrastructure.database import get_db
from app.repositories.business_repo import StatisticsRepo

router = APIRouter(prefix="/statistics", tags=["statistics"])


# ═══════════════════════════════════════════════════════════
# 2.6.1 基本信息统计
# ═══════════════════════════════════════════════════════════


@router.get("/students/older-than-30", response_model=list[OlderStudent])
async def students_older_than_30(
    db: AsyncSession = Depends(get_db),
):
    """查询所有超过30岁的学员的信息"""
    repo = StatisticsRepo(db)
    return await repo.get_students_older_than(30)


@router.get("/class/gender-count", response_model=list[ClassGenderCount])
async def class_gender_count(
    db: AsyncSession = Depends(get_db),
):
    """统计每个班级的人数以及男生女生的人数"""
    repo = StatisticsRepo(db)
    return await repo.get_class_gender_counts()


# ═══════════════════════════════════════════════════════════
# 2.6.2 成绩统计
# ═══════════════════════════════════════════════════════════


@router.get("/scores/always-above-80", response_model=list[HighScoreStudent])
async def scores_always_above_80(
    db: AsyncSession = Depends(get_db),
):
    """查询每次考试成绩都在80分以上的学生的编号、姓名和成绩"""
    repo = StatisticsRepo(db)
    return await repo.get_students_always_above_80()


@router.get("/scores/failures", response_model=list[FailStats])
async def scores_multiple_failures(
    db: AsyncSession = Depends(get_db),
):
    """查询有两次以上不及格的学生的姓名、班级和不及格成绩"""
    repo = StatisticsRepo(db)
    return await repo.get_students_with_failures(2)


@router.get("/scores/exam-avg-by-class", response_model=list[ScoreStats])
async def exam_avg_by_class(
    db: AsyncSession = Depends(get_db),
):
    """统计每次考试每个班级的平均分，按照从高到低排序"""
    repo = StatisticsRepo(db)
    return await repo.get_exam_avg_by_class()


# ═══════════════════════════════════════════════════════════
# 2.6.3 就业统计
# ═══════════════════════════════════════════════════════════


@router.get("/employment/top-salary", response_model=list[TopSalaryStudent])
async def employment_top_salary(
    db: AsyncSession = Depends(get_db),
):
    """统计就业薪资最高的前五名学生的姓名、班级、就业时间、就业公司"""
    repo = StatisticsRepo(db)
    return await repo.get_top_salary(5)


@router.get("/employment/duration-per-student", response_model=list[EmploymentDuration])
async def employment_duration_per_student(
    db: AsyncSession = Depends(get_db),
):
    """统计每个学生的就业时长 (offer下发时间 - 就业开放时间)"""
    repo = StatisticsRepo(db)
    return await repo.get_employment_durations()


@router.get("/employment/avg-duration-by-class", response_model=list[ClassAvgDuration])
async def employment_avg_duration_by_class(
    db: AsyncSession = Depends(get_db),
):
    """统计每个班级的平均就业时长 (只统计进入就业阶段的学生)"""
    repo = StatisticsRepo(db)
    return await repo.get_class_avg_employment_duration()
