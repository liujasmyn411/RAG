# 学生管理系统 · 数据库设计方案

> 与《需求.md》配套，覆盖当前所有功能 + 用户认证体系 + 预留后续扩展（部门/顾问管理）。

---

## 一、设计原则

1. **去冗余**：就业表不再冗余存储学生姓名/班级，统一通过 `student_id` JOIN 查询。
2. **逻辑删除**：学生表用 `is_deleted` 软删除，保留历史数据可追溯。
3. **审计字段**：每张表都有 `created_at`、`updated_at`，便于排查问题。
4. **业务主键 + 自增主键**：学生编号 `student_no` 是业务唯一标识，但数据库层面仍用自增 `id` 做主键，兼顾性能和灵活性。
5. **统一认证 + 分离详情**：所有用户（管理员、老师、学生）共用一张 `users` 表做登录认证，各自的业务详情保存在独立表中，通过 `user_id` 关联。
6. **RBAC 预留**：角色权限表先设计好，当前阶段可简化，但结构完整。

---

## 二、用户体系总体设计

系统有三类用户，都需要登录：

| 用户类型 | 登录账号 | 密码 | 详情表 | 典型权限 |
|----------|---------|------|--------|---------|
| **管理员** | 自定义（如 admin） | 有 | 无独立详情，或关联 teacher | 全部权限 |
| **老师** | 工号（teacher_no） | 有 | teachers | 本班学生的增改查、成绩录入 |
| **学生** | 学号（student_no） | 有 | students | 仅查看自己的成绩、就业信息 |

**认证流程**：
1. 用户用 `username` + `password` 登录 `users` 表
2. 根据 `user_type` 路由到对应详情表获取业务数据
3. 根据 `role_id` 鉴权，决定可操作的范围

---

## 三、ER 关系图（文字版）

```
roles (角色定义)
  │1
  │
  ▼N
users (统一认证入口)
  │1          │1          │1          │0..1
  │          │          │          │
  ▼1         ▼1         ▼1         ▼
teachers  students   advisors   (admin无详情表)
  │1          │
  │          │
  ▼N         ▼N
classes ────┘
  │1
  │
  ▼N
scores
  │
  ▼1
employments
```

---

## 四、表结构详细定义

### 4.1 roles（角色定义）

RBAC 基础，先定义好角色，后续权限迭代时挂菜单/按钮权限。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | AUTO_INCREMENT | 自增主键 |
| role_code | VARCHAR(32) | UNIQUE, NOT NULL | 角色编码：admin / teacher / student |
| role_name | VARCHAR(64) | NOT NULL | 角色名称：管理员 / 老师 / 学生 |
| description | VARCHAR(256) | | 描述 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**初始数据：**
- admin / 管理员
- teacher / 老师
- student / 学生

---

### 4.2 users（统一认证表）

所有登录用户的唯一入口。管理员、老师、学生都在这张表。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | AUTO_INCREMENT | 自增主键 |
| username | VARCHAR(64) | UNIQUE, NOT NULL | 登录账号（管理员自定义，老师=工号，学生=学号） |
| password_hash | VARCHAR(256) | NOT NULL | 密码哈希（bcrypt） |
| role_id | BIGINT FK | → roles.id | 角色 |
| user_type | VARCHAR(16) | NOT NULL | 用户类型：admin / teacher / student / advisor |
| ref_id | BIGINT | | 关联详情表的主键ID（根据user_type路由到teachers/students/advisors） |
| name | VARCHAR(64) | NOT NULL | 显示姓名 |
| avatar | VARCHAR(256) | | 头像URL |
| last_login | DATETIME | | 最后登录时间 |
| is_active | TINYINT | DEFAULT 1 | 是否启用：0=禁用 1=启用 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**索引：**
- UNIQUE `uk_username` (username)
- INDEX `idx_role_type` (role_id, user_type)

**设计说明：**
- `ref_id` 是一个通用外键，配合 `user_type` 使用：
  - 当 `user_type='teacher'` 时，`ref_id` → `teachers.id`
  - 当 `user_type='student'` 时，`ref_id` → `students.id`
  - 当 `user_type='advisor'` 时，`ref_id` → `advisors.id`
  - 当 `user_type='admin'` 时，`ref_id` 可为空（纯管理员账号）
- 程序层负责维护 `ref_id` 和 `user_type` 的一致性，数据库层不做跨表外键约束（MySQL 不支持一个字段同时外键关联多张表）。

---

### 4.3 departments（部门 · 预留）

后续迭代"部门管理、顾问管理"时使用。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | AUTO_INCREMENT | 自增主键 |
| dept_no | VARCHAR(32) | UNIQUE, NOT NULL | 部门编号 |
| name | VARCHAR(128) | NOT NULL | 部门名称 |
| manager_id | BIGINT | | 部门负责人（关联 users.id） |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

### 4.4 advisors（顾问 · 预留）

