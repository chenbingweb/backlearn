# 第 31 天：String 与 Hash 操作

## 学习目标

- 深入掌握 String 类型操作
- 深入掌握 Hash 类型操作
- 学会在实际场景中应用
- 掌握批量操作优化

---

## 1. String 进阶操作

### 数值操作

```bash
# 计数器
SET counter 0
INCR counter          # 原子递增，返回新值
INCRBY counter 5      # 指定增量
INCRBYFLOAT counter 0.5  # 浮点增量

# 字符串操作
APPEND name " Chen"   # 追加字符串，返回长度
STRLEN name           # 获取长度

# 位操作
SETBIT flags 0 1     # 设置第0位为1
GETBIT flags 0        # 获取第0位
BITCOUNT flags        # 统计1的位数
BITOP AND result flags1 flags2  # 位运算

# 范围操作
SET message "Hello World"
GETRANGE message 0 4     # "Hello"
SETRANGE message 6 "Redis" # 替换，从第6位开始
```

### 批量操作

```bash
# MSET/MGET
MSET user:1001:name "Alice" user:1001:age "25" user:1002:name "Bob"
MGET user:1001:name user:1001:age user:1002:name

# 批量操作优势
# 普通方式：10次 GET = 10次网络往返
# MGET：1次网络往返
```

### 过期操作

```bash
# 设置过期
SET token "abc123" EX 3600        # 设置值和过期时间
SET token "abc123" PX 3600000     # 毫秒过期
SET token "abc123" EX 3600 NX     # 不存在则设置（分布式锁）

# 查询过期
TTL token                         # 秒
PTTL token                        # 毫秒

# 移除过期
PERSIST token
```

---

## 2. String 应用场景

### 缓存

```python
import json
import redis

r = redis.Redis(decode_responses=True)

def get_user(user_id):
    """用户缓存"""
    cache_key = f'user:{user_id}'

    # 1. 查缓存
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    # 2. 查数据库
    user = db.query(User).get(user_id)

    # 3. 写入缓存
    if user:
        r.setex(cache_key, 3600, json.dumps(user.to_dict()))

    return user
```

### 计数器

```python
def increment_views(article_id):
    """文章浏览量"""
    key = f'article:{article_id}:views'

    # 原子递增
    views = r.incr(key)

    # 每天重置一次（设置当天过期）
    if views == 1:
        r.expire(key, 86400)  # 24小时

    return views

def get_article_stats(article_id):
    """获取文章统计"""
    pipe = r.pipeline()
    pipe.get(f'article:{article_id}:views')
    pipe.get(f'article:{article_id}:likes')
    pipe.get(f'article:{article_id}:comments')
    return pipe.execute()
```

### 分布式 ID

```python
def generate_order_id():
    """订单号生成器"""
    # 格式：时间戳 + 序列号
    timestamp = int(time.time() * 1000)
    sequence = r.incr('order:sequence')

    return f'{timestamp}{sequence:06d}'

def generate_user_id():
    """用户 ID 生成器（雪花算法简化版）"""
    # 使用 Redis INCR 保证全局唯一
    user_id = r.incr('global:user:id')
    return user_id
```

---

## 3. Hash 进阶操作

### 基本操作

```bash
# 设置
HSET user:1001 name "Alice" age "25" city "Beijing"
HSETNX user:1001 email "alice@test.com"  # 不存在则设置

# 获取
HGET user:1001 name
HMGET user:1001 name age city
HGETALL user:1001                    # 获取所有字段值

# 字段操作
HINCRBY user:1001 age 1             # 整数字段递增
HINCRBYFLOAT user:1001 balance 100.5  # 浮点递增
HLEN user:1001                       # 字段数量
HEXISTS user:1001 name               # 字段是否存在

# 删除
HDEL user:1001 city email            # 删除多个字段

# 遍历
HKEYS user:1001                      # 所有字段名
HVALS user:1001                      # 所有字段值
```

### 游标遍历

```bash
# 大 Hash 遍历（Redis 4.0+）
HSCAN user:1001:large CURSOR 0 COUNT 100
# 返回：[next_cursor, [field1, value1, field2, value2, ...]]

# 使用
HSCAN user:1001:large CURSOR 0 MATCH product:* COUNT 100
```

---

## 4. Hash 应用场景

### 对象存储

```python
def cache_user(user):
    """缓存用户对象"""
    key = f'user:{user.id}'

    # 使用 Hash 存储用户属性
    r.hset(key, mapping={
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'age': str(user.age),
        'created_at': user.created_at.isoformat()
    })

    # 设置过期时间
    r.expire(key, 3600)

def get_cached_user(user_id):
    """获取缓存用户"""
    key = f'user:{user_id}'

    # 检查是否存在
    if not r.exists(key):
        return None

    # 获取所有字段
    data = r.hgetall(key)

    if not data:
        return None

    # 转换为用户对象
    return User(
        id=int(data['id']),
        name=data['name'],
        email=data['email'],
        age=int(data['age']),
        created_at=datetime.fromisoformat(data['created_at'])
    )

def update_user_field(user_id, field, value):
    """更新用户单个字段"""
    key = f'user:{user_id}'
    r.hset(key, field, value)
    # 重置过期时间
    r.expire(key, 3600)
```

### 购物车

