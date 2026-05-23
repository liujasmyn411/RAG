-- 学生管理系统数据库初始化脚本
-- MySQL 8.0

USE student_system;

-- ============================================
-- 1. roles（角色定义）
-- ============================================
CREATE TABLE IF NOT EXISTS roles (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    role_code VARCHAR(32) NOT NULL COMMENT '角色编码',
    role_name VARCHAR(64) NOT NULL COMMENT '角色名称',
    description VARCHAR(256) DEFAULT NULL COMMENT '描述',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_role_code (role_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色定义表';

-- 初始角色数据
INSERT INTO roles (role_code, role_name, description) VALUES
('admin', '管理员', '系统管理员，拥有全部权限'),
('teacher', '老师', '班主任或授课老师，管理本班学生'),
('student', '学生', '仅能查看自己的成绩和就业信息');

-- ============================================
-- 2. users（统一认证表）
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    username VARCHAR(64) NOT NULL COMMENT '登录账号',
    password_hash VARCHAR(256) NOT NULL COMMENT '密码哈希（bcrypt）',
    role_id BIGINT UNSIGNED NOT NULL COMMENT '角色ID',
    user_type VARCHAR(16) NOT NULL COMMENT '用户类型：admin/teacher/student/advisor',
    ref_id BIGINT UNSIGNED DEFAULT NULL COMMENT '关联详情表主键ID',
    name VARCHAR(64) NOT NULL COMMENT '显示姓名',
    avatar VARCHAR(256) DEFAULT NULL COMMENT '头像URL',
    last_login DATETIME DEFAULT NULL COMMENT '最后登录时间',
    is_active TINYINT UNSIGNED DEFAULT 1 COMMENT '是否启用：0=禁用 1=启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_username (username),
    KEY idx_role_type (role_id, user_type),
    CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='统一认证表';

-- ============================================
-- 3. departments（部门 · 预留）
-- ============================================
CREATE TABLE IF NOT EXISTS departments (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    dept_no VARCHAR(32) NOT NULL COMMENT '部门编号',
    name VARCHAR(128) NOT NULL COMMENT '部门名称',
    manager_id BIGINT UNSIGNED DEFAULT NULL COMMENT '部门负责人（users.id）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_dept_no (dept_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部门表';

-- ============================================
-- 4. advisors（顾问 · 预留）
-- ============================================
CREATE TABLE IF NOT EXISTS advisors (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    user_id BIGINT UNSIGNED DEFAULT NULL COMMENT '关联认证账号（users.id）',
    advisor_no VARCHAR(32) NOT NULL COMMENT '顾问编号',
    name VARCHAR(64) NOT NULL COMMENT '姓名',
    phone VARCHAR(32) DEFAULT NULL COMMENT '手机号',
    email VARCHAR(128) DEFAULT NULL COMMENT '邮箱',
    department_id BIGINT UNSIGNED DEFAULT NULL COMMENT '所属部门',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_advisor_no (advisor_no),
    KEY idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='顾问表';

-- ============================================
-- 5. teachers（老师）
-- ============================================
CREATE TABLE IF NOT EXISTS teachers (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    user_id BIGINT UNSIGNED DEFAULT NULL COMMENT '关联认证账号（users.id）',
    teacher_no VARCHAR(32) NOT NULL COMMENT '老师工号',
    name VARCHAR(64) NOT NULL COMMENT '姓名',
    phone VARCHAR(32) DEFAULT NULL COMMENT '手机号',
    email VARCHAR(128) DEFAULT NULL COMMENT '邮箱',
    info VARCHAR(512) DEFAULT NULL COMMENT '老师简介、专长',
    status VARCHAR(16) DEFAULT 'active' COMMENT '状态：active/resigned',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_teacher_no (teacher_no),
    KEY idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='老师表';

-- ============================================
-- 6. classes（班级）
-- ============================================
CREATE TABLE IF NOT EXISTS classes (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    class_no VARCHAR(32) NOT NULL COMMENT '班级编号',
    name VARCHAR(128) DEFAULT NULL COMMENT '班级名称',
    start_date DATE DEFAULT NULL COMMENT '开课时间',
    end_date DATE DEFAULT NULL COMMENT '预计结课时间',
    headteacher_id BIGINT UNSIGNED DEFAULT NULL COMMENT '班主任（teachers.id）',
    instructor_id BIGINT UNSIGNED DEFAULT NULL COMMENT '授课老师（teachers.id）',
    status VARCHAR(16) DEFAULT 'active' COMMENT '状态：active/closed',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_class_no (class_no),
    KEY idx_headteacher (headteacher_id),
    KEY idx_instructor (instructor_id),
    CONSTRAINT fk_class_headteacher FOREIGN KEY (headteacher_id) REFERENCES teachers (id),
    CONSTRAINT fk_class_instructor FOREIGN KEY (instructor_id) REFERENCES teachers (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='班级表';

-- ============================================
-- 7. students（学生 · 核心表）
-- ============================================
CREATE TABLE IF NOT EXISTS students (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    user_id BIGINT UNSIGNED DEFAULT NULL COMMENT '关联认证账号（users.id）',
    student_no VARCHAR(32) NOT NULL COMMENT '学生编号（业务主键）',
    name VARCHAR(64) NOT NULL COMMENT '姓名',
    class_id BIGINT UNSIGNED DEFAULT NULL COMMENT '所属班级（classes.id）',
    native_place VARCHAR(128) DEFAULT NULL COMMENT '籍贯',
    school VARCHAR(128) DEFAULT NULL COMMENT '毕业院校',
    major VARCHAR(128) DEFAULT NULL COMMENT '专业',
    enrollment_date DATE DEFAULT NULL COMMENT '入学时间',
    graduation_date DATE DEFAULT NULL COMMENT '毕业时间',
    education VARCHAR(32) DEFAULT NULL COMMENT '学历：本科/硕士/大专/高中',
    advisor_id BIGINT UNSIGNED DEFAULT NULL COMMENT '顾问（advisors.id）',
    age INT DEFAULT NULL COMMENT '年龄',
    gender VARCHAR(8) DEFAULT NULL COMMENT '性别：男/女',
    phone VARCHAR(32) DEFAULT NULL COMMENT '手机号',
    email VARCHAR(128) DEFAULT NULL COMMENT '邮箱',
    id_card VARCHAR(18) DEFAULT NULL COMMENT '身份证号',
    status VARCHAR(16) DEFAULT 'studying' COMMENT '状态：studying/graduated/employed',
    is_deleted TINYINT UNSIGNED DEFAULT 0 COMMENT '逻辑删除：0=正常 1=已删',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_student_no (student_no),
    KEY idx_class_id (class_id),
    KEY idx_name (name),
    KEY idx_status_deleted (status, is_deleted),
    KEY idx_user_id (user_id),
    CONSTRAINT fk_student_class FOREIGN KEY (class_id) REFERENCES classes (id),
    CONSTRAINT fk_student_advisor FOREIGN KEY (advisor_id) REFERENCES advisors (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学生表';

-- ============================================
-- 8. scores（考核成绩）
-- ============================================
CREATE TABLE IF NOT EXISTS scores (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    student_id BIGINT UNSIGNED NOT NULL COMMENT '学生（students.id）',
    exam_seq INT NOT NULL COMMENT '考核序次',
    exam_name VARCHAR(64) DEFAULT NULL COMMENT '考核名称（期中/期末/月考）',
    score DECIMAL(5,2) NOT NULL COMMENT '成绩',
    max_score DECIMAL(5,2) DEFAULT 100 COMMENT '满分',
    exam_date DATE DEFAULT NULL COMMENT '考试日期',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_student_exam (student_id, exam_seq),
    KEY idx_student_id (student_id),
    CONSTRAINT fk_score_student FOREIGN KEY (student_id) REFERENCES students (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成绩表';

-- ============================================
-- 9. employments（就业信息）
-- ============================================
CREATE TABLE IF NOT EXISTS employments (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    student_id BIGINT UNSIGNED NOT NULL COMMENT '学生（students.id）',
    open_date DATE DEFAULT NULL COMMENT '就业开放时间',
    offer_date DATE DEFAULT NULL COMMENT 'offer下发时间',
    company VARCHAR(128) DEFAULT NULL COMMENT '就业公司名称',
    position VARCHAR(128) DEFAULT NULL COMMENT '职位',
    salary DECIMAL(10,2) DEFAULT NULL COMMENT '月薪',
    location VARCHAR(128) DEFAULT NULL COMMENT '工作地点',
    status VARCHAR(16) DEFAULT 'employed' COMMENT '状态：employed/intern/resigned',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_student_employment (student_id),
    KEY idx_company (company),
    CONSTRAINT fk_employment_student FOREIGN KEY (student_id) REFERENCES students (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='就业表';
