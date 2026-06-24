# 第 42 天：Redlock 算法与分布式锁进阶

## 学习目标

- 深入理解 Redlock 算法
- 掌握 Redlock 实现细节
- 学会分布式锁进阶应用
- 理解分布式锁注意事项

---

## 1. Redlock 算法详解

### 单机锁的问题

```markdown
单机 Redis 分布式锁的问题：

主从架构下的锁失效：

时刻1: 客户端A 在主库获取锁（SET lock NX EX）
       │
时刻2: 主库崩溃，还没同步到从库
       │
时刻3: 从库升级为主库
       │
时刻4: 客户端B 在新主库获取锁（同一资源）
       │
结果: 客户端A 和 客户端B 同时持有锁 ❌

原因：主从异步复制，锁数据丢失
```

### Redlock 原理

```markdown
Redlock：使用多个独立的 Redis 实例

┌─────────┐  ┌─────────┐  ┌─────────┐
│ Redis 1 │  │ Redis 2 │  │ Redis 3 │
│  (独立)  │  │  (独立)  │  │  (独立)  │
└─────────┘  └─────────┘  └─────────┘
     │            │            │
     │            │            │
     ▼            ▼            ▼
获取锁 ◄──────────┼───────────►
N/2+1 成功？      │            │
     │            │            │
     ▼            │            ▼
   成功          │          成功
                 │
                 ▼
            大多数节点拥有锁
            即便部分节点崩溃
            锁仍然有效
```

### Redlock 算法步骤

```python
def redlock_acquire(redis_servers, resource_name, ttl=10):
    """
    Redlock 获取锁步骤：

    1. 获取当前时间（毫秒）
    2. 依次向 N 个实例获取锁
    3. 计算获取锁花费的时间
    4. 如果获取锁花费的时间 < ttl，认为成功
    5. 释放锁时，向所有实例发送释放命令
    """
    N = len(redis_servers)
    Quorum = N // 2 + 1

    start_time = get_current_time_ms()

    # 向所有实例尝试获取锁
    acquired = 0
    for r in redis_servers:
        if try_acquire(r, resource_name, ttl):
            acquired += 1

    # 计算有效时间
    elapsed = get_current_time_ms() - start_time
    validity_time = ttl - elapsed - (elapsed * 0.1)  # 留10%buffer

    if acquired >= Quorum and validity_time > 0:
        return True  # 获取锁成功
    else:
        # 释放所有已获取的锁
        for r in redis_servers:
            release(r, resource_name)
        return False
```

---

## 2. Redlock 详细实现

### Python 实现

