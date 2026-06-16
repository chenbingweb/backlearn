# 第 1 天：SQL 概述与数据库概念

## 学习目标

- 理解数据库的基本概念
- 掌握关系型数据库的核心术语
- 了解 SQL 语言的作用和分类
- 学会安装和连接数据库

---

## 1. 数据库基础概念

### 什么是数据库

数据库（Database）是按照数据结构来组织、存储和管理数据的仓库。

**核心特征：**
- 持久化存储：数据存储在磁盘上，关机不丢失
- 结构化组织：数据以表、行、列的形式存储
- 高效访问：通过索引快速检索数据
- 并发控制：支持多用户同时访问

### 关系型数据库

关系型数据库（Relational Database）使用表格（表）来存储数据，表之间可以通过外键建立关联。

```
┌─────────────┐       ┌─────────────┐
│   users     │       │   orders   │
├─────────────┤       ├─────────────┤
│ id          │◄──────│ user_id    │
│ username    │ 1   N│ id         │
│ email       │       │ total      │
│ created_at  │       │ created_at │
└─────────────┘       └─────────────┘
```

### 核心术语

| 术语 | 说明 | 示例 |
|------|------|------|
| 表（Table） | 存储特定类型数据的结构 | users、orders |
| 行（Row） | 表中的一条记录 | 用户 Alice |
| 列（Column） | 表中的一个字段 | username、email |
| 主键（Primary Key） | 唯一标识每行 | id |
| 外键（Foreign Key） | 建立表间关联 | user_id |
| 索引（Index） | 加速查询的数据结构 | 邮箱索引 |

---

## 2. SQL 语言概述

### 什么是 SQL

SQL（Structured Query Language）是用于管理关系型数据库的标准编程语言。

**SQL 的功能：**
- 数据查询（Query）
- 数据插入（Insert）
- 数据更新（Update）
- 数据删除（Delete）
- 数据库定义（DDL）
- 访问控制（DCL）

### SQL 分类

```sql
-- 1. DDL (Data Definition Language) - 数据定义语言
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT
);
DROP TABLE users;
ALTER TABLE users ADD COLUMN email TEXT;

-- 2. DML (Data Manipulation Language) - 数据操作语言
INSERT INTO users (name) VALUES ('Alice');
UPDATE users SET email = 'alice@example.com' WHERE id = 1;
DELETE FROM users WHERE id = 1;

-- 3. DQL (Data Query Language) - 数据查询语言
SELECT * FROM users WHERE id = 1;

-- 4. DCL (Data Control Language) - 数据控制语言
GRANT SELECT ON users TO 'user1';
REVOKE SELECT ON users FROM 'user1';

-- 5. TCL (Transaction Control Language) - 事务控制语言
BEGIN;
COMMIT;
ROLLBACK;
```

---

## 3. 主流关系型数据库

### PostgreSQL

```sql
-- PostgreSQL 示例
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 特点
-- ✅ 开源免费，功能强大
-- ✅ 支持复杂数据类型（JSON、数组）
-- ✅ 强大的扩展性
-- ✅ 遵循 SQL 标准
```

### MySQL

```sql
-- MySQL 示例
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 特点
-- ✅ 开源免费（社区版）
-- ✅ 性能优异
-- ✅ 易于使用和部署
-- ✅ 广泛使用（WordPress、Facebook）
```

### SQLite

```sql
-- SQLite 示例
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 特点
-- ✅ 零配置，无需服务器
-- ✅ 单文件数据库
-- ✅ 适合移动端和小型应用
-- ❌ 并发性能较弱
```

---

## 4. 数据库安装与连接

### PostgreSQL 安装

```bash
# macOS
brew install postgresql
brew services start postgresql

# Linux (Ubuntu)
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Windows
# 下载安装包：https://www.postgresql.org/download/windows/
```

### MySQL 安装

```bash
# macOS
brew install mysql
brew services start mysql

# Linux (Ubuntu)
sudo apt install mysql-server
sudo systemctl start mysql
```

