"""数据库初始化脚本 — 创建所有 PostgreSQL 表 + Neo4j 约束 + Milvus Collection

运行: python -m app.init_db
"""

import asyncio

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from app.infrastructure.config import get_settings
from app.infrastructure.embedding import get_embedding_service
from app.repositories.milvus_repo import MilvusRepo

settings = get_settings()

# ═══════════════════════════════════════════════════════════
# PostgreSQL DDL
# ═══════════════════════════════════════════════════════════

PG_DDL = """
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS thread_session_map;
DROP TABLE IF EXISTS admin_audit_log;
DROP TABLE IF EXISTS crisis_alerts;
DROP TABLE IF EXISTS security_log;
DROP TABLE IF EXISTS student_profile;
DROP TABLE IF EXISTS session_archive;
DROP TABLE IF EXISTS l2_draft_candidates;
DROP TABLE IF EXISTS episodes;
DROP TABLE IF EXISTS l3_cold;
DROP TABLE IF EXISTS scores;
DROP TABLE IF EXISTS attendance;

DROP TABLE IF EXISTS conversation_messages;
DROP TABLE IF EXISTS conversation_episodes;
DROP TABLE IF EXISTS conversation_sessions;
DROP TABLE IF EXISTS employments;
DROP TABLE IF EXISTS memory_embeddings;
DROP TABLE IF EXISTS user_memories;
DROP TABLE IF EXISTS advisors;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS roles;
DROP TABLE IF EXISTS alembic_version;

DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS classes;
DROP TABLE IF EXISTS teachers;
DROP TABLE IF EXISTS users;

CREATE TABLE students (
    student_id   VARCHAR(32) PRIMARY KEY,
    name         VARCHAR(64) NOT NULL,
    class_name   VARCHAR(32) NOT NULL,
    teacher_id   VARCHAR(32) NOT NULL,
    gender       VARCHAR(4),
    birth_date   DATE,
    enrollment_date DATE,
    created_at   TIMESTAMP DEFAULT NOW(),
    updated_at   TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_students_class ON students(class_name);
CREATE INDEX idx_students_teacher ON students(teacher_id);

CREATE TABLE scores (
    id           BIGINT PRIMARY KEY AUTO_INCREMENT,
    student_id   VARCHAR(32) NOT NULL,
    subject      VARCHAR(32) NOT NULL,
    score        DECIMAL(5,1) NOT NULL,
    exam_date    DATE NOT NULL,
    exam_type    VARCHAR(16) DEFAULT '月考',
    rank_total   INT,
    rank_class   INT,
    created_at   TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);
CREATE INDEX idx_scores_student ON scores(student_id);
CREATE INDEX idx_scores_subject ON scores(student_id, subject);

CREATE TABLE attendance (
    id           BIGINT PRIMARY KEY AUTO_INCREMENT,
    student_id   VARCHAR(32) NOT NULL,
    date         DATE NOT NULL,
    status       VARCHAR(16) NOT NULL,
    reason       VARCHAR(256),
    created_at   TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);
CREATE INDEX idx_attendance_student ON attendance(student_id);

CREATE TABLE classes (
    class_name   VARCHAR(32) PRIMARY KEY,
    grade        VARCHAR(16) NOT NULL,
    teacher_id   VARCHAR(32) NOT NULL
);

CREATE TABLE teachers (
    teacher_id   VARCHAR(32) PRIMARY KEY,
    name         VARCHAR(64) NOT NULL,
    department   VARCHAR(64),
    title        VARCHAR(32)
);

CREATE TABLE users (
    user_id      VARCHAR(32) PRIMARY KEY,
    role         VARCHAR(16) NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    disabled     BOOLEAN DEFAULT FALSE,
    created_at   TIMESTAMP DEFAULT NOW()
);

-- 记忆表
CREATE TABLE l3_cold (
    cold_id        VARCHAR(128) PRIMARY KEY,
    student_id     VARCHAR(32) NOT NULL,
    session_id     VARCHAR(64) NOT NULL,
    raw_dialogue   JSON NOT NULL,
    crisis_flag    BOOLEAN DEFAULT FALSE,
    importance     FLOAT DEFAULT 0.5,
    archive_status VARCHAR(16) DEFAULT 'hot',
    need_reprocess BOOLEAN DEFAULT FALSE,
    created_at     TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_l3_cold_student ON l3_cold(student_id);
CREATE INDEX idx_l3_cold_created ON l3_cold(created_at);
CREATE INDEX idx_l3_cold_status ON l3_cold(archive_status);

-- Episode 情景记忆容器 (Quick Win 2: Episode 边界检测)
CREATE TABLE episodes (
    episode_id       VARCHAR(128) PRIMARY KEY,
    student_id       VARCHAR(32) NOT NULL,
    session_id       VARCHAR(64) NOT NULL,
    topic            VARCHAR(32) NOT NULL,
    started_at       TIMESTAMP NOT NULL,
    ended_at         TIMESTAMP,
    l3_count         INT DEFAULT 1,
    is_closed        BOOLEAN DEFAULT FALSE,
    boundary_trigger VARCHAR(32) DEFAULT 'first_episode',
    created_at       TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_episodes_student ON episodes(student_id);
CREATE INDEX idx_episodes_active ON episodes(is_closed, student_id);

CREATE TABLE l2_draft_candidates (
    draft_id       VARCHAR(128) PRIMARY KEY,
    student_id     VARCHAR(32) NOT NULL,
    trait_name     VARCHAR(128) NOT NULL,
    trait_value    VARCHAR(256),
    polarity       VARCHAR(16) DEFAULT 'positive',
    source_type    VARCHAR(16) NOT NULL,
    write_confidence FLOAT DEFAULT 0.5,
    evidence_l3_ids JSON,
    drafted_at     TIMESTAMP DEFAULT NOW(),
    consumed       BOOLEAN DEFAULT FALSE
);
CREATE INDEX idx_draft_student ON l2_draft_candidates(student_id);
CREATE INDEX idx_draft_confidence ON l2_draft_candidates(write_confidence);

CREATE TABLE session_archive (
    session_id       VARCHAR(64) PRIMARY KEY,
    student_id       VARCHAR(32) NOT NULL,
    closed_at        TIMESTAMP NOT NULL,
    close_reason     VARCHAR(16) NOT NULL,
    summary          TEXT,
    safety_snapshot  JSON,
    last_intent      VARCHAR(32),
    last_topic       VARCHAR(64),
    unclosed_topic   VARCHAR(256),
    message_count    INT DEFAULT 0,
    created_at       TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_sa_student ON session_archive(student_id);

CREATE TABLE student_profile (
    student_id            VARCHAR(32) PRIMARY KEY,
    rolling_summary       TEXT,
    total_sessions        INT DEFAULT 0,
    total_messages        INT DEFAULT 0,
    first_interaction_at  TIMESTAMP,
    last_interaction_at   TIMESTAMP,
    safety_status         VARCHAR(32) DEFAULT 'normal',
    violation_b1_count    INT DEFAULT 0,
    violation_b2_count    INT DEFAULT 0,
    b2_window_start       TIMESTAMP,
    b2_last_decay_time    TIMESTAMP,
    account_status        VARCHAR(16) DEFAULT 'normal',
    updated_at            TIMESTAMP DEFAULT NOW()
);

-- 安全表
CREATE TABLE crisis_alerts (
    id           BIGINT PRIMARY KEY AUTO_INCREMENT,
    student_id   VARCHAR(32) NOT NULL,
    teacher_id   VARCHAR(32) NOT NULL,
    severity     VARCHAR(16) NOT NULL,
    summary      VARCHAR(500) NOT NULL,
    status       VARCHAR(16) DEFAULT 'pending',
    triggered_at TIMESTAMP DEFAULT NOW(),
    confirmed_at TIMESTAMP,
    confirmed_by VARCHAR(32),
    resolution   VARCHAR(500),
    escalated_at TIMESTAMP
);

CREATE TABLE security_log (
    id                 BIGINT PRIMARY KEY AUTO_INCREMENT,
    student_id         VARCHAR(32) NOT NULL,
    teacher_id         VARCHAR(32),
    category           VARCHAR(16) NOT NULL,
    risk_level         INT NOT NULL,
    trigger_type       VARCHAR(16) NOT NULL,
    escalation         VARCHAR(16) NOT NULL,
    original_message_hash VARCHAR(64),
    anonymized_summary VARCHAR(256),
    new_user_status    VARCHAR(32),
    created_at         TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_sl_student ON security_log(student_id);

CREATE TABLE admin_audit_log (
    id           BIGINT PRIMARY KEY AUTO_INCREMENT,
    admin_id     VARCHAR(32) NOT NULL,
    action_type  VARCHAR(32) NOT NULL,
    target_type  VARCHAR(32) NOT NULL,
    target_id    VARCHAR(64),
    action_detail JSON,
    ip_address   VARCHAR(45),
    created_at   TIMESTAMP DEFAULT NOW()
);

-- 运行时表
CREATE TABLE thread_session_map (
    session_id   VARCHAR(64) PRIMARY KEY,
    thread_id    VARCHAR(128) NOT NULL,
    student_id   VARCHAR(32) NOT NULL,
    user_role    VARCHAR(16) NOT NULL,
    carry_over   VARCHAR(16) NOT NULL,
    created_at   TIMESTAMP DEFAULT NOW(),
    closed_at    TIMESTAMP
);

SET FOREIGN_KEY_CHECKS = 1;
"""


