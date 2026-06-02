"""Embedding 服务 — bge-large-zh-v1.5 本地推理"""

import numpy as np
from sentence_transformers import SentenceTransformer

from app.infrastructure.config import get_settings


class EmbeddingService:
    """向量化服务 — 单例, 启动时加载模型"""

    def __init__(self) -> None:
        settings = get_settings()
        model_path = settings.MILVUS__EMBEDDING_MODEL_PATH
        self._model = SentenceTransformer(model_path)
        self._dim = settings.MILVUS__DIM

    def encode(self, text: str) -> list[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def encode_array(self, text: str) -> np.ndarray:
        return self._model.encode(text, normalize_embeddings=True)

    @property
    def dim(self) -> int:
        return self._dim


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
