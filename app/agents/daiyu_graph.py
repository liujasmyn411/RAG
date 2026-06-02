"""黛玉 Agent LangGraph 图定义 — 编译完整的 StateGraph"""

from functools import partial

from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.nodes.safety_filter import safety_filter_node
from app.agents.nodes.intent_router import intent_router_node
from app.agents.nodes.memory_retrieval import memory_retrieval_node
from app.agents.nodes.context_builder import context_builder_node
from app.agents.nodes.response_generator import response_generator_node
from app.agents.nodes.fact_verifier import fact_verifier_node
from app.agents.nodes.post_processor import post_processor_node
from app.agents.prompts.daiyu_persona import DAIYU_SYSTEM_PROMPT


def build_daiyu_graph(
    safety_service,
    memory_service,
    pg_repo,
    milvus_repo,
    checkpointer=None,
):
    """构建并编译黛玉 Agent 的 LangGraph

    Args:
        checkpointer: PG AsyncPostgresSaver 或 None (跨会话 State 持久化)

    节点流程:
    safety_filter → [分支]
      ├─ flagged → response_generator (安全回复)
      └─ safe → intent_router → memory_retrieval
                → context_builder → response_generator
                → fact_verifier → post_processor → END
    """
    graph = StateGraph(AgentState)

    # 添加节点 (绑定服务依赖)
    graph.add_node("safety_filter", partial(safety_filter_node, safety_service=safety_service))
    graph.add_node("intent_router", intent_router_node)
    graph.add_node(
        "memory_retrieval",
        partial(memory_retrieval_node, memory_service=memory_service),
    )
    graph.add_node(
        "context_builder",
        partial(context_builder_node, persona_prompt=DAIYU_SYSTEM_PROMPT),
    )
    graph.add_node(
        "response_generator",
        partial(response_generator_node, persona_prompt=DAIYU_SYSTEM_PROMPT),
    )
    graph.add_node("fact_verifier", fact_verifier_node)
    graph.add_node(
        "post_processor",
        partial(post_processor_node, pg_repo=pg_repo, milvus_repo=milvus_repo),
    )

    # 设置入口
    graph.set_entry_point("safety_filter")

    # 安全路由: flagged → 直接生成回复, safe → 正常流程
    def route_after_safety(state: AgentState) -> str:
        safety = state.get("safety") or {}
        if safety.get("risk_level") == "flagged":
            return "response_generator"
        return "intent_router"

    graph.add_conditional_edges("safety_filter", route_after_safety, {
        "response_generator": "response_generator",
        "intent_router": "intent_router",
    })

    # 正常流程
    graph.add_edge("intent_router", "memory_retrieval")
    graph.add_edge("memory_retrieval", "context_builder")
    graph.add_edge("context_builder", "response_generator")
    graph.add_edge("response_generator", "fact_verifier")
    graph.add_edge("fact_verifier", "post_processor")
    graph.add_edge("post_processor", END)

    return graph.compile(checkpointer=checkpointer)


def build_teacher_graph(teacher_service):
    """构建教师查询图 (简化: 无 L3 写入, 无双向交互)"""
    from app.agents.state import AgentState

    graph = StateGraph(AgentState)
    # 教师查询简化版: 直接检索 + 生成报告
    # 生产环境可扩展
    return graph.compile()
