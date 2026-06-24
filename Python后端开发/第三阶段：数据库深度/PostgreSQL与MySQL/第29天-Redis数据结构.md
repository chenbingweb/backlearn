# 第 29 天：Redis 数据结构

## 学习目标

- 理解 Redis 键值结构
- 掌握 Redis 核心数据结构
- 学会 Redis 数据类型选择
- 理解 Redis 编码方式

---

## 1. Redis 键值结构

### 键的基本概念

```bash
# Redis 键是字符串类型
SET name "Alice"
GET name

# 键的命名规范
# 建议格式：业务:对象:属性
user:1001:info          # 用户信息
order:20240101:count    # 订单计数
session:abc123:data     # 会话数据

# 键操作
KEYS user:*             # 查找匹配键
EXISTS user:1001:info   # 检查键是否存在
TYPE user:1001:info     # 获取值类型
DEL user:1001:info      # 删除键
RENAME old_key new_key  # 重命名
```

### 键的过期时间

```bash
# 设置过期
EXPIRE user:1001:info 3600        # 1小时后过期
EXPIREAT user:1001:info 1704067200 # 过期时间戳
PEXPIRE user:1001:info 3600000     # 毫秒过期

# 查询过期
TTL user:1001:info        # 返回剩余秒数（-1表示永久）
PTTL user:1001:info       # 返回剩余毫秒

# 移除过期（永不过期）
PERSIST user:1001:info
```

---

## 2. Redis 核心数据结构

### 数据结构总览

```
┌─────────────────────────────────────────────────────┐
│                      Redis                          │
├─────────────────────────────────────────────────────┤
│  String    │  Hash    │  List  │  Set  │  ZSet     │
│  字符串    │  哈希    │  列表  │  集合  │  有序集合  │
├─────────────────────────────────────────────────────┤
│ SDS        │  ziplist │ quicklist│ intset │ ziplist │
│ 简单动态字符串│ 压缩列表  │ 快速列表│ 整数集合│ 压缩列表  │
└─────────────────────────────────────────────────────┘
```

### 内部编码

| 数据类型 | 编码方式 | 适用场景 |
|---------|---------|---------|
| String | int, embstr, raw | 简单值、计数器、缓存对象 |
| Hash | ziplist, hashtable | 字段少用压缩列表，字段多用字典 |
| List | ziplist, quicklist | 小列表用压缩列表，大列表用快速列表 |
| Set | intset, hashtable | 全整数用整数集合，否则用字典 |
| ZSet | ziplist, skiplist | 小有序集合用压缩列表，否则用跳跃表 |

### 编码转换

```bash
# 查看键的编码
OBJECT ENCODING user:1001:info

# 编码说明
# "int"          - 整数字符串
# "embstr"       - embstr 编码（<=39字节）
# "raw"          - raw 编码（>39字节）
# "ziplist"      - 压缩列表
# "quicklist"    - 快速列表
# "intset"       - 整数集合
# "hashtable"    - 字典
# "skiplist"     - 跳跃表
```

---

## 3. String 详解

### SDS（Simple Dynamic String）

```
┌──────────────────────────────────────────────────────┐
│                      SDS 结构                          │
├────────┬────────┬────────────┬────────────────────────┤
│ free   │ len    │ alloc     │        char[]          │
│ 可用空间│ 长度   │ 分配空间   │        字符数组         │
└────────┴────────┴────────────┴────────────────────────┘
```

```bash
# SDS 特性
# 1. O(1) 获取长度（len字段）
STRLEN user:1001:name

# 2. 空间预分配
SET name "Alice"           # 分配刚好够用的空间
APPEND name " Chen"        # 追加时预分配更多空间

# 3. 惰性空间释放
SET name "Bob"             # 不立即释放多余空间
```

### String 应用场景

```bash
# 缓存
SET user:1001:cache '{"id":1001,"name":"Alice"}'
GET user:1001:cache

# 计数器
INCR article:1001:views           # 原子递增
INCRBY article:1001:views 100    # 指定增量
DECR article:1001:views          # 原子递减

# 分布式锁
SET lock:order:1001 "1" NX EX 30  # NX 不存在则设置，30秒过期

# 限流
INCR rate:ip:192.168.1.1
EXPIRE rate:ip:192.168.1.1 60
```

---

## 4. Hash 详解

### Hash 结构

```
┌─────────────────────────────────────────────────────┐
│                    Hash 结构                          │
├─────────────────────────────────────────────────────┤
│  field1 │ value1 │ field2 │ value2 │ field3 │ value3│
│  字段1  │  值1   │ 字段2  │  值2   │ 字段3  │  值3   │
└─────────────────────────────────────────────────────┘
```

### Hash 命令

```bash
# 基本操作
HSET user:1001 name "Alice" age "25" email "alice@test.com"
HGET user:1001 name
HMGET user:1001 name age email
HGETALL user:1001

# 字段操作
HINCRBY user:1001 age 1        # 年龄+1
HINCRBYFLOAT user:1001 balance 100.5  # 浮点增量
HEXISTS user:1001 name          # 检查字段存在
HLEN user:1001                   # 字段数量
HDEL user:1001 email             # 删除字段
HKEYS user:1001                  # 获取所有字段
HVALS user:1001                  # 获取所有值
```

### Hash vs String

```bash
# String 方式（每个属性一个键）
SET user:1001:name "Alice"
SET user:1001:age "25"
SET user:1001:email "alice@test.com"

# Hash 方式（一个键包含所有属性）
HSET user:1001 name "Alice" age "25" email "alice@test.com"

# 对比
# Hash：减少键数量，批量操作更高效
# String：可设置单独过期时间，更灵活
```

---

