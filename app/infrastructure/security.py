"""JWT 鉴权 + 角色校验"""

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import UserRole
from app.infrastructure.database import get_db
from app.infrastructure.jwt import decode_access_token
from app.models import Student, Teacher, User


@dataclass
class CurrentUser:
    user_id: str
    role: UserRole
    name: str = ""
    class_name: Optional[str] = None
    teacher_id: Optional[str] = None
    account_status: str = "normal"


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """从 Authorization header 解析 JWT，返回当前用户。

    支持两种传 token 方式（优先级从高到低）：
    1. Authorization: Bearer <token> header
    2. ?token=<token> query 参数（前端兼容）
    """
    token = None

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    else:
        token = request.query_params.get("token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌，请先登录",
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌无效或已过期，请重新登录",
        )

    user_id = payload.get("sub")
    role_str = payload.get("role")
    if not user_id or not role_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌格式错误")

    # 查 users 表确认账号未被禁用
    result = await db.execute(select(User).where(User.user_id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user or db_user.disabled:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号不存在或已被禁用")

    role = db_user.role
    if hasattr(role, "value"):
        role = role.value
    try:
        role_enum = UserRole(role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的角色类型")

    # 查业务表获取详细信息
    name = ""
    class_name = None
    teacher_id = None
    account_status = "normal"

    if role_enum == UserRole.STUDENT:
        result = await db.execute(
            select(Student).where(
                Student.student_id == user_id,
                Student.is_deleted == False,  # noqa: E712
            )
        )
        student = result.scalar_one_or_none()
        if student:
            name = student.name
            class_name = student.class_name
            teacher_id = student.advisor_id

    elif role_enum == UserRole.TEACHER:
        result = await db.execute(
            select(Teacher).where(Teacher.teacher_id == user_id)
        )
        teacher = result.scalar_one_or_none()
        if teacher:
            name = teacher.name

    # 如果是 admin，name 直接给管理员
    if not name:
        name = payload.get("name", user_id)

    return CurrentUser(
        user_id=user_id,
        role=role_enum,
        name=name,
        class_name=class_name,
        teacher_id=teacher_id,
        account_status=account_status,
    )


def require_role(user: CurrentUser, *roles: UserRole) -> bool:
    return user.role in roles


def require_student(user: CurrentUser) -> bool:
    return user.role == UserRole.STUDENT


def require_teacher(user: CurrentUser) -> bool:
    return user.role == UserRole.TEACHER


def require_admin(user: CurrentUser) -> bool:
    return user.role == UserRole.ADMIN
