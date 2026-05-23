#!/usr/bin/env python3
"""直接测试工具层，不经过 LLM"""
import asyncio
from app.agents.tools.registry import registry
from app.agents.tools import classic_search, student_query  # noqa: F401

async def main():
    print("=" * 50)
    print("1. 测试 query_student_info")
    r = await registry.execute("query_student_info", '{"student_no": "1001"}')
    print(r)

    print("=" * 50)
    print("2. 测试 query_student_score")
    r = await registry.execute("query_student_score", '{"student_no": "1001"}')
    print(r)

    print("=" * 50)
    print("3. 测试 query_employment")
    r = await registry.execute("query_employment", '{"class_no": "JAVA-01"}')
    print(r)

    print("=" * 50)
    print("4. 测试 query_statistics (class_gender)")
    r = await registry.execute("query_statistics", '{"stat_type": "class_gender"}')
    print(r)

    print("=" * 50)
    print("5. 测试 search_classic_literature")
    r = await registry.execute("search_classic_literature", '{"query": "林黛玉葬花", "book_name": "红楼梦"}')
    print(r[:500] + "...")

    print("=" * 50)
    print("所有工具测试完成")

if __name__ == "__main__":
    asyncio.run(main())
