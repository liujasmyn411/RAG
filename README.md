# 林黛玉 Agent 学生管理系统

基于 FastAPI + LangGraph + RAG 的智能学生管理系统，以林黛玉人格驱动的 AI 辅导员。

## 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | FastAPI + Pydantic |
| AI 编排 | LangGraph（节点化对话流水线） |
| LLM | 通义千问 (DashScope API) |
| 关系数据库 | MySQL 8.0 |
| 图数据库 | Neo4j（角色图谱 + 学生认知图谱） |
| 向量数据库 | Milvus（情景记忆 + 名场面检索） |
| Embedding | bge-small-zh-v1.5（512维） |
| Reranker | bge-reranker-v2-m3 |
| 前端 | 原生 HTML/CSS/JS |

## 项目结构

```
app/
├── api/                    ← 表现层（路由/控制器）
│   ├── auth.py                 POST /auth/login, /register, /me
│   ├── chat.py                 林黛玉对话 POST /chat/send
│   ├── teacher.py              教师视图 GET /teacher/*
│   ├── admin.py                管理员 POST /admin/*
│   ├── students.py, scores.py  CRUD 路由
│   ├── employment.py, classes.py, teachers.py
│   ├── statistics.py           统计分析
│   └── deps.py                 依赖注入工厂（Service/Repo 单例）
│
├── services/               ← 业务逻辑层
│   ├── chat_service.py        对话编排：安全→路由→检索→生成→后处理
│   ├── safety_service.py      安全熔断：两级检测 + 违规累积 + 账号管控
│   ├── session_service.py     会话管理：边界检测 + 归档 + carry_over
│   ├── memory_service.py      记忆检索：按 intent 多库检索 + 合并
│   ├── reflection_service.py  L3→L2 提炼：聚类 + 冲突检测 + 置信度更新
│   ├── teacher_service.py     教师报告：单生画像 + 班级聚合
│   └── admin_service.py       管理员：审计 + 知识库 + 账号控制
│
├── repositories/           ← 数据访问层 (DAO)
│   ├── business_repo.py       CRUD (StudentRepo / ScoreRepo / EmploymentRepo / ...)
│   ├── pg_repo.py             L3-Cold / session_archive / student_profile / security_log
│   ├── milvus_repo.py         L3-Hot 向量检索 + 衰减 / hlmm_scenes 名场面检索
│   └── neo4j_repo.py          L0 角色子图 / L2 认知边 CRUD / 关心边衰减
│
├── domain/                 ← 领域模型层
│   ├── enums.py               EmotionPrimary / Topic / Intent / UserRole / ...
│   ├── schemas.py             内部 Schema：ChatRequest / SafetyResult / L3Summary /
│   │                          SessionBoundary / RetrievedMemory / StudentProfileReport
│   ├── business_schemas.py    CRUD Schema：StudentCreate / ScoreCreate / EmploymentCreate
│   ├── auth_schemas.py        认证 Schema：LoginRequest / TokenResponse / RegisterRequest
│   └── entities/              领域实体 dataclass：Student / L3Snapshot / L2Cognition /
│                              SafetyEvent / CrisisAlert / ViolationRecord
│
├── infrastructure/         ← 基础设施/工具层（横向公共能力）
│   ├── config.py              pydantic-settings 配置管理（70+ 配置项）
│   ├── database.py            SQLAlchemy async engine + get_db 依赖
│   ├── security.py            JWT 鉴权 get_current_user / 角色校验
│   ├── jwt.py                 JWT 签发 create_access_token / 解码 decode_access_token
│   ├── llm_client.py          LLM 调用封装（chat / chat_json / haiku / haiku_json）
│   ├── embedding.py           bge-large-zh-v1.5 向量化服务
│   ├── classifier.py          Haiku 情绪/话题分类器
│   └── reranker.py            bge-reranker-v2-m3 重排序
│
├── agents/                 ← Agent 编排层
│   ├── daiyu_graph.py         LangGraph StateGraph 构建（7节点 + 条件边）
│   ├── state.py               AgentState TypedDict（messages / intent / safety / ...）
│   ├── nodes/                 7 个节点实现
│   │   ├── safety_filter.py      前置安全检测（两级过滤）
│   │   ├── intent_router.py      情境路由（关键词 + 危机覆盖）
│   │   ├── memory_retrieval.py   按 intent 触发多库检索
│   │   ├── context_builder.py    组装 LLM 上下文（人设 + 事实 + 记忆）
│   │   ├── response_generator.py LLM 生成 + 自纠回路
│   │   ├── fact_verifier.py      数字提取对比 + 纠正重生成
│   │   └── post_processor.py     L3-Cold/Hot 写入 + Reflection 触发
│   └── prompts/
│       ├── daiyu_persona.py      黛玉系统 Prompt
│       └── reflection.py         L3→L2 提炼 Prompt
│
├── jobs/                   ← 定时任务
│   ├── scheduler.py            APScheduler 调度器
│   ├── decay_job.py            每日衰减（Neo4j关心边 / Milvus重要性 / B2违规降级）
│   └── archive_job.py          每日归档（Cold温迁移 / 过期删除 / 冲突超时归档）
│
├── models.py               ← SQLAlchemy ORM（14 张表）
├── init_db.py              ← 一键初始化：建表 + seed 数据 + Neo4j 约束 + Milvus Collection
└── main.py                 ← 入口：挂载路由 + 静态文件 + 启动调度器
```

