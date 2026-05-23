#!/usr/bin/env python3
import httpx
import json

def test_case(name, payload):
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"{'='*60}")
    url = "http://127.0.0.1:8000/api/v1/lin-daiyu/chat"
    with httpx.stream("POST", url, json=payload, timeout=90) as response:
        for line in response.iter_lines():
            if line.strip():
                print(line)

# 测试 1: 四大名著
test_case("四大名著", {"message": "红楼梦里黛玉葬花是怎么回事？", "session_id": None})

# 测试 2: 闲聊
test_case("闲聊", {"message": "你今天心情怎么样？", "session_id": None})

# 测试 3: 统计查询
test_case("统计", {"message": "哪个班级就业薪资最高？", "session_id": None})
