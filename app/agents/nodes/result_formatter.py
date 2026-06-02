"""结果格式化节点 — LLM 将 SQL 查询结果格式化为自然语言"""

from app.agents.state import AgentState
from app.infrastructure.llm_client import get_llm_client


FORMATTER_PROMPT = """你是一个数据分析助手。将以下 SQL 查询结果格式化为清晰的自然语言报告。

要求:
1. 先简述查询了什么
2. 如果结果≤10行，用表格展示
3. 如果结果是统计数字，直接给出结论
4. 如果结果为空，说明"没有匹配的数据"
5. 客观准确，不要添加虚构信息
6. 不超过 500 字"""


async def result_formatter_node(state: AgentState) -> dict:
    """将 SQL 执行结果格式化为自然语言"""
    result = state.get("sql_execution_result")
    sql = state.get("generated_sql", "")
    error = state.get("sql_error")

    messages = state.get("messages", [])
    question = ""
    if messages:
        last_msg = messages[-1]
        question = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    # 错误情况
    if error:
        return {
            "formatted_answer": f"查询失败: {error}",
            "needs_memory_update": False,
        }

    # 空结果
    if result is None:
        return {
            "formatted_answer": "查询未返回任何结果。",
            "needs_memory_update": False,
        }

    # 小结果集: LLM 格式化
    if len(result) <= 20:
        try:
            llm = get_llm_client()
            context = f"用户问题: {question}\n\nSQL: {sql}\n\n查询结果 ({len(result)} 行):\n{_format_table(result)}"

            formatted = await llm.chat(
                [
                    {"role": "system", "content": FORMATTER_PROMPT},
                    {"role": "user", "content": context},
                ],
                temperature=0.3,
                max_tokens=800,
            )
        except Exception:
            formatted = _format_table(result)
    else:
        # 大结果集: 直接表格 + 截断
        preview = result[:20]
        formatted = (
            f"查询返回了 {len(result)} 条记录（显示前20条）:\n\n"
            + _format_table(preview)
            + f"\n\n... 还有 {len(result) - 20} 条记录未显示。"
        )

    return {
        "formatted_answer": formatted,
        "needs_memory_update": False,
    }


def _format_table(rows: list[dict]) -> str:
    """将 dict 列表格式化为 Markdown 表格"""
    if not rows:
        return "(空)"

    columns = list(rows[0].keys())
    # 表头
    header = "| " + " | ".join(columns) + " |"
    separator = "|" + "|".join("---" for _ in columns) + "|"
    # 数据行
    data_rows = []
    for row in rows[:20]:
        vals = [str(row.get(c, "")) for c in columns]
        data_rows.append("| " + " | ".join(vals) + " |")

    return "\n".join([header, separator] + data_rows)
