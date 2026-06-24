# 第 34 天：List 与 Sorted Set 进阶

## 学习目标

- 深入理解 List 内部实现
- 深入理解 Sorted Set 跳跃表
- 掌握高级操作技巧
- 学会应用场景实践

---

## 1. List 内部实现

### quicklist 结构

```markdown
Redis 3.2+ 使用 quicklist 作为 List 的实现

quicklist = ziplist 的链表

┌────────┬────────┬────────┬────────┬────────┐
│ zip1   │ zip2   │ zip3   │ zip4   │ zip5   │
│(压缩节点)│(压缩节点)│(压缩节点)│(压缩节点)│(压缩节点)│
└────────┴────────┴────────┴────────┴────────┘
     ↖                            ↗
       ←——— 双向链表指针 ———→

每个 ziplist 最多存放 8KB 左右的数据
```

### 配置

```bash
# 每个 ziplist 的最大大小
list-max-ziplist-size 8kb  # -2 (8KB), -1 (4KB), 0, 1, 2...

# 是否压缩（两端不压缩）
list-compress-depth 0  # 0 不压缩，1 首尾各 1 个不压缩
```

### 操作复杂度

```bash
# 时间复杂度
LPUSH key value        # O(1)
RPUSH key value        # O(1)
LPOP key               # O(1)
RPOP key               # O(1)
LINDEX key 0           # O(N)
LINSERT key BEFORE     # O(N)
LGETRANGE key 0 -1    # O(N)
LTRIM key 0 99        # O(N)
```

---

## 2. List 高级应用

### 消息队列

```python
import redis
import json
import time

class ReliableQueue:
    """可靠消息队列（消费确认）"""

    def __init__(self, redis_client):
        self.r = redis_client
        self.queue_key = 'queue:可靠队列'
        self.processing_key = 'queue:processing'

    def enqueue(self, message):
        """发送消息"""
        payload = json.dumps({
            'msg_id': f'{time.time()}:{message}',
            'data': message,
            'timestamp': time.time()
        })
        self.r.lpush(self.queue_key, payload)

    def dequeue(self, timeout=0):
        """消费消息（带确认）"""
        # 1. 从队列弹出一个
        result = self.r.brpoplpush(
            self.queue_key,
            self.processing_key,
            timeout=timeout
        )

        if not result:
            return None

        return json.loads(result)

    def ack(self, message):
        """确认消息处理成功"""
        # 从 processing 队列删除
        self.r.lrem(self.processing_key, 1, json.dumps(message))

    def nack(self, message):
        """消息处理失败，放回队列"""
        # 从 processing 移回原队列
        self.r.lrem(self.processing_key, 1, json.dumps(message))
        self.r.lpush(self.queue_key, json.dumps(message))

    def retry_dead_letters(self, max_retries=3):
        """处理死信（多次处理失败的消息）"""
        # 获取 processing 队列中的消息
        while True:
            msg = self.r.rpoplpush(
                self.processing_key,
                f'{self.processing_key}:dead'
            )
            if not msg:
                break

            data = json.loads(msg)
            retries = data.get('retries', 0) + 1

            if retries >= max_retries:
                # 移到死信队列
                self.r.lpush('queue:dead_letters', json.dumps(data))
            else:
                data['retries'] = retries
                # 重新加入处理队列
                self.r.lpush(self.processing_key, json.dumps(data))
```

### 分页列表

```python
class PaginatedList:
    """分页列表"""

    def __init__(self, redis_client):
        self.r = redis_client

    def add_item(self, list_key, item_id, timestamp=None):
        """添加元素"""
        if timestamp is None:
            timestamp = time.time()

        # 使用时间戳作为分数
        self.r.zadd(list_key, {str(item_id): timestamp})

    def get_page(self, list_key, page, page_size=20):
        """获取分页"""
        start = (page - 1) * page_size
        end = start + page_size - 1

        # 按分数降序获取
        items = self.r.zrevrange(list_key, start, end)
        total = self.r.zcard(list_key)

        return {
            'items': items,
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': (total + page_size - 1) // page_size
        }

    def remove_item(self, list_key, item_id):
        """删除元素"""
        self.r.zrem(list_key, str(item_id))


# 使用
paginated = PaginatedList(r)

# 添加文章
paginated.add_item('articles:recent', 'article:1001')
paginated.add_item('articles:recent', 'article:1002')

# 获取第一页
page1 = paginated.get_page('articles:recent', page=1)
```

