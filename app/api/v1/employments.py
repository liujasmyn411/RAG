from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.entities import Employment, Student, Class, User
from app.models.schemas import (
    EmploymentCreate, EmploymentUpdate, EmploymentOut,
    EmploymentListResponse, ResponseBase
)
from app.core.dependencies import get_current_user, require_teacher

router = APIRouter(prefix="/employments", tags=["就业管理"])


def _employment_to_out(emp: Employment) -> EmploymentOut:
    student = emp.student
    class_no = student.class_.class_no if student and student.class_ else None
    return EmploymentOut(
        id=emp.id,
        student_id=emp.student_id,
        student_no=student.student_no if student else None,
        student_name=student.name if student else None,
        student_class=class_no,
        open_date=emp.open_date,
        offer_date=emp.offer_date,
        company=emp.company,
        position=emp.position,
        salary=float(emp.salary) if emp.salary else None,
        location=emp.location,
        status=emp.status,
    )


@router.get("/student/{student_no}", response_model=Optional[EmploymentOut])
def get_employment_by_student(
    student_no: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取指定学生的就业信息"""
    student = db.query(Student).filter(Student.student_no == student_no, Student.is_deleted == 0).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    emp = db.query(Employment).filter(Employment.student_id == student.id).first()
    if not emp:
        return None
    return _employment_to_out(emp)


@router.get("/class/{class_no}", response_model=EmploymentListResponse)
def list_employments_by_class(
    class_no: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取班级学生的就业信息"""
    cls = db.query(Class).filter(Class.class_no == class_no).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")

    emps = (
        db.query(Employment)
        .join(Student, Employment.student_id == Student.id)
        .filter(Student.class_id == cls.id, Student.is_deleted == 0)
        .all()
    )
    return EmploymentListResponse(data=[_employment_to_out(e) for e in emps])


@router.post("", response_model=EmploymentOut, status_code=status.HTTP_201_CREATED)
def create_employment(
    data: EmploymentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
):
    """添加就业信息"""
    student = db.query(Student).filter(Student.id == data.student_id, Student.is_deleted == 0).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    existing = db.query(Employment).filter(Employment.student_id == data.student_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="该学生已有就业记录")

    emp = Employment(**data.model_dump())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return _employment_to_out(emp)


@router.put("/{employment_id}", response_model=EmploymentOut)
def update_employment(
    employment_id: int,
    data: EmploymentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
):
    """修改就业信息"""
    emp = db.query(Employment).filter(Employment.id == employment_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="就业记录不存在")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(emp, field, value)

    db.commit()
    db.refresh(emp)
    return _employment_to_out(emp)


@router.delete("/{employment_id}", response_model=ResponseBase)
def delete_employment(
    employment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
):
    """删除就业信息"""
    emp = db.query(Employment).filter(Employment.id == employment_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="就业记录不存在")

    db.delete(emp)
    db.commit()
    return ResponseBase(message="删除成功")