后续迭代使用。当前阶段学生表的 `advisor_id` 可为空。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | AUTO_INCREMENT | 自增主键 |
| user_id | BIGINT FK | → users.id | 关联认证账号（可空，未开通账号时不关联） |
| advisor_no | VARCHAR(32) | UNIQUE, NOT NULL | 顾问编号 |
| name | VARCHAR(64) | NOT NULL | 姓名 |
| phone | VARCHAR(32) | | 手机号 |
| email | VARCHAR(128) | | 邮箱 |
| department_id | BIGINT FK | → departments.id | 所属部门 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

### 4.5 teachers（老师）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | AUTO_INCREMENT | 自增主键 |
| user_id | BIGINT FK | → users.id | 关联认证账号（可空） |
| teacher_no | VARCHAR(32) | UNIQUE, NOT NULL | 老师工号 |
| name | VARCHAR(64) | NOT NULL | 姓名 |
| phone | VARCHAR(32) | | 手机号 |
| email | VARCHAR(128) | | 邮箱 |
| info | VARCHAR(512) | | 老师简介、专长 |
| status | VARCHAR(16) | DEFAULT 'active' | 状态：active / resigned |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

---

### 4.6 classes（班级）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | AUTO_INCREMENT | 自增主键 |
| class_no | VARCHAR(32) | UNIQUE, NOT NULL | 班级编号 |
| name | VARCHAR(128) | | 班级名称（如"Java后端精英班"） |
| start_date | DATE | | 开课时间 |
| end_date | DATE | | 预计结课时间 |
| headteacher_id | BIGINT FK | → teachers.id | 班主任 |
| instructor_id | BIGINT FK | → teachers.id | 授课老师 |
| status | VARCHAR(16) | DEFAULT 'active' | 状态：active / closed |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

---

### 4.7 students（学生 · 核心表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | AUTO_INCREMENT | 自增主键 |
| user_id | BIGINT FK | → users.id | 关联认证账号（可空，未开通账号时不关联） |
| student_no | VARCHAR(32) | UNIQUE, NOT NULL | 学生编号（业务主键） |
| name | VARCHAR(64) | NOT NULL | 姓名 |
| class_id | BIGINT FK | → classes.id | 所属班级 |
| native_place | VARCHAR(128) | | 籍贯 |
| school | VARCHAR(128) | | 毕业院校 |
| major | VARCHAR(128) | | 专业 |
| enrollment_date | DATE | | 入学时间 |
| graduation_date | DATE | | 毕业时间 |
| education | VARCHAR(32) | | 学历：本科/硕士/大专/高中 |
| advisor_id | BIGINT FK | → advisors.id (可空) | 顾问 |
| age | INT | | 年龄 |
| gender | VARCHAR(8) | | 性别：男/女 |
| phone | VARCHAR(32) | | 手机号 |
| email | VARCHAR(128) | | 邮箱 |
| id_card | VARCHAR(18) | | 身份证号 |
| status | VARCHAR(16) | DEFAULT 'studying' | 状态：studying / graduated / employed |
| is_deleted | TINYINT | DEFAULT 0 | 逻辑删除：0=正常 1=已删 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**索引：**
- UNIQUE `uk_student_no` (student_no)
- INDEX `idx_class_id` (class_id)
- INDEX `idx_name` (name)
- INDEX `idx_status_deleted` (status, is_deleted)

---

### 4.8 scores（考核成绩）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | AUTO_INCREMENT | 自增主键 |
| student_id | BIGINT FK | → students.id | 学生 |
| exam_seq | INT | NOT NULL | 考核序次（第1次、第2次…） |
| exam_name | VARCHAR(64) | | 考核名称（期中/期末/月考） |
| score | DECIMAL(5,2) | NOT NULL | 成绩 |
| max_score | DECIMAL(5,2) | DEFAULT 100 | 满分 |
| exam_date | DATE | | 考试日期 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**约束：**
- UNIQUE `uk_student_exam` (student_id, exam_seq) —— 一个学生同一序次只能有一条成绩

---

### 4.9 employments（就业信息）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | AUTO_INCREMENT | 自增主键 |
| student_id | BIGINT FK | → students.id | 学生（一对一） |
| open_date | DATE | | 就业开放时间 |
| offer_date | DATE | | offer 下发时间 |
| company | VARCHAR(128) | | 就业公司名称 |
| position | VARCHAR(128) | | 职位 |
| salary | DECIMAL(10,2) | | 月薪 |
| location | VARCHAR(128) | | 工作地点 |
| status | VARCHAR(16) | DEFAULT 'employed' | 状态：employed / intern / resigned |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**约束：**
- UNIQUE `uk_student_employment` (student_id) —— 一个学生一条就业记录

---

## 五、权限矩阵（RBAC 参考）

