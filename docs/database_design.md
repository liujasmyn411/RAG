# 林黛玉 Agent 学生管理系统：数据库设计

本文档描述三数据库（PostgreSQL / Milvus / Neo4j）的完整 Schema 设计。

---

## 1. 三数据库分工总览

```
┌──────────────────────────────────────────────────────────────────────┐
│                         三数据库分工                                   │
│                                                                      │
│  PostgreSQL (关系)              Milvus (向量)         Neo4j (图)       │
│  ═══════════════               ═══════════          ════════         │
│                                                                      │
│  业务数据:                      情景摘要:             角色图谱:         │
│  · students                    · l3_hot_memories     · Character     │
│  · scores                       (partitioned         · Scene         │
│  · attendance                    by student_id)      · [:RELATED_TO] │
│  · classes / teachers                                   [:APPEARS_IN]│
│  · users                       名场面:                              │
│                                 · hlmm_scenes        语义认知:        │
│  记忆归档:                          (shared)          · Student       │
│  · l3_cold (原文)                                    · Subject/Trait │
│  · session_archive                                    · [:偏科]等     │
│  · student_profile                                                   │
│                                                    跨层桥接:          │
│  安全与运维:                                         · [:关心]        │
│  · security_log                                                        │
│  · admin_audit_log                                                     │
│  · thread_session_map                                                  │
│                                                                      │
│  查询方式: SQL                  查询方式: ANN+过滤    查询方式: Cypher │
│  一致性:  强一致                一致性:  最终一致      一致性:  强一致  │
│  更新频率: 实时                 更新频率: 每轮对话     更新频率: Reflection│
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. PostgreSQL（关系数据库）

### 2.1 表清单

```
PostgreSQL
├── 业务表 (原有)
│   ├── students          学籍信息
│   ├── scores            成绩记录
│   ├── attendance        考勤记录
│   ├── classes           班级信息
│   ├── teachers          教师信息
│   └── users             用户登录
│
├── 记忆表 (新增)
│   ├── l3_cold           L3 原始对话归档
│   ├── session_archive   会话归档
│   └── student_profile   学生档案 (跨会话累计)
│
├── 安全表 (新增)
│   ├── security_log      安全事件日志
│   └── admin_audit_log   管理员操作审计
│
└── 运行时表 (新增)
    └── thread_session_map  LangGraph thread 映射
