"""就业管理 API"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.business_schemas import (
    EmploymentCreate,
    EmploymentResponse,
    MessageResponse,
)
from app.infrastructure.database import get_db
from app.repositories.business_repo import EmploymentRepo

router = APIRouter(prefix="/employment", tags=["employment"])


@router.get("/students/{stu_id}", response_model=EmploymentResponse)
async def get_student_employment(
    stu_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = EmploymentRepo(db)
    emp = await repo.get_by_student(stu_id)
    if not emp:
        raise HTTPException(404, f"学生 {stu_id} 暂无就业信息")
    return emp


@router.get("/class/{class_name}", response_model=list[EmploymentResponse])
async def get_class_employment(
    class_name: str,
    db: AsyncSession = Depends(get_db),
):
    repo = EmploymentRepo(db)
    return await repo.get_by_class(class_name)


@router.post("/students/{stu_id}", response_model=EmploymentResponse, status_code=201)
async def upsert_employment(
    stu_id: str,
    data: EmploymentCreate,
    db: AsyncSession = Depends(get_db),
):
    if data.student_id != stu_id:
        data.student_id = stu_id
    repo = EmploymentRepo(db)
    return await repo.upsert(data.model_dump())


@router.delete("/students/{stu_id}", response_model=MessageResponse)
async def delete_employment(
    stu_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = EmploymentRepo(db)
    ok = await repo.delete(stu_id)
    if not ok:
        raise HTTPException(404, f"学生 {stu_id} 暂无就业信息")
    return MessageResponse(message=f"学生 {stu_id} 就业信息已删除")
