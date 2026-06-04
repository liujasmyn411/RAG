# ChatGPT 问答记录 — 项目记忆能力梳理

> 背景：ChatGPT 询问本项目是否具备四项记忆能力，以下为基于代码实际分析的回答。

---

## Q1: 项目是否具备长期记忆能力？（记住用户过去对话）

**答：已实现。** 项目有四层长期记忆架构：

| 层级 | 存储 | 内容 | 生命周期 |
|------|------|------|----------|
| L0 人设本体 | Neo4j | 林黛玉人格、人物关系、名场面 | 永久只读 |
| L1 业务事实 | MySQL | 学生成绩、考勤等结构化数据 | 随源数据 |
| L2 语义认知 | Neo4j | 偏科、情绪倾向、态度偏好、社交模式 | 置信度动态调整 |
| L3 情景快照 | Milvus + MySQL | 每轮对话的结构化摘要 + 原始对话 | 热30天→温90天→删除（危机永久） |

关键文件：`app/services/memory_service.py`、`app/repositories/neo4j_repo.py`、`app/repositories/milvus_repo.py`

---

## Q2: 项目是否具备经验总结能力？（多案例 → 提炼规律）

**答：已实现。** Reflection Service 负责从 L3 情景快照蒸馏出 L2 语义认知：

- 聚类同 topic 的 L3 快照（每组 ≥2 条）
- LLM 提炼结构化认知（学科能力/情绪模式/社交模式/态度偏好）
- 写入 Neo4j 作为 (Student)-[关系边]->(Subject/Trait) 的图结构
- 每条认知附带置信度三因子（confidence / C_peak / C_trough）、streak 计数器、验证次数

关键文件：`app/services/reflection_service.py`

---

## Q3: 项目是否具备冲突检测能力？（以前说A，现在说B → 发现矛盾）

**答：已实现。** Reflection Service 内置 6 种冲突分类：

| 类型 | 含义 | 示例 |
|------|------|------|
| type_1_oppose | 直接对立 | "讨厌数学" vs "喜欢数学" |
| type_2_supersede | 时间覆盖 | "数学不及格" vs "数学85分" |
| type_3_refine | 范围细化 | "数学弱" vs "代数弱但几何好" |
| type_4_source_conflict | 来源冲突 | 系统成绩 vs 学生自述 |
| type_5_affective | 情绪波动 | 短期内情绪极性交替 |
| type_6_overlap | 语义重叠 | "数学不太好" vs "数学有点吃力" |

冲突处理采用贝叶斯对抗更新公式：`Δ = quality × (-1) × C_old × (1 - resistance) × streak_mult`

关键文件：`app/services/reflection_service.py` (`CONFLICT_CLASSIFY_PROMPT`)

---

## Q4: 项目是否具备记忆评分能力？（重要程度、可信度）

**答：已实现。** 多维度评分体系：

- **confidence（置信度）**：0~1，三级过滤（高≥0.85 / 中≥0.70 / 低≥0.50 / <0.50 丢弃），支持贝叶斯动态更新
- **C_peak / C_trough**：置信度历史峰值和谷值，用于计算 damage（伤害深度）
- **importance（重要度）**：0~1，危机事件=1.0 永久保留，普通=0.5 随时间指数衰减
- **write_confidence（写入质量）**：Level 0=0.50 / Level 1=0.40 / Level 2=0.30 / Level 3=丢弃
- **streak_count / streak_direction**：连续验证或反驳次数
- **verified_count**：被证据验证的总次数
- **resistance（抗变性）**：旧认知对新证据的抵抗力，随旧置信度增长

关键文件：`app/domain/entities/memory.py`、`app/services/reflection_service.py`

---

## Q5: L2 语义认知存储的真实内容是什么？

**答：** L2 不是简单的 key-value，而是 Neo4j 图数据库中的关系边：

```
(Student) -[偏科 {confidence:0.70, level:"代数薄弱，几何中等偏上", trend:"波动"}]-> (Subject {name:"数学"})
(Student) -[情绪倾向 {confidence:0.82, intensity:0.78}]-> (Trait {name:"考前焦虑"})
(Student) -[态度偏好 {confidence:0.70, valence:"positive"}]-> (Subject {name:"英语"})
(Student) -[社交模式 {confidence:0.65, pattern:"小圈子社交，回避集体活动"}]-> (Trait {name:"同伴关系"})
```

注入 LLM 上下文时的格式：
```
学生认知:
· 偏科→数学 (置信度:0.70)
· 情绪倾向→考前焦虑 (置信度:0.82)
· 态度偏好→英语 (置信度:0.70)
· 社交模式→同伴关系 (置信度:0.65)
```

---

## Q6: 从用户输入到 L2 形成的完整流程是什么？

**答：** 7 节点 LangGraph StateGraph 流水线：

```
用户输入 → Safety Filter → Intent Router → Memory Retrieval
→ Context Builder → Response Generator → Fact Verifier
→ Post Processor (写入 L3-Hot/Cold, Episode 边界检测)
→ [异步] Reflection Service (定时 Job 触发 L3→L2 蒸馏)
```

技术栈：FastAPI + LangGraph + Qwen (DashScope) + MySQL + Neo4j + Milvus + bge-large-zh-v1.5 (768维) + bge-reranker-v2-m3

---

## 关键结论

**四个能力全部已实现**，其中冲突检测和记忆评分的实现较为细致（6 种冲突分类、贝叶斯置信度更新、多因子评分）。L2 存储的是带完整上下文的结构化领域认知记录，具备包装为"专家经验库"的基础。
