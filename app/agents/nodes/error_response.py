"""错误响应节点 — 处理 SQL 安全校验失败"""

from app.agents.state import AgentState


async def error_response_node(state: AgentState) -> dict:
    """生成错误响应"""
    error = state.get("sql_error", "未知错误")
    sql = state.get("generated_sql", "")

    response = f"⚠️ 查询无法执行: {error}"

    # 给出安全提示
    if sql:
        response += f"\n\n生成的 SQL:\n```sql\n{sql}\n```"

    response += "\n\n请尝试换一种方式描述你的查询需求。"

    return {"formatted_answer": response}
