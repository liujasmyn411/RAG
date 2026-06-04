# 简历项目描述 — EIA Expert Agent

---

法规RAG 


## 一、STAR 格式项目描述

### 简短版（简历上用，3-4行）

> **EIA Expert Agent — 基于认知记忆框架的环评专家系统**
>
> 设计并实现了领域无关的认知记忆框架（Cognitive Memory Framework），包含 L3 情景案例记忆、L2 语义认知图谱和 L0 实体知识图谱三层架构。通过 LLM 驱动的 Reflection 蒸馏引擎实现案例到专家认知的自动转化，配合六类语义冲突检测和基于 C_peak/C_trough/streak 三因子的贝叶斯置信度演化机制，实现专家经验的长期沉淀与动态更新。
>
> *LangGraph · Milvus · Neo4j · Reflection · Bayesian Confidence Evolution · LLM Conflict Detection*

### STAR 完整版（面试用）

**S - Situation**

环境影响评价（EIA）领域面临两个核心挑战：(1) 资深工程师的经验以隐性知识形式存在，难以系统化沉淀和传承；(2) 项目案例分散在文档中，无法自动提炼为可复用的专家认知。传统 RAG 方案只能检索原文，缺乏从案例到认知的蒸馏能力和认知冲突时的自我纠错机制。

**T - Task**

设计一套通用认知记忆框架，使 Agent 能够：(1) 从项目案例中自动提炼专家级认知；(2) 在新旧认知冲突时自动检测并更新；(3) 通过置信度动态演化反映认知的可靠性变化。以 EIA 场景为应用实例进行验证。

**A - Action**

- **三层记忆架构**: 设计 L3 情景记忆（Milvus向量检索 + 叙事链）、L2 语义认知（Neo4j图谱，4维度认知建模）、L0 实体图谱（项目/法规/污染物关联），实现跨层混合检索
- **Reflection 认知蒸馏**: 基于 LLM 的语义提炼引擎，对案例按 topic 聚类后蒸馏为结构化认知（relation_type + target + content），支持维度可配置的 Schema Registry
- **六类语义冲突检测**: 设计 Oppose/Supersede/Refine/Source_Conflict/Affective/Overlap 六分类体系，通过 LLM 语义比对自动判定新旧认知关系类型
- **三因子贝叶斯演化**: 设计 C_peak（历史最高）/ C_trough（历史最低）/ streak（连续方向）三因子驱动置信度更新：
  ```
  Δ = quality × direction × C_old × (1 - resistance) × streak_mult
  damage = C_peak - C_trough
  resistance = min((C_old - 0.35) / 0.65, 0.85)
  ```
- **Schema-flexible 设计**: 认知维度通过 COGNITION_DIMENSIONS 注册表管理，从学生心理场景（6维度：ability/emotion/behavior/attitude/social/risk）重构为 EIA 场景（4维度：risk/compliance/impact/experience），核心引擎零改动
- **LangGraph 编排**: 基于 LangGraph 实现多节点有状态 Agent，串联分类→检索→上下文组装→生成→后处理全链路

**R - Result**

- 通过 12 个手工设计 EIA 案例 + 14 条结构化法规进行验证
- Reflection 蒸馏产出 14 条专家认知，覆盖 4/4 认知维度（100%），压缩率 0.86:1
- 6 组人工设计冲突（3 overlap + 2 oppose + 1 supersede）覆盖 3/6 冲突类型
- 认知演化链路完整：案例→蒸馏→冲突检测→贝叶斯更新→置信度动态调整
- 框架本身领域无关，Schema 切换即可适配新领域

---

## 二、技术关键词（简历用）

| 类别 | 关键词 |
|---|---|
| 记忆框架 | L3 Episodic Memory, L2 Cognitive Memory, L0 Entity Graph, Cognitive Distillation |
| 冲突检测 | 6-Type Semantic Conflict Detection, LLM-based Classification |
| 置信度演化 | Bayesian Confidence Evolution, C_peak/C_trough, Streak Mechanism |
| 技术栈 | LangGraph, Milvus (HNSW), Neo4j (Graph DB), DashScope (Qwen) |
| 向量检索 | BGE-Large-v1.5 (768d), BGE-Reranker-v2-m3, Hybrid Retrieval |
| 其他 | Schema Registry, Narrative Chain, Entity-Relation Modeling |

