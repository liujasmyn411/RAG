#!/usr/bin/env python3
"""
初始化 MySQL 测试数据
运行前确保：
  1. docker-compose up -d 已启动 MySQL
  2. .env 中 DATABASE_URL 已指向 MySQL
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import date
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.database import SessionLocal, engine, Base
from app.models.entities import (
    Role, User, Teacher, Class, Student, Score, Employment
)


def init_data():
    # 清空旧数据（按依赖顺序）
    db = SessionLocal()
    try:
        db.query(Score).delete()
        db.query(Employment).delete()
        db.query(Student).delete()
        db.query(Class).delete()
        db.query(Teacher).delete()
        db.query(User).delete()
        db.query(Role).delete()
        db.commit()
        print("[OK] 旧数据已清空")
    except Exception as e:
        db.rollback()
        print(f"[WARN] 清空失败（可能是空表）: {e}")

    # 1. 角色
    role_admin = Role(role_code="admin", role_name="管理员", description="系统管理员")
    role_teacher = Role(role_code="teacher", role_name="老师", description="班主任或授课老师")
    role_student = Role(role_code="student", role_name="学生", description="仅能查看自己的成绩和就业信息")
    db.add_all([role_admin, role_teacher, role_student])
    db.commit()
    print(f"[OK] 角色初始化: {role_admin.id}, {role_teacher.id}, {role_student.id}")

    # 2. 管理员账号
    admin_user = User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        role_id=role_admin.id,
        user_type="admin",
        name="系统管理员",
    )
    db.add(admin_user)
    db.commit()
    print(f"[OK] 管理员账号: {admin_user.username}")

    # 3. 老师
    t1 = Teacher(teacher_no="T001", name="王老师", info="资深班主任，带班经验丰富", phone="13800138001")
    t2 = Teacher(teacher_no="T002", name="李老师", info="数学名师，擅长逻辑推导", phone="13800138002")
    t3 = Teacher(teacher_no="T003", name="张老师", info="就业指导老师，企业资源丰富", phone="13800138003")
    db.add_all([t1, t2, t3])
    db.commit()

    # 为老师创建登录账号
    u_t1 = User(username="T001", password_hash=get_password_hash("teacher123"), role_id=role_teacher.id,
                user_type="teacher", ref_id=t1.id, name=t1.name)
    u_t2 = User(username="T002", password_hash=get_password_hash("teacher123"), role_id=role_teacher.id,
                user_type="teacher", ref_id=t2.id, name=t2.name)
    u_t3 = User(username="T003", password_hash=get_password_hash("teacher123"), role_id=role_teacher.id,
                user_type="teacher", ref_id=t3.id, name=t3.name)
    db.add_all([u_t1, u_t2, u_t3])
    db.commit()
    print(f"[OK] 老师: {t1.name}, {t2.name}, {t3.name}")

    # 4. 班级
    c1 = Class(class_no="JAVA-01", name="Java后端精英班", start_date=date(2024, 3, 1),
               headteacher_id=t1.id, instructor_id=t2.id)
    c2 = Class(class_no="PYTHON-01", name="Python全栈班", start_date=date(2024, 6, 1),
               headteacher_id=t1.id, instructor_id=t3.id)
    db.add_all([c1, c2])
    db.commit()
    print(f"[OK] 班级: {c1.class_no}, {c2.class_no}")

    # 5. 学生
    students = [
        Student(student_no="1001", name="张三", class_id=c1.id, native_place="江苏南京",
                school="南京大学", major="计算机", enrollment_date=date(2024, 3, 1),
                age=22, gender="男", education="本科"),
        Student(student_no="1002", name="李四", class_id=c1.id, native_place="浙江杭州",
                school="浙江大学", major="软件工程", enrollment_date=date(2024, 3, 1),
                age=24, gender="女", education="本科"),
        Student(student_no="1003", name="王五", class_id=c2.id, native_place="安徽合肥",
                school="合肥工业大学", major="电子信息", enrollment_date=date(2024, 6, 1),
                age=28, gender="男", education="硕士"),
        Student(student_no="1004", name="赵六", class_id=c1.id, native_place="四川成都",
                school="四川大学", major="数学", enrollment_date=date(2024, 3, 1),
                age=32, gender="男", education="本科"),
        Student(student_no="1005", name="孙七", class_id=c2.id, native_place="湖北武汉",
                school="武汉大学", major="物理", enrollment_date=date(2024, 6, 1),
                age=21, gender="女", education="本科"),
    ]
    db.add_all(students)
    db.commit()
    for s in students:
        db.refresh(s)

    # 为学生创建登录账号
    for s in students:
        u = User(
            username=s.student_no,
            password_hash=get_password_hash("student123"),
            role_id=role_student.id,
            user_type="student",
            ref_id=s.id,
            name=s.name,
        )
        db.add(u)
    db.commit()
    print(f"[OK] 学生: {', '.join([s.name for s in students])}")

    # 6. 成绩
    scores = [
        Score(student_id=students[0].id, exam_seq=1, exam_name="第一次月考", score=85),
        Score(student_id=students[0].id, exam_seq=2, exam_name="第二次月考", score=78),
        Score(student_id=students[1].id, exam_seq=1, exam_name="第一次月考", score=92),
        Score(student_id=students[1].id, exam_seq=2, exam_name="第二次月考", score=88),
        Score(student_id=students[2].id, exam_seq=1, exam_name="第一次月考", score=55),
        Score(student_id=students[2].id, exam_seq=2, exam_name="第二次月考", score=48),
        Score(student_id=students[3].id, exam_seq=1, exam_name="第一次月考", score=90),
        Score(student_id=students[3].id, exam_seq=2, exam_name="第二次月考", score=85),
        Score(student_id=students[4].id, exam_seq=1, exam_name="第一次月考", score=75),
        Score(student_id=students[4].id, exam_seq=2, exam_name="第二次月考", score=82),
    ]
    db.add_all(scores)
    db.commit()
    print(f"[OK] 成绩: {len(scores)} 条")

    # 7. 就业
    emps = [
        Employment(student_id=students[1].id, open_date=date(2024, 9, 1),
                   offer_date=date(2024, 9, 15), company="阿里巴巴",
                   position="Java开发工程师", salary=15000, location="杭州"),
        Employment(student_id=students[3].id, open_date=date(2024, 8, 1),
                   offer_date=date(2024, 10, 1), company="腾讯",
                   position="后端开发", salary=18000, location="深圳"),
    ]
    db.add_all(emps)
    db.commit()
    print(f"[OK] 就业: {len(emps)} 条")

    print("\n[OK] MySQL 测试数据初始化完成！")
    print(f"   管理员: 1 人 (admin)")
    print(f"   老师: 3 人")
    print(f"   班级: 2 个")
    print(f"   学生: 5 人")
    print(f"   成绩: 10 条")
    print(f"   就业: 2 条")
    db.close()


if __name__ == "__main__":
    init_data()
