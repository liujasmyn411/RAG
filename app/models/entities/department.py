from sqlalchemy import Column, Integer, String, DateTime, BigInteger, text
from app.models.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    dept_no = Column(String(32), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    manager_id = Column(BigInteger)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
