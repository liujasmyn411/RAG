#!/usr/bin/env python3
"""
四大名著 -> Milvus 向量知识库
"""

import os
import re
import numpy as np
from typing import List, Dict
import torch
from sentence_transformers import SentenceTransformer
from pymilvus import MilvusClient, DataType

torch.set_num_threads(os.cpu_count() or 4)

MILVUS_URI = "http://localhost:19530"
COLLECTION_NAME = "fourpaper"
# 计算项目根目录（本脚本位于 scripts/rag/）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "bge-small-zh-v1.5")

BOOKS = {
    os.path.join(PROJECT_ROOT, "data", "literature", "sanguo.txt"): "三国演义",
    os.path.join(PROJECT_ROOT, "data", "literature", "shuihu.txt"):   "水浒传",
    os.path.join(PROJECT_ROOT, "data", "literature", "xiyou.txt"):   "西游记",
    os.path.join(PROJECT_ROOT, "data", "literature", "honglou.txt"):   "红楼梦",
}

CHAPTER_MAX_LEN = 800
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
BGE_DOC_PREFIX = "为这个文档生成表示以用于检索："

# 文本清洗
def clean_html_tags(text: str) -> str:
    text = re.sub('<\\s*p\\s*>', '', text, flags=re.IGNORECASE)
    text = re.sub('<\\s*/\\s*p\\s*>', '', text, flags=re.IGNORECASE)
    return text


def clean_copyright_header(lines: List[str]) -> List[str]:
    result = []
    skip_patterns = [
        '^本书由爱上阅读',
        '^声明：本书来自互联网',
        '^敬告：请在下载后',
        '^书名：',
        '^作者：',
        '^章节数：',
        '^字数：',
        '^={8,}',
        '^========简介========',
        '^========正文========',
    ]
    in_body = False
    for line in lines:
        stripped = line.strip()
        if stripped == '========正文========':
            in_body = True
            continue
        if not in_body:
            skip = False
            for pat in skip_patterns:
                if re.match(pat, stripped):
                    skip = True
                    break
            if skip:
                continue
        result.append(line)
    return result


# 章节解析
CHAPTER_PATTERNS = {
    "三国演义": re.compile('^(第[一二三四五六七八九十百千]+回\\s+.*)$'),
    "水浒传":   re.compile('^((?:楔子|第\\d+回)[：:]\\s*.*)$'),
    "西游记":   re.compile('^(第[一二三四五六七八九十百千]+回[：:]\\s*.*)$'),
    "红楼梦":   re.compile('^(第[一二三四五六七八九十百千]+回\\s+.*)$'),
}


def parse_chapters(book_name: str, raw_lines: List[str]) -> List[Dict]:
    pattern = CHAPTER_PATTERNS[book_name]
    chapters = []
    current_title = None
    current_lines = []

    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            if current_title is not None:
                chapters.append({
                    "title": current_title,
                    "text": "\n".join(current_lines).strip()
                })
            current_title = m.group(1).strip()
            current_lines = []
        else:
            if current_title is not None:
                current_lines.append(line)

    if current_title is not None:
        chapters.append({
            "title": current_title,
            "text": "\n".join(current_lines).strip()
        })

    result = []
    for i, ch in enumerate(chapters, 1):
        result.append({
            "num": i,
            "title": ch["title"],
            "text": ch["text"]
        })
    return result


# 混合切片
def split_paragraphs(text: str) -> List[str]:
    return [p.strip() for p in text.split('\n') if p.strip()]


def hybrid_split(chapters: List[Dict]) -> List[Dict]:
    chunks = []
    for ch in chapters:
        text = ch["text"]
        if len(text) <= CHAPTER_MAX_LEN:
            chunks.append({
                "title": ch["title"],
                "num": ch["num"],
                "text": text,
                "chunk_index": 0,
            })
        else:
            paragraphs = split_paragraphs(text)
            buffer = ""
            chunk_idx = 0
            for para in paragraphs:
                if len(buffer) + len(para) + 1 > CHUNK_SIZE:
                    if buffer:
                        chunks.append({
                            "title": ch["title"],
                            "num": ch["num"],
                            "text": buffer.strip(),
                            "chunk_index": chunk_idx,
                        })
                        chunk_idx += 1
                    buffer = para
                else:
                    buffer = (buffer + "\n" + para).strip() if buffer else para
            if buffer:
                chunks.append({
                    "title": ch["title"],
                    "num": ch["num"],
                    "text": buffer.strip(),
                    "chunk_index": chunk_idx,
                })
    return chunks