### 数据库连接工具

```bash
# psql (PostgreSQL 命令行客户端)
psql -h localhost -U postgres -d mydb

# mysql (MySQL 命令行客户端)
mysql -h localhost -u root -p mydb

# 常用 GUI 工具
# - pgAdmin (PostgreSQL)
# - DBeaver (通用)
# - TablePlus (通用)
# - DataGrip (JetBrains)
```

### Python 连接数据库

```python
# PostgreSQL
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="mydb",
    user="postgres",
    password="secret"
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()

for row in rows:
    print(row)

cursor.close()
conn.close()

# MySQL
import pymysql

conn = pymysql.connect(
    host="localhost",
    port=3306,
    database="mydb",
    user="root",
    password="secret"
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()

cursor.close()
conn.close()
```

---

## 5. 数据库客户端操作

### psql 基本命令

```sql
-- 连接数据库
\c mydb

-- 列出所有数据库
\l

-- 列出所有表
\dt

-- 列出表结构
\d users

-- 列出所有用户
\du

-- 执行外部 SQL 文件
\i schema.sql

-- 退出
\q
```

### MySQL 基本命令

```sql
-- 列出所有数据库
SHOW DATABASES;

-- 使用数据库
USE mydb;

-- 列出所有表
SHOW TABLES;

-- 列出表结构
DESC users;

-- 列出所有用户
SELECT user, host FROM mysql.user;
```

---

## 6. 第一个数据库操作

### 创建数据库和表

```sql
-- 创建数据库
CREATE DATABASE shop;

-- 连接数据库后创建表
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入数据
INSERT INTO products (name, price, stock) VALUES
    ('iPhone', 999.99, 100),
    ('MacBook', 1999.99, 50),
    ('AirPods', 199.99, 200);

-- 查询数据
SELECT * FROM products;
SELECT name, price FROM products WHERE price > 500;
```

### 完整 Python 示例

```python
import psycopg2
from decimal import Decimal
from datetime import datetime

# 连接数据库
conn = psycopg2.connect(
    host="localhost",
    database="shop",
    user="postgres",
    password="secret"
)
conn.autocommit = True

cursor = conn.cursor()

# 创建表
cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        stock INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# 插入数据
cursor.execute(
    "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)",
    ('iPhone', Decimal('999.99'), 100)
)

# 查询数据
cursor.execute("SELECT * FROM products")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Name: {row[1]}, Price: {row[2]}")

cursor.close()
conn.close()

print("数据库操作完成！")
```

---

## 实战练习

### 练习 1：创建个人信息表

```sql
CREATE TABLE personal_info (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    age INTEGER,
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入几条数据
INSERT INTO personal_info (name, age, email, phone, address) VALUES
    ('张三', 25, 'zhangsan@example.com', '13800138000', '北京'),
    ('李四', 30, 'lisi@example.com', '13900139000', '上海'),
    ('王五', 28, 'wangwu@example.com', '13700137000', '深圳');
```

### 练习 2：创建订单表

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_no VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入订单数据
INSERT INTO orders (order_no, user_id, total_amount, status) VALUES
    ('ORD202401010001', 1, 2999.99, 'completed'),
    ('ORD202401010002', 1, 599.99, 'pending'),
    ('ORD202401010003', 2, 1299.99, 'shipped');
```

---

## 今日总结

- [ ] 数据库是按照数据结构组织、存储和管理数据的仓库
- [ ] 关系型数据库使用表格（行、列）存储数据，表间通过外键关联
- [ ] SQL 分为 DDL、DML、DQL、DCL、TCL 五类
- [ ] 主流关系型数据库：PostgreSQL、MySQL、SQLite
- [ ] 主键唯一标识每行记录，外键建立表间关联
- [ ] 使用 psql/mysql 命令行或 Python 连接数据库

---

*第 1 天 / 330 天*
*Python 后端 - SQL 基础*