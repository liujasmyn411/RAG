"""管理员接口"""

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_admin_service, get_current_user
from app.domain.schemas import AccountControlRequest
from app.domain.enums import UserRole
from app.infrastructure.security import CurrentUser

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/audit/l3")
async def audit_l3(
    student_id: str,
    days: int = 30,
    user: CurrentUser = Depends(get_current_user),
) -> list[dict]:
    if user.role != UserRole.ADMIN:
        raise HTTPException(403, "仅管理员可查看")

    service = get_admin_service()
    return await service.audit_l3_raw(student_id, user.user_id, days)


@router.post("/account/control")
async def account_control(
    req: AccountControlRequest,
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    if user.role != UserRole.ADMIN:
        raise HTTPException(403, "仅管理员可操作")

    service = get_admin_service()
    return await service.account_control(
        req.student_id, req.action, req.reason, user.user_id
    )


@router.post("/knowledge")
async def knowledge_manage(
    action: str,
    data: dict,
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    if user.role != UserRole.ADMIN:
        raise HTTPException(403, "仅管理员可操作")

    service = get_admin_service()
    return await service.knowledge_manage(action, data, user.user_id)


@router.get("/security-logs/{student_id}")
async def get_security_logs(
    student_id: str,
    category: str | None = None,
    days: int = 30,
    user: CurrentUser = Depends(get_current_user),
) -> list[dict]:
    if user.role != UserRole.ADMIN:
        raise HTTPException(403, "仅管理员可查看")

    service = get_admin_service()
    return await service.get_security_logs(student_id, category, days)
