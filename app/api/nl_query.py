"""NL 查询 API — 自然语言数据查询端点"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import AgentState
from app.agents.data_graph import build_data_query_graph
from app.domain.nl_query_schemas import NLQueryRequest, NLQueryResponse
from app.domain.enums import Intent
from app.infrastructure.database import get_db
from app.infrastructure.sql_guard import SqlGuard
from app.infrastructure.security import CurrentUser, get_current_user

router = APIRouter(prefix="/nl-query", tags=["natural-language-query"])


@router.post("/", response_model=NLQueryResponse)
async def natural_language_query(
    request: NLQueryRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """自然语言数据查询 (只读 SELECT)

    任何角色均可使用，权限由 SQL Guard Layer 3 自动注入:
    - 学生: 仅可见自己的数据
    - 教师: 仅可见所管班级的数据
    - 管理员: 可见全部数据
    """
    question = request.question.strip()

    # 获取用户所管班级 (教师角色)
    managed_classes = []
    if current_user.class_name:
        managed_classes = [current_user.class_name]

    # 构建 SQL 安全守卫 (role 是 UserRole 枚举，取其 value)
    role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    sql_guard = SqlGuard(
        user_role=role_str,
        current_user_id=current_user.user_id,
        managed_classes=managed_classes,
    )

    # 构建 Data Query Graph
    graph = build_data_query_graph(
        sql_guard=sql_guard,
        db_session_factory=db,
    )

    # 构建初始 State
    initial_state: AgentState = {
        "messages": [question],
        "current_intent": Intent.DATA_QUERY.value,
        "academic_context": None,
        "daiyu_persona_context": None,
        "safety": None,
        "retrieved_context": None,
        "student_id": current_user.user_id if role_str == "student" else "",
        "needs_memory_update": False,
        "table_schema_context": None,
        "generated_sql": None,
        "safe_sql": None,
        "guard_result": None,
        "sql_execution_result": None,
        "result_columns": None,
        "result_row_count": None,
        "sql_error": None,
        "formatted_answer": None,
        "user_role": role_str,
    }

    # 执行 Graph
    result = await graph.ainvoke(initial_state)

    return NLQueryResponse(
        question=question,
        sql=result.get("generated_sql"),
        sql_error=result.get("sql_error"),
        result=result.get("sql_execution_result"),
        result_row_count=result.get("result_row_count", 0) or 0,
        answer=result.get("formatted_answer", ""),
    )
