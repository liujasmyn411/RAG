# 情景记忆 (Episodic Memory) 演进计划

## 问题诊断

当前 L3 层名为"情景快照"但实际是 **语义特征标签集合**（emotion + topic + subject + trigger），每个 L3 孤立存储，缺乏：
- 叙事序列 (narrative sequence)
- 情节边界 (episode boundary)
- 因果链 (causal chain)
- 情境检索 (situation-based retrieval)

## 三期演进路线

---

## 第一期：Episode 容器化 (Episode Containerization)

**目标**: 把分散的 L3 快照组织成有边界的 Episode，建立叙事结构。

### 1.1 新增 Episode 实体和表

```python
@dataclass
class Episode:
    """情景记忆的基本单位 — 一个完整的话题/事件弧"""
    episode_id: str
    student_id: str
    session_id: str

    # 边界
    started_at: datetime
    ended_at: Optional[datetime]
    boundary_trigger: str  # "topic_shift" | "emotion_peak" | "time_gap" | "user_signal"

    # 叙事
    title: str              # LLM 生成的简短标题, 如 "数学考试焦虑"
    abstract: str           # 100-200字摘要
    narrative_chain: list[str]  # ["l3_001","l3_002","l3_003"] — 有序 L3 ID 列表

    # 情感弧线
    emotion_arc: list[dict]  # [{"l3_id":"l3_001","emotion":"anxious","intensity":0.7}, ...]

    # 结果/闭合
    resolution: Optional[str]  # 问题是否解决, 对话如何结束
    importance: float

    # 元数据
    created_at: datetime
    is_closed: bool
```

### 1.2 Episode 边界检测器 (Boundary Detector)

在 `post_processor_node` 之后新增一个轻量检测步骤：

| 信号 | 检测方式 | 说明 |
|------|---------|------|
| Topic Shift | 连续两轮 topic 不同 | 话题切换 → 新 Episode |
| Emotion Peak | intensity > 0.8 且前后轮低 | 情绪爆发点 → Episode 高潮/结束 |
| Time Gap | 用户超过 30 分钟没回复 | 时间断点 → Episode 自然结束 |
| User Signal | "下次聊"、"不说这个了" | 用户明确结束 |
| Session Boundary | 会话结束/开始 | 强制 Episode 边界 |

### 1.3 存储方案

- **PG**: `episodes` 表（结构化元数据 + narrative_chain JSON）
- **Milvus**: 用 episode 的 `abstract` 做向量化（而非单个 L3），检索粒度从"单条快照"提升到"完整事件"

### 1.4 改动范围

| 文件 | 改动 |
|------|------|
| `app/domain/entities/memory.py` | 新增 `Episode` dataclass |
| `app/domain/enums.py` | 新增 `BoundaryTrigger` enum |
| `app/repositories/pg_repo.py` | 新增 `insert_episode`, `close_episode`, `get_active_episode` |
| `app/repositories/milvus_repo.py` | 新增 `search_episodes` (用 abstract 向量检索) |
| `app/agents/nodes/post_processor.py` | 新增 `_episode_boundary_check()` |
| `app/init_db.py` | 新增 `episodes` 表和 Milvus `episode_embeddings` collection |

**预计工作量**: 3-5 天

---

## 第二期：情景检索与回放 (Episode Retrieval & Replay)

**目标**: 让检索从"匹配标签"升级为"匹配情境"。

### 2.1 情境相似度检索

当前检索:
```
query → embedding → Milvus ANN (匹配 emotion + topic + trigger)
```

改进后:
```
query → 提取情境特征 (Contextual Features)
      → Milvus ANN (匹配 episode abstract)
      → Reranker (用完整 episode narrative 重排)
      → 返回 "类似情境" 而非 "类似标签"
```

情境特征提取 prompt:
```
给定当前对话，提取情境特征:
- 触发事件是什么？（考试、社交冲突、家庭问题...）
- 学生的情绪演变轨迹？（平静→焦虑→崩溃 / 低落到逐渐开朗...）
- 对话处于什么阶段？（问题暴露期、情绪宣泄期、解决方案期...）
```

### 2.2 Episode 回放

在 MemoryService 中新增 `replay_episode(episode_id)` 方法：
- 从 PG 拉取 `narrative_chain`
- 按 L3-Cold 回源完整对话
- 生成带时间轴的叙述摘要，注入 context_builder

### 2.3 情境类比

利用 Episode 的 narrative 做跨 Episode 类比：
```
"这个学生现在的状态，和上次遇到类似问题时的状态有什么不同？"
→ 检索相似 Episode → 对比情感弧线 → 发现变化趋势
```

