# 第 30 天：Redis 快速入门

## 学习目标

- 理解 Redis 是什么
- 掌握 Redis 安装配置
- 学会基本数据类型操作
- 理解 Redis 应用场景

---

## 1. Redis 简介

### 什么是 Redis

```markdown
Redis = RE mote DI ctionary S erver

- 开源、内存数据结构存储
- 可用作数据库、缓存、消息队列
- 支持多种数据结构：String、Hash、List、Set、ZSet
- 性能极高：读 11万次/秒，写 8万次/秒
```

### vs 其他数据库

| 特性 | Redis | MySQL | MongoDB |
|------|-------|-------|---------|
| 数据存储 | 内存 | 磁盘 | 磁盘 |
| 数据结构 | 多种 | 关系型 | 文档型 |
| 性能 | 极高 | 中等 | 中等 |
| 容量 | 受内存限制 | TB级 | TB级 |
| 持久化 | 支持 | 支持 | 支持 |

---

## 2. 安装配置

### macOS 安装

```bash
# Homebrew 安装
brew install redis

# 启动服务
brew services start redis

# 连接
redis-cli

# 测试
PING
# 回复：PONG
```

### Docker 安装

```bash
# 启动 Redis 容器
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:alpine

# 连接
docker exec -it redis redis-cli
```

### 基本配置

```bash
# redis.conf 基本配置
port 6379
daemonize no
bind 127.0.0.1
maxmemory 256mb
maxmemory-policy allkeys-lru
```

---

## 3. 基本数据类型

### String

```bash
# 设置和获取
SET name "Alice"
GET name

# 数值操作
SET counter 0
INCR counter      # 1
INCR counter      # 2
INCRBY counter 5 # 7
DECR counter      # 6

# 过期时间
SET token "abc123" EX 3600  # 1小时后过期
TTL token                     # 查看剩余时间
```

### Hash

```bash
# 存储对象
HSET user:1001 name "Alice" age "25"
HGET user:1001 name
HGETALL user:1001

# 批量操作
HMSET user:1002 name "Bob" age "30"
HMGET user:1002 name age
```

### List

```bash
# 列表操作
LPUSH tasks "task1"       # 添加到头部
RPUSH tasks "task2"       # 添加到尾部
LPOP tasks                # 弹出头部
RPOP tasks                # 弹出尾部

# 查看列表
LRANGE tasks 0 -1         # 查看所有
```

### Set

```bash
# 集合操作
SADD tags "python" "redis" "database"
SMEMBERS tags
SISMEMBER tags "python"   # 检查是否存在

# 集合运算
SADD set1 "a" "b" "c"
SADD set2 "b" "c" "d"
SINTER set1 set2          # 交集
SUNION set1 set2           # 并集
```

### ZSet

```bash
# 有序集合（排行榜）
ZADD leaderboard 100 "Alice" 200 "Bob" 150 "Carol"
ZRANGE leaderboard 0 -1 WITHSCORES  # 按分数升序
ZREVRANGE leaderboard 0 -1 WITHSCORES # 按分数降序
ZSCORE leaderboard "Alice"           # 获取 Alice 的分数
```

---

## 4. Python 操作

### 安装驱动

```bash
pip install redis
```

### 基本操作

```python
import redis

# 连接
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# String
r.set('name', 'Alice')
name = r.get('name')

# Hash
r.hset('user:1001', mapping={'name': 'Alice', 'age': 25})
user = r.hgetall('user:1001')

# List
r.lpush('tasks', 'task1', 'task2')
tasks = r.lrange('tasks', 0, -1)

# Set
r.sadd('tags', 'python', 'redis')
tags = r.smembers('tags')

# ZSet
r.zadd('leaderboard', {'Alice': 100, 'Bob': 200})
top3 = r.zrevrange('leaderboard', 0, 2, withscores=True)

# 计数器
r.incr('page_views')
views = r.get('page_views')
```

---

## 5. 应用场景

### 缓存

```python
# 缓存用户信息
def get_user(user_id):
    cache_key = f'user:{user_id}'

    # 1. 查缓存
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    # 2. 查数据库
    user = db.query(User).get(user_id)

    # 3. 回填缓存
    if user:
        r.setex(cache_key, 3600, json.dumps(user.to_dict()))

    return user
```

### 计数器

```python
# 文章浏览量
r.incr(f'article:{article_id}:views')
views = r.get(f'article:{article_id}:views')
```

### 分布式锁

```python
# 获取锁
lock = r.set('lock:order:1001', '1', nx=True, ex=30)
if lock:
    # 执行业务
    process_order(1001)
    # 释放锁
    r.delete('lock:order:1001')
```

---

## 今日总结

- [ ] Redis：内存数据结构存储，高性能
- [ ] 支持 5 种数据结构：String、Hash、List、Set、ZSet
- [ ] String：`SET/GET/INCR/SETEX`
- [ ] Hash：`HSET/HGET/HGETALL`
- [ ] List：`LPUSH/RPOP/LRANGE`
- [ ] Set：`SADD/SMEMBERS/SINTER`
- [ ] ZSet：`ZADD/ZRANGE/ZSCORE`
- [ ] 应用场景：缓存、计数器、分布式锁、排行榜

---

*第 30 天 / 330 天*
*Python 后端 - Redis 快速入门*
