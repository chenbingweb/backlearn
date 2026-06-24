# 第 33 天：List 与 Set 操作

## 学习目标

- 深入掌握 List 类型操作
- 深入掌握 Set 类型操作
- 理解 Sorted Set 高级操作
- 学会在实际场景中应用

---

## 1. List 进阶操作

### 双端队列

```bash
# 左侧操作（队首）
LPUSH queue "task1"           # 添加到队首
LPOP queue                     # 弹出队首
LPUSHX queue "task0"          # 仅当队列存在才添加
LRANGE queue 0 -1             # 查看队列内容

# 右侧操作（队尾）
RPUSH queue "taskN"           # 添加到队尾
RPOP queue                     # 弹出队尾
RPUSHX queue "taskEnd"        # 仅当队列存在才添加

# 阻塞操作
BLPOP queue 0                 # 阻塞直到有元素弹出
BLPOP queue 10                 # 超时时间（秒）
BRPOP queue 0                 # 右侧阻塞弹出
BRPOPLPUSH source dest 0      # 弹出一个并推送到另一个列表
```

### 队列长度和索引

```bash
# 长度
LLEN queue

# 按索引访问
LINDEX queue 0                 # 第一个元素
LINDEX queue -1                # 最后一个元素

# 按索引范围获取
LRANGE queue 0 9              # 前10个元素
LRANGE queue -10 -1            # 后10个元素

# 按索引设置
LSET queue 0 "new_task0"       # 设置第一个元素
```

### 插入和修剪

```bash
# 在元素前/后插入
LINSERT queue BEFORE "task1" "task0"
LINSERT queue AFTER "task1" "task2"

# 列表修剪（只保留范围内的元素）
LTRIM queue 0 99              # 只保留前100个元素

# 组合：实现队列（LPUSH + LTRIM）
LPUSH jobs "new_job"
LTRIM jobs 0 99               # 保持最多100个元素
```

---

## 2. List 应用场景

### 消息队列

```python
import redis
import json
import time

class MessageQueue:
    def __init__(self, redis_client):
        self.r = redis_client

    def enqueue(self, queue_name, message):
        """入队"""
        payload = json.dumps({
            'message': message,
            'timestamp': time.time()
        })
        self.r.lpush(f'queue:{queue_name}', payload)

    def dequeue(self, queue_name, timeout=0):
        """出队（阻塞）"""
        result = self.r.brpop(f'queue:{queue_name}', timeout=timeout)
        if result:
            _, payload = result
            return json.loads(payload)
        return None

    def process_queue(self, queue_name, callback, batch_size=10):
        """批量处理队列"""
        pipe = self.r.pipeline()
        for _ in range(batch_size):
            pipe.rpop(f'queue:{queue_name}')

        results = pipe.execute()
        for payload in results:
            if payload:
                data = json.loads(payload)
                callback(data['message'])

    def queue_length(self, queue_name):
        """获取队列长度"""
        return self.r.llen(f'queue:{queue_name}')
```

### 任务队列（延迟任务）

```python
class DelayedTaskQueue:
    def __init__(self, redis_client):
        self.r = redis_client

    def add_task(self, task_id, delay_seconds, task_data):
        """添加延迟任务"""
        execute_at = time.time() + delay_seconds
        score = execute_at

        # 存入有序集合
        self.r.zadd('delayed:tasks', {task_id: score})

        # 存储任务数据
        self.r.hset('task:data', task_id, json.dumps(task_data))

    def get_ready_tasks(self, batch_size=10):
        """获取到期的任务"""
        now = time.time()

        # 获取所有到期任务
        task_ids = self.r.zrangebyscore(
            'delayed:tasks',
            '-inf',
            now,
            start=0,
            num=batch_size
        )

        if not task_ids:
            return []

        # 批量获取任务数据
        pipe = self.r.pipeline()
        for task_id in task_ids:
            pipe.hget('task:data', task_id)

        task_datas = pipe.execute()

        # 删除已获取的任务
        self.r.zrem('delayed:tasks', *task_ids)

        return [
            {'task_id': tid, 'data': json.loads(tdata)}
            for tid, tdata in zip(task_ids, task_datas)
        ]
```