```python
import redis
import uuid
import time
import threading

class RedLock:
    """Redlock 分布式锁实现"""

    # 重试配置
    CLOCK_DRIFT_FACTOR = 0.01  # 时钟漂移因子
    RETRY_COUNT = 3
    RETRY_DELAY = 0.2  # 秒

    def __init__(self, redis_servers, retry_count=None, retry_delay=None):
        """
        redis_servers: list of Redis connections
        示例：[r1, r2, r3, r4, r5]
        """
        self.redis_servers = redis_servers
        self.retry_count = retry_count or self.RETRY_COUNT
        self.retry_delay = retry_delay or self.RETRY_DELAY
        self.quorum = len(redis_servers) // 2 + 1
        self.ttl = 10  # 默认锁持有时间（秒）

    def _get_unique_id(self):
        """生成唯一标识"""
        return f'{uuid.uuid4()}:{threading.get_ident()}'

    def acquire(self, resource_name, ttl=None):
        """获取锁"""
        if ttl is None:
            ttl = self.ttl

        unique_id = self._get_unique_id()
        start_time = time.time()

        for retry in range(self.retry_count):
            acquired = 0
            failures = []

            # 向每个实例尝试获取锁
            for rs in self.redis_servers:
                try:
                    if self._try_acquire(rs, resource_name, unique_id, ttl):
                        acquired += 1
                    else:
                        failures.append(rs)
                except Exception as e:
                    failures.append(rs)

            # 计算有效时间
            elapsed = time.time() - start_time
            drift = self.CLOCK_DRIFT_FACTOR * ttl + 0.01  # 预留
            validity_time = ttl - elapsed - drift

            # 检查是否获取了多数派锁
            if acquired >= self.quorum and validity_time > 0:
                self.resource_name = resource_name
                self.unique_id = unique_id
                return True

            # 获取失败，释放已获取的锁
            for rs in self.redis_servers:
                try:
                    self._release_single(rs, resource_name, unique_id)
                except:
                    pass

            # 重试前等待
            if retry < self.retry_count - 1:
                time.sleep(self.retry_delay)

        return False

    def _try_acquire(self, rs, resource_name, unique_id, ttl):
        """尝试在单个实例获取锁"""
        lock_key = f'redlock:{resource_name}'
        result = rs.set(
            lock_key,
            unique_id,
            nx=True,
            ex=ttl
        )
        return result is not None

    def release(self):
        """释放锁"""
        if not hasattr(self, 'unique_id'):
            return False

        for rs in self.redis_servers:
            try:
                self._release_single(
                    rs,
                    self.resource_name,
                    self.unique_id
                )
            except:
                pass

        return True

    def _release_single(self, rs, resource_name, unique_id):
        """释放单个实例的锁"""
        lock_key = f'redlock:{resource_name}'

        # Lua 脚本保证原子性
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        rs.eval(script, 1, lock_key, unique_id)

    def extend(self, additional_time=None):
        """延长锁持有时间"""
        if not hasattr(self, 'unique_id'):
            return False

        if additional_time is None:
            additional_time = self.ttl

        extended = 0
        for rs in self.redis_servers:
            try:
                lock_key = f'redlock:{self.resource_name}'
                script = """
                if redis.call("get", KEYS[1]) == ARGV[1] then
                    return redis.call("expire", KEYS[1], ARGV[2])
                else
                    return 0
                end
                """
                if rs.eval(script, 1, lock_key, self.unique_id, additional_time):
                    extended += 1
            except:
                pass

        return extended >= self.quorum

    def __enter__(self):
        if not self.acquire(self.resource_name):
            raise TimeoutError("Failed to acquire Redlock")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


# 使用示例
r1 = redis.Redis(host='redis1.local', port=6379)
r2 = redis.Redis(host='redis2.local', port=6379)
r3 = redis.Redis(host='redis3.local', port=6379)
r4 = redis.Redis(host='redis4.local', port=6379)
r5 = redis.Redis(host='redis5.local', port=6379)

lock = RedLock([r1, r2, r3, r4, r5])

try:
    lock.resource_name = 'order:1001'
    if lock.acquire('order:1001', ttl=30):
        # 执行业务操作
        process_order(1001)
finally:
    lock.release()
```

---

## 3. 分布式锁进阶应用

### 任务分布式执行

```python
class DistributedTaskExecutor:
    """分布式任务执行器"""

    def __init__(self, redis_servers):
        self.lock = RedLock(redis_servers)

    def execute_task(self, task_id, task_func, ttl=60):
        """
        分布式执行任务
        确保同一任务只被一个节点执行
        """
        lock_key = f'task:lock:{task_id}'

        if self.lock.acquire(lock_key, ttl):
            try:
                # 检查任务是否已完成
                if self._is_task_completed(task_id):
                    return {'status': 'already_completed', 'task_id': task_id}

                # 执行任务
                result = task_func()

                # 标记任务完成
                self._mark_task_completed(task_id, result)

                return {'status': 'completed', 'result': result}
            finally:
                self.lock.release()
        else:
            return {'status': 'running_elsewhere', 'task_id': task_id}

    def _is_task_completed(self, task_id):
        """检查任务是否已完成"""
        # 使用单独的 Redis 检查
        r = redis.Redis()
        return r.exists(f'task:result:{task_id}')

    def _mark_task_completed(self, task_id, result):
        """标记任务完成"""
        r = redis.Redis()
        r.setex(f'task:result:{task_id}', 86400, json.dumps(result))
```

### 分布式计数器

```python
class DistributedCounter:
    """分布式计数器"""

    def __init__(self, redis_servers):
        self.lock = RedLock(redis_servers)

    def increment_with_limit(self, counter_name, limit, ttl=60):
        """
        带限制的计数器
        返回是否允许操作
        """
        lock_key = f'counter:lock:{counter_name}'

        if self.lock.acquire(lock_key, ttl):
            try:
                r = redis.Redis()
                count = r.incr(counter_name)

                if count == 1:
                    # 第一次，设置过期
                    r.expire(counter_name, ttl)

                if count <= limit:
                    return True, count
                else:
                    return False, count
            finally:
                self.lock.release()
        else:
            # 获取锁失败，保守处理
            return False, None
```

