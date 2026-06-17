# 第 28 天：Redis 缓存与数据库

## 学习目标

- 理解缓存架构
- 掌握 Redis 使用
- 学会缓存策略
- 掌握缓存问题处理

---

## 1. 缓存架构

### 多级缓存

```
┌─────────────────────────────────────────────────────┐
│                   请求                              │
└─────────────────┬───────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────┐
│              Browser Cache (CDN)                    │
│         静态资源、JS/CSS/Images                      │
└─────────────────┬───────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────┐
│              Redis Cache (内存)                     │
│         热点数据、Session、Token                    │
└─────────────────┬───────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────┐
│              PostgreSQL / MySQL (磁盘)              │
│               持久化存储                             │
└─────────────────────────────────────────────────────┘
```

### 缓存读写模式

```markdown
## Cache-Aside（旁路缓存）- 推荐
1. 读：先读缓存，缓存不存在则读数据库，再写入缓存
2. 写：先写数据库，再删除缓存

## Read-Through
1. 读：缓存负责加载数据，应用程序只与缓存交互

## Write-Through
1. 写：同时写缓存和数据库

## Write-Behind
1. 写：先写缓存，异步写数据库
```

---

## 2. Redis 安装和配置

### 安装

```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo apt install redis-server

# Docker
docker run -d --name redis -p 6379:6379 redis:alpine
```

### 配置

```bash
# Redis 配置 /etc/redis/redis.conf

# 基础配置
bind 127.0.0.1
port 6379
daemonize no
databases 16

# 持久化
save 900 1      # 900秒内1次修改
save 300 100    # 300秒内100次修改
save 60 10000   # 60秒内10000次修改

# 内存
maxmemory 2gb
maxmemory-policy allkeys-lru

# 日志
loglevel notice
logfile ""
```

### 连接

```bash
# 命令行连接
redis-cli

# 选择数据库
SELECT 0

# 测试
PING
# 回复：PONG
```

---

## 3. Python 操作 Redis

### 安装驱动

```bash
pip install redis
```

### 基本操作

```python
import redis

# 连接
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# 字符串操作
r.set('name', 'Alice')
r.get('name')
r.setex('token', 3600, 'abc123')  # 过期时间
r.setnx('lock', 'locked')          # 不存在则设置

# 批量操作
r.mset({'key1': 'value1', 'key2': 'value2'})
r.mget(['key1', 'key2'])

# 计数器
r.incr('counter')
r.incrby('counter', 10)
r.decr('counter')

# 过期时间
r.expire('name', 60)           # 60秒后过期
r.ttl('name')                    # 查看剩余时间
r.persist('name')                # 移除过期
```

### 哈希操作

```python
# 哈希操作
r.hset('user:1', 'name', 'Alice')
r.hset('user:1', 'email', 'alice@example.com')
r.hget('user:1', 'name')

# 批量设置
r.hmset('user:2', {'name': 'Bob', 'email': 'bob@example.com'})

# 获取所有字段
r.hgetall('user:1')

# 字段操作
r.hincrby('user:1', 'login_count', 1)
r.hexists('user:1', 'email')
r.hdel('user:1', 'email')
r.hkeys('user:1')
r.hvals('user:1')
```

### 列表操作

```python
# 列表操作
r.lpush('queue', 'task1')
r.rpush('queue', 'task2')
r.lpop('queue')
r.rpop('queue')

# 阻塞操作
r.brpop('queue', timeout=5)

# 列表长度
r.llen('queue')

# 范围查询
r.lrange('queue', 0, -1)
```

### 集合操作

```python
# 集合操作
r.sadd('tags', 'python', 'redis', 'cache')
r.smembers('tags')
r.sismember('tags', 'python')
r.scard('tags')  # 集合大小
r.srem('tags', 'redis')

# 集合运算
r.sinter('tags1', 'tags2')  # 交集
r.sunion('tags1', 'tags2')  # 并集
r.sdiff('tags1', 'tags2')   # 差集
```

### 有序集合

```python
# 有序集合（排行榜）
r.zadd('leaderboard', {'Alice': 100, 'Bob': 200, 'Charlie': 150})

# 获取排名（0开始）
r.zrevrank('leaderboard', 'Alice')  # 降序排名

# 获取分数
r.zscore('leaderboard', 'Alice')

# 按分数范围获取
r.zrangebyscore('leaderboard', 100, 200)
r.zrevrangebyscore('leaderboard', 200, 100)  # 降序

# 更新分数
r.zincrby('leaderboard', 50, 'Alice')

# Top N
r.zrevrange('leaderboard', 0, 9, withscores=True)
```

