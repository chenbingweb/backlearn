# 第 18 天：上下文管理器、with 语句原理

## 学习目标

- 理解 with 语句的执行流程
- 掌握上下文管理器协议
- 学会自定义上下文管理器
- 了解 contextlib 模块

---

## 1. with 语句回顾

### 基本用法

```python
# 自动关闭文件
with open("test.txt", "w") as f:
    f.write("Hello")
# 文件自动关闭
```

### 等价代码

```python
# 不使用 with
f = open("test.txt", "w")
try:
    f.write("Hello")
finally:
    f.close()  # 确保关闭
```

---

## 2. 上下文管理器协议

一个对象要成为上下文管理器，必须实现：

- `__enter__(self)`：进入 with 块时调用，返回值赋给 as 变量
- `__exit__(self, exc_type, exc_val, exc_tb)`：退出 with 块时调用

```python
class ManagedFile:
    """自定义文件上下文管理器"""
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode
        self.file = None

    def __enter__(self):
        print(f"打开文件: {self.filename}")
        self.file = open(self.filename, self.mode)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            print(f"关闭文件: {self.filename}")
            self.file.close()
        # 返回 True 抑制异常，False 传播异常
        return False

# 使用
with ManagedFile("test.txt", "w") as f:
    f.write("Hello, World!")
```

### __exit__ 参数详解

```python
class ExceptionLogger:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print(f"异常类型: {exc_type.__name__}")
            print(f"异常信息: {exc_val}")
            # 返回 True 会抑制异常
            return False  # 传播异常

with ExceptionLogger():
    raise ValueError("出错了！")
```

---

## 3. contextlib 模块

### @contextmanager

使用生成器简化上下文管理器的创建。

```python
from contextlib import contextmanager

@contextmanager
def managed_file(filename, mode):
    """使用装饰器创建上下文管理器"""
    print(f"打开: {filename}")
    f = open(filename, mode)
    try:
        yield f  # yield 的值赋给 as 变量
    finally:
        print(f"关闭: {filename}")
        f.close()

# 使用
with managed_file("test.txt", "w") as f:
    f.write("Hello")
```

### 数据库连接示例

```python
from contextlib import contextmanager
import sqlite3

@contextmanager
def database_connection(db_path):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()  # 成功时提交
    except Exception:
        conn.rollback()  # 异常时回滚
        raise
    finally:
        conn.close()

# 使用
with database_connection("app.db") as conn:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
```

### 计时上下文

```python
from contextlib import contextmanager
import time

@contextmanager
def timer(name="操作"):
    start = time.time()
    yield
    elapsed = time.time() - start
    print(f"{name} 耗时: {elapsed:.4f}秒")

# 使用
with timer("数据处理"):
    time.sleep(1)
    # 执行耗时操作
```

---

## 4. 实用工具

### suppress 忽略异常

```python
from contextlib import suppress

# 忽略 FileNotFoundError
with suppress(FileNotFoundError):
    os.remove("不存在的文件.txt")
# 不会报错

# 等同于
try:
    os.remove("不存在的文件.txt")
except FileNotFoundError:
    pass
```

### redirect_stdout 重定向输出

```python
from contextlib import redirect_stdout
import io

output = io.StringIO()
with redirect_stdout(output):
    print("这条输出被捕获")
    print("不会显示在控制台")

result = output.getvalue()
print(f"捕获内容: {result.strip()}")
```

### ExitStack 动态管理多个上下文

```python
from contextlib import ExitStack

with ExitStack() as stack:
    files = [
        stack.enter_context(open(f"file{i}.txt", "w"))
        for i in range(3)
    ]
    # 所有文件都会自动关闭
    for i, f in enumerate(files):
        f.write(f"Content {i}")
```

---

## 实战练习

### 练习 1：临时目录上下文

```python
import os
import tempfile
import shutil
from contextlib import contextmanager

@contextmanager
def temp_directory():
    """创建临时目录，结束后自动清理"""
    dir_path = tempfile.mkdtemp()
    original_dir = os.getcwd()
    try:
        os.chdir(dir_path)
        yield dir_path
    finally:
        os.chdir(original_dir)
        shutil.rmtree(dir_path)

# 使用
with temp_directory() as tmpdir:
    print(f"在临时目录: {tmpdir}")
    with open("test.txt", "w") as f:
        f.write("临时文件")
    # 目录自动清理
```

### 练习 2：重试上下文

```python
from contextlib import contextmanager
import time

@contextmanager
def retry_on_error(max_retries=3, delay=1):
    """在 with 块内自动重试"""
    last_exception = None
    for attempt in range(max_retries):
        try:
            yield attempt
            return  # 成功退出
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                print(f"尝试 {attempt + 1} 失败，{delay}秒后重试...")
                time.sleep(delay)
    raise last_exception

# 使用
import random

def unstable():
    if random.random() < 0.7:
        raise RuntimeError("随机失败")
    return "成功"

with retry_on_error(max_retries=5) as attempt:
    print(f"第 {attempt + 1} 次尝试")
    result = unstable()
    print(result)
```

---

## 今日总结

- [ ] 上下文管理器实现 `__enter__` 和 `__exit__`
- [ ] `__exit__` 返回 True 会抑制异常
- [ ] `@contextmanager` 用生成器简化创建
- [ ] `contextlib.suppress` 忽略指定异常
- [ ] `ExitStack` 动态管理多个上下文
- [ ] with 语句确保资源正确释放

---

*第 18 天 / 330 天*
