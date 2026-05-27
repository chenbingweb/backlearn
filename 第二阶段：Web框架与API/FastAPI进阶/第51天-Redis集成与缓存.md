# 第 51 天：Redis 集成与缓存

## 学习目标

- 掌握 Redis 基本操作
- 学会在 FastAPI 中集成 Redis
- 实现多级缓存策略
- 理解缓存失效与更新策略

---

## 1. Redis 简介

### Redis 数据结构

| 类型 | 说明 | 用途 |
|------|------|------|
| String | 字符串 | 缓存、计数器、Session |
| Hash | 哈希表 | 对象存储 |
| List | 列表 | 队列、消息队列 |
| Set | 集合 | 去重、标签 |
| Sorted Set | 有序集合 | 排行榜、优先级队列 |

### 安装 Redis

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt install redis-server

# Docker
docker run -d -p 6379:6379 redis
```

---

## 2. Python Redis 客户端

### 安装

```bash
pip install redis

# 异步版本
pip install redis[hiredis]  # hiredis 是 C 实现的解析器，更快
```

### 基本连接

```python
import redis

# 同步连接
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# 连接池（推荐）
pool = redis.ConnectionPool(host="localhost", port=6379, db=0, decode_responses=True)
r = redis.Redis(connection_pool=pool)

# 异步连接
import asyncio
import aioredis

async def main():
    r = await aioredis.create_redis_pool("redis://localhost")
    # ...
    r.close()
```

---

## 3. 基本操作

### String

```python
# 设置值
r.set("name", "Alice")
r.set("count", 100)

# 设置过期时间
r.setex("token", 3600, "abc123")  # 1 小时后过期
r.set("key", "value", ex=3600)

# 获取值
name = r.get("name")  # "Alice"
count = r.get("count")  # "100"

# 自增/自减
r.incr("count")      # 101
r.incrby("count", 5)  # 106
r.decr("count")      # 105
r.decrby("count", 10) # 95

# 批量操作
r.mset({"key1": "value1", "key2": "value2"})
values = r.mget(["key1", "key2"])
```

### Hash

```python
# 设置
r.hset("user:1", "name", "Alice")
r.hset("user:1", "email", "alice@example.com")
r.hmset("user:1", {"name": "Alice", "age": "30"})  # 旧版本

# 获取
name = r.hget("user:1", "name")
all_data = r.hgetall("user:1")  # {"name": "Alice", "email": "alice@example.com"}

# 自增
r.hincrby("user:1", "age", 1)
```

### List

```python
# 添加
r.lpush("queue", "task1")
r.rpush("queue", "task2")

# 获取
task = r.lpop("queue")  # task1
task = r.rpop("queue")   # task2

# 范围
tasks = r.lrange("queue", 0, -1)  # 所有任务
```

### Set

```python
# 添加
r.sadd("tags", "python", "fastapi", "redis")

# 获取
tags = r.smembers("tags")

# 判断
is_member = r.sismember("tags", "python")

# 交集/并集
r.sinter("tags1", "tags2")
r.sunion("tags1", "tags2")
```

---

## 4. FastAPI 集成 Redis

### 连接管理

```python
# app/redis.py
import redis.asyncio as redis
from typing import Optional

redis_pool: Optional[redis.Redis] = None


async def init_redis():
    global redis_pool
    redis_pool = redis.from_url(
        "redis://localhost:6379/0",
        encoding="utf-8",
        decode_responses=True,
    )


async def close_redis():
    await redis_pool.close()


def get_redis() -> redis.Redis:
    return redis_pool
```

### 中间件配置

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    await init_redis()
    yield
    # 关闭时
    await close_redis()
```

---

## 5. 缓存实现

### 装饰器缓存

```python
from functools import wraps
import json

def cache(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存 key
            key = f"cache:{func.__name__}:{json.dumps(args)}:{json.dumps(kwargs)}"

            r = get_redis()
            cached = await r.get(key)
            if cached:
                return json.loads(cached)

            result = await func(*args, **kwargs)

            await r.setex(key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator


@cache(ttl=60)
async def get_article(article_id: int):
    # 复杂查询...
    return {"id": article_id, "title": "..."}
```

### 缓存模式

```python
async def get_user_cached(user_id: int):
    cache_key = f"user:{user_id}"
    r = get_redis()

    # 1. 尝试从缓存获取
    cached = await r.get(cache_key)
    if cached:
        return json.loads(cached)

    # 2. 缓存未命中，查询数据库
    user = await get_user_from_db(user_id)
    if not user:
        return None

    # 3. 存入缓存
    await r.setex(cache_key, 3600, json.dumps(user))
    return user
```

### 缓存更新策略

```python
async def update_user_and_clear_cache(user_id: int, data: dict):
    # 1. 更新数据库
    user = await update_user_in_db(user_id, data)

    # 2. 删除缓存
    r = get_redis()
    await r.delete(f"user:{user_id}")

    # 3. 可选：重新写入缓存
    await r.setex(f"user:{user_id}", 3600, json.dumps(user))

    return user
```

---

## 6. 分布式锁

```python
import uuid

async def acquire_lock(key: str, ttl: int = 10) -> Optional[str]:
    """获取分布式锁"""
    r = get_redis()
    lock_id = str(uuid.uuid4())

    if await r.set(key, lock_id, nx=True, ex=ttl):
        return lock_id
    return None


async def release_lock(key: str, lock_id: str):
    """释放分布式锁"""
    r = get_redis()

    # Lua 脚本保证原子性
    lua = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
    await r.eval(lua, 1, key, lock_id)


async def do_with_lock(key: str, func, ttl: int = 10):
    """使用锁执行函数"""
    lock_id = await acquire_lock(key, ttl)
    if not lock_id:
        raise RuntimeError("获取锁失败")

    try:
        return await func()
    finally:
        await release_lock(key, lock_id)
```

---

## 实战练习

### 练习：访问计数

```python
async def track_article_view(article_id: int):
    r = get_redis()

    # 今日计数
    today = datetime.now().strftime("%Y-%m-%d")
    key = f"article:{article_id}:views:{today}"

    # 增加计数
    views = await r.incr(key)

    # 设置当天过期
    await r.expire(key, 86400 * 2)  # 保留 2 天

    return views


async def get_article_views(article_id: int) -> dict:
    r = get_redis()

    views = {}
    today = datetime.now()
    for i in range(7):
        day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        key = f"article:{article_id}:views:{day}"
        count = await r.get(key)
        if count:
            views[day] = int(count)

    return views
```

---

## 今日总结

- [ ] Redis 支持 String/Hash/List/Set/Sorted Set
- [ ] `redis-py` 提供同步和异步客户端
- [ ] `r.setex()` 设置带过期时间的值
- [ ] 缓存 key 命名建议用 `: ` 分隔层级
- [ ] 缓存更新：先更新 DB，再删除/更新缓存
- [ ] 分布式锁用 `SET NX EX` 实现
- [ ] Lua 脚本保证原子性操作

---

*第 51 天 / 330 天*
*第二阶段：FastAPI 进阶 - Redis 缓存*