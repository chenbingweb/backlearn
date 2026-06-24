# 第 32 天：String 与 Hash 进阶

## 学习目标

- 深入理解 String 编码
- 掌握 Hash 内部实现
- 学会批量操作优化
- 掌握应用场景实践

---

## 1. String 编码详解

### 三种编码

```bash
# String 类型有三种编码方式
# 根据值的大小和类型自动选择

# 1. int：整数值
SET num 12345
OBJECT ENCODING num
# "int"

# 2. embstr：短字符串（<= 39 字节）
SET name "Alice"
OBJECT ENCODING name
# "embstr"

# 3. raw：长字符串（> 39 字节）
SET content "这是一段很长的内容..."
OBJECT ENCODING content
# "raw"
```

### 编码转换

```bash
# int -> raw
SET num 123
INCR num              # int
APPEND num "abc"     # 变成 raw

# embstr -> raw
SET name "Alice"      # embstr
APPEND name " Chen"   # 超过39字节，变成 raw

# 注意：embstr 是只读的，修改会变成 raw
```

### 内存优化

```python
# 1. 数字类型用 String，不是 Hash
# ✅ 好
r.set('user:1001:views', '100')
r.incr('user:1001:views')

# ❌ 差
r.hset('user:1001', 'views', '100')

# 2. 短字符串用 String，不用 Hash
# ✅ 好
r.set('user:1001', '{"name":"Alice","age":25}')

# ❌ 差
r.hset('user:1001', 'name', 'Alice')
r.hset('user:1001', 'age', '25')
```

---

## 2. Hash 内部实现

### 编码选择

```bash
# 小 Hash：ziplist（压缩列表）
# 条件：字段数 < 512 且 每字段值 < 64 字节
HSET user:1001 name "Alice"
OBJECT ENCODING user:1001
# "ziplist"

# 大 Hash：hashtable（哈希表）
# 超出上述条件时转换
HSET user:1001 name "Alice" age "25" email "alice@example.com" city "Beijing" country "China" phone "12345678901" address "..." ...
OBJECT ENCODING user:1001
# "hashtable"
```

### ziplist vs hashtable

```
ziplist（压缩列表）：
┌─────────────────────────────────────────┐
│ zlbytes │ zltail │ zllen │ entry* │ zlend │
└─────────────────────────────────────────┘
- 内存连续，节省空间
- 增删需要移动元素
- 适合小数据量

hashtable（哈希表）：
┌─────────────────────────────────────────┐
│ dictEntry*[] │ dictht[2] │ rehashidx   │
└─────────────────────────────────────────┘
- O(1) 增删查
- 需要额外内存
- 适合大数据量
```

---

## 3. 批量操作实战

### Pipeline vs MGET/MSET

```python
import redis
import time

r = redis.Redis(decode_responses=True)

# ============ 普通逐个操作 ============
keys = [f'user:{i}' for i in range(1000)]

start = time.time()
for key in keys:
    r.get(key)
t1 = time.time() - start
print(f'逐个 GET: {t1:.3f}s')

# ============ Pipeline ============
pipe = r.pipeline()
for key in keys:
    pipe.get(key)
start = time.time()
pipe.execute()
t2 = time.time() - start
print(f'Pipeline: {t2:.3f}s')

# ============ MGET ============
start = time.time()
r.mget(keys)
t3 = time.time() - start
print(f'MGET: {t3:.3f}s')

# 对比结果
print(f'Pipeline 加速: {t1/t2:.1f}x')
print(f'MGET 加速: {t1/t3:.1f}x')
```

### Hash 批量操作

```python
# ============ Hash 批量操作 ============

# 批量设置
pipe = r.pipeline()
for i in range(100):
    pipe.hset(f'user:{i}', mapping={
        'name': f'User{i}',
        'age': 20 + i % 50,
        'city': 'Beijing'
    })
pipe.execute()

# 批量获取
pipe = r.pipeline()
for i in range(100):
    pipe.hgetall(f'user:{i}')
results = pipe.execute()

# 批量检查存在
pipe = r.pipeline()
for i in range(100):
    pipe.exists(f'user:{i}')
results = pipe.execute()
```

### 计数器批量处理

```python
# 批量递增
pipe = r.pipeline()
for i in range(100):
    pipe.incr(f'counter:{i}')
results = pipe.execute()

# 批量获取计数器
pipe = r.pipeline()
for i in range(100):
    pipe.get(f'counter:{i}')
results = pipe.execute()
```

---

## 4. 应用场景实践

### 用户画像

