# 第 7 天：JOIN 表连接

## 学习目标

- 掌握 INNER JOIN 内连接
- 学会 LEFT/RIGHT OUTER JOIN
- 理解 FULL OUTER JOIN
- 学会多表连接与自连接

---

## 1. INNER JOIN 内连接

### 基本语法

```sql
-- 连接两个表
SELECT
    users.username,
    orders.order_no,
    orders.total
FROM users
INNER JOIN orders ON users.id = orders.user_id;

-- 简写（省略 INNER）
SELECT
    users.username,
    orders.order_no,
    orders.total
FROM users
JOIN orders ON users.id = orders.user_id;
```

### 使用 USING（字段名相同时）

```sql
-- 当连接字段名相同时可以用 USING
SELECT
    username,
    order_no,
    total
FROM users
JOIN orders USING (id);  -- 等价于 ON users.id = orders.user_id
```

### 多表连接

```sql
-- 连接多个表
SELECT
    users.username,
    orders.order_no,
    products.name AS product_name,
    order_items.quantity,
    order_items.price
FROM users
JOIN orders ON users.id = orders.user_id
JOIN order_items ON orders.id = order_items.order_id
JOIN products ON order_items.product_id = products.id
WHERE orders.status = 'completed'
ORDER BY orders.created_at DESC;
```

---

## 2. OUTER JOIN 外连接

### LEFT JOIN 左连接

```sql
-- LEFT JOIN：返回左表所有行，右表无匹配则显示 NULL
SELECT
    users.username,
    orders.order_no,
    orders.total
FROM users
LEFT JOIN orders ON users.id = orders.user_id;

-- 结果：所有用户都会出现，即使没有订单
-- username | order_no | total
-- ---------+----------+------
-- alice   | ORD001   | 299.99
-- alice   | ORD002   | 199.99
-- bob     | NULL     | NULL   -- bob 没下过单
```

### RIGHT JOIN 右连接

```sql
-- RIGHT JOIN：返回右表所有行，左表无匹配则显示 NULL
SELECT
    users.username,
    orders.order_no,
    orders.total
FROM users
RIGHT JOIN orders ON users.id = orders.user_id;

-- 结果：所有订单都会出现，即使用户已删除
```

### FULL OUTER JOIN 全连接

```sql
-- FULL OUTER JOIN：返回两表所有行，无匹配则 NULL
SELECT
    users.username,
    orders.order_no,
    orders.total
FROM users
FULL OUTER JOIN orders ON users.id = orders.user_id;

-- PostgreSQL 特有
-- MySQL 不支持 FULL OUTER JOIN，可用 UNION 模拟
SELECT ... LEFT JOIN ...
UNION
SELECT ... RIGHT JOIN ... WHERE 左表.id IS NULL;
```

---

## 3. JOIN 变体

### LEFT JOIN 排除右表无匹配

```sql
-- 找出没有订单的用户
SELECT users.*
FROM users
LEFT JOIN orders ON users.id = orders.user_id
WHERE orders.id IS NULL;

-- 找出从不下单的用户
SELECT u.*
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.id IS NULL;
```

### RIGHT JOIN 排除左表无匹配

```sql
-- 找出已被删除用户的订单（如果有的话）
SELECT o.*
FROM users
RIGHT JOIN orders o ON users.id = o.user_id
WHERE users.id IS NULL;
```

### 多条件 JOIN

```sql
-- 带有多个连接条件
SELECT
    p.name,
    o.order_no
FROM products p
JOIN order_items oi ON p.id = oi.product_id
JOIN orders o ON oi.order_id = o.id
              AND o.status = 'completed'  -- 额外条件
WHERE p.category = 'electronics';
```

---

## 4. 自连接

### 自连接概念

