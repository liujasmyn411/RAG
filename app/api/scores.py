"""成绩管理 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.business_schemas import (
    ScoreCreate,
    ScoreUpdate,
    ScoreDelete,
    ScoreResponse,
    MessageResponse,
)
from app.infrastructure.database import get_db
from app.repositories.business_repo import ScoreRepo

router = APIRouter(prefix="/score", tags=["score"])


@router.get("/{stu_id}", response_model=list[ScoreResponse])
async def get_student_scores(
    stu_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = ScoreRepo(db)
    return await repo.get_by_student(stu_id)


@router.post("/", response_model=ScoreResponse, status_code=201)
async def create_score(
    data: ScoreCreate,
    db: AsyncSession = Depends(get_db),
):
    repo = ScoreRepo(db)
    return await repo.create(data.model_dump())


@router.put("/update", response_model=ScoreResponse)
async def update_score(
    data: ScoreUpdate,
    db: AsyncSession = Depends(get_db),
):
    repo = ScoreRepo(db)
    result = await repo.update_score(data.student_id, data.exam_sequence, data.score)
    if not result:
        raise HTTPException(404, "成绩记录不存在")
    return result


@router.post("/delete", response_model=MessageResponse)
async def delete_score(
    data: ScoreDelete,
    db: AsyncSession = Depends(get_db),
):
    repo = ScoreRepo(db)
    ok = await repo.delete_score(data.student_id, data.exam_sequence)
    if not ok:
        raise HTTPException(404, "成绩记录不存在")
    return MessageResponse(message="成绩已删除")
