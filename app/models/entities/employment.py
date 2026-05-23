from sqlalchemy import Column, Integer, String, Date, DateTime, BigInteger, ForeignKey, Numeric, text
from sqlalchemy.orm import relationship
from app.models.database import Base


class Employment(Base):
    __tablename__ = "employments"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    student_id = Column(BigInteger, ForeignKey("students.id"), nullable=False)
    open_date = Column(Date)
    offer_date = Column(Date)
    company = Column(String(128))
    position = Column(String(128))
    salary = Column(Numeric(10, 2))
    location = Column(String(128))
    status = Column(String(16), default="employed")
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    student = relationship("Student", back_populates="employment")
