"""Milvus DAO — 向量数据库增删改查"""

import time
from typing import Optional

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    MilvusClient,
    connections,
)

from app.infrastructure.config import get_settings


class MilvusRepo:
    """Milvus 数据访问 — L3-Hot + hlmm_scenes"""

    def __init__(self) -> None:
        settings = get_settings()
        connections.connect(alias="default", uri=settings.MILVUS__URI)
        self._client = MilvusClient(uri=settings.MILVUS__URI)
        self._l3_collection = settings.MILVUS__L3_COLLECTION
        self._hlmm_collection = settings.MILVUS__HLMM_COLLECTION

    # ═══════════════════════════════════════════════════════════
    # L3-Hot: CRUD
    # ═══════════════════════════════════════════════════════════

    async def insert_l3(self, embedding: list[float], metadata: dict) -> str:
        """插入一条 L3-Hot 快照, 返回 l3_id"""
        data = {
            "l3_id": metadata["l3_id"],
            "student_id": metadata["student_id"],
            "embedding": embedding,
            "session_id": metadata.get("session_id", ""),
            "timestamp": metadata.get("timestamp", int(time.time())),
            "emotion_primary": metadata.get("emotion_primary", ""),
            "emotion_intensity": metadata.get("emotion_intensity", 0.5),
            "topic": metadata.get("topic", ""),
            "subject": metadata.get("subject", ""),
            "importance": metadata.get("importance", 0.5),
            "write_confidence": metadata.get("write_confidence", 0.5),
            "processed_for_l2": "false",
            "archived": False,
            "cold_ref": metadata.get("cold_ref", ""),
            "prev_l3_id": metadata.get("prev_l3_id", ""),
            "episode_id": metadata.get("episode_id", ""),
            "embedding_text": metadata.get("embedding_text", ""),
        }
        self._client.insert(
            collection_name=self._l3_collection,
            data=[data],
        )
        return metadata["l3_id"]

    async def search_l3(
        self,
        student_id: str,
        query_vector: list[float],
        emotion_filter: Optional[list[str]] = None,
        top_k: int = 20,
    ) -> list[dict]:
        """ANN 检索 L3-Hot (单学生分区)"""
        expr = f'student_id == "{student_id}" and archived == false'
        if emotion_filter:
            emotions = ", ".join(f'"{e}"' for e in emotion_filter)
            expr += f" and emotion_primary in [{emotions}]"

        results = self._client.search(
            collection_name=self._l3_collection,
            data=[query_vector],
            anns_field="embedding",
            filter=expr,
            limit=top_k,
            output_fields=[
                "l3_id", "student_id", "session_id", "timestamp",
                "emotion_primary", "emotion_intensity", "topic", "subject",
                "importance", "write_confidence", "cold_ref",
                "prev_l3_id", "episode_id", "embedding_text",
            ],
        )
        return results[0] if results else []

    async def get_l3_by_id(self, l3_id: str) -> Optional[dict]:
        """查询单条 L3"""
        results = self._client.query(
            collection_name=self._l3_collection,
            filter=f'l3_id == "{l3_id}"',
        )
        return results[0] if results else None

    async def update_l3_episode(self, l3_id: str, episode_id: str) -> None:
        """回写 L3 的 episode_id（post_processor 调用）"""
        self._client.upsert(
            collection_name=self._l3_collection,
            data=[{"l3_id": l3_id, "episode_id": episode_id}],
        )

    async def get_last_l3(self, student_id: str) -> Optional[dict]:
        """查询学生最近一条 L3（按 timestamp 降序）"""
        results = self._client.query(
            collection_name=self._l3_collection,
            filter=f'student_id == "{student_id}" and archived == false',
            output_fields=[
                "l3_id", "student_id", "session_id", "timestamp",
                "emotion_primary", "topic", "subject", "trigger",
                "embedding_text", "episode_id",
            ],
            limit=1,
            sort_by="timestamp DESC",
        )
        return results[0] if results else None

    async def get_adjacent_l3(
        self, l3_id: str, student_id: str
    ) -> dict:
        """按 timestamp 查询指定 L3 的前一条和后一条记录"""
        target = await self.get_l3_by_id(l3_id)
        if not target:
            return {"prev": None, "next": None}

        ts = target.get("timestamp", 0)

        # 前一条: 最近的 timestamp < ts
        prev_results = self._client.query(
            collection_name=self._l3_collection,
            filter=(
                f'student_id == "{student_id}"'
                f" and timestamp < {ts}"
                f" and archived == false"
            ),
            output_fields=[
                "l3_id", "timestamp", "emotion_primary", "topic",
                "subject", "embedding_text",
            ],
            limit=1,
            sort_by="timestamp DESC",
        )

        # 后一条: 最近的 timestamp > ts
        next_results = self._client.query(
            collection_name=self._l3_collection,
            filter=(
                f'student_id == "{student_id}"'
                f" and timestamp > {ts}"
                f" and archived == false"
            ),
            output_fields=[
                "l3_id", "timestamp", "emotion_primary", "topic",
                "subject", "embedding_text",
            ],
            limit=1,
            sort_by="timestamp ASC",
        )

        return {
            "prev": prev_results[0] if prev_results else None,
            "next": next_results[0] if next_results else None,
        }

    async def pull_unprocessed(
        self, student_id: str, limit: int = 30
    ) -> list[dict]:
        """拉取未处理的 L3-Hot (用于 Reflection)"""
        results = self._client.query(
            collection_name=self._l3_collection,
            filter=(
                f'student_id == "{student_id}"'
                f' and processed_for_l2 in ["false", "skipped"]'
                f" and archived == false"
            ),
            output_fields=[
                "l3_id", "student_id", "session_id", "timestamp",
                "emotion_primary", "emotion_intensity", "topic", "subject",
                "importance", "write_confidence", "cold_ref",
                "prev_l3_id", "episode_id", "embedding_text",
            ],
            limit=limit,
        )
        return results

    async def mark_processed(
        self, l3_ids: list[str], status: str = "true"
    ) -> None:
        """标记 L3 状态 (false/skipped/batched/true)"""
        if not l3_ids:
            return
        self._client.upsert(
            collection_name=self._l3_collection,
            data=[{"l3_id": lid, "processed_for_l2": status} for lid in l3_ids],
        )

    async def mark_skipped(self, l3_ids: list[str]) -> None:
        """标记 L3 跳过 (不足2条, 等攒够)"""
        await self.mark_processed(l3_ids, status="skipped")

    async def mark_archived(self, l3_ids: list[str]) -> None:
        """标记 L3 硬遗忘"""
        if not l3_ids:
            return
        for lid in l3_ids:
            self._client.upsert(
                collection_name=self._l3_collection,
                data=[{"l3_id": lid, "archived": True}],
            )

    async def batch_decay_importance(
        self, lambda_rate: float, now_ts: int
    ) -> int:
        """批量软遗忘 — 衰减 L3 importance"""
        # Milvus 不支持批量更新函数, 需遍历查询再更新
        # 这里仅返回待处理的数量, 实际衰减在定时任务中执行
        results = self._client.query(
            collection_name=self._l3_collection,
            filter="archived == false",
            output_fields=["l3_id", "importance", "timestamp"],
            limit=10000,
        )
        updated = 0
        for item in results:
            days = (now_ts - item["timestamp"]) / 86400
            new_imp = item["importance"] * pow(2.71828, -lambda_rate * days)
            if abs(new_imp - item["importance"]) > 0.01:
                self._client.upsert(
                    collection_name=self._l3_collection,
                    data=[{"l3_id": item["l3_id"], "importance": new_imp}],
                )
                updated += 1
        return updated

    # ═══════════════════════════════════════════════════════════
    # fourpaper: 四大名著 RAG 检索
    # ═══════════════════════════════════════════════════════════

    async def search_fourpaper(
        self,
        query_vector: list[float],
        book_name: str | None = None,
        top_k: int = 10,
    ) -> list[dict]:
        """ANN 检索四大名著 chunks"""
        expr = ""
        if book_name:
            expr = f'book_name == "{book_name}"'

        results = self._client.search(
            collection_name="fourpaper",
            data=[query_vector],
            anns_field="embedding",
            filter=expr if expr else None,
            limit=top_k,
            output_fields=[
                "id", "book_name", "chapter_title", "chapter_num",
                "chunk_index", "content", "word_count",
            ],
        )
        return results[0] if results else []

    # ═══════════════════════════════════════════════════════════
    # L0: hlmm_scenes (只读)
    # ═══════════════════════════════════════════════════════════

    async def search_scenes(
        self, emotion_tag: str, limit: int = 5
    ) -> list[dict]:
        """按情绪标签检索名场面"""
        results = self._client.query(
            collection_name=self._hlmm_collection,
            filter=f'emotion_tag == "{emotion_tag}"',
            output_fields=[
                "scene_id", "scene_name", "key_quote",
                "scene_summary", "response_hint", "chapter",
            ],
            limit=limit,
        )
        return results
