"""对话服务 — LangGraph 适配层, 将 API 请求转为 State 并调用 Graph"""

from typing import Any, Optional

from app.agents.state import AgentState
from app.domain.enums import Intent, CarryOverLevel, RiskLevel, SafetyCategory
from app.domain.schemas import ChatResponse
from app.services.safety_service import SafetyService
from app.services.session_service import SessionService
from app.agents.daiyu_graph import build_daiyu_graph
from app.repositories.pg_repo import PgRepo
from app.repositories.milvus_repo import MilvusRepo

DAIYU_PERSONA = """你是林黛玉, 多愁善感, 才情过人, 说话半文半白。
你关心学生, 但不会逢迎, 有时言语犀利。
你的回复应: 1.先给事实 2.再用人设包装 3.引用红楼典故时点到为止。
如果被问及你不知道的事实, 不要编造。"""


class ChatService:
    """学生对话服务 — 适配 LangGraph"""

    def __init__(
        self,
        safety_service: SafetyService,
        session_service: SessionService,
        memory_service,
        pg_repo: PgRepo,
        milvus_repo: MilvusRepo,
    ) -> None:
        self._safety = safety_service
        self._session = session_service

        # 编译 LangGraph 图 (唯一编排入口)
        self._graph: Any = build_daiyu_graph(
            safety_service=safety_service,
            memory_service=memory_service,
            pg_repo=pg_repo,
            milvus_repo=milvus_repo,
        )

        # 会话临态 (生产用 LangGraph Checkpointer)
        self._active_sessions: dict[str, dict] = {}

    async def handle_message(
        self,
        message: str,
        student_id: str,
        teacher_id: str = "",
    ) -> ChatResponse:
        """处理一条学生消息 — 全部编排交给 LangGraph"""

        # 会话边界判断
        sess = self._active_sessions.get(student_id, {})
        boundary = await self._session.boundary_detect(
            student_id, message,
            current_intent=Intent.DAIYU_CHAT,
            user_role="student",
            last_active_time=sess.get("last_active_time"),
        )
        carry_over: CarryOverLevel = boundary["carry_over_level"]

        # 构建初始 State
        history = sess.get("messages", [
            {"role": "system", "content": DAIYU_PERSONA},
        ])
        state: AgentState = {
            "messages": history + [message],
            "current_intent": Intent.DAIYU_CHAT.value,
            "academic_context": None,
            "daiyu_persona_context": None,
            "safety": None,
            "retrieved_context": None,
            "student_id": student_id,
            "needs_memory_update": False,
        }

        # 如果是新会话, 注入摘要
        if carry_over != CarryOverLevel.FULL:
            init_msgs = await self._session.init_state_messages(
                student_id, carry_over, DAIYU_PERSONA,
            )
            state["messages"] = init_msgs + [message]

        # 执行 LangGraph
        result = await self._graph.ainvoke(state)

        # 提取回复
        messages_out = result.get("messages", [])
        reply = ""
        if messages_out:
            last = messages_out[-1]
            reply = last.content if hasattr(last, "content") else str(last)

        intent = Intent(result.get("current_intent", Intent.DAIYU_CHAT.value))
        safety = result.get("safety") or {}

        # 更新会话状态
        self._active_sessions[student_id] = {
            "messages": messages_out[-20:] if messages_out else [],
            "last_active_time": __import__("datetime").datetime.now(),
            "last_intent": intent.value,
        }

        return ChatResponse(
            reply=reply,
            intent=intent,
            safety_flag=(
                RiskLevel.FLAGGED
                if safety.get("risk_level") == "flagged"
                else None
            ),
        )
