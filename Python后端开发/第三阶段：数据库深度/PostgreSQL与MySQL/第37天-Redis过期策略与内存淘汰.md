# 第 37 天：Redis 过期策略与内存淘汰

## 学习目标

- 理解 Redis 过期机制
- 掌握过期删除策略
- 掌握内存淘汰算法
- 学会内存管理

---

## 1. 过期机制

### 设置过期

```bash
# 设置过期时间
EXPIRE user:1001:cache 3600      # 1小时后过期
EXPIREAT user:1001:cache 1704067200  # 过期时间戳
PEXPIRE user:1001:cache 3600000    # 毫秒

# 移除过期（永不过期）
PERSIST user:1001:cache

# 查询剩余时间
TTL user:1001:cache    # 秒（-1 永不过期，-2 不存在）
PTTL user:1001:cache  # 毫秒
```

### 过期精度

```bash
# 对于字符串类型，SET 操作会清除过期
SET key value
EXPIRE key 100
SET key new_value    # 过期时间被清除

# 解决方案：SETEX（原子操作）
SETEX key 100 value  # 原子设置值和过期时间

# SET 带过期参数
SET key value EX 100 PX 3600000 NX
```

---

## 2. 过期删除策略

### 三种策略

```
┌─────────────────────────────────────────────────────┐
│                 过期删除策略                          │
├─────────────┬─────────────┬────────────────────────┤
│   定时删除   │   惰性删除   │       定期删除           │
│ (定时器)     │ (访问时)    │    (定期扫描)            │
└─────────────┴─────────────┴────────────────────────┘
```

### 定时删除

```markdown
原理：用定时器 timer 主动删除过期键

优点：内存友好，键一过期就删除
缺点：CPU 不友好，可能影响性能

实现：时间事件（serverCron）
```

### 惰性删除

```markdown
原理：访问键时检查是否过期，过期则删除

优点：CPU 友好，只删除访问到的
缺点：内存不友好，过期键可能一直占用内存

实现：getCommand 等读写命令
```

### 定期删除

```markdown
原理：每隔一段时间，扫描expires字典，删除过期键

优点：平衡 CPU 和内存
缺点：可能删除不及时

实现：serverCron 中的 databasesCron
```

### Redis 采用的策略

```bash
# Redis 采用：惰性删除 + 定期删除

# 惰性删除：每次访问 key 时检查
GET key    # 内部检查是否过期

# 定期删除：serverCron 每 100ms 执行一次
HZ 10      # 每秒执行 10 次（Redis 5.0+）
```

### 定期删除实现

```c
// Redis 源码逻辑（简化）
void databasesCron(void) {
    // 遍历所有数据库
    for (j = 0; j < server.dbnum; j++) {
        // 每次只随机检查部分 key
        int expired = activeExpireCycle(try_expire);

        // 如果删除过多，下次减少检查数量
        if (server.active_expire_effort > 1) {
            // 调整检查数量
        }
    }
}
```

---

## 3. 内存淘汰算法

### 内存上限

```bash
# 设置最大内存
maxmemory 2gb

# 0 表示不限制（不推荐）
# 不设置时，物理内存不足会导致 OOM

# 内存计算
INFO memory
# used_memory: 1234567
# used_memory_human: 1.23M
# maxmemory: 2147483648
```

### 淘汰策略

```bash
# 设置淘汰策略
maxmemory-policy allkeys-lru

# 可选策略
```

### 8种淘汰策略

```
┌─────────────────────────────────────────────────────┐
│                  淘汰策略分类                         │
├────────────────────┬────────────────────────────────┤
│     不淘汰         │   noeviction                    │
├────────────────────┼────────────────────────────────┤
│   全局淘汰          │  allkeys-lru                   │
│   (所有 key)        │  allkeys-random                 │
├────────────────────┼────────────────────────────────┤
│   带过期淘汰        │  volatile-lru                   │
│   (只淘汰过期键)    │  volatile-random                 │
│                    │  volatile-ttl                    │
│                    │  volatile-lfu                    │
└────────────────────┴────────────────────────────────┘
```

