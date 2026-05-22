# 第 24 天：async/await 进阶

## 学习目标

- 掌握高级 asyncio API
- 理解事件循环
- 学会混合同步和异步代码
- 了解 asyncio 最佳实践

---

## 1. 事件循环

### 获取和操作事件循环

```python
import asyncio

async def main():
    # 获取当前事件循环
    loop = asyncio.get_running_loop()
    print(f"事件循环: {loop}")

    # 在指定时间执行
    loop.call_later(1, lambda: print("1秒后"))

asyncio.run(main())
```

### 手动管理事件循环

```python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

try:
    result = loop.run_until_complete(some_coroutine())
    print(result)
finally:
    loop.close()
```

---

## 2. 高级并发控制

### Semaphore 限制并发数

```python
import asyncio
import aiohttp

async def fetch(session, url, semaphore):
    async with semaphore:  # 限制并发数
        async with session.get(url) as response:
            return await response.text()

async def main():
    semaphore = asyncio.Semaphore(5)  # 最多5个并发请求
    urls = [f"https://httpbin.org/get?id={i}" for i in range(20)]

    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url, semaphore) for url in urls]
        results = await asyncio.gather(*tasks)

asyncio.run(main())
```

### 批量处理

```python
async def process_batch(items, batch_size=10):
    """分批处理，控制并发"""
    semaphore = asyncio.Semaphore(batch_size)

    async def process_one(item):
        async with semaphore:
            await asyncio.sleep(0.1)  # 模拟处理
            return item * 2

    tasks = [process_one(item) for item in items]
    return await asyncio.gather(*tasks)

async def main():
    results = await process_batch(range(100), batch_size=10)
    print(f"处理了 {len(results)} 个")

asyncio.run(main())
```

---

## 3. 混合同步和异步

### 在协程中运行同步代码

```python
import asyncio
import time

def blocking_task():
    """同步阻塞函数"""
    time.sleep(2)
    return "同步结果"

async def main():
    # 方式1：使用 run_in_executor（推荐）
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, blocking_task)
    print(result)

    # 方式2：使用 to_thread（Python 3.9+）
    result = await asyncio.to_thread(blocking_task)
    print(result)

asyncio.run(main())
```

### 线程池执行器

```python
from concurrent.futures import ThreadPoolExecutor
import asyncio

executor = ThreadPoolExecutor(max_workers=4)

async def main():
    loop = asyncio.get_running_loop()

    # 在线程池中执行
    result = await loop.run_in_executor(
        executor,
        lambda: sum(range(1000000))
    )
    print(result)

asyncio.run(main())
```

---

## 4. 异步上下文管理器

```python
class AsyncDatabase:
    async def connect(self):
        print("连接数据库")
        await asyncio.sleep(0.5)
        return self

    async def disconnect(self):
        print("断开数据库")
        await asyncio.sleep(0.5)

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()

    async def query(self, sql):
        await asyncio.sleep(0.1)
        return f"结果: {sql}"

async def main():
    async with AsyncDatabase() as db:
        result = await db.query("SELECT * FROM users")
        print(result)

asyncio.run(main())
```

---

## 5. 异步生成器

```python
async def async_range(n):
    for i in range(n):
        await asyncio.sleep(0.1)
        yield i

async def main():
    async for num in async_range(5):
        print(num)

asyncio.run(main())
```

---

## 6. 实用模式

### 带重试的异步请求

```python
import asyncio

async def fetch_with_retry(session, url, max_retries=3):
    for attempt in range(max_retries):
        try:
            async with session.get(url, timeout=5) as response:
                return await response.text()
        except asyncio.TimeoutError:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt  # 指数退避
            print(f"重试 {url}, 等待 {wait}s")
            await asyncio.sleep(wait)
```

### 竞速执行

```python
async def race(tasks, timeout=None):
    """返回第一个完成的任务结果"""
    done, pending = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_COMPLETED,
        timeout=timeout
    )

    # 取消剩余任务
    for task in pending:
        task.cancel()

    # 返回第一个结果
    return done.pop().result()

async def main():
    tasks = [
        asyncio.create_task(asyncio.sleep(2, result="慢")),
        asyncio.create_task(asyncio.sleep(0.5, result="快")),
    ]
    result = await race(tasks)
    print(result)  # 快

asyncio.run(main())
```

---

## 实战练习

### 练习 1：异步限速器

```python
import asyncio
import time

class RateLimiter:
    """令牌桶限速器"""
    def __init__(self, rate, capacity):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens < 1:
                wait = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait)
                self.tokens = 0
            else:
                self.tokens -= 1

# 使用
limiter = RateLimiter(rate=5, capacity=5)  # 每秒5个请求

async def api_call(i):
    await limiter.acquire()
    print(f"请求 {i} at {time.strftime('%H:%M:%S')}")

async def main():
    await asyncio.gather(*[api_call(i) for i in range(10)])

asyncio.run(main())
```

### 练习 2：WebSocket 客户端

```python
import asyncio
import websockets

async def websocket_client():
    uri = "wss://echo.websocket.org"

    async with websockets.connect(uri) as websocket:
        # 发送消息
        await websocket.send("Hello Server!")

        # 接收响应
        response = await websocket.recv()
        print(f"收到: {response}")

# asyncio.run(websocket_client())
```

---

## 今日总结

- [ ] Semaphore 限制并发数
- [ ] `run_in_executor` 在线程池中运行同步代码
- [ ] 异步上下文管理器实现 `__aenter__` 和 `__aexit__`
- [ ] 异步生成器使用 `async for`
- [ ] `asyncio.wait` 可以设置返回条件
- [ ] 指数退避是重试的常用策略

---

*第 24 天 / 330 天*
