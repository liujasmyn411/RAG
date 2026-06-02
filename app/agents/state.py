"""AgentState — LangGraph 工作记忆 State 定义"""

from typing import Annotated, Optional, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """一次对话的完整 State"""

    # 核心对话流
    messages: Annotated[list, add_messages]

    # 情境路由
    current_intent: str  # "daiyu_chat" | "academic_query" | "psych_crisis" | "data_query"

    # 业务数据暂存
    academic_context: Optional[dict]

    # 人设增强包
    daiyu_persona_context: Optional[str]

    # 安全层 (Layer 0)
    safety: Optional[dict]

    # 检索结果
    retrieved_context: Optional[dict]

    # 学生标识
    student_id: str

    # 触发标记
    needs_memory_update: bool

    # ── NL2SQL 相关字段 ──

    # Table Schema 上下文 (注入给 LLM)
    table_schema_context: Optional[str]

    # LLM 生成的 SQL
    generated_sql: Optional[str]

    # 安全校验后的 SQL
    safe_sql: Optional[str]

    # SQL 安全校验结果
    guard_result: Optional[object]

    # SQL 执行结果 (list[dict])
    sql_execution_result: Optional[list]

    # 结果列名
    result_columns: Optional[list]

    # 结果行数
    result_row_count: Optional[int]

    # SQL 安全校验/执行错误信息
    sql_error: Optional[str]

    # 格式化后的自然语言回答
    formatted_answer: Optional[str]

    # 当前用户角色 (用于 SQL 权限注入)
    user_role: str