async def init_postgres() -> None:
    """创建所有 PG 表"""
    async_url = settings.DATABASE__URL.replace("mysql+pymysql://", "mysql+asyncmy://")
    engine = create_async_engine(async_url, echo=True)

    async with engine.begin() as conn:
        for statement in PG_DDL.split(";"):
            # Remove line-based SQL comments, keep the actual SQL
            lines = [line for line in statement.split("\n")
                     if not line.strip().startswith("--")]
            stmt = "\n".join(lines).strip()
            if stmt:
                try:
                    await conn.execute(text(stmt))
                except Exception as e:
                    if "Duplicate" not in str(e) and "already exists" not in str(e):
                        print(f"SKIP: {e}")

    await engine.dispose()
    print("PostgreSQL tables created.")


async def seed_postgres() -> None:
    """插入测试数据（学生、教师、用户账号）"""
    from passlib.context import CryptContext

    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    default_hash = pwd.hash("123456")

    async_url = settings.DATABASE__URL.replace("mysql+pymysql://", "mysql+asyncmy://")
    engine = create_async_engine(async_url, echo=False)

    async with engine.begin() as conn:
        # 测试班级
        await conn.execute(text(
            "INSERT INTO classes (class_name, grade, teacher_id) "
            "VALUES ('初二3班', '初二', 'TCH_001')"
        ))

        # 测试教师（业务表）
        await conn.execute(text(
            "INSERT INTO teachers (teacher_id, name, department, title) "
            "VALUES "
            "('TCH_001', '张老师', '教务处', '辅导员'), "
            "('TCH_002', '李老师', '教务处', '班主任')"
        ))

        # 测试学生（业务表）
        await conn.execute(text(
            "INSERT INTO students "
            "(student_id, name, class_name, teacher_id, gender) "
            "VALUES "
            "('XH_2024001', '小红', '初二3班', 'TCH_001', '女'), "
            "('XH_2024002', '小明', '初二3班', 'TCH_001', '男'), "
            "('XH_2024003', '小刚', '初二3班', 'TCH_001', '男')"
        ))

        # 用户登录账号
        await conn.execute(text(
            "INSERT INTO users (user_id, role, password_hash) "
            "VALUES "
            f"('XH_2024001', 'student', '{default_hash}'), "
            f"('XH_2024002', 'student', '{default_hash}'), "
            f"('XH_2024003', 'student', '{default_hash}'), "
            f"('TCH_001', 'teacher', '{default_hash}'), "
            f"('TCH_002', 'teacher', '{default_hash}'), "
            f"('ADMIN_001', 'admin', '{default_hash}')"
        ))

    await engine.dispose()
    print("Seed data inserted.")


