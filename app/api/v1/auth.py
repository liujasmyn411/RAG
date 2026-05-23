from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.database import get_db
from app.models.entities import User
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["认证"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_type: str
    name: str


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录

    返回 JWT Token，用于后续接口鉴权。
    """
    user = db.query(User).filter(User.username == form_data.username, User.is_active == 1).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 开发阶段兼容 placeholder 密码（未设置真实密码时允许通过）
    is_valid = False
    if user.password_hash.startswith("$2b$") or user.password_hash.startswith("$2a$"):
        is_valid = verify_password(form_data.password, user.password_hash)
    elif user.password_hash == "$2b$12$placeholder":
        # 开发兜底：placeholder 密码直接通过
        is_valid = True

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "user_type": user.user_type,
            "role_id": user.role_id,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": user.user_type,
        "name": user.name,
    }