### 策略详解

```bash
# 1. noeviction（不淘汰）
# 内存满时，不删除任何键，返回错误
# 写入操作会失败
maxmemory-policy noeviction

# 2. allkeys-lru（全局 LRU）
# 在所有 key 中，淘汰最近最少使用的
# 推荐用于缓存场景
maxmemory-policy allkeys-lru

# 3. allkeys-random（全局随机）
# 随机淘汰任意 key
maxmemory-policy allkeys-random

# 4. volatile-lru（过期 LRU）
# 只在设置了过期时间的 key 中淘汰
# 适用于：缓存 + 持久化混合场景
maxmemory-policy volatile-lru

# 5. volatile-random（过期随机）
# 随机淘汰设置了过期时间的 key
maxmemory-policy volatile-random

# 6. volatile-ttl（过期时间优先）
# 淘汰存活时间最短的 key
# 优先删除即将过期的 key
maxmemory-policy volatile-ttl

# 7. volatile-lfu（过期 LFU）
# 淘汰使用频率最低的 key（带过期时间）
# Redis 4.0+
maxmemory-policy volatile-lfu

# 8. allkeys-lfu（全局 LFU）
# 在所有 key 中淘汰使用频率最低的
# Redis 4.0+
maxmemory-policy allkeys-lfu
```

### LRU 算法

```bash
# LRU：Least Recently Used（最近最少使用）
# 通过访问时间判断

# 配置 LRU 采样数量
maxmemory-samples 5
# Redis 不使用真正的 LRU，而是近似 LRU

# 近似 LRU：
# 随机采样 5 个 key
# 淘汰其中最旧的
# 采样越多越接近真正的 LRU，但消耗更多 CPU
```

### LFU 算法

```bash
# LFU：Least Frequently Used（最不经常使用）
# 通过访问频率判断

# LFU 配置
lfu-log-factor 10     # 频率对数因子（1-100）
lfu-decay-time 1      # 频率衰减时间（分钟）

# lfu-log-factor 影响频率最大值
# factor 1:   max frequency ≈ 100
# factor 10:  max frequency ≈ 1000
# factor 100: max frequency ≈ 10000
```

---

## 4. 过期与淘汰关系

```
┌─────────────────────────────────────────────────────┐
│                    键的生命周期                       │
├─────────────────────────────────────────────────────┤
│                                                      │
│   创建 ────► 过期 ────► 删除                         │
│     │           │                                   │
│     │           │ 惰性删除/定期删除                   │
│     │           │                                   │
│     │           ▼                                   │
│     │      内存淘汰（如果内存不足）                   │
│     │           │                                   │
│     │           │                                   │
│     └───────────┴──────────────────────────────────► │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 选择策略

| 场景 | 推荐策略 | 说明 |
|------|---------|------|
| 缓存 | allkeys-lru | 自动淘汰最久未使用的 |
| 缓存（偶有持久化） | volatile-lru | 保留非过期数据 |
| 队列/会话 | allkeys-random | 随机淘汰 |
| 限流凭证 | volatile-ttl | 优先删除即将过期的 |
| 热点缓存 | allkeys-lfu | 保留高频访问的 |

---

## 5. Python 内存管理

```python
import redis

r = redis.Redis(host='localhost', port=6379)

# 查看内存使用
def get_memory_info():
    info = r.info('memory')
    return {
        'used_memory': info['used_memory'],
        'used_memory_human': info['used_memory_human'],
        'maxmemory': info['maxmemory'],
        'maxmemory_human': info['maxmemory_human'],
        'mem_fragmentation_ratio': info['mem_fragmentation_ratio'],
    }

# 设置内存上限
r.config_set('maxmemory', '1gb')
r.config_set('maxmemory-policy', 'allkeys-lru')

# 获取当前淘汰策略
policy = r.config_get('maxmemory-policy')
print(policy)