### 分层依赖方向

```
┌─────────────────────────────────────────────────────────────┐
│                        api (表现层)                          │
│  路由定义 / 参数校验 / 依赖注入 / 返回 JSON                   │
│  Depends(get_current_user) → 鉴权                           │
├─────────────────────────────────────────────────────────────┤
│                      services (业务层)                       │
│  编排 repositories / 调用 LLM / 事务管理                     │
├─────────────────────────────────────────────────────────────┤
│                    repositories (数据层)                      │
│  SQL / Cypher / pymilvus / 统一 DAO 接口                     │
├──────────┬──────────────────────────────────────────────────┤
│ domain   │  infrastructure (横切)             agents         │
│ 枚举     │  配置 / JWT / LLM / Embedding       LangGraph     │
│ Schema   │  / Reranker / Classifier           状态图         │
│ Entity   │  / 数据库引擎                     / 节点 / Prompt │
└──────────┴──────────────────────────────────────────────────┘

依赖方向: api → services → repositories
             ↓          ↓
          domain    infrastructure
             ↓          ↓
          agents ←── (注入 services + repos)

横向: 所有层可引用 infrastructure（工具/配置）和 domain（枚举/Schema）
```

> `main.py` 在启动时组装依赖链：`depts.py` 通过工厂函数创建 Service → Repo 单例，
> 注入到各 API 路由的 `Depends()` 中。`agents/` 的 LangGraph 节点通过闭包
> 接收 Service 实例，不直接访问 infrastructure。

## 快速开始

### 1. 环境要求

- Python 3.12+
- MySQL 8.0
- Neo4j 5.x
- Milvus 2.4+

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env` 并填入真实配置：

```env
# LLM
LLM__DASHSCOPE_API_KEY=your-api-key
LLM__MODEL=qwen-plus

# MySQL
DATABASE__URL=mysql+pymysql://user:password@localhost:3307/student_system

# Neo4j
NEO4J__URI=bolt://localhost:7687
NEO4J__USER=neo4j
NEO4J__PASSWORD=your-password

# Milvus
MILVUS__URI=http://localhost:19530
MILVUS__EMBEDDING_MODEL_PATH=./models/bge-small-zh-v1.5
MILVUS__DIM=512
```

### 4. 初始化数据库

```bash
python -m app.init_db
```

一次性创建所有 MySQL 表 + 种子数据 + Neo4j 约束/角色图谱 + Milvus Collection。

### 5. 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问 http://localhost:8000 打开前端界面。

### 6. 测试账号

| 账号 | 密码 | 角色 |
|------|------|------|
| XH_2024001 | 123456 | 学生（小红） |
| TCH_001 | 123456 | 教师（张老师） |
| ADMIN_001 | 123456 | 管理员 |

## 核心架构

### 三层记忆系统

```
L0 角色本体 (Neo4j)  →  林黛玉人设 + 红楼梦名场面 + 人物关系图谱
L2 语义认知 (Neo4j)  →  学生偏科/情绪倾向/社交模式 + 置信度动力学
L3 情景快照 (Milvus)  →  每轮对话摘要向量化 → Hot/Cold 双层存储
```

### 对话流水线 (LangGraph)

```
用户消息 → 安全过滤(前置) → 意图路由 → 三层记忆检索 → 上下文构建
         → 黛玉人设生成 → 事实校验 → 安全后处理 → 回复输出
         → 异步: Reflection 提炼 → L2/L3 记忆更新
```

### API 概览

| 前缀 | 说明 |
|------|------|
| `/auth` | 登录认证 (JWT) |
| `/chat` | 林黛玉对话 |
| `/teacher` | 教师视图（学生画像/班级聚合/危机通知） |
| `/admin` | 管理员（审计/知识库管理/账号控制） |
| `/students` | 学生 CRUD |
| `/scores` | 成绩管理 |
| `/classes` | 班级管理 |
| `/teachers` | 教师管理 |
| `/employment` | 就业管理 |
| `/statistics` | 统计分析 |

API 文档：http://localhost:8000/docs

## 数据库

| 数据库 | 用途 |
|--------|------|
| MySQL | 业务数据 / 记忆归档 / 安全日志 / 会话存档 |
| Neo4j | 角色图谱 / 学生认知图谱 / 关系边 + 置信度动力学 |
| Milvus | L3 情景向量 / 名场面向量 (ANN + Reranker) |

详细设计见 [docs/database_design.md](docs/database_design.md)。

## 安全熔断

- **前置过滤**：关键词 + LLM 语义双重检测
- **B1 政治敏感**：永久累计，3次封号
- **B2 粗鄙语言**：7天滑动窗口，5次封号，24h降1
- **心理危机**：自动通知辅导员，30分钟未确认升级至管理员
- **管理员审计**：查看 L3 原文 / 修改安全状态 / 知识库操作 全部留痕
