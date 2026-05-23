#!/usr/bin/env python3
"""
初始化测试数据（SQLite）
运行: python seed_data.py
"""

from datetime import date
from app.models.database import SessionLocal, engine, Base
from app.models.entities import Student, Score, Employment, Class, Teacher


def init():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 清空旧数据
    db.query(Score).delete()
    db.query(Employment).delete()
    db.query(Student).delete()
    db.query(Class).delete()
    db.query(Teacher).delete()
    db.commit()

    # 老师
    t1 = Teacher(name="王老师", info="资深班主任，带班经验丰富", phone="13800138001")
    t2 = Teacher(name="李老师", info="数学名师，擅长逻辑推导", phone="13800138002")
    t3 = Teacher(name="张老师", info="就业指导老师，企业资源丰富", phone="13800138003")
    db.add_all([t1, t2, t3])
    db.commit()

    # 班级
    c1 = Class(class_no="JAVA-01", start_date=date(2024, 3, 1), headteacher_id=t1.id, instructor_id=t2.id)
    c2 = Class(class_no="PYTHON-01", start_date=date(2024, 6, 1), headteacher_id=t1.id, instructor_id=t3.id)
    db.add_all([c1, c2])
    db.commit()

    # 学生
    students = [
        Student(student_no="1001", name="张三", class_id=c1.id, native_place="江苏南京", school="南京大学", major="计算机", enrollment_date=date(2024, 3, 1), age=22, gender="男", education="本科"),
        Student(student_no="1002", name="李四", class_id=c1.id, native_place="浙江杭州", school="浙江大学", major="软件工程", enrollment_date=date(2024, 3, 1), age=24, gender="女", education="本科"),
        Student(student_no="1003", name="王五", class_id=c2.id, native_place="安徽合肥", school="合肥工业大学", major="电子信息", enrollment_date=date(2024, 6, 1), age=28, gender="男", education="硕士"),
        Student(student_no="1004", name="赵六", class_id=c1.id, native_place="四川成都", school="四川大学", major="数学", enrollment_date=date(2024, 3, 1), age=32, gender="男", education="本科"),
        Student(student_no="1005", name="孙七", class_id=c2.id, native_place="湖北武汉", school="武汉大学", major="物理", enrollment_date=date(2024, 6, 1), age=21, gender="女", education="本科"),
    ]
    db.add_all(students)
    db.commit()

    # 刷新以获取 ID
    for s in students:
        db.refresh(s)

    # 成绩
    scores = [
        Score(student_id=students[0].id, exam_seq=1, score=85),
        Score(student_id=students[0].id, exam_seq=2, score=78),
        Score(student_id=students[1].id, exam_seq=1, score=92),
        Score(student_id=students[1].id, exam_seq=2, score=88),
        Score(student_id=students[2].id, exam_seq=1, score=55),
        Score(student_id=students[2].id, exam_seq=2, score=48),
        Score(student_id=students[3].id, exam_seq=1, score=90),
        Score(student_id=students[3].id, exam_seq=2, score=85),
        Score(student_id=students[4].id, exam_seq=1, score=75),
        Score(student_id=students[4].id, exam_seq=2, score=82),
    ]
    db.add_all(scores)
    db.commit()

    # 就业
    emps = [
        Employment(student_id=students[1].id, student_name="李四", student_class="JAVA-01", open_date=date(2024, 9, 1), offer_date=date(2024, 9, 15), company="阿里巴巴", salary=15000),
        Employment(student_id=students[3].id, student_name="赵六", student_class="JAVA-01", open_date=date(2024, 8, 1), offer_date=date(2024, 10, 1), company="腾讯", salary=18000),
    ]
    db.add_all(emps)
    db.commit()

    print("[OK] 测试数据初始化完成！")
    print(f"   老师: {db.query(Teacher).count()} 人")
    print(f"   班级: {db.query(Class).count()} 个")
    print(f"   学生: {db.query(Student).count()} 人")
    print(f"   成绩: {db.query(Score).count()} 条")
    print(f"   就业: {db.query(Employment).count()} 条")


if __name__ == "__main__":
    init()
