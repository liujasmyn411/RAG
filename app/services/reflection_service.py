"""Reflection 提炼服务 — L3 → L2 认知提炼引擎"""

import json
from datetime import datetime
from collections import defaultdict
from typing import Optional

from app.domain.enums import (
    ConflictType,
    StreakDirection,
    SourceType,
    get_dimension_target_type,
    get_dimension_label,
    get_dimension_keys,
    build_dimensions_prompt,
)
from app.domain.entities.memory import L2Cognition
from app.infrastructure.llm_client import get_llm_client
from app.infrastructure.config import get_settings
from app.repositories.neo4j_repo import Neo4jRepo
from app.repositories.milvus_repo import MilvusRepo


REFLECTION_PROMPT = """你是一个环评专家认知提炼助手。从多条案例记录中提炼专家的经验性认知。

可用的认知维度 (从注册表动态注入):
{dimensions_prompt}

规则:
· 从以上维度中选择最匹配的一个, 填入 relation_type 字段
· 至少2条案例记录指向同一方向才提炼
· 不编造案例中没有的内容
· 标注"案例直接体现"还是"专家推断"
· 如果多条案例记录之间有矛盾, 在输出中标注
· 输出严格JSON, 无其他文字

输出格式:
{{"cognitions": [{{
  "relation_type": "risk_pattern" | "compliance_pattern" | "impact_pattern" | "experience_pattern",
  "target": "VOC" | "化工项目" | "居民区投诉" | ...,
  "content": "涉及VOC排放且邻近居民区的项目具有较高投诉风险 — 对认知的完整描述",
  "trend": "波动"|"下降"|"上升"|"平稳"|null,
  "intensity": 0.75|null,
  "valence": "positive"|"negative"|"neutral"|null,
  "source_type": "reflection",
  "evidence_ids": ["l3_001","l3_002"],
  "contradiction_noted": "案例1显示VOC风险低但案例2风险高"|null
}}]}}"""


