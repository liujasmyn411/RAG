"""认证相关 Pydantic 模型"""

from typing import Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    user_id: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    name: str


class RegisterRequest(BaseModel):
    user_id: str
    password: str
    role: str  # student / teacher / admin


class BatchRegisterRequest(BaseModel):
    """管理员批量创建账号"""
    user_ids: list[str]
    password: str = "123456"
    role: str
