"""
速率限制配置
使用 slowapi 实现基于 Redis 的速率限制
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings

# 创建 Limiter 实例
# 使用内存存储（生产环境建议使用 Redis）
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}" if settings.REDIS_HOST != "localhost" else "memory://",
    strategy="fixed-window",
)


def get_rate_limit_key(request) -> str:
    """
    获取速率限制的 key
    
    优先使用 API Key，其次使用 IP 地址
    
    Args:
        request: FastAPI Request 对象
        
    Returns:
        str: 限制 key
    """
    # 尝试从 Header 获取 API Key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api_key:{api_key}"
    
    # 否则使用 IP 地址
    return f"ip:{get_remote_address(request)}"


# 重新创建 Limiter，使用自定义 key 函数
limiter = Limiter(
    key_func=get_rate_limit_key,
    storage_uri=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}" if settings.REDIS_HOST != "localhost" else "memory://",
    strategy="fixed-window",
)