---

## 三、面试追问清单（30题）

### 架构与设计（10题）

1. **为什么选择三层记忆架构（L0/L2/L3）而不是单一向量库？**
   > L3 存原始案例（what happened），L2 存提炼认知（what we learned），L0 存领域实体（what exists）。三层各司其职，检索时可跨层互补——L3 提供案例细节，L2 提供专家判断，L0 提供法规依据。

2. **Reflection 蒸馏和普通 RAG 摘要有什么区别？**
   > RAG 摘要是一对一映射（文档→摘要），Reflection 是多对一蒸馏（多个案例→一条认知），且附带置信度和冲突检测。关键差异在于"知识压缩"和"矛盾处理"。

3. **为什么用 Neo4j 而非关系数据库存 L2 认知？**
   > 认知之间存在天然图结构——同一项目的多条认知、跨项目的同类风险、法规与认知的映射关系。图遍历比 JOIN 更自然。且 Neo4j 的边即维度 key，Schema 扩展零成本。

4. **Schema Registry 的设计动机是什么？**
   > 让框架本身领域无关。认知维度不是硬编码的，而是注册表驱动。从学生心理切到 EIA，只改 COGNITION_DIMENSIONS 字典，Reflection 引擎和冲突检测逻辑原封不动。

5. **六类冲突是怎么设计的？为什么是六类？**
   > 不是拍脑袋的。对认知更新场景做了穷举：矛盾(Oppose)、过时(Supersede)、细化(Refine)、来源不一致(Source)、时间波动(Affective)、重复(Overlap)。这六类覆盖了认知更新的全部语义关系。

6. **为什么用三因子贝叶斯而不是简单的加权平均？**
   > 加权平均无法表达"认知的抗变性"——高置信度认知不应因一次反例就崩溃。resistance 因子让置信度越高越难被推翻（类似认知科学中的"确认偏误"）；streak 因子让连续同方向证据加速收敛。

7. **Milvus 的叙事链（prev_l3_id/next_l3_id）解决了什么问题？**
   > 向量检索只能找回"语义相似"的记录，但无法找回"时间相邻"的记录。叙事链让检索结果能附加上下文——"这个案例之前发生了什么，之后又发生了什么"。

8. **LangGraph 在这个项目里起了什么作用？**
   > 编排多个异步节点：意图分类→安全过滤→记忆检索（多路并发）→上下文组装→LLM生成→后处理（L3入库+Reflection触发检查）。LangGraph 的 State 传递让各节点解耦。

9. **如果扩展到 10000 个案例，哪些地方会成为瓶颈？**
   > (1) Reflection 的 LLM 调用是最大瓶颈——需要按 topic 聚类后分批蒸馏，可通过增加 trigger_count 阈值减少触发频率；(2) Milvus 的 pull_unprocessed 需要分区索引确保扫描范围可控；(3) Neo4j 的 get_student_traits 需要按维度创建索引。

10. **你认为这个框架最大的技术亮点是什么？**
    > 不是某单一技术，而是"认知蒸馏→冲突检测→贝叶斯演化"这个闭环。大多数 Agent 项目只有检索+生成，缺乏认知形成和演化机制。这个闭环让系统具备了"从经验中学习"的能力。

### 工程能力（7题）

11. **为什么用异步（async/await）而不是同步？**
    > Reflection 蒸馏链路涉及多个 IO 密集型操作：Milvus 向量检索、Neo4j 图查询、LLM API 调用。这三个操作互不依赖，用 `asyncio.gather` 并发执行可将单次 Reflection 耗时从 "Milvus耗时 + Neo4j耗时 + LLM耗时" 降到 "max(三者)"。实测中 LLM 调用占约 80% 耗时，异步让另外两个操作与 LLM 并行，整体延迟降约 15%。此外 LangGraph 本身就是异步框架，State 在节点间传递天然适配 async/await 模型。

12. **你是怎么管理 LLM 调用的错误和重试的？**
    > 分层处理。最外层是 `try/except` 兜底——LLM 超时或返回非法 JSON 时返回默认值（如 `classifier.classify()` 失败时返回 `CaseRiskLevel.MEDIUM + GENERAL_CONSULTATION`），确保主链路不因 LLM 故障而中断。中间层是 quality_level 分级——`classify_with_fallback` 输出 Level 0~3，Level 3（完全失败）的提取直接不入库，避免脏数据污染认知图谱。目前没有加自动重试，因为 LLM 的失败通常是 token 超限或 API 限流，盲目重试会加剧问题。如果做，会加指数退避 + 熔断器。

