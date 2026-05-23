from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.models.database import Base, engine
from app.api.v1 import chat, auth, students, scores, employments, statistics

# 创建所有表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="林黛玉Agent · 学生信息管理系统",
    description="一个能查学生信息、能聊四大名著的林黛玉角色扮演 AI Agent",
    version="0.1.0",
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# API 路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
app.include_router(scores.router, prefix="/api/v1")
app.include_router(employments.router, prefix="/api/v1")
app.include_router(statistics.router, prefix="/api/v1")


@app.get("/")
def root():
    return RedirectResponse(url="/static/chat.html")


@app.get("/health")
def health_check():
    return {"status": "ok"}
