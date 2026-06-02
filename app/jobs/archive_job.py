"""超时归档定时任务"""

from datetime import datetime, timedelta

from app.infrastructure.config import get_settings
from app.repositories.pg_repo import PgRepo
from app.repositories.neo4j_repo import Neo4jRepo


class ArchiveJob:
    """每日凌晨: L3-Cold 两阶段归档 + 草稿清理 + Neo4j 冲突超时归档"""

    def __init__(self, pg_repo: PgRepo, neo4j_repo: Neo4jRepo) -> None:
        self._pg = pg_repo
        self._neo4j = neo4j_repo
        self._settings = get_settings()

    async def execute(self) -> dict:
        results: dict = {}

        # 1. Cold: hot → warm (Day 30, crisis 跳过)
        warmed = await self._pg.move_cold_to_warm(
            self._settings.STORAGE__COLD_WARM_DAYS
        )
        results["cold_warmed"] = warmed

        # 2. Cold: warm → 删除
        #    普通对话 90天 / importance≥0.7 180天 / crisis 永久
        deleted = await self._pg.expire_cold_archive(
            normal_days=self._settings.STORAGE__COLD_DELETE_DAYS,
            high_imp_days=self._settings.STORAGE__COLD_HIGHIMP_DAYS,
        )
        results["cold_deleted"] = deleted

        # 3. 草稿区: 清理已消费的超期草稿
        purged = await self._pg.purge_stale_drafts(
            self._settings.STORAGE__DRAFT_RETENTION_DAYS
        )
        results["drafts_purged"] = purged

        # 4. Neo4j 冲突超时归档 (> 30天 pending → archived)
        archived = await self._neo4j.batch_archive_pending_conflicts(
            self._settings.STORAGE__CONTRADICTION_TIMEOUT_DAYS
        )
        results["conflicts_archived"] = archived

        return results
