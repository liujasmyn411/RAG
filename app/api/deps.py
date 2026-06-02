"""API 依赖注入 — FastAPI Depends"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db, async_session_factory
from app.infrastructure.config import get_settings
from app.infrastructure.security import CurrentUser, get_current_user
from app.repositories.neo4j_repo import Neo4jRepo
from app.repositories.milvus_repo import MilvusRepo
from app.repositories.pg_repo import PgRepo
from app.services.chat_service import ChatService
from app.services.memory_service import MemoryService
from app.services.reflection_service import ReflectionService
from app.services.safety_service import SafetyService
from app.services.session_service import SessionService
from app.services.teacher_service import TeacherService
from app.services.admin_service import AdminService

# ── 单例 ──

_neo4j_repo: Neo4jRepo | None = None
_milvus_repo: MilvusRepo | None = None
_checkpointer: object | None = None


def get_neo4j_repo() -> Neo4jRepo:
    global _neo4j_repo
    if _neo4j_repo is None:
        _neo4j_repo = Neo4jRepo()
    return _neo4j_repo


def get_milvus_repo() -> MilvusRepo:
    global _milvus_repo
    if _milvus_repo is None:
        _milvus_repo = MilvusRepo()
    return _milvus_repo


def get_pg_repo(db: Optional[AsyncSession] = None) -> PgRepo:
    if db is not None:
        return PgRepo(db)
    return PgRepo(async_session_factory())


async def get_checkpointer():
    """PG AsyncPostgresSaver 单例 — 跨会话 LangGraph State 持久化"""
    global _checkpointer
    if _checkpointer is None:
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            settings = get_settings()
            async_url = settings.DATABASE__URL.replace(
                "mysql+pymysql://", "postgresql+asyncpg://"
            )
            # 尝试 PG 适配; 如果 DATABASE__URL 是 MySQL, 回退到内存
            _checkpointer = AsyncPostgresSaver.from_conn_string(async_url)
            await _checkpointer.setup()
        except Exception:
            # 回退: 无 checkpointer (内存模式)
            _checkpointer = None
    return _checkpointer


# ── Service 工厂 ──

def get_memory_service() -> MemoryService:
    return MemoryService(get_neo4j_repo(), get_milvus_repo(), get_pg_repo())


def get_safety_service() -> SafetyService:
    return SafetyService(get_pg_repo())


def get_session_service() -> SessionService:
    return SessionService(get_pg_repo(), get_neo4j_repo())


def get_reflection_service() -> ReflectionService:
    return ReflectionService(get_neo4j_repo(), get_milvus_repo())


def get_chat_service() -> ChatService:
    return ChatService(
        safety_service=get_safety_service(),
        session_service=get_session_service(),
        memory_service=get_memory_service(),
        pg_repo=get_pg_repo(),
        milvus_repo=get_milvus_repo(),
    )


def get_teacher_service() -> TeacherService:
    return TeacherService(get_neo4j_repo(), get_pg_repo())


def get_admin_service() -> AdminService:
    return AdminService(get_pg_repo(), get_milvus_repo(), get_neo4j_repo())
