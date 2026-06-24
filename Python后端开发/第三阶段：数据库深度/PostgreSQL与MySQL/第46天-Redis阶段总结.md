# 第 46 天：Redis 阶段总结

## 学习目标

- 回顾 Redis 核心知识点
- 掌握 Redis 应用场景
- 理解缓存最佳实践
- 完成阶段练习

---

## 1. Redis 知识回顾

### 数据结构总结

```
┌─────────────────────────────────────────────────────┐
│                    Redis 数据结构                      │
├─────────────────────────────────────────────────────┤
│  String    │  值可以是字符串、整数、浮点数             │
│  Hash      │  field-value 映射，适合对象存储          │
│  List      │  有序列表，支持队列和栈操作              │
│  Set       │  无序集合，支持交并差运算               │
│  ZSet      │  有序集合，跳跃表实现，用于排行榜        │
└─────────────────────────────────────────────────────┘
```

### 持久化总结

```
┌─────────────────────────────────────────────────────┐
│                    Redis 持久化                       │
├─────────────────────────────────────────────────────┤
│  RDB      │  定时快照，文件紧凑，恢复快              │
│  AOF      │  记录命令，数据完整，文件较大            │
│  混合持久化 │  RDB + AOF 增量                       │
└─────────────────────────────────────────────────────┘
```

### 缓存问题总结

```
┌─────────────────────────────────────────────────────┐
│                    缓存三大问题                       │
├─────────────────────────────────────────────────────┤
│  穿透    │  布隆过滤器 + 缓存空值                    │
│  雪崩    │  过期时间随机 + 多级缓存                  │
│  击穿    │  互斥锁 + 逻辑过期                        │
└─────────────────────────────────────────────────────┘
```

---

## 2. Redis 应用场景

### 缓存

```python
# 页面缓存
r.setex(f'page:{path}', 3600, html_content)

# 数据缓存
r.setex(f'data:{id}', 1800, json.dumps(data))

# 用户会话
r.setex(f'session:{token}', 86400, user_id)
```

### 计数器

```python
# 访问量
r.incr(f'article:{id}:views')
r.incr(f'user:{id}:login_count')

# 限流
r.incr(f'rate:{ip}')
r.expire(f'rate:{ip}', 60)
```

### 分布式锁

```python
# 基础锁
r.set('lock:resource', token, nx=True, ex=30)

# 看门狗锁
# 自动续期，防止业务超时
```

### 消息队列

```python
# 延迟队列
r.zadd('delayed:tasks', {task_id: execute_at_timestamp})

# 优先级队列
r.zadd('priority:queue', {task_id: priority_score})
```

### 排行榜

```python
# ZSet 实现
r.zadd('leaderboard', {user_id: score})
r.zrevrange('leaderboard', 0, 9, withscores=True)
```

---

## 3. 缓存最佳实践

### 缓存设计原则

```
1. 缓存粒度
   - 缓存单个对象 vs 缓存整个页面
   - 平衡灵活性与效率

2. 过期策略
   - 热点数据：永不过期 + 逻辑删除
   - 冷数据：短过期 + 懒加载

3. 容量规划
   - 预估数据量
   - 预留足够内存
   - 设置 maxmemory-policy

4. 性能优化
   - Pipeline 批量操作
   - Lua 脚本原子操作
   - 本地缓存热点数据
```

### Redis 配置建议

```bash
# 内存配置
maxmemory 4gb
maxmemory-policy allkeys-lru

# 持久化配置
appendonly yes
appendfsync everysec
rdbcompression yes

# 连接配置
timeout 300
tcp-keepalive 60
```

---

## 4. 阶段练习：设计缓存架构

### 练习：电商系统缓存设计

```
需求：
1. 商品信息缓存
2. 库存扣减
3. 订单会话
4. 热门商品排行榜
5. 用户 Session
```

### 参考答案

