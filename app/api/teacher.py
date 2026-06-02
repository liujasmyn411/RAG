"""教师查询接口"""

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_teacher_service, get_current_user
from app.domain.schemas import StudentProfileReport, ClassAggregateReport
from app.domain.enums import UserRole
from app.infrastructure.security import CurrentUser

router = APIRouter(prefix="/teacher", tags=["teacher"])


@router.get("/student/{student_id}", response_model=StudentProfileReport)
async def get_student_profile(
    student_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> StudentProfileReport:
    if user.role not in (UserRole.TEACHER, UserRole.ADMIN):
        raise HTTPException(403, "仅教师/管理员可查看")

    service = get_teacher_service()
    return await service.student_profile_report(student_id)


@router.get("/class/{class_name}/stats", response_model=ClassAggregateReport)
async def get_class_stats(
    class_name: str,
    user: CurrentUser = Depends(get_current_user),
) -> ClassAggregateReport:
    if user.role not in (UserRole.TEACHER, UserRole.ADMIN):
        raise HTTPException(403, "仅教师/管理员可查看")

    service = get_teacher_service()
    return await service.class_aggregate(class_name)


@router.get("/alerts")
async def get_crisis_alerts(
    user: CurrentUser = Depends(get_current_user),
) -> list[dict]:
    if user.role not in (UserRole.TEACHER, UserRole.ADMIN):
        raise HTTPException(403, "仅教师/管理员可查看")

    service = get_teacher_service()
    return await service.crisis_alerts(user.user_id)
