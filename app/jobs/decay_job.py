"""遗忘衰减 + 回升计算 + B2降级定时任务"""

import time
from datetime import datetime

from app.infrastructure.database import async_session_factory
from app.infrastructure.config import get_settings
from app.repositories.neo4j_repo import Neo4jRepo
from app.repositories.milvus_repo import MilvusRepo
from app.repositories.pg_repo import PgRepo


class DecayJob:
    """每日凌晨: 软遗忘衰减 + 置信度回升 + B2窗口管理"""

    def __init__(self, neo4j_repo: Neo4jRepo, milvus_repo: MilvusRepo) -> None:
        self._neo4j = neo4j_repo
        self._milvus = milvus_repo
        self._settings = get_settings()

    async def execute(self) -> dict:
        results: dict = {}

        # 1. Neo4j 关系边衰减
        updated = await self._neo4j.batch_decay_strengths(
            self._settings.DECAY__EMOTION_LAMBDA
        )
        results["neo4j_decayed"] = updated

        # 2. Neo4j 回升计算
        recovered = await self._neo4j.batch_recover_confidence(
            self._settings.DECAY__RECOVERY_LAMBDA,
            self._settings.DECAY__RECOVERY_CAP,
        )
        results["neo4j_recovered"] = recovered

        # 3. Milvus L3 软遗忘
        now_ts = int(time.time())
        decayed = await self._milvus.batch_decay_importance(
            self._settings.DECAY__EMOTION_LAMBDA, now_ts
        )
        results["milvus_decayed"] = decayed

        # 4. B2 24h 降级: 每24h无新违规 → count -= 1
        async with async_session_factory() as session:
            pg = PgRepo(session)
            results["b2_decayed"] = await self._b2_daily_decay(pg)

            # 5. 危机通知超时升级: pending > 30min → escalated
            escalated = await pg.escalate_overdue_alerts(timeout_minutes=30)
            results["crisis_escalated"] = escalated

        return results

    async def _b2_daily_decay(self, pg: PgRepo) -> int:
        """B2 违规 24h 降1 + 7天窗口重置"""
        # 需要批量扫描 student_profile
        # 简化: 遍历有 b2_count > 0 的记录
        from sqlalchemy import text
        result = await pg._session.execute(
            text(
                """SELECT student_id, violation_b2_count, b2_last_decay_time,
                          b2_window_start
                   FROM student_profile
                   WHERE violation_b2_count > 0"""
            )
        )
        rows = result.fetchall()
        now = datetime.now()
        updated = 0

        for row in rows:
            sid = row[0]
            b2 = row[1]
            last_decay = row[2]
            window_start = row[3]

            # 7 天窗口: 过期重置
            if window_start and (now - window_start).days >= 7:
                await pg._session.execute(
                    text(
                        """UPDATE student_profile
                           SET violation_b2_count=0, b2_window_start=NULL
                           WHERE student_id=:sid"""
                    ),
                    {"sid": sid},
                )
                updated += 1
                continue

            # 24h 降1
            if last_decay and (now - last_decay).total_seconds() >= 86400:
                new_count = max(b2 - 1, 0)
                await pg._session.execute(
                    text(
                        """UPDATE student_profile
                           SET violation_b2_count=:cnt,
                               b2_last_decay_time=:now,
                               b2_window_start=CASE WHEN :cnt=0 THEN NULL
                                                    ELSE b2_window_start END
                           WHERE student_id=:sid"""
                    ),
                    {"sid": sid, "cnt": new_count, "now": now},
                )
                updated += 1

        return updated
