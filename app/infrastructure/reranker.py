"""Cross-Encoder Reranker — bge-reranker-v2-m3"""

from dataclasses import dataclass
from typing import Optional

from sentence_transformers import CrossEncoder

from app.infrastructure.config import get_settings


@dataclass
class RankedResult:
    index: int
    score: float
    item: dict


class RerankerService:
    """Reranker — 单例, 对 Milvus ANN 粗排结果精排"""

    def __init__(self) -> None:
        settings = get_settings()
        self._model = CrossEncoder(settings.RERANKER__MODEL)
        self._top_k = settings.RERANKER__TOP_K
        self._final_k = settings.RERANKER__FINAL_K

    def rerank(
        self,
        query: str,
        candidates: list[dict],
        text_field: str = "embedding_text",
    ) -> list[dict]:
        """对候选列表精排, 返回 top_k 结果

        Args:
            query: 原始用户查询
            candidates: Milvus ANN 返回的候选列表 [{text_field: str, ...}, ...]
            text_field: 候选中的文本字段名
            top_k: ANN 候选数
            final_k: Reranker 后返回数
        """
        if not candidates:
            return []

        pairs = [(query, c[text_field]) for c in candidates]
        scores = self._model.predict(pairs, show_progress_bar=False)

        ranked = sorted(
            [RankedResult(i, float(scores[i]), candidates[i]) for i in range(len(candidates))],
            key=lambda x: x.score,
            reverse=True,
        )

        return [
            {**r.item, "rerank_score": r.score}
            for r in ranked[:self._final_k]
        ]


_reranker_service: Optional[RerankerService] = None


def get_reranker_service() -> RerankerService:
    global _reranker_service
    if _reranker_service is None:
        _reranker_service = RerankerService()
    return _reranker_service