这是 L2 语义认知无法做到的 —— L2 只知道"数学偏弱"，但不知道"上次是因为考试不及格哭了，这次是因为被老师当众批评"。

### 2.4 改动范围

| 文件 | 改动 |
|------|------|
| `app/services/memory_service.py` | `_retrieve_daiyu_chat` 增加 Episode 检索路径 |
| `app/services/memory_service.py` | 新增 `replay_episode()`, `analogize_episodes()` |
| `app/agents/nodes/context_builder.py` | 新增 Episode 上下文格式化 |
| `app/agents/prompts/context_builder.py` | 新增 Episode replay 的 System Prompt 模板 |

**预计工作量**: 5-7 天

---

## 第三期：叙事推理与预测 (Narrative Reasoning)

**目标**: 让 Agent 具备跨 Episode 的因果推理和趋势预测能力。

### 3.1 Episode Graph (Neo4j)

在 Neo4j 中建立 Episode 之间的关系：

```
(Episode_1)-[:PRECEDES]->(Episode_2)-[:PRECEDES]->(Episode_3)
(Episode_1)-[:CAUSED]->(Episode_3)     # "数学成绩下降" 导致了 "厌学情绪"
(Episode_2)-[:SIMILAR_TO]->(Episode_5) # 类似情境
(Episode_1)-[:ESCALATED_FROM]->(Episode_1) # 自我循环加剧
```

### 3.2 叙事推理 Prompt

新增 Reflection 维度 —— 不仅提炼认知特征，还提炼 **叙事模式**：

```
分析该学生最近 N 个 Episode:
1. 是否存在重复的行为模式？（如"考试前必焦虑"）
2. 情绪是否有恶化/改善趋势？
3. 哪些 Episode 之间存在因果关系？
4. 预测：如果当前趋势持续，接下来可能发生什么？
```

产出 → L2.5 "叙事认知" (Narrative Cognition)，存储在 Neo4j 中作为 Episode-Episode 关系边。

### 3.3 Memory Chain 预测

基于 Episode 序列做简单预测：
- "根据过去的模式，这个学生下周考试前大概率会再次焦虑"
- → 主动触发关怀（而非被动等待学生表达）

### 3.4 改动范围

| 文件 | 改动 |
|------|------|
| `app/services/reflection_service.py` | 新增 `_extract_narrative_patterns()` |
| `app/repositories/neo4j_repo.py` | 新增 Episode Node CRUD |
| `app/domain/enums.py` | 新增 `EpisodeRelationType` |
| `app/services/memory_service.py` | 新增 `predict_next_episode()` |
| `app/agents/nodes/` | 新增 `narrative_reasoning_node`（可选，非实时路径） |

**预计工作量**: 7-10 天

---

## 与现有架构的关系

```
当前架构:
  L0 (本体) + L1 (事实) + L2 (语义认知) + L3 (语义标签快照)

第一期后:
  L0 + L1 + L2 + L3 (Episode容器, 含多个L3快照的叙事链)

第二期后:
  L0 + L1 + L2 + L3 (Episode检索 + 回放 + 类比)

第三期后:
  L0 + L1 + L2 + L2.5 (叙事认知) + L3 (Episode Graph + 预测)
```

**关键不变项**:
- L0 (角色本体) 不变
- L1 (业务事实) 不变
- L2 (语义认知提取) 保留但输入从孤立的 L3 变为完整的 Episode
- Reflection 引擎增加 Episode 级别的提炼能力
- L3-Cold 仍然是原始对话的 source of truth

---

## 优先级建议

| 优先级 | 期数 | 价值 | 理由 |
|--------|------|------|------|
| **P0** | 第一期 | 基础架构 | 没有 Episode 容器，后续都无法进行 |
| **P1** | 第二期 | 用户体验提升 | 检索质量从"标签匹配"跃升到"情境匹配" |
| **P2** | 第三期 | 差异化能力 | 预测和主动关怀是产品的核心壁垒 |

## 即刻可做的小改进 (Quick Wins)

这些改动小但方向正确，可以立刻开始：

1. **L3Snapshot 增加 `prev_l3_id` / `episode_id` 字段** — 建立叙事链的基础
2. **post_processor 在写入 L3-Hot 时记录当前活跃 Episode ID** — 先不建 Episode 表，只在 L3 上加外键
3. **embedding_text() 加入上一轮 L3 的 trigger/subject** — 让向量包含上下文信息
4. **检索返回时附带 L3 的前后相邻记录** — 让 context_builder 能看到叙事上下文
