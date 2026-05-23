#!/usr/bin/env python3
"""
项目启动入口

用法:
    python main.py              # 默认启动，host=127.0.0.1, port=8000
    python main.py --host 0.0.0.0 --port 8080
    python main.py --no-reload  # 关闭热重载
"""

import sys
import argparse
import uvicorn


def parse_args():
    parser = argparse.ArgumentParser(description="林黛玉Agent · 学生管理系统")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址 (默认: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="监听端口 (默认: 8000)")
    parser.add_argument("--no-reload", action="store_true", help="关闭热重载")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数 (默认: 1)")
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 50)
    print("  林黛玉Agent · 学生管理系统")
    print("=" * 50)
    print(f"  启动模式: {'生产' if args.no_reload else '开发(热重载)'}")
    print(f"  监听地址: http://{args.host}:{args.port}")
    print(f"  API 文档: http://{args.host}:{args.port}/docs")
    print(f"  对话接口: POST http://{args.host}:{args.port}/api/v1/lin-daiyu/chat")
    print("=" * 50)

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
        workers=args.workers if args.no_reload else 1,
        log_level="info",
    )


if __name__ == "__main__":
    main()
