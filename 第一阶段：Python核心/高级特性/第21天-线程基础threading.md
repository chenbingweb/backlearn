# 第 21 天：线程基础、threading 模块

## 学习目标

- 理解线程的概念和用途
- 掌握 threading 模块的基本使用
- 学会线程同步
- 了解 GIL 的影响

---

## 1. 线程基础

### 什么是线程

线程是程序执行的最小单元，一个进程可以包含多个线程，它们共享进程的资源。

```python
import threading
import time

def worker():
    print(f"工作线程: {threading.current_thread().name}")
    time.sleep(1)
    print("工作完成")

# 创建线程
thread = threading.Thread(target=worker, name="Worker-1")
thread.start()      # 启动线程
thread.join()       # 等待线程结束
print("主线程继续")
```

### 传递参数

```python
def greet(name, greeting="Hello"):
    print(f"{greeting}, {name}!")

# 方式1：args 元组
thread1 = threading.Thread(target=greet, args=("Alice",))

# 方式2：kwargs 字典
thread2 = threading.Thread(target=greet, kwargs={"name": "Bob", "greeting": "Hi"})

thread1.start()
thread2.start()
thread1.join()
thread2.join()
```

---

## 2. 线程类

### 继承 Thread

```python
class DownloadThread(threading.Thread):
    def __init__(self, url, filename):
        super().__init__()
        self.url = url
        self.filename = filename

    def run(self):
        print(f"开始下载: {self.url}")
        time.sleep(2)  # 模拟下载
        print(f"下载完成: {self.filename}")

# 使用
threads = [
    DownloadThread("http://example.com/1.zip", "1.zip"),
    DownloadThread("http://example.com/2.zip", "2.zip"),
]

for t in threads:
    t.start()
for t in threads:
    t.join()
```

---

## 3. 线程同步

### 竞争条件

```python
import threading

counter = 0

def increment():
    global counter
    for _ in range(100000):
        counter += 1

threads = [threading.Thread(target=increment) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"期望: 1000000, 实际: {counter}")  # 实际值小于期望！
```

### Lock 锁

```python
import threading

counter = 0
lock = threading.Lock()

def increment():
    global counter
    for _ in range(100000):
        with lock:  # 自动获取和释放
            counter += 1

# 或者
# lock.acquire()
# counter += 1
# lock.release()

threads = [threading.Thread(target=increment) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"结果: {counter}")  # 1000000
```

### RLock 可重入锁

```python
rlock = threading.RLock()

def outer():
    with rlock:
        print("outer")
        inner()

def inner():
    with rlock:  # 同一线程可以再次获取
        print("inner")

outer()
```

### Semaphore 信号量

```python
# 限制同时访问的线程数
semaphore = threading.Semaphore(3)

def limited_resource():
    with semaphore:
        print(f"{threading.current_thread().name} 获取资源")
        time.sleep(1)
        print(f"{threading.current_thread().name} 释放资源")

threads = [threading.Thread(target=limited_resource) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

---

## 4. 线程间通信

### Event 事件

```python
event = threading.Event()

def waiter():
    print("等待信号...")
    event.wait()  # 阻塞直到事件被设置
    print("收到信号！")

def setter():
    time.sleep(2)
    print("发送信号")
    event.set()

threading.Thread(target=waiter).start()
threading.Thread(target=setter).start()
```

### Condition 条件变量

```python
condition = threading.Condition()
items = []

def producer():
    for i in range(5):
        with condition:
            items.append(i)
            print(f"生产: {i}")
            condition.notify()  # 通知消费者
        time.sleep(0.5)

def consumer():
    for _ in range(5):
        with condition:
            while not items:
                condition.wait()  # 等待生产
            item = items.pop(0)
            print(f"消费: {item}")

threading.Thread(target=producer).start()
threading.Thread(target=consumer).start()
```

---

## 5. GIL（全局解释器锁）

### GIL 的影响

```python
import threading
import multiprocessing
import time

def cpu_bound_task():
    count = 0
    for i in range(10_000_000):
        count += i
    return count

# 多线程（CPU 密集型）- 不会加速
start = time.time()
threads = [threading.Thread(target=cpu_bound_task) for _ in range(2)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print(f"多线程: {time.time() - start:.2f}s")

# 多进程（CPU 密集型）- 会加速
start = time.time()
processes = [multiprocessing.Process(target=cpu_bound_task) for _ in range(2)]
for p in processes:
    p.start()
for p in processes:
    p.join()
print(f"多进程: {time.time() - start:.2f}s")
```

### GIL 总结

- **线程**：适合 I/O 密集型任务（网络、文件）
- **进程**：适合 CPU 密集型任务（计算）

---

## 实战练习

### 练习 1：线程池下载器

```python
import threading
import queue
import time

class ThreadPool:
    def __init__(self, num_workers=4):
        self.tasks = queue.Queue()
        self.workers = []
        for _ in range(num_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.workers.append(t)

    def _worker(self):
        while True:
            func, args, kwargs = self.tasks.get()
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"任务出错: {e}")
            finally:
                self.tasks.task_done()

    def submit(self, func, *args, **kwargs):
        self.tasks.put((func, args, kwargs))

    def wait(self):
        self.tasks.join()

# 使用
def download(url):
    print(f"下载: {url}")
    time.sleep(1)
    print(f"完成: {url}")

pool = ThreadPool(3)
for i in range(10):
    pool.submit(download, f"http://example.com/{i}.txt")

pool.wait()
```

### 练习 2：并发爬虫

```python
import threading
import queue
import time
import random

class ConcurrentCrawler:
    def __init__(self, max_workers=5):
        self.urls = queue.Queue()
        self.results = queue.Queue()
        self.lock = threading.Lock()
        self.seen = set()
        self.workers = max_workers

    def add_url(self, url):
        with self.lock:
            if url not in self.seen:
                self.seen.add(url)
                self.urls.put(url)

    def _fetch(self, url):
        time.sleep(random.uniform(0.5, 1.5))  # 模拟请求
        return f"内容 of {url}"

    def _worker(self):
        while True:
            try:
                url = self.urls.get(timeout=1)
            except queue.Empty:
                break

            try:
                content = self._fetch(url)
                self.results.put((url, content))
            except Exception as e:
                print(f"获取失败 {url}: {e}")
            finally:
                self.urls.task_done()

    def run(self, seed_urls):
        for url in seed_urls:
            self.add_url(url)

        threads = []
        for _ in range(self.workers):
            t = threading.Thread(target=self._worker)
            t.start()
            threads.append(t)

        self.urls.join()
        for t in threads:
            t.join()

        results = []
        while not self.results.empty():
            results.append(self.results.get())
        return results

# 使用
crawler = ConcurrentCrawler(3)
results = crawler.run([f"http://site.com/page{i}" for i in range(10)])
print(f"爬取完成: {len(results)} 个页面")
```

---

## 今日总结

- [ ] 线程是轻量级的并发执行单元
- [ ] threading.Thread 创建和启动线程
- [ ] Lock/Rlock/Semaphore 用于线程同步
- [ ] Event/Condition 用于线程通信
- [ ] GIL 限制线程的 CPU 并行能力
- [ ] 线程适合 I/O 密集型，进程适合 CPU 密集型

---

*第 21 天 / 330 天*
