"""SQL 安全守卫 — 四层校验: 语法解析 → 白名单 → 权限注入 → 安全执行"""

from dataclasses import dataclass, field
from typing import Optional

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError


# ═══════════════════════════════════════════════════════════
# 白名单: 表名 → 允许的列名
# ═══════════════════════════════════════════════════════════

ALLOWED_TABLES: dict[str, list[str]] = {
    "students": [
        "student_id", "name", "class_name", "age", "gender",
        "hometown", "graduated_school", "major", "education",
        "enrollment_date", "graduation_date", "advisor_id",
        "is_deleted", "created_at", "updated_at",
    ],
    "scores": [
        "id", "student_id", "exam_sequence", "score",
        "exam_date", "exam_type", "subject", "rank_total", "rank_class",
        "created_at",
    ],
    "employment": [
        "id", "student_id", "name", "class_name",
        "employment_open_time", "offer_time", "company_name", "salary",
        "created_at", "updated_at",
    ],
    "classes": [
        "class_name", "grade", "teacher_id", "head_teacher", "instructor",
        "start_time", "created_at",
    ],
    "teachers": [
        "teacher_id", "name", "department", "title", "phone",
        "created_at",
    ],
}

# 允许的 JOIN 条件（表A.列 = 表B.列）
JOIN_RELATIONS = {
    ("students", "scores"): ("student_id", "student_id"),
    ("students", "employment"): ("student_id", "student_id"),
    ("students", "classes"): ("class_name", "class_name"),
    ("students", "teachers"): ("advisor_id", "teacher_id"),
    ("scores", "students"): ("student_id", "student_id"),
    ("employment", "students"): ("student_id", "student_id"),
    ("classes", "students"): ("class_name", "class_name"),
    ("teachers", "students"): ("teacher_id", "advisor_id"),
}

FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE",
    "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "CALL",
    "LOAD", "INTO", "OUTFILE", "DUMPFILE",
]

MAX_ROWS = 1000
QUERY_TIMEOUT_SECONDS = 5


# ═══════════════════════════════════════════════════════════
# 安全守卫
# ═══════════════════════════════════════════════════════════

@dataclass
class GuardResult:
    """安全校验结果"""
    passed: bool
    safe_sql: str = ""          # 经过安全处理后的 SQL
    error: str = ""             # 校验失败的原因
    tables_used: list[str] = field(default_factory=list)
    columns_used: list[str] = field(default_factory=list)


