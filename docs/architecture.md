# EIA Expert Agent — 项目架构

## 一、系统全景

```mermaid
flowchart TB
    subgraph Input["输入层"]
        CASE["EIA 案例<br/>(建设项目/审批/事故)"]
        REG["法规知识<br/>(环评法/条例/导则)"]
        QUERY["咨询查询<br/>(风险/合规/选址)"]
    end

    subgraph Classifier["Haiku 分类器"]
        CLS["案例分类<br/>risk_level / topic<br/>pollutant / sensitive_target"]
    end

    subgraph Memory["三层记忆架构"]
        direction TB
        L3["L3 情景记忆 (Milvus)<br/>案例快照 · 向量检索<br/>叙事链: prev → curr → next"]
        L2["L2 认知记忆 (Neo4j)<br/>专家认知图谱<br/>4维 × N条认知边"]
        L0["L0 实体图谱 (Neo4j)<br/>Entity节点: 项目/法规/污染物"]
    end

    subgraph Reflection["Reflection 认知蒸馏"]
        RF_LLM["LLM 语义提炼<br/>案例聚类 → 认知抽取"]
        CONFLICT["六类冲突检测<br/>LLM 语义比对"]
        BAYES["三因子贝叶斯更新<br/>C_peak / C_trough / streak"]
    end

    subgraph Output["输出层"]
        RISK["风险识别"]
        CASE_REF["案例参考"]
        COMPLIANCE["法规关注点"]
        EXPERT["专家经验建议"]
    end

    CASE --> CLS
    QUERY --> CLS
    CLS --> L3
    REG --> L0

    L3 --> RF_LLM
    RF_LLM --> L2
    L2 --> CONFLICT
    CONFLICT --> BAYES
    BAYES --> L2

    L2 --> Output
    L3 --> Output
    L0 --> Output

    style Memory fill:#1a1a2e,stroke:#16213e,color:#e0e0e0
    style Reflection fill:#0f3460,stroke:#16213e,color:#e0e0e0
```

---

## 二、认知蒸馏链路 (L3 → L2)

```mermaid
flowchart LR
    subgraph L3["L3: 案例情景记忆"]
        C1["case_01: 精细化工 VOC 居民区投诉"]
        C2["case_02: 汽车喷涂 VOC 居民区投诉"]
        C3["case_03: 制药 VOC 学校附近投诉"]
    end

    subgraph Reflection["Reflection 蒸馏引擎"]
        CLUSTER["按 topic 聚类<br/>air_pollution_risk ×3"]
        EXTRACT["LLM 语义提炼<br/>生成认知候选"]
        VALIDATE["置信度校验<br/>write_confidence ≥ 0.5"]
    end

    subgraph L2["L2: 专家认知图谱"]
        COG["risk_pattern → VOC<br/>VOC排放+邻近敏感目标<br/>= 高投诉风险<br/>confidence: 0.80"]
    end

    C1 & C2 & C3 --> CLUSTER --> EXTRACT --> VALIDATE --> COG
    COG -.->|"streak+1"| C1
```

---

## 三、六类冲突检测机制

```mermaid
flowchart TB
    subgraph Types["六类语义冲突"]
        T1["Type 1: Oppose 直接对立<br/>VOC风险低 vs VOC风险高"]
        T2["Type 2: Supersede 时间覆盖<br/>2020标准 → 2025新标准"]
        T3["Type 3: Refine 范围细化<br/>化工有风险 → 精细化工风险更高"]
        T4["Type 4: Source Conflict 来源冲突<br/>企业自报 vs 监测数据"]
        T5["Type 5: Affective 风险波动<br/>项目不同阶段风险等级变化"]
        T6["Type 6: Overlap 语义重叠<br/>多条案例指向同一风险"]
    end

    subgraph Process["冲突处理流程"]
        NEW["新认知候选"] --> LLM_CMP["LLM 语义比对<br/>vs 现存认知"]
        LLM_CMP --> CLASSIFY{"六分类判定"}
        CLASSIFY --> T1 & T2 & T3 & T4 & T5 & T6
    end

    subgraph Update["更新策略"]
        OPPOSE["Oppose: 贝叶斯对抗<br/>damage = C_peak - C_trough<br/>resistance = f(C_old)"]
        OVERLAP["Overlap: 置信度提升<br/>confidence += 0.05"]
        SUPERSEDE["Supersede: 新边覆盖<br/>旧认知归档"]
    end

    T1 --> OPPOSE
    T6 --> OVERLAP
    T2 --> SUPERSEDE

    style Types fill:#1a1a2e,stroke:#e94560,color:#e0e0e0
```

