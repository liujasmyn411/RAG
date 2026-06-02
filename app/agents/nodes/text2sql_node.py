"""Text-to-SQL 节点 — LLM 根据 Schema + 用户问题生成 SQL"""

from app.agents.state import AgentState
from app.infrastructure.llm_client import get_llm_client


async def text2sql_node(state: AgentState) -> dict:
    """LLM 根据 Schema 上下文 + 用户自然语言问题生成 SQL"""
    schema = state.get("table_schema_context", "")
    messages = state.get("messages", [])
    if not messages:
        return {"generated_sql": None, "sql_error": "没有用户消息"}

    last_msg = messages[-1]
    question = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    llm = get_llm_client()

    try:
        sql = await llm.chat(
            [
                {"role": "system", "content": schema},
                {"role": "user", "content": f"请将以下问题转为SQL查询:\n{question}"},
            ],
            temperature=0.1,
            max_tokens=1024,
        )
    except Exception as e:
        return {"generated_sql": None, "sql_error": f"LLM 调用失败: {e}"}

    if not sql or not sql.strip():
        return {"generated_sql": None, "sql_error": "LLM 未生成 SQL"}

    return {"generated_sql": sql.strip()}
