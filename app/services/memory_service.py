"""记忆检索服务 — 统一检索入口, 按 intent 调度不同检索策略"""

from app.domain.enums import Intent, EmotionPrimary
from app.infrastructure.classifier import ClassifierService
from app.infrastructure.embedding import get_embedding_service
from app.infrastructure.reranker import get_reranker_service
from app.repositories.neo4j_repo import Neo4jRepo
from app.repositories.milvus_repo import MilvusRepo
from app.repositories.pg_repo import PgRepo


class MemoryService:
    """记忆检索统一入口"""

    def __init__(
        self,
        neo4j_repo: Neo4jRepo,
        milvus_repo: MilvusRepo,
        pg_repo: PgRepo,
    ) -> None:
        self._neo4j = neo4j_repo
        self._milvus = milvus_repo
        self._pg = pg_repo
        self._embed = get_embedding_service()
        self._reranker = get_reranker_service()
        self._classifier = ClassifierService()

    async def retrieve_by_intent(
        self,
        intent: Intent,
        query: str,
        student_id: str,
    ) -> dict:
        """按 intent 分发检索策略"""
        if intent == Intent.DAIYU_CHAT:
            return await self._retrieve_daiyu_chat(query, student_id)
        elif intent == Intent.ACADEMIC_QUERY:
            return await self._retrieve_academic(query, student_id)
        elif intent == Intent.PSYCH_CRISIS:
            return await self._retrieve_psych_crisis(student_id)
        elif intent == Intent.LITERARY_QUERY:
            return await self._retrieve_literary(query)
        return {}

    # ── daiyu_chat: 三阶段混合编排 ──

    async def _retrieve_daiyu_chat(
        self, query: str, student_id: str
    ) -> dict:
        # Phase 1: 快速提取
        l2_tags = await self._neo4j.get_student_traits(student_id)
        emotions = await self._classifier.classify(query)

        # 增强 query
        enhanced = (
            f"{query}。该生特征: {l2_tags}。情绪: {emotions}"
        )

        # Phase 2: 深度检索
        query_vec = self._embed.encode(enhanced)
        emotion_val = emotions.get("emotion_primary", "")

        # L3 Milvus
        l3_raw = await self._milvus.search_l3(
            student_id, query_vec,
            emotion_filter=[emotion_val] if emotion_val else None,
            top_k=20,
        )
        l3_ranked = self._reranker.rerank(query, l3_raw) if l3_raw else []
        l3_final = self._filter_by_confidence(l3_ranked)[:5]

        # Quick Win 4: 为 top-3 结果拉取叙事相邻记录
        for l3 in l3_final[:3]:
            try:
                adjacent = await self._milvus.get_adjacent_l3(
                    l3["l3_id"], student_id
                )
                l3["_prev"] = adjacent.get("prev")
                l3["_next"] = adjacent.get("next")
            except Exception:
                l3["_prev"] = None
                l3["_next"] = None

        # L0 Neo4j
        l0_scenes = await self._neo4j.get_scenes_by_emotion(emotion_val, limit=2)

        # Phase 3: 按 token 预算合并, 附加四大名著知识
        # 四大名著 RAG (轻量, top-3)
        lk_raw = await self._milvus.search_fourpaper(query_vec, top_k=5)
        lk_ranked = self._reranker.rerank(query, lk_raw) if lk_raw else []

        return {
            "L3": l3_final,
            "L2": l2_tags,
            "L0": l0_scenes,
            "L-K": lk_ranked[:3] if lk_ranked else [],
        }

    # ── academic_query: L1 + 可选 L2 ──

    async def _retrieve_academic(
        self, query: str, student_id: str
    ) -> dict:
        # L1: 从 PG 获取成绩/考勤
        scores = await self._pg.get_student_scores(student_id)
        attendance = await self._pg.get_student_attendance(student_id)

        # L2: 学科认知 (可选, 辅助解释成绩)
        traits = await self._neo4j.get_student_traits(student_id)

        return {
            "L1": {"scores": scores, "attendance": attendance},
            "L2": traits,
        }

    # ── psych_crisis: L2 危机 + L3-Cold 回源 ──

    async def _retrieve_psych_crisis(self, student_id: str) -> dict:
        traits = await self._neo4j.get_student_traits(student_id)

        # 危机相关 L3-Cold 回源
        unprocessed = await self._milvus.pull_unprocessed(student_id, limit=10)
        cold_refs = [l.get("cold_ref") for l in unprocessed if l.get("cold_ref")]
        cold_data = []
        for ref in cold_refs[:3]:
            data = await self._pg.get_l3_cold(ref)
            if data:
                cold_data.append(data)

        return {
            "L2": traits,
            "L3-Cold": cold_data,
        }

    # ── literary_query: 四大名著 RAG 检索 ──

    async def _retrieve_literary(self, query: str) -> dict:
        """检索四大名著知识库"""
        query_vec = self._embed.encode(query)

        raw = await self._milvus.search_fourpaper(query_vec, top_k=10)
        if not raw:
            return {"L-K": []}

        # Rerank
        ranked = self._reranker.rerank(query, raw) if raw else []
        top = ranked[:5] if ranked else raw[:5]

        # 按书名分组
        by_book = {}
        for r in top:
            book = r.get("book_name", "未知")
            by_book.setdefault(book, []).append(r)

        return {
            "L-K": top,
            "L-K_by_book": by_book,
        }

    # ── 辅助 ──

    def _filter_by_confidence(self, results: list[dict]) -> list[dict]:
        """按检索置信度三档过滤"""
        filtered = []
        for r in results:
            score = r.get("rerank_score", 0)
            if score >= 0.85:
                r["confidence_label"] = "高置信"
            elif score >= 0.70:
                r["confidence_label"] = "中置信"
            elif score >= 0.50:
                r["confidence_label"] = "低置信"
            else:
                continue
            filtered.append(r)
        return filtered
