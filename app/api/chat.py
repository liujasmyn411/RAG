"""学生对话接口 POST /chat/send"""

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_chat_service, get_current_user
from app.domain.schemas import ChatRequest, ChatResponse
from app.domain.enums import UserRole, AccountStatus
from app.infrastructure.security import CurrentUser

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/send", response_model=ChatResponse)
async def chat_send(
    req: ChatRequest,
    user: CurrentUser = Depends(get_current_user),
) -> ChatResponse:
    if user.role != UserRole.STUDENT:
        raise HTTPException(403, "仅学生用户可使用此接口")

    if user.account_status == AccountStatus.BLOCKED.value:
        raise HTTPException(403, "账号已被限制, 请联系管理员")

    chat_service = get_chat_service()
    return await chat_service.handle_message(
        message=req.message,
        student_id=user.user_id,
        teacher_id=user.teacher_id or "",
    )
