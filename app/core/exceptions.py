class AgentException(Exception):
    """Agent 业务异常基类"""
    pass


class ToolExecutionError(AgentException):
    """工具执行失败"""
    pass


class LLMError(AgentException):
    """LLM 调用异常"""
    pass


class SessionNotFoundError(AgentException):
    """会话不存在"""
    pass
