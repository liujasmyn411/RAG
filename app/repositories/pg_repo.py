"""PostgreSQL DAO — 关系数据库增删改查"""

import json
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.memory import SessionArchive
from app.domain.entities.student import StudentProfile
from app.domain.entities.safety import SafetyEvent


class PgRepo:
    """PostgreSQL 数据访问"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ═══════════════════════════════════════════════════════════
    # L1: 业务数据 (只读)
    # ═══════════════════════════════════════════════════════════

    async def get_student_scores(
        self, student_id: str, subject: Optional[str] = None, days: int = 90
    ) -> list[dict]:
        result = await self._session.execute(
            text(
                """SELECT subject, score, exam_date, rank_total, rank_class
                   FROM scores WHERE student_id = :sid
                   AND exam_date >= :since ORDER BY exam_date DESC"""
            ),
            {"sid": student_id, "since": datetime.now() - timedelta(days=days)},
        )
        return [dict(row._mapping) for row in result]

    async def get_student_attendance(
        self, student_id: str, days: int = 30
    ) -> list[dict]:
        result = await self._session.execute(
            text(
                """SELECT date, status, reason
                   FROM attendance WHERE student_id = :sid
                   AND date >= :since ORDER BY date DESC"""
            ),
            {"sid": student_id, "since": datetime.now() - timedelta(days=days)},
        )
        return [dict(row._mapping) for row in result]

    async def get_student_info(self, student_id: str) -> Optional[dict]:
        result = await self._session.execute(
            text("SELECT * FROM students WHERE student_id = :sid"),
            {"sid": student_id},
        )
        row = result.first()
        return dict(row._mapping) if row else None

    # ═══════════════════════════════════════════════════════════
    # L3-Cold: 原始对话
    # ═══════════════════════════════════════════════════════════

    async def insert_l3_cold(
        self,
        student_id: str,
        session_id: str,
        raw_dialogue: list[dict],
        crisis_flag: bool = False,
        importance: float = 0.5,
    ) -> str:
        cold_id = f"pg_l3_raw_{datetime.now().strftime('%Y%m%d')}_{student_id}_{session_id}"
        await self._session.execute(
            text(
                """INSERT INTO l3_cold
                   (cold_id, student_id, session_id, raw_dialogue,
                    crisis_flag, importance, created_at)
                   VALUES (:cid, :sid, :sess, :raw, :crisis, :imp, :now)"""
            ),
            {
                "cid": cold_id,
                "sid": student_id,
                "sess": session_id,
                "raw": json.dumps(raw_dialogue),
                "crisis": crisis_flag,
                "imp": importance,
                "now": datetime.now(),
            },
        )
        return cold_id

    async def mark_cold_reprocess(self, cold_id: str) -> None:
        """标记 Cold 待重试 — L3-Hot Level 3 提取失败时调用"""
        await self._session.execute(
            text("UPDATE l3_cold SET need_reprocess = TRUE WHERE cold_id = :cid"),
            {"cid": cold_id},
        )

    async def get_l3_cold(self, cold_id: str) -> Optional[dict]:
        result = await self._session.execute(
            text("SELECT * FROM l3_cold WHERE cold_id = :cid"),
            {"cid": cold_id},
        )
        row = result.first()
        return dict(row._mapping) if row else None

    async def move_cold_to_warm(self, warm_days: int = 30) -> int:
        """将超过 warm_days 天的 hot 记录移入温归档 (archive_status: hot→warm)"""
        since = datetime.now() - timedelta(days=warm_days)
        result = await self._session.execute(
            text(
                """UPDATE l3_cold SET archive_status = 'warm'
                   WHERE archive_status = 'hot'
                   AND created_at < :since
                   AND crisis_flag = false"""
            ),
            {"since": since},
        )
        return result.rowcount

    async def expire_cold_archive(
        self,
        normal_days: int = 90,
        high_imp_days: int = 180,
    ) -> int:
        """删除过期 Cold warm 记录，返回删除数。
        普通对话 (importance < 0.7): warm 后 90 天删除
        高重要性 (importance ≥ 0.7): warm 后 180 天删除
        危机 (crisis_flag = true): 永久保留，不进入此流程
        """
        since_normal = datetime.now() - timedelta(days=normal_days)
        since_high = datetime.now() - timedelta(days=high_imp_days)

        result = await self._session.execute(
            text(
                """DELETE FROM l3_cold
                   WHERE archive_status = 'warm'
                   AND crisis_flag = false
                   AND (
                       (importance < 0.7 AND created_at < :normal)
                       OR
                       (importance >= 0.7 AND created_at < :high)
                   )"""
            ),
            {"normal": since_normal, "high": since_high},
        )
        return result.rowcount

    # ═══════════════════════════════════════════════════════════
    # Episode: 情景记忆容器
    # ═══════════════════════════════════════════════════════════

    async def get_active_episode(self, student_id: str) -> Optional[dict]:
        """获取学生当前活跃的 Episode（未关闭的最新一条）"""
        result = await self._session.execute(
            text(
                """SELECT * FROM episodes
                   WHERE student_id = :sid AND is_closed = FALSE
                   ORDER BY started_at DESC LIMIT 1"""
            ),
            {"sid": student_id},
        )
        row = result.first()
        return dict(row._mapping) if row else None

    async def upsert_episode(
        self,
        episode_id: str,
        student_id: str,
        session_id: str,
        topic: str,
        boundary_trigger: str = "first_episode",
    ) -> None:
        """创建新 Episode 或增加已有 Episode 的 l3_count"""
        await self._session.execute(
            text(
                """INSERT INTO episodes
                   (episode_id, student_id, session_id, topic, started_at,
                    boundary_trigger)
                   VALUES (:eid, :sid, :sess, :topic, NOW(), :trigger)
                   ON DUPLICATE KEY UPDATE l3_count = l3_count + 1"""
            ),
            {
                "eid": episode_id,
                "sid": student_id,
                "sess": session_id,
                "topic": topic,
                "trigger": boundary_trigger,
            },
        )

    async def close_episode(self, episode_id: str) -> None:
        """关闭 Episode"""
        await self._session.execute(
            text(
                """UPDATE episodes SET is_closed = TRUE, ended_at = NOW()
                   WHERE episode_id = :eid"""
            ),
            {"eid": episode_id},
        )

    # ═══════════════════════════════════════════════════════════
    # 会话归档
    # ═══════════════════════════════════════════════════════════

    async def upsert_session_archive(self, archive: SessionArchive) -> None:
        await self._session.execute(
            text(
                """INSERT INTO session_archive
                   (session_id, student_id, closed_at, close_reason, summary,
                    safety_snapshot, last_intent, last_topic, unclosed_topic,
                    message_count)
                   VALUES (:sid, :stid, :closed, :reason, :summary,
                           :safety, :intent, :topic, :utopic, :cnt)
                   ON DUPLICATE KEY UPDATE
                    summary=VALUES(summary), safety_snapshot=VALUES(safety_snapshot),
                    unclosed_topic=VALUES(unclosed_topic)"""
            ),
            {
                "sid": archive.session_id,
                "stid": archive.student_id,
                "closed": archive.closed_at,
                "reason": archive.close_reason.value,
                "summary": archive.summary,
                "safety": json.dumps(archive.safety_snapshot),
                "intent": archive.last_intent,
                "topic": archive.last_topic,
                "utopic": archive.unclosed_topic,
                "cnt": archive.message_count,
            },
        )

    async def get_latest_archive(self, student_id: str) -> Optional[dict]:
        result = await self._session.execute(
            text(
                """SELECT * FROM session_archive
                   WHERE student_id = :sid
                   ORDER BY closed_at DESC LIMIT 1"""
            ),
            {"sid": student_id},
        )
        row = result.first()
        return dict(row._mapping) if row else None

    # ═══════════════════════════════════════════════════════════
    # 学生档案
    # ═══════════════════════════════════════════════════════════

    async def upsert_student_profile(self, profile: StudentProfile) -> None:
        await self._session.execute(
            text(
                """INSERT INTO student_profile
                   (student_id, rolling_summary, total_sessions, total_messages,
                    first_interaction_at, last_interaction_at, safety_status,
                    violation_b1_count, violation_b2_count, account_status)
                   VALUES (:sid, :summary, :ts, :tm, :first, :last, :safety,
                           :b1, :b2, :status)
                   ON DUPLICATE KEY UPDATE
                    rolling_summary=VALUES(rolling_summary),
                    total_sessions=VALUES(total_sessions),
                    total_messages=VALUES(total_messages),
                    last_interaction_at=VALUES(last_interaction_at),
                    safety_status=VALUES(safety_status),
                    violation_b1_count=VALUES(violation_b1_count),
                    violation_b2_count=VALUES(violation_b2_count),
                    account_status=VALUES(account_status)"""
            ),
            {
                "sid": profile.student_id,
                "summary": profile.rolling_summary,
                "ts": profile.total_sessions,
                "tm": profile.total_messages,
                "first": profile.first_interaction_at,
                "last": profile.last_interaction_at,
                "safety": profile.safety_status,
                "b1": profile.violation_b1_count,
                "b2": profile.violation_b2_count,
                "status": profile.account_status.value,
            },
        )

    async def get_student_profile(self, student_id: str) -> Optional[dict]:
        result = await self._session.execute(
            text("SELECT * FROM student_profile WHERE student_id = :sid"),
            {"sid": student_id},
        )
        row = result.first()
        return dict(row._mapping) if row else None

    # ═══════════════════════════════════════════════════════════
    # 草稿区: L2 候选认知
    # ═══════════════════════════════════════════════════════════

    async def insert_draft_candidate(
        self,
        student_id: str,
        trait_name: str,
        trait_value: str = "",
        source_type: str = "llm_infer",
        write_confidence: float = 0.5,
        evidence_l3_ids: Optional[list[str]] = None,
    ) -> str:
        draft_id = f"draft_{student_id}_{trait_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        await self._session.execute(
            text(
                """INSERT INTO l2_draft_candidates
                   (draft_id, student_id, trait_name, trait_value,
                    source_type, write_confidence, evidence_l3_ids)
                   VALUES (:did, :sid, :name, :val, :src, :conf, :ev)"""
            ),
            {
                "did": draft_id,
                "sid": student_id,
                "name": trait_name,
                "val": trait_value,
                "src": source_type,
                "conf": write_confidence,
                "ev": json.dumps(evidence_l3_ids or []),
            },
        )
        return draft_id

    async def get_draft_candidates(
        self, student_id: str, min_confidence: float = 0.5, limit: int = 20
    ) -> list[dict]:
        """获取未消费的草稿候选 (0.5 ≤ conf < 0.7, 仅 Reflection 可见)"""
        result = await self._session.execute(
            text(
                """SELECT * FROM l2_draft_candidates
                   WHERE student_id = :sid
                   AND consumed = false
                   AND write_confidence >= :min
                   AND write_confidence < 0.7
                   ORDER BY write_confidence DESC LIMIT :lim"""
            ),
            {"sid": student_id, "min": min_confidence, "lim": limit},
        )
        return [dict(row._mapping) for row in result]

    async def consume_draft(self, draft_id: str) -> None:
        """标记草稿为已消费 (Reflection 处理完后)"""
        await self._session.execute(
            text(
                "UPDATE l2_draft_candidates SET consumed = true WHERE draft_id = :did"
            ),
            {"did": draft_id},
        )

    async def purge_stale_drafts(self, retention_days: int = 60) -> int:
        """清理过期草稿"""
        since = datetime.now() - timedelta(days=retention_days)
        result = await self._session.execute(
            text(
                """DELETE FROM l2_draft_candidates
                   WHERE drafted_at < :since AND consumed = true"""
            ),
            {"since": since},
        )
        return result.rowcount

    async def update_safety_status(
        self,
        student_id: str,
        safety_status: str,
        b1_count: Optional[int] = None,
        b2_count: Optional[int] = None,
        b2_window_start: Optional[datetime] = None,
        b2_last_decay: Optional[datetime] = None,
        account_status: Optional[str] = None,
    ) -> None:
        sets = ["safety_status = :safety", "updated_at = :now"]
        params: dict = {"sid": student_id, "safety": safety_status, "now": datetime.now()}
        if b1_count is not None:
            sets.append("violation_b1_count = :b1")
            params["b1"] = b1_count
        if b2_count is not None:
            sets.append("violation_b2_count = :b2")
            params["b2"] = b2_count
        if b2_window_start is not None:
            sets.append("b2_window_start = :b2ws")
            params["b2ws"] = b2_window_start
        if b2_last_decay is not None:
            sets.append("b2_last_decay_time = :b2ld")
            params["b2ld"] = b2_last_decay
        if account_status is not None:
            sets.append("account_status = :status")
            params["status"] = account_status
        await self._session.execute(
            text(f"UPDATE student_profile SET {', '.join(sets)} WHERE student_id = :sid"),
            params,
        )

    # ═══════════════════════════════════════════════════════════
    # 安全日志
    # ═══════════════════════════════════════════════════════════

    async def insert_security_log(self, event: SafetyEvent) -> None:
        await self._session.execute(
            text(
                """INSERT INTO security_log
                   (student_id, teacher_id, category, risk_level, trigger_type,
                    escalation, original_message_hash, anonymized_summary,
                    new_user_status, created_at)
                   VALUES (:sid, :tid, :cat, :level, :trigger, :esc,
                           :hash, :summary, :status, :now)"""
            ),
            {
                "sid": event.student_id,
                "tid": event.teacher_id,
                "cat": event.category.value,
                "level": event.risk_level,
                "trigger": event.trigger_type,
                "esc": event.escalation.value,
                "hash": event.original_message_hash,
                "summary": event.anonymized_summary,
                "status": event.new_user_status,
                "now": datetime.now(),
            },
        )

    async def get_security_logs(
        self,
        student_id: str,
        category: Optional[str] = None,
        days: int = 30,
    ) -> list[dict]:
        extra = " AND category = :cat" if category else ""
        result = await self._session.execute(
            text(
                f"""SELECT * FROM security_log
                    WHERE student_id = :sid
                    AND created_at >= :since{extra}
                    ORDER BY created_at DESC"""
            ),
            {"sid": student_id, "since": datetime.now() - timedelta(days=days),
             **({"cat": category} if category else {})},
        )
        return [dict(row._mapping) for row in result]

    # ═══════════════════════════════════════════════════════════
    # 危机通知
    # ═══════════════════════════════════════════════════════════

    async def insert_crisis_alert(self, alert) -> int:
        result = await self._session.execute(
            text(
                """INSERT INTO crisis_alerts
                   (student_id, teacher_id, severity, summary, status, triggered_at)
                   VALUES (:sid, :tid, :sev, :sum, :status, :now)"""
            ),
            {
                "sid": alert.student_id,
                "tid": alert.teacher_id,
                "sev": alert.severity.value,
                "sum": alert.summary,
                "status": alert.status.value,
                "now": datetime.now(),
            },
        )
        return result.lastrowid

    async def get_pending_alerts(self, teacher_id: str) -> list[dict]:
        result = await self._session.execute(
            text(
                """SELECT * FROM crisis_alerts
                   WHERE teacher_id = :tid
                   AND status IN ('pending','escalated')
                   ORDER BY triggered_at DESC"""
            ),
            {"tid": teacher_id},
        )
        return [dict(row._mapping) for row in result]

    async def confirm_alert(
        self, alert_id: int, user_id: str, resolution: str
    ) -> None:
        await self._session.execute(
            text(
                """UPDATE crisis_alerts
                   SET status='confirmed', confirmed_at=:now,
                       confirmed_by=:uid, resolution=:res
                   WHERE id=:id"""
            ),
            {"id": alert_id, "now": datetime.now(),
             "uid": user_id, "res": resolution},
        )

    async def escalate_overdue_alerts(self, timeout_minutes: int = 30) -> int:
        result = await self._session.execute(
            text(
                """UPDATE crisis_alerts
                   SET status='escalated', escalated_at=NOW()
                   WHERE status='pending'
                   AND triggered_at < DATE_SUB(NOW(), INTERVAL :t MINUTE)"""
            ),
            {"t": timeout_minutes},
        )
        return result.rowcount

    # ═══════════════════════════════════════════════════════════
    # 管理员审计
    # ═══════════════════════════════════════════════════════════

    async def insert_admin_audit_log(self, admin_id: str, action: dict) -> None:
        await self._session.execute(
            text(
                """INSERT INTO admin_audit_log
                   (admin_id, action_type, target_type, target_id, action_detail)
                   VALUES (:aid, :atype, :ttype, :tid, :detail)"""
            ),
            {
                "aid": admin_id,
                "atype": action.get("type", ""),
                "ttype": action.get("target_type", ""),
                "tid": action.get("target_id", ""),
                "detail": json.dumps(action.get("detail", {})),
            },
        )