---

## 4. 分布式锁注意事项

### 注意事项

```markdown
使用 Redlock 的注意事项：

1. 性能开销
   - 需要向多个 Redis 发送请求
   - 网络延迟增加
   - 通常用于对可靠性要求高的场景

2. 时钟问题
   - 各节点时钟必须同步
   - 使用 NTP 校时
   - drift_factor 预留时钟误差

3. 锁粒度
   - 锁粒度要细
   - 避免长时间持有锁
   - 业务要能处理锁超时

4. 失败处理
   - 获取锁失败要有退路
   - 释放锁要处理异常
   - 要有监控告警

5. 不适合的场景
   - Redlock 不适合长任务
   - 不适合需要严格公平性的场景
   - 不适合需要顺序锁的场景
```

### 安全讨论

```python
# Redlock 的争议

# Martin Fowler 的观点：
# Redlock 并不是一个安全分布式锁的实现
# 原因：
# 1. 依赖时钟，不是纯异步模型
# 2. 锁定时间不精确
# 3. 释放锁可能释放别人的锁

# 建议：
# 如果不需要严格分布式锁，用单节点 Redis + 哨兵
# 如果需要严格分布式锁，用 Zookeeper

# Redisson 的观点：
# Redlock 是安全的，前提是：
# 1. 时钟漂移可控
# 2. 网络分区概率低
# 3. 适当的安全边界
```

### 替代方案

```python
# 1. Zookeeper 分布式锁
# 更可靠，但性能低于 Redis
from kazoo.client import KazooClient

zk = KazooClient()
lock = zk.Lock("/lock", "my-identifier")
with lock:
    # 临界区操作
    pass

# 2. etcd 分布式锁
#  Kubernetes 使用的分布式一致性存储
#  性能介于 Redis 和 Zookeeper 之间

# 3. Consul 分布式锁
#  HashiCorp 的服务发现和配置工具
#  支持分布式锁
```

---

## 5. 最佳实践

### 锁使用规范

```python
class LockBestPractices:
    """分布式锁最佳实践"""

    def __init__(self, redis_client):
        self.r = redis_client

    def safe_lock(self, resource_name, timeout=30, retry=3):
        """安全的锁获取"""
        lock_key = f'lock:{resource_name}'
        token = str(uuid.uuid4())

        # 1. 尝试获取锁
        acquired = self.r.set(
            lock_key,
            token,
            nx=True,
            ex=timeout
        )

        if not acquired:
            # 2. 获取失败，等待后重试
            for _ in range(retry):
                time.sleep(0.1)
                acquired = self.r.set(lock_key, token, nx=True, ex=timeout)
                if acquired:
                    break

        return acquired, token

    def safe_unlock(self, resource_name, token):
        """安全的锁释放"""
        lock_key = f'lock:{resource_name}'

        # 使用 Lua 脚本确保只释放自己的锁
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        result = self.r.eval(script, 1, lock_key, token)
        return result == 1

    def with_lock(self, resource_name, func, timeout=30):
        """上下文管理器方式使用锁"""
        acquired, token = self.safe_lock(resource_name, timeout)

        if not acquired:
            raise TimeoutError(f"Failed to acquire lock: {resource_name}")

        try:
            return func()
        finally:
            self.safe_unlock(resource_name, token)


# 使用示例
locker = LockBestPractices(r)

try:
    result = locker.with_lock('order:1001', lambda: process_order(1001))
except TimeoutError:
    print('系统繁忙，请稍后重试')
```

---

## 今日总结

- [ ] 单机锁问题：主从切换导致锁失效
- [ ] Redlock：多实例多数派获取锁
- [ ] 算法步骤：依次获取锁，计算有效时间
- [ ] 注意事项：时钟同步、锁粒度、失败处理
- [ ] 适用场景：对可靠性要求高的分布式锁
- [ ] 替代方案：Zookeeper、etcd、Consul

---

*第 42 天 / 330 天*
*Python 后端 - Redlock 算法与分布式锁进阶*
