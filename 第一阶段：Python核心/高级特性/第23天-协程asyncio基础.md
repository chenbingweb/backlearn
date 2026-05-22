# 第 23 天：协程、asyncio 基础

## 学习目标

- 理解协程的概念和优势
- 掌握 asyncio 的基本使用
- 学会定义和运行协程
- 了解异步和同步的区别

---

## 1. 什么是协程

协程（Coroutine）是可以暂停和恢复执行的函数，比线程更轻量。

```
同步：任务A → 等待 → 完成 → 任务B → 等待 → 完成
线程：任务A → 创建线程 → 任务B → 上下文切换开销
协程：任务A → 挂起 → 任务B → 挂起 → 任务A恢复（无上下文切换）
```

---

## 2. async/await 基础

### 定义协程

```python
import asyncio

async def hello():
    print("Hello")
    await asyncio.sleep(1)  # 模拟异步操作
    print("World")

# 运行协程
asyncio.run(hello())
```

### 多个协程

```python
async def task(name, delay):
    print(f"任务 {name} 开始")
    await asyncio.sleep(delay)
    print(f"任务 {name} 完成")

async def main():
    # 串行执行
    await task("A", 1)
    await task("B", 1)
    # 总耗时 2 秒

asyncio.run(main())
```

### 并发执行

```python
async def main():
    # 并发执行（使用 gather）
    await asyncio.gather(
        task("A", 1),
        task("B", 1),
        task("C", 1),
    )
    # 总耗时约 1 秒

asyncio.run(main())
```

---

## 3. 创建任务

### asyncio.create_task

```python
async def main():
    # 创建任务
    task1 = asyncio.create_task(task("A", 2))
    task2 = asyncio.create_task(task("B", 1))

    # 等待任务完成
    await task1
    await task2

asyncio.run(main())
```

### 任务回调

```python
async def my_task():
    await asyncio.sleep(1)
    return "结果"

def on_complete(task):
    print(f"任务完成: {task.result()}")

async def main():
    t = asyncio.create_task(my_task())
    t.add_done_callback(on_complete)
    await t

asyncio.run(main())
```

---

## 4. 超时和取消

### 超时控制

```python
async def slow_task():
    await asyncio.sleep(10)
    return "完成"

async def main():
    try:
        result = await asyncio.wait_for(slow_task(), timeout=2)
    except asyncio.TimeoutError:
        print("任务超时！")

asyncio.run(main())
```

### 取消任务

```python
async def worker():
    try:
        while True:
            print("工作中...")
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("任务被取消")
        raise

async def main():
    task = asyncio.create_task(worker())
    await asyncio.sleep(3)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("确认取消")

asyncio.run(main())
```

---

## 5. 异步迭代器

```python
class AsyncCounter:
    def __init__(self, limit):
        self.limit = limit
        self.current = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.current >= self.limit:
            raise StopAsyncIteration
        await asyncio.sleep(0.1)
        self.current += 1
        return self.current

async def main():
    async for num in AsyncCounter(5):
        print(num)

asyncio.run(main())
```

---

## 6. 与同步代码对比

### 同步版本

```python
import time
import requests  # 假设的请求库

def fetch_url(url):
    time.sleep(1)  # 模拟网络请求
    return f"数据 from {url}"

start = time.time()
results = [fetch_url(f"http://api.com/{i}") for i in range(10)]
print(f"耗时: {time.time() - start:.2f}s")  # ~10s
```

### 异步版本

```python
import asyncio
import aiohttp

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_url(session, f"http://api.com/{i}")
            for i in range(10)
        ]
        results = await asyncio.gather(*tasks)
        return results

# asyncio.run(main())  # ~1s
```

---

## 实战练习

### 练习 1：异步爬虫

```python
import asyncio
import aiohttp

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def main():
    urls = [f"https://httpbin.org/get?id={i}" for i in range(10)]

    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)

    print(f"获取了 {len(results)} 个页面")

asyncio.run(main())
```

### 练习 2：异步生产者消费者

```python
import asyncio

async def producer(queue, n):
    for i in range(n):
        await asyncio.sleep(0.1)
        await queue.put(i)
        print(f"生产: {i}")
    await queue.put(None)  # 结束信号

async def consumer(queue):
    while True:
        item = await queue.get()
        if item is None:
            break
        await asyncio.sleep(0.2)
        print(f"消费: {item}")
        queue.task_done()

async def main():
    queue = asyncio.Queue(maxsize=5)
    await asyncio.gather(
        producer(queue, 10),
        consumer(queue),
    )

asyncio.run(main())
```

---

## 今日总结

- [ ] `async def` 定义协程，`await` 等待协程完成
- [ ] `asyncio.run()` 运行主协程
- [ ] `asyncio.gather()` 并发执行多个协程
- [ ] `asyncio.create_task()` 创建后台任务
- [ ] `asyncio.wait_for()` 设置超时
- [ ] 协程适合高并发 I/O 场景

---

*第 23 天 / 330 天*