```python
class UserProfileCache:
    """用户画像缓存"""

    def __init__(self, redis_client):
        self.r = redis_client

    def set_profile(self, user_id, profile_data):
        """设置用户画像"""
        key = f'profile:{user_id}'

        # 使用 Hash 存储多维度属性
        mapping = {
            'basic': json.dumps(profile_data.get('basic', {})),
            'behavior': json.dumps(profile_data.get('behavior', {})),
            'preference': json.dumps(profile_data.get('preference', {})),
            'level': str(profile_data.get('level', 0)),
            'score': str(profile_data.get('score', 0)),
        }

        pipe = self.r.pipeline()
        pipe.hset(key, mapping=mapping)
        pipe.expire(key, 86400)  # 24小时
        pipe.execute()

    def get_profile(self, user_id):
        """获取用户画像"""
        key = f'profile:{user_id}'
        data = self.r.hgetall(key)

        if not data:
            return None

        return {
            'basic': json.loads(data.get('basic', '{}')),
            'behavior': json.loads(data.get('behavior', '{}')),
            'preference': json.loads(data.get('preference', '{}')),
            'level': int(data.get('level', 0)),
            'score': int(data.get('score', 0)),
        }

    def update_score(self, user_id, score_delta):
        """更新用户积分"""
        key = f'profile:{user_id}'
        return self.r.hincrby(key, 'score', score_delta)

    def get_top_users(self, count=100):
        """获取积分排行"""
        # 使用 ZSet 单独维护排行
        return self.r.zrevrange('user:leaderboard', 0, count - 1, withscores=True)
```

### 配置中心

```python
class ConfigCache:
    """配置中心"""

    def __init__(self, redis_client):
        self.r = redis_client
        self.config_prefix = 'config:'

    def set_config(self, app, env, key, value):
        """设置配置"""
        config_key = f'{self.config_prefix}{app}:{env}'
        self.r.hset(config_key, key, value)

    def get_config(self, app, env, key):
        """获取配置"""
        config_key = f'{self.config_prefix}{app}:{env}'
        return self.r.hget(config_key, key)

    def get_all_configs(self, app, env):
        """获取所有配置"""
        config_key = f'{self.config_prefix}{app}:{env}'
        return self.r.hgetall(config_key)

    def delete_config(self, app, env, key):
        """删除配置"""
        config_key = f'{self.config_prefix}{app}:{env}'
        self.r.hdel(config_key, key)

    def refresh_config(self, app, env, configs):
        """刷新配置（批量设置）"""
        config_key = f'{self.config_prefix}{app}:{env}'

        pipe = self.r.pipeline()
        pipe.delete(config_key)
        pipe.hset(config_key, mapping=configs)
        pipe.expire(config_key, 86400)
        pipe.execute()
```

---

## 5. 性能优化技巧

### 键设计原则

```python
# 1. 键名要简短
# ✅ 好
r.set('u:1001', data)        # user:1001 -> u:1001
r.hset('u:1001:p', ...)      # user:1001:profile -> u:1001:p

# ❌ 差
r.set('user:1001:profile:info:basic', data)

# 2. 使用冒号分隔层级
# ✅ 好：'order:1001:items'
# ❌ 差：'order1001items'

# 3. 相关信息放一起
# ✅ 好：Hash 存储用户属性
r.hset('user:1001', mapping={'name': 'Alice', 'age': 25})

# ❌ 差：多个 String
r.set('user:1001:name', 'Alice')
r.set('user:1001:age', '25')
```

### 内存优化

```python
# 1. 使用压缩列表（控制字段数量和大小）
# Hash 字段数 < 512
# 每字段值 < 64 字节

# 2. 数字用 String，不是 Hash
# ✅ 好
r.set('user:1001:age', '25')
r.incr('user:1001:age')

# ❌ 差
r.hset('user:1001', 'age', '25')
r.hincrby('user:1001', 'age', 1)

# 3. 批量操作减少网络往返
pipe = r.pipeline()
for _ in range(1000):
    pipe.incr('counter')
pipe.execute()
```

### 连接池优化

```python
import redis

# 1. 使用连接池
pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50,
    decode_responses=True
)

# 2. 复用连接
def get_redis():
    return redis.Redis(connection_pool=pool)

# 3. 正确关闭连接
# redis-py 会自动归还连接到池
r = get_redis()
r.get('key')
r.close()  # 或 del r，归还到池
```

---

## 今日总结

- [ ] String 编码：int、embstr、raw，自动转换
- [ ] Hash 编码：ziplist（小数据）、hashtable（大数据）
- [ ] Pipeline：减少网络往返，提升性能
- [ ] MGET/MSET：批量获取/设置
- [ ] 键设计：简短、使用冒号分层
- [ ] 连接池：复用连接，减少开销

---

*第 32 天 / 330 天*
*Python 后端 - String 与 Hash 进阶*
