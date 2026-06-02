"""学生信息管理 API"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.business_schemas import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    MessageResponse,
)
from app.infrastructure.database import get_db
from app.repositories.business_repo import StudentRepo

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=list[StudentResponse])
async def list_students(
    student_id: Optional[str] = Query(default=None, description="按学号筛选"),
    name: Optional[str] = Query(default=None, description="按姓名筛选"),
    class_name: Optional[str] = Query(default=None, description="按班级筛选"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    repo = StudentRepo(db)
    students, _ = await repo.list_all(
        student_id=student_id, name=name, class_name=class_name,
        skip=skip, limit=limit,
    )
    return students


@router.post("", response_model=StudentResponse, status_code=201)
async def create_student(
    data: StudentCreate,
    db: AsyncSession = Depends(get_db),
):
    repo = StudentRepo(db)
    existing = await repo.get_by_id(data.student_id)
    if existing:
        raise HTTPException(400, f"学生 {data.student_id} 已存在")
    return await repo.create(data.model_dump())


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = StudentRepo(db)
    student = await repo.get_by_id(student_id)
    if not student:
        raise HTTPException(404, f"学生 {student_id} 不存在")
    return student


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: str,
    data: StudentUpdate,
    db: AsyncSession = Depends(get_db),
):
    repo = StudentRepo(db)
    student = await repo.update(student_id, data.model_dump(exclude_none=True))
    if not student:
        raise HTTPException(404, f"学生 {student_id} 不存在")
    return student


@router.delete("/{student_id}", response_model=MessageResponse)
async def delete_student(
    student_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = StudentRepo(db)
    ok = await repo.soft_delete(student_id)
    if not ok:
        raise HTTPException(404, f"学生 {student_id} 不存在")
    return MessageResponse(message=f"学生 {student_id} 已删除")
