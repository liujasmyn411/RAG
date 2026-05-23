from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.entities import Student, Class, User
from app.models.schemas import (
    StudentCreate, StudentUpdate, StudentOut, StudentListResponse, ResponseBase
)
from app.core.dependencies import get_current_user, require_teacher

router = APIRouter(prefix="/students", tags=["学生管理"])


def _student_to_out(student: Student) -> StudentOut:
    return StudentOut(
        id=student.id,
        student_no=student.student_no,
        name=student.name,
        class_id=student.class_id,
        class_no=student.class_.class_no if student.class_ else None,
        class_name=student.class_.name if student.class_ else None,
        native_place=student.native_place,
        school=student.school,
        major=student.major,
        enrollment_date=student.enrollment_date,
        graduation_date=student.graduation_date,
        education=student.education,
        age=student.age,
        gender=student.gender,
        phone=student.phone,
        email=student.email,
        id_card=student.id_card,
        status=student.status,
    )


def _get_student_query(db: Session, user: User):
    """根据用户角色返回查询范围"""
    base_query = db.query(Student).filter(Student.is_deleted == 0)
    if user.user_type == "admin":
        return base_query
    # 老师和学生的范围过滤后续细化
    return base_query


@router.get("", response_model=StudentListResponse)
def list_students(
    class_id: Optional[int] = Query(None, description="按班级筛选"),
    keyword: Optional[str] = Query(None, description="按姓名或学号模糊搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取学生列表（支持分页、筛选、搜索）"""
    query = _get_student_query(db, user)

    if class_id:
        query = query.filter(Student.class_id == class_id)
    if keyword:
        query = query.filter(
            (Student.name.like(f"%{keyword}%")) |
            (Student.student_no.like(f"%{keyword}%"))
        )

    total = query.count()
    students = query.offset((page - 1) * page_size).limit(page_size).all()

    return StudentListResponse(
        data=[_student_to_out(s) for s in students],
        total=total,
    )


@router.get("/{student_id}", response_model=StudentOut)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取单个学生详情"""
    student = _get_student_query(db, user).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    return _student_to_out(student)


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(
    data: StudentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
):
    """创建学生"""
    # 检查学号唯一
    if db.query(Student).filter(Student.student_no == data.student_no).first():
        raise HTTPException(status_code=400, detail="学号已存在")

    student = Student(**data.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return _student_to_out(student)


@router.put("/{student_id}", response_model=StudentOut)
def update_student(
    student_id: int,
    data: StudentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
):
    """更新学生信息"""
    student = db.query(Student).filter(Student.id == student_id, Student.is_deleted == 0).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)

    db.commit()
    db.refresh(student)
    return _student_to_out(student)


@router.delete("/{student_id}", response_model=ResponseBase)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
):
    """逻辑删除学生"""
    student = db.query(Student).filter(Student.id == student_id, Student.is_deleted == 0).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    student.is_deleted = 1
    db.commit()
    return ResponseBase(message="删除成功")
