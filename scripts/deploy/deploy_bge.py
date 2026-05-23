"""
BAAI/bge-large-zh-v1.5 本地部署与使用脚本
模型大小：约 400MB | 向量维度：1024 | 中文语义效果顶尖
"""

import os
import sys
import numpy as np
from typing import List, Union

# ============================================================
# 配置下载源
# ============================================================
# HuggingFace 国内镜像（二选一）
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

MODEL_NAME = "BAAI/bge-large-zh-v1.5"
LOCAL_DIR = "./models/bge-large-zh-v1.5"

# ============================================================
# 加载模型（优先本地，其次自动下载）
# ============================================================
print("正在加载模型 BAAI/bge-large-zh-v1.5 ...")

from sentence_transformers import SentenceTransformer

# 判断本地是否存在
if os.path.exists(LOCAL_DIR) and os.path.isdir(LOCAL_DIR):
    print(f"发现本地模型: {LOCAL_DIR}")
    model_path = LOCAL_DIR
else:
    print("本地未找到模型，尝试自动下载...")
    print("（约 400MB，请耐心等待）\n")
    model_path = MODEL_NAME

try:
    model = SentenceTransformer(model_path, trust_remote_code=True)
except Exception as e:
    print(f"加载失败: {e}")
    print("\n【备用方案】尝试从 ModelScope 下载...")
    try:
        from modelscope import snapshot_download
        # ModelScope 模型 ID
        ms_model_id = "AI-ModelScope/bge-large-zh-v1.5"
        model_path = snapshot_download(ms_model_id, cache_dir="./models")
        print(f"ModelScope 下载完成: {model_path}")
        model = SentenceTransformer(model_path, trust_remote_code=True)
    except Exception as e2:
        print(f"自动下载均失败: {e2}")
        print("\n请手动下载模型文件：")
        print("  方式A：浏览器访问 https://modelscope.cn/models/AI-ModelScope/bge-large-zh-v1.5")
        print("  方式B：浏览器访问 https://hf-mirror.com/BAAI/bge-large-zh-v1.5")
        print(f"  下载全部文件后放入: {os.path.abspath(LOCAL_DIR)}")
        sys.exit(1)

print(f"\n模型加载完成！")
print(f"向量维度: {model.get_sentence_embedding_dimension()}")
print(f"最大输入长度: {model.max_seq_length}\n")


# ============================================================
# 保存到本地（如果是从云端下载的，建议执行一次保存）
# ============================================================
if model_path == MODEL_NAME and not os.path.exists(LOCAL_DIR):
    print(f"正在将模型保存到本地: {LOCAL_DIR} ...")
    try:
        model.save(LOCAL_DIR)
        print(f"✅ 已保存到: {os.path.abspath(LOCAL_DIR)}\n")
    except Exception as e:
        print(f"保存失败（不影响使用）: {e}\n")


# ============================================================
# 基础用法：文本转向量
# ============================================================
def encode_texts(texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
    """
    将文本列表转换为向量
    
    Args:
        texts: 单条文本或文本列表
        batch_size: 批处理大小，显存大可调大
    
    Returns:
        归一化后的向量（L2归一化，方便直接计算余弦相似度）
    """
    if isinstance(texts, str):
        texts = [texts]
    
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=len(texts) > 100
    )
    return embeddings


# ============================================================
# 相似度计算
# ============================================================
def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """计算两个向量间的余弦相似度（输入需已归一化）"""
    return float(np.dot(vec1, vec2))


def similarity_matrix(embeddings1: np.ndarray, embeddings2: np.ndarray) -> np.ndarray:
    """计算两组向量间的相似度矩阵"""
    return np.dot(embeddings1, embeddings2.T)


# ============================================================
# 向量检索：从文档库中找出最相似的 Top-K
# ============================================================
def search(
    query: str,
    doc_embeddings: np.ndarray,
    documents: List[str],
    top_k: int = 3,
    use_instruction: bool = True
) -> List[dict]:
    """
    语义检索：根据查询找出最相关的文档
    
    Args:
        query: 查询语句
        doc_embeddings: 文档向量矩阵（需已归一化）
        documents: 原文档列表
        top_k: 返回前 K 个结果
        use_instruction: 是否使用检索指令前缀
    
    Returns:
        [{"text": ..., "score": ...}, ...]
    """
    if use_instruction:
        query_emb = encode_texts("为这个句子生成表示以用于检索相关文章：" + query)
    else:
        query_emb = encode_texts(query)
    
    scores = np.dot(query_emb, doc_embeddings.T)[0]
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        results.append({
            "text": documents[idx],
            "score": round(float(scores[idx]), 4)
        })
    return results


# ============================================================
# 演示代码
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("【演示1】基础文本向量化")
    print("=" * 60)
    
    texts = [
        "机器学习是人工智能的一个分支",
        "深度学习是机器学习的一种方法",
        "今天天气真好，适合去公园散步"
    ]
    
    embeddings = encode_texts(texts)
    print(f"输入文本数: {len(texts)}")
    print(f"输出向量形状: {embeddings.shape}")
    print(f"向量示例（前10维）: {embeddings[0][:10]}\n")
    
    print("=" * 60)
    print("【演示2】语义相似度计算")
    print("=" * 60)
    
    sim_matrix = similarity_matrix(embeddings, embeddings)
    for i in range(len(texts)):
        for j in range(len(texts)):
            print(f"  [{i}]-[{j}] 相似度: {sim_matrix[i][j]:.4f}")
    
    print("\n" + "=" * 60)
    print("【演示3】语义检索（RAG 场景）")
    print("=" * 60)
    
    docs = [
        "Python 是一种高级编程语言，语法简洁优雅",
        "FastAPI 是一个基于 Python 的高性能 Web 框架",
        "学生管理系统需要包含学生信息、成绩和就业模块",
        "机器学习让计算机能够从数据中学习规律",
        "《红楼梦》是清代曹雪芹创作的长篇小说"
    ]
    
    print(f"文档库共 {len(docs)} 条：")
    for i, d in enumerate(docs):
        print(f"  [{i}] {d}")
    
    doc_prefix = "为这个文档生成表示以用于检索："
    doc_embeddings = encode_texts([doc_prefix + d for d in docs])
    
    queries = ["怎么开发 Web 接口", "四大名著相关", "人工智能是什么"]
    
    for q in queries:
        print(f"\n查询: 「{q}」")
        results = search(q, doc_embeddings, docs, top_k=2, use_instruction=True)
        for rank, res in enumerate(results, 1):
            print(f"  Top-{rank} [相似度 {res['score']}] {res['text']}")
    
    print("\n[OK] 全部演示完成！")
