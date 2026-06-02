"""教师管理 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.business_schemas import (
    TeacherCreate,
    TeacherUpdate,
    TeacherResponse,
    MessageResponse,
)
from app.infrastructure.database import get_db
from app.repositories.business_repo import TeacherRepo

router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.get("", response_model=list[TeacherResponse])
async def list_teachers(
    db: AsyncSession = Depends(get_db),
):
    repo = TeacherRepo(db)
    return await repo.list_all()


@router.post("", response_model=TeacherResponse, status_code=201)
async def create_teacher(
    data: TeacherCreate,
    db: AsyncSession = Depends(get_db),
):
    repo = TeacherRepo(db)
    existing = await repo.get_by_id(data.teacher_id)
    if existing:
        raise HTTPException(400, f"教师 {data.teacher_id} 已存在")
    return await repo.create(data.model_dump())


@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(
    teacher_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = TeacherRepo(db)
    t = await repo.get_by_id(teacher_id)
    if not t:
        raise HTTPException(404, f"教师 {teacher_id} 不存在")
    return t


@router.put("/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(
    teacher_id: str,
    data: TeacherUpdate,
    db: AsyncSession = Depends(get_db),
):
    repo = TeacherRepo(db)
    t = await repo.update(teacher_id, data.model_dump(exclude_none=True))
    if not t:
        raise HTTPException(404, f"教师 {teacher_id} 不存在")
    return t


@router.delete("/{teacher_id}", response_model=MessageResponse)
async def delete_teacher(
    teacher_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = TeacherRepo(db)
    ok = await repo.delete(teacher_id)
    if not ok:
        raise HTTPException(404, f"教师 {teacher_id} 不存在")
    return MessageResponse(message=f"教师 {teacher_id} 已删除")
