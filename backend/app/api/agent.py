"""Agent API — 流式接口，graph.astream(stream_mode="messages") + text/plain"""
from typing import Optional, AsyncGenerator
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.graphs.sales_agent import sales_agent, SalesState

router = APIRouter(tags=["agent"])


class AgentRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="用户输入")


@router.post("/stream")
async def agent_stream(request: AgentRequest):
    try:
        async def event_generator() -> AsyncGenerator[str, None]:
            initial_state: SalesState = {
                "messages": [{"role": "user", "content": request.message}],
                "stage": "start",
                "lead_info": {},
                "is_lead": False,
            }
            async for msg_chunk, _metadata in sales_agent.astream(
                initial_state,
                stream_mode="messages",
            ):
                if msg_chunk.content:
                    yield msg_chunk.content

        return StreamingResponse(
            event_generator(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "server_error", "message": str(e)})


@router.get("/status")
async def agent_status():
    return {"status": "ok", "agent": "sales_agent", "version": "2.1.0", "architecture": "LangGraph stream_mode=messages + AsyncOpenAI stream=True"}
