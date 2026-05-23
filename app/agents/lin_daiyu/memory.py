import time
import uuid
from typing import List, Dict, Optional


class SessionMemory:
    """内存版会话管理（一期方案）
    
    限制：
    - 单 Session 最多保留 10 轮对话（用户+助手各算一轮）
    - 应用重启后清空
    - 超长时自动丢弃最旧的记录
    """

    MAX_TURNS = 10  # 10轮 = 20条消息

    def __init__(self):
        self._store: Dict[str, List[Dict]] = {}
        self._last_access: Dict[str, float] = {}

    def create_session(self) -> str:
        sid = str(uuid.uuid4())[:16]
        self._store[sid] = []
        self._last_access[sid] = time.time()
        return sid

    def has_session(self, session_id: str) -> bool:
        return session_id in self._store

    def get_history(self, session_id: str) -> List[Dict]:
        if session_id not in self._store:
            return []
        self._last_access[session_id] = time.time()
        return list(self._store[session_id])

    def add_message(self, session_id: str, role: str, content: str):
        if session_id not in self._store:
            self._store[session_id] = []
        self._store[session_id].append({"role": role, "content": content})
        self._last_access[session_id] = time.time()

        # 保留最近 MAX_TURNS 轮（每轮2条消息）
        max_messages = self.MAX_TURNS * 2
        if len(self._store[session_id]) > max_messages:
            self._store[session_id] = self._store[session_id][-max_messages:]

    def add_tool_result(self, session_id: str, tool_name: str, result: str):
        """添加 tool 角色消息（OpenAI 格式）"""
        self.add_message(
            session_id,
            role="tool",
            content=result,
        )
        # 为简化，不在内存中维护 tool_call_id 映射，
        # 通义千问兼容模式下通常只需要角色和内容

    def clear(self, session_id: str):
        if session_id in self._store:
            del self._store[session_id]
            del self._last_access[session_id]


# 全局实例
memory = SessionMemory()