# 查看 key 过期时间
def get_key_ttl(key_pattern):
    """查看匹配 key 的过期时间"""
    keys = r.keys(key_pattern)
    result = []
    for key in keys:
        ttl = r.ttl(key)
        result.append({'key': key, 'ttl': ttl})
    return result

# 主动清理过期 key
def cleanup_expired():
    """定期清理过期 key"""
    # 触发主动过期检查
    r.expire('temp:key', -1)  # 强制删除

# 查看内存碎片
def get_fragmentation():
    info = r.info('memory')
    ratio = info['mem_fragmentation_ratio']
    return {
        'ratio': ratio,
        'status': '正常' if ratio < 1.5 else '警告' if ratio < 2 else '严重'
    }

# 整理内存碎片
def defragment():
    """内存碎片整理"""
    r.memory_defrag()
```

---

## 6. 生产实践

### 缓存预热

```python
def cache_warm_up(redis_client, db_client):
    """缓存预热"""
    # 1. 加载热门商品
    hot_products = db_client.query(
        "SELECT * FROM products ORDER BY view_count DESC LIMIT 1000"
    )

    pipe = redis_client.pipeline()
    for product in hot_products:
        key = f'product:{product.id}'
        pipe.hset(key, mapping={
            'id': product.id,
            'name': product.name,
            'price': str(product.price),
            'stock': product.stock,
        })
        pipe.expire(key, 86400)  # 24小时
    pipe.execute()

    # 2. 加载热门分类
    hot_categories = db_client.query(
        "SELECT * FROM categories ORDER BY product_count DESC LIMIT 100"
    )

    pipe = redis_client.pipeline()
    for category in hot_categories:
        key = f'category:{category.id}'
        pipe.set(f'category:{category.id}:name', category.name, ex=86400)
    pipe.execute()
```

### 过期策略配置

```python
# 推荐配置
MAX_MEMORY_CONFIG = {
    'maxmemory': '2gb',
    'maxmemory-policy': 'allkeys-lru',
    'maxmemory-samples': 5,
    'lfu-log-factor': 10,
    'lfu-decay-time': 1,
}

def apply_redis_config(redis_client):
    """应用推荐的 Redis 配置"""
    for key, value in MAX_MEMORY_CONFIG.items():
        redis_client.config_set(key, value)

# 监控内存使用
def monitor_memory(redis_client, threshold_mb=1800):
    """监控内存使用，超过阈值告警"""
    info = redis_client.info('memory')
    used_mb = info['used_memory'] / (1024 * 1024)

    if used_mb > threshold_mb:
        print(f"警告：Redis 内存使用 {used_mb:.2f}MB，超过阈值 {threshold_mb}MB")

    return {
        'used_mb': used_mb,
        'threshold_mb': threshold_mb,
        'need_alert': used_mb > threshold_mb
    }
```

---

## 7. 监控命令

```bash
# 查看过期 key 统计
INFO keyspace
# db0:keys=1000,expires=900,avg_ttl=3600000

# 查看内存使用
INFO memory
# used_memory: 1048576
# maxmemory: 2147483648
# mem_fragmentation_ratio: 1.25

# 查看淘汰统计
INFO stats
# evicted_keys: 0
# expired_keys: 100

# 实时内存
redis-cli INFO memory | grep used_memory

# 查看大 key
redis-cli --bigkeys
redis-cli --scan | head -100 | xargs -I{} redis-cli DEBUG OBJECT ENCODING {}
```

---

## 今日总结

- [ ] 过期策略：惰性删除 + 定期删除
- [ ] 定时删除：CPU 友好但性能差
- [ ] 惰性删除：访问时删除，内存可能堆积
- [ ] 定期删除：每隔 100ms 扫描部分 key
- [ ] 内存淘汰：`allkeys-lru` 最常用
- [ ] LRU：近似算法，采样 5 个 key
- [ ] LFU：访问频率，配置 `lfu-log-factor`

---

*第 37 天 / 330 天*
*Python 后端 - Redis 过期策略与内存淘汰*
