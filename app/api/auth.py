"""认证接口 — 登录 / 注册"""

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domain.auth_schemas import (
    BatchRegisterRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.domain.enums import UserRole
from app.infrastructure.database import get_db
from app.infrastructure.jwt import create_access_token
from app.infrastructure.security import CurrentUser
from app.models import User, Student, Teacher

router = APIRouter(prefix="/auth", tags=["认证"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


async def _verify_business_record(db: AsyncSession, user_id: str, role: str) -> str:
    """验证用户在其角色对应的业务表中存在，返回用户姓名"""
    if role == "student":
        result = await db.execute(
            select(Student).where(
                Student.student_id == user_id,
                Student.is_deleted == False,  # noqa: E712
            )
        )
        student = result.scalar_one_or_none()
        if not student:
            raise HTTPException(
                status_code=403, detail="该学号不在学生名册中，请联系管理员"
            )
        return student.name

    if role == "teacher":
        result = await db.execute(
            select(Teacher).where(Teacher.teacher_id == user_id)
        )
        teacher = result.scalar_one_or_none()
        if not teacher:
            raise HTTPException(
                status_code=403, detail="该教师编号不在教师名册中，请联系管理员"
            )
        return teacher.name

    # admin 不需要关联业务表
    return "系统管理员"


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    # 1. 查 users 表
    result = await db.execute(
        select(User).where(User.user_id == req.user_id)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if user.disabled:
        raise HTTPException(status_code=401, detail="该账号已被禁用")

    role = user.role.value if hasattr(user.role, "value") else user.role

    # 2. 跨表验证
    name = await _verify_business_record(db, req.user_id, role)

    # 3. 签发 JWT
    token = create_access_token(user_id=req.user_id, role=role, name=name)

    return TokenResponse(
        access_token=token,
        user_id=req.user_id,
        role=role,
        name=name,
    )


@router.post("/register", status_code=201)
async def register(
    req: RegisterRequest,
    admin: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """仅管理员可创建账号"""
    if admin.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="仅管理员可创建账号")

    if req.role not in ("student", "teacher", "admin"):
        raise HTTPException(status_code=400, detail="无效的角色类型")

    # 验证业务表中存在
    await _verify_business_record(db, req.user_id, req.role)

    # 检查 users 表是否已存在
    result = await db.execute(
        select(User).where(User.user_id == req.user_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="该用户已有登录账号")

    new_user = User(
        user_id=req.user_id,
        role=UserRole(req.role),
        password_hash=hash_password(req.password),
    )
    db.add(new_user)
    await db.commit()

    return {"message": f"账号 {req.user_id} 创建成功", "user_id": req.user_id, "role": req.role}


@router.post("/register/batch", status_code=201)
async def batch_register(
    req: BatchRegisterRequest,
    admin: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员批量创建账号"""
    if admin.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="仅管理员可创建账号")

    created = []
    skipped = []
    for uid in req.user_ids:
        result = await db.execute(select(User).where(User.user_id == uid))
        if result.scalar_one_or_none():
            skipped.append(uid)
            continue

        try:
            await _verify_business_record(db, uid, req.role)
        except HTTPException:
            skipped.append(uid)
            continue

        new_user = User(
            user_id=uid,
            role=UserRole(req.role),
            password_hash=hash_password(req.password),
        )
        db.add(new_user)
        created.append(uid)

    await db.commit()
    return {"created": created, "skipped": skipped}


@router.get("/me")
async def me(user: CurrentUser = Depends(get_current_user)):
    """返回当前登录用户信息"""
    return {
        "user_id": user.user_id,
        "role": user.role.value if hasattr(user.role, "value") else user.role,
        "name": user.name,
        "class_name": user.class_name,
        "teacher_id": user.teacher_id,
        "account_status": user.account_status,
    }
