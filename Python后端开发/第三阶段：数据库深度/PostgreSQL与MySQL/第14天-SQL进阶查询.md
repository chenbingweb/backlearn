# 第 14 天：SQL 进阶查询

## 学习目标

- 掌握复杂 JOIN 技术
- 学会高级聚合和窗口函数
- 理解 CTE（公用表表达式）
- 掌握高级子查询技巧

---

## 1. 高级 JOIN 技术

### 自连接

```sql
-- 员工表自连接：找出每个员工及其经理
SELECT
    e.employee_name AS employee,
    e.department,
    m.employee_name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;

-- 自连接实现展开层次数据
SELECT
    p.name AS parent_category,
    c.name AS sub_category
FROM categories p
JOIN categories c ON p.id = c.parent_id;
```

### 多表 JOIN

```sql
-- 四表连接：订单详情完整视图
SELECT
    o.order_no,
    o.created_at,
    c.name AS customer_name,
    e.name AS employee_name,
    p.name AS product_name,
    oi.quantity,
    oi.price,
    oi.quantity * oi.price AS subtotal
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN employees e ON o.employee_id = e.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE o.status = 'completed'
ORDER BY o.created_at DESC;
```

### 复杂条件 JOIN

```sql
-- 非等值连接：价格区间匹配
SELECT
    p.name AS product,
    p.price,
    d.discount_name,
    d.min_amount,
    d.max_amount,
    CASE
        WHEN p.price >= d.min_amount AND p.price <= d.max_amount
        THEN p.price * (1 - d.discount_rate)
        ELSE p.price
    END AS final_price
FROM products p
JOIN discounts d ON p.price >= d.min_amount AND p.price <= d.max_amount;
```

---

## 2. 窗口函数

### 基础窗口函数

```sql
-- ROW_NUMBER：行号
SELECT
    employee_name,
    department,
    salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS row_num
FROM employees;

-- RANK：排名（有并列跳过后面的）
SELECT
    employee_name,
    department,
    salary,
    RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS rank
FROM employees;

-- DENSE_RANK：排名（有并列不跳过后面的）
SELECT
    employee_name,
    department,
    salary,
    DENSE_RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS dense_rank
FROM employees;

-- NTILE：分桶
SELECT
    employee_name,
    salary,
    NTILE(4) OVER (ORDER BY salary) AS quartile
FROM employees;
```

### 聚合窗口函数

```sql
-- 累计求和
SELECT
    order_date,
    daily_amount,
    SUM(daily_amount) OVER (ORDER BY order_date) AS cumulative_sum
FROM daily_sales;

-- 累计平均值
SELECT
    order_date,
    daily_amount,
    AVG(daily_amount) OVER (ORDER BY order_date) AS cumulative_avg
FROM daily_sales;

-- 移动平均值（最近3天）
SELECT
    order_date,
    daily_amount,
    AVG(daily_amount) OVER (
        ORDER BY order_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg_3
FROM daily_sales;

-- 第一行/最后一行值
SELECT
    employee_name,
    salary,
    FIRST_VALUE(salary) OVER (PARTITION BY department ORDER BY hire_date) AS first_salary,
    LAST_VALUE(salary) OVER (PARTITION BY department ORDER BY hire_date) AS last_salary
FROM employees;
```

### LAG 和 LEAD

```sql
-- LAG：获取前一行数据
SELECT
    order_date,
    amount,
    LAG(amount, 1) OVER (ORDER BY order_date) AS prev_amount,
    amount - LAG(amount, 1) OVER (ORDER BY order_date) AS diff_from_prev
FROM daily_sales;

-- LEAD：获取后一行数据
SELECT
    order_date,
    amount,
    LEAD(amount, 1) OVER (ORDER BY order_date) AS next_amount
FROM daily_sales;

-- 计算环比增长率
SELECT
    order_date,
    amount,
    ROUND(
        (amount - LAG(amount, 1) OVER (ORDER BY order_date)) /
        NULLIF(LAG(amount, 1) OVER (ORDER BY order_date), 0) * 100,
        2
    ) AS环比增长率
FROM monthly_sales;
```

---

## 3. CTE 公用表表达式

### 基本 CTE

```sql
-- 单个 CTE
WITH high_value_customers AS (
    SELECT customer_id, SUM(total) AS total_spent
    FROM orders
    GROUP BY customer_id
    HAVING SUM(total) > 10000
)
SELECT
    c.name,
    c.email,
    h.total_spent
FROM customers c
JOIN high_value_customers h ON c.id = h.customer_id
ORDER BY h.total_spent DESC;
```

