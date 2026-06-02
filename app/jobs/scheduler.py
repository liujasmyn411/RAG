"""定时任务调度器 — APScheduler"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.jobs.decay_job import DecayJob
from app.jobs.archive_job import ArchiveJob
from app.repositories.neo4j_repo import Neo4jRepo
from app.repositories.milvus_repo import MilvusRepo
from app.repositories.pg_repo import PgRepo
from app.infrastructure.database import async_session_factory

scheduler = AsyncIOScheduler()


async def run_decay_job() -> None:
    """每日衰减任务"""
    neo4j = Neo4jRepo()
    milvus = MilvusRepo()
    job = DecayJob(neo4j, milvus)
    await job.execute()


async def run_archive_job() -> None:
    """每日归档任务"""
    async with async_session_factory() as session:
        pg = PgRepo(session)
        neo4j = Neo4jRepo()
        job = ArchiveJob(pg, neo4j)
        await job.execute()


def start_scheduler() -> None:
    """启动所有定时任务"""
    scheduler.add_job(
        run_decay_job,
        trigger="cron",
        hour=3,
        minute=7,
        id="decay_job",
    )
    scheduler.add_job(
        run_archive_job,
        trigger="cron",
        hour=4,
        minute=13,
        id="archive_job",
    )
    scheduler.start()
