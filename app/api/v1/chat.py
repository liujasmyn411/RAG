import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest
from app.agents.lin_daiyu.agent import chat as agent_chat

router = APIRouter()


async def _sse_generator(session_id: str, message: str):
    """SSE 事件生成器"""
    try:
        async for event in agent_chat(session_id, message):
            yield f"event: {event['event']}\ndata: {json.dumps(event['data'], ensure_ascii=False)}\n\n"
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'message': str(e)}, ensure_ascii=False)}\n\n"


@router.post("/lin-daiyu/chat")
async def chat_endpoint(req: ChatRequest):
    """林黛玉 Agent 对话接口（SSE 流式）
    
    - 首次请求：session_id 留空，返回中会携带新生成的 session_id
    - 继续对话：传入上次返回的 session_id
    """
    return StreamingResponse(
        _sse_generator(req.session_id, req.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