| 功能模块 | 管理员 | 老师（班主任/授课） | 学生 |
|----------|--------|---------------------|------|
| 查看所有学生 | ✅ | ✅ 仅限本班 | ❌ |
| 修改学生信息 | ✅ | ✅ 仅限本班 | ❌ |
| 删除学生 | ✅ | ❌ | ❌ |
| 录入成绩 | ✅ | ✅ | ❌ |
| 修改成绩 | ✅ | ✅ | ❌ |
| 查看成绩 | ✅ | ✅ 仅限本班 | ✅ 仅自己 |
| 查看就业 | ✅ | ✅ 仅限本班 | ✅ 仅自己 |
| 班级管理（增改查） | ✅ | ❌ | ❌ |
| 老师管理 | ✅ | ❌ | ❌ |
| 系统统计报表 | ✅ | ✅ 仅限本班 | ❌ |
| 个人中心修改密码 | ✅ | ✅ | ✅ |

> 说明：当前阶段权限可在程序层硬编码控制，后续迭代时接入 `roles` + `permissions` 表做动态配置。

---

## 六、与《需求.md》的功能对照

| 需求功能 | 涉及表 | 查询/操作方式 |
|----------|--------|--------------|
| 学生信息增改查 | students + users | CRUD，管理员查全部，老师查本班 |
| 成绩录入与管理 | scores | 老师录入，学生仅查看自己 |
| 就业信息管理 | employments | 管理员/老师查本班，学生查自己 |
| 班级管理 | classes + teachers | 管理员操作 |
| 老师管理 | teachers + users | 管理员操作 |
| 超30岁学员查询 | students | WHERE age > 30 |
| 班级人数/性别统计 | students + classes | GROUP BY class_id |
| 每次考试80分以上 | scores | HAVING MIN(score) >= 80 |
| 两次以上不及格 | scores | WHERE score < 60 GROUP BY student_id HAVING COUNT >= 2 |
| 班级平均分排序 | scores + students + classes | GROUP BY class_id, exam_seq ORDER BY AVG |
| 就业薪资Top5 | employments + students | ORDER BY salary DESC LIMIT 5 |
| 就业时长统计 | employments | offer_date - open_date |
| 班级平均就业时长 | employments + students + classes | GROUP BY class_id |
| 用户登录认证 | users + roles | username + password 校验 |

---

## 七、扩展预留

| 扩展方向 | 预留点 | 当前状态 |
|----------|--------|---------|
| 菜单/按钮级权限 | roles + permissions + role_permission 关联表 | 后续可补 |
| 操作日志 | operation_logs 表 | 后续可补 |
| 成绩细分科目 | scores 增加 subject 字段 | 当前按考核序次，后续可加 |
| 一个学生多条就业记录 | employments 去掉 UNIQUE 约束 | 如需可改 |
| 学生签到/考勤 | 新增 attendance 表 | 后续可补 |
| 通知公告 | 新增 announcements 表 | 后续可补 |

---

## 八、待确认事项（需要你拍板）

### 1. 数据库选型
- **A. MySQL 8.0**（推荐）：与需求文档一致，生产首选，团队熟悉度高
- **B. PostgreSQL 15+**：功能更强，JSON/数组类型友好，但团队可能需要学习成本
- **C. 先 SQLite 跑通，后期迁移**：零配置，适合单人开发，但迁移有脚本成本

### 2. 就业表是否一对一
- **A. 一对一**（推荐）：一个学生一条就业记录，简单直观，符合当前需求
- **B. 一对多**：一个学生可有多段就业经历（跳槽记录），需要关联表

### 3. 冗余字段处理
- **A. 去冗余**（推荐）：就业表去掉 student_name / student_class，查询时 JOIN，数据一致性好
- **B. 保留冗余**：就业表保留姓名/班级冗余字段，查询快但需触发器/应用层维护一致性

### 4. 学生账号是否默认开通
- **A. 录入学生时自动创建 users 账号**（推荐）：学生学号即用户名，初始密码随机生成/身份证后6位，首次登录强制修改
- **B. 学生账号暂不创建**：当前阶段只有管理员和老师能登录，学生功能后续迭代时再开账号

### 5. 管理员账号设计
- **A. 独立 admin 账号**（推荐）：users.user_type='admin'，ref_id 为空，拥有全部权限
- **B. 由老师兼任管理员**：某个 teacher 标记为 is_admin=1，减少账号体系复杂度

---

## 九、实施计划（确认后立即执行）

| 阶段 | 内容 | 预计时间 |
|------|------|---------|
| P1 建库建表 | 创建数据库 + 9张表 + 索引 + 约束 + 初始角色数据 | 1 天 |
| P2 数据迁移 | 把现有 SQLite 测试数据导入新库，补全 users 关联 | 半天 |
| P3 SQLAlchemy 模型重构 | 重写 ORM 模型，建立 users/teachers/students 关联关系 | 1 天 |
| P4 登录接口 | JWT / Session 登录认证，根据角色返回不同权限 | 1 天 |
| P5 Agent 适配 | 更新 Service 层，确保统计接口正确，鉴权透传 | 半天 |

---

**请回复确认以上 5 个决策点，或告诉我哪些需要调整。**
