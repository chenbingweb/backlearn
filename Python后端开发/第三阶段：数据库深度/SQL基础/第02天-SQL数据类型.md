# 第 2 天：SQL 数据类型

## 学习目标

- 掌握数值类型的分类和使用
- 掌握字符串类型的分类和使用
- 掌握日期时间类型的分类和使用
- 理解 JSON 和布尔类型

---

## 1. 数值类型

### 整数类型

| 类型 | 存储大小 | 范围 | 适用场景 |
|------|----------|------|----------|
| TINYINT | 1 字节 | -128 ~ 127 / 0 ~ 255 | 状态码、布尔 |
| SMALLINT | 2 字节 | -32768 ~ 32767 | 小数量 |
| INT/INTEGER | 4 字节 | -21亿 ~ 21亿 | 主键、计数 |
| BIGINT | 8 字节 | -922亿亿 ~ 922亿亿 | 大数据量 |

```sql
-- PostgreSQL
CREATE TABLE examples (
    id SERIAL PRIMARY KEY,          -- 自增主键
    tiny TINYINT,                    -- 0-255
    small SMALLINT,                  -- -32768 ~ 32767
    regular INTEGER,                -- -21亿 ~ 21亿
    big BIGINT                      -- 大数字
);

-- MySQL
CREATE TABLE examples (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tiny TINYINT,
    small SMALLINT,
    regular INT,
    big BIGINT
);
```

### 浮点数类型

| 类型 | 存储大小 | 精度 | 适用场景 |
|------|----------|------|----------|
| FLOAT/DOUBLE | 4/8 字节 | 单/双精度 | 科学计算 |
| DECIMAL/NUMERIC | 可变 | 精确数值 | 货币金额 |

```sql
-- FLOAT (单精度)
CREATE TABLE measurements (
    id SERIAL PRIMARY KEY,
    temperature FLOAT,
    pressure DOUBLE
);

-- DECIMAL (精确数值，推荐用于货币)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    price DECIMAL(10, 2),          -- 总共10位，2位小数
    discount DECIMAL(5, 2)        -- 最多999.99
);

-- 货币计算示例
INSERT INTO products (name, price) VALUES
    ('iPhone', 999.99),
    ('MacBook', 1999.99);

-- 计算总金额（精确计算）
SELECT SUM(price) FROM products;  -- 2999.98
```

### 数值类型选择建议

```sql
-- ❌ 错误：使用 FLOAT 存储货币
CREATE TABLE bad_example (
    price FLOAT
);
-- 计算 0.1 + 0.2 可能得到 0.30000000000000004

-- ✅ 正确：使用 DECIMAL 存储货币
CREATE TABLE good_example (
    price DECIMAL(10, 2)
);
-- 0.1 + 0.2 = 0.30
```

---

## 2. 字符串类型

### 定长字符串 CHAR

```sql
-- CHAR(n) - 固定长度，不足用空格填充
CREATE TABLE codes (
    code CHAR(6) NOT NULL          -- 始终占用6个字符
);

-- 插入 '123' 会存储为 '123   '（补空格）
INSERT INTO codes VALUES ('123');

-- 特点
-- ✅ 存储固定长度数据（如邮编、身份证号）
-- ✅ 性能略高（固定长度便于索引）
-- ❌ 浪费空间
```

### 变长字符串 VARCHAR

```sql
-- VARCHAR(n) - 最大长度 n，可变长度
CREATE TABLE users (
    username VARCHAR(50) NOT NULL,  -- 最大50字符
    email VARCHAR(100),
    bio VARCHAR(500)               -- 个人简介
);

-- 插入 'alice' 实际存储为 'alice'（不补空格）
INSERT INTO users (username, email, bio) VALUES
    ('alice', 'alice@example.com', 'Hello world');

-- 特点
-- ✅ 节省空间
-- ✅ 实际长度内灵活存储
-- ✅ 最常用的字符串类型
```

### 文本类型 TEXT

```sql
-- PostgreSQL
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200),
    content TEXT,                   -- 无长度限制
    summary TEXT
);

-- MySQL
CREATE TABLE articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200),
    content TEXT,                  -- 最大65535字节
    summary MEDIUMTEXT             -- 最大1.67亿字节
);

-- 特点
-- ✅ 存储大段文本
-- ❌ 无法创建索引（需要全文索引）
```

### 字符串类型对比

