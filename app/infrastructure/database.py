"""数据库连接管理 — SQLAlchemy async + 连接池"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.infrastructure.config import get_settings

settings = get_settings()

# MySQL → asyncmy driver
async_url = settings.DATABASE__URL.replace("mysql+pymysql://", "mysql+asyncmy://")

engine = create_async_engine(
    async_url,
    pool_size=settings.DATABASE__POOL_SIZE,
    max_overflow=settings.DATABASE__MAX_OVERFLOW,
    echo=False,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
