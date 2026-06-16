# 第 4 天：INSERT 插入语句

## 学习目标

- 掌握单行插入语法
- 学会多行插入
- 理解 INSERT INTO SELECT 语法
- 掌握更新和删除数据

---

## 1. 插入单行数据

### 基本语法

```sql
-- 插入所有列（按表结构顺序）
INSERT INTO users VALUES (1, 'alice', 'alice@example.com', 'pass123', 25);

-- 插入指定列
INSERT INTO users (username, email) VALUES ('alice', 'alice@example.com');

-- 插入多个字段
INSERT INTO users (username, email, age) VALUES ('alice', 'alice@example.com', 25);
```

### 使用 DEFAULT 和 CURRENT_TIMESTAMP

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入时使用默认值
INSERT INTO products (name, price) VALUES ('iPhone', 999.99);
-- status 会自动设为 'active'，created_at 自动设为当前时间

-- 显式使用 DEFAULT
INSERT INTO products (name, price, status) VALUES ('iPhone', 999.99, DEFAULT);
```

---

## 2. 插入多行数据

### 批量插入

```sql
INSERT INTO users (username, email, age) VALUES
    ('alice', 'alice@example.com', 25),
    ('bob', 'bob@example.com', 30),
    ('charlie', 'charlie@example.com', 28),
    ('david', 'david@example.com', 35);

-- 插入不同数据
INSERT INTO products (name, price, stock) VALUES
    ('iPhone', 999.99, 100),
    ('MacBook', 1999.99, 50),
    ('AirPods', 199.99, 200);
```

### 插入并返回数据

```sql
-- PostgreSQL: RETURNING
INSERT INTO users (username, email) VALUES ('alice', 'alice@example.com')
RETURNING id, username, created_at;

-- 插入并获取自动生成的主键
INSERT INTO orders (user_id, total) VALUES (1, 299.99)
RETURNING id;

-- 插入多条并返回
INSERT INTO products (name, price) VALUES
    ('Product A', 10.00),
    ('Product B', 20.00)
