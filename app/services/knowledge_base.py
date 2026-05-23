import os
from typing import List, Dict, Optional
import numpy as np
from pymilvus import MilvusClient
from app.core.config import settings

# 全局单例（懒加载）
_model = None
_client = None

BGE_QUERY_PREFIX = "为这个句子生成表示以用于检索相关文章："


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        path = settings.embedding_model_path
        if not os.path.exists(path):
            raise FileNotFoundError(f"Embedding 模型未找到: {path}")
        _model = SentenceTransformer(path, trust_remote_code=True)
    return _model


def _get_client() -> MilvusClient:
    global _client
    if _client is None:
        _client = MilvusClient(uri=settings.milvus_uri)
    return _client


def search_classic(
    query: str,
    book_name: Optional[str] = None,
    top_k: int = 5,
) -> List[Dict]:
    """在四大名著知识库中语义检索

    Args:
        query: 查询内容
        book_name: 限定书名（三国演义/水浒传/西游记/红楼梦），None 则搜索全部
        top_k: 返回条数
    """
    model = _get_model()
    client = _get_client()

    query_text = BGE_QUERY_PREFIX + query
    query_vec = model.encode(
        [query_text],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )[0].tolist()

    filter_expr = None
    if book_name:
        filter_expr = f'book_name == "{book_name}"'

    results = client.search(
        collection_name=settings.milvus_collection,
        data=[query_vec],
        limit=top_k,
        filter=filter_expr,
        output_fields=["book_name", "chapter_title", "chapter_num", "chunk_index", "word_count", "content"],
    )

    output = []
    for hits in results:
        for hit in hits:
            output.append({
                "book": hit["entity"]["book_name"],
                "title": hit["entity"]["chapter_title"],
                "chapter_num": hit["entity"]["chapter_num"],
                "chunk_index": hit["entity"]["chunk_index"],
                "word_count": hit["entity"]["word_count"],
                "content": hit["entity"]["content"],
                "score": hit["distance"],
            })
    return output
