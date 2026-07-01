"""
ISA-Sales-Agent 后端主入口
FastAPI 应用实例与路由注册
"""
import time
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.api.chat import router as chat_router
from app.api.agent import router as agent_router
from app.core.config import settings
from app.core.logging import logger
from app.core.security import verify_api_key
from app.core.rate_limit import limiter

# 创建 FastAPI 应用实例
app = FastAPI(
    title="ISA Sales Agent API",
    description="智能销售助手后端服务",
    version="1.0.0",
)

# 配置速率限制
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 配置 CORS 中间件（支持多环境）
cors_origins = [
    "http://localhost:3000",  # 本地开发
    "http://frontend:3000",   # Docker 网络
    "http://127.0.0.1:3000",  # 本地备用
]

# 如果配置了额外的 CORS 来源，添加到列表
if settings.CORS_ORIGINS:
    extra_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
    cors_origins.extend(extra_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 全局异常处理器 ============

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器
    捕获所有未处理的异常，返回统一格式
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "服务器内部错误，请稍后重试",
            "detail": str(exc) if settings.APP_DEBUG else None,
        }
    )


# ============ 请求日志中间件 ============

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    请求日志中间件
    记录每次请求的 endpoint、status_code、latency
    """
    start_time = time.time()
    
    # 处理请求
    response = await call_next(request)
    
    # 计算延迟
    latency = time.time() - start_time
    
    # 记录日志
    logger.info(
        f"Request: {request.method} {request.url.path} | "
        f"Status: {response.status_code} | "
        f"Latency: {latency*1000:.2f}ms | "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    return response


# ============ 注册路由 ============

# 健康检查接口（无需鉴权）
@app.get("/health")
@limiter.limit("100/minute")
async def health_check(request: Request):
    return {
        "status": "ok",
        "version": "1.0.0",
        "services": {
            "chat": "available",
            "agent": "available",
        }
    }


app.include_router(chat_router, dependencies=[Depends(verify_api_key)])
app.include_router(agent_router, prefix="/api/agent", dependencies=[Depends(verify_api_key)])


# ============ 启动事件 ============

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"Starting ISA Sales Agent API v1.0.0")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"CORS Origins: {cors_origins}")
    logger.info(f"Rate Limit: {settings.RATE_LIMIT_PER_MINUTE}/minute")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("Shutting down ISA Sales Agent API")
