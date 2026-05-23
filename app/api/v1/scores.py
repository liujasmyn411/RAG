from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.entities import Score, Student, User
from app.models.schemas import (
    ScoreCreate, ScoreUpdate, ScoreOut, ScoreListResponse, ResponseBase
)
from app.core.dependencies import get_current_user, require_teacher

router = APIRouter(prefix="/scores", tags=["成绩管理"])


def _score_to_out(score: Score) -> ScoreOut:
    return ScoreOut(
        id=score.id,
        student_id=score.student_id,
        student_name=score.student.name if score.student else None,
        student_no=score.student.student_no if score.student else None,
        exam_seq=score.exam_seq,
        exam_name=score.exam_name,
        score=float(score.score),
        max_score=float(score.max_score),
        exam_date=score.exam_date,
    )


@router.get("/student/{student_no}", response_model=ScoreListResponse)
def list_scores_by_student(
    student_no: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取指定学生的所有成绩"""
    student = db.query(Student).filter(Student.student_no == student_no, Student.is_deleted == 0).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    scores = db.query(Score).filter(Score.student_id == student.id).order_by(Score.exam_seq).all()
    return ScoreListResponse(data=[_score_to_out(s) for s in scores])


@router.post("", response_model=ScoreOut, status_code=status.HTTP_201_CREATED)
def create_score(
    data: ScoreCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
):
    """录入成绩"""
    student = db.query(Student).filter(Student.id == data.student_id, Student.is_deleted == 0).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 检查同一序次是否已存在
    existing = db.query(Score).filter(
        Score.student_id == data.student_id,
        Score.exam_seq == data.exam_seq
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该考核序次的成绩已存在")

    score = Score(**data.model_dump())
    db.add(score)
    db.commit()
    db.refresh(score)
    return _score_to_out(score)


@router.put("/{score_id}", response_model=ScoreOut)
def update_score(
    score_id: int,
    data: ScoreUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
):
    """修改成绩"""
    score = db.query(Score).filter(Score.id == score_id).first()
    if not score:
        raise HTTPException(status_code=404, detail="成绩记录不存在")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(score, field, value)

    db.commit()
    db.refresh(score)
    return _score_to_out(score)


@router.delete("/{score_id}", response_model=ResponseBase)
def delete_score(
    score_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
):
    """删除成绩"""
    score = db.query(Score).filter(Score.id == score_id).first()
    if not score:
        raise HTTPException(status_code=404, detail="成绩记录不存在")

    db.delete(score)
    db.commit()
    return ResponseBase(message="删除成功")