### 最新列表

```python
class LatestItems:
    def __init__(self, redis_client, max_size=100):
        self.r = redis_client
        self.max_size = max_size

    def add_item(self, item_key, item_id):
        """添加新条目"""
        # 生成唯一成员
        member = f'{item_id}'

        # 添加到列表
        self.r.lpush(item_key, member)

        # 修剪列表大小
        self.r.ltrim(item_key, 0, self.max_size - 1)

        # 设置过期（可选，防止数据僵化）
        self.r.expire(item_key, 86400 * 30)

    def get_latest(self, item_key, count=10):
        """获取最新条目"""
        return self.r.lrange(item_key, 0, count - 1)

    def is_duplicate(self, item_key, item_id):
        """检查是否重复"""
        return self.r.lrem(item_key, 0, f'{item_id}') > 0


# 使用
latest = LatestItems(r, max_size=100)

# 追踪最新评论
latest.add_item('article:1001:comments', 'comment:10000')
comments = latest.get_latest('article:1001:comments', 20)
```

---

## 3. Set 进阶操作

### 基本操作

```bash
# 添加/删除
SADD tags "python" "redis" "database"
SREM tags "database"                # 删除成员
SPOP tags                           # 随机弹出（删除）
SRANDMEMBER tags 2                  # 随机获取（不删除）

# 查询
SISMEMBER tags "python"            # 检查存在
SCARD tags                          # 成员数量
SMEMBERS tags                        # 获取所有成员

# 遍历（大数据量）
SSCAN tags CURSOR 0 COUNT 100
```

### 集合运算

```bash
# 交集
SINTER tag:python tag:redis tag:database
SINTERSTORE result tag:python tag:redis  # 存入新集合

# 并集
SUNION tag:python tag:redis tag:database
SUNIONSTORE result tag:python tag:redis

# 差集（第一个集合有，其他集合没有的）
SDIFF tag:python tag:redis tag:database
SDIFFSTORE result tag:python tag:redis

# 混合运算
SINTERSTORE result tag:python tag:redis tag:database
```

---

## 4. Set 应用场景

### 标签系统

```python
class TagSystem:
    def __init__(self, redis_client):
        self.r = redis_client

    def add_tag(self, entity_type, entity_id, tags):
        """为实体添加标签"""
        key = f'{entity_type}:{entity_id}:tags'

        # 添加到实体的标签集合
        self.r.sadd(key, *tags)

        # 更新标签的实体集合
        for tag in tags:
            self.r.sadd(f'tag:{tag}:entities', f'{entity_type}:{entity_id}')

    def remove_tag(self, entity_type, entity_id, tags):
        """移除标签"""
        key = f'{entity_type}:{entity_id}:tags'

        self.r.srem(key, *tags)

        for tag in tags:
            self.r.srem(f'tag:{tag}:entities', f'{entity_type}:{entity_id}')

    def get_tags(self, entity_type, entity_id):
        """获取实体所有标签"""
        return list(self.r.smembers(f'{entity_type}:{entity_id}:tags'))

    def get_entities_by_tag(self, tag):
        """获取拥有指定标签的所有实体"""
        return list(self.r.smembers(f'tag:{tag}:entities'))

    def get_entities_by_tags(self, tags, match='all'):
        """获取同时拥有多个标签的实体"""
        if match == 'all':
            # 交集：同时拥有所有标签
            if not tags:
                return []
            result = self.r.sinter(*[f'tag:{tag}:entities' for tag in tags])
        else:
            # 并集：拥有任一标签
            result = self.r.sunion(*[f'tag:{tag}:entities' for tag in tags])

        return list(result)
```

### 关注系统

