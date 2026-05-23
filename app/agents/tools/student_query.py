from sqlalchemy.orm import Session
from app.agents.tools.registry import registry
from app.services.student_service import StudentService
from app.models.database import SessionLocal


def _get_service():
    db = SessionLocal()
    return StudentService(db)


@registry.register(
    name="query_student_info",
    description="查询学生的基本信息，如姓名、班级、年龄、籍贯、学历等。支持按学生编号或姓名查询。",
    parameters={
        "type": "object",
        "properties": {
            "student_no": {
                "type": "string",
                "description": "学生编号，如'1001'。如知道编号优先用编号查询。"
            },
            "name": {
                "type": "string",
                "description": "学生姓名，如'张三'。不知道编号时可用姓名模糊查询。"
            },
        },
    },
)
def query_student_info(student_no: str = None, name: str = None):
    svc = _get_service()
    if student_no:
        s = svc.get_student_by_no(student_no)
        if not s:
            return "未找到该编号的学生，许是簿子上没记着。"
        class_no = s.class_.class_no if s.class_ else ""
        return (
            f"学生编号：{s.student_no}，姓名：{s.name}，班级：{class_no}，"
            f"年龄：{s.age}，性别：{s.gender}，籍贯：{s.native_place or '未知'}，"
            f"学历：{s.education or '未知'}，毕业院校：{s.school or '未知'}，专业：{s.major or '未知'}"
        )
    if name:
        students = svc.get_students_by_name(name)
        if not students:
            return f"未找到姓名含'{name}'的学生。"
        lines = []
        for s in students:
            class_no = s.class_.class_no if s.class_ else ""
            lines.append(f"编号{s.student_no} {s.name}，班级{class_no}，{s.gender}，{s.age}岁")
        return "\n".join(lines)
    return "请提供学生编号或姓名。"


@registry.register(
    name="query_student_score",
    description="查询指定学生的各次考核成绩。",
    parameters={
        "type": "object",
        "properties": {
            "student_no": {
                "type": "string",
                "description": "学生编号"
            },
        },
        "required": ["student_no"],
    },
)
def query_student_score(student_no: str):
    svc = _get_service()
    scores = svc.get_scores_by_student_no(student_no)
    if not scores:
        return "该学生暂无成绩记录，或是还没考过。"
    lines = [f"学生 {student_no} 的成绩："]
    for sc in scores:
        name = sc.exam_name or f"第{sc.exam_seq}次考核"
        lines.append(f"  {name}：{float(sc.score)}分")
    return "\n".join(lines)


@registry.register(
    name="query_employment",
    description="查询学生的就业信息，包括就业公司、薪资、就业时长等。支持按学生编号、班级或公司名查询。",
    parameters={
        "type": "object",
        "properties": {
            "student_no": {
                "type": "string",
                "description": "学生编号"
            },
            "class_no": {
                "type": "string",
                "description": "班级编号，查询整个班级的就业情况"
            },
            "company": {
                "type": "string",
                "description": "公司名称，模糊查询"
            },
        },
    },
)
def query_employment(student_no: str = None, class_no: str = None, company: str = None):
    svc = _get_service()
    if student_no:
        emp = svc.get_employment_by_student_no(student_no)
        if not emp:
            return "该学生暂无就业记录。"
        duration = ""
        if emp.get("open_date") and emp.get("offer_date"):
            from datetime import datetime
            d1 = datetime.fromisoformat(emp["open_date"]).date()
            d2 = datetime.fromisoformat(emp["offer_date"]).date()
            days = (d2 - d1).days
            duration = f"，就业时长{days}天"
        return (
            f"学生 {student_no}（{emp['student_name']}）的就业信息："
            f"公司：{emp['company'] or '未知'}，"
            f"职位：{emp['position'] or '未记录'}，"
            f"薪资：{emp['salary'] if emp['salary'] else '未记录'}，"
            f"offer时间：{emp['offer_date'] or '未记录'}{duration}"
        )
    if class_no:
        emps = svc.get_employments_by_class(class_no)
        if not emps:
            return f"班级 {class_no} 暂无就业记录。"
        lines = [f"班级 {class_no} 的就业情况："]
        for e in emps:
            lines.append(f"  {e['student_name']} → {e['company'] or '未知'}，薪资{e['salary'] if e['salary'] else '未记录'}")
        return "\n".join(lines)
    if company:
        emps = svc.get_employments_by_company(company)
        if not emps:
            return f"未找到在'{company}'就业的学生。"
        lines = [f"在'{company}'就业的学生："]
        for e in emps:
            lines.append(f"  {e['student_name']}（班级{e['student_class'] or '未知'}）")
        return "\n".join(lines)
    return "请提供学生编号、班级编号或公司名称。"


