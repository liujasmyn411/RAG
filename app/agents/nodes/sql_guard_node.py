"""SQL 安全守卫节点 — 对 LLM 生成的 SQL 执行四层校验"""

from app.agents.state import AgentState
from app.infrastructure.sql_guard import SqlGuard, GuardResult


async def sql_guard_node(state: AgentState, guard: SqlGuard) -> dict:
    """执行 SQL 安全校验"""
    sql = state.get("generated_sql")
    if not sql:
        return {"sql_error": "没有可校验的 SQL", "guard_result": None}

    result: GuardResult = guard.guard(sql)

    return {
        "guard_result": result,
        "sql_error": None if result.passed else result.error,
        "safe_sql": result.safe_sql if result.passed else None,
    }
