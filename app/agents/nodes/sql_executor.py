"""SQL 执行节点 — 安全执行 SQL 并返回结果"""

import asyncio
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import AgentState


async def sql_executor_node(
    state: AgentState,
    db_session: AsyncSession,
) -> dict:
    """执行已通过安全校验的 SQL"""
    safe_sql = state.get("safe_sql")
    if not safe_sql:
        return {"sql_execution_result": None, "sql_error": "没有可执行的 SQL"}

    try:
        # 直接使用 session 执行 (session 由 FastAPI Depends 管理)
        # MySQL 不支持 max_execution_time 变量名，跳过
        result = await db_session.execute(text(safe_sql))

        # 获取列名
        columns = list(result.keys()) if result.keys() else []

        # 获取数据行
        rows = result.fetchall()

        # 转换为 dict 列表
        data = []
        for row in rows:
            data.append(dict(zip(columns, row)))

        return {
            "sql_execution_result": data,
            "result_columns": columns,
            "result_row_count": len(data),
            "sql_error": None,
        }

    except asyncio.TimeoutError:
        return {"sql_execution_result": None, "sql_error": "查询超时 (5秒)"}
    except Exception as e:
        return {"sql_execution_result": None, "sql_error": f"SQL 执行错误: {e}"}
