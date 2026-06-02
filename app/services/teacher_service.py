"""教师查询服务 — 学生画像 / 班级聚合 / 危机预警"""

from datetime import datetime, timedelta
from typing import Optional

from app.domain.schemas import StudentProfileReport, ClassAggregateReport
from app.infrastructure.llm_client import get_llm_client
from app.repositories.neo4j_repo import Neo4jRepo
from app.repositories.pg_repo import PgRepo

REPORT_PROMPT = """你是一个学生心理分析助手。根据以下数据生成学生心理状态报告。

格式要求:
1. 学业概况: 各科成绩趋势, 偏科情况
2. 情绪状态: 情绪基线, 近期变化, 焦虑程度
3. 社交情况: 同伴关系, 课堂参与
4. 风险提示: 危机历史, 违规记录
5. 建议: 针对性的关注建议

输出专业、客观、简洁, 不超过500字。"""

CLASS_AGGREGATE_PROMPT = """你是一个学生心理分析助手。根据以下班级聚合数据生成班级心理健康报告。

要求: 匿名, 不暴露任何单个学生。分析趋势和建议。不超过400字。"""


class TeacherService:
    """教师查询服务"""

    def __init__(self, neo4j_repo: Neo4jRepo, pg_repo: PgRepo) -> None:
        self._neo4j = neo4j_repo
        self._pg = pg_repo
        self._llm = get_llm_client()

    async def student_profile_report(self, student_id: str) -> StudentProfileReport:
        """生成单个学生画像报告"""
        # 收集数据
        info = await self._pg.get_student_info(student_id)
        scores = await self._pg.get_student_scores(student_id, days=90)
        traits = await self._neo4j.get_student_traits(student_id)
        profile = await self._pg.get_student_profile(student_id)
        care = await self._neo4j.get_care_strength(student_id)

        # 组装上下文
        context = self._assemble_student_context(info, scores, traits, profile, care)

        # LLM 生成报告
        report_text = await self._llm.chat([
            {"role": "system", "content": REPORT_PROMPT},
            {"role": "user", "content": context},
        ])

        return StudentProfileReport(
            student_id=student_id,
            name=info.get("name", "") if info else "",
            class_name=info.get("class_name", "") if info else "",
            report_text=report_text,
        )

    async def class_aggregate(self, class_name: str) -> ClassAggregateReport:
        """班级群体聚合报告 (匿名)"""
        # 聚合 L2 情绪分布
        # 注意: Neo4j 班级标签查询 Student:Class{name}
        # 此处为简化, 实际需要 Cypher 聚合
        report_text = await self._llm.chat([
            {"role": "system", "content": CLASS_AGGREGATE_PROMPT},
            {"role": "user", "content": f"班级: {class_name}\n请生成该班级的心理健康聚合报告。"},
        ])

        return ClassAggregateReport(
            class_name=class_name,
            student_count=0,  # 从查询获得
            report_text=report_text,
        )

    async def crisis_alerts(self, teacher_id: str) -> list[dict]:
        """待处理危机预警列表"""
        # 查询 security_log 中最近 7 天、未确认的危机
        # 简化实现
        return []

    def _assemble_student_context(
        self,
        info: Optional[dict],
        scores: list[dict],
        traits: list[dict],
        profile: Optional[dict],
        care: Optional[dict],
    ) -> str:
        parts = []
        if info:
            parts.append(f"学生: {info.get('name','')}, 班级: {info.get('class_name','')}")
        if scores:
            score_lines = [
                f"  {s.get('subject','')}: {s.get('score','')}分 ({s.get('exam_date','')})"
                for s in scores[:10]
            ]
            parts.append("成绩:\n" + "\n".join(score_lines))
        if traits:
            trait_lines = [
                f"  {t.get('relation_type','')}→{t.get('target_name','')} (置信度:{t.get('confidence',0):.2f})"
                for t in traits
            ]
            parts.append("认知特征:\n" + "\n".join(trait_lines))
        if profile:
            parts.append(
                f"互动统计: 共{profile.get('total_sessions',0)}次会话, "
                f"安全状态: {profile.get('safety_status','normal')}, "
                f"B1违规: {profile.get('violation_b1_count',0)}, "
                f"B2违规: {profile.get('violation_b2_count',0)}"
            )
        if care:
            parts.append(
                f"互动频率: {care.get('interaction_count',0)}次, "
                f"当前关系强度: {care.get('strength',1.0):.2f}"
            )
        return "\n\n".join(parts)