```python
class EcommerceCache:
    """电商系统缓存设计"""

    def __init__(self, redis_client):
        self.r = redis_client

    # ============ 商品缓存 ============

    def cache_product(self, product_id, data, ttl=3600):
        """商品缓存"""
        key = f'product:{product_id}'
        self.r.setex(key, ttl, json.dumps(data))

    def get_product(self, product_id):
        """获取商品"""
        key = f'product:{product_id}'
        cached = self.r.get(key)
        return json.loads(cached) if cached else None

    # ============ 库存扣减 ============

    def deduct_stock(self, product_id, quantity):
        """扣减库存"""
        key = f'stock:{product_id}'

        # 使用 Lua 脚本保证原子性
        script = """
        local stock = tonumber(redis.call('GET', KEYS[1]) or '0')
        if stock >= tonumber(ARGV[1]) then
            redis.call('DECRBY', KEYS[1], ARGV[1])
            return stock - tonumber(ARGV[1])
        else
            return -1
        end
        """
        result = self.r.eval(script, 1, key, quantity)
        return result >= 0

    def restore_stock(self, product_id, quantity):
        """恢复库存"""
        key = f'stock:{product_id}'
        self.r.incrby(key, quantity)

    # ============ 订单会话 ============

    def create_order_session(self, order_id, user_id):
        """创建订单会话"""
        key = f'order:session:{order_id}'
        self.r.setex(key, 1800, str(user_id))

    def get_order_session(self, order_id):
        """获取订单会话"""
        key = f'order:session:{order_id}'
        return self.r.get(key)

    def delete_order_session(self, order_id):
        """删除订单会话"""
        key = f'order:session:{order_id}'
        self.r.delete(key)

    # ============ 排行榜 ============

    def update_leaderboard(self, product_id, view_count):
        """更新热门商品排行"""
        key = 'leaderboard:hot_products'
        self.r.zadd(key, {str(product_id): view_count})

    def get_hot_products(self, limit=10):
        """获取热门商品"""
        key = 'leaderboard:hot_products'
        return self.r.zrevrange(key, 0, limit - 1, withscores=True)

    # ============ 用户 Session ============

    def set_user_session(self, user_id, session_data, ttl=86400):
        """设置用户会话"""
        key = f'session:user:{user_id}'
        self.r.setex(key, ttl, json.dumps(session_data))

    def get_user_session(self, user_id):
        """获取用户会话"""
        key = f'session:user:{user_id}'
        cached = self.r.get(key)
        return json.loads(cached) if cached else None

    def refresh_session(self, user_id, ttl=86400):
        """刷新会话过期"""
        key = f'session:user:{user_id}'
        self.r.expire(key, ttl)

    def delete_user_session(self, user_id):
        """删除用户会话"""
        key = f'session:user:{user_id}'
        self.r.delete(key)
```

---

## 5. Redis 阶段回顾表

| 天数 | 主题 | 核心内容 |
|------|------|----------|
| 29 | Redis 数据结构 | 5种数据结构、SDS、跳跃表 |
| 31 | String/Hash 操作 | 计数器、对象存储、Pipeline |
| 33 | List/Set 操作 | 队列、集合运算、标签系统 |
| 35 | 持久化 RDB/AOF | 快照、追加、混合持久化 |
| 37 | 过期与淘汰 | 惰性删除、定期删除、LRU/LFU |
| 39 | 穿透/雪崩/击穿 | 布隆过滤器、随机 TTL、互斥锁 |
| 41 | 分布式锁 | SETNX、看门狗、Redlock |
| 43 | Redis Cluster | 槽分片、故障转移、高可用 |
| 45 | 缓存策略设计 | Cache-Aside、多级缓存、监控 |

---

## 6. 延伸学习

### 深入话题

```markdown
1. Redis 7.0 新特性
   - 多线程 IO
   - ACL v2
   - 函数（Functions）

2. Redis 协议
   - RESP 协议详解
   - 客户端实现

3. Redis 源码
   - SDS 实现
   - 跳跃表实现
   - 事件循环

4. Redis 运维
   - 集群扩缩容
   - 性能调优
   - 监控告警

5. Redis 替代品
   - Memcached
   - Dragonfly
   - KeyDB
```

### 学习资源

```
- Redis 官网：redis.io
- Redis 命令参考：redis.io/commands
- Redis 源码：github.com/redis/redis
- Redis 中文网：redis.cn
```

---

## 今日总结

- [ ] Redis 5 种数据结构：String、Hash、List、Set、ZSet
- [ ] 持久化：RDB 快照、AOF 追加、混合持久化
- [ ] 内存管理：过期删除、LRU/LFU 淘汰策略
- [ ] 高可用：主从复制、哨兵、Cluster
- [ ] 缓存问题：穿透、雪崩、击穿及解决方案
- [ ] 分布式锁：SETNX、看门狗、Redlock
- [ ] 应用场景：缓存、计数器、锁、队列、排行榜

---

## Redis 阶段完成

```
┌─────────────────────────────────────────────────────┐
│           🎉 Redis 阶段（29-46天）已完成！           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  接下来：                                           │
│  第 47-60 天：NoSQL 数据库（MongoDB、Cassandra）    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

*第 46 天 / 330 天*
*Python 后端 - Redis 阶段总结*
