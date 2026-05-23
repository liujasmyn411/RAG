#!/usr/bin/env python3
"""
语义检索脚本
"""

import numpy as np
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from pymilvus import MilvusClient

MILVUS_URI = "http://localhost:19530"
COLLECTION_NAME = "fourpaper"
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "bge-small-zh-v1.5")
BGE_QUERY_PREFIX = "为这个句子生成表示以用于检索相关文章："


def load_model():
    print("加载模型: " + MODEL_PATH)
    model = SentenceTransformer(MODEL_PATH, trust_remote_code=True)
    print("模型就绪")
    return model


def search(client: MilvusClient, model, query: str, top_k: int = 5) -> List[Dict]:
    # 编码查询
    query_text = BGE_QUERY_PREFIX + query
    query_vec = model.encode(
        [query_text],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )[0].tolist()

    # Milvus 检索
    results = client.search(
        collection_name=COLLECTION_NAME,
        data=[query_vec],
        limit=top_k,
        output_fields=["book_name", "chapter_title", "chapter_num", "chunk_index", "word_count", "content"],
    )

    # 组装结果
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


def main():
    client = MilvusClient(uri=MILVUS_URI)
    model = load_model()

    queries = [
        "孙悟空大闹天宫",
        "诸葛亮草船借箭",
        "武松打虎",
        "林黛玉葬花",
        "桃园三结义",
    ]

    for q in queries:
        print(f"\n{'='*60}")
        print(f"查询: {q}")
        print(f"{'='*60}")
        results = search(client, model, q, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"\nTop-{i}  [相似度: {r['score']:.4f}]  [{r['book']}] {r['title']}")
            print(f"  {r['content'][:200]}...")


if __name__ == "__main__":
    main()