| 类型 | 最大长度 | 存储方式 | 适用场景 |
|------|----------|----------|----------|
| CHAR(n) | n | 定长 | 代码、邮编、身份证 |
| VARCHAR(n) | n | 变长 | 姓名、邮箱、标题 |
| TEXT | 65535+ | 变长 | 文章内容、评论 |

```sql
-- 最佳实践
CREATE TABLE best_practices (
    -- 固定格式用 CHAR
    country_code CHAR(2),           -- 'CN', 'US'
    zip_code CHAR(6),               -- '100000'

    -- 可变长度用 VARCHAR
    username VARCHAR(50),
    email VARCHAR(100),
    url VARCHAR(500),

    -- 大文本用 TEXT
    description TEXT,
    article_content TEXT
);
```

---

## 3. 日期时间类型

### DATE 和 TIME

```sql
-- DATE - 日期（年-月-日）
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    event_name VARCHAR(100),
    event_date DATE,
    start_time TIME,
    end_time TIME
);

INSERT INTO events (event_name, event_date, start_time) VALUES
    ('生日派对', '2024-01-15', '18:30:00'),
    ('会议', '2024-02-01', '09:00:00');
```

### DATETIME 和 TIMESTAMP

```sql
-- DATETIME - 日期时间（无时区）
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_no VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    shipped_at DATETIME
);

-- TIMESTAMP - 时间戳（有时区，自动更新）
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PostgreSQL 的 TIMESTAMP 变体
created_at TIMESTAMP WITH TIME ZONE,  -- 带时区
created_at TIMESTAMP WITHOUT TIME ZONE  -- 不带时区
```

### 日期时间类型对比

| 类型 | 范围 | 精度 | 时区 | 适用场景 |
|------|------|------|------|----------|
| DATE | 0001-01-01 ~ 9999-12-31 | 1天 | 无 | 生日、纪念日 |
| TIME | 00:00:00 ~ 23:59:59 | 1秒 | 无 | 营业时间 |
| DATETIME | 1000-01-01 ~ 9999-12-31 | 1秒 | 无 | 一般场景 |
| TIMESTAMP | 1970-01-01 ~ 2038-01-19 | 1秒 | 有 | 记录创建/修改时间 |

### 日期函数

```sql
-- 获取当前日期时间
SELECT CURRENT_DATE;       -- 2024-01-15
SELECT CURRENT_TIME;       -- 14:30:00
SELECT NOW();              -- 2024-01-15 14:30:00
SELECT CURRENT_TIMESTAMP; -- 2024-01-15 14:30:00

-- PostgreSQL
SELECT CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Shanghai';

-- 提取部分
SELECT EXTRACT(YEAR FROM created_at) FROM orders;
SELECT EXTRACT(MONTH FROM created_at) FROM orders;
SELECT EXTRACT(DAY FROM created_at) FROM orders;

-- MySQL
SELECT YEAR(created_at), MONTH(created_at), DAY(created_at) FROM orders;
SELECT DATE_FORMAT(created_at, '%Y-%m-%d') FROM orders;
```

---

## 4. 其他常用类型

### 布尔类型 BOOLEAN

```sql
-- BOOLEAN - true/false/null
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE
);

-- 插入布尔值
INSERT INTO users (username, is_active, is_verified) VALUES
    ('alice', TRUE, TRUE),
    ('bob', TRUE, FALSE),
    ('charlie', FALSE, FALSE);

-- 查询布尔值
SELECT * FROM users WHERE is_active = TRUE;
SELECT * FROM users WHERE is_verified = FALSE;

-- PostgreSQL 也接受
INSERT INTO users (username, is_active) VALUES
    ('david', 'true'),
    ('eve', 'yes'),
    ('frank', 1);
```

### JSON 类型

```sql
-- PostgreSQL JSON/JSONB
CREATE TABLE configurations (
    id SERIAL PRIMARY KEY,
    config_name VARCHAR(50),
    settings JSON,
    metadata JSONB                   -- JSONB 更适合索引
);

INSERT INTO configurations (config_name, settings) VALUES
    ('app_config', '{"theme": "dark", "language": "zh"}'),
    ('user_prefs', '{"notifications": true, "email": "a@b.com"}');

-- 查询 JSON 字段
SELECT settings->'theme' FROM configurations WHERE config_name = 'app_config';
-- 结果: "dark"

SELECT settings->>'theme' FROM configurations;  -- 去除引号
-- 结果: dark

-- 修改 JSON
UPDATE configurations
SET settings = settings || '{"notifications": false}'
WHERE config_name = 'app_config';

-- MySQL JSON
CREATE TABLE configurations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    settings JSON
);

INSERT INTO configurations VALUES (1, '{"theme": "dark"}');

SELECT settings->>'$.theme' FROM configurations;
```

