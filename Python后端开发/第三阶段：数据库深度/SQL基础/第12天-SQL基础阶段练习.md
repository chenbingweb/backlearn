# 第 12 天：SQL 基础阶段练习

## 学习目标

- 整合前11天的知识
- 完成完整的数据库设计
- 实践复杂查询
- 掌握综合应用

---

## 项目：学生成绩管理系统

### 需求分析

```
1. 学生信息管理
2. 课程管理
3. 成绩录入
4. 成绩查询统计
```

---

## 1. 创建数据库和表

```sql
-- 创建数据库
CREATE DATABASE student_system;
\c student_system

-- 学生表
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    student_no VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    gender VARCHAR(10),
    birth_date DATE,
    class_name VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 课程表
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    credits DECIMAL(3, 1),
    department VARCHAR(50),
    teacher_name VARCHAR(50),
    max_students INTEGER DEFAULT 50,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 选课表（成绩表）
CREATE TABLE enrollments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    course_id INTEGER NOT NULL REFERENCES courses(id),
    semester VARCHAR(20) NOT NULL,
    score DECIMAL(5, 2),
    grade VARCHAR(2),
    status VARCHAR(20) DEFAULT 'enrolled',
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(student_id, course_id, semester)
);

-- 创建索引
CREATE INDEX idx_students_class ON students(class_name);
CREATE INDEX idx_students_no ON students(student_no);
CREATE INDEX idx_courses_code ON courses(course_code);
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);
CREATE INDEX idx_enrollments_semester ON enrollments(semester);
```

---

## 2. 插入测试数据

```sql
-- 插入学生数据
INSERT INTO students (student_no, name, gender, birth_date, class_name, email) VALUES
    ('S2024001', '张三', '男', '2005-03-15', '计算机1班', 'zhangsan@example.com'),
    ('S2024002', '李四', '女', '2005-06-20', '计算机1班', 'lisi@example.com'),
    ('S2024003', '王五', '男', '2005-09-10', '计算机1班', 'wangwu@example.com'),
    ('S2024004', '赵六', '女', '2005-01-05', '计算机2班', 'zhaoliu@example.com'),
    ('S2024005', '钱七', '男', '2004-11-30', '计算机2班', 'qianqi@example.com'),
    ('S2024006', '孙八', '女', '2005-07-22', '计算机2班', 'sunba@example.com'),
    ('S2024007', '周九', '男', '2004-05-18', '计算机3班', 'zhoujiu@example.com'),
    ('S2024008', '吴十', '女', '2005-12-25', '计算机3班', 'wushi@example.com');

-- 插入课程数据
INSERT INTO courses (course_code, name, credits, department, teacher_name, max_students) VALUES
    ('CS101', '数据结构', 4.0, '计算机学院', '陈教授', 100),
    ('CS102', '算法设计', 3.5, '计算机学院', '王教授', 80),
    ('MA101', '高等数学', 5.0, '数学学院', '刘教授', 150),
    ('EN101', '大学英语', 2.0, '外语学院', '张教授', 120),
    ('PE101', '体育', 1.0, '体育学院', '赵教授', 200);

-- 插入选课数据
INSERT INTO enrollments (student_id, course_id, semester, score, grade, status) VALUES
    -- 2024学年第一学期
    (1, 1, '2024-1', 85, 'B', 'completed'),
    (1, 2, '2024-1', 78, 'C', 'completed'),
    (1, 3, '2024-1', 92, 'A', 'completed'),
    (2, 1, '2024-1', 88, 'B', 'completed'),
    (2, 3, '2024-1', 95, 'A', 'completed'),
    (2, 4, '2024-1', 82, 'B', 'completed'),
    (3, 1, '2024-1', 72, 'C', 'completed'),
    (3, 2, '2024-1', 68, 'D', 'completed'),
    (3, 4, '2024-1', 90, 'A', 'completed'),
    (4, 1, '2024-1', 91, 'A', 'completed'),
    (4, 2, '2024-1', 85, 'B', 'completed'),
    (4, 3, '2024-1', 88, 'B', 'completed'),
    (5, 3, '2024-1', 75, 'C', 'completed'),
    (5, 4, '2024-1', 80, 'B', 'completed'),
    (5, 5, '2024-1', 95, 'A', 'completed'),
    -- 2024学年第二学期（进行中）
    (1, 4, '2024-2', NULL, NULL, 'enrolled'),
    (1, 5, '2024-2', NULL, NULL, 'enrolled'),
    (2, 1, '2024-2', NULL, NULL, 'enrolled'),
    (3, 2, '2024-2', NULL, NULL, 'enrolled'),
    (4, 1, '2024-2', NULL, NULL, 'enrolled');
```