def init_neo4j() -> None:
    """创建 Neo4j 约束、索引 和 基础知识库"""
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(
        settings.NEO4J__URI,
        auth=(settings.NEO4J__USER, settings.NEO4J__PASSWORD),
        connection_acquisition_timeout=5,
        connection_timeout=5,
    )

    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Character) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Scene) REQUIRE s.scene_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Student) REQUIRE s.student_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (sub:Subject) REQUIRE sub.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Trait) REQUIRE t.name IS UNIQUE",
    ]
    indexes = [
        "CREATE INDEX IF NOT EXISTS FOR (s:Scene) ON (s.emotion_tag)",
        "CREATE INDEX IF NOT EXISTS FOR (t:Trait) ON (t.confidence)",
    ]

    with driver.session() as session:
        for c in constraints:
            try:
                session.run(c)
            except Exception:
                pass
        for i in indexes:
            try:
                session.run(i)
            except Exception:
                pass

        # ── 红楼梦角色节点 ──
        session.run(
            """
            MERGE (daiyu:Character {id: "char_daiyu"})
            SET daiyu.name = "林黛玉",
                daiyu.aliases = ["颦儿","潇湘妃子","林妹妹"],
                daiyu.role = "protagonist",
                daiyu.traits = ["敏感","才情","多疑","孤傲"],
                daiyu.residence = "潇湘馆",
                daiyu.importance = 1.0,
                daiyu.sensitivity = 0.9,
                daiyu.talent = 0.95,
                daiyu.suspicion = 0.8,
                daiyu.fragility = 0.85
            """
        )
        session.run(
            """
            MERGE (baoyu:Character {id: "char_baoyu"})
            SET baoyu.name = "贾宝玉",
                baoyu.aliases = ["宝二爷","怡红公子","混世魔王"],
                baoyu.role = "protagonist",
                baoyu.traits = ["痴情","叛逆","厌学","怜香惜玉"],
                baoyu.residence = "怡红院",
                baoyu.importance = 1.0
            """
        )
        session.run(
            """
            MERGE (baochai:Character {id: "char_baochai"})
            SET baochai.name = "薛宝钗",
                baochai.aliases = ["宝姐姐","蘅芜君"],
                baochai.role = "protagonist",
                baochai.traits = ["端庄","世故","博学","冷情"],
                baochai.residence = "蘅芜苑",
                baochai.importance = 0.95
            """
        )
        session.run(
            """
            MERGE (jiamu:Character {id: "char_jiamu"})
            SET jiamu.name = "贾母",
                jiamu.aliases = ["老太太","老祖宗","史太君"],
                jiamu.role = "elder",
                jiamu.traits = ["慈爱","权威","享乐","精明"],
                jiamu.residence = "荣庆堂",
                jiamu.importance = 0.9
            """
        )
        session.run(
            """
            MERGE (wang:Character {id: "char_wangxifeng"})
            SET wang.name = "王熙凤",
                wang.aliases = ["凤姐","凤辣子","琏二奶奶"],
                wang.role = "manager",
                wang.traits = ["精明","泼辣","能干","狠毒"],
                wang.residence = "荣国府",
                wang.importance = 0.9
            """
        )
        session.run(
            """
            MERGE (xiangyun:Character {id: "char_xiangyun"})
            SET xiangyun.name = "史湘云",
                xiangyun.aliases = ["云妹妹","枕霞旧友"],
                xiangyun.role = "supporting",
                xiangyun.traits = ["豪爽","天真","才情","乐观"],
                xiangyun.residence = "保龄侯府",
                xiangyun.importance = 0.75
            """
        )
        session.run(
            """
            MERGE (tanchun:Character {id: "char_tanchun"})
            SET tanchun.name = "贾探春",
                tanchun.aliases = ["三姑娘","蕉下客"],
                tanchun.role = "supporting",
                tanchun.traits = ["精明","有志","才情","自尊"],
                tanchun.residence = "秋爽斋",
                tanchun.importance = 0.8
            """
        )

        # ── 主要人物关系 ──
        relationships = [
            # 黛玉的关系
            ("char_daiyu", "char_baoyu",
             "倾慕", 0.95, {"nature": "知己之爱", "key_quote": "这个妹妹我曾见过的"}),
            ("char_daiyu", "char_baochai",
             "忌惮", 0.7, {"nature": "情敌/亦友", "note": "金玉良缘 vs 木石前盟"}),
            ("char_daiyu", "char_jiamu",
             "依赖", 0.85, {"nature": "祖孙", "note": "贾母对外孙女的疼爱"}),
            # 宝玉的关系
            ("char_baoyu", "char_baochai",
             "敬而远之", 0.6, {"nature": "表姐弟/夫妻", "note": "金玉良缘"}),
            ("char_baoyu", "char_wangxifeng",
             "亲近", 0.7, {"nature": "表嫂/玩伴"}),
            ("char_baoyu", "char_xiangyun",
             "友善", 0.65, {"nature": "表兄妹/玩伴"}),
            # 宝钗的关系
            ("char_baochai", "char_wangxifeng",
             "同盟", 0.6, {"nature": "王家亲属"}),
            ("char_baochai", "char_xiangyun",
             "亲近", 0.7, {"nature": "闺中密友"}),
            # 探春
            ("char_tanchun", "char_baoyu",
             "亲近", 0.7, {"nature": "同父异母兄妹"}),
            ("char_tanchun", "char_daiyu",
             "友善", 0.65, {"nature": "诗社同伴"}),
        ]
        for from_id, to_id, rel_type, weight, props in relationships:
            session.run(
                f"""
                MATCH (a:Character {{id: $from_id}})
                MATCH (b:Character {{id: $to_id}})
                MERGE (a)-[r:{rel_type.replace(' ', '_')}]->(b)
                SET r.weight = $weight, r += $props
                """,
                {"from_id": from_id, "to_id": to_id,
                 "weight": weight, "props": props},
            )

        # ── 名场面节点 ──
        scenes = [
            {
                "scene_id": "scene_001", "scene_name": "黛玉葬花",
                "chapter": 27,
                "emotion_tag": "sadness",
                "emotion_tags": ["sadness", "lonely", "sensitive"],
                "characters": ["char_daiyu", "char_baoyu"],
                "scene_type": "emotional",
                "trigger_tag": "惜春伤时",
                "key_quote": "花谢花飞花满天，红消香断有谁怜",
                "scene_summary": "黛玉见落花触景生情，以葬花自喻身世飘零",
                "response_hint": "对学生的哀伤表达深切共情，用落花比喻引导其倾诉心事",
            },
            {
                "scene_id": "scene_002", "scene_name": "黛玉焚稿",
                "chapter": 97,
                "emotion_tag": "hopelessness",
                "emotion_tags": ["hopelessness", "sadness", "anger"],
                "characters": ["char_daiyu"],
                "scene_type": "emotional",
                "trigger_tag": "绝望断情",
                "key_quote": "侬今葬花人笑痴，他年葬侬知是谁",
                "scene_summary": "黛玉闻知宝玉娶宝钗，焚烧诗稿以断情丝",
                "response_hint": "★ 仅用于心理危机场景的共情介入，不主动引用",
            },
            {
                "scene_id": "scene_003", "scene_name": "黛玉进贾府",
                "chapter": 3,
                "emotion_tag": "anxiety",
                "emotion_tags": ["anxiety", "calm", "sensitive"],
                "characters": ["char_daiyu", "char_jiamu"],
                "scene_type": "narrative",
                "trigger_tag": "寄人篱下",
                "key_quote": "步步留心，时时在意，不肯轻易多说一句话，多行一步路",
                "scene_summary": "黛玉初入贾府时的谨慎小心，对陌生环境的敏感适应",
                "response_hint": "当学生表现出对陌生环境的紧张时，以自身经历给予理解",
            },
            {
                "scene_id": "scene_004", "scene_name": "黛玉教香菱学诗",
                "chapter": 48,
                "emotion_tag": "happy",
                "emotion_tags": ["happy", "calm"],
                "characters": ["char_daiyu"],
                "scene_type": "teaching",
                "trigger_tag": "授业解惑",
                "key_quote": "什么难事，也值得去学！不过是起承转合",
                "scene_summary": "黛玉热情教导香菱学诗，展现其才情与耐心的一面",
                "response_hint": "学生请教学习问题时，以过来人身份鼓励，先轻描淡写再认真指导",
            },
            {
                "scene_id": "scene_005", "scene_name": "宝黛共读西厢",
                "chapter": 23,
                "emotion_tag": "happy",
                "emotion_tags": ["happy", "excited"],
                "characters": ["char_daiyu", "char_baoyu"],
                "scene_type": "romantic",
                "trigger_tag": "知己共读",
                "key_quote": "我就是个'多愁多病身'，你就是那'倾国倾城貌'",
                "scene_summary": "宝黛二人在桃花树下共读《西厢记》，心意相通的美好时光",
                "response_hint": "学生提到兴趣爱好时，可自然地分享乐趣并建立情感连接",
            },
            {
                "scene_id": "scene_006", "scene_name": "黛玉讽宝玉上学",
                "chapter": 9,
                "emotion_tag": "calm",
                "emotion_tags": ["calm", "happy"],
                "characters": ["char_daiyu", "char_baoyu"],
                "scene_type": "daily",
                "trigger_tag": "劝学",
                "key_quote": "好，这一去，可定是要'蟾宫折桂'去了。我不能送你了",
                "scene_summary": "黛玉用半开玩笑的方式送宝玉去上学",
                "response_hint": "学生提及考试/上学时，用半调侃的口吻表达关心和鼓励",
            },
            {
                "scene_id": "scene_007", "scene_name": "黛玉感怀身世",
                "chapter": 45,
                "emotion_tag": "lonely",
                "emotion_tags": ["lonely", "sadness", "sensitive"],
                "characters": ["char_daiyu"],
                "scene_type": "emotional",
                "trigger_tag": "孤寂自伤",
                "key_quote": "秋花惨淡秋草黄，耿耿秋灯秋夜长。已觉秋窗秋不尽，那堪风雨助凄凉",
                "scene_summary": "黛玉秋夜独坐，听闻窗外风雨声而感怀身世",
                "response_hint": "学生表达孤独感时，以诗句共情并暗示孤独中的诗意与坚韧",
            },
        ]
        for sc in scenes:
            session.run(
                """
                MERGE (s:Scene {scene_id: $scene_id})
                SET s.scene_name = $scene_name,
                    s.chapter = $chapter,
                    s.emotion_tag = $emotion_tag,
                    s.emotion_tags = $emotion_tags,
                    s.scene_type = $scene_type,
                    s.trigger_tag = $trigger_tag,
                    s.key_quote = $key_quote,
                    s.scene_summary = $scene_summary,
                    s.response_hint = $response_hint
                WITH s
                UNWIND $characters AS cid
                MATCH (c:Character {id: cid})
                MERGE (s)-[:FEATURES]->(c)
                """,
                sc,
            )

    driver.close()
    print("Neo4j constraints + characters + relationships + scenes created.")