```python
class FollowSystem:
    def __init__(self, redis_client):
        self.r = redis_client

    def follow(self, user_id, follow_user_id):
        """关注用户"""
        pipe = self.r.pipeline()

        # 添加到关注列表
        pipe.sadd(f'user:{user_id}:following', str(follow_user_id))
        # 添加到粉丝列表
        pipe.sadd(f'user:{follow_user_id}:followers', str(user_id))

        pipe.execute()

        # 更新计数
        self.r.incr(f'user:{user_id}:following:count')
        self.r.incr(f'user:{follow_user_id}:followers:count')

    def unfollow(self, user_id, follow_user_id):
        """取消关注"""
        pipe = self.r.pipeline()

        pipe.srem(f'user:{user_id}:following', str(follow_user_id))
        pipe.srem(f'user:{follow_user_id}:followers', str(user_id))

        pipe.execute()

        self.r.decr(f'user:{user_id}:following:count')
        self.r.decr(f'user:{follow_user_id}:followers:count')

    def is_following(self, user_id, follow_user_id):
        """检查是否关注"""
        return self.r.sismember(f'user:{user_id}:following', str(follow_user_id))

    def get_following(self, user_id):
        """获取关注列表"""
        return list(self.r.smembers(f'user:{user_id}:following'))

    def get_followers(self, user_id):
        """获取粉丝列表"""
        return list(self.r.smembers(f'user:{user_id}:followers'))

    def get_mutual_followers(self, user_id):
        """获取互相关注（共同关注）"""
        return list(self.r.sinter(
            f'user:{user_id}:following',
            f'user:{user_id}:followers'
        ))
```

### UV 统计（去重计数）

```python
class UVCounter:
    def __init__(self, redis_client):
        self.r = redis_client

    def add_visitor(self, date, user_id):
        """添加访客"""
        key = f'uv:{date}'
        self.r.sadd(key, str(user_id))

    def get_uv(self, date):
        """获取日 UV"""
        return self.r.scard(f'uv:{date}')

    def get_uv_range(self, start_date, end_date):
        """获取日期范围内的 UV（去重）"""
        keys = [
            f'uv:{date}'
            for date in self._date_range(start_date, end_date)
        ]
        # 并集去重
        return len(self.r.sunion(*keys))

    def _date_range(self, start_date, end_date):
        """生成日期范围"""
        from datetime import timedelta
        current = start_date
        while current <= end_date:
            yield current.strftime('%Y-%m-%d')
            current += timedelta(days=1)
```

---

## 5. Sorted Set 高级操作

### 基本操作回顾

```bash
# 添加/获取
ZADD leaderboard 100 "Alice" 200 "Bob" 150 "Carol"
ZSCORE leaderboard "Alice"
ZRANGE leaderboard 0 -1
ZREVRANGE leaderboard 0 -1 WITHSCORES

# 排名
ZRANK leaderboard "Alice"      # 升序排名（0开始）
ZREVRANK leaderboard "Alice"   # 降序排名

# 分数操作
ZINCRBY leaderboard 10 "Alice"    # 增加分数
ZCOUNT leaderboard 90 100         # 分数范围内数量
ZRANGEBYSCORE leaderboard 90 100  # 按分数范围获取
```

### 有序集合运算

```bash
# 并集
ZUNIONSTORE result 2 zset1 zset2        # 简单并集
ZUNIONSTORE result 2 zset1 zset2 WEIGHTS 2 1  # 加权并集
ZUNIONSTORE result 2 zset1 zset2 AGGREGATE MIN  # 取最小值

# 交集
ZINTERSTORE result 2 zset1 zset2
ZINTERSTORE result 2 zset1 zset2 WEIGHTS 1 0.5
```

### 跳跃表原理

```
Level 3: 0 ────────────────────────────────► 100 (Alice)
Level 2: 0 ──────────────► 50 ─────────────► 100
Level 1: 0 ───► 25 ───► 50 ───► 75 ───► 100
Level 0: 0 ─► 10 ─► 25 ─► 40 ─► 50 ─► 60 ─► 75 ─► 90 ─► 100
          Alice Bob Carol David Eve Frank Gary Helen Iris
```

---

## 6. Sorted Set 应用场景

### 排行榜