---

## 3. 基础查询练习

### 学生信息查询

```sql
-- 查询所有学生
SELECT * FROM students WHERE is_active = TRUE;

-- 按学号查询学生
SELECT * FROM students WHERE student_no = 'S2024001';

-- 查询班级人数
SELECT class_name, COUNT(*) AS student_count
FROM students
GROUP BY class_name
ORDER BY class_name;
```

### 成绩查询

```sql
-- 查询学生成绩
SELECT
    s.student_no,
    s.name,
    c.name AS course_name,
    e.semester,
    e.score,
    e.grade
FROM enrollments e
JOIN students s ON e.student_id = s.id
JOIN courses c ON e.course_id = c.id
ORDER BY s.student_no, e.semester;
```

---

## 4. 聚合查询练习

### 成绩统计

```sql
-- 统计每个学生的平均分
SELECT
    s.student_no,
    s.name,
    s.class_name,
    COUNT(e.id) AS course_count,
    ROUND(AVG(e.score), 2) AS avg_score,
    MAX(e.score) AS max_score,
    MIN(e.score) AS min_score
FROM students s
JOIN enrollments e ON s.id = e.student_id
WHERE e.status = 'completed' AND e.score IS NOT NULL
GROUP BY s.id, s.student_no, s.name, s.class_name
ORDER BY avg_score DESC;
```

### 课程统计

```sql
-- 统计每门课程的平均分、最高分、最低分
SELECT
    c.course_code,
    c.name,
    COUNT(e.id) AS student_count,
    ROUND(AVG(e.score), 2) AS avg_score,
    MAX(e.score) AS max_score,
    MIN(e.score) AS min_score
FROM courses c
JOIN enrollments e ON c.id = e.course_id
WHERE e.status = 'completed' AND e.score IS NOT NULL
GROUP BY c.id, c.course_code, c.name
ORDER BY avg_score DESC;
```

### 班级排名

```sql
-- 班级平均成绩排名
SELECT
    s.class_name,
    COUNT(DISTINCT s.id) AS student_count,
    ROUND(AVG(e.score), 2) AS class_avg_score
FROM students s
JOIN enrollments e ON s.id = e.student_id
WHERE e.status = 'completed' AND e.score IS NOT NULL
GROUP BY s.class_name
ORDER BY class_avg_score DESC;
```

---

## 5. 复杂查询练习

### TOP N 查询

```sql
-- 每班成绩最好的学生
SELECT *
FROM (
    SELECT
        s.student_no,
        s.name,
        s.class_name,
        ROUND(AVG(e.score), 2) AS avg_score,
        RANK() OVER (PARTITION BY s.class_name ORDER BY AVG(e.score) DESC) AS class_rank
    FROM students s
    JOIN enrollments e ON s.id = e.student_id
    WHERE e.status = 'completed' AND e.score IS NOT NULL
    GROUP BY s.id, s.student_no, s.name, s.class_name
) ranked
WHERE class_rank <= 1;
```

### 不及格统计

```sql
-- 找出不及格学生及课程
SELECT
    s.student_no,
    s.name,
    s.class_name,
    c.name AS course_name,
    e.score,
    CASE
        WHEN e.score < 60 THEN '不及格'
        WHEN e.score < 70 THEN '及格'
        WHEN e.score < 85 THEN '良好'
        ELSE '优秀'
    END AS score_level
FROM enrollments e
JOIN students s ON e.student_id = s.id
JOIN courses c ON e.course_id = c.id
WHERE e.status = 'completed' AND e.score < 70
ORDER BY e.score ASC;
```

### 学分统计

```sql
-- 学生已获得学分
SELECT
    s.student_no,
    s.name,
    SUM(c.credits) AS total_credits
FROM students s
JOIN enrollments e ON s.id = e.student_id
JOIN courses c ON e.course_id = c.id
WHERE e.status = 'completed'
  AND e.score >= 60
GROUP BY s.id, s.student_no, s.name
ORDER BY total_credits DESC;
```