13. **Schema 变更时（如我们刚做的学生→EIA迁移），怎么保证数据一致性？**
    > 严格分层迁移。第一层改枚举和 Schema 注册表（`COGNITION_DIMENSIONS`），纯代码变更，零数据影响。第二层改实体字段（`L3Snapshot`），对应 Milvus collection 的 field schema——需要 `drop_collection` + `recreate` + 重新导入数据。第三层改 Neo4j 节点 label（`Student→Entity`），通过 Cypher 的 `MATCH (n:Student) SET n:Entity REMOVE n:Student` 无损迁移。核心原则：改 Schema 在改数据之前，改数据有回滚脚本。项目中的 `migrate_episodic.py` 就是为 Milvus 字段增量迁移设计的，避免全量重建——用 `col.add_field()` 增量加新字段，用 `col.release()` / `col.load()` 热重载。

14. **Milvus 和 Neo4j 的数据一致性问题怎么处理？**
    > 采用最终一致性模型，不是强一致。写入流程：L3 先写 Milvus（向量检索需要实时性）→ 标记 `processed_for_l2=false` → Reflection 定时触发，从 Milvus 拉未处理记录 → LLM 蒸馏 → 写 Neo4j L2 边 → 回写 Milvus `processed_for_l2=true`。如果 Reflection 中途崩溃，`processed_for_l2` 保持 false，下次触发重新处理，天然幂等。不需要分布式事务——因为 Reflection 是异步批处理而非在线写入，最终一致性足够。L3 写入和 L2 认知更新之间有数分钟到数小时的延迟窗口是设计上可接受的。

15. **你的 eval 脚本是怎么验证 Reflection 输出质量的？**
    > 分两层验证。结构层：检查产出认知的 `relation_type` 是否在注册表维度内、`confidence` 是否在 [0,1] 区间、`evidence_ids` 是否非空且指向真实 L3 ID。语义层：对比预期认知（基于案例设计推算）与实际产出，计算维度覆盖率和冲突识别准确率。我特意在 12 个案例中埋了 6 组冲突（3 overlap + 2 oppose + 1 supersede），eval 脚本会验证每组冲突是否被正确触发和分类。脚本支持两种模式：`--dry-run` 基于案例设计推算预期值（零外部依赖），`--live` 跑真实 Reflection 后对比实际与预期。

16. **项目里最复杂的 bug 是什么？怎么排查的？**
    > 最早版本的贝叶斯更新公式有个隐蔽问题：当 `streak_direction` 翻转时（从 support 切到 oppose），`streak_count` 应该重置为 1 而非累加。但 `_update_bayesian_oppose` 里的判断逻辑是 `prev_direction == "oppose"` 才累加，否则重置——第一次 oppose 时 `prev_direction` 必然是 `"support"`（因为之前是 overlap 增强），导致 streak_count 永远是 1，`streak_mult` 永远是 1.0，连续反证永远无法加速推翻旧认知。排查方式是对 `streak_count` 打 log，发现从 support×3 翻转后一直是 oppose×1。修复是在方向翻转分支显式设 `streak_count = 1`，方向不变才累加。这个 bug 让我深刻理解：贝叶斯更新必须对"方向翻转"和"方向持续"做显式的分支处理。

17. **如果要给这个项目加单元测试，你会怎么设计？**
    > 三层测试。单元层：对 `_cluster_by_topic` 做纯函数参数化测试（输入 list[dict]，验证聚类分组逻辑）；对贝叶斯公式做参数化边界测试（给定 C_old/quality/streak_count/direction，断言 C_new 在 [0.01, 0.99] 区间且方向翻转时 damage > 0）。集成层：Mock LLM 返回固定 JSON，测试 Reflection 主流程（pull_unprocessed → extract → classify_conflict → create/update edge）的完整链路。端到端层：准备 mini 案例集（3 个案例，1 组 overlap），跑完整 Reflection，验证 Neo4j 里多了正确的边且置信度符合预期。最关键的是冲突检测的单元测试——每种冲突类型准备一对 old/new 认知，验证 `_classify_conflict` 返回正确的 `ConflictType`。同时 Mock LLM 返回各种 JSON（正确/错误/超时），验证兜底逻辑不崩溃。