## 5. List 详解

### List 结构（quicklist）

```
┌─────────────────────────────────────────────────────┐
│                   QuickList 结构                      │
├────────┬────────┬────────┬────────┬────────┬─────────┤
│  Node  │  Node  │  Node  │  Node  │  Node  │  Node  │
│ 压缩节点│ 压缩节点│ 压缩节点│ 压缩节点│ 压缩节点│ 压缩节点│
└────────┴────────┴────────┴────────┴────────┴─────────┘
```

### List 命令

```bash
# 基本操作
LPUSH queue:tasks "task1"        # 左侧插入
RPUSH queue:tasks "task2"         # 右侧插入
LPOP queue:tasks                  # 左侧弹出
RPOP queue:tasks                  # 右侧弹出

# 范围操作
LRANGE queue:tasks 0 -1           # 获取所有元素
LRANGE queue:tasks 0 9            # 获取前10个

# 阻塞操作
BLPOP queue:tasks 0               # 阻塞左侧弹出
BRPOP queue:tasks 0               # 阻塞右侧弹出

# 队列长度
LLEN queue:tasks

# 插入操作
LINSERT queue:tasks BEFORE "task1" "task0"  # 在task1前插入
LINSERT queue:tasks AFTER "task1" "task2"   # 在task1后插入

# 索引操作
LINDEX queue:tasks 0              # 获取指定索引元素
LSET queue:tasks 0 "new_task"     # 设置指定索引元素

# 修剪
LTRIM queue:tasks 0 99            # 只保留前100个元素
```

---

## 6. Set 详解

### Set 结构（intset/hashtable）

```bash
# 基本操作
SADD tags:article:1001 "python" "redis" "database"
SMEMBERS tags:article:1001        # 获取所有成员
SISMEMBER tags:article:1001 "python"  # 检查是否存在

# 集合运算
SINTER tags:python tags:redis     # 交集（同时包含）
SUNION tags:python tags:redis     # 并集
SDIFF tags:python tags:redis      # 差集（python有但redis没有）

# 集合计数
SCARD tags:article:1001           # 成员数量

# 随机操作
SRANDMEMBER tags:article:1001     # 随机获取一个成员
SRANDMEMBER tags:article:1001 3   # 随机获取3个成员
SPOP tags:article:1001            # 随机弹出（删除）

# 删除
SREM tags:article:1001 "python"   # 删除指定成员
```

---

## 7. Sorted Set 详解

### ZSet 结构（ziplist/skiplist）

```
┌─────────────────────────────────────────────────────┐
│                 ZSet (跳跃表) 结构                     │
├─────────────────────────────────────────────────────┤
│  Level 3 ─────────────────────────────►           │
│  Level 2 ─────────► ────────────────────────────► │
│  Level 1 ───► ───► ───► ────────────────────────► │
│  Level 0 ──► ──► ──► ──► ──► ──► ──► ──► ──► ──► │
│            Alice  Bob   Carol  David  Eve  Frank   │
│              95    88    92     78    100   85     │
└─────────────────────────────────────────────────────┘
```

### ZSet 命令

```bash
# 基本操作
ZADD leaderboard 100 "Alice" 200 "Bob" 150 "Carol"
ZSCORE leaderboard "Alice"              # 获取分数
ZRANGE leaderboard 0 -1                # 按分数升序
ZREVRANGE leaderboard 0 -1 WITHSCORES   # 按分数降序

# 排名
ZRANK leaderboard "Alice"               # 升序排名（0开始）
ZREVRANK leaderboard "Alice"            # 降序排名

# 分数操作
ZINCRBY leaderboard 10 "Alice"          # 增加分数
ZCOUNT leaderboard 90 100              # 统计指定分数范围

# 按分数范围
ZRANGEBYSCORE leaderboard 90 100        # 90-100分之间
ZRANGEBYSCORE leaderboard (90 100      # 90<分数<=100

# 删除
ZREM leaderboard "Alice"               # 删除成员
ZREMRANGEBYRANK leaderboard 0 9        # 删除排名0-9
ZREMRANGEBYSCORE leaderboard 0 60      # 删除60分以下

# 集合运算
ZUNIONSTORE result 2 set1 set2 WEIGHTS 1 0.5 AGGREGATE SUM
```

---

## 8. Python 操作示例

```python
import redis

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# String
r.set('name', 'Alice', ex=3600)  # 带过期
r.setnx('lock', '1')             # 不存在则设置
r.get('name')
r.incr('counter')
r.incrbyfloat('balance', 100.5)

# Hash
r.hset('user:1001', mapping={'name': 'Alice', 'age': '25'})
r.hgetall('user:1001')
r.hincrby('user:1001', 'age', 1)

# List
r.lpush('queue', 'task1', 'task2')
r.rpop('queue')
r.lrange('queue', 0, -1)
r.brpop('queue', timeout=5)

# Set
r.sadd('tags', 'python', 'redis')
r.smembers('tags')
r.sinter('tags1', 'tags2')

# ZSet
r.zadd('leaderboard', {'Alice': 100, 'Bob': 200})
r.zrevrange('leaderboard', 0, 9, withscores=True)
r.zrank('leaderboard', 'Alice')
```

---

## 今日总结

- [ ] Redis 键是字符串，值支持 5 种数据结构
- [ ] String：SDS 实现，O(1) 长度获取，预分配空间
- [ ] Hash： field-value 映射，适合对象存储
- [ ] List： quicklist 实现，支持队列和栈
- [ ] Set：无序唯一集合，支持交并差运算
- [ ] ZSet：跳跃表实现，有序唯一，支持排名

---

*第 29 天 / 330 天*
*Python 后端 - Redis 数据结构*
