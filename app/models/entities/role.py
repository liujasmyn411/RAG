from sqlalchemy import Column, Integer, String, DateTime, text
from app.models.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    role_code = Column(String(32), unique=True, nullable=False)
    role_name = Column(String(64), nullable=False)
    description = Column(String(256))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
