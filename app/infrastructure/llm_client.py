"""LLM 调用封装 — 统一 OpenAI 兼容接口"""

import json
from typing import Optional

from openai import AsyncOpenAI

from app.infrastructure.config import get_settings


class LLMClient:
    """LLM 调用客户端 — 支持主模型和 Haiku 小模型"""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.LLM__DASHSCOPE_API_KEY,
            base_url=settings.LLM__BASE_URL,
        )
        self.default_model = settings.LLM__MODEL
        self.haiku_model = settings.LLM__HAIKU_MODEL

    async def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        kwargs: dict = dict(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    async def chat_json(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.3,
    ) -> dict:
        """返回解析后的 JSON"""
        text = await self.chat(
            messages, model=model, temperature=temperature, json_mode=True
        )
        return json.loads(text)

    async def haiku(self, messages: list[dict], json_mode: bool = False) -> str:
        """使用 Haiku 小模型"""
        return await self.chat(messages, model=self.haiku_model, temperature=0.3, json_mode=json_mode)

    async def haiku_json(self, messages: list[dict]) -> dict:
        return await self.chat_json(messages, model=self.haiku_model, temperature=0.3)


_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