class ReflectionService:
    """Reflection 提炼引擎"""

    def __init__(self, neo4j_repo: Neo4jRepo, milvus_repo: MilvusRepo) -> None:
        self._neo4j = neo4j_repo
        self._milvus = milvus_repo
        self._llm = get_llm_client()
        self._settings = get_settings()

    # ═══════════════════════════════════════════════════════════
    # 主流程
    # ═══════════════════════════════════════════════════════════

    async def reflect(self, student_id: str) -> dict:
        """执行一次 Reflection"""

        # Step 1: 拉取未处理 L3
        l3_list = await self._milvus.pull_unprocessed(
            student_id, limit=self._settings.REFLECTION__MAX_L3_BATCH
        )
        if not l3_list:
            return {"status": "no_data"}

        # Step 2: 按 topic 聚类
        groups = self._cluster_by_topic(l3_list)
        viable = {
            k: v for k, v in groups.items()
            if len(v) >= 2 or any(
                l.get("topic") == "self_harm" for l in v
            )
        }
        if not viable:
            for l in l3_list:
                l["_skip_reason"] = "insufficient_group"
            await self._milvus.mark_processed([l["l3_id"] for l in l3_list])
            return {"status": "insufficient_data"}

        processed_ids = []
        total_cognitions = 0

        for topic, items in viable.items():
            candidate_ids = [l["l3_id"] for l in items]

            # Step 3: LLM 提炼
            candidates = await self._extract_cognitions(
                student_id, items[:self._settings.REFLECTION__MAX_PER_GROUP]
            )
            if not candidates:
                processed_ids.extend(candidate_ids)
                continue

            # Step 4: 查现存 L2
            existing_edges = await self._neo4j.get_student_traits(student_id)

            # Step 5: 冲突分类 + 更新
            for cand in candidates:
                conflict_type, old_edge = await self._classify_conflict(
                    cand, existing_edges
                )

                if conflict_type == ConflictType.TYPE_1_OPPOSE:
                    await self._update_bayesian_oppose(
                        student_id, cand, existing_edges
                    )
                elif conflict_type == ConflictType.TYPE_2_SUPERSEDE:
                    await self._handle_supersede(student_id, cand)
                elif conflict_type == ConflictType.TYPE_3_REFINE:
                    await self._handle_refine(student_id, cand)
                elif conflict_type == ConflictType.TYPE_6_OVERLAP:
                    await self._handle_overlap(student_id, cand)
                else:
                    await self._create_new_edge(student_id, cand)
                total_cognitions += 1

            processed_ids.extend(candidate_ids)

        # Step 6: 标记已处理
        await self._milvus.mark_processed(processed_ids)

        return {
            "status": "success",
            "groups_processed": len(viable),
            "cognitions_created": total_cognitions,
            "l3_processed": len(processed_ids),
        }

    # ═══════════════════════════════════════════════════════════
    # 私有: 聚类
    # ═══════════════════════════════════════════════════════════

    def _cluster_by_topic(self, l3_list: list[dict]) -> dict[str, list[dict]]:
        groups: dict[str, list[dict]] = defaultdict(list)
        for item in l3_list:
            topic = item.get("topic", "daily_chat")
            groups[topic].append(item)
        return dict(groups)

    # ═══════════════════════════════════════════════════════════
    # 私有: LLM 提炼
    # ═══════════════════════════════════════════════════════════

    async def _extract_cognitions(
        self, student_id: str, items: list[dict]
    ) -> list[dict]:
        summaries = []
        for i, l3 in enumerate(items):
            summaries.append(
                f"[{i+1}] {l3.get('timestamp','')} | "
                f"{l3.get('topic','')} | 风险:{l3.get('risk_level','')},"
                f"置信度{l3.get('risk_confidence',0.5)} | "
                f"污染物:{l3.get('pollutant','') or '无'} | "
                f"敏感目标:{l3.get('sensitive_target','') or '无'} | "
                f"embedding_text: {l3.get('embedding_text','')}"
            )

        user_prompt = f"项目主体: {student_id}\n\n近期案例记录:\n" + "\n".join(summaries)

        try:
            system_prompt = REFLECTION_PROMPT.format(
                dimensions_prompt=build_dimensions_prompt()
            )
            result = await self._llm.chat_json([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ])
            return result.get("cognitions", [])
        except Exception:
            return []

    # ═══════════════════════════════════════════════════════════
    # 私有: 冲突分类
    # ═══════════════════════════════════════════════════════════

    async def _classify_conflict(
        self, candidate: dict, existing: list[dict]
    ) -> tuple[ConflictType, dict | None]:
        """LLM 六分类语义比对, 返回 (类型, 旧边或None)"""
        relation_type = candidate.get("relation_type", "")
        target = candidate.get("target", "")
        new_content = candidate.get("content", "")

        for edge in existing:
            if edge.get("relation_type") == relation_type:
                if edge.get("target_name") == target:
                    old_content = edge.get("content", "")
                    if not old_content:
                        return ConflictType.TYPE_6_OVERLAP, edge

                    # LLM 语义比对六分类
                    try:
                        dim_label = get_dimension_label(relation_type)
                        prompt = CONFLICT_CLASSIFY_PROMPT.format(
                            dimension=dim_label,
                            old_content=old_content,
                            new_content=new_content,
                        )
                        result = await self._llm.haiku_json([
                            {"role": "user", "content": prompt},
                        ])
                        type_str = result.get("type", "type_1_oppose")
                        return ConflictType(type_str), edge
                    except Exception:
                        return ConflictType.TYPE_1_OPPOSE, edge

        return ConflictType.TYPE_6_OVERLAP, None  # 无匹配 → 新认知

    CONFLICT_CLASSIFY_PROMPT = """判断两条关于{dimension}的认知之间的关系类型。

旧认知: {old_content}
新认知: {new_content}

分类:
1. type_1_oppose (直接对立): 同一维度结论相反, 不能同时为真。如VOC风险低vs高。
2. type_2_supersede (时间覆盖): 新信息是旧信息的更新版本, 旧信息已过时。如排放标准更新。
3. type_3_refine (范围细化): 新信息加了条件限定, 缩小旧信息范围。如"化工项目有地下水风险"→"精细化工项目地下水风险更高"。
4. type_4_source_conflict (来源冲突): 企业自报数据vs监测数据不一致。
5. type_5_affective (风险波动): 同一项目/污染物在不同阶段风险等级交替变化。
6. type_6_overlap (语义重叠): 两条说的是同一件事, 表述不同。

输出严格 JSON (仅此):
{{"type": "type_X_XXX", "reason": "一句话理由"}}"""

    # ═══════════════════════════════════════════════════════════
    # 私有: 更新操作
    # ═══════════════════════════════════════════════════════════

    async def _create_new_edge(
        self, student_id: str, candidate: dict
    ) -> None:
        now = datetime.now()
        relation = candidate.get("relation_type", "")
        target_label = get_dimension_target_type(relation)
        props = {
            "confidence": 0.70,
            "C_peak": 0.70,
            "C_trough": 0.70,
            "source": "reflection",
            "verified_count": 1,
            "streak_count": 1,
            "streak_direction": "support",
            "content": candidate.get("content", ""),
            "created_at": now,
            "updated_at": now,
        }
        # 可选: 维度通用属性 (仅非空时写入)
        trend = candidate.get("trend")
        if trend:
            props["trend"] = trend
        intensity = candidate.get("intensity")
        if intensity is not None:
            props["intensity"] = float(intensity)
        valence = candidate.get("valence")
        if valence:
            props["valence"] = valence

        await self._neo4j.create_l2_edge(
            student_id, relation, candidate["target"], target_label, props
        )

    async def _update_bayesian_oppose(
        self, student_id: str, candidate: dict, existing: list[dict]
    ) -> None:
        """类型一: 三因子贝叶斯对抗更新"""
        relation = candidate.get("relation_type", "")
        target = candidate.get("target", "")

        edge = next(
            (e for e in existing
             if e.get("relation_type") == relation and e.get("target_name") == target),
            None,
        )
        if not edge:
            return

        C_old = edge.get("confidence", 0.70)
        quality = 0.70  # C 级 Reflection

        # resistance
        resistance = min((C_old - 0.35) / 0.65, 0.85)
        resistance = max(resistance, 0.0)

        # streak (如果是同方向继续)
        streak_count = edge.get("streak_count", 1)
        prev_direction = edge.get("streak_direction", "support")
        if prev_direction == "oppose":
            streak_count += 1
        else:
            streak_count = 1  # 方向翻转, 重置

        streak_mult = min(1 + (streak_count - 1) * 0.35, 2.5)

        # Δ
        delta = quality * (-1) * 1.0 * C_old * (1 - resistance) * streak_mult
        C_new = max(C_old + delta, 0.01)

        await self._neo4j.update_l2_edge(
            student_id, relation, target,
            {
                "confidence": C_new,
                "C_trough": min(C_new, edge.get("C_trough", C_old)),
                "last_oppose_time": datetime.now(),
                "streak_count": streak_count,
                "streak_direction": "oppose",
                "updated_at": datetime.now(),
            },
        )

    async def _handle_supersede(
        self, student_id: str, candidate: dict
    ) -> None:
        """类型二: 时间覆盖"""
        await self._create_new_edge(student_id, candidate)

    async def _handle_refine(
        self, student_id: str, candidate: dict
    ) -> None:
        """类型三: 范围细化 (微降旧, 升新)"""
        await self._create_new_edge(student_id, candidate)

    async def _handle_overlap(
        self, student_id: str, candidate: dict
    ) -> None:
        """类型六: 语义重叠, 不创建新边, 仅提升置信度"""
        relation = candidate.get("relation_type", "")
        target = candidate.get("target", "")
        await self._neo4j.update_l2_edge(
            student_id, relation, target,
            {
                "confidence": 0.75,  # min(max+0.05)
                "verified_count": 2,
                "updated_at": datetime.now(),
            },
        )