---

## 4. 缓存策略

### Cache-Aside 实现

```python
import redis
import json
from typing import Optional, Any

class CacheService:
    def __init__(self, redis_client: redis.Redis, prefix: str = 'cache'):
        self.redis = redis_client
        self.prefix = prefix

    def _make_key(self, key: str) -> str:
        return f'{self.prefix}:{key}'

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        data = self.redis.get(self._make_key(key))
        if data:
            return json.loads(data)
        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存"""
        self.redis.setex(
            self._make_key(key),
            ttl,
            json.dumps(value)
        )

    def delete(self, key: str):
        """删除缓存"""
        self.redis.delete(self._make_key(key))

    def get_or_set(self, key: str, fetch_func, ttl: int = 3600) -> Any:
        """获取缓存，不存在则调用 fetch_func 并缓存"""
        cached = self.get(key)
        if cached is not None:
            return cached

        data = fetch_func()
        if data is not None:
            self.set(key, data, ttl)
        return data
```

### 在 FastAPI 中使用

```python
from fastapi import FastAPI, Depends
import redis
import json

app = FastAPI()

# Redis 连接池
redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0)

def get_redis():
    return redis.Redis(connection_pool=redis_pool)

@app.get('/users/{user_id}')
async def get_user(user_id: int, r: redis.Redis = Depends(get_redis)):
    # 尝试从缓存获取
    cache_key = f'user:{user_id}'
    cached = r.get(cache_key)

    if cached:
        return json.loads(cached)

    # 缓存不存在，查询数据库
    user = db.query(User).filter(User.id == user_id).first()

    if user:
        # 写入缓存，过期时间1小时
        r.setex(cache_key, 3600, json.dumps({
            'id': user.id,
            'username': user.username,
            'email': user.email
        }))

    return user

@app.post('/users/{user_id}')
async def update_user(user_id: int, data: dict, r: redis.Redis = Depends(get_redis)):
    # 更新数据库
    user = db.query(User).filter(User.id == user_id).first()
    # ... 更新逻辑

    # 删除缓存
    cache_key = f'user:{user_id}'
    r.delete(cache_key)

    return {'status': 'success'}
```

---

## 5. 缓存问题处理

### 缓存穿透

```python
# 问题：查询不存在的数据，每次都穿透到数据库
# 解决：布隆过滤器 或 缓存空值

def get_user(self, user_id: int):
    # 1. 布隆过滤器检查
    if not self.bloom_filter.exists(user_id):
        return None  # 一定不存在

    # 2. 查缓存
    cached = self.redis.get(f'user:{user_id}')
    if cached == 'NULL':  # 空值缓存
        return None
    if cached:
        return json.loads(cached)

    # 3. 查数据库
    user = db.query(User).get(user_id)

    # 4. 写入缓存（包括空值）
    if user:
        self.redis.setex(f'user:{user_id}', 3600, json.dumps(user))
    else:
        # 缓存空值，短过期时间
        self.redis.setex(f'user:{user_id}', 60, 'NULL')

    return user
```

### 缓存击穿

```python
# 问题：热点 key 过期，瞬间大量请求打到数据库
# 解决：互斥锁 或 永不过期 + 异步更新

import threading

def get_user_with_lock(self, user_id: int):
    cache_key = f'user:{user_id}'

    # 1. 先查缓存
    cached = self.redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # 2. 获取锁
    lock_key = f'lock:{cache_key}'
    lock_acquired = self.redis.set(lock_key, '1', nx=True, ex=10)

    if lock_acquired:
        try:
            # 3. 双重检查
            cached = self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

            # 4. 查数据库
            user = db.query(User).get(user_id)

            # 5. 写入缓存
            if user:
                self.redis.setex(cache_key, 3600, json.dumps(user))

            return user
        finally:
            self.redis.delete(lock_key)
    else:
        # 等待其他线程写入
        import time
        for _ in range(3):
            time.sleep(0.1)
            cached = self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        # 兜底：查数据库
        return db.query(User).get(user_id)
```

### 缓存雪崩

```python
# 问题：大量缓存同时过期，导致数据库压力
# 解决：过期时间随机化 + 永不过期 + 熔断降级

def set_with_random_ttl(self, key: str, value: Any, base_ttl: int = 3600):
    import random
    # 过期时间加随机偏移：base_ttl + random(0, base_ttl * 0.2)
    ttl = base_ttl + int(random.uniform(0, base_ttl * 0.2))
    self.redis.setex(key, ttl, json.dumps(value))

# 或使用逻辑过期（不设置过期时间）
def get_user_logical_expire(self, user_id: int):
    cache_key = f'user:{user_id}'

    # 1. 获取缓存
    cached = self.redis.get(cache_key)
    if not cached:
        return db.query(User).get(user_id)

    data = json.loads(cached)

    # 2. 检查是否过期
    if time.time() - data['cache_time'] > data['ttl']:
        # 异步更新（不阻塞）
        threading.Thread(
            target=self._refresh_cache,
            args=(user_id,)
        ).start()
        # 返回旧数据（不阻塞）
        return data['value']

    return data['value']
```

