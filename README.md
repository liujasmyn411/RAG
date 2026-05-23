# 林黛玉Agent · 学生管理系统

基于 FastAPI + AI Agent 的学生信息管理系统，支持自然语言查询学生信息、成绩、就业数据，以及四大名著知识问答。AI 以林黛玉的形象与用户交互。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| 数据库 | MySQL 8.0 |
| ORM | SQLAlchemy 2.0 |
| 向量库 | Milvus 2.x |
| Embedding | BGE-Small-ZH-v1.5 |
| LLM | 通义千问 (DashScope) |
| 容器化 | Docker + Docker Compose |

---

## 快速启动

### 1. 配置环境

```bash
cp .env.example .env
# 编辑 .env，填入你的 DASHSCOPE_API_KEY
```

### 2. 启动基础设施

```bash
docker-compose up -d
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 初始化数据

```bash
python scripts/data/init_mysql_data.py
```

### 5. 启动服务

```bash
uvicorn app.main:app --reload --port 8000
```

### 6. 测试

```bash
curl -N -H "Accept: text/event-stream" \
  -H "Content-Type: application/json" \
  -X POST http://127.0.0.1:8000/api/v1/lin-daiyu/chat \
  -d '{"message": "查一下学生 1001 的成绩"}'
```

---

## 项目结构

```
.
├── app/                      # 应用源码
│   ├── main.py               # FastAPI 入口
│   ├── core/                 # 配置、异常、依赖注入
│   ├── api/                  # HTTP 路由层
│   ├── agents/               # AI Agent 编排层
│   ├── services/             # 业务逻辑层
│   ├── models/               # 数据访问层（ORM）
│   └── prompts/              # Prompt 模板
├── scripts/                  # 工具脚本
│   ├── rag/                  # RAG 相关（Milvus 建库、检索）
│   ├── data/                 # 数据初始化
│   └── deploy/               # 部署脚本
├── tests/                    # 测试
│   └── integration/          # 集成测试
├── docs/                     # 文档
│   ├── requirements.md       # 需求文档
│   ├── architecture.md       # 架构设计
│   └── database_design.md    # 数据库设计
├── data/                     # 数据文件
│   └── literature/           # 四大名著原文
├── models/                   # 本地 AI 模型（BGE）
├── prompts/                  # Agent Prompt 模板
├── docker-compose.yml        # 基础设施编排
├── init.sql                  # 数据库初始化脚本
└── requirements.txt          # Python 依赖
```

---

## 核心功能

- **学生信息管理**：增改查、班级管理、老师管理
- **考核成绩管理**：成绩录入、统计报表
- **就业管理**：就业信息记录、薪资排行、就业时长统计
- **AI 智能助手**：林黛玉角色扮演，自然语言查询所有数据
- **四大名著问答**：基于 RAG 的知识库问答

---

## 文档

- [需求文档](docs/requirements.md)
- [架构设计](docs/architecture.md)
- [数据库设计](docs/database_design.md)
- [实施计划](docs/plan.md)

---

## 许可证

MIT