---

## 3. Sorted Set 跳跃表原理

### 跳跃表结构

```
跳跃表是一种多层链表，每层是有序的

Level 3: 0 ────────────────────────────────► 100 (Alice)
Level 2: 0 ──────────────► 50 ─────────────► 100
Level 1: 0 ───► 25 ───► 50 ───► 75 ───► 100
Level 0: 0 ► 10 ► 25 ► 40 ► 50 ► 60 ► 75 ► 90 ► 100
          Alice  Bob  Carol David Eve  Frank Gary Helen Iris

查找 Carol (50)：
Level 3: 0 → 100 (跳过)
Level 2: 0 → 50 ✓ Carol

Level 1: 0 → 25 → 50 ✓ Carol
Level 0: 0 → 10 → 25 → 40 → 50 ✓ Carol
```

### Redis ZSet 实现

```markdown
Redis 使用跳跃表 + 字典实现 ZSet

┌─────────────────────────────────────────────────────┐
│                    ZSet 结构                          │
├─────────────────────────────────────────────────────┤
│  zset {                                             │
│    dict *dict;     // O(1) 通过 member 查找 score    │
│    skiplist *zsl;  // O(log N) 范围操作、排名       │
│  }                                                   │
└─────────────────────────────────────────────────────┘

字典和跳跃表共享数据，不会浪费内存
```

### 复杂度

```bash
# 时间复杂度
ZADD key score member      # O(log N)
ZSCORE key member          # O(1) 使用字典
ZRANK key member           # O(log N)
ZREVRANK key member        # O(log N)
ZRANGE key 0 -1            # O(log N + M)
ZINCRBY key increment      # O(log N)
```

---

## 4. Sorted Set 高级应用

### 滑动窗口排行榜

```python
class SlidingWindowLeaderboard:
    """滑动窗口排行榜"""

    def __init__(self, redis_client):
        self.r = redis_client

    def record_score(self, user_id, score, date=None):
        """记录分数"""
        if date is None:
            date = time.strftime('%Y-%m-%d')

        key = f'leaderboard:daily:{date}'
        self.r.zincrby(key, score, str(user_id))

        # 设置当天结束过期
        expire_at = time.mktime(time.strptime(date, '%Y-%m-%d')) + 86400
        self.r.expireat(key, int(expire_at))

    def get_daily_rank(self, user_id, date=None):
        """获取当日排名"""
        if date is None:
            date = time.strftime('%Y-%m-%d')

        key = f'leaderboard:daily:{date}'
        rank = self.r.zrevrank(key, str(user_id))
        return rank + 1 if rank is not None else None

    def get_weekly_top(self, week_start_date, count=10):
        """获取周榜"""
        keys = []
        for i in range(7):
            date = ...
            keys.append(f'leaderboard:daily:{date}')

        # 合并7天数据
        temp_key = f'leaderboard:temp:{time.time()}'
        self.r.zunionstore(temp_key, keys)
        self.r.expire(temp_key, 60)

        result = self.r.zrevrange(temp_key, 0, count - 1, withscores=True)
        self.r.delete(temp_key)

        return result

    def get_percentile(self, user_id, date=None):
        """获取百分为"""
        if date is None:
            date = time.strftime('%Y-%m-%d')

        key = f'leaderboard:daily:{date}'

        # 获取用户分数
        score = self.r.zscore(key, str(user_id))
        if score is None:
            return None

        # 获取排名
        rank = self.r.zrevrank(key, str(user_id))

        # 计算百分为
        total = self.r.zcard(key)
        percentile = (total - rank - 1) / total * 100

        return round(percentile, 2)
```

### 滑动窗口限流