### 数组类型（PostgreSQL）

```sql
-- PostgreSQL 支持数组类型
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    courses TEXT[],
    grades INTEGER[]
);

INSERT INTO students (name, courses, grades) VALUES
    ('Alice', ARRAY['Math', 'English', 'Science'], ARRAY[95, 88, 92]),
    ('Bob', ARRAY['Math', 'Art'], ARRAY[85, 90]);

-- 查询数组
SELECT * FROM students WHERE 'Math' = ANY(courses);
SELECT * FROM students WHERE courses[1] = 'Math';
```

---

## 5. NULL 与默认值

### NULL 概念

```sql
-- NULL 表示缺失或未知的数据
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,     -- 不能为 NULL
    price DECIMAL(10, 2),           -- 可以为 NULL
    description TEXT,               -- 可以为 NULL
    discount DECIMAL(5, 2) DEFAULT NULL  -- 显式允许 NULL
);

-- NULL 特性
-- ❌ NULL = NULL 不成立（需要使用 IS NULL）
-- ✅ NULL 不等于任何值，包括自身
-- ✅ 聚合函数通常忽略 NULL

-- 正确判断 NULL
SELECT * FROM products WHERE price IS NULL;
SELECT * FROM products WHERE price IS NOT NULL;

-- ❌ 错误写法
SELECT * FROM products WHERE price = NULL;  -- 永远不会匹配
```

### 默认值

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    score INTEGER DEFAULT 0
);

-- 使用 DEFAULT 关键字
INSERT INTO users (username) VALUES ('alice');
-- 等价于
INSERT INTO users (username, status, created_at, is_active, score)
VALUES ('alice', 'active', CURRENT_TIMESTAMP, TRUE, 0);

-- 使用表达式作为默认值
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER DEFAULT (SELECT MAX(id) FROM users)
);
```

---

## 实战练习

### 练习 1：设计员工表

```sql
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    employee_no VARCHAR(20) UNIQUE NOT NULL,  -- 员工编号
    name VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    department VARCHAR(50),
    position VARCHAR(50),
    salary DECIMAL(10, 2),
    hire_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO employees (employee_no, name, email, department, salary, hire_date) VALUES
    ('EMP001', '张三', 'zhangsan@example.com', '技术部', 15000.00, '2020-01-15'),
    ('EMP002', '李四', 'lisi@example.com', '市场部', 12000.00, '2021-03-20'),
    ('EMP003', '王五', 'wangwu@example.com', '技术部', 18000.00, '2019-06-01');
```

### 练习 2：设计商品表

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_no VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2),
    stock INTEGER DEFAULT 0,
    description TEXT,
    images TEXT[],
    specs JSON,                     -- 规格参数
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO products (product_no, name, category, price, stock, specs) VALUES
    ('PROD001', 'iPhone 15', '手机', 5999.00, 100, '{"color": "黑色", "storage": "128GB"}'),
    ('PROD002', 'MacBook Pro', '电脑', 12999.00, 50, '{"color": "银色", "cpu": "M3"}'),
    ('PROD003', 'AirPods Pro', '耳机', 1899.00, 200, '{"color": "白色", "noise_cancellation": true}');
```

---

## 今日总结

- [ ] 整数类型：TINYINT、SMALLINT、INT、BIGINT，主键用 INT/BIGINT
- [ ] 浮点类型：FLOAT/DOUBLE（科学计算）、DECIMAL（货币）
- [ ] 字符串类型：CHAR（固定）、VARCHAR（可变）、TEXT（大文本）
- [ ] 日期时间：DATE、TIME、DATETIME、TIMESTAMP（带时区）
- [ ] 布尔类型：存储 TRUE/FALSE，适合状态标记
- [ ] JSON 类型：存储半结构化数据，PostgreSQL 的 JSONB 支持索引
- [ ] NULL 表示缺失值，需要用 `IS NULL` 判断
- [ ] DEFAULT 设置默认值，简化插入操作

---

*第 2 天 / 330 天*
*Python 后端 - SQL 数据类型*