```python
def add_to_cart(user_id, product_id, quantity):
    """添加商品到购物车"""
    key = f'cart:{user_id}'

    # 字段：商品ID，值：数量
    if quantity <= 0:
        r.hdel(key, str(product_id))
    else:
        r.hset(key, str(product_id), str(quantity))

def get_cart(user_id):
    """获取购物车"""
    key = f'cart:{user_id}'
    cart = r.hgetall(key)

    return {int(k): int(v) for k, v in cart.items()}

def remove_from_cart(user_id, product_id):
    """从购物车移除"""
    r.hdel(f'cart:{user_id}', str(product_id))

def clear_cart(user_id):
    """清空购物车"""
    r.delete(f'cart:{user_id}')
```

### 用户标签

```python
def add_user_tag(user_id, tag):
    """为用户添加标签"""
    r.hset(f'user:tags:{user_id}', tag, time.time())

def remove_user_tag(user_id, tag):
    """移除用户标签"""
    r.hdel(f'user:tags:{user_id}', tag)

def get_user_tags(user_id):
    """获取用户所有标签"""
    return list(r.hgetall(f'user:tags:{user_id}').keys())

def get_users_with_tags(tags):
    """获取同时拥有多个标签的用户"""
    pipe = r.pipeline()
    for tag in tags:
        pipe.keys(f'user:tags:*:{tag}')
    return pipe.execute()
```

---

## 5. 性能优化

### Pipeline 批量操作

```python
# 不使用 Pipeline：10次操作 = 10次网络往返
for user_id in user_ids:
    r.get(f'user:{user_id}:name')

# 使用 Pipeline：1次网络往返
pipe = r.pipeline()
for user_id in user_ids:
    pipe.get(f'user:{user_id}:name')
names = pipe.execute()

# Pipeline 执行批量操作
pipe = r.pipeline()
pipe.set('key1', 'value1')
pipe.incr('counter')
pipe.hset('user:1', 'name', 'Alice')
pipe.expire('user:1', 3600)
results = pipe.execute()  # 返回每个命令的结果列表
```

### 事务（MULTI/EXEC）

```python
# 事务：保证原子性
pipe = r.pipeline(transaction=True)
pipe.set('key1', 'value1')
pipe.incr('counter')
pipe.hset('user:1', 'name', 'Bob')
results = pipe.execute()  # 全部成功或全部失败

# WATCH：乐观锁
def update_user_balance(user_id, amount):
    """乐观锁更新余额"""
    key = f'user:{user_id}:balance'

    while True:
        try:
            # 监视 key
            r.watch(key)

            # 获取当前值
            current = r.get(key)
            if current is None:
                r.unwatch()
                return None

            new_balance = int(current) + amount

            # 开启事务
            pipe = r.pipeline(transaction=True)
            pipe.multi()
            pipe.set(key, str(new_balance))
            pipe.execute()
            return new_balance

        except redis.WatchError:
            # 其他客户端修改了 key，重试
            continue
```

### Lua 脚本

```python
# Lua 脚本：保证原子性，比 Pipeline 更强大
INCREMENT_AND_EXPIRE = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""

def increment_with_expire(key, ttl):
    """递增并设置过期"""
    return r.eval(INCREMENT_AND_EXPIRE, 1, key, ttl)

# 限流 Lua 脚本
RATE_LIMIT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local current = tonumber(redis.call('GET', key) or '0')

if current >= limit then
    return 0
end

current = redis.call('INCR', key)
if current == 1 then
    redis.call('EXPIRE', key, window)
end

return current
"""

def rate_limit(key, limit, window):
    """限流"""
    result = r.eval(RATE_LIMIT, 1, key, limit, window)
    return result > 0
```

---

## 6. 实战练习

### 实现短链接服务

```python
import hashlib
import base62

class ShortUrlService:
    def __init__(self, redis_client):
        self.r = redis_client

    def encode(self, long_url):
        """生成短链接"""
        # 生成短码
        hash_val = hashlib.md5(long_url.encode()).hexdigest()[:8]
        short_code = base62.encode(int(hash_val, 16))

        # 存储映射
        short_url = f'http://short.url/{short_code}'
        self.r.hset('short_urls', short_code, long_url)
        self.r.hset('long_urls', long_url, short_code)

        # 访问统计
        self.r.hincrby('url:stats', f'{short_code}:views', 1)

        return short_url

    def decode(self, short_code):
        """获取原始链接"""
        return self.r.hget('short_urls', short_code)

    def get_stats(self, short_code):
        """获取访问统计"""
        return {
            'views': int(self.r.hget('url:stats', f'{short_code}:views') or 0)
        }

    def is_short_url(self, url):
        """检查是否已存在"""
        return self.r.hget('long_urls', url) is not None
```

---

## 今日总结

- [ ] String：`INCR`、`APPEND`、`SETBIT`、`SETNX`
- [ ] Hash：`HSET`、`HGETALL`、`HINCRBY`
- [ ] Pipeline：减少网络往返，提升性能
- [ ] 事务（MULTI/EXEC）：保证原子性
- [ ] Lua 脚本：复杂原子操作
- [ ] 过期时间：`EX`、`PX`、`TTL`

---

*第 31 天 / 330 天*
*Python 后端 - String 与 Hash 操作*