@registry.register(
    name="query_statistics",
    description="查询学生管理系统的各类统计数据，如班级人数、成绩排名、就业薪资排行、平均就业时长等。",
    parameters={
        "type": "object",
        "properties": {
            "stat_type": {
                "type": "string",
                "description": "统计类型，可选值：\n"
                               "- class_gender: 每个班级的人数及男女生人数\n"
                               "- excellent_students: 每次考试都在80分以上的学生\n"
                               "- multiple_failures: 两次以上不及格的学生\n"
                               "- class_avg_score: 每次考试每个班级的平均分\n"
                               "- top_salary: 就业薪资最高的前五名学生\n"
                               "- employment_duration: 每个学生的就业时长\n"
                               "- class_avg_employment_duration: 每个班级的平均就业时长\n"
                               "- students_over_30: 超过30岁的学员"
            },
        },
        "required": ["stat_type"],
    },
)
def query_statistics(stat_type: str):
    svc = _get_service()
    if stat_type == "class_gender":
        data = svc.get_class_gender_stats()
        if not data:
            return "暂无班级统计信息。"
        lines = ["各班级人数及性别分布："]
        for d in data:
            lines.append(f"  {d['class_no']}：共{d['total']}人，男{d['male']}人，女{d['female']}人")
        return "\n".join(lines)

    if stat_type == "excellent_students":
        data = svc.get_always_excellent_students()
        if not data:
            return "暂无每次考试都在80分以上的学生。"
        lines = ["每次考试都在80分以上的学生："]
        for d in data:
            scores = ", ".join([f"{s['name']}{s['seq']}次{s['score']}分" for s in d["scores"]])
            lines.append(f"  {d['name']}（{d['student_no']}）：{scores}")
        return "\n".join(lines)

    if stat_type == "multiple_failures":
        data = svc.get_multiple_failures()
        if not data:
            return "暂无两次以上不及格的学生，倒也是件好事。"
        lines = ["两次以上不及格的学生："]
        for d in data:
            fails = ", ".join([f"{f['name']}{f['seq']}次{f['score']}分" for f in d["failures"]])
            lines.append(f"  {d['name']}（{d['class_no']}）：{fails}")
        return "\n".join(lines)

    if stat_type == "class_avg_score":
        data = svc.get_class_average_scores()
        if not data:
            return "暂无成绩统计信息。"
        lines = ["各班级每次考试平均分（从高到低）："]
        for d in data:
            name = d['exam_name'] or f"第{d['exam_seq']}次"
            lines.append(f"  {d['class_no']} {name}：{d['avg_score']}分")
        return "\n".join(lines)

    if stat_type == "top_salary":
        data = svc.get_top_employment_salary(limit=5)
        if not data:
            return "暂无就业薪资记录。"
        lines = ["就业薪资最高的前五名学生："]
        for i, d in enumerate(data, 1):
            lines.append(
                f"  第{i}名：{d['name']}（{d['class_no']}），"
                f"公司：{d['company'] or '未知'}，"
                f"职位：{d['position'] or '未记录'}，"
                f"薪资：{d['salary']}，"
                f"offer时间：{d['offer_date'] or '未记录'}"
            )
        return "\n".join(lines)

    if stat_type == "employment_duration":
        data = svc.get_student_employment_duration()
        if not data:
            return "暂无就业时长记录。"
        lines = ["各学生的就业时长（天）："]
        for d in data:
            lines.append(f"  {d['name']}（{d['student_no']}）：{d['duration_days']}天")
        return "\n".join(lines)

    if stat_type == "class_avg_employment_duration":
        data = svc.get_class_average_employment_duration()
        if not data:
            return "暂无班级平均就业时长记录。"
        lines = ["各班级平均就业时长（天）："]
        for d in data:
            lines.append(f"  {d['class_no']}：{d['avg_days']}天")
        return "\n".join(lines)

    if stat_type == "students_over_30":
        data = svc.get_students_over_30()
        if not data:
            return "暂无超过30岁的学员。"
        lines = ["超过30岁的学员："]
        for s in data:
            class_no = s.class_.class_no if s.class_ else ""
            lines.append(f"  {s.name}（{s.student_no}），{s.age}岁，班级{class_no}")
        return "\n".join(lines)

    return f"未知的统计类型：{stat_type}"
