# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import SecretStr, Field
from datetime import timedelta

class Settings(BaseSettings):
    # LLM API 配置
    DEEPSEEK_API_KEY: SecretStr = Field(default=SecretStr(""), description="DeepSeek API密钥，从环境变量读取")

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
    
    # 异步数据库连接字符串
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # 嵌入模型配置
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

    # 向量数据库集合名称
    COLLECTION_NAME: str = "all_documents"

    # LLM 模型配置
    LLM_BASE_URL: str = "https://api.deepseek.com"
    LLM_MODEL_NAME: str = "deepseek-chat"

    SECRET_KEY: SecretStr = Field(default=SecretStr("a_very_secret_key_that_you_should_change"), description="用于签名 JWT 的密钥")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # Token 有效期：7天
    
    @property
    def ACCESS_TOKEN_EXPIRE_DELTA(self) -> timedelta:
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

# 创建一个全局可用的配置实例
try:
    settings = Settings()
except Exception as e:
    raise ValueError(f"配置加载失败，请检查环境变量是否正确设置: {e}")