# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import SecretStr

class Settings(BaseSettings):
    # LLM API 配置
    DEEPSEEK_API_KEY: SecretStr

    # 数据库配置
    DB_USER: str = "rag_user"
    DB_PASSWORD: str = "rag_password"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "rag_db"

    # 完整的数据库连接字符串
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # 嵌入模型配置
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

    # 向量数据库集合名称
    COLLECTION_NAME: str = "all_documents"

    # LLM 模型配置
    LLM_BASE_URL: str = "https://api.deepseek.com"
    LLM_MODEL_NAME: str = "deepseek-chat"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 创建一个全局可用的配置实例
settings = Settings()