# 加载模型
def load_model():
    print("加载模型: " + MODEL_PATH)
    model = SentenceTransformer(MODEL_PATH, trust_remote_code=True)
    dim = model.get_embedding_dimension()
    print(f"模型就绪 | 维度: {dim} | 最大长度: {model.max_seq_length}")
    return model


# Milvus 操作
def setup_collection(client: MilvusClient):
    if client.has_collection(COLLECTION_NAME):
        print(f"Collection '{COLLECTION_NAME}' 已存在，删除重建")
        client.drop_collection(COLLECTION_NAME)

    schema = client.create_schema(auto_id=True, enable_dynamic_field=True)
    schema.add_field("id", DataType.INT64, is_primary=True)
    schema.add_field("book_name", DataType.VARCHAR, max_length=64)
    schema.add_field("chapter_title", DataType.VARCHAR, max_length=256)
    schema.add_field("chapter_num", DataType.INT64)
    schema.add_field("chunk_index", DataType.INT64)
    schema.add_field("word_count", DataType.INT64)
    schema.add_field("content", DataType.VARCHAR, max_length=65535)
    schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=512)

    client.create_collection(collection_name=COLLECTION_NAME, schema=schema)
    print(f"Collection '{COLLECTION_NAME}' 创建完成")

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        index_type="HNSW",
        metric_type="COSINE",
        params={"M": 16, "efConstruction": 200}
    )
    client.create_index(COLLECTION_NAME, index_params)
    print("HNSW 索引创建完成")

    client.load_collection(COLLECTION_NAME)
    print("Collection 已加载到内存")


def insert_batch(client: MilvusClient, data: List[Dict]):
    client.insert(collection_name=COLLECTION_NAME, data=data)


# 主流程
def main():
    model = load_model()
    all_chunks = []
    for filename, book_name in BOOKS.items():
        print(f"\n处理: {book_name} ({filename})")
        with open(filename, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()

        lines = [clean_html_tags(line) for line in raw_lines]
        lines = clean_copyright_header(lines)
        print(f"  清洗后行数: {len(lines)}")

        chapters = parse_chapters(book_name, lines)
        print(f"  解析章节数: {len(chapters)}")

        chunks = hybrid_split(chapters)
        print(f"  切片后 chunk 数: {len(chunks)}")

        for ch in chunks:
            all_chunks.append({
                "book_name": book_name,
                "chapter_title": ch["title"],
                "chapter_num": ch["num"],
                "chunk_index": ch["chunk_index"],
                "content": ch["text"],
                "word_count": len(ch["text"]),
            })

    total = len(all_chunks)
    print(f"\n总计 chunk 数: {total}")

    batch_size = 128
    print(f"开始向量化，batch_size={batch_size}...")
    texts_to_encode = [BGE_DOC_PREFIX + ch["content"] for ch in all_chunks]

    embeddings = model.encode(
        texts_to_encode,
        batch_size=batch_size,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True,
    )
    print(f"向量化完成，形状: {embeddings.shape}")

    print("\n向量化完成，连接 Milvus...")
    client = MilvusClient(uri=MILVUS_URI)
    print("连接成功")
    setup_collection(client)

    print("组装数据并插入 Milvus...")
    milvus_data = []
    for i, ch in enumerate(all_chunks):
        milvus_data.append({
            "book_name": ch["book_name"],
            "chapter_title": ch["chapter_title"],
            "chapter_num": ch["chapter_num"],
            "chunk_index": ch["chunk_index"],
            "word_count": ch["word_count"],
            "content": ch["content"],
            "embedding": embeddings[i].tolist(),
        })

    insert_batch_size = 500
    for i in range(0, len(milvus_data), insert_batch_size):
        batch = milvus_data[i:i + insert_batch_size]
        insert_batch(client, batch)
        print(f"  已插入 {i + len(batch)} / {len(milvus_data)}")

    client.flush(COLLECTION_NAME)
    stats = client.get_collection_stats(COLLECTION_NAME)
    print(f"\n完成！Collection 统计: {stats}")


if __name__ == "__main__":
    main()
