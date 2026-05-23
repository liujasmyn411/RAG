"""
手动下载 BAAI/bge-large-zh-v1.5 到本地目录
适用场景：网络环境受限，需要提前下载后拷贝到内网/离线环境
"""

import os
import sys

# 设置国内镜像
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

MODEL_NAME = "BAAI/bge-large-zh-v1.5"
SAVE_DIR = "./models/bge-large-zh-v1.5"

print(f"即将下载模型: {MODEL_NAME}")
print(f"保存路径: {os.path.abspath(SAVE_DIR)}\n")

# 方式1：通过 sentence-transformers 下载并保存
print("【方式1】使用 sentence-transformers 下载...")
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
    model.save(SAVE_DIR)
    print(f"✅ 下载完成！模型已保存到: {SAVE_DIR}\n")
except Exception as e:
    print(f"❌ 方式1失败: {e}\n")

    # 方式2：通过 huggingface_hub 下载
    print("【方式2】使用 huggingface_hub 下载...")
    try:
        from huggingface_hub import snapshot_download
        snapshot_download(repo_id=MODEL_NAME, local_dir=SAVE_DIR, local_dir_use_symlinks=False)
        print(f"✅ 下载完成！模型已保存到: {SAVE_DIR}\n")
    except Exception as e2:
        print(f"❌ 方式2也失败: {e2}\n")
        
        # 方式3：通过 ModelScope（国内镜像）
        print("【方式3】使用 ModelScope 下载...")
        try:
            from modelscope import snapshot_download
            # ModelScope 的模型 ID 格式
            model_id = "AI-ModelScope/bge-large-zh-v1.5"
            snapshot_download(model_id, cache_dir="./models")
            print(f"✅ 下载完成！请检查 ./models 目录\n")
        except Exception as e3:
            print(f"❌ 方式3也失败: {e3}\n")
            print("请尝试手动下载：")
            print(f"  1. 浏览器访问 https://hf-mirror.com/BAAI/bge-large-zh-v1.5")
            print(f"  2. 点击 Files → 下载所有文件")
            print(f"  3. 放入本地目录: {SAVE_DIR}")
            sys.exit(1)

print("=" * 60)
print("下载完成！后续使用本地模型的方式：")
print("=" * 60)
print(f"""
from sentence_transformers import SentenceTransformer

# 使用本地路径加载（无需联网）
model = SentenceTransformer("{SAVE_DIR}")

# 或者继续使用云端名称（会自动找本地缓存）
model = SentenceTransformer("{MODEL_NAME}")
""")