```python
class SlidingWindowRateLimiter:
    """滑动窗口限流器"""

    def __init__(self, redis_client):
        self.r = redis_client

    def is_allowed(self, key, max_requests, window_seconds):
        """
        检查是否允许请求
        使用 ZSet 实现滑动窗口
        """
        now = time.time()
        window_key = f'rate:{key}'

        # 移除窗口外的请求
        self.r.zremrangebyscore(
            window_key,
            '-inf',
            now - window_seconds
        )

        # 获取当前请求数
        current_count = self.r.zcard(window_key)

        if current_count >= max_requests:
            return False

        # 添加当前请求
        self.r.zadd(window_key, {f'{now}:{random.random()}': now})
        self.r.expire(window_key, window_seconds)

        return True

    def get_remaining(self, key, max_requests, window_seconds):
        """获取剩余请求数"""
        now = time.time()
        window_key = f'rate:{key}'

        self.r.zremrangebyscore(
            window_key,
            '-inf',
            now - window_seconds
        )

        current_count = self.r.zcard(window_key)
        return max(0, max_requests - current_count)


# 使用
limiter = SlidingWindowRateLimiter(r)

def rate_limit_view(view_func):
    """限流装饰器"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        ip = request.remote_addr
        if not limiter.is_allowed(f'view:{ip}', 100, 60):
            return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
        return view_func(request, *args, **kwargs)
    return wrapper
```

---

## 5. 实战练习

### 实现关注 Feed

```python
class FeedService:
    """Feed 服务"""

    def __init__(self, redis_client):
        self.r = redis_client

    def post(self, user_id, content_id, timestamp=None):
        """发布动态到粉丝 Feed"""
        if timestamp is None:
            timestamp = time.time()

        # 获取用户粉丝
        followers = self.r.smembers(f'user:{user_id}:followers')

        if not followers:
            return

        # 推送到每个粉丝的 Feed
        feed_key = 'feed:{}'
        pipe = self.r.pipeline()

        for follower_id in followers:
            key = feed_key.format(follower_id)
            # ZSet：score=时间戳，member=内容ID
            pipe.zadd(key, {f'{user_id}:{content_id}': timestamp})
            # 限制 Feed 大小
            pipe.zremrangebyrank(key, 0, -1000)  # 只保留最新 1000 条

        pipe.execute()

    def get_feed(self, user_id, page=1, page_size=20):
        """获取用户 Feed"""
        feed_key = f'feed:{user_id}'

        start = (page - 1) * page_size
        end = start + page_size - 1

        # 获取 Feed
        items = self.r.zrevrange(feed_key, start, end)

        if not items:
            return []

        # 解析内容 ID
        result = []
        for item in items:
            user_id, content_id = item.split(':')
            result.append({
                'user_id': user_id,
                'content_id': content_id
            })

        return result

    def refresh_feed(self, user_id):
        """刷新 Feed（拉取最新）"""
        feed_key = f'feed:{user_id}'

        # 获取关注列表
        following = self.r.smembers(f'user:{user_id}:following')

        # 合并关注用户的最新内容
        temp_key = f'feed:temp:{user_id}'

        pipe = self.r.pipeline()
        pipe.delete(temp_key)

        for followed_id in following:
            key = f'user:{followed_id}:posts'
            pipe.zunionstore(temp_key, [temp_key, key], aggregate='MAX')

        pipe.execute()

        # 重命名
        self.r.rename(temp_key, feed_key)

        # 限制大小
        self.r.zremrangebyrank(feed_key, 0, -1000)
```

---

## 今日总结

- [ ] List：quicklist 实现，ziplist 的链表
- [ ] List：`LPUSH/LPOP` O(1)，`LINDEX` O(N)
- [ ] ZSet：跳跃表 + 字典，O(log N) 增删查
- [ ] ZSet 字典：O(1) 查找分数
- [ ] ZSet 跳跃表：O(log N) 排名和范围操作
- [ ] 滑动窗口：ZSet 实现精确限流
- [ ] Feed 系统：ZSet 存储时间线

---

*第 34 天 / 330 天*
*Python 后端 - List 与 Sorted Set 进阶*
