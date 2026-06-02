"""配置管理 — 基于 pydantic-settings 从 .env 加载"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    # LLM
    LLM__DASHSCOPE_API_KEY: str = ""
    LLM__MODEL: str = "qwen-plus"
    LLM__BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM__HAIKU_MODEL: str = "qwen-turbo"

    # Milvus
    MILVUS__URI: str = "http://localhost:19530"
    MILVUS__COLLECTION: str = "fourpaper"
    MILVUS__EMBEDDING_MODEL_PATH: str = "./models/bge-large-zh-v1.5"
    MILVUS__DIM: int = 768
    MILVUS__L3_COLLECTION: str = "l3_hot_memories"
    MILVUS__HLMM_COLLECTION: str = "hlmm_scenes"

    # Database
    DATABASE__URL: str = "mysql+pymysql://student:student123@localhost:3307/student_system"
    DATABASE__POOL_SIZE: int = 10
    DATABASE__MAX_OVERFLOW: int = 20

    # Neo4j
    NEO4J__URI: str = "bolt://localhost:7687"
    NEO4J__USER: str = "neo4j"
    NEO4J__PASSWORD: str = "password"

    # Reranker
    RERANKER__MODEL: str = "BAAI/bge-reranker-v2-m3"
    RERANKER__TOP_K: int = 20
    RERANKER__FINAL_K: int = 5

    # Reflection
    REFLECTION__TRIGGER_COUNT: int = 5
    REFLECTION__TRIGGER_HOURS: int = 168
    REFLECTION__MAX_L3_BATCH: int = 30
    REFLECTION__MAX_PER_GROUP: int = 15

    # Session
    SESSION__TIMEOUT_MINUTES: int = 30
    SESSION__CLOSING_MINUTES: int = 5
    SESSION__EXPIRE_HOURS: int = 24

    # 遗忘
    DECAY__EMOTION_LAMBDA: float = 0.01
    DECAY__FACT_LAMBDA: float = 0.05
    DECAY__CRISIS_LAMBDA: float = 0.005
    DECAY__RECOVERY_LAMBDA: float = 0.05
    DECAY__RECOVERY_CAP: float = 0.70

    # 存储生命周期
    STORAGE__COLD_WARM_DAYS: int = 30
    STORAGE__COLD_DELETE_DAYS: int = 90
    STORAGE__COLD_HIGHIMP_DAYS: int = 180
    STORAGE__CONTRADICTION_TIMEOUT_DAYS: int = 30
    STORAGE__DRAFT_RETENTION_DAYS: int = 60

    # 安全
    SAFETY__B2_WINDOW_DAYS: int = 7
    SAFETY__B2_BLOCK_THRESHOLD: int = 5
    SAFETY__B1_BLOCK_THRESHOLD: int = 3

    # JWT
    JWT_SECRET_KEY: str = "daiyu-agent-secret-key-change-in-production"

    # 检索
    RETRIEVAL__HIGH_CONFIDENCE: float = 0.85
    RETRIEVAL__MID_CONFIDENCE: float = 0.70
    RETRIEVAL__LOW_CONFIDENCE: float = 0.50


@lru_cache()
def get_settings() -> Settings:
    return Settings()