### 业务理解（6题）

18. **为什么选 EIA 场景而不是其他场景？**
    > EIA 有四个特点使它成为这个框架的理想应用实例。(1) 案例驱动——环评工作的核心就是不断积累项目案例经验，天然匹配 L3→L2 蒸馏模式。(2) 认知可结构化——风险模式、合规要点、影响规律都是可以明确表达的认知，不是模糊的"感觉"，每个认知都有明确的 target 和 content。(3) 存在真实认知冲突——新旧排放标准替代、不同来源的矛盾信息、同一项目不同阶段的风险波动，让六类冲突检测有真实场景支撑，不需要编造。(4) 行业壁垒高——资深环评工程师稀缺，经验沉淀有实际社会价值。相比之下，电商推荐或客服问答虽然数据量大，但认知深度不够，无法展示冲突检测和贝叶斯演化的技术优势。

19. **12 个案例怎么选的？覆盖了哪些行业和风险类型？**
    > 不是随机选，是按三个维度交叉设计的矩阵。行业维度：化工、制药、喷涂、电镀/表面处理、综合园区——5 个环评高频行业。风险维度：大气污染(VOC)、水污染(COD/重金属)、地下水、异味扰民、危废处置、邻避效应——6 类典型环评风险。冲突维度：故意设计了 3 组 overlap（同方向案例重复出现→置信度提升）、2 组 oppose（矛盾结论→贝叶斯对抗更新）、1 组 supersede（新旧标准替代→旧认知归档）。每个案例都标注了 `_group` 和 `_conflict_target` 元数据，让 eval 脚本可以自动验证每组冲突是否被正确识别。

20. **法规知识库为什么不做全文 RAG 而做结构化摘要？**
    > 因为项目的核心不是"法规问答"而是"认知形成"。全文 RAG 能回答"《环评法》第二十条写了什么"，但无法形成"VOC排放+邻近居民区→需重点关注公众参与"这种认知。结构化摘要（law + article + industry + pollutant + keywords + requirement + related_dimension）让法规条款可以和 risk_pattern/compliance_pattern 形成映射关系。比如一条关于 VOC 的 compliance_pattern 认知，可以通过 `pollutant=VOC` 自动关联到《大气污染防治法》第十八条和《环评法》第二十条。这种"法规-认知对齐"的简历含金量远高于一个普通的法规 RAG。全文检索可以后续作为 L0 层的一个检索通道加上，但不是核心差异化能力。

21. **如果用户问"我这个项目选址有什么问题"，系统怎么回答？**
    > 三类检索并行。(1) L3 案例检索——向量检索 topic=site_selection/public_concern 的案例，找回类似"某工业园区合规审批但遭遇邻避效应"的历史案例。(2) L2 认知查询——从 Neo4j 拉 experience_pattern 中与选址相关的认知，如"居民区500m范围内项目公众关注度显著升高""选址阶段充分调查敏感目标可避免大量后期问题"。(3) L0 实体匹配——如果用户提到了具体污染物或敏感目标（如"项目靠近学校"），匹配相关的法规实体和条款。LLM 综合三类信息生成回复：先引用已发生的类似案例（事实），再给出经验判断（认知），最后指出需要关注的法规要点（法规）。这比纯 LLM 凭空回答的可信度高一个数量级。

22. **你怎么确保 LLM 不会编造法规或案例？**
    > 三道防线。(1) 检索前置——所有事实（案例、认知、法规）先检索再注入 System Prompt，LLM 只做"综合和表达"不做"回忆和检索"。System Prompt 明确写"如果被问及你不知道的事实，不要编造，应建议查阅相关技术导则"。(2) 置信度标记——每条 L2 认知都带 confidence 字段，context_builder 组装时把置信度注入上下文。LLM 回复时可以区分"高置信度的经验结论"和"尚需验证的初步判断"。(3) `fact_verifier` 节点——对数据类回复做数字校验，检测 LLM 输出中的数值是否在检索到的 fact_snapshot 中出现，未匹配到则标记需要重新生成。三道防线分别防止"幻觉"的发生阶段、传播阶段和输出阶段。