### 多个 CTE

```sql
-- 多个 CTE 串联
WITH
-- CTE 1：活跃用户
active_users AS (
    SELECT id, username
    FROM users
    WHERE last_login > CURRENT_DATE - INTERVAL '30 days'
),
-- CTE 2：用户订单统计
user_order_stats AS (
    SELECT
        user_id,
        COUNT(*) AS order_count,
        SUM(total) AS total_spent
    FROM orders
    WHERE user_id IN (SELECT id FROM active_users)
    GROUP BY user_id
),
-- CTE 3：高价值用户
vip_users AS (
    SELECT user_id
    FROM user_order_stats
    WHERE total_spent > 5000
)
SELECT
    u.username,
    s.order_count,
    s.total_spent,
    CASE
        WHEN v.user_id IS NOT NULL THEN 'VIP'
        ELSE 'Regular'
    END AS user_tier
FROM active_users u
JOIN user_order_stats s ON u.id = s.user_id
LEFT JOIN vip_users v ON u.id = v.user_id;
```

### 递归 CTE

```sql
-- 递归 CTE：生成数字序列
WITH RECURSIVE digits(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM digits WHERE n < 10
)
SELECT n FROM digits;

-- 递归 CTE：组织架构遍历
WITH RECURSIVE org_chart AS (
    -- 起始：CEO
    SELECT id, name, manager_id, 1 AS level, name AS path
    FROM employees
    WHERE manager_id IS NULL

    UNION ALL

    -- 递归：下属
    SELECT e.id, e.name, e.manager_id, oc.level + 1, oc.path || ' > ' || e.name
    FROM employees e
    JOIN org_chart oc ON e.manager_id = oc.id
)
SELECT level, path FROM org_chart ORDER BY level, name;
```

---

## 4. 高级子查询

### 标量子查询

```sql
-- 在 SELECT 中使用子查询
SELECT
    product_name,
    price,
    (SELECT AVG(price) FROM products) AS avg_price,
    price - (SELECT AVG(price) FROM products) AS diff_from_avg
FROM products;

-- 在 WHERE 中使用标量子查询
SELECT
    order_no,
    total,
    customer_name
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE total > (SELECT AVG(total) FROM orders);
```

### 列子查询

```sql
-- IN 子查询
SELECT * FROM products
WHERE category_id IN (
    SELECT id FROM categories WHERE name LIKE '%Electronics%'
);

-- NOT IN（注意 NULL 处理）
SELECT * FROM products
WHERE category_id NOT IN (
    SELECT id FROM categories WHERE is_active = TRUE
);

-- 使用 EXISTS
SELECT * FROM products p
WHERE EXISTS (
    SELECT 1 FROM order_items oi
    JOIN orders o ON oi.order_id = o.id
    WHERE oi.product_id = p.id
    AND o.created_at > CURRENT_DATE - INTERVAL '7 days'
);
```

### 表子查询

```sql
-- 在 FROM 中使用子查询
SELECT
    category_name,
    product_count,
    avg_price
FROM (
    SELECT
        c.name AS category_name,
        COUNT(p.id) AS product_count,
        AVG(p.price) AS avg_price
    FROM categories c
    LEFT JOIN products p ON c.id = p.category_id
    GROUP BY c.id, c.name
) category_stats
WHERE product_count > 10
ORDER BY product_count DESC;
```

### 关联子查询

```sql
-- 找出每个类别中价格最高的产品
SELECT
    p.name,
    p.category_id,
    p.price
FROM products p
WHERE price = (
    SELECT MAX(price)
    FROM products p2
    WHERE p2.category_id = p.category_id
);

-- 找出销售额超过类目平均值的产品
SELECT
    p.name,
    c.name AS category,
    p.price,
    total_sales
FROM products p
JOIN categories c ON p.category_id = c.id
JOIN (
    SELECT product_id, SUM(quantity * price) AS total_sales
    FROM order_items
    GROUP BY product_id
) sales ON p.id = sales.product_id
WHERE total_sales > (
    SELECT AVG(s2.total_sales)
    FROM (
        SELECT product_id, SUM(quantity * price) AS total_sales
        FROM order_items
        GROUP BY product_id
    ) s2
    JOIN products p2 ON s2.product_id = p2.id
    WHERE p2.category_id = p.category_id
);
```

---

## 5. 高级聚合

### GROUP BY + CASE

