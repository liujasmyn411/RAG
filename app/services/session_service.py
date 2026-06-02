"""会话管理服务 — 边界检测 + 归档 + State 初始化"""

from datetime import datetime, timedelta
from typing import Optional

from app.domain.enums import (
    Intent,
    CarryOverLevel,
    SessionStatus,
    CloseReason,
)
from app.domain.entities.memory import SessionArchive
from app.domain.entities.student import StudentProfile
from app.infrastructure.embedding import get_embedding_service
from app.infrastructure.llm_client import get_llm_client
from app.repositories.pg_repo import PgRepo
from app.repositories.neo4j_repo import Neo4jRepo

# ── 结束信号关键词 ──
EXPLICIT_END_SIGNALS = ["再见", "拜拜", "明天见", "下次聊", "我先去", "晚点", "下了", "我走了"]
CONTINUE_SIGNALS = ["接着说", "刚才说到", "继续", "对了还有"]


class SessionService:
    """会话生命周期管理"""

    def __init__(self, pg_repo: PgRepo, neo4j_repo: Neo4jRepo) -> None:
        self._pg = pg_repo
        self._neo4j = neo4j_repo
        self._embed = get_embedding_service()
        self._llm = get_llm_client()

    # ═══════════════════════════════════════════════════════════
    # 会话边界判断: 多信号融合
    # ═══════════════════════════════════════════════════════════

    async def boundary_detect(
        self,
        student_id: str,
        message: str,
        current_intent: Intent,
        user_role: str,
        last_active_time: Optional[datetime] = None,
    ) -> dict:
        """多信号融合: T(时间) / S(语义) / U(用户信号) / I(Intent)"""

        # Rule 0: 教师/管理员 → 默认 partial
        if user_role != "student":
            return {
                "is_new_session": True,
                "carry_over_level": CarryOverLevel.PARTIAL,
                "time_gap_minutes": 0,
                "semantic_continuity": 0,
            }

        # Rule 1: 危机强制续接
        if current_intent == Intent.PSYCH_CRISIS:
            return {
                "is_new_session": False,
                "carry_over_level": CarryOverLevel.FULL,
                "time_gap_minutes": 0,
                "semantic_continuity": 1.0,
            }

        if last_active_time is None:
            return {"is_new_session": True, "carry_over_level": CarryOverLevel.MINIMAL}

        # T: 时间间隔
        time_gap = (datetime.now() - last_active_time).total_seconds() / 60

        # U: 用户信号
        user_signal = self._detect_user_signal(message)

        # Rule 2: 显式结束信号 + >5 分钟 → 新会话
        if user_signal == "end" and time_gap > 5:
            return {
                "is_new_session": True,
                "carry_over_level": CarryOverLevel.PARTIAL,
                "time_gap_minutes": time_gap,
                "semantic_continuity": 0,
                "user_signal": user_signal,
            }

        # Rule 5: 长间隔 > 2 小时 → 新会话
        if time_gap > 120:
            return {
                "is_new_session": True,
                "carry_over_level": CarryOverLevel.PARTIAL,
                "time_gap_minutes": time_gap,
                "semantic_continuity": 0,
                "user_signal": user_signal,
            }

        # S: 语义连续性 — embedding 余弦相似度
        import numpy as np
        archive = await self._pg.get_latest_archive(student_id)
        semantic_cont = 0.5  # 无归档数据时默认中性
        if archive and archive.get("summary"):
            try:
                arch_vec = self._embed.encode_array(archive["summary"])
                curr_vec = self._embed.encode_array(message)
                cos_sim = np.dot(arch_vec, curr_vec) / (
                    np.linalg.norm(arch_vec) * np.linalg.norm(curr_vec)
                )
                semantic_cont = float(cos_sim)
            except Exception:
                pass  # 兜底 0.5

        # Rule 3: 续接信号 → 续接
        if user_signal == "continue":
            return {
                "is_new_session": False,
                "carry_over_level": CarryOverLevel.FULL,
                "time_gap_minutes": time_gap,
                "semantic_continuity": semantic_cont,
                "user_signal": user_signal,
            }

        # Rule 4: 短间隔 + 高连续 → 续接
        if time_gap < 30:
            return {
                "is_new_session": False,
                "carry_over_level": CarryOverLevel.FULL,
                "time_gap_minutes": time_gap,
                "semantic_continuity": semantic_cont,
            }

        # Rule 6: 兜底
        return {
            "is_new_session": True,
            "carry_over_level": CarryOverLevel.PARTIAL,
            "time_gap_minutes": time_gap,
            "semantic_continuity": semantic_cont,
        }

    # ═══════════════════════════════════════════════════════════
    # 会话归档
    # ═══════════════════════════════════════════════════════════

    async def archive_session(
        self,
        session_id: str,
        student_id: str,
        messages: list,
        close_reason: CloseReason,
        safety_snapshot: dict,
        last_intent: str,
        last_topic: str,
        message_count: int,
    ) -> SessionArchive:
        # 生成摘要
        summary = await self._generate_summary(messages)

        archive = SessionArchive(
            session_id=session_id,
            student_id=student_id,
            closed_at=datetime.now(),
            close_reason=close_reason,
            summary=summary,
            safety_snapshot=safety_snapshot,
            last_intent=last_intent,
            last_topic=last_topic,
            message_count=message_count,
        )
        await self._pg.upsert_session_archive(archive)

        # 更新 rolling_summary
        profile_data = await self._pg.get_student_profile(student_id)
        if profile_data:
            new_summary = await self._merge_rolling_summary(
                profile_data.get("rolling_summary", ""), summary
            )
            await self._pg.upsert_student_profile(
                StudentProfile(
                    student_id=student_id,
                    rolling_summary=new_summary,
                    total_sessions=profile_data.get("total_sessions", 0) + 1,
                    total_messages=profile_data.get("total_messages", 0) + message_count,
                    last_interaction_at=datetime.now(),
                )
            )

        return archive

    # ═══════════════════════════════════════════════════════════
    # State 初始化
    # ═══════════════════════════════════════════════════════════

    async def init_state_messages(
        self,
        student_id: str,
        carry_over: CarryOverLevel,
        persona_prompt: str,
    ) -> list:
        """按 carry_over_level 构建初始 messages"""
        messages = [{"role": "system", "content": persona_prompt}]

        archive = await self._pg.get_latest_archive(student_id)
        profile = await self._pg.get_student_profile(student_id)

        if carry_over == CarryOverLevel.FULL:
            # 保留最后 10 轮 (从归档恢复, 此处仅注入摘要骨架)
            if archive:
                messages.append({
                    "role": "system",
                    "content": f"上次对话: {archive.get('summary', '')}",
                })

        elif carry_over == CarryOverLevel.PARTIAL:
            if archive:
                messages.append({
                    "role": "system",
                    "content": f"【上次对话摘要】{archive.get('summary', '')}",
                })

        elif carry_over == CarryOverLevel.MINIMAL:
            parts = []
            if profile:
                parts.append(
                    f"学生档案: 互动{profile.get('total_sessions', 0)}次, "
                    f"{profile.get('rolling_summary', '')}"
                )
            # 关心关系强度
            care = await self._neo4j.get_care_strength(student_id)
            if care:
                days = 0
                if care.get("last_interaction"):
                    delta = datetime.now() - care["last_interaction"]
                    days = delta.days
                strength = care.get("strength", 1.0)
                if days > 0:
                    parts.append(
                        f"关系提示: 距上次互动已有{days}天, 关系略有疏远"
                    )
            if parts:
                messages.append({
                    "role": "system",
                    "content": "【学生档案】" + "。".join(parts),
                })

        return messages

    # ── 私有方法 ──

    def _detect_user_signal(self, message: str) -> Optional[str]:
        for sig in CONTINUE_SIGNALS:
            if sig in message:
                return "continue"
        for sig in EXPLICIT_END_SIGNALS:
            if sig in message:
                return "end"
        return None

    async def _generate_summary(self, messages: list) -> str:
        if len(messages) < 4:
            return ""
        recent = messages[-20:]
        text = "\n".join(
            m.get("content", "") if isinstance(m, dict) else str(m)
            for m in recent
        )
        try:
            result = await self._llm.chat([
                {"role": "system", "content": "将以下对话压缩为一段摘要, 不超过300字, 保留: 1.主要话题 2.学生情绪变化 3.未解决问题或约定。"},
                {"role": "user", "content": text},
            ])
            return result.strip()
        except Exception:
            return ""

    async def _merge_rolling_summary(
        self, old_summary: str, new_summary: str
    ) -> str:
        if not old_summary:
            return new_summary
        try:
            result = await self._llm.chat([
                {"role": "system", "content": "将两段学生互动摘要合并为一段, 保留稳定认知, 淘汰过时信息, 不超过300字。"},
                {"role": "user", "content": f"旧摘要: {old_summary}\n新摘要: {new_summary}"},
            ])
            return result.strip()
        except Exception:
            return new_summary or old_summary