```sql
-- 自连接：表与自身连接
-- 用于处理层次结构数据

CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    manager_id INTEGER REFERENCES employees(id)
);

INSERT INTO employees (name, manager_id) VALUES
    ('张三', NULL),           -- CEO，没有上级
    ('李四', 1),              -- 张三的下属
    ('王五', 1),              -- 张三的下属
    ('赵六', 2),              -- 李四的下属
    ('孙七', 2),              -- 李四的下属
    ('周八', 3);              -- 王五的下属
```

### 查询员工及其上级

```sql
-- 自连接：员工表 JOIN 员工表
SELECT
    e.name AS employee_name,
    m.name AS manager_name
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id
ORDER BY m.name, e.name;

-- 结果：
-- employee_name | manager_name
-- ---------------+--------------
-- 张三          | NULL
-- 李四          | 张三
-- 王五          | 张三
-- 赵六          | 李四
-- 孙七          | 李四
-- 周八          | 王五
```

### 查找所有上级/下属

```sql
-- 递归查询找所有下属（PostgreSQL）
WITH RECURSIVE subordinates AS (
    -- 基础查询：直接从属
    SELECT id, name, manager_id, 1 AS level
    FROM employees
    WHERE name = '李四'

    UNION ALL

    -- 递归查询
    SELECT e.id, e.name, e.manager_id, s.level + 1
    FROM employees e
    JOIN subordinates s ON e.manager_id = s.id
)
SELECT * FROM subordinates WHERE level > 1;
```

---

## 5. JOIN 与聚合

### JOIN 后的聚合

```sql
-- 统计每个用户的订单数量和总金额
SELECT
    u.username,
    COUNT(o.id) AS order_count,
    COALESCE(SUM(o.total), 0) AS total_amount
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed' OR o.status IS NULL
GROUP BY u.id, u.username
ORDER BY total_amount DESC;
```

### 多表聚合统计

```sql
-- 订单详细统计
SELECT
    o.order_no,
    u.username,
    COUNT(oi.id) AS item_count,
    SUM(oi.quantity) AS total_quantity,
    SUM(oi.price * oi.quantity) AS order_total
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, o.order_no, u.username
HAVING SUM(oi.price * oi.quantity) > 100
ORDER BY order_total DESC;
```

---

## 6. 实战练习

### 练习 1：完整的订单查询

```sql
-- 订单完整信息
SELECT
    o.order_no,
    u.username,
    u.email,
    p.name AS product_name,
    oi.quantity,
    oi.price,
    oi.quantity * oi.price AS subtotal,
    o.total,
    o.status,
    o.created_at
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE o.status = 'completed'
ORDER BY o.created_at DESC
LIMIT 20;
```

### 练习 2：用户消费分析

```sql
-- 用户消费排名
SELECT
    u.id,
    u.username,
    COUNT(DISTINCT o.id) AS order_count,
    COUNT(DISTINCT oi.product_id) AS product_types,
    SUM(oi.quantity) AS total_items,
    SUM(oi.price * oi.quantity) AS total_spent,
    MAX(o.created_at) AS last_order_date
FROM users u
LEFT JOIN orders o ON u.id = o.user_id AND o.status = 'completed'
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY u.id, u.username
HAVING SUM(oi.price * oi.quantity) > 0
   OR COUNT(DISTINCT o.id) > 0
ORDER BY total_spent DESC NULLS LAST;
```

---

## 今日总结

- [ ] `INNER JOIN` 只返回两表都匹配的行
- [ ] `LEFT JOIN` 返回左表所有行，右表无匹配填 NULL
- [ ] `RIGHT JOIN` 返回右表所有行，左表无匹配填 NULL
- [ ] `FULL OUTER JOIN` 返回两表所有行，无匹配填 NULL
- [ ] `JOIN ... USING (column)` 当连接字段名相同时使用
- [ ] 自连接用于处理层次结构（员工-经理关系）
- [ ] 多表连接时注意连接顺序和条件

---

*第 7 天 / 330 天*
*Python 后端 - SQL JOIN 表连接*