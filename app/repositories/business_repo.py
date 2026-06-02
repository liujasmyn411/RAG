"""业务 CRUD 数据访问层"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import func, select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Student, Score, Employment, Class, Teacher


class StudentRepo:
    """学生信息 CRUD"""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, data: dict) -> Student:
        s = Student(**data)
        self._db.add(s)
        await self._db.flush()
        return s

    async def get_by_id(self, student_id: str) -> Optional[Student]:
        result = await self._db.execute(
            select(Student).where(
                Student.student_id == student_id,
                Student.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        student_id: Optional[str] = None,
        name: Optional[str] = None,
        class_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Student], int]:
        conditions = [Student.is_deleted == False]
        if student_id:
            conditions.append(Student.student_id.like(f"%{student_id}%"))
        if name:
            conditions.append(Student.name.like(f"%{name}%"))
        if class_name:
            conditions.append(Student.class_name == class_name)

        base = select(Student).where(and_(*conditions))
        count_q = select(func.count()).select_from(base.subquery())
        total = (await self._db.execute(count_q)).scalar() or 0

        result = await self._db.execute(
            base.order_by(Student.student_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def update(self, student_id: str, data: dict) -> Optional[Student]:
        s = await self.get_by_id(student_id)
        if not s:
            return None
        for k, v in data.items():
            if v is not None:
                setattr(s, k, v)
        s.updated_at = datetime.now()
        await self._db.flush()
        return s

    async def soft_delete(self, student_id: str) -> bool:
        s = await self.get_by_id(student_id)
        if not s:
            return False
        s.is_deleted = True
        s.updated_at = datetime.now()
        await self._db.flush()
        return True


class ScoreRepo:
    """成绩 CRUD"""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, data: dict) -> Score:
        s = Score(**data)
        self._db.add(s)
        await self._db.flush()
        return s

    async def get_by_student(self, student_id: str) -> list[Score]:
        result = await self._db.execute(
            select(Score)
            .where(Score.student_id == student_id)
            .order_by(Score.exam_sequence)
        )
        return list(result.scalars().all())

    async def update_score(
        self, student_id: str, exam_sequence: int, score: float
    ) -> Optional[Score]:
        result = await self._db.execute(
            select(Score).where(
                Score.student_id == student_id,
                Score.exam_sequence == exam_sequence,
            )
        )
        s = result.scalar_one_or_none()
        if not s:
            return None
        s.score = score
        await self._db.flush()
        return s

    async def delete_score(self, student_id: str, exam_sequence: int) -> bool:
        result = await self._db.execute(
            delete(Score).where(
                Score.student_id == student_id,
                Score.exam_sequence == exam_sequence,
            )
        )
        await self._db.flush()
        return result.rowcount > 0


class EmploymentRepo:
    """就业信息 CRUD"""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def upsert(self, data: dict) -> Employment:
        result = await self._db.execute(
            select(Employment).where(Employment.student_id == data["student_id"])
        )
        existing = result.scalar_one_or_none()
        if existing:
            for k, v in data.items():
                if v is not None:
                    setattr(existing, k, v)
            existing.updated_at = datetime.now()
        else:
            existing = Employment(**data)
            self._db.add(existing)
        await self._db.flush()
        return existing

    async def get_by_student(self, student_id: str) -> Optional[Employment]:
        result = await self._db.execute(
            select(Employment).where(Employment.student_id == student_id)
        )
        return result.scalar_one_or_none()

    async def get_by_class(self, class_name: str) -> list[Employment]:
        result = await self._db.execute(
            select(Employment).where(Employment.class_name == class_name)
        )
        return list(result.scalars().all())

    async def query(
        self,
        student_id: Optional[str] = None,
        company_name: Optional[str] = None,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Employment], int]:
        conditions = []
        if student_id:
            conditions.append(Employment.student_id.like(f"%{student_id}%"))
        if company_name:
            conditions.append(Employment.company_name.like(f"%{company_name}%"))
        if salary_min is not None:
            conditions.append(Employment.salary >= salary_min)
        if salary_max is not None:
            conditions.append(Employment.salary <= salary_max)

        base = select(Employment).where(and_(*conditions)) if conditions else select(Employment)
        count_q = select(func.count()).select_from(base.subquery())
        total = (await self._db.execute(count_q)).scalar() or 0

        result = await self._db.execute(
            base.order_by(Employment.student_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def delete(self, student_id: str) -> bool:
        result = await self._db.execute(
            delete(Employment).where(Employment.student_id == student_id)
        )
        await self._db.flush()
        return result.rowcount > 0


class ClassRepo:
    """班级 CRUD"""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, data: dict) -> Class:
        c = Class(**data)
        self._db.add(c)
        await self._db.flush()
        return c

    async def get_by_name(self, class_name: str) -> Optional[Class]:
        result = await self._db.execute(
            select(Class).where(Class.class_name == class_name)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Class]:
        result = await self._db.execute(select(Class).order_by(Class.class_name))
        return list(result.scalars().all())

    async def update(self, class_name: str, data: dict) -> Optional[Class]:
        c = await self.get_by_name(class_name)
        if not c:
            return None
        for k, v in data.items():
            if v is not None:
                setattr(c, k, v)
        await self._db.flush()
        return c

    async def delete(self, class_name: str) -> bool:
        c = await self.get_by_name(class_name)
        if not c:
            return False
        await self._db.delete(c)
        await self._db.flush()
        return True


class TeacherRepo:
    """教师 CRUD"""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, data: dict) -> Teacher:
        t = Teacher(**data)
        self._db.add(t)
        await self._db.flush()
        return t

    async def get_by_id(self, teacher_id: str) -> Optional[Teacher]:
        result = await self._db.execute(
            select(Teacher).where(Teacher.teacher_id == teacher_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Teacher]:
        result = await self._db.execute(select(Teacher).order_by(Teacher.teacher_id))
        return list(result.scalars().all())

    async def update(self, teacher_id: str, data: dict) -> Optional[Teacher]:
        t = await self.get_by_id(teacher_id)
        if not t:
            return None
        for k, v in data.items():
            if v is not None:
                setattr(t, k, v)
        await self._db.flush()
        return t

    async def delete(self, teacher_id: str) -> bool:
        t = await self.get_by_id(teacher_id)
        if not t:
            return False
        await self._db.delete(t)
        await self._db.flush()
        return True


class StatisticsRepo:
    """统计分析查询"""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_students_older_than(self, age: int = 30) -> list[dict]:
        """查询所有超过指定年龄的学生"""
        result = await self._db.execute(
            select(Student)
            .where(Student.age > age, Student.is_deleted == False)
            .order_by(Student.age.desc())
        )
        rows = result.scalars().all()
        return [
            {
                "student_id": r.student_id,
                "name": r.name,
                "class_name": r.class_name,
                "age": r.age,
                "gender": r.gender,
            }
            for r in rows
        ]

    async def get_class_gender_counts(self) -> list[dict]:
        """统计每个班级的人数以及男女数量"""
        result = await self._db.execute(
            select(Student)
            .where(Student.is_deleted == False)
            .order_by(Student.class_name)
        )
        rows = result.scalars().all()

        class_stats: dict[str, dict] = {}
        for r in rows:
            cn = r.class_name
            if cn not in class_stats:
                class_stats[cn] = {"class_name": cn, "total": 0, "male": 0, "female": 0}
            class_stats[cn]["total"] += 1
            if r.gender in ("男", "male"):
                class_stats[cn]["male"] += 1
            elif r.gender in ("女", "female"):
                class_stats[cn]["female"] += 1
        return sorted(class_stats.values(), key=lambda x: x["class_name"])

    async def get_students_always_above_80(self) -> list[dict]:
        """查询每次考试成绩都在80分以上的学生"""
        # 子查询: 找出所有最低分 >= 80 的学生
        subq = (
            select(Score.student_id)
            .group_by(Score.student_id)
            .having(func.min(Score.score) >= 80)
            .subquery()
        )
        result = await self._db.execute(
            select(Student, Score)
            .join(subq, Student.student_id == subq.c.student_id)
            .join(Score, Student.student_id == Score.student_id)
            .where(Student.is_deleted == False)
            .order_by(Student.student_id, Score.exam_sequence)
        )
        rows = result.all()
        grouped: dict[str, dict] = {}
        for student, score in rows:
            sid = student.student_id
            if sid not in grouped:
                grouped[sid] = {
                    "student_id": sid,
                    "name": student.name,
                    "scores": [],
                }
            grouped[sid]["scores"].append({
                "exam_sequence": score.exam_sequence,
                "score": score.score,
            })
        return list(grouped.values())

    async def get_students_with_failures(self, min_fail_count: int = 2) -> list[dict]:
        """查询有指定次数以上不及格(成绩<60)的学生"""
        subq = (
            select(
                Score.student_id,
                func.count(Score.id).label("fail_count"),
                func.group_concat(Score.score).label("fail_scores_str"),
            )
            .where(Score.score < 60)
            .group_by(Score.student_id)
            .having(func.count(Score.id) > min_fail_count)
            .subquery()
        )
        result = await self._db.execute(
            select(Student, subq.c.fail_count, subq.c.fail_scores_str)
            .join(subq, Student.student_id == subq.c.student_id)
            .where(Student.is_deleted == False)
        )
        rows = result.all()
        output = []
        for student, fail_count, fail_scores_str in rows:
            try:
                fail_scores = [float(x) for x in fail_scores_str.split(",")]
            except (ValueError, AttributeError):
                fail_scores = []
            output.append({
                "student_id": student.student_id,
                "name": student.name,
                "class_name": student.class_name,
                "fail_count": fail_count,
                "fail_scores": fail_scores,
            })
        return output

    async def get_exam_avg_by_class(self) -> list[dict]:
        """统计每次考试每个班级的平均分，从高到低排序"""
        result = await self._db.execute(
            select(
                Student.class_name,
                Score.exam_sequence,
                func.avg(Score.score).label("avg_score"),
                func.count(Score.student_id).label("student_count"),
            )
            .join(Score, Student.student_id == Score.student_id)
            .where(Student.is_deleted == False)
            .group_by(Student.class_name, Score.exam_sequence)
            .order_by(func.avg(Score.score).desc())
        )
        return [
            {
                "class_name": row.class_name,
                "exam_sequence": row.exam_sequence,
                "avg_score": round(float(row.avg_score), 2),
                "student_count": row.student_count,
            }
            for row in result.all()
        ]

    async def get_top_salary(self, limit: int = 5) -> list[dict]:
        """统计就业薪资最高的前N名学生"""
        result = await self._db.execute(
            select(Employment)
            .where(Employment.salary.isnot(None))
            .order_by(Employment.salary.desc())
            .limit(limit)
        )
        return [
            {
                "student_id": r.student_id,
                "name": r.name,
                "class_name": r.class_name,
                "offer_time": r.offer_time,
                "company_name": r.company_name,
                "salary": r.salary,
            }
            for r in result.scalars().all()
        ]

    async def get_employment_durations(self) -> list[dict]:
        """统计每个学生的就业时长 (offer_time - employment_open_time)"""
        result = await self._db.execute(
            select(Employment).where(
                Employment.employment_open_time.isnot(None),
                Employment.offer_time.isnot(None),
            )
        )
        rows = result.scalars().all()
        output = []
        for r in rows:
            duration = (r.offer_time - r.employment_open_time).days
            output.append({
                "student_id": r.student_id,
                "name": r.name,
                "class_name": r.class_name,
                "open_time": r.employment_open_time,
                "offer_time": r.offer_time,
                "duration_days": duration,
            })
        return sorted(output, key=lambda x: x["duration_days"] or 0)

    async def get_class_avg_employment_duration(self) -> list[dict]:
        """统计每个班级的平均就业时长(只统计有就业开放时间的学生)"""
        result = await self._db.execute(
            select(Employment).where(
                Employment.employment_open_time.isnot(None),
                Employment.offer_time.isnot(None),
            )
        )
        rows = result.scalars().all()
        class_data: dict[str, dict] = {}
        for r in rows:
            cn = r.class_name or "未分配"
            duration = (r.offer_time - r.employment_open_time).days
            if cn not in class_data:
                class_data[cn] = {"total_days": 0, "count": 0}
            class_data[cn]["total_days"] += duration
            class_data[cn]["count"] += 1

        output = []
        for cn, d in class_data.items():
            output.append({
                "class_name": cn,
                "avg_duration_days": round(d["total_days"] / d["count"], 1),
                "student_count": d["count"],
            })
        return sorted(output, key=lambda x: x["avg_duration_days"])
