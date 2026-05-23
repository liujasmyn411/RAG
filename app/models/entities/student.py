from sqlalchemy import Column, Integer, String, Date, DateTime, BigInteger, ForeignKey, text
from sqlalchemy.orm import relationship
from app.models.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), default=None)
    student_no = Column(String(32), unique=True, nullable=False)
    name = Column(String(64), nullable=False)
    class_id = Column(BigInteger, ForeignKey("classes.id"))
    native_place = Column(String(128))
    school = Column(String(128))
    major = Column(String(128))
    enrollment_date = Column(Date)
    graduation_date = Column(Date)
    education = Column(String(32))
    advisor_id = Column(BigInteger, ForeignKey("advisors.id"))
    age = Column(Integer)
    gender = Column(String(8))
    phone = Column(String(32))
    email = Column(String(128))
    id_card = Column(String(18))
    status = Column(String(16), default="studying")
    is_deleted = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    class_ = relationship("Class", back_populates="students")
    scores = relationship("Score", back_populates="student", cascade="all, delete-orphan")
    employment = relationship("Employment", back_populates="student", uselist=False, cascade="all, delete-orphan")
