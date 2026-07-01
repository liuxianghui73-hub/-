"""
销售 Agent - 基于 LangGraph + stream_mode="messages"
使用 AsyncOpenAI 直接调 DeepSeek，节点为 async generator + yield
不依赖 langchain / langchain-openai 等高层封装
"""
import json
import re
from typing import Dict, List, Any, TypedDict, AsyncGenerator

from openai import AsyncOpenAI
from langgraph.graph import StateGraph, END

from app.core.config import settings


# ============ 轻量消息类型（替代 langchain_core.messages.AIMessageChunk）============
class _StreamMessage:
    __slots__ = ("content",)
    def __init__(self, content: str):
        self.content = content


# ============ OpenAI Client ============
client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
    timeout=settings.OPENAI_TIMEOUT,
)


# ============ State ============
class SalesState(TypedDict):
    messages: List[Dict[str, str]]
    stage: str
    lead_info: Dict[str, Any]
    is_lead: bool


# ============ Tool 定义（OpenAI Function Calling 格式）============
EXTRACT_LEAD_INFO_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_lead_info",
        "description": "从用户消息中提取销售线索信息（预算、痛点、时间线、决策人）",
        "parameters": {
            "type": "object",
            "properties": {
                "budget": {"type": "string", "description": "预算范围"},
                "pain_points": {"type": "array", "items": {"type": "string"}, "description": "痛点列表"},
                "timeline": {"type": "string", "description": "时间线"},
                "decision_maker": {"type": "string", "description": "决策人"},
                "confidence": {"type": "number", "description": "提取置信度 0-1"},
            },
            "required": ["budget", "pain_points", "timeline", "decision_maker", "confidence"],
        },
    },
}


def mock_extract_lead_info(user_message: str) -> Dict[str, Any]:
    message_lower = user_message.lower()

    budget = "未明确"
    m = re.search(r"(\d+)\s*万", message_lower)
    if m:
        budget = f"{m.group(1)}万"

    pain_points = []
    pain_map = {
        "慢": "性能问题", "卡": "性能问题",
        "贵": "成本问题",
        "复杂": "易用性问题", "难用": "易用性问题",
        "不稳定": "稳定性问题", "崩溃": "稳定性问题",
    }
    for kw, pain in pain_map.items():
        if kw in message_lower and pain not in pain_points:
            pain_points.append(pain)
    if not pain_points:
        pain_points = ["待进一步沟通"]

    timeline = "未明确"
    time_map = {"月底": "本月底", "季度": "本季度", "年底": "年底前", "下周": "下周", "个月": "1-3个月"}
    for kw, t in time_map.items():
        if kw in message_lower:
            timeline = t
            break

    decision_maker = "未明确"
    if "cto" in message_lower or "技术总监" in message_lower:
        decision_maker = "CTO/技术总监"
    elif "采购" in message_lower:
        decision_maker = "采购经理"
    elif "老板" in message_lower or "ceo" in message_lower:
        decision_maker = "CEO/老板"

    extracted = sum([budget != "未明确", pain_points != ["待进一步沟通"], timeline != "未明确", decision_maker != "未明确"])
    confidence = round(extracted / 4, 2)

    return {"budget": budget, "pain_points": pain_points, "timeline": timeline, "decision_maker": decision_maker, "confidence": confidence}


# ============ ReAct 流式节点 (async generator + yield) ============
async def stream_reply_node(state: SalesState) -> AsyncGenerator[Dict[str, List[_StreamMessage]], None]:
    """
    流式回复节点 — LangGraph async generator
    内部三步：analyze → extract → stream reply
    每一步通过 yield AIMessageChunk 推送 token，配合 stream_mode="messages" 使用
    """
    messages = state["messages"]
    user_message = messages[-1]["content"]
    accumulated: List[Dict[str, str]] = []
    lead_info: Dict[str, Any] = {}

    # ---------- Step 1: 分析 ----------
    try:
        resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是销售线索分析专家。判断用户输入是否包含有效销售线索。"},
                {"role": "user", "content": f"用户输入：{user_message}\n\n请输出 JSON：{{\"is_lead\":true/false,\"summary\":\"...\"}}"},
            ],
            temperature=0.3,
            extra_body={"thinking": {"type": "enabled"}},
        )
        raw = resp.choices[0].message.content or ""
        try:
            s, e = raw.find("{"), raw.rfind("}") + 1
            result = json.loads(raw[s:e]) if s >= 0 else {"is_lead": False, "summary": "无法解析"}
        except json.JSONDecodeError:
            result = {"is_lead": False, "summary": "解析失败"}
    except Exception:
        result = {"is_lead": False, "summary": "分析失败"}

    is_lead = result.get("is_lead", False)
    summary = result.get("summary", "")

    # ---------- Step 2: 提取 ----------
    if is_lead:
        try:
            resp = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "从用户消息中提取销售线索信息。"},
                    {"role": "user", "content": user_message},
                ],
                tools=[EXTRACT_LEAD_INFO_TOOL],
                tool_choice={"type": "function", "function": {"name": "extract_lead_info"}},
                temperature=0.3,
            )
            msg = resp.choices[0].message
            if msg.tool_calls:
                lead_info = json.loads(msg.tool_calls[0].function.arguments)
            else:
                lead_info = mock_extract_lead_info(user_message)
        except Exception:
            lead_info = mock_extract_lead_info(user_message)
    else:
        lead_info = {}

    # ---------- Step 3: 构建 prompt ----------
    system_prompt = (
        "你是一位拥有10年经验的资深销售顾问，擅长分析客户心理，回答专业、简洁且富有亲和力。"
        "请使用 Markdown 格式回复，支持标题、列表、引用等。"
    )

    if is_lead and lead_info:
        user_prompt = f"""基于以下线索信息，生成一条专业、友好的销售跟进话术。

提取的线索信息：
- 预算：{lead_info.get('budget', '未明确')}
- 痛点：{', '.join(lead_info.get('pain_points', []))}
- 时间线：{lead_info.get('timeline', '未明确')}
- 决策人：{lead_info.get('decision_maker', '未明确')}
- 置信度：{lead_info.get('confidence', 0)}

用户原始消息：{user_message}

要求：确认理解用户需求、针对性回应痛点、提供下一步建议、使用 Markdown 格式。"""
    else:
        user_prompt = f"""对用户的消息进行友好回复。

用户消息：{user_message}

要求：表达感谢、询问更多需求细节、引导用户提供预算/时间/具体需求等信息、使用 Markdown 格式。"""

    # ---------- Step 4: 流式生成回复 ----------
    try:
        stream = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
            temperature=0.7,
            max_tokens=800,
            extra_body={"thinking": {"type": "enabled"}},
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                yield {"messages": [_StreamMessage(token)]}
    except Exception:
        yield {"messages": [_StreamMessage("[回复生成失败，请重试]")]}


# ============ 构建 Graph ============
def build_sales_agent():
    workflow = StateGraph(SalesState)
    workflow.add_node("stream_reply", stream_reply_node)
    workflow.set_entry_point("stream_reply")
    workflow.add_edge("stream_reply", END)
    return workflow.compile()


sales_agent = build_sales_agent()
