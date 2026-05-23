# 林黛玉Agent 实现计划

> 与《需求.md》配套，聚焦"林黛玉Agent"单一需求的落地实施。

---

## 一、项目定位

在现有 FastAPI 学生管理系统 + 四大名著 RAG（Milvus/BGE）基础上，构建一个**角色扮演型 AI Agent**：
- **角色**：林黛玉（才情高绝、心性敏感、言语温婉机锋）
- **能力1**：回答学生信息管理系统相关问题（查 MySQL）
- **能力2**：回答四大名著相关问题（查 Milvus 向量库）
- **交互**：FastAPI SSE 流式对话接口

---

## 二、技术选型

| 层级 | 选型 | 说明 |
|------|------|------|
| LLM | 云端 API（OpenAI 兼容格式） | 原生支持 Function Calling，推荐通义千问 `qwen-plus` |
| Agent 模式 | 原生 Function Calling | 模型通过 `tools` 参数自主决策调用 |
| Web 框架 | FastAPI | 异步原生，SSE 支持完善 |
| 结构化数据 | MySQL 8.0 + SQLAlchemy 2.0 + Alembic | 按《需求.md》建库 |
| 非结构化数据 | Milvus 2.x + BGE-Small | 复用现有 `fourpaper` Collection |
| 流式输出 | SSE (`text/event-stream`) | 打字机效果，体验最佳 |
| 会话管理 | 内存 Dict（Session ID → History） | 一期先跑通，二期换 Redis |

---

## 三、项目结构

```
app/
├── main.py                      # FastAPI 入口，挂载路由
├── core/
│   ├── config.py               # Pydantic Settings（LLM Key、DB URL、Milvus URI）
│   ├── llm_client.py           # 统一 LLM Client：流式 + Function Calling
│   ├── exceptions.py           # 业务异常定义
│   └── dependencies.py         # DB Session、Milvus Client 依赖注入
├── api/
│   └── v1/
│       └── chat.py             # POST /api/v1/lin-daiyu/chat (SSE)
├── agents/
│   ├── lin_daiyu/
│   │   ├── agent.py            # Agent 主循环
│   │   ├── prompts.py          # 系统 Prompt 加载与渲染
│   │   └── memory.py           # Session 对话历史管理
│   └── tools/
│       ├── registry.py         # @tool 装饰器 + 自动发现
│       ├── classic_search.py   # 封装 rag_search → Milvus
│       └── student_query.py    # 封装 SQLAlchemy → MySQL
├── services/
│   ├── knowledge_base.py       # 知识库服务层
│   └── student_service.py      # 学生管理服务层（CRUD + 统计）
├── models/
│   ├── database.py             # SQLAlchemy Base + 引擎
│   ├── schemas.py              # Pydantic Request/Response 模型
│   └── entities/               # SQLAlchemy ORM 模型
│       ├── student.py
│       ├── score.py
│       ├── employment.py
│       ├── class_.py
│       └── teacher.py
├── prompts/
│   └── lin_daiyu_system.md     # 林黛玉系统 Prompt（Jinja2 模板）
└── alembic/                    # 数据库迁移
    └── versions/
```

---

## 四、Phase 拆解（预计 8~10 天）

### P1 基座搭建（2 天）
- [ ] 创建项目结构，补充 FastAPI / SQLAlchemy / Alembic 依赖
- [ ] `core/config.py`：环境变量统一管理（`.env` 支持）
- [ ] `core/llm_client.py`：封装云端 API，支持流式 + Function Calling
- [ ] `agents/tools/registry.py`：`@tool` 装饰器，Agent 启动时自动收集工具
- [ ] `agents/lin_daiyu/memory.py`：内存版 Session 历史（限制 10 轮，超长自动摘要）

**产出**：可运行的空壳，LLM 能 echo 回复。

### P2 数据层建设（2 天）
- [ ] 按《需求.md》定义 SQLAlchemy ORM 模型（5 张表）
- [ ] Alembic 初始化 + 生成首版迁移脚本
- [ ] `student_service.py`：封装 CRUD + 统计查询（班级人数、平均分、就业时长等）
- [ ] `knowledge_base.py`：封装 Milvus 检索，复用现有 BGE-Small 模型

**产出**：MySQL 和 Milvus 两条数据通路独立可测。

### P3 工具层开发（1 天）
注册到 Tool Registry 的 4 个原子工具：

| 工具名 | 功能 | 数据源 |
|--------|------|--------|
| `query_student_info` | 按条件查询学生基本信息 | MySQL |
| `query_student_score` | 查询学生考核成绩 | MySQL |
| `query_employment` | 查询学生就业信息 | MySQL |
| `search_classic_literature` | 在四大名著中语义检索 | Milvus |

**产出**：每个工具独立可测，Agent 通过描述自动发现。

### P4 Agent 核心（2 天）
- [ ] 编写 `prompts/lin_daiyu_system.md`（角色定义 + 工具描述 + few-shot 示例）
- [ ] `agents/lin_daiyu/agent.py` 主循环：
  1. 接收用户消息 + Session 历史
  2. 调用 LLM（带 `tools`）
  3. 若返回 `tool_calls`：执行工具 → 获取 Observation → 再次调用 LLM
  4. 若返回普通消息：流式输出最终回答
- [ ] 流式事件设计（SSE）：`thinking` / `tool_call` / `tool_result` / `message`

**产出**：Agent 能自动选择工具，并以林黛玉口吻生成回答。

