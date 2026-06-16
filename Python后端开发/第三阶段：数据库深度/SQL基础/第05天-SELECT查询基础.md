# 第 5 天：SELECT 查询基础

## 学习目标

- 掌握 SELECT 基本语法
- 学会使用 WHERE 条件过滤
- 掌握 ORDER BY 排序
- 学会 LIMIT 和 OFFSET 分页

---

## 1. SELECT 基础

### 基本语法

```sql
-- 查询所有列
SELECT * FROM users;

-- 查询指定列
SELECT username, email FROM users;

-- 带别名的查询
SELECT username AS "用户名", email AS "邮箱" FROM users;
```

### 列别名

```sql
-- 使用 AS 指定别名
SELECT
    username AS "用户名",
    email AS "邮箱",
    age AS "年龄"
FROM users;

-- 不使用 AS
SELECT
    username "用户名",
    email "邮箱"
FROM users;

-- 表达式别名
SELECT
    username,
    price * 1.1 AS "含税价格"
FROM products;

-- PostgreSQL 支持中文别名
SELECT username AS 用户名 FROM users;
```

### 去重查询

```sql
-- DISTINCT 去重
SELECT DISTINCT category FROM products;

-- 多字段去重
SELECT DISTINCT category, status FROM products;

-- 带聚合的去重
SELECT COUNT(DISTINCT category) FROM products;
```

---

## 2. WHERE 条件过滤

### 比较运算符

```sql
-- 基本比较
SELECT * FROM products WHERE price > 500;
SELECT * FROM products WHERE price >= 500;
SELECT * FROM products WHERE price < 500;
SELECT * FROM products WHERE price <= 500;
SELECT * FROM products WHERE price = 999.99;
SELECT * FROM products WHERE price != 999.99;  -- 不等于
SELECT * FROM products WHERE price <> 999.99;  -- 不等于（标准）
```

### 逻辑运算符

```sql
-- AND 逻辑与
SELECT * FROM products WHERE price > 500 AND stock > 0;

-- OR 逻辑或
SELECT * FROM products WHERE category = 'electronics' OR category = 'books';

-- NOT 逻辑非
SELECT * FROM products WHERE NOT status = 'inactive';

-- 组合逻辑
SELECT * FROM products
WHERE (price > 500 AND stock > 0)
   OR (category = 'electronics' AND status = 'active');

-- 优先级：NOT > AND > OR
```

### BETWEEN 和 IN

```sql
-- BETWEEN 范围查询（包含边界）
SELECT * FROM products WHERE price BETWEEN 100 AND 500;
-- 等价于：WHERE price >= 100 AND price <= 500

-- NOT BETWEEN
SELECT * FROM products WHERE price NOT BETWEEN 100 AND 500;

-- IN 指定值列表
SELECT * FROM products WHERE category IN ('electronics', 'books', 'food');

-- NOT IN
SELECT * FROM products WHERE category NOT IN ('obsolete', 'discontinued');

-- IN 与子查询
SELECT * FROM products WHERE category IN (
    SELECT category FROM categories WHERE is_active = TRUE
);
```

### LIKE 模糊匹配

```sql
-- % 匹配任意字符
SELECT * FROM users WHERE username LIKE 'a%';        -- 以 a 开头
SELECT * FROM users WHERE username LIKE '%a%';        -- 包含 a
SELECT * FROM users WHERE username LIKE '%a';         -- 以 a 结尾

-- _ 匹配单个字符
SELECT * FROM users WHERE username LIKE '_lice';      -- 第2-5个字符任意
SELECT * FROM users WHERE username LIKE '__ce';       -- 4个字符，末尾 ce

-- NOT LIKE
SELECT * FROM users WHERE username NOT LIKE '%admin%';

-- ILIKE（PostgreSQL，不区分大小写）
SELECT * FROM users WHERE username ILIKE '%alice%';

-- MySQL 不区分大小写（默认）
SELECT * FROM users WHERE username LIKE '%ALICE%';  -- 能匹配到 alice
```

### NULL 判断

```sql
-- IS NULL 判断为空
SELECT * FROM users WHERE email IS NULL;

-- IS NOT NULL 判断非空
SELECT * FROM users WHERE email IS NOT NULL;

-- 常见错误：NULL 不能用 = 判断
-- ❌ SELECT * FROM users WHERE email = NULL;  -- 永远返回空
-- ✅ SELECT * FROM users WHERE email IS NULL;
```

---

## 3. ORDER BY 排序

### 单字段排序

```sql
-- 升序排序（ASC，默认）
SELECT * FROM products ORDER BY price ASC;
SELECT * FROM products ORDER BY price;  -- 省略 ASC

-- 降序排序（DESC）
SELECT * FROM products ORDER BY price DESC;

-- 按字符串排序
SELECT * FROM users ORDER BY username;
```

### 多字段排序

