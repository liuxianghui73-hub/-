"""
安全认证模块
API Key 鉴权逻辑
"""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

# API Key Header 定义
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    验证 API Key
    
    Args:
        api_key: 从 X-API-Key Header 中读取的 API Key
        
    Returns:
        str: 验证通过的 API Key
        
    Raises:
        HTTPException: 403 如果 API Key 无效或缺失
    """
    # 如果未配置 API_SECRET_KEY，则跳过鉴权（开发环境）
    if not settings.API_SECRET_KEY:
        return api_key or "development"
    
    # 验证 API Key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "missing_api_key",
                "message": "缺少 API Key，请在 Header 中携带 X-API-Key"
            }
        )
    
    if api_key != settings.API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "invalid_api_key",
                "message": "API Key 无效"
            }
        )
    
    return api_key


def get_api_key_dependency():
    """
    获取 API Key 依赖（用于路由注入）
    
    Returns:
        Callable: verify_api_key 函数
    """
    return verify_api_key