```python
class Leaderboard:
    def __init__(self, redis_client):
        self.r = redis_client

    def add_score(self, leaderboard_name, user_id, score):
        """添加/更新分数"""
        self.r.zadd(f'leaderboard:{leaderboard_name}', {str(user_id): score})

    def increment_score(self, leaderboard_name, user_id, increment):
        """增加分数"""
        return self.r.zincrby(f'leaderboard:{leaderboard_name}', increment, str(user_id))

    def get_rank(self, leaderboard_name, user_id):
        """获取排名（0开始，降序）"""
        rank = self.r.zrevrank(f'leaderboard:{leaderboard_name}', str(user_id))
        return rank + 1 if rank is not None else None

    def get_score(self, leaderboard_name, user_id):
        """获取分数"""
        return self.r.zscore(f'leaderboard:{leaderboard_name}', str(user_id))

    def get_top(self, leaderboard_name, count=10):
        """获取 Top N"""
        return self.r.zrevrange(
            f'leaderboard:{leaderboard_name}',
            0,
            count - 1,
            withscores=True
        )

    def get_rank_range(self, leaderboard_name, rank_start, rank_end):
        """获取指定排名范围"""
        return self.r.zrevrange(
            f'leaderboard:{leaderboard_name}',
            rank_start,
            rank_end,
            withscores=True
        )

    def remove_user(self, leaderboard_name, user_id):
        """移除用户"""
        self.r.zrem(f'leaderboard:{leaderboard_name}', str(user_id))


# 使用
lb = Leaderboard(r)
lb.add_score('weekly', 1001, 95)
lb.add_score('weekly', 1002, 88)
lb.add_score('weekly', 1003, 92)

print(lb.get_top('weekly'))      # [('1003', 92), ('1001', 95), ('1002', 88)]
print(lb.get_rank('weekly', 1001))  # 2（第二名）
```

### 时间线排序

```python
class Timeline:
    def __init__(self, redis_client):
        self.r = redis_client

    def post(self, user_id, post_id, timestamp=None):
        """发布动态"""
        if timestamp is None:
            timestamp = time.time()

        # 使用时间戳作为分数
        key = f'timeline:{user_id}'
        self.r.zadd(key, {str(post_id): timestamp})

    def get_timeline(self, user_id, count=20, offset=0):
        """获取用户时间线"""
        key = f'timeline:{user_id}'
        return self.r.zrevrange(key, offset, offset + count - 1)

    def get_timeline_with_scores(self, user_id, count=20):
        """获取时间线（带时间戳）"""
        key = f'timeline:{user_id}'
        return self.r.zrevrange(key, 0, count - 1, withscores=True)

    def delete_post(self, user_id, post_id):
        """删除动态"""
        self.r.zrem(f'timeline:{user_id}', str(post_id))


# 粉丝时间线（推模式）
class FanTimeline:
    def __init__(self, redis_client):
        self.r = redis_client

    def publish(self, user_id, post_id):
        """发布动态到所有粉丝"""
        timestamp = time.time()
        key = f'timeline:{user_id}'
        self.r.zadd(key, {str(post_id): timestamp})

        # 获取粉丝列表
        followers = self.r.smembers(f'user:{user_id}:followers')

        # 推送给每个粉丝
        pipe = self.r.pipeline()
        for follower_id in followers:
            pipe.zadd(f'timeline:{follower_id}', {str(post_id): timestamp})
        pipe.execute()

    def get_fan_timeline(self, user_id, count=20):
        """获取粉丝时间线"""
        return self.r.zrevrange(f'timeline:{user_id}', 0, count - 1)
```

---

## 今日总结

- [ ] List：`LPUSH/RPOP` 队列，`LPUSH/LPOP` 栈
- [ ] List：`BLPOP/BRPOP` 阻塞获取
- [ ] List：`LTRIM` 保持固定长度
- [ ] Set：`SINTER/SUNION/SDIFF` 集合运算
- [ ] Set：标签系统、关注系统、UV 统计
- [ ] ZSet：跳跃表实现，排行榜、时间线排序
- [ ] ZSet：`ZINCRBY` 递增分数

---

*第 33 天 / 330 天*
*Python 后端 - List 与 Set 操作*
