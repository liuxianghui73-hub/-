"""
日志配置模块
使用 Loguru 实现统一 JSON 日志格式
"""
import sys
from loguru import logger
from app.core.config import settings


class JSONFormatter:
    """JSON 格式日志格式化器"""
    
    def __call__(self, record):
        """
        格式化日志记录为 JSON 格式
        
        Args:
            record: Loguru 日志记录
            
        Returns:
            str: JSON 格式的日志字符串
        """
        record["extra"]["serialized"] = (
            f'{{"timestamp":"{record["time"].isoformat()}",'
            f'"level":"{record["level"].name}",'
            f'"logger":"{record["name"]}",'
            f'"message":"{record["message"]}",'
            f'"module":"{record["module"]}",'
            f'"function":"{record["function"]}",'
            f'"line":{record["line"]}}}\n'
        )
        return "{extra[serialized]}"


class TextFormatter:
    """文本格式日志格式化器（开发环境使用）"""
    
    def __call__(self, record):
        """
        格式化日志记录为文本格式
        
        Args:
            record: Loguru 日志记录
            
        Returns:
            str: 文本格式的日志字符串
        """
        record["extra"]["serialized"] = (
            f'<green>{{time:YYYY-MM-DD HH:mm:ss}}</green> | '
            f'<level>{{level: <8}}</level> | '
            f'<cyan>{{name}}</cyan>:<cyan>{{function}}</cyan>:<cyan>{{line}}</cyan> - '
            f'<level>{{message}}</level>\n'
        )
        return "{extra[serialized]}"


def setup_logger():
    """
    配置 Loguru 日志
    
    根据环境变量 LOG_FORMAT 和 LOG_LEVEL 配置日志格式和级别
    """
    # 移除默认处理器
    logger.remove()
    
    # 根据配置选择格式化器
    if settings.LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # 添加控制台处理器
    logger.add(
        sys.stdout,
        format=formatter,
        level=settings.LOG_LEVEL,
        colorize=(settings.LOG_FORMAT != "json"),
        backtrace=True,
        diagnose=True,
    )
    
    return logger


def log_request(endpoint: str, status_code: int, latency: float, token_usage: dict = None):
    """
    记录请求日志
    
    Args:
        endpoint: 请求端点
        status_code: HTTP 状态码
        latency: 请求延迟（秒）
        token_usage: Token 使用量（包含 prompt_tokens 和 completion_tokens）
    """
    log_data = {
        "event": "request",
        "endpoint": endpoint,
        "status_code": status_code,
        "latency_ms": round(latency * 1000, 2),
    }
    
    if token_usage:
        log_data["token_usage"] = {
            "prompt_tokens": token_usage.get("prompt_tokens", 0),
            "completion_tokens": token_usage.get("completion_tokens", 0),
            "total_tokens": token_usage.get("total_tokens", 0),
        }
    
    logger.info(f"Request completed: {endpoint} | Status: {status_code} | Latency: {latency*1000:.2f}ms")


# 初始化日志
logger = setup_logger()
