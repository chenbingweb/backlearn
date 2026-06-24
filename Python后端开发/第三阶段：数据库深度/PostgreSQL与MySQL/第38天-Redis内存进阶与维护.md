# 第 38 天：Redis 内存进阶与维护

## 学习目标

- 深入理解内存管理
- 掌握内存优化技巧
- 学会内存监控
- 掌握问题排查

---

## 1. 内存管理

### 内存分配

```bash
# Redis 使用 jemalloc 分配内存
# 小于 64KB 按桶分配，大于 64KB 直接 mmap

# 查看内存使用
INFO memory
# used_memory: 1048576          # Redis 内部使用字节
# used_memory_human: 1.00M      # 人类可读
# used_memory_rss: 2097152      # 物理内存（包含碎片）
# used_memory_peak: 1048576     # 峰值使用
# mem_fragmentation_ratio: 2.0  # 碎片率 = RSS/used
```

### 内存碎片

```markdown
内存碎片产生原因：

1. 频繁更新：SDS 惰性空间释放
2. 数据删除：释放的内存被小块占用
3. 键过期：删除后空间不连续

碎片率：
- 1.0-1.5：正常
- 1.5-2.0：需要优化
- > 2.0：严重，需要处理
```

### 碎片整理

```bash
# 1. 重启 Redis（最有效）

# 2. 动态内存碎片整理（Redis 4.0+）
redis-cli MEMORY PURGE

# 3. 配置自动整理
# redis.conf
activedefrag yes
active-defrag-ignore-bytes 100mb
active-defrag-threshold-lower 10
active-defrag-threshold-upper 100
```

---

## 2. 内存优化

### 优化策略

```python
# 1. 避免短生命周期的大 key
# ❌ 差：存储大对象
r.set('big_data', json.dumps(large_dict))

# ✅ 好：拆分存储
for i, chunk in enumerate(chunks):
    r.set(f'big_data:{i}', chunk)

# 2. 使用合适的数据结构
# ❌ 差：String 存储列表
r.set('ids', '1,2,3,4,5')
ids = r.get('ids').split(',')

# ✅ 好：List 存储列表
r.delete('ids')
for id in [1,2,3,4,5]:
    r.rpush('ids', id)
ids = r.lrange('ids', 0, -1)

# 3. 数字用 String，不是 Hash
# ❌ 差
r.hset('user:1', 'views', '100')
r.hincrby('user:1', 'views', 1)

# ✅ 好
r.set('user:1:views', '100')
r.incr('user:1:views', 1)
```

### 小对象压缩

```python
# Hash 优化：设置字段数量限制
# redis.conf
hash-max-ziplist-entries 512   # 字段数 <= 512
hash-max-ziplist-value 64       # 值 <= 64 字节

# ZSet 优化：设置元素数量限制
zset-max-ziplist-entries 128
zset-max-ziplist-value 64

# List 优化
list-max-ziplist-size -2       # 8KB
list-compress-depth 0           # 不压缩
```

---

## 3. 内存监控

### 监控指标

```python
def get_memory_stats(r):
    """获取内存统计"""
    info = r.info('memory')

    return {
        'used_memory': info['used_memory'],
        'used_memory_human': info['used_memory_human'],
        'used_memory_rss': info['used_memory_rss'],
        'used_memory_rss_human': info['used_memory_rss_human'],
        'mem_fragmentation_ratio': info['mem_fragmentation_ratio'],
        'mem_fragmentation_ratio': info['mem_fragmentation_ratio'],
        'maxmemory': info['maxmemory'],
        'maxmemory_human': info['maxmemory_human'],
        'mem_allocator': info['mem_allocator'],
    }

def check_memory_health(r):
    """检查内存健康"""
    info = r.info('memory')
    stats = get_memory_stats(r)

    alerts = []

    # 碎片率检查
    frag_ratio = info['mem_fragmentation_ratio']
    if frag_ratio > 2.0:
        alerts.append({
            'level': 'critical',
            'message': f'内存碎片率严重: {frag_ratio}'
        })
    elif frag_ratio > 1.5:
        alerts.append({
            'level': 'warning',
            'message': f'内存碎片率较高: {frag_ratio}'
        })

    # 内存使用率
    used = info['used_memory']
    maxmemory = info['maxmemory']
    if maxmemory > 0:
        usage = used / maxmemory
        if usage > 0.9:
            alerts.append({
                'level': 'critical',
                'message': f'内存使用率超过 90%: {usage:.1%}'
            })
        elif usage > 0.8:
            alerts.append({
                'level': 'warning',
                'message': f'内存使用率超过 80%: {usage:.1%}'
            })

    return {
        'stats': stats,
        'alerts': alerts,
        'healthy': len([a for a in alerts if a['level'] == 'critical']) == 0
    }
```

