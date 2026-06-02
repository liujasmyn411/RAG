"""管理员服务 — 审计 / 账号管控 / 知识库 / 系统配置"""

import json
from datetime import datetime
from typing import Optional

from app.domain.enums import AccountStatus
from app.repositories.pg_repo import PgRepo
from app.repositories.milvus_repo import MilvusRepo
from app.repositories.neo4j_repo import Neo4jRepo


class AdminService:
    """管理员功能服务"""

    def __init__(
        self,
        pg_repo: PgRepo,
        milvus_repo: MilvusRepo,
        neo4j_repo: Neo4jRepo,
    ) -> None:
        self._pg = pg_repo
        self._milvus = milvus_repo
        self._neo4j = neo4j_repo

    # ═══════════════════════════════════════════════════════════
    # L3-Cold 原文审计
    # ═══════════════════════════════════════════════════════════

    async def audit_l3_raw(
        self, student_id: str, admin_id: str, days: int = 30
    ) -> list[dict]:
        """查看学生 L3-Cold 原始对话 (仅管理员)"""
        # 从 L3-Hot 找到最近的 cold_ref
        l3_list = await self._milvus.pull_unprocessed(student_id, limit=50)
        cold_ids = list(set(
            l.get("cold_ref") for l in l3_list if l.get("cold_ref")
        ))

        results = []
        for cid in cold_ids[:10]:
            data = await self._pg.get_l3_cold(cid)
            if data:
                results.append({
                    "cold_id": cid,
                    "created_at": str(data.get("created_at", "")),
                    "raw_dialogue": json.loads(data.get("raw_dialogue", "[]")),
                })

        # 写入审计日志
        await self._pg.insert_admin_audit_log(admin_id, {
            "type": "audit_l3",
            "target_type": "student",
            "target_id": student_id,
            "detail": {"days": days, "records_viewed": len(results)},
        })

        return results

    # ═══════════════════════════════════════════════════════════
    # 账号管控
    # ═══════════════════════════════════════════════════════════

    async def account_control(
        self, student_id: str, action: str, reason: str, admin_id: str
    ) -> dict:
        """账号管控: unblock | reset_violation | force_logout | delete"""
        if action == "unblock":
            await self._pg.update_safety_status(
                student_id,
                safety_status="normal",
                account_status=AccountStatus.NORMAL.value,
            )
        elif action == "reset_violation":
            await self._pg.update_safety_status(
                student_id,
                safety_status="normal",
                b1_count=0,
                b2_count=0,
                account_status=AccountStatus.NORMAL.value,
            )
        elif action == "delete":
            await self._pg.update_safety_status(
                student_id,
                safety_status="deleted",
                account_status=AccountStatus.BLOCKED.value,
            )

        await self._pg.insert_admin_audit_log(admin_id, {
            "type": "account_control",
            "target_type": "student",
            "target_id": student_id,
            "detail": {"action": action, "reason": reason},
        })

        return {"status": "success", "action": action, "student_id": student_id}

    # ═══════════════════════════════════════════════════════════
    # 知识库管理 (L0)
    # ═══════════════════════════════════════════════════════════

    async def knowledge_manage(
        self, action: str, data: dict, admin_id: str
    ) -> dict:
        """管理红楼梦知识库: add_scene | edit_scene | delete_scene | add_character"""
        await self._pg.insert_admin_audit_log(admin_id, {
            "type": "knowledge_manage",
            "target_type": "l0_knowledge",
            "target_id": data.get("scene_id", data.get("character_id", "")),
            "detail": {"action": action, "data": data},
        })
        # 具体操作转给 Neo4j / Milvus
        return {"status": "success", "action": action}

    # ═══════════════════════════════════════════════════════════
    # 安全日志查询
    # ═══════════════════════════════════════════════════════════

    async def get_security_logs(
        self, student_id: str, category: Optional[str] = None, days: int = 30
    ) -> list[dict]:
        return await self._pg.get_security_logs(student_id, category, days)
