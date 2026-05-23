from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey, text
from sqlalchemy.orm import relationship
from app.models.database import Base


class Advisor(Base):
    __tablename__ = "advisors"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), default=None)
    advisor_no = Column(String(32), unique=True, nullable=False)
    name = Column(String(64), nullable=False)
    phone = Column(String(32))
    email = Column(String(128))
    department_id = Column(BigInteger, ForeignKey("departments.id"))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
