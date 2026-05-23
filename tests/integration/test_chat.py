#!/usr/bin/env python3
import httpx
import json

url = "http://127.0.0.1:8000/api/v1/lin-daiyu/chat"
payload = {"message": "查一下学生 1001 的成绩", "session_id": None}

print(f"POST {url}")
print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
print("-" * 50)

with httpx.stream("POST", url, json=payload, timeout=60) as response:
    if response.status_code != 200:
        print(f"HTTP Error: {response.status_code}")
        print(response.text)
    else:
        for line in response.iter_lines():
            if line.strip():
                print(line)