### 大 Key 分析

```python
def find_big_keys(r, count=10):
    """查找大 key"""
    big_keys = []

    # 使用 SCAN 遍历所有键
    cursor = 0
    while True:
        cursor, keys = r.scan(cursor, count=100)
        for key in keys:
            key_type = r.type(key)
            if key_type == 'string':
                size = r.strlen(key)
            elif key_type == 'hash':
                size = r.hlen(key)
            elif key_type == 'list':
                size = r.llen(key)
            elif key_type == 'set':
                size = r.scard(key)
            elif key_type == 'zset':
                size = r.zcard(key)
            else:
                size = 0

            big_keys.append({
                'key': key,
                'type': key_type,
                'size': size
            })

        if cursor == 0:
            break

    # 按大小排序
    big_keys.sort(key=lambda x: x['size'], reverse=True)

    return big_keys[:count]

# redis-cli 大 key 分析
# redis-cli --bigkeys
```

---

## 4. 内存问题排查

### OOM 问题

```markdown
Redis OOM（Out of Memory）：

原因：
1. maxmemory 未设置，内存无限增长
2. maxmemory-policy 设置不当
3. 突发的流量高峰

排查：
1. 查看内存使用
   INFO memory | grep used_memory

2. 查看 OOM 次数
   INFO stats | grep evicted

3. 查看大 key
   redis-cli --bigkeys

解决：
1. 设置 maxmemory
2. 调整 maxmemory-policy
3. 增加内存
4. 扩容/分片
```

### 内存泄漏

```python
# 常见的内存泄漏模式

# 1. 不断增长的 Set/List/ZSet
def leak_example1(r):
    """不断添加，不删除"""
    # ❌ 会导致内存不断增长
    while True:
        r.sadd('leaking:set', new_item)

# ✅ 解决：设置最大大小
def fixed_example1(r):
    # 只保留最新 10000 条
    r.sadd('fixed:set', new_item)
    r.srem('fixed:set', *r.srandmember('fixed:set', r.scard('fixed:set') - 10000))

# 2. 未设置过期的 key
def leak_example2(r):
    """设置了过期时间但条件永远不满足"""
    # ❌ 永远不会过期
    r.setex('key', get_ttl_that_never_arrives(), 'value')

# ✅ 解决：确保过期时间合理
```

### 性能问题

```python
# 内存使用导致的性能问题

# 1. swap 使用
# 查看 Redis 是否使用 swap
# redis-cli INFO | grep process_id
# cat /proc/<pid>/status | grep VmSwap

# 2. 大 key 阻塞
# 删除大 key 会阻塞
# ❌ DEL big_key
# ✅ 使用 UNLINK（异步删除）
r.unlink('big_key')

# 3. 内存分配竞争
# jemalloc 多线程分配竞争
# 解决：使用 Redis 6.0+ 的多线程 IO
```

---

## 5. 日常维护

### 定期任务

```python
import schedule

def daily_maintenance():
    """日常维护任务"""
    r = redis.Redis()

    # 1. 检查内存健康
    health = check_memory_health(r)
    if not health['healthy']:
        send_alert(health['alerts'])

    # 2. 整理内存碎片
    if health['stats']['mem_fragmentation_ratio'] > 1.5:
        r.memory_defrag()

    # 3. 分析大 key
    big_keys = find_big_keys(r)
    if big_keys:
        log_big_keys(big_keys)

# 定时任务
schedule.every().day.at("03:00").do(daily_maintenance)
```

### 安全配置

```bash
# redis.conf 安全配置

# 1. 设置密码
requirepass your_password_here

# 2. 禁用危险命令
rename-command FLUSHALL ""
rename-command FLUSHDB ""
rename-command CONFIG ""
rename-command SHUTDOWN ""

# 3. 绑定 IP
bind 127.0.0.1 10.0.0.1

# 4. 禁用危险命令
protected-mode yes
```

---

## 今日总结

- [ ] 内存碎片：`mem_fragmentation_ratio` > 1.5 需要处理
- [ ] `MEMORY PURGE`：手动整理内存
- [ ] 大 key：使用 `--bigkeys` 分析
- [ ] UNLINK：异步删除大 key
- [ ] `MEMORY DEFRAG`：在线内存碎片整理
- [ ] 监控：定期检查内存健康和碎片率

---

*第 38 天 / 330 天*
*Python 后端 - Redis 内存进阶与维护*
