from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    dashscope_api_key: str
    llm_model: str = "qwen-plus"
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    milvus_uri: str = "http://localhost:19530"
    milvus_collection: str = "fourpaper"
    embedding_model_path: str = "./models/bge-small-zh-v1.5"

    database_url: str = "sqlite:///./student_system.db"

    # JWT 配置
    jwt_secret_key: str = "student-system-dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_days: int = 7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