---

## 6. 分布式锁

```python
import redis
import uuid
import time

class DistributedLock:
    def __init__(self, redis_client: redis.Redis, lock_name: str, timeout: int = 10):
        self.redis = redis_client
        self.lock_name = f'lock:{lock_name}'
        self.timeout = timeout
        self.token = str(uuid.uuid4())

    def acquire(self, blocking: bool = True, blocking_timeout: int = 5) -> bool:
        """获取锁"""
        end_time = time.time() + blocking_timeout

        while True:
            if self.redis.set(self.lock_name, self.token, nx=True, ex=self.timeout):
                return True

            if not blocking or time.time() > end_time:
                return False

            time.sleep(0.01)

    def release(self):
        """释放锁"""
        # 使用 Lua 脚本确保只释放自己的锁
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        self.redis.eval(script, 1, self.lock_name, self.token)

    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"Failed to acquire lock: {self.lock_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


# 使用
lock = DistributedLock(r, 'update_user_1')
try:
    # 临界区操作
    user.balance -= 100
    db.commit()
finally:
    lock.release()

# 或使用上下文管理器
with DistributedLock(r, 'update_user_1'):
    user.balance -= 100
    db.commit()
```

---

## 7. 实战练习

### 完整缓存方案

```python
import redis
import json
import time
from typing import Optional, Callable, Any
from functools import wraps

class CacheManager:
    def __init__(self, redis_url: str = 'redis://localhost:6379/0'):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    def cache(self, key_prefix: str, ttl: int = 3600, key_func: Optional[Callable] = None):
        """缓存装饰器"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 生成缓存 key
                if key_func:
                    cache_key = f'{key_prefix}:{key_func(*args, **kwargs)}'
                else:
                    cache_key = f'{key_prefix}:{":".join(str(a) for a in args)}'

                # 尝试获取缓存
                cached = self.redis.get(cache_key)
                if cached:
                    return json.loads(cached)

                # 调用原函数
                result = await func(*args, **kwargs)

                # 写入缓存
                if result is not None:
                    self.redis.setex(cache_key, ttl, json.dumps(result, default=str))

                return result

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if key_func:
                    cache_key = f'{key_prefix}:{key_func(*args, **kwargs)}'
                else:
                    cache_key = f'{key_prefix}:{":".join(str(a) for a in args)}'

                cached = self.redis.get(cache_key)
                if cached:
                    return json.loads(cached)

                result = func(*args, **kwargs)

                if result is not None:
                    self.redis.setex(cache_key, ttl, json.dumps(result, default=str))

                return result

            # 返回对应版本
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator


# 使用示例
cache = CacheManager()

class UserService:
    def __init__(self, db, cache: CacheManager):
        self.db = db
        self.cache = cache

    @cache.cache('user', ttl=1800, key_func=lambda user_id: str(user_id))
    def get_user(self, user_id: int):
        """获取用户（带缓存）"""
        return self.db.query(User).get(user_id)

    def update_user(self, user_id: int, **kwargs):
        """更新用户（清除缓存）"""
        user = self.db.query(User).get(user_id)
        for key, value in kwargs.items():
            setattr(user, key, value)
        self.db.commit()

        # 清除缓存
        self.cache.redis.delete(f'user:{user_id}')

    @cache.cache('user_orders', ttl=600, key_func=lambda user_id: str(user_id))
    def get_user_orders(self, user_id: int):
        """获取用户订单"""
        return self.db.query(Order).filter(Order.user_id == user_id).all()
```

---

## 今日总结

- [ ] 缓存模式：Cache-Aside、Read-Through、Write-Through
- [ ] Redis：String、Hash、List、Set、ZSet
- [ ] Cache-Aside：读先缓存，写先数据库再删缓存
- [ ] 缓存穿透：布隆过滤器 + 缓存空值
- [ ] 缓存击穿：互斥锁 + 永不过期
- [ ] 缓存雪崩：随机 TTL + 熔断降级
- [ ] 分布式锁：SETNX + Lua 脚本

---

*第 28 天 / 330 天*
*Python 后端 - Redis 缓存与数据库*
