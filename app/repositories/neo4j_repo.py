"""Neo4j DAO — 图数据库增删改查"""

from datetime import datetime
from typing import Optional

from neo4j import AsyncGraphDatabase, AsyncManagedTransaction

from app.domain.enums import EmotionPrimary, RelationType, CognitionDimension
from app.domain.entities.memory import L2Cognition
from app.infrastructure.config import get_settings


class Neo4jRepo:
    """Neo4j 数据访问 — 封装所有 Cypher 操作"""

    def __init__(self) -> None:
        settings = get_settings()
        self._driver = AsyncGraphDatabase.driver(
            settings.NEO4J__URI,
            auth=(settings.NEO4J__USER, settings.NEO4J__PASSWORD),
        )

    # ═══════════════════════════════════════════════════════════
    # L0: 角色本体 (只读)
    # ═══════════════════════════════════════════════════════════

    async def get_daiyu_subgraph(self) -> list[dict]:
        """黛玉 1-hop 人物关系 (匹配 init_neo4j 中创建的关系类型)"""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (daiyu:Character {id: "char_daiyu"})
                MATCH (daiyu)-[r]-(other:Character)
                WHERE type(r) IN ['倾慕','忌惮','依赖','敬而远之','亲近','友善','同盟']
                RETURN type(r) AS relation, r.weight AS strength,
                       other.name AS name, other.traits AS traits
                """
            )
            records = await result.data()
            return records

    async def get_scenes_by_emotion(
        self, emotion: str, limit: int = 2
    ) -> list[dict]:
        """按情绪标签匹配名场面, 随机轮换"""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (s:Scene)
                WHERE s.emotion_tag = $emotion
                RETURN s.scene_name AS scene_name,
                       s.key_quote AS key_quote,
                       s.response_hint AS response_hint,
                       s.summary AS summary,
                       s.scene_id AS scene_id
                ORDER BY rand()
                LIMIT $limit
                """,
                emotion=emotion,
                limit=limit,
            )
            return await result.data()

    # ═══════════════════════════════════════════════════════════
    # L2: 语义认知 (增删改查)
    # ═══════════════════════════════════════════════════════════

    async def get_student_traits(self, student_id: str) -> list[dict]:
        """学生所有 L2 认知边"""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (s:Student {student_id: $sid})-[r]-(t)
                WHERE type(r) IN ['偏科', '情绪倾向', '态度偏好', '社交模式']
                RETURN type(r) AS relation_type, t.name AS target_name,
                       r.confidence AS confidence, r.C_peak AS C_peak,
                       r.C_trough AS C_trough,
                       r.streak_count AS streak_count,
                       r.streak_direction AS streak_direction,
                       r.last_oppose_time AS last_oppose_time,
                       r.source AS source, r.verified_count AS verified_count,
                       r.level AS level, r.trend AS trend,
                       r.intensity AS intensity, r.valence AS valence,
                       r.pattern AS pattern
                ORDER BY r.confidence DESC
                """,
                sid=student_id,
            )
            return await result.data()

    async def get_trait_by_dimension(
        self, student_id: str, relation_type: str, target_name: str
    ) -> Optional[dict]:
        """查询单条 L2 认知边"""
        async with self._driver.session() as session:
            result = await session.run(
                f"""
                MATCH (s:Student {{student_id: $sid}})
                MATCH (s)-[r:`{relation_type}`]->(t {{name: $target}})
                RETURN r.confidence AS confidence, r.C_peak AS C_peak,
                       r.C_trough AS C_trough, r.streak_count AS streak_count,
                       r.streak_direction AS streak_direction,
                       r.last_oppose_time AS last_oppose_time,
                       r.level AS level, r.trend AS trend
                """,
                sid=student_id,
                target=target_name,
            )
            records = await result.data()
            return records[0] if records else None

    async def create_l2_edge(
        self,
        student_id: str,
        relation_type: str,
        target_name: str,
        target_label: str,
        props: dict,
    ) -> None:
        """创建新的 L2 认知边"""
        async with self._driver.session() as session:
            await session.run(
                f"""
                MATCH (s:Student {{student_id: $sid}})
                MERGE (t:{target_label} {{name: $target}})
                CREATE (s)-[r:`{relation_type}`]->(t)
                SET r = $props
                """,
                sid=student_id,
                target=target_name,
                props=props,
            )

    async def update_l2_edge(
        self,
        student_id: str,
        relation_type: str,
        target_name: str,
        updates: dict,
    ) -> None:
        """更新 L2 认知边属性"""
        set_clause = ", ".join(f"r.{k} = ${k}" for k in updates)
        async with self._driver.session() as session:
            params = {"sid": student_id, "target": target_name, **updates}
            await session.run(
                f"""
                MATCH (s:Student {{student_id: $sid}})
                MATCH (s)-[r:`{relation_type}`]->(t {{name: $target}})
                SET {set_clause}
                """,
                **params,
            )

    async def mark_edge_conflict(
        self,
        student_id: str,
        relation_type: str,
        target_name: str,
        conflict_with: str,
    ) -> None:
        """标记 L2 认知边进入冲突待验证状态"""
        await self.update_l2_edge(
            student_id, relation_type, target_name,
            {
                "conflict_status": "pending_verification",
                "conflict_with": conflict_with,
                "pending_since": datetime.now(),
                "updated_at": datetime.now(),
            },
        )

    async def resolve_edge_conflict(
        self,
        student_id: str,
        relation_type: str,
        target_name: str,
    ) -> None:
        """解除冲突状态 (三角验证通过)"""
        await self.update_l2_edge(
            student_id, relation_type, target_name,
            {
                "conflict_status": "active",
                "conflict_with": None,
                "pending_since": None,
                "updated_at": datetime.now(),
            },
        )

    async def archive_l2_edge(
        self, student_id: str, relation_type: str, target_name: str
    ) -> None:
        """归档 L2 认知边 (置信度 ≈ 0, 标记 archived)"""
        await self.update_l2_edge(
            student_id,
            relation_type,
            target_name,
            {
                "conflict_status": "archived",
                "confidence": 0.05,
                "updated_at": datetime.now(),
            },
        )

    async def get_pending_conflicts(
        self, student_id: str, timeout_days: int = 30
    ) -> list[dict]:
        """查询超时的待验证冲突 (用于定时归档)"""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (s:Student {student_id: $sid})-[r]-(t)
                WHERE type(r) IN ['偏科','情绪倾向','态度偏好','社交模式']
                  AND r.conflict_status = 'pending_verification'
                  AND r.pending_since IS NOT NULL
                  AND duration.inDays(r.pending_since, datetime()).days > $days
                RETURN type(r) AS relation_type, t.name AS target_name,
                       r.conflict_with AS conflict_with,
                       r.pending_since AS pending_since
                """,
                sid=student_id,
                days=timeout_days,
            )
            return await result.data()

    # ═══════════════════════════════════════════════════════════
    # 跨层: 关心关系
    # ═══════════════════════════════════════════════════════════

    async def get_care_strength(self, student_id: str) -> Optional[dict]:
        """黛玉→学生 关系强度"""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (:Character {id: "char_daiyu"})-[r:关心]->(s:Student {student_id: $sid})
                RETURN r.strength AS strength,
                       r.first_interaction AS first_interaction,
                       r.last_interaction AS last_interaction,
                       r.interaction_count AS interaction_count
                """,
                sid=student_id,
            )
            records = await result.data()
            return records[0] if records else None

    async def upsert_care_relation(self, student_id: str, props: dict) -> None:
        """创建/更新 黛玉→学生 关心关系"""
        async with self._driver.session() as session:
            await session.run(
                """
                MATCH (daiyu:Character {id: "char_daiyu"})
                MATCH (s:Student {student_id: $sid})
                MERGE (daiyu)-[r:关心]->(s)
                SET r += $props
                """,
                sid=student_id,
                props=props,
            )

    async def batch_decay_strengths(self, lambda_rate: float) -> int:
        """批量衰减关心边 strength, 返回更新条数"""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (:Character)-[r:关心]->(:Student)
                WHERE r.last_interaction IS NOT NULL
                SET r.strength = r.strength * exp(-$lambda *
                    (duration.inDays(r.last_interaction, datetime()).days))
                RETURN count(r) AS updated
                """,
                lambda_rate=lambda_rate,
            )
            records = await result.data()
            return records[0]["updated"] if records else 0

    async def batch_recover_confidence(self, recovery_lambda: float, recovery_cap: float) -> int:
        """批量回升 L2 认知边的置信度"""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (s:Student)-[r]-(t)
                WHERE type(r) IN ['偏科', '情绪倾向', '态度偏好', '社交模式']
                  AND r.streak_count = 0
                  AND r.last_oppose_time IS NOT NULL
                  AND r.C_peak > r.C_trough
                WITH r, r.C_peak - r.C_trough AS damage
                SET r.confidence = r.C_trough + damage *
                    (1 - exp(-$lambda *
                     duration.inDays(r.last_oppose_time, datetime()).days)) *
                    $cap
                RETURN count(r) AS updated
                """,
                lambda_rate=recovery_lambda,
                cap=recovery_cap,
            )
            records = await result.data()
            return records[0]["updated"] if records else 0

    async def batch_archive_pending_conflicts(self, timeout_days: int) -> int:
        """批量归档超时的待验证冲突 (> timeout_days天)"""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (s:Student)-[r]-(t)
                WHERE type(r) IN ['偏科','情绪倾向','态度偏好','社交模式']
                  AND r.conflict_status = 'pending_verification'
                  AND r.pending_since IS NOT NULL
                  AND duration.inDays(r.pending_since, datetime()).days > $days
                SET r.conflict_status = 'archived',
                    r.updated_at = datetime()
                RETURN count(r) AS updated
                """,
                days=timeout_days,
            )
            records = await result.data()
            return records[0]["updated"] if records else 0

    async def close(self) -> None:
        await self._driver.close()
