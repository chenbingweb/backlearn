# 第 22 天：进程基础、multiprocessing 模块

## 学习目标

- 理解进程和线程的区别
- 掌握 multiprocessing 模块的使用
- 学会进程间通信
- 了解进程池

---

## 1. 进程 vs 线程

| 特性 | 进程 | 线程 |
|------|------|------|
| 内存空间 | 独立 | 共享 |
| 创建开销 | 大 | 小 |
| 通信方式 | IPC（复杂） | 直接共享（简单） |
| 崩溃影响 | 不影响其他进程 | 可能导致整个程序崩溃 |
| GIL | 每个进程独立 | 受 GIL 限制 |
| 适用场景 | CPU 密集型 | I/O 密集型 |

---

## 2. 创建进程

### 基本用法

```python
import multiprocessing
import os
import time

def worker(name):
    print(f"进程 {name}, PID: {os.getpid()}")
    time.sleep(1)
    print(f"{name} 完成")

if __name__ == "__main__":
    print(f"主进程 PID: {os.getpid()}")

    p = multiprocessing.Process(target=worker, args=("Worker-1",))
    p.start()
    p.join()
    print("主进程结束")
```

### 继承 Process

```python
class WorkerProcess(multiprocessing.Process):
    def __init__(self, task_id):
        super().__init__()
        self.task_id = task_id

    def run(self):
        print(f"处理任务 {self.task_id}, PID: {os.getpid()}")
        time.sleep(1)
        print(f"任务 {self.task_id} 完成")

if __name__ == "__main__":
    processes = [WorkerProcess(i) for i in range(4)]
    for p in processes:
        p.start()
    for p in processes:
        p.join()
```

---

## 3. 进程池

### Pool 的基本使用

```python
from multiprocessing import Pool
import time

def square(n):
    return n * n

if __name__ == "__main__":
    numbers = list(range(1, 11))

    # 创建4个进程的进程池
    with Pool(4) as pool:
        # map：阻塞等待所有结果
        results = pool.map(square, numbers)
        print(results)  # [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]

        # map_async：异步执行
        async_result = pool.map_async(square, numbers)
        print(async_result.get())

        # apply：单个任务
        result = pool.apply(square, (5,))
        print(result)  # 25

        # apply_async：异步单个任务
        async_res = pool.apply_async(square, (10,))
        print(async_res.get())  # 100
```

### CPU 密集型任务加速

```python
from multiprocessing import Pool
import time

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

if __name__ == "__main__":
    numbers = list(range(2, 100000))

    # 单进程
    start = time.time()
    result_single = list(map(is_prime, numbers))
    print(f"单进程: {time.time() - start:.2f}s")

    # 多进程
    start = time.time()
    with Pool() as pool:
        result_multi = pool.map(is_prime, numbers)
    print(f"多进程: {time.time() - start:.2f}s")
```

---

## 4. 进程间通信

### Queue 队列

```python
from multiprocessing import Process, Queue

def producer(queue):
    for i in range(5):
        queue.put(f"数据-{i}")
        print(f"生产: 数据-{i}")

def consumer(queue):
    for _ in range(5):
        data = queue.get()
        print(f"消费: {data}")

if __name__ == "__main__":
    queue = Queue()

    p1 = Process(target=producer, args=(queue,))
    p2 = Process(target=consumer, args=(queue,))

    p1.start()
    p2.start()
    p1.join()
    p2.join()
```

### Pipe 管道

```python
from multiprocessing import Process, Pipe

def sender(conn):
    conn.send("Hello from sender")
    conn.close()

def receiver(conn):
    msg = conn.recv()
    print(f"收到: {msg}")

if __name__ == "__main__":
    parent_conn, child_conn = Pipe()

    p1 = Process(target=sender, args=(child_conn,))
    p2 = Process(target=receiver, args=(parent_conn,))

    p1.start()
    p2.start()
    p1.join()
    p2.join()
```

### Manager 共享对象

```python
from multiprocessing import Process, Manager

def worker(d, l, n):
    d[n] = n * n
    l.append(n)
    print(f"进程 {n}: {dict(d)}, {list(l)}")

if __name__ == "__main__":
    with Manager() as manager:
        shared_dict = manager.dict()
        shared_list = manager.list()

        processes = [
            Process(target=worker, args=(shared_dict, shared_list, i))
            for i in range(4)
        ]

        for p in processes:
            p.start()
        for p in processes:
            p.join()

        print(f"最终结果: {dict(shared_dict)}")
        print(f"列表: {list(shared_list)}")
```

---

## 5. 进程同步

### Lock

```python
from multiprocessing import Process, Lock
import time

def printer(lock, text):
    with lock:
        print(text)
        time.sleep(0.1)

if __name__ == "__main__":
    lock = Lock()

    processes = [
        Process(target=printer, args=(lock, f"第{i}行"))
        for i in range(10)
    ]

    for p in processes:
        p.start()
    for p in processes:
        p.join()
```

---

## 实战练习

### 练习 1：并行文件处理

```python
from multiprocessing import Pool
import os

def process_file(filename):
    """处理单个文件"""
    with open(filename, "r") as f:
        content = f.read()
    word_count = len(content.split())
    return filename, word_count

if __name__ == "__main__":
    # 假设有多个文本文件
    files = [f"doc{i}.txt" for i in range(10)]

    with Pool() as pool:
        results = pool.map(process_file, files)

    for filename, count in results:
        print(f"{filename}: {count} 词")
```

### 练习 2：MapReduce 简化版

```python
from multiprocessing import Pool
from collections import Counter

def map_word_count(chunk):
    """映射：统计块中单词"""
    words = chunk.lower().split()
    return Counter(words)

def reduce_counts(counters):
    """归约：合并计数"""
    total = Counter()
    for c in counters:
        total.update(c)
    return total

if __name__ == "__main__":
    # 模拟大数据
    text = "hello world " * 10000
    chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]

    with Pool(4) as pool:
        mapped = pool.map(map_word_count, chunks)

    result = reduce_counts(mapped)
    print(result.most_common(5))
```

---

## 今日总结

- [ ] 进程有独立的内存空间，不受 GIL 限制
- [ ] multiprocessing.Process 创建进程
- [ ] Pool 管理进程池，支持 map/apply
- [ ] Queue/Pipe/Manager 实现进程间通信
- [ ] 进程适合 CPU 密集型任务
- [ ] Windows 上需要用 `if __name__ == "__main__"`

---

*第 22 天 / 330 天*