### P5 接口层（1 天）
- [ ] `POST /api/v1/lin-daiyu/chat`
- [ ] SSE 流式响应（EventSource 格式）
- [ ] Session ID 管理（Header `X-Session-Id`）
- [ ] 全局异常捕获与兜底

**产出**：前端可对接的标准 API。

### P6 调优迭代（2 天）
- [ ] Prompt 调优：查不到数据时的委婉表达（"许是簿子上没记着"）
- [ ] 边界 case：无关问题（略带傲娇拒绝）、超长上下文、跨工具查询
- [ ] 性能测试：LLM 首 token 延迟、DB 查询耗时、Milvus 召回率

**产出**：可用 Demo，具备演示条件。

---

## 五、关键技术细节

### 5.1 LLM Client：流式 Function Calling

云端 API 的流式 Function Calling 需要处理 `delta.tool_calls` 的累积：

```
第一次 chunk: delta.tool_calls[0].id = "call_xxx", function.name = "query_..."
第二次 chunk: delta.tool_calls[0].function.arguments = "{\"stu"
第三次 chunk: delta.tool_calls[0].function.arguments += "dent_id\": \"10"
... 
直到 arguments 完整
```

Client 层需要：
1. 累积流式 tool_call 片段
2. 完整后解析 JSON arguments
3. Agent 层执行对应 Tool
4. 把 Tool 结果以 `tool` role 塞回 messages
5. 再次调用 LLM，此时流式输出的是最终文字回答

### 5.2 SSE 事件协议

前端通过 `EventSource` 连接，事件类型如下：

| 事件名 | 内容 | 时机 |
|--------|------|------|
| `thinking` | `{"content": "用户问的是学生成绩..."}` | LLM 开始推理 |
| `tool_call` | `{"name": "query_student_score", "arguments": {...}}` | 决定调用工具 |
| `tool_result` | `{"name": "...", "result": "..."}` | 工具执行完毕 |
| `message` | `{"content": "这功课簿子..."}` | 最终回答文字流 |
| `done` | `{"session_id": "..."}` | 全部结束 |
| `error` | `{"code": "...", "message": "..."}` | 发生异常 |

### 5.3 林黛玉角色深度（L2 性格层）

不做 L1（太像 Siri 套壳），也不做 L3（工程量过大），定位 **L2**：

- **语气**：用词雅致，"罢""也""倒""罢了"等语气词自然融入
- **情绪**：对成绩差的学生表示惋惜（"可惜了一块美玉"），而非批评
- **偏好**：提及《红楼梦》时反应更热烈，略带自嘲
- **边界**：拒绝暴露 AI 身份，把"查数据库"转译为"翻阅簿册"
- **长度**：回答控制在 200 字以内，用户要求详细时再展开

### 5.4 数据库模型概要

按《需求.md》提取：

- **students**: 学生编号、班级、姓名、籍贯、毕业院校、专业、入学/毕业时间、学历、顾问编号、年龄、性别、逻辑删除标志
- **scores**: 学生编号、考核序次、成绩
- **employments**: 学生编号、就业开放时间、offer 下发时间、就业公司、就业薪资、冗余字段（姓名、班级）
- **classes**: 班级编号、开课时间、班主任、授课老师
- **teachers**: 老师信息、带班信息

统计查询（平均分、不及格人数、就业时长等）在 `student_service.py` 中封装为 Service 方法，Agent 通过 Tool 调用，而非直接写 SQL。

---

## 六、风险与应对

| 风险 | 可能性 | 应对策略 |
|------|--------|---------|
| 云端 API 首 token 延迟高（>3s） | 中 | SSE 先发送 `thinking` 事件，给用户反馈；必要时加 Loading 文案 |
| Function Calling 不稳定（模型不调用工具直接瞎编） | 中 | Prompt 中加 few-shot 示例 + 明确规则"涉及数据必须调用工具" |
| 林黛玉语气太浓导致信息不清 | 低 | Prompt 强调"准确第一，文采第二"，L2 不做过度转译 |
| Session 内存泄漏 | 低 | 单 Session 限制 10 轮，应用重启时清空（一期方案） |
| Milvus 未启动或 Collection 缺失 | 低 | 启动时检查连接，缺失时报错提示运行 `rag_milvus.py` |

---

## 七、待确认事项

1. **具体云 API 厂商**：通义千问（DashScope）/ 智谱（Zhipu）/ OpenAI / 兼容层？
   - 不同厂商的流式 Function Calling 字段结构略有差异，确认后 `llm_client.py` 可直接对准实现。

2. **MySQL 连接信息**：数据库是否已部署？连接地址、账号密码？
   - 若已有，直接配置；若没有，可用 Docker Compose 一键拉起。

---

## 八、产出物清单

| 文件/目录 | 说明 |
|-----------|------|
| `app/main.py` | FastAPI 入口 |
| `app/core/llm_client.py` | LLM 统一客户端 |
| `app/agents/lin_daiyu/` | Agent 核心（Prompt + 循环 + 记忆） |
| `app/agents/tools/` | 工具注册 + 4 个原子工具 |
| `app/services/` | Service 层（MySQL + Milvus） |
| `app/models/entities/` | SQLAlchemy ORM 模型 |
| `app/prompts/lin_daiyu_system.md` | 角色 Prompt 模板 |
| `alembic/versions/` | 数据库迁移脚本 |
| `.env.example` | 环境变量模板 |
| `docker-compose.yml`（可选） | MySQL + Milvus 一键开发环境 |

---

*计划制定时间：2026-05-23*
*下一步：确认"待确认事项"后，进入 P1 编码阶段。*