```sql
-- 条件聚合
SELECT
    EXTRACT(YEAR FROM order_date) AS year,
    SUM(CASE WHEN status = 'completed' THEN total ELSE 0 END) AS completed_total,
    SUM(CASE WHEN status = 'cancelled' THEN total ELSE 0 END) AS cancelled_total,
    SUM(CASE WHEN status = 'refunded' THEN total ELSE 0 END) AS refunded_total,
    COUNT(*) AS total_orders
FROM orders
GROUP BY EXTRACT(YEAR FROM order_date)
ORDER BY year;
```

### GROUPING SETS

```sql
-- 多维度分组
SELECT
    EXTRACT(YEAR FROM order_date) AS year,
    EXTRACT(MONTH FROM order_date) AS month,
    customer_segment,
    SUM(total) AS total_sales
FROM orders
GROUP BY
    GROUPING SETS (
        (EXTRACT(YEAR FROM order_date)),           -- 年汇总
        (EXTRACT(YEAR FROM order_date), EXTRACT(MONTH FROM order_date)),  -- 年月
        (customer_segment),                         -- 客户维度
        ()                                          -- 总计
    )
ORDER BY year, month, customer_segment;
```

### CUBE

```sql
-- CUBE：所有组合
SELECT
    brand,
    category,
    SUM(quantity) AS total_qty
FROM products p
JOIN order_items oi ON p.id = oi.product_id
GROUP BY CUBE (brand, category)
ORDER BY brand, category;
-- 输出：brand+category, brand, category, 总计 的所有组合
```

### ROLLUP

```sql
-- ROLLUP：层级汇总
SELECT
    EXTRACT(YEAR FROM order_date) AS year,
    EXTRACT(MONTH FROM order_date) AS month,
    SUM(total) AS total_sales
FROM orders
GROUP BY ROLLUP (
    EXTRACT(YEAR FROM order_date),
    EXTRACT(MONTH FROM order_date)
)
ORDER BY year, month;
-- 输出：年/月组合, 年汇总, 总计
```

---

## 6. 实战练习

### 练习 1：销售排名报表

```sql
-- 每个销售员的月度业绩排名
WITH monthly_sales AS (
    SELECT
        e.id AS employee_id,
        e.name AS employee_name,
        e.department,
        TO_CHAR(o.created_at, 'YYYY-MM') AS month,
        SUM(o.total) AS sales_amount
    FROM employees e
    JOIN orders o ON e.id = o.employee_id
    WHERE o.status = 'completed'
    GROUP BY e.id, e.name, e.department, TO_CHAR(o.created_at, 'YYYY-MM')
)
SELECT
    month,
    employee_name,
    department,
    sales_amount,
    RANK() OVER (PARTITION BY month ORDER BY sales_amount DESC) AS month_rank,
    SUM(sales_amount) OVER (PARTITION BY department ORDER BY month) AS dept_cumulative
FROM monthly_sales
ORDER BY month, month_rank;
```

### 练习 2：用户行为分析

```sql
-- 用户复购周期分析
WITH user_orders AS (
    SELECT
        user_id,
        created_at,
        LAG(created_at) OVER (PARTITION BY user_id ORDER BY created_at) AS prev_order
    FROM orders
    WHERE status = 'completed'
),
avg_cycle AS (
    SELECT
        user_id,
        AVG(created_at - prev_order) AS avg_cycle_days
    FROM user_orders
    WHERE prev_order IS NOT NULL
    GROUP BY user_id
)
SELECT
    u.username,
    COUNT(o.id) AS order_count,
    ROUND(AVG(ac.avg_cycle_days), 1) AS avg_cycle_days,
    CASE
        WHEN AVG(ac.avg_cycle_days) <= 7 THEN '高频'
        WHEN AVG(ac.avg_cycle_days) <= 30 THEN '普通'
        ELSE '低频'
    END AS purchase_frequency
FROM users u
JOIN orders o ON u.id = o.user_id
LEFT JOIN avg_cycle ac ON u.id = ac.user_id
WHERE o.status = 'completed'
GROUP BY u.id, u.username
ORDER BY order_count DESC;
```

---

## 今日总结

- [ ] 自连接用于表内层次关系
- [ ] 窗口函数：`ROW_NUMBER`、`RANK`、`LAG`、`LEAD`
- [ ] CTE 简化复杂查询，递归 CTE 处理层次数据
- [ ] 子查询可在 SELECT、FROM、WHERE 中使用
- [ ] `GROUPING SETS`、`CUBE`、`ROLLUP` 多维度聚合

---

*第 14 天 / 330 天*
*Python 后端 - SQL 进阶查询*