---

## 四、三因子贝叶斯置信度演化

```mermaid
flowchart LR
    subgraph Formula["贝叶斯更新公式"]
        DELTA["Δ = quality × direction × C_old × (1 - resistance) × streak_mult"]
    end

    subgraph Factors["三因子"]
        CP["C_peak<br/>历史最高置信度"]
        CT["C_trough<br/>历史最低置信度"]
        SK["streak<br/>连续同方向次数"]
    end

    subgraph Derived["导出指标"]
        DM["damage = C_peak - C_trough<br/>认知伤害深度"]
        RS["resistance = min((C-0.35)/0.65, 0.85)<br/>认知抵抗力"]
        RC["recovery = C_trough + damage × (1 - e^(-λt))<br/>自然恢复曲线"]
    end

    Factors --> Derived
    Derived --> DELTA
    DELTA -->|"C_new = C_old + Δ"| CONF["新置信度"]

    style Formula fill:#0f3460,stroke:#16213e,color:#e0e0e0
```

---

## 五、技术栈

| 层 | 技术 | 用途 |
|---|---|---|
| 编排 | **LangGraph** | 多节点有状态 Agent 编排 |
| 向量存储 | **Milvus** | L3 情景记忆向量检索 (COSINE/HNSW) |
| 图数据库 | **Neo4j** | L2 认知图谱 + Entity 节点关系 |
| 关系存储 | **MySQL** | L3-Cold 归档 + 会话管理 |
| LLM | **DashScope (Qwen)** | Reflection 蒸馏 + 冲突分类 + 案例分类 |
| Embedding | **BGE-Large-v1.5** | 768维中文语义向量 |
| Reranker | **BGE-Reranker-v2-m3** | 检索结果重排序 |

---

## 六、数据流时序

```mermaid
sequenceDiagram
    actor User as 用户
    participant API as Chat API
    participant CLS as Haiku 分类器
    participant MILVUS as Milvus (L3)
    participant NEO4J as Neo4j (L2 + L0)
    participant LLM as LLM (Qwen)
    participant REF as Reflection 引擎

    User->>API: EIA咨询
    API->>CLS: 分类 (risk_level/topic)
    CLS-->>API: case_info
    API->>MILVUS: 向量检索 L3 案例
    API->>NEO4J: 查询 L2 认知 + L0 实体
    MILVUS-->>API: 相关案例
    NEO4J-->>API: 专家认知 + 法规实体
    API->>LLM: 上下文 + 回复生成
    LLM-->>User: 专家建议

    Note over REF,MILVUS: 异步 Reflection
    REF->>MILVUS: pull_unprocessed
    MILVUS-->>REF: 未提炼案例
    REF->>LLM: 聚类 + 蒸馏
    LLM-->>REF: 认知候选
    REF->>NEO4J: 冲突检测 + 更新
```

---

## 七、简历可用的一句话架构描述

> 基于 LangGraph + Milvus + Neo4j 构建三层认知记忆架构（L3情景/L2语义/L0实体），
> 通过 LLM驱动的 Reflection 蒸馏引擎实现案例到专家认知的自动转化，
> 配合六类语义冲突检测和三因子贝叶斯置信度演化机制，
> 形成可长期沉淀和动态更新的 EIA 专家认知系统。
