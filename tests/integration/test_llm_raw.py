#!/usr/bin/env python3
"""诊断：直接看 LLM 原始输出"""
import asyncio
from app.agents.lin_daiyu.prompts import load_system_prompt
from app.core.llm_client import llm_client

async def main():
    prompt = load_system_prompt()
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": "查一下学生 1001 的成绩"},
    ]
    print("=" * 60)
    print("LLM 原始输出：")
    print("=" * 60)
    text = await llm_client.chat_complete(messages)
    print(text)
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