23. **这个系统跟市面上的环评软件（如 EIAPro）有什么区别？**
    > EIAPro 是计算工具——输入排放参数，计算扩散模型和浓度分布，输出数值结果。我这个是认知工具——不计算浓度，而是从历史案例中提炼"这类项目历史上出过什么问题""审批时哪个环节容易卡""居民投诉的典型案例是什么"。本质差异：EIAPro 做数值预测（基于物理模型），我的系统做经验推理（基于认知图谱）。两者是互补的——一个环评工程师既需要用 EIAPro 算大气扩散，也需要查阅历史案例和专家经验来做综合判断。可以这样类比：EIAPro 是"计算器"，这个系统是"师父带徒弟"。

### 未来展望（4题）

24. **如果给你三个月继续做，你会做什么？**
    > 三件事，按优先级：(1) 案例自动入库管线——当前案例是手工设计的 JSON，要接真实数据需要一个"文档→结构化案例"的提取链，用 LLM 从环评报告 PDF 中提取 project_type/pollutant/sensitive_target 等字段自动入库；(2) 法规动态更新机制——当前法规是静态 JSON，实际法规会修订更新，需要加一个"法规变更检测→type_2_supersede 自动触发"的机制，让认知图谱跟随法规变化自动演化；(3) 前端 Demo——当前只有 API，做一个简单的 Web 界面，展示"案例检索→认知蒸馏→冲突检测→置信度演化"的全链路可视化，面试时直接演示比口述有说服力十倍。

25. **你觉得这个框架还能应用到哪些领域？**
    > 核心适用条件：案例驱动 + 认知可结构化 + 存在冲突和演化。几个典型场景：(1) 医疗诊断——病例(L3)→诊疗认知(L2)，不同医生的诊断矛盾触发 oppose，新治疗指南替代旧指南触发 supersede；(2) 法律判例——判例(L3)→裁判规则(L2)，一审vs二审的矛盾判决触发 oppose；(3) 金融风控——违约案例(L3)→风控规则(L2)，市场环境变化导致旧规则失效触发 supersede；(4) 设备运维——故障案例(L3)→诊断经验(L2)，同一故障的不同根因分析触发 refine。关键是——这些场景只需要换 Schema 注册表（COGNITION_DIMENSIONS）和案例数据，核心引擎一行不用改。这个"领域无关性"本身就是简历最亮眼的点。

26. **如果要接真实的环评数据库，最大的挑战是什么？**
    > 不是技术问题，是数据质量问题。真实环评报告是非结构化 PDF，关键信息（污染物种类、排放量、敏感目标、审批结论）散落在不同章节，LLM 提取准确率很难做到 90% 以上。而且真实案例缺乏"标签"——你不知道哪些案例之间有冲突关系、哪些案例指向同一认知。换句话说，eval 所需的 ground truth 不存在。解决方案是先做半自动——LLM 提取 + 人工审核，积累 100~200 个高质量结构化案例后再做全自动。这本身也可以写入简历："设计 LLM+人工审核的混合标注管线，从真实环评报告中提取结构化案例数据"。

27. **你怎么看 Agent 记忆的未来发展方向？**
    > 三个趋势。(1) 从"检索增强"到"认知形成"——未来 Agent 不只是检索相关文档，而是像人一样从经验中形成抽象认知。Google DeepMind 的"Agent as Learner"方向已经在做这个。(2) 从"静态记忆"到"演化记忆"——置信度动态调整、旧认知自动归档、矛盾自动调解，记忆不再是写入后永不修改的死数据。认知科学里这叫"记忆再巩固"（memory reconsolidation）。(3) 从"单一 Agent"到"多 Agent 记忆共享"——一个 Agent 的经验可以传递给另一个 Agent，形成组织级记忆。技术上需要解决跨 Agent 认知冲突仲裁（谁的认知更可信？基于 track record 加权）。Mem0、LangMem 等项目已经在探索，但大多是简单的状态存储，缺乏本项目中的冲突检测和置信度演化机制——这正是差异化的价值所在。

### 行为面试（3题）

28. **这个项目是你一个人做的还是团队？**
    > 独立完成，从架构设计到代码实现到评估验证。但我不会回避"参考了社区方案"——LangGraph 的编排模式参考了官方文档的 Agent 示例，六类冲突的分类框架参考了知识图谱领域的冲突检测论文（KG Conflict Detection），贝叶斯更新公式参考了认知建模中的记忆更新模型（Memory Updating Model）。独立开发不等于从零发明，关键能力是理解、整合和改造不同来源的思路，形成自己的一套方案。用东北话说——不装，是啥就是啥。面试官更看重的是你能否讲清楚每个设计决策的 why，而不是你是不是全部原创。

