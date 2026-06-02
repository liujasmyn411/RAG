林黛玉 Agent + 学生管理系统：记忆架构设计方案总结
本文档总结了基于 LangGraph + Neo4j + Milvus 技术栈的 Agent 记忆架构设计，核心解决“感性人设”与“理性教务数据”的融合与隔离问题。可直接用于新会话的上下文初始化。
1. 核心设计理念：双核驱动 + 情境路由
三态存储分离：
角色本体记忆 (Neo4j)：红楼原著切片、人物关系图谱、性格范式（永不遗忘）。
业务事实记忆 (PostgreSQL)：学籍、成绩、考勤等结构化数据（严禁向量化，仅通过工具调用）。
关系演化记忆 (Milvus + Neo4j)：互动历史、情绪标签、专属羁绊（支持异步整理与衰减）。
物理隔离原则：教务数据与黛玉人设上下文在 State 中严格分离，避免角色崩塌或数据幻觉。
2. LangGraph 工作记忆 State 定义 (已确认)
采用 TypedDict 定义 AgentState，核心字段如下：
表格
字段名	类型	作用与隔离策略
messages	Annotated[list, add_messages]	核心对话流，仅保留自然语言交互，自动追加
current_intent	Literal[...]	情境路由标记 (daiyu_chat / academic_query / psych_crisis)，决定加载哪套 Prompt 与检索策略
academic_context	Optional[dict]	业务数据暂存区，仅在教务查询时填充，不进入 messages
daiyu_persona_context	Optional[str]	人设增强包，仅在情感交互时填充（含红楼子图+情绪切片）
needs_memory_update	bool	异步记忆整理触发器，为 True 时才启动后台 Reflection
3. 工作记忆压缩与轮次策略 (已确认)
滑动窗口：保留最近 10 轮完整对话。
摘要触发：采用 语义触发（小模型判断对话价值），超过 10 轮且判定有价值时生成摘要；教务查询类对话跳过摘要。
摘要存储：作为 System Message 插入 messages 头部，保证历史脉络连贯。
业务数据：仅保留最近 1 次查询结果，不跨轮次持久化。
安全标记：心理危机状态永久保留，不参与常规压缩。
4. 待完善模块清单 (新会话接续点)
当前已完成【模块1：工作记忆设计】，后续需按顺序推进：
【模块2】检索增强策略：LangGraph 中编排 Milvus 向量检索与 Neo4j 子图提取的顺序、并行/Rerank 逻辑、情绪标签过滤规则。
【模块3】异步记忆整理机制：Reflection 节点的触发时机、LLM 提取 Prompt 设计、双库写入事务一致性、新旧记忆冲突解决。
【模块4】遗忘与置信度衰减：衰减公式与 Milvus 标量字段的结合、Neo4j 关系边权重动态更新、归档阈值设定。  
5. 关键技术约束备忘
心理安全熔断：识别到自伤/重度抑郁关键词时，立即绕过黛玉人设，切换标准干预话术并通知辅导员。
风格校准：允许额外 LLM 调用成本用于 Self-Correction Loop，确保回复符合黛玉口吻（半文半白、避免客服用语）。
情节预处理：红楼文本需提前用 LLM 批量标注 {scene, emotion, trigger, response_style, key_quote}，构建情绪索引后再入库。
新会话启动提示词建议：
“我正在开发一个嵌入林黛玉人设的学生信息管理 Agent，技术栈为 LangGraph + Neo4j + Milvus。已完成工作记忆 State 设计和压缩策略（见上方总结）。请继续帮我完善【模块2：检索增强策略】，重点设计 LangGraph 中如何编排 Milvus 情绪切片检索与 Neo4j 人物子图提取的协同流程。”