```sql
-- 先按第一个字段，相同则按第二个字段
SELECT * FROM orders ORDER BY user_id, created_at DESC;

-- 混合排序
SELECT * FROM products
ORDER BY
    category ASC,
    price DESC;
```

### 表达式排序

```sql
-- 按计算表达式排序
SELECT * FROM products ORDER BY price * quantity DESC;

-- 按聚合结果排序
SELECT
    category,
    COUNT(*) AS product_count,
    AVG(price) AS avg_price
FROM products
GROUP BY category
ORDER BY avg_price DESC;
```

### NULL 排序位置

```sql
-- NULL 值排在前面（默认 ASC 时）
SELECT * FROM products ORDER BY discount ASC;  -- NULL 最前

-- NULL 值排在后面
SELECT * FROM products ORDER BY discount ASC NULLS LAST;

-- NULL 值排在前面（DESC 时）
SELECT * FROM products ORDER BY discount DESC NULLS FIRST;
```

---

## 4. LIMIT 和 OFFSET

### 分页查询

```sql
-- LIMIT 限制返回行数
SELECT * FROM products ORDER BY price DESC LIMIT 10;

-- OFFSET 跳过行数
SELECT * FROM products ORDER BY price DESC LIMIT 10 OFFSET 20;

-- 分页查询公式
-- 第 N 页，每页 M 条
-- LIMIT M OFFSET (N-1) * M
```

### 分页示例

```sql
-- 第1页，每页10条
SELECT * FROM products ORDER BY id LIMIT 10 OFFSET 0;

-- 第2页，每页10条
SELECT * FROM products ORDER BY id LIMIT 10 OFFSET 10;

-- 第3页，每页10条
SELECT * FROM products ORDER BY id LIMIT 10 OFFSET 20;

-- PostgreSQL 简写语法
SELECT * FROM products ORDER BY id LIMIT 10, 20;  -- LIMIT 20 OFFSET 10
```

### LIMIT 的变体

```sql
-- MySQL 语法（位置不同）
SELECT * FROM products LIMIT 10 OFFSET 20;  -- 先 LIMIT 后 OFFSET

-- PostgreSQL FETCH（SQL 标准）
SELECT * FROM products ORDER BY id LIMIT 10 FETCH FIRST 10 ROWS ONLY;

-- SQLite
SELECT * FROM products ORDER BY id LIMIT 10;
```

### 获取最大/最小值

```sql
-- 价格最高的产品
SELECT * FROM products ORDER BY price DESC LIMIT 1;

-- 价格最低的3个产品
SELECT * FROM products ORDER BY price ASC LIMIT 3;

-- 每个分类最贵的产品
SELECT DISTINCT ON (category) * FROM products
ORDER BY category, price DESC;
```

---

## 5. 实战练习

### 练习 1：用户查询

```sql
-- 创建测试数据
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100),
    age INTEGER,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (username, email, age, status) VALUES
    ('alice', 'alice@example.com', 25, 'active'),
    ('bob', 'bob@example.com', 30, 'active'),
    ('charlie', 'charlie@example.com', 28, 'inactive'),
    ('david', 'david@example.com', 35, 'active'),
    ('eve', 'eve@example.com', NULL, 'active');

-- 查询活跃用户
SELECT * FROM users WHERE status = 'active';

-- 查询18-30岁用户
SELECT * FROM users WHERE age BETWEEN 18 AND 30;

-- 查询未填写年龄的用户
SELECT * FROM users WHERE age IS NULL;

-- 查询用户名包含 'a' 的用户（不区分大小写）
SELECT * FROM users WHERE username LIKE '%a%';

-- 按年龄降序排列前3个用户
SELECT * FROM users WHERE status = 'active' ORDER BY age DESC LIMIT 3;
```

### 练习 2：商品查询

```sql
-- 查询价格区间商品
SELECT * FROM products
WHERE price BETWEEN 100 AND 1000
ORDER BY price ASC;

-- 查询特定分类商品
SELECT * FROM products
WHERE category IN ('electronics', 'books', 'food')
ORDER BY category, price DESC;

-- 查询商品（分页）
SELECT * FROM products
WHERE status = 'active'
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;

-- 获取第2页
SELECT * FROM products
WHERE status = 'active'
ORDER BY created_at DESC
LIMIT 20 OFFSET 20;
```

---

## 今日总结

- [ ] `SELECT column AS alias` 指定列查询并起别名
- [ ] `DISTINCT` 去除重复行
- [ ] `WHERE` 条件过滤：比较、逻辑、BETWEEN、IN、LIKE、IS NULL
- [ ] `LIKE '%_%'` 模糊匹配，`%` 任意字符，`_` 单个字符
- [ ] `ORDER BY column [ASC|DESC]` 排序
- [ ] `NULLS LAST/FIRST` 控制 NULL 排序位置
- [ ] `LIMIT n OFFSET m` 分页查询
- [ ] 多字段排序：`ORDER BY field1, field2 DESC`

---

*第 5 天 / 330 天*
*Python 后端 - SQL SELECT 查询基础*