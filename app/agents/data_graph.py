"""数据查询 LangGraph — 独立的 NL2SQL 图 (不走黛玉人设)"""

from functools import partial

from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.nodes.schema_builder import schema_builder_node
from app.agents.nodes.text2sql_node import text2sql_node
from app.agents.nodes.sql_guard_node import sql_guard_node
from app.agents.nodes.sql_executor import sql_executor_node
from app.agents.nodes.result_formatter import result_formatter_node
from app.agents.nodes.error_response import error_response_node


def build_data_query_graph(sql_guard, db_session_factory):
    """构建数据查询 LangGraph

    节点流程:
    schema_builder → text2sql → sql_guard
      ├─ guard 失败 → error_response → END
      └─ guard 成功 → sql_executor → result_formatter → END
    """
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("schema_builder", schema_builder_node)
    graph.add_node("text2sql", text2sql_node)
    graph.add_node(
        "sql_guard",
        partial(sql_guard_node, guard=sql_guard),
    )
    graph.add_node(
        "sql_executor",
        partial(sql_executor_node, db_session=db_session_factory),
    )
    graph.add_node("result_formatter", result_formatter_node)
    graph.add_node("error_response", error_response_node)

    # 设置入口
    graph.set_entry_point("schema_builder")

    # 顺序边
    graph.add_edge("schema_builder", "text2sql")
    graph.add_edge("text2sql", "sql_guard")

    # 条件分支: guard 结果
    def route_after_guard(state: AgentState) -> str:
        guard_result = state.get("guard_result")
        if guard_result is not None and guard_result.passed:
            return "executor"
        return "error"

    graph.add_conditional_edges("sql_guard", route_after_guard, {
        "executor": "sql_executor",
        "error": "error_response",
    })

    graph.add_edge("sql_executor", "result_formatter")
    graph.add_edge("result_formatter", END)
    graph.add_edge("error_response", END)

    return graph.compile()