class SqlGuard:
    """SQL 四层安全守卫"""

    def __init__(
        self,
        user_role: str = "admin",
        current_user_id: str = "",
        managed_classes: Optional[list[str]] = None,
    ) -> None:
        self._user_role = user_role
        self._current_user_id = current_user_id
        self._managed_classes = managed_classes or []

    # ── Layer 1: 语法解析 + 危险操作检测 ──

    def validate_syntax(self, sql: str) -> GuardResult:
        """解析 SQL 并检测危险操作"""
        # 清理 SQL
        sql = self._clean_sql(sql)

        # 1a. 危险关键词检测 (比 AST 更可靠)
        upper_sql = sql.upper()
        for kw in FORBIDDEN_KEYWORDS:
            # 用词边界检测 (避免误判 SELECT 中的 DROP 子串等)
            import re
            if re.search(r'\b' + kw + r'\b', upper_sql):
                return GuardResult(
                    passed=False,
                    error=f"禁止的SQL操作: {kw}。仅允许 SELECT 查询。"
                )

        # 1b. sqlglot 解析
        try:
            parsed = sqlglot.parse_one(sql, dialect="mysql")
        except ParseError as e:
            return GuardResult(
                passed=False,
                error=f"SQL 语法错误: {e}"
            )

        # 1c. AST 中确保只有 SELECT
        if not isinstance(parsed, exp.Select):
            return GuardResult(
                passed=False,
                error=f"仅允许 SELECT 查询，检测到: {type(parsed).__name__}"
            )

        # 检查子查询中是否有写操作
        for node in parsed.walk():
            if isinstance(node, (exp.Delete, exp.Insert, exp.Update,
                                  exp.Drop, exp.Create, exp.Alter)):
                return GuardResult(
                    passed=False,
                    error=f"子查询中包含禁止操作: {type(node).__name__}"
                )

        return GuardResult(passed=True, safe_sql=sql)

    # ── Layer 2: 白名单校验 ──

    def validate_whitelist(self, sql: str) -> GuardResult:
        """校验 SQL 中引用的表和列都在白名单中"""
        parsed = sqlglot.parse_one(sql, dialect="mysql")

        tables_used: list[str] = []
        columns_used: list[str] = []

        # 提取所有表引用
        for node in parsed.walk():
            if isinstance(node, exp.Table):
                table_name = node.name
                # 去除可能的别名前缀
                if table_name not in ALLOWED_TABLES:
                    return GuardResult(
                        passed=False,
                        error=f"表 '{table_name}' 不在白名单中。允许的表: {list(ALLOWED_TABLES.keys())}"
                    )
                if table_name not in tables_used:
                    tables_used.append(table_name)

            # 提取所有列引用
            if isinstance(node, exp.Column):
                col_name = node.name
                table_alias = node.table  # 可能是表名或别名

                # 如果列有 table 前缀，校验该列是否在该表的白名单中
                if table_alias:
                    # 尝试匹配真实表名 (别名可能不同)
                    found_table = self._resolve_table(table_alias, tables_used)
                    if found_table and col_name != "*":
                        allowed_cols = ALLOWED_TABLES.get(found_table, [])
                        if col_name not in allowed_cols:
                            return GuardResult(
                                passed=False,
                                error=f"列 '{found_table}.{col_name}' 不在白名单中"
                            )

                # COUNT(*), SUM(*) 等聚合允许 *
                if col_name != "*" and col_name not in columns_used:
                    columns_used.append(col_name)

        return GuardResult(
            passed=True,
            safe_sql=sql,
            tables_used=tables_used,
            columns_used=columns_used,
        )

    # ── Layer 3: 权限 WHERE 注入 ──

    def inject_permission(self, sql: str, tables_used: list[str]) -> GuardResult:
        """根据用户角色自动注入权限过滤条件"""
        if self._user_role == "admin":
            return GuardResult(passed=True, safe_sql=sql)

        import re

        # 学生: 只能查自己的数据
        if self._user_role == "student":
            condition = f"students.student_id = '{self._current_user_id}'"
            # 如果查询涉及 students 表，注入过滤条件
            if "students" in tables_used:
                sql = self._inject_where(sql, condition)
            # 如果查询只涉及 scores/employment 但没有 JOIN students
            elif any(t in tables_used for t in ["scores", "employment"]):
                for t in ["scores", "employment"]:
                    if t in tables_used:
                        sql = self._inject_where(sql, f"{t}.student_id = '{self._current_user_id}'")

        # 教师: 只能查所管班级
        elif self._user_role == "teacher":
            if self._managed_classes:
                classes_str = ", ".join(f"'{c}'" for c in self._managed_classes)
                condition = f"students.class_name IN ({classes_str})"
                if "students" in tables_used:
                    sql = self._inject_where(sql, condition)

        return GuardResult(passed=True, safe_sql=sql)

    # ── Layer 4: 安全执行参数 ──

    def prepare_execution(self, sql: str) -> GuardResult:
        """为安全执行做准备: 追加 LIMIT、只读标记"""
        parsed = sqlglot.parse_one(sql, dialect="mysql")

        # 检查是否已有 LIMIT
        has_limit = any(isinstance(node, exp.Limit) for node in parsed.walk())

        # 自动追加 LIMIT
        if not has_limit:
            sql = sql.rstrip(";").rstrip() + f" LIMIT {MAX_ROWS}"

        return GuardResult(passed=True, safe_sql=sql)

    # ── 完整校验流程 ──

    def guard(self, sql: str) -> GuardResult:
        """执行完整的四层安全校验"""
        # Layer 1
        result = self.validate_syntax(sql)
        if not result.passed:
            return result

        # Layer 2
        result = self.validate_whitelist(result.safe_sql)
        if not result.passed:
            return result

        # Layer 3
        result = self.inject_permission(result.safe_sql, result.tables_used)
        if not result.passed:
            return result

        # Layer 4
        result = self.prepare_execution(result.safe_sql)
        return result

    # ── 辅助方法 ──

    @staticmethod
    def _clean_sql(sql: str) -> str:
        """清理 LLM 输出的 SQL"""
        sql = sql.strip()
        # 去除 markdown 代码块
        if sql.startswith("```"):
            lines = sql.split("\n")
            # 去掉第一行和最后一行
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            sql = "\n".join(lines).strip()
        # 去除末尾分号 (会统一处理)
        sql = sql.rstrip(";")
        return sql

    @staticmethod
    def _resolve_table(alias: str, tables_used: list[str]) -> Optional[str]:
        """将表别名解析为真实表名"""
        # 如果别名本身就是真实表名
        if alias in ALLOWED_TABLES:
            return alias
        # 简单策略: 返回第一个匹配的表 (实际应更精确)
        return None

    @staticmethod
    def _inject_where(sql: str, condition: str) -> str:
        """在 SQL 中注入 WHERE 条件"""
        import re

        # 检查是否已有 WHERE 子句
        if re.search(r'\bWHERE\b', sql, re.IGNORECASE):
            # 已有 WHERE → 追加 AND
            # 找到 WHERE 位置并在其后追加 (简化版: 在 GROUP BY/ORDER BY/LIMIT 前插入)
            for marker in ["GROUP BY", "ORDER BY", "LIMIT", "HAVING"]:
                m = re.search(r'\b' + marker + r'\b', sql, re.IGNORECASE)
                if m:
                    idx = m.start()
                    return sql[:idx] + f" AND {condition} " + sql[idx:]
            # 没有这些子句 → 在末尾追加
            return sql + f" AND {condition}"
        else:
            # 没有 WHERE → 在 GROUP BY/ORDER BY/LIMIT 前插入
            for marker in ["GROUP BY", "ORDER BY", "LIMIT", "HAVING"]:
                m = re.search(r'\b' + marker + r'\b', sql, re.IGNORECASE)
                if m:
                    idx = m.start()
                    return sql[:idx] + f" WHERE {condition} " + sql[idx:]
            # 末尾追加
            return sql + f" WHERE {condition}"
