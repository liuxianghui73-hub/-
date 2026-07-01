"""
配置管理模块
使用 pydantic-settings 从环境变量和 .env 文件加载配置
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """应用配置类"""
    
    # LLM API 配置（支持 OpenAI 兼容接口，如 DeepSeek）
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.deepseek.com"
    OPENAI_MODEL: str = "deepseek-chat"
    OPENAI_TIMEOUT: int = 60
    
    # 应用配置
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    
    # CORS 配置
    CORS_ORIGINS: str = "http://localhost:3000"
    
    # 数据库配置（预留）
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "isa_sales_agent"
    
    # 向量数据库配置（预留）
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION: str = "sales_knowledge"
    
    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # API 鉴权配置
    API_SECRET_KEY: Optional[str] = None
    
    # 速率限制配置
    RATE_LIMIT_PER_MINUTE: int = 10
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    
    # 配置来源：优先从环境变量读取，其次从 .env 文件读取
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# 创建全局配置实例
settings = Settings()


@lru_cache
def get_settings() -> Settings:
    return settings