```

### 2.2 业务表

```sql
-- ── 学生学籍 ──
CREATE TABLE students (
    student_id   VARCHAR(32) PRIMARY KEY,       -- XH_2024001
    name         VARCHAR(64) NOT NULL,
    class_name   VARCHAR(32) NOT NULL,           -- 初二3班
    teacher_id   VARCHAR(32) NOT NULL,           -- 辅导员
    gender       VARCHAR(4),
    birth_date   DATE,
    enrollment_date DATE,
    created_at   TIMESTAMP DEFAULT NOW(),
    updated_at   TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_students_class ON students(class_name);
CREATE INDEX idx_students_teacher ON students(teacher_id);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| student_id | VARCHAR(32) PK | 学号, XH_2024001 |
| name | VARCHAR(64) | 姓名 |
| class_name | VARCHAR(32) | 班级名 |
| teacher_id | VARCHAR(32) | 辅导员 ID |
| gender | VARCHAR(4) | 性别 |
| birth_date | DATE | 出生日期 |
| enrollment_date | DATE | 入学日期 |

```sql
-- ── 成绩记录 ──
CREATE TABLE scores (
    id           BIGINT PRIMARY KEY AUTO_INCREMENT,
    student_id   VARCHAR(32) NOT NULL,
    subject      VARCHAR(32) NOT NULL,           -- 数学 / 语文 / 英语 ...
    score        DECIMAL(5,1) NOT NULL,
    exam_date    DATE NOT NULL,
    exam_type    VARCHAR(16) DEFAULT '月考',      -- 月考 / 期中 / 期末
    rank_total   INT,                            -- 年级排名
    rank_class   INT,                            -- 班级排名
    created_at   TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);
CREATE INDEX idx_scores_student ON scores(student_id);
CREATE INDEX idx_scores_subject ON scores(student_id, subject);
CREATE INDEX idx_scores_date ON scores(exam_date);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | 自增 |
| student_id | VARCHAR(32) FK | 学号 |
| subject | VARCHAR(32) | 学科 |
| score | DECIMAL(5,1) | 分数 |
| exam_date | DATE | 考试日期 |
| exam_type | VARCHAR(16) | 月考/期中/期末 |
| rank_total | INT | 年级排名 |
| rank_class | INT | 班级排名 |

```sql
-- ── 考勤记录 ──
CREATE TABLE attendance (
    id           BIGINT PRIMARY KEY AUTO_INCREMENT,
    student_id   VARCHAR(32) NOT NULL,
    date         DATE NOT NULL,
    status       VARCHAR(16) NOT NULL,           -- present / absent / late / leave
    reason       VARCHAR(256),
    created_at   TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);
CREATE INDEX idx_attendance_student ON attendance(student_id);
CREATE INDEX idx_attendance_date ON attendance(date);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | 自增 |
| student_id | VARCHAR(32) FK | 学号 |
| date | DATE | 日期 |
| status | VARCHAR(16) | present/absent/late/leave |
| reason | VARCHAR(256) | 请假/缺勤原因 |

```sql
-- ── 班级 ──
CREATE TABLE classes (
    class_name   VARCHAR(32) PRIMARY KEY,        -- 初二3班
    grade        VARCHAR(16) NOT NULL,           -- 初二
    teacher_id   VARCHAR(32) NOT NULL
);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| class_name | VARCHAR(32) PK | 班级名 |
| grade | VARCHAR(16) | 年级 |
| teacher_id | VARCHAR(32) | 班主任 ID |

```sql
-- ── 教师 ──
CREATE TABLE teachers (
    teacher_id   VARCHAR(32) PRIMARY KEY,
    name         VARCHAR(64) NOT NULL,
    department   VARCHAR(64),
    title        VARCHAR(32)                     -- 辅导员 / 班主任 / 年级主任
);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| teacher_id | VARCHAR(32) PK | 教师 ID |
| name | VARCHAR(64) | 姓名 |
| department | VARCHAR(64) | 院系/部门 |
| title | VARCHAR(32) | 职称 |

```sql
-- ── 用户登录 ──
CREATE TABLE users (
    user_id      VARCHAR(32) PRIMARY KEY,
    role         ENUM('student','teacher','admin') NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    disabled     BOOLEAN DEFAULT FALSE,
    created_at   TIMESTAMP DEFAULT NOW()
);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| user_id | VARCHAR(32) PK | 用户 ID |
| role | ENUM | student/teacher/admin |
| password_hash | VARCHAR(256) | 密码哈希 |
| disabled | BOOLEAN | 是否禁用 |

### 2.3 记忆表

```sql
-- ── L3 原始对话归档 (Cold 层) ──
CREATE TABLE l3_cold (
    cold_id      VARCHAR(128) PRIMARY KEY,       -- pg_l3_raw_20260529_XH_2024001_sess_xxx
    student_id   VARCHAR(32) NOT NULL,
    session_id   VARCHAR(64) NOT NULL,
    raw_dialogue JSON NOT NULL,                  -- [{role, content, timestamp}, ...]
    crisis_flag  BOOLEAN DEFAULT FALSE,          -- 危机对话永久保留
    importance   FLOAT DEFAULT 0.5,
    need_reprocess BOOLEAN DEFAULT FALSE,        -- 提取失败, 待重试
    created_at   TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_l3_cold_student ON l3_cold(student_id);
CREATE INDEX idx_l3_cold_created ON l3_cold(created_at);
CREATE INDEX idx_l3_cold_crisis ON l3_cold(crisis_flag, created_at);
-- 生命周期: Day0-30 热归档 → Day31-90 温归档 → Day91+ 删除 (危机除外)
```

| 字段 | 类型 | 说明 |
|---|---|---|
| cold_id | VARCHAR(128) PK | pg_l3_raw_{date}_{student_id}_{session_id} |
| student_id | VARCHAR(32) | 学号 |
| session_id | VARCHAR(64) | 会话 ID |
| raw_dialogue | JSON | `[{role, content, timestamp}, ...]` |
| crisis_flag | BOOLEAN | 危机对话永久保留 |
| importance | FLOAT | 重要性 0~1 |
| need_reprocess | BOOLEAN | 提取失败标记, 定时任务重试 |

```sql
-- ── 会话归档 ──
CREATE TABLE session_archive (
    session_id       VARCHAR(64) PRIMARY KEY,
    student_id       VARCHAR(32) NOT NULL,
    closed_at        TIMESTAMP NOT NULL,
    close_reason     VARCHAR(16) NOT NULL,       -- timeout / explicit / admin
    summary          TEXT,                       -- 对话摘要 (≤300字)
    safety_snapshot  JSON,                       -- 关闭时的安全状态快照
    last_intent      VARCHAR(32),                -- 最后一个 intent
    last_topic       VARCHAR(64),                -- 最后一个话题
    unclosed_topic   VARCHAR(256),               -- 未完成的话题/约定
    message_count    INT DEFAULT 0,
    created_at       TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_session_archive_student ON session_archive(student_id);
CREATE INDEX idx_session_archive_closed ON session_archive(closed_at);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| session_id | VARCHAR(64) PK | 会话 ID |
| student_id | VARCHAR(32) | 学号 |
| closed_at | TIMESTAMP | 关闭时间 |
| close_reason | VARCHAR(16) | timeout/explicit/admin |
| summary | TEXT | LLM 生成的对话摘要, ≤300字 |
| safety_snapshot | JSON | 安全状态快照 `{crisis, b1_count, b2_count, account_status}` |
| last_intent | VARCHAR(32) | 最后一个情境标记 |
| last_topic | VARCHAR(64) | 最后一个话题 |
| unclosed_topic | VARCHAR(256) | 未完成话题/约定 |
| message_count | INT | 本会话总轮数 |

```sql
-- ── 学生档案 (跨会话累计) ──
CREATE TABLE student_profile (
    student_id            VARCHAR(32) PRIMARY KEY,
    rolling_summary       TEXT,                  -- 跨会话累计摘要 (≤300字)
    total_sessions        INT DEFAULT 0,         -- 总会话数
    total_messages        INT DEFAULT 0,         -- 总交互轮数
    first_interaction_at  TIMESTAMP,
    last_interaction_at   TIMESTAMP,
    safety_status         VARCHAR(32) DEFAULT 'normal',
    violation_b1_count    INT DEFAULT 0,         -- 政治敏感违规 (永久累计)
    violation_b2_count    INT DEFAULT 0,         -- 粗鄙语言违规 (7天滑动窗口)
    b2_window_start       TIMESTAMP,             -- B2 滑动窗口起始时间
    b2_last_decay_time    TIMESTAMP,             -- B2 上次降级时间 (24h降1)
    account_status        VARCHAR(16) DEFAULT 'normal',  -- normal / limited / blocked
    updated_at            TIMESTAMP DEFAULT NOW()
);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| student_id | VARCHAR(32) PK | 学号 |
| rolling_summary | TEXT | 跨会话累计摘要, ≤300字, 每次归档时合并 |
| total_sessions | INT | 总会话数 |
| total_messages | INT | 总交互轮数 |
| first_interaction_at | TIMESTAMP | 首次互动时间 |
| last_interaction_at | TIMESTAMP | 末次互动时间 |
| safety_status | VARCHAR(32) | normal/flagged_b1_l2/limited_b1/blocked_b1/warned_b2/limited_b2/blocked_b2 |
| violation_b1_count | INT | B1 累计 (永久, 不降级) |
| violation_b2_count | INT | B2 累计 (7天滑动窗口) |
| b2_window_start | TIMESTAMP | B2 窗口起始, 超7天重置 count |
| b2_last_decay_time | TIMESTAMP | 上次 24h 降1 的时间 |
| account_status | VARCHAR(16) | normal/limited/blocked |

### 2.4 安全表

```sql
-- ── 危机通知 ──
CREATE TABLE crisis_alerts (
    id           BIGINT PRIMARY KEY AUTO_INCREMENT,
    student_id   VARCHAR(32) NOT NULL,
    teacher_id   VARCHAR(32) NOT NULL,
    severity     VARCHAR(16) NOT NULL,           -- urgent / warning
    summary      VARCHAR(500) NOT NULL,           -- 脱敏触发摘要
    status       VARCHAR(16) DEFAULT 'pending',   -- pending / confirmed / escalated / closed
    triggered_at TIMESTAMP DEFAULT NOW(),
    confirmed_at TIMESTAMP,
    confirmed_by VARCHAR(32),
    resolution   VARCHAR(500),                    -- 处理结果说明
    escalated_at TIMESTAMP
);
CREATE INDEX idx_crisis_alerts_teacher ON crisis_alerts(teacher_id, status);
CREATE INDEX idx_crisis_alerts_triggered ON crisis_alerts(triggered_at);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | 自增 |
| student_id | VARCHAR(32) | 学号 |
| teacher_id | VARCHAR(32) | 通知的辅导员 |
| severity | VARCHAR(16) | urgent (危机) / warning (情绪走低/违规) |
| summary | VARCHAR(500) | 脱敏触发摘要 |
| status | VARCHAR(16) | pending→confirmed/escalated/closed |
| triggered_at | TIMESTAMP | 触发时间 |
| confirmed_at | TIMESTAMP | 确认时间 |
| confirmed_by | VARCHAR(32) | 确认人 |
| resolution | VARCHAR(500) | 处理结果 |
| escalated_at | TIMESTAMP | 升级时间 (30分钟未确认) |

**通知流程**: 危机触发 → 写入 pending → 通知辅导员 → 30分钟确认 → 超时 escalated → 通知管理员

```sql
-- ── 安全事件日志 ──
CREATE TABLE security_log (
    id                 BIGINT PRIMARY KEY AUTO_INCREMENT,
    student_id         VARCHAR(32) NOT NULL,
    teacher_id         VARCHAR(32),
    category           VARCHAR(16) NOT NULL,     -- political / vulgar / injection / psych_crisis
    risk_level         INT NOT NULL,             -- 1 / 2 / 3
    trigger_type       VARCHAR(16) NOT NULL,     -- keyword / llm_semantic
    escalation         VARCHAR(16) NOT NULL,     -- ignore / warn / refuse / notify / suspend
    original_message_hash VARCHAR(64),           -- SHA256 (审计用, 不存原文)
    anonymized_summary VARCHAR(256),             -- 脱敏摘要
    new_user_status    VARCHAR(32),              -- 更新后的 safety_status
    created_at         TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_security_log_student ON security_log(student_id);
CREATE INDEX idx_security_log_category ON security_log(category);
CREATE INDEX idx_security_log_created ON security_log(created_at);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | 自增 |
| student_id | VARCHAR(32) | 学号 |
| teacher_id | VARCHAR(32) | 所属教师 |
| category | VARCHAR(16) | political/vulgar/injection/psych_crisis |
| risk_level | INT | 1/2/3 |
| trigger_type | VARCHAR(16) | keyword/llm_semantic |
| escalation | VARCHAR(16) | ignore/warn/refuse/notify/suspend |
| original_message_hash | VARCHAR(64) | SHA256 哈希 (审计, 不存原文) |
| anonymized_summary | VARCHAR(256) | 脱敏摘要 |
| new_user_status | VARCHAR(32) | 更新后的 safety_status |

**权限**: 学生不可见、教师可见所管学生、管理员可见全部

```sql
-- ── 管理员操作审计 ──
CREATE TABLE admin_audit_log (
    id           BIGINT PRIMARY KEY AUTO_INCREMENT,
    admin_id     VARCHAR(32) NOT NULL,
    action_type  VARCHAR(32) NOT NULL,           -- audit_l3 / account_control / knowledge_manage / config_change
    target_type  VARCHAR(32) NOT NULL,           -- student / config / knowledge
    target_id    VARCHAR(64),
    action_detail JSON,                          -- {reason, before, after, ...}
    ip_address   VARCHAR(45),
    created_at   TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_admin_audit_admin ON admin_audit_log(admin_id);
CREATE INDEX idx_admin_audit_created ON admin_audit_log(created_at);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | 自增 |
| admin_id | VARCHAR(32) | 管理员 ID |
| action_type | VARCHAR(32) | audit_l3/account_control/knowledge_manage |
| target_type | VARCHAR(32) | student/config/knowledge |
| target_id | VARCHAR(64) | 操作目标 ID |
| action_detail | JSON | 操作详情 + 原因 |
| ip_address | VARCHAR(45) | 操作 IP |

**必须记录的操作**: 查看 L3-Cold 原文、修改 safety_status、重置 violation_count、编辑知识库、修改系统配置

### 2.5 运行时表

```sql
-- ── LangGraph thread_id 映射 ──
CREATE TABLE thread_session_map (
    session_id   VARCHAR(64) PRIMARY KEY,
    thread_id    VARCHAR(128) NOT NULL,
    student_id   VARCHAR(32) NOT NULL,
    user_role    VARCHAR(16) NOT NULL,           -- student / teacher / admin
    carry_over   VARCHAR(16) NOT NULL,           -- full / partial / minimal
    created_at   TIMESTAMP DEFAULT NOW(),
    closed_at    TIMESTAMP
);
CREATE INDEX idx_tsm_student ON thread_session_map(student_id);
CREATE INDEX idx_tsm_thread ON thread_session_map(thread_id);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| session_id | VARCHAR(64) PK | 业务会话 ID |
| thread_id | VARCHAR(128) | LangGraph checkpointer thread_id |
| student_id | VARCHAR(32) | 学号 |
| user_role | VARCHAR(16) | student/teacher/admin |
| carry_over | VARCHAR(16) | full/partial/minimal |
| closed_at | TIMESTAMP | null = active |

**映射规则**:
- `carry_over = full` → 复用上一个 thread_id → checkpointer 自动加载历史
- `carry_over = partial/minimal` → 新建 thread_id → 手动从 PG 归档加载

---

## 3. Milvus（向量数据库）

### 3.1 两个 Collection

```
Milvus
├── l3_hot_memories     L3-Hot 情景快照 (按学生分区)
└── hlmm_scenes         红楼梦名场面 (全局共享)
```

### 3.2 Collection 1: l3_hot_memories

```
用途: 日常检索 + LLM 注入 + Reflection 提炼
分区: student_id (Partition Key, 物理隔离)
写入: 每轮有意义对话 1 条
检索: ANN (HNSW) + 标量过滤 + Cross-Encoder Reranker
```

| 字段 | 类型 | 说明 |
|---|---|---|
| l3_id | VARCHAR (PK) | l3_20260529_XH_2024001_{ts} |
| student_id | VARCHAR (Partition Key) | 学号, 物理隔离 |
| embedding | FLOAT_VECTOR(768) | bge-large-zh-v1.5 |
| session_id | VARCHAR | 会话 ID |
| timestamp | INT64 | Unix 秒 |
| emotion_primary | VARCHAR | 枚举 (标量索引) |
| emotion_intensity | FLOAT | 0~1 |
| topic | VARCHAR | 枚举 (标量索引) |
| subject | VARCHAR | 可选, 关联学科 |
| importance | FLOAT | 衰减分数, 初始 0.5 |
| write_confidence | FLOAT | 写入置信度 |
| processed_for_l2 | VARCHAR | false/skipped/batched/true (四态) |
| archived | BOOL | 硬遗忘标记 (不物理删除) |
| cold_ref | VARCHAR | PG l3_cold 回源指针 |
| embedding_text | VARCHAR | embedding 原始输入文本 `{topic} {emotion} {trigger} {self_report} {behavioral_signal}` |

```
索引参数:
  type: HNSW
  M: 16
  efConstruction: 200
  ef: 64 (检索时可调)
  metric_type: COSINE

标量索引: emotion_primary, topic, processed_for_l2, archived

检索模式:
  daiyu_chat:
    partition = student_{sid}
    filter = "emotion_primary in [...] and archived == false"
    top_k = 20 → Reranker → 5

  Reflection:
    filter = "processed_for_l2 == false and archived == false"
    limit = 30

容量估算:
  每学生/年: 10轮/天 × 0.6提取率 × 200天 = 1200 条
  100学生 × 1200 = 120,000 条/年
  向量: 120K × 768 × 4B ≈ 350 MB
  标量+索引: ≈ 200 MB
  总计: ≈ 550 MB/年
```

### 3.3 Collection 2: hlmm_scenes

```
用途: L0 角色本体 — 按情绪标签匹配红楼名场面
分区: 无 (全局共享)
写入: 离线批量导入, 管理员手动增量
检索: 标量过滤 (emotion_tag 精确匹配), 不走向量检索
数据量: 100~500 条, 静态
```

| 字段 | 类型 | 说明 |
|---|---|---|
| scene_id | VARCHAR (PK) | hlmm_葬花_001 |
| embedding | FLOAT_VECTOR(768) | bge-large-zh-v1.5 |
| scene_name | VARCHAR | 黛玉葬花 |
| chapter | INT | 第几回 |
| emotion_tag | VARCHAR | 主情绪 (标量索引) |
| emotion_tags | ARRAY[VARCHAR] | 多情绪标签 |
| characters | ARRAY[VARCHAR] | 出场人物 |
| scene_type | VARCHAR | monologue/dialogue/action |
| trigger_tag | VARCHAR | 情绪触发标签 |
| key_quote | VARCHAR | 核心台词 |
| scene_summary | VARCHAR | 场景简述 (≤100字) |
| response_hint | VARCHAR | 风格提示 |

```
索引参数:
  type: HNSW
  M: 16
  efConstruction: 200
  metric_type: COSINE

标量索引: emotion_tag

检索模式:
  filter = 'emotion_tag == "{emotion}"'
  limit = 5, 随机选 2 条返回
  原因: 数据量少 (100-500), ANN 无优势, 标量匹配即可

数据预处理:
  红楼梦原文 → LLM 标注 {scene, emotion, trigger, key_quote, response_hint}
  → 人工审核 (管理员) → embedding → 入库
  同时写入 Neo4j (人物+场景关系)
```

### 3.4 统一向量化模型

```
模型: bge-large-zh-v1.5
维度: 768
模型路径: ./models/bge-large-zh-v1.5
部署: 本地 GPU (~20ms/条) 或 CPU ONNX (~50ms/条)

两个 Collection 共用同一模型:
  - L3 摘要文本和 L0 场景描述都是中文自然语言
  - 统一模型 → 单一 embedding 服务 → 不维护两套管道
```

---

## 4. Neo4j（图数据库）

### 4.1 节点定义

```
┌──────────────────────────────────────────────────────────────────────┐
│  L0 角色本体 (共享, 只读)                                              │
│                                                                      │
│  Character:                                                           │
│  ┌────────────────┬──────────────────────────────────────────────┐  │
│  │  字段           │  说明                                         │  │
│  ├────────────────┼──────────────────────────────────────────────┤  │
│  │  id            │ VARCHAR 唯一 "char_daiyu"                     │  │
│  │  name          │ 人物名 "林黛玉"                                │  │
│  │  aliases       │ LIST 别称 ["颦儿","潇湘妃子","林妹妹"]         │  │
│  │  role          │ "protagonist"|"supporting"|"minor"            │  │
│  │  traits        │ LIST 性格标签 ["敏感","才情","多疑","孤傲"]     │  │
│  │  residence     │ 居所 "潇湘馆"                                  │  │
│  │  importance    │ FLOAT 角色重要度 1.0(主角)~0.1(龙套)           │  │
│  └────────────────┴──────────────────────────────────────────────┘  │
│  约束: CREATE CONSTRAINT FOR (c:Character) REQUIRE c.id IS UNIQUE    │
│                                                                      │
│  Scene:                                                              │
│  ┌────────────────┬──────────────────────────────────────────────┐  │
│  │  字段           │  说明                                         │  │
│  ├────────────────┼──────────────────────────────────────────────┤  │
│  │  scene_id      │ VARCHAR 唯一 "scene_bury_flowers"             │  │
│  │  scene_name    │ "黛玉葬花"                                    │  │
│  │  chapter       │ INT 第23回                                    │  │
│  │  emotion_tag   │ VARCHAR 主情绪 "sadness"                      │  │
│  │  emotion_tags  │ LIST 多标签 ["sadness","loneliness","loss"]   │  │
│  │  characters    │ LIST 出场人物                                  │  │
│  │  scene_type    │ "monologue"|"dialogue"|"action"               │  │
│  │  trigger_tag   │ VARCHAR 触发标签 "loss"|"lonely"|"injustice"  │  │
│  │  key_quote     │ VARCHAR 核心台词                               │  │
│  │  summary       │ VARCHAR 简述 (≤100字)                         │  │
│  │  response_hint │ VARCHAR 风格提示                               │  │
│  └────────────────┴──────────────────────────────────────────────┘  │
│  约束: CREATE CONSTRAINT FOR (s:Scene) REQUIRE s.scene_id IS UNIQUE │
│  索引: CREATE INDEX FOR (s:Scene) ON (s.emotion_tag)                │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  L2 语义认知 (按学生隔离)                                              │
│                                                                      │
│  Student (多标签: Student:Class{班级名}):                              │
│  ┌────────────────┬──────────────────────────────────────────────┐  │
│  │  字段           │  说明                                         │  │
│  ├────────────────┼──────────────────────────────────────────────┤  │
│  │  student_id    │ VARCHAR 唯一 "XH_2024001"                     │  │
│  │  name          │ "小红"                                        │  │
│  │  class_name    │ "初二3班"                                     │  │
│  │  teacher_id    │ VARCHAR 所属辅导员                              │  │
│  │  created_at    │ DATETIME                                      │  │
│  └────────────────┴──────────────────────────────────────────────┘  │
│  约束: CREATE CONSTRAINT FOR (s:Student) REQUIRE s.student_id IS UNIQUE│
│                                                                      │
│  Subject (共享节点):                                                  │
│    字段: name (VARCHAR 唯一, "数学"/"语文"/"英语"/...)                │
│    约束: CREATE CONSTRAINT FOR (sub:Subject) REQUIRE sub.name IS UNIQUE│
│                                                                      │
│  Trait (预建 10~15 + 允许动态新增):                                    │
│    字段: name (VARCHAR 唯一), category ("emotion"|"social"|"behavior")│
│    约束: CREATE CONSTRAINT FOR (t:Trait) REQUIRE t.name IS UNIQUE    │
│    预建: 考前焦虑, 社交回避, 自我否定, 独处偏好, 同伴冲突,             │
│          课堂参与度低, 家庭压力, 未来焦虑, 自信心不足, 学习倦怠        │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 关系定义

```
L0 关系 (只读):
┌──────────────────────┬──────────────────────────────────────────┐
│  [:RELATED_TO]       │ type: 关系类型                            │
│  (Character→Character)│   倾慕/依赖/忌惮/信赖/敬畏/母女/父子/     │
│                      │   姐妹/主仆/知己                          │
│                      │ strength: FLOAT [0,1] 关系强度            │
├──────────────────────┼──────────────────────────────────────────┤
│  [:APPEARS_IN]       │ role: protagonist/supporting/mentioned   │
│  (Character→Scene)   │                                          │
└──────────────────────┴──────────────────────────────────────────┘

L2 认知关系 (含完整置信度动力学字段):
┌──────────────────────┬──────────────────────────────────────────┐
│  [:偏科]              │ level: STRING 认知内容                    │
│  (Student→Subject)   │   "代数薄弱,几何中等偏上"                 │
│                      │ trend: STRING 波动/下降/上升/平稳          │
├──────────────────────┼──────────────────────────────────────────┤
│  [:情绪倾向]          │ intensity: FLOAT 0~1 情绪强度             │
│  (Student→Trait)     │                                          │
├──────────────────────┼──────────────────────────────────────────┤
│  [:态度偏好]          │ valence: STRING positive/negative/neutral │
│  (Student→Subject)   │   "positive" 对语文态度正面               │
├──────────────────────┼──────────────────────────────────────────┤
│  [:社交模式]          │ pattern: STRING 社交模式描述               │
│  (Student→Trait)     │   "独处偏好, 小圈子交流"                   │
└──────────────────────┴──────────────────────────────────────────┘

跨层关系:
┌──────────────────────┬──────────────────────────────────────────┐
│  [:关心]              │ strength: FLOAT [0,1] 当前关系强度       │
│  (Character→Student) │   每日按 e^(-λ×days) 衰减                 │
│                      │ first_interaction: DATETIME 首次互动      │
│                      │ last_interaction: DATETIME 末次互动       │
│                      │ interaction_count: INT 总互动次数          │
└──────────────────────┴──────────────────────────────────────────┘

每条 L2 关系边共同携带的置信度动力学字段:
┌──────────────────────┬──────────────────────────────────────────┐
│  confidence          │ FLOAT  当前置信度 C                       │
│  C_peak              │ FLOAT  历史最高置信度                     │
│  C_trough            │ FLOAT  历史最低置信度                     │
│  streak_count        │ INT    当前连续同向证据数                  │
│  streak_direction    │ STRING "support"|"oppose"|null            │
│  last_oppose_time    │ DATETIME 最后一次反对时间                 │
│  source              │ STRING 来源 reflection/inference          │
│  verified_count      │ INT    被验证次数                         │
│  created_at          │ DATETIME                                 │
│  updated_at          │ DATETIME                                 │
│                                                                  │
│  冲突追踪字段 (仅存在冲突时非空):                                  │
│  conflict_status     │ STRING "active"|"pending_verification"    │
│                      │       |"archived"|null                    │
│  conflict_with       │ STRING 对方 target_name (维度内唯一标识)   │
│                      │       null=无冲突                         │
│  pending_since       │ DATETIME 进入 pending 的时间,              │
│                      │         用于 30 天超时归档判断             │
└──────────────────────┴──────────────────────────────────────────┘
```

### 4.3 核心查询

```cypher
-- daiyu_chat: 学生 L2 认知 (1-hop)
MATCH (s:Student {student_id: $sid})-[r]-(t)
WHERE type(r) IN ['偏科','情绪倾向','态度偏好','社交模式']
RETURN type(r), t.name, r.confidence, r.C_peak, r.streak_direction
ORDER BY r.confidence DESC;

-- daiyu_chat: 黛玉人物子图
MATCH (daiyu:Character {id: "char_daiyu"})-[r:RELATED_TO]-(o)
RETURN type(r), r.strength, o.name, o.traits;

-- daiyu_chat: 情绪匹配名场面 (随机轮换)
MATCH (s:Scene) WHERE s.emotion_tag = $emotion
RETURN s.scene_name, s.key_quote, s.response_hint
ORDER BY rand() LIMIT 2;

-- 教师: 单个学生画像
MATCH (s:Student {student_id: $sid})
OPTIONAL MATCH (s)-[r1:偏科]->(subj)
OPTIONAL MATCH (s)-[r2:情绪倾向]->(tr)
OPTIONAL MATCH (s)-[r3:态度偏好]->(subj2)
OPTIONAL MATCH (:Character {id:"char_daiyu"})-[rc:关心]->(s)
RETURN s, r1, subj, r2, tr, r3, subj2, rc;

-- 教师: 班级聚合 (不返回单生 ID)
MATCH (s:Student:Class3)-[r:情绪倾向]->(t:Trait)
WHERE t.category = "emotion"
RETURN t.name, count(s) AS cnt ORDER BY cnt DESC;

-- 重连: 关心边强度
MATCH (:Character {id:"char_daiyu"})-[r:关心]->(:Student {student_id:$sid})
RETURN r.strength, r.last_interaction, r.interaction_count;

-- Reflection: 更新认知边
MATCH (s:Student {student_id:$sid})-[r:偏科]->(t:Subject {name:$target})
SET r.confidence = r.confidence + $delta,
    r.C_peak = CASE WHEN r.confidence > r.C_peak THEN r.confidence ELSE r.C_peak END,
    r.streak_count = $new_streak,
    r.updated_at = datetime();

-- 定时任务: 批量衰减关心边
MATCH (:Character)-[r:关心]->(:Student)
WHERE r.last_interaction IS NOT NULL
SET r.strength = r.strength * exp(-$lambda *
    duration.inDays(r.last_interaction, datetime()).days);

-- 定时任务: 批量回升置信度
MATCH (s:Student)-[r]-(t)
WHERE type(r) IN ['偏科','情绪倾向','态度偏好','社交模式']
  AND r.streak_count = 0 AND r.last_oppose_time IS NOT NULL
  AND r.C_peak > r.C_trough
WITH r, r.C_peak - r.C_trough AS damage
SET r.confidence = r.C_trough + damage *
    (1 - exp(-$lambda * duration.inDays(r.last_oppose_time, datetime()).days)) * $cap;
```

---

## 5. 数据生命周期

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  PostgreSQL:                                                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  l3_cold:                                                     │   │
│  │    Day 0-30:  热归档 (active), 可回源                          │   │
│  │    Day 31-90: 温归档 (warm_archive), 保留但查询需指定表         │   │
│  │    Day 91+:   删除 (危机+importance≥0.7 除外)                   │   │
│  │                                                               │   │
│  │  session_archive: 永久保留 (数据量小)                           │   │
│  │  student_profile: 永久保留                                     │   │
│  │  security_log:    保留 2 年                                    │   │
│  │  admin_audit_log: 保留 2 年                                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Milvus:                                                             │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  l3_hot:                                                      │   │
│  │    软遗忘: importance 按 e^(-λ×days) 衰减                       │   │
│  │    硬遗忘: archived=true (标记, 不物理删除)                      │   │
│  │    物理删除: 学生毕业/退学, 管理员手动                            │   │
│  │                                                               │   │
│  │  hlmm_scenes: 静态, 管理员维护                                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Neo4j:                                                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  L0 (Character/Scene): 永久, 只读                              │   │
│  │  L2 (Student + 关系边): 永久, 认知边可归档为 archived 状态       │   │
│  │  [:关心]: strength 每日定时衰减, 学生删除时删边                  │   │
│  │  矛盾悬挂: >30天未验证 → 双方归档                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```
