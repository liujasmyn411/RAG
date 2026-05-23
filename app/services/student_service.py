from typing import List, Optional
from sqlalchemy import func, text
from sqlalchemy.orm import Session, joinedload
from app.models.entities import Student, Score, Employment, Class, Teacher


class StudentService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- 基础查询 ----------

    def get_student_by_no(self, student_no: str) -> Optional[Student]:
        return (
            self.db.query(Student)
            .filter(Student.student_no == student_no, Student.is_deleted == 0)
            .first()
        )

    def get_students_by_class(self, class_no: str) -> List[Student]:
        return (
            self.db.query(Student)
            .join(Class)
            .filter(Class.class_no == class_no, Student.is_deleted == 0)
            .all()
        )

    def get_students_by_name(self, name: str) -> List[Student]:
        return (
            self.db.query(Student)
            .filter(Student.name.like(f"%{name}%"), Student.is_deleted == 0)
            .all()
        )

    # ---------- 成绩查询 ----------

    def get_scores_by_student_no(self, student_no: str) -> List[Score]:
        student = self.get_student_by_no(student_no)
        if not student:
            return []
        return self.db.query(Score).filter(Score.student_id == student.id).order_by(Score.exam_seq).all()

    # ---------- 就业查询 ----------

    def get_employment_by_student_no(self, student_no: str) -> Optional[dict]:
        student = self.get_student_by_no(student_no)
        if not student:
            return None
        emp = self.db.query(Employment).filter(Employment.student_id == student.id).first()
        if not emp:
            return None
        class_no = student.class_.class_no if student.class_ else ""
        return {
            "student_no": student.student_no,
            "student_name": student.name,
            "student_class": class_no,
            "company": emp.company,
            "position": emp.position,
            "salary": float(emp.salary) if emp.salary else None,
            "open_date": emp.open_date.isoformat() if emp.open_date else None,
            "offer_date": emp.offer_date.isoformat() if emp.offer_date else None,
            "location": emp.location,
        }

    def get_employments_by_class(self, class_no: str) -> List[dict]:
        students = self.get_students_by_class(class_no)
        ids = [s.id for s in students]
        if not ids:
            return []
        emps = (
            self.db.query(Employment, Student)
            .join(Student, Employment.student_id == Student.id)
            .filter(Employment.student_id.in_(ids))
            .all()
        )
        result = []
        for emp, stu in emps:
            class_no_val = stu.class_.class_no if stu.class_ else ""
            result.append({
                "student_no": stu.student_no,
                "student_name": stu.name,
                "student_class": class_no_val,
                "company": emp.company,
                "position": emp.position,
                "salary": float(emp.salary) if emp.salary else None,
                "offer_date": emp.offer_date.isoformat() if emp.offer_date else None,
            })
        return result

    def get_employments_by_company(self, company: str) -> List[dict]:
        emps = (
            self.db.query(Employment, Student)
            .join(Student, Employment.student_id == Student.id)
            .filter(Employment.company.like(f"%{company}%"))
            .all()
        )
        result = []
        for emp, stu in emps:
            class_no = stu.class_.class_no if stu.class_ else ""
            result.append({
                "student_no": stu.student_no,
                "student_name": stu.name,
                "student_class": class_no,
                "company": emp.company,
                "position": emp.position,
                "salary": float(emp.salary) if emp.salary else None,
            })
        return result

    # ---------- 统计分析 ----------

    def get_students_over_30(self) -> List[Student]:
        return self.db.query(Student).filter(Student.age > 30, Student.is_deleted == 0).all()

    def get_class_gender_stats(self) -> List[dict]:
        results = []
        classes = self.db.query(Class).all()
        for cls in classes:
            total = self.db.query(Student).filter(Student.class_id == cls.id, Student.is_deleted == 0).count()
            male = self.db.query(Student).filter(
                Student.class_id == cls.id,
                Student.gender == "男",
                Student.is_deleted == 0
            ).count()
            female = self.db.query(Student).filter(
                Student.class_id == cls.id,
                Student.gender == "女",
                Student.is_deleted == 0
            ).count()
            results.append({
                "class_no": cls.class_no,
                "total": total,
                "male": male,
                "female": female,
            })
        return results

    def get_always_excellent_students(self) -> List[dict]:
        subq = (
            self.db.query(Score.student_id)
            .filter(Score.score < 80)
            .subquery()
        )
        students = (
            self.db.query(Student)
            .filter(~Student.id.in_(subq), Student.is_deleted == 0)
            .all()
        )
        result = []
        for s in students:
            scores = self.db.query(Score).filter(Score.student_id == s.id).all()
            if scores:
                result.append({
                    "student_no": s.student_no,
                    "name": s.name,
                    "scores": [{"seq": sc.exam_seq, "name": sc.exam_name, "score": float(sc.score)} for sc in scores],
                })
        return result

    def get_multiple_failures(self) -> List[dict]:
        fail_subq = (
            self.db.query(Score.student_id)
            .filter(Score.score < 60)
            .group_by(Score.student_id)
            .having(func.count(Score.id) >= 2)
            .subquery()
        )
        students = (
            self.db.query(Student)
            .filter(Student.id.in_(fail_subq), Student.is_deleted == 0)
            .all()
        )
        result = []
        for s in students:
            fails = self.db.query(Score).filter(
                Score.student_id == s.id,
                Score.score < 60
            ).all()
            class_no = s.class_.class_no if s.class_ else ""
            result.append({
                "name": s.name,
                "class_no": class_no,
                "failures": [{"seq": f.exam_seq, "name": f.exam_name, "score": float(f.score)} for f in fails],
            })
        return result

    def get_class_average_scores(self) -> List[dict]:
        results = (
            self.db.query(
                Class.class_no,
                Score.exam_seq,
                Score.exam_name,
                func.avg(Score.score).label("avg_score")
            )
            .join(Student, Student.class_id == Class.id)
            .join(Score, Score.student_id == Student.id)
            .filter(Student.is_deleted == 0)
            .group_by(Class.class_no, Score.exam_seq)
            .order_by(func.avg(Score.score).desc())
            .all()
        )
        return [
            {"class_no": r.class_no, "exam_seq": r.exam_seq, "exam_name": r.exam_name, "avg_score": round(float(r.avg_score), 2)}
            for r in results
        ]

    def get_top_employment_salary(self, limit: int = 5) -> List[dict]:
        results = (
            self.db.query(Employment, Student, Class)
            .join(Student, Employment.student_id == Student.id)
            .outerjoin(Class, Student.class_id == Class.id)
            .filter(Employment.salary != None)
            .order_by(Employment.salary.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "name": r.Student.name,
                "student_no": r.Student.student_no,
                "class_no": r.Class.class_no if r.Class else "",
                "offer_date": r.Employment.offer_date.isoformat() if r.Employment.offer_date else None,
                "company": r.Employment.company,
                "position": r.Employment.position,
                "salary": float(r.Employment.salary) if r.Employment.salary else None,
            }
            for r in results
        ]

    def get_student_employment_duration(self) -> List[dict]:
        results = (
            self.db.query(Employment, Student)
            .join(Student, Employment.student_id == Student.id)
            .filter(Employment.open_date != None, Employment.offer_date != None)
            .all()
        )
        return [
            {
                "name": r.Student.name,
                "student_no": r.Student.student_no,
                "duration_days": (r.Employment.offer_date - r.Employment.open_date).days,
            }
            for r in results
        ]

    def get_class_average_employment_duration(self) -> List[dict]:
        sql = """
        SELECT c.class_no, AVG(DATEDIFF(e.offer_date, e.open_date)) as avg_days
        FROM employments e
        JOIN students s ON e.student_id = s.id
        JOIN classes c ON s.class_id = c.id
        WHERE e.open_date IS NOT NULL AND e.offer_date IS NOT NULL AND s.is_deleted = 0
        GROUP BY c.class_no
        ORDER BY avg_days ASC
        """
        rows = self.db.execute(text(sql)).fetchall()
        return [
            {"class_no": r.class_no, "avg_days": round(float(r.avg_days), 1) if r.avg_days else 0}
            for r in rows
        ]
