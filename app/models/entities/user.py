from sqlalchemy import Column, Integer, String, DateTime, BigInteger, text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role_id = Column(BigInteger, ForeignKey("roles.id"), nullable=False)
    user_type = Column(String(16), nullable=False)
    ref_id = Column(BigInteger, default=None)
    name = Column(String(64), nullable=False)
    avatar = Column(String(256))
    last_login = Column(DateTime)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    role = relationship("Role")
