"""JWT 签发与验证"""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from app.infrastructure.config import get_settings

_settings = get_settings()
SECRET_KEY = _settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8


def create_access_token(user_id: str, role: str, name: str = "") -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "role": role,
        "name": name,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