29. **做这个项目过程中最大的挫折是什么？**
    > Schema 迁移。最初项目是学生心理场景，写着写着发现代码里 `student_id`、`emotion_primary`、`Student` 节点渗透到了每一个文件，改一个字段名要联动 35 个文件。最痛苦的是改了 Python 代码但 Milvus collection 的 field schema 还是旧的，运行时默默报错"field not found"——因为 Python 代码不校验 Milvus schema，只有在实际 insert/search 时才报错，排查要同时看懂 Python、Cypher 和 Milvus 三层的日志。这次经历让我学到两个东西：领域建模的第一行代码就要想清楚命名（改名成本随文件数指数增长）；以及把 Schema 注册表做成动态注入（`COGNITION_DIMENSIONS` → `build_dimensions_prompt()`）而非硬编码——这两件事都是从这次痛苦中来的。

30. **你从中学到的最重要的东西是什么？**
    > "框架思维"vs"功能思维"的区别。如果我只想做 EIA 专家 Agent，我可以把案例检索、法规匹配、风险提示堆在一起快速做出一个能跑的系统。但我选择先把底层认知记忆框架做扎实——三层记忆、Reflection 蒸馏、冲突检测、贝叶斯演化——然后 EIA 只是这个框架的一个应用实例。这个选择带来的后果是：改 4 行 Schema 注册表就能切换到全新领域，核心引擎一行不动；面试时能讲的不只是一个环评工具，而是一套通用的认知记忆方法论。花 70% 时间做框架、30% 时间做应用，短期看起来慢了，但长期简历价值翻倍。技术之外还学到一点：独立完成一个完整项目需要同时做架构设计、代码实现、测试验证、文档编写——这几件事的思维方式完全不同，但必须一个人全扛，这对综合能力的锻炼是写一万道 LeetCode 都比不了的。

---

## 四、一句话项目总结

> 设计并实现领域无关的认知记忆框架，通过三层记忆架构（L3情景/L2认知/L0实体）、LLM驱动的Reflection认知蒸馏、六类语义冲突检测和三因子贝叶斯置信度演化，实现专家经验的自动沉淀与动态更新，以环境影响评价（EIA）场景完成端到端验证。

题号	类别	核心论点
11	工程	async 让 Milvus/Neo4j/LLM 三路并发，降延迟 15%
12	工程	分层兜底：try/except 默认值 → quality_level 分级 → 不入库
13	工程	三层分步迁移：枚举→实体→图节点，migrate_episodic.py 增量迁移
14	工程	最终一致性：processed_for_l2 标记 + 崩溃后天然幂等重处理
15	工程	结构校验 + 语义校验，dry-run/live 双模式
16	工程	streak_direction 翻转时 count 不重置的 bug，log 辅助排查
17	工程	三层测试：单元参数化 + 集成 Mock LLM + E2E mini 案例集
18	业务	EIA 四特点：案例驱动/认知可结构化/真实冲突/行业壁垒
19	业务	三维矩阵：5行业 × 6风险 × 3冲突类型交叉设计
20	业务	结构化摘要 > 全文 RAG，实现"法规-认知对齐"
21	业务	三类检索并行：L3案例 + L2认知 + L0法规实体
22	业务	三道防线：检索前置 → 置信度标记 → fact_verifier 校验
23	业务	EIAPro=计算器（数值预测），我的系统=师父（经验推理）
24	展望	案例自动入库 → 法规动态更新 → 前端可视化 Demo
25	展望	医疗/法律/金融/运维——换 Schema 注册表即可适配
26	展望	PDF非结构化 + 缺乏 ground truth → 半自动 LLM+人工审核
27	展望	检索增强→认知形成，静态→演化，单Agent→多Agent记忆共享
28	行为	独立完成，但参考了 LangGraph 官方文档和 KG 冲突检测论文
29	行为	Schema 迁移联动 35 个文件 → 学会了动态注册表和迁移脚本
30	行为	框架思维 vs 功能思维：70% 做框架 30% 做应用，长期价值翻倍