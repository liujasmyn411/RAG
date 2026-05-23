#!/usr/bin/env python3
"""CRUD API 集成测试"""
import httpx
import json

BASE = "http://127.0.0.1:8080"


def login(username, password):
    r = httpx.post(f"{BASE}/api/v1/auth/login", data={"username": username, "password": password})
    return r.json()["access_token"]


def main():
    admin_token = login("admin", "admin123")
    stu_token = login("1001", "student123")
    headers = {"Authorization": f"Bearer {admin_token}"}
    stu_headers = {"Authorization": f"Bearer {stu_token}"}

    print("=== 1. 学生列表 ===")
    r = httpx.get(f"{BASE}/api/v1/students?page_size=2", headers=headers)
    print(r.status_code, r.json()["total"], "条学生")

    print("\n=== 2. 创建学生 ===")
    r = httpx.post(f"{BASE}/api/v1/students", headers=headers, json={
        "student_no": "9999",
        "name": "测试学生",
        "class_id": 3,
        "age": 20,
        "gender": "男"
    })
    print(r.status_code, r.text[:200])

    print("\n=== 3. 学生越权创建 ===")
    r = httpx.post(f"{BASE}/api/v1/students", headers=stu_headers, json={
        "student_no": "8888", "name": "越权", "class_id": 3
    })
    print(r.status_code, r.json())

    print("\n=== 4. 录入成绩 ===")
    r = httpx.post(f"{BASE}/api/v1/scores", headers=headers, json={
        "student_id": 6,
        "exam_seq": 3,
        "exam_name": "第三次月考",
        "score": 88,
        "max_score": 100
    })
    print(r.status_code, r.text[:200])

    print("\n=== 5. 统计接口 ===")
    r = httpx.get(f"{BASE}/api/v1/statistics/top-salary?limit=3", headers=headers)
    print(r.status_code, r.json())


if __name__ == "__main__":
    main()
