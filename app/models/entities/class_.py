from sqlalchemy import Column, Integer, String, Date, DateTime, BigInteger, ForeignKey, text
from sqlalchemy.orm import relationship
from app.models.database import Base


class Class(Base):
    __tablename__ = "classes"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    class_no = Column(String(32), unique=True, nullable=False)
    name = Column(String(128))
    start_date = Column(Date)
    end_date = Column(Date)
    headteacher_id = Column(BigInteger, ForeignKey("teachers.id"))
    instructor_id = Column(BigInteger, ForeignKey("teachers.id"))
    status = Column(String(16), default="active")
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    headteacher = relationship("Teacher", foreign_keys=[headteacher_id])
    instructor = relationship("Teacher", foreign_keys=[instructor_id])
    students = relationship("Student", back_populates="class_")
