"""
聊天服务层
封装 DeepSeek API 调用逻辑，支持流式响应、多角色 System Prompt、上下文历史
"""
from typing import AsyncGenerator, List, Dict
from openai import AsyncOpenAI
from app.core.config import settings


# 创建异步 OpenAI 客户端（兼容 DeepSeek API）
client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
    timeout=settings.OPENAI_TIMEOUT,
)

# 角色 System Prompt 映射
SYSTEM_PROMPTS: Dict[str, str] = {
    "sales": (
        "你是一位拥有10年经验的资深销售话术顾问。"
        "你擅长撰写邮件、微信话术、电话邀约脚本，"
        "能根据不同场景和客户类型，给出专业、简洁且富有亲和力的话术建议。"
        "回答时请直接给出可用的话术模板，并简要说明使用场景。"
    ),
    "competitor": (
        "你是一位资深的市场分析师，擅长竞品分析与 SWOT 分析。"
        "你能从产品功能、定价策略、渠道布局、品牌定位等维度进行差异化对比，"
        "给出清晰的结构化分析，帮助销售团队制定竞争策略。"
    ),
    "portrait": (
        "你是一位资深的客户洞察专家，擅长客户画像分析。"
        "你能根据碎片化的客户信息（行业、职位、沟通记录、行为偏好等），"
        "推断客户性格类型、决策偏好、关注重点和潜在异议，"
        "并给出针对性的沟通策略建议。"
    ),
}

# 默认 System Prompt（兜底）
DEFAULT_SYSTEM_PROMPT = (
    "你是一位拥有10年经验的资深销售顾问，擅长分析客户心理，"
    "回答专业、简洁且富有亲和力。"
)


def _build_messages(
    role: str,
    history: List[Dict[str, str]],
    user_message: str,
) -> List[Dict[str, str]]:
    """
    构建发送给 LLM 的 messages 数组

    结构：[system] + [history...] + [user]
    System Prompt 始终在第一位，不可被覆盖
    """
    system_content = SYSTEM_PROMPTS.get(role, DEFAULT_SYSTEM_PROMPT)

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_content},
    ]

    # 拼接历史对话（已由前端截断为最近 10 轮）
    for msg in history:
        if msg.get("role") in ("user", "assistant") and msg.get("content"):
            messages.append({"role": msg["role"], "content": msg["content"]})

    # 当前用户消息
    messages.append({"role": "user", "content": user_message})

    return messages


async def stream_chat_response(
    user_message: str,
    role: str = "sales",
    history: List[Dict[str, str]] = None,
) -> AsyncGenerator[str, None]:
    """
    流式生成聊天响应（DeepSeek 深度思考模式）

    Args:
        user_message: 用户输入的消息
        role: 角色类型 (sales|competitor|portrait)
        history: 历史对话列表，每条包含 role 和 content

    Yields:
        str: 逐块返回的文本内容（SSE 格式）
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY 未配置，请在 .env 文件中设置")

    if history is None:
        history = []

    messages = _build_messages(role, history, user_message)

    try:
        stream = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            stream=True,
            extra_body={"thinking": {"type": "enabled"}},
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield f"data: {content}\n\n"

        yield "data: [DONE]\n\n"

    except Exception as e:
        error_msg = f"AI 服务调用失败：{str(e)}"
        yield f"data: {error_msg}\n\n"
        yield "data: [DONE]\n\n"
        raise
