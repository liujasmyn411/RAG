from typing import List, Dict, Any, AsyncGenerator
from openai import AsyncOpenAI
from app.core.config import settings


class LLMClient:
    """基于 OpenAI 兼容格式的 LLM 客户端
    
    支持通义千问 DashScope 的 /compatible-mode/v1 端点。
    同时提供流式和非流式两种调用方式。
    """

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.llm_base_url,
        )
        self.model = settings.llm_model

    async def chat_complete(
        self,
        messages: List[Dict[str, str]],
    ) -> str:
        """非流式调用，返回完整文本（用于 ReAct 第一轮解析 Action）"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False,
                temperature=0.7,
                max_tokens=1024,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[LLM 调用出错: {e}]"

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        """流式调用，仅输出文字内容（用于 ReAct 第二轮输出 Final Answer）"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=1024,
            )
        except Exception as e:
            yield f"[LLM 调用出错: {e}]"
            return

        async for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content


# 全局单例
llm_client = LLMClient()