---

## 6. 视图创建练习

### 学生成绩视图

```sql
CREATE OR REPLACE VIEW student_scores AS
SELECT
    s.id AS student_id,
    s.student_no,
    s.name,
    s.class_name,
    c.id AS course_id,
    c.course_code,
    c.name AS course_name,
    c.credits,
    e.semester,
    e.score,
    e.grade,
    CASE
        WHEN e.score >= 90 THEN 'A'
        WHEN e.score >= 80 THEN 'B'
        WHEN e.score >= 70 THEN 'C'
        WHEN e.score >= 60 THEN 'D'
        WHEN e.score IS NOT NULL THEN 'F'
        ELSE NULL
    END AS grade_level
FROM students s
JOIN enrollments e ON s.id = e.student_id
JOIN courses c ON e.course_id = c.id;

-- 查询视图
SELECT * FROM student_scores WHERE student_no = 'S2024001';
```

### 学生统计视图

```sql
CREATE OR REPLACE VIEW student_statistics AS
SELECT
    s.id,
    s.student_no,
    s.name,
    s.class_name,
    COUNT(e.id) AS total_courses,
    SUM(c.credits) AS total_credits,
    ROUND(AVG(e.score), 2) AS avg_score,
    SUM(CASE WHEN e.score >= 60 THEN c.credits ELSE 0 END) AS earned_credits
FROM students s
JOIN enrollments e ON s.id = e.student_id
JOIN courses c ON e.course_id = c.id
WHERE e.status = 'completed'
GROUP BY s.id, s.student_no, s.name, s.class_name;

-- 查询优秀学生
SELECT * FROM student_statistics WHERE avg_score >= 90 ORDER BY avg_score DESC;
```

---

## 7. 综合应用

### 完整成绩单报表

```sql
-- 生成学生成绩单
SELECT
    s.student_no AS "学号",
    s.name AS "姓名",
    s.class_name AS "班级",
    COALESCE(SUM(c.credits), 0) AS "总学分",
    COUNT(e.id) AS "选课数",
    ROUND(AVG(e.score), 2) AS "平均分",
    MAX(e.score) AS "最高分",
    MIN(e.score) AS "最低分",
    STRING_AGG(
        c.name || ': ' || COALESCE(e.score::TEXT, 'N/A'),
        ', '
        ORDER BY e.semester
    ) AS "成绩详情"
FROM students s
LEFT JOIN enrollments e ON s.id = e.student_id
LEFT JOIN courses c ON e.course_id = c.id
GROUP BY s.id, s.student_no, s.name, s.class_name
ORDER BY s.student_no;
```

---

## 今日总结

通过本阶段学习，掌握了：

- [ ] 数据库、表、字段的创建和管理
- [ ] 各种数据类型的正确使用
- [ ] INSERT/UPDATE/DELETE 数据操作
- [ ] SELECT 查询及 WHERE、ORDER BY、LIMIT
- [ ] 聚合函数和 GROUP BY
- [ ] 多表连接 JOIN
- [ ] 子查询的嵌套使用
- [ ] 常用字符串、数值、日期函数
- [ ] 索引的作用和创建
- [ ] 视图的创建和使用

---

## SQL 基础阶段回顾

| 天数 | 主题 | 核心内容 |
|------|------|----------|
| 1 | SQL概述与数据库概念 | 数据库、关系型、SQL分类 |
| 2 | SQL数据类型 | 数值、字符串、日期、布尔、JSON |
| 3 | 数据库与表操作 | DDL、约束（主键、外键、唯一、检查） |
| 4 | INSERT语句 | 插入、更新、删除 |
| 5 | SELECT查询基础 | WHERE、ORDER BY、LIMIT |
| 6 | 聚合函数与分组 | COUNT、SUM、AVG、GROUP BY、HAVING |
| 7 | JOIN表连接 | INNER、LEFT、RIGHT、FULL JOIN |
| 8 | 子查询 | 标量、列、表子查询、EXISTS |
| 9 | 常用函数 | 字符串、数值、日期、条件表达式 |
| 10 | 索引 | B-Tree、Hash、GIN、复合索引 |
| 11 | 视图 | 普通视图、物化视图、可更新视图 |
| 12 | 阶段练习 | 学生成绩管理系统 |

---

*第 12 天 / 330 天*
*Python 后端 - SQL 基础阶段练习*