def _migrate_l3_schema(collection) -> None:
    """为已有 L3 Collection 补加 prev_l3_id / episode_id 字段（向前兼容）"""
    from pymilvus import DataType

    existing_fields = {f.name for f in collection.schema.fields}
    new_fields = []

    if "prev_l3_id" not in existing_fields:
        new_fields.append(FieldSchema("prev_l3_id", DataType.VARCHAR, max_length=128))
    if "episode_id" not in existing_fields:
        new_fields.append(FieldSchema("episode_id", DataType.VARCHAR, max_length=128))

    if new_fields:
        print(f"Migrating L3 schema: adding fields {[f.name for f in new_fields]}")
        collection.release()
        for field in new_fields:
            collection.add_field(field)
        collection.load()


def init_milvus() -> None:
    """创建 Milvus Collection"""
    from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections

    connections.connect(alias="default", uri=settings.MILVUS__URI, timeout=10)
    print("Loading embedding model (this takes ~30s on first run)...")
    try:
        dim = get_embedding_service().dim
    except Exception as e:
        print(f"Embedding model load failed: {e}")
        connections.disconnect("default")
        return

    # l3_hot_memories
    l3_fields = [
        FieldSchema("l3_id", DataType.VARCHAR, is_primary=True, max_length=128),
        FieldSchema("student_id", DataType.VARCHAR, max_length=32, is_partition_key=True),
        FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=dim),
        FieldSchema("session_id", DataType.VARCHAR, max_length=64),
        FieldSchema("timestamp", DataType.INT64),
        FieldSchema("risk_level", DataType.VARCHAR, max_length=32),
        FieldSchema("risk_confidence", DataType.FLOAT),
        FieldSchema("topic", DataType.VARCHAR, max_length=64),
        FieldSchema("pollutant", DataType.VARCHAR, max_length=64),
        FieldSchema("sensitive_target", DataType.VARCHAR, max_length=64),
        FieldSchema("risk_event", DataType.VARCHAR, max_length=512),
        FieldSchema("importance", DataType.FLOAT),
        FieldSchema("write_confidence", DataType.FLOAT),
        FieldSchema("processed_for_l2", DataType.VARCHAR, max_length=16),
        FieldSchema("archived", DataType.BOOL),
        FieldSchema("cold_ref", DataType.VARCHAR, max_length=128),
        FieldSchema("prev_l3_id", DataType.VARCHAR, max_length=128),
        FieldSchema("episode_id", DataType.VARCHAR, max_length=128),
        FieldSchema("embedding_text", DataType.VARCHAR, max_length=2048),
    ]
    l3_schema = CollectionSchema(l3_fields, "L3-Hot EIA case snapshots")
    l3_collection = Collection(settings.MILVUS__L3_COLLECTION, l3_schema)

    # HNSW index
    l3_index_params = {
        "metric_type": "COSINE",
        "index_type": "HNSW",
        "params": {"M": 16, "efConstruction": 200},
    }
    l3_collection.create_index("embedding", l3_index_params)
    # timestamp 标量索引 — get_last_l3 / get_adjacent_l3 的 sort 查询需要
    try:
        l3_collection.create_index(
            "timestamp",
            {"index_type": "STL_SORT"},
        )
    except Exception:
        pass  # 索引已存在或类型不支持时跳过
    l3_collection.load()

    # ── Schema 迁移: 为已有 Collection 补加叙事链字段 ──
    _migrate_l3_schema(l3_collection)

    # hlmm_scenes
    hlmm_fields = [
        FieldSchema("scene_id", DataType.VARCHAR, is_primary=True, max_length=128),
        FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=dim),
        FieldSchema("scene_name", DataType.VARCHAR, max_length=128),
        FieldSchema("chapter", DataType.INT64),
        FieldSchema("emotion_tag", DataType.VARCHAR, max_length=32),
        FieldSchema("emotion_tags", DataType.ARRAY, element_type=DataType.VARCHAR, max_length=32, max_capacity=10),
        FieldSchema("characters", DataType.ARRAY, element_type=DataType.VARCHAR, max_length=64, max_capacity=20),
        FieldSchema("scene_type", DataType.VARCHAR, max_length=32),
        FieldSchema("trigger_tag", DataType.VARCHAR, max_length=32),
        FieldSchema("key_quote", DataType.VARCHAR, max_length=512),
        FieldSchema("scene_summary", DataType.VARCHAR, max_length=512),
        FieldSchema("response_hint", DataType.VARCHAR, max_length=256),
    ]
    hlmm_schema = CollectionSchema(hlmm_fields, "HLMM famous scenes")
    hlmm_collection = Collection(settings.MILVUS__HLMM_COLLECTION, hlmm_schema)
    hlmm_collection.create_index("embedding", l3_index_params)
    hlmm_collection.load()

    connections.disconnect("default")
    print("Milvus collections created.")


async def main() -> None:
    print("Initializing databases...")
    await init_postgres()
    await seed_postgres()
    try:
        init_neo4j()
    except Exception as e:
        print(f"Neo4j init skipped: {e}")
    try:
        init_milvus()
    except Exception as e:
        print(f"Milvus init skipped: {e}")
    print("Database initialization complete.")


if __name__ == "__main__":
    asyncio.run(main())
