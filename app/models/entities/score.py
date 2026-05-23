from sqlalchemy import Column, Integer, String, Date, DateTime, BigInteger, ForeignKey, Numeric, text
from sqlalchemy.orm import relationship
from app.models.database import Base


class Score(Base):
    __tablename__ = "scores"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    student_id = Column(BigInteger, ForeignKey("students.id"), nullable=False)
    exam_seq = Column(Integer, nullable=False)
    exam_name = Column(String(64))
    score = Column(Numeric(5, 2), nullable=False)
    max_score = Column(Numeric(5, 2), default=100)
    exam_date = Column(Date)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    student = relationship("Student", back_populates="scores")
