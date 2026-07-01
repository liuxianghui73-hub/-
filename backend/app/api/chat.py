"""
聊天 API 路由
提供流式对话接口
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.services.chat_service import stream_chat_response

# 创建路由器
router = APIRouter(prefix="/api", tags=["chat"])


class HistoryMessage(BaseModel):
    """历史消息模型"""
    role: str = Field(..., pattern="^(user|assistant)$", description="消息角色")
    content: str = Field(..., min_length=1, description="消息内容")


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="用户输入的消息",
    )
    role: str = Field(
        default="sales",
        pattern="^(sales|competitor|portrait)$",
        description="角色类型：sales|competitor|portrait",
    )
    history: Optional[List[HistoryMessage]] = Field(
        default=None,
        description="历史对话记录（最近 10 轮）",
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式聊天接口（Server-Sent Events）

    接收用户消息、角色类型、历史对话，逐字返回 AI 响应
    """
    try:
        # 将 Pydantic 模型转为 dict 列表
        history_dicts = None
        if request.history:
            history_dicts = [msg.model_dump() for msg in request.history]

        response_generator = stream_chat_response(
            user_message=request.message,
            role=request.role,
            history=history_dicts,
        )

        return StreamingResponse(
            response_generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "config_error", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "server_error", "message": f"服务器内部错误：{str(e)}"}
        )
