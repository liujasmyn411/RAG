"""班级管理 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.business_schemas import (
    ClassCreate,
    ClassUpdate,
    ClassResponse,
    MessageResponse,
)
from app.infrastructure.database import get_db
from app.repositories.business_repo import ClassRepo

router = APIRouter(prefix="/classes", tags=["classes"])


@router.get("", response_model=list[ClassResponse])
async def list_classes(
    db: AsyncSession = Depends(get_db),
):
    repo = ClassRepo(db)
    return await repo.list_all()


@router.post("", response_model=ClassResponse, status_code=201)
async def create_class(
    data: ClassCreate,
    db: AsyncSession = Depends(get_db),
):
    repo = ClassRepo(db)
    existing = await repo.get_by_name(data.class_name)
    if existing:
        raise HTTPException(400, f"班级 {data.class_name} 已存在")
    return await repo.create(data.model_dump())


@router.get("/{class_name}", response_model=ClassResponse)
async def get_class(
    class_name: str,
    db: AsyncSession = Depends(get_db),
):
    repo = ClassRepo(db)
    c = await repo.get_by_name(class_name)
    if not c:
        raise HTTPException(404, f"班级 {class_name} 不存在")
    return c


@router.put("/{class_name}", response_model=ClassResponse)
async def update_class(
    class_name: str,
    data: ClassUpdate,
    db: AsyncSession = Depends(get_db),
):
    repo = ClassRepo(db)
    c = await repo.update(class_name, data.model_dump(exclude_none=True))
    if not c:
        raise HTTPException(404, f"班级 {class_name} 不存在")
    return c


@router.delete("/{class_name}", response_model=MessageResponse)
async def delete_class(
    class_name: str,
    db: AsyncSession = Depends(get_db),
):
    repo = ClassRepo(db)
    ok = await repo.delete(class_name)
    if not ok:
        raise HTTPException(404, f"班级 {class_name} 不存在")
    return MessageResponse(message=f"班级 {class_name} 已删除")
