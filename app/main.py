"""FastAPI 应用入口"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api import auth, chat, teacher, admin, students, scores, employment, classes, teachers, statistics, nl_query
from app.jobs.scheduler import start_scheduler

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    start_scheduler()
    yield
    # 关闭时
    from app.jobs.scheduler import scheduler
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="林黛玉 Agent 学生管理系统",
    description="基于 LangGraph + Neo4j + Milvus 的记忆架构",
    version="0.1.0",
    lifespan=lifespan,
)

# API 路由（必须在静态文件挂载之前注册，保证优先级）
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(teacher.router)
app.include_router(admin.router)
app.include_router(students.router)
app.include_router(scores.router)
app.include_router(employment.router)
app.include_router(classes.router)
app.include_router(teachers.router)
app.include_router(statistics.router)
app.include_router(nl_query.router)


@app.get("/")
async def serve_frontend():
    """返回前端入口页面"""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# 挂载前端静态资源
app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
