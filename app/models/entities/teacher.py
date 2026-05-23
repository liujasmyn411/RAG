from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey, text
from app.models.database import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), default=None)
    teacher_no = Column(String(32), unique=True, nullable=False)
    name = Column(String(64), nullable=False)
    phone = Column(String(32))
    email = Column(String(128))
    info = Column(String(512))
    status = Column(String(16), default="active")
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