RETURNING id, name;
```

---

## 3. INSERT INTO SELECT

### 基本语法

```sql
-- 从其他表复制数据
INSERT INTO archive_users (username, email, created_at)
SELECT username, email, created_at
FROM users
WHERE created_at < '2020-01-01';
```

### 完整示例

```sql
-- 创建归档表
CREATE TABLE archive_orders (
    id INTEGER,
    order_no VARCHAR(50),
    user_id INTEGER,
    total DECIMAL(10, 2),
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 从 orders 表复制已完成订单
INSERT INTO archive_orders (id, order_no, user_id, total)
SELECT id, order_no, user_id, total
FROM orders
WHERE status = 'completed';

-- 带条件的数据复制
INSERT INTO products_archive (name, price, category)
SELECT name, price, category
FROM products
WHERE category = 'electronics'
  AND price > 500;
```

### 复制表结构和数据

```sql
-- 复制表结构
CREATE TABLE users_backup AS SELECT * FROM users WHERE 1=0;

-- 复制表结构和数据
CREATE TABLE users_copy AS SELECT * FROM users;

-- PostgreSQL 特有：包括约束和索引
CREATE TABLE users_full_backup (LIKE users INCLUDING ALL);
```

---

## 4. UPDATE 更新数据

### 基本语法

```sql
-- 更新所有行
UPDATE users SET status = 'inactive';

-- 更新指定行
UPDATE users SET email = 'new@example.com' WHERE id = 1;

-- 更新多个字段
UPDATE users
SET email = 'new@example.com',
    age = 30,
    status = 'active'
WHERE id = 1;
```

### 条件更新

```sql
-- 根据条件更新
UPDATE products
SET price = price * 0.9
WHERE stock > 100;

-- 多条件更新
UPDATE orders
SET status = 'shipped',
    shipped_at = CURRENT_TIMESTAMP
WHERE status = 'pending'
  AND created_at < CURRENT_TIMESTAMP - INTERVAL '7 days';
```

### 使用表达式更新

```sql
-- 数值计算
UPDATE products SET price = price * 0.9;                    -- 9折
UPDATE products SET price = price * 1.1 WHERE category = 'food';  -- 食品涨价10%
UPDATE orders SET total = total * 1.05 WHERE user_id = 1;    -- 用户1订单涨价5%

-- 字符串操作
UPDATE users SET email = LOWER(email);                      -- 转小写
UPDATE products SET name = TRIM(name);                      -- 去空格
UPDATE articles SET title = CONCAT(title, ' - Updated');     -- 拼接字符串

-- 条件表达式
UPDATE users
SET status = CASE
    WHEN age < 18 THEN 'minor'
    WHEN age < 65 THEN 'adult'
    ELSE 'senior'
END;
```

### RETURNING（PostgreSQL）

```sql
UPDATE users SET status = 'active' WHERE id = 1
RETURNING id, username, status;

UPDATE products SET stock = stock - 1 WHERE id = 1
RETURNING id, name, stock;
```

---

## 5. DELETE 删除数据

### 基本语法

```sql
-- 删除所有数据（谨慎！）
DELETE FROM users;

-- 删除指定行
DELETE FROM users WHERE id = 1;

-- 删除多行
DELETE FROM users WHERE status = 'inactive' AND created_at < '2020-01-01';
```

### 使用子查询删除

```sql
-- 删除没有订单的用户
DELETE FROM users
WHERE NOT EXISTS (
    SELECT 1 FROM orders WHERE orders.user_id = users.id
);

-- 删除特定分类的所有产品
DELETE FROM products
WHERE category IN (
    SELECT category FROM categories WHERE name = 'obsolete'
);
```

### TRUNCATE 清空表

```sql
-- 清空表数据（比 DELETE 快）
TRUNCATE TABLE users;

-- 重置自增序列
TRUNCATE TABLE users RESTART IDENTITY;

-- 级联清空相关表
TRUNCATE TABLE orders CASCADE;

-- PostgreSQL：清空并重置统计信息
TRUNCATE TABLE users RESTART IDENTITY CONTINUE IDENTITY;
```

### DELETE vs TRUNCATE

| 特性 | DELETE | TRUNCATE |
|------|--------|----------|
| 速度 | 慢 | 快 |
| WHERE 支持 | 支持 | 不支持（清空所有） |
| 触发器 | 会触发 | 不触发 |
| 事务回滚 | 可以 | 不行（DDL） |
| 重置自增 | 否 | 是 |

---

## 6. 实战练习

### 练习 1：订单数据操作

```sql
-- 创建订单表
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_no VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入订单数据
INSERT INTO orders (order_no, user_id, total, status) VALUES
    ('ORD202401010001', 1, 299.99, 'pending'),
    ('ORD202401010002', 1, 599.99, 'completed'),
    ('ORD202401010003', 2, 199.99, 'pending'),
    ('ORD202401010004', 3, 899.99, 'shipped');

-- 更新订单状态
UPDATE orders SET status = 'completed' WHERE order_no = 'ORD202401010003';

-- 删除已取消的订单
INSERT INTO orders (order_no, user_id, total, status) VALUES
    ('ORD202401010005', 1, 99.99, 'cancelled');

DELETE FROM orders WHERE status = 'cancelled';
```

### 练习 2：批量数据处理

```sql
-- 创建库存日志表
CREATE TABLE stock_logs (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    change_amount INTEGER NOT NULL,
    reason VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 批量记录库存变动
INSERT INTO stock_logs (product_id, change_amount, reason) VALUES
    (1, -10, '销售'),
    (2, -5, '销售'),
    (1, 100, '进货'),
    (3, 50, '进货');

-- 更新产品库存（汇总计算）
UPDATE products p
SET stock = stock + (
    SELECT COALESCE(SUM(change_amount), 0)
    FROM stock_logs sl
    WHERE sl.product_id = p.id
);

-- 删除已处理的库存日志
DELETE FROM stock_logs WHERE created_at < CURRENT_DATE - INTERVAL '30 days';
```

---

## 今日总结

- [ ] `INSERT INTO` 插入数据，`VALUES` 指定值
- [ ] 多行插入：`INSERT INTO ... VALUES (...), (...), (...)`
- [ ] `INSERT INTO ... SELECT` 从其他表复制数据
- [ ] `UPDATE ... SET` 更新数据，`WHERE` 限定条件
- [ ] `DELETE FROM` 删除数据，`WHERE` 限定条件
- [ ] `TRUNCATE TABLE` 清空表，比 DELETE 快
- [ ] `RETURNING`（PostgreSQL）返回插入/更新的数据
- [ ] 使用事务保证数据一致性

---

*第 4 天 / 330 天*
*Python 后端 - SQL INSERT 插入语句*