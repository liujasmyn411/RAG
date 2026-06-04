"""定向迁移: 只加 episodes 表和 Milvus 新字段, 不动现有数据"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from pymilvus import Collection, DataType, FieldSchema, connections

from app.infrastructure.config import get_settings

settings = get_settings()

PG_MIGRATION = """
CREATE TABLE IF NOT EXISTS episodes (
    episode_id       VARCHAR(128) PRIMARY KEY,
    student_id       VARCHAR(32) NOT NULL,
    session_id       VARCHAR(64) NOT NULL,
    topic            VARCHAR(32) NOT NULL,
    started_at       TIMESTAMP NOT NULL,
    ended_at         TIMESTAMP,
    l3_count         INT DEFAULT 1,
    is_closed        BOOLEAN DEFAULT FALSE,
    boundary_trigger VARCHAR(32) DEFAULT 'first_episode',
    created_at       TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_episodes_student ON episodes(student_id);
CREATE INDEX IF NOT EXISTS idx_episodes_active ON episodes(is_closed, student_id);
"""


async def migrate_pg():
    async_url = settings.DATABASE__URL.replace("mysql+pymysql://", "mysql+asyncmy://")
    engine = create_async_engine(async_url, echo=True)
    async with engine.begin() as conn:
        for statement in PG_MIGRATION.split(";"):
            stmt = statement.strip()
            if stmt:
                try:
                    await conn.execute(text(stmt))
                    print(f"  OK  {stmt[:60]}...")
                except Exception as e:
                    if "Duplicate" in str(e) or "already exists" in str(e):
                        print(f" SKIP (exists) {stmt[:60]}...")
                    else:
                        print(f" FAIL {e}")
    await engine.dispose()
    print("PG migration done.")


def migrate_milvus():
    connections.connect(alias="default", uri=settings.MILVUS__URI, timeout=10)
    col = Collection(settings.MILVUS__L3_COLLECTION)

    existing = {f.name for f in col.schema.fields}
    to_add = []
    if "prev_l3_id" not in existing:
        to_add.append(FieldSchema("prev_l3_id", DataType.VARCHAR, max_length=128))
    if "episode_id" not in existing:
        to_add.append(FieldSchema("episode_id", DataType.VARCHAR, max_length=128))

    if to_add:
        print(f"Adding fields: {[f.name for f in to_add]}")
        col.release()
        for field in to_add:
            col.add_field(field)
        # timestamp index for sort queries
        try:
            col.create_index("timestamp", {"index_type": "STL_SORT"})
        except Exception:
            pass
        col.load()
        print("Milvus schema migrated.")
    else:
        print("Milvus schema already up-to-date.")

    connections.disconnect("default")


async def main():
    print("=== PG Migration ===")
    await migrate_pg()
    print("\n=== Milvus Migration ===")
    try:
        migrate_milvus()
    except Exception as e:
        print(f"Milvus migration skipped: {e}")
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
