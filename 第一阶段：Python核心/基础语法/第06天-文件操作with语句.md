# 第 6 天：文件操作、with 语句

## 学习目标

- 掌握文件打开、读写、关闭
- 理解 with 语句的优势
- 学会处理文件和目录
- 了解文件指针和模式

---

## 1. 文件基础操作

### 打开文件

```python
# 基本语法
file = open("filename", "mode")

# 模式
# 'r' - 读模式（默认）
# 'w' - 写模式（覆盖）
# 'a' - 追加模式
# 'x' - 创建新文件（若存在则报错）
# 'b' - 二进制模式
# 't' - 文本模式（默认）
# '+' - 读写模式

# 常用组合
file = open("test.txt", "r")          # 文本读
file = open("test.txt", "w")          # 文本写
file = open("test.txt", "a")          # 文本追加
file = open("test.dat", "rb")         # 二进制读
file = open("test.dat", "wb")         # 二进制写
```

### 关闭文件

```python
# 方法1：手动关闭
file = open("test.txt", "r")
content = file.read()
file.close()  # 忘记关闭会资源泄漏

# 方法2：with 语句（推荐）
with open("test.txt", "r") as file:
    content = file.read()
# with 块结束后自动关闭文件
```

### 读取文件

```python
# 读取全部
with open("test.txt", "r") as f:
    content = f.read()
    print(content)

# 读取一行
with open("test.txt", "r") as f:
    line = f.readline()
    print(line)

# 读取所有行到列表
with open("test.txt", "r") as f:
    lines = f.readlines()
    for line in lines:
        print(line.strip())

# 遍历文件对象（推荐，内存高效）
with open("test.txt", "r") as f:
    for line in f:
        print(line.strip())
```

### 写入文件

```python
# 写入字符串
with open("test.txt", "w") as f:
    f.write("Hello, World!\n")
    f.write("第二行")

# 写入多行
lines = ["第一行\n", "第二行\n", "第三行\n"]
with open("test.txt", "w") as f:
    f.writelines(lines)

# 使用 print 写入（自动加换行）
with open("test.txt", "w") as f:
    print("第一行", file=f)
    print("第二行", file=f)
```

### 追加模式

```python
# 追加内容
with open("test.txt", "a") as f:
    f.write("\n追加的内容")

# 追加多行
with open("test.txt", "a") as f:
    f.writelines(["\n新行1\n", "新行2\n"])
```

---

## 2. 文件指针

### tell 和 seek

```python
with open("test.txt", "r") as f:
    print(f.read(5))    # 读取前5个字符
    position = f.tell()  # 获取当前指针位置
    print(f"当前位置: {position}")
    print(f.read(5))    # 继续读取5个字符

    f.seek(0)          # 回到文件开头
    print(f.read())     # 重新读取全部

    f.seek(0, 2)        # 移到文件末尾（seek(offset, whence)）
    print(f.tell())     # 文件大小
```

### whence 参数

```python
# seek(offset, whence)
# whence: 0 - 从文件开头（默认）
# whence: 1 - 从当前位置
# whence: 2 - 从文件末尾

with open("test.txt", "rb") as f:
    f.seek(-5, 2)      # 从末尾往前5个字节
    print(f.read())
```

---

## 3. with 语句详解

### 为什么使用 with

```python
# 不使用 with - 需要手动关闭
file = open("test.txt", "r")
try:
    content = file.read()
    # 处理内容
finally:
    file.close()  # 确保关闭

# 使用 with - 自动关闭
with open("test.txt", "r") as file:
    content = file.read()
    # 自动关闭，无需手动处理
```

### 上下文管理器协议

```python
# __enter__ 和 __exit__
class MyContextManager:
    def __enter__(self):
        print("进入上下文")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("退出上下文")
        return False  # 返回 True 抑制异常

with MyContextManager() as cm:
    print("在上下文中")
```

### 嵌套 with 语句

```python
# 旧写法（嵌套）
with open("file1.txt", "r") as f1:
    content1 = f1.read()
    with open("file2.txt", "r") as f2:
        content2 = f2.read()

# Python 3.10+ 支持的写法
with (
    open("file1.txt", "r") as f1,
    open("file2.txt", "r") as f2
):
    content1 = f1.read()
    content2 = f2.read()
```

---

## 4. os 模块文件操作

### 文件检查

```python
import os

os.path.exists("test.txt")       # 文件是否存在
os.path.isfile("test.txt")      # 是否是文件
os.path.isdir("folder")         # 是否是目录
os.path.getsize("test.txt")     # 文件大小（字节）
os.path.getmtime("test.txt")    # 修改时间（时间戳）
```

### 文件操作

```python
import os

os.rename("old.txt", "new.txt")     # 重命名
os.remove("file.txt")               # 删除文件
os.link("src.txt", "hard_link.txt") # 创建硬链接
os.symlink("src.txt", "sym_link.txt")  # 创建符号链接
```

### 目录操作

```python
import os

os.mkdir("new_folder")            # 创建目录
os.makedirs("a/b/c", exist_ok=True)  # 递归创建目录
os.rmdir("folder")               # 删除空目录
os.rmdir("a/b/c")                # 删除 c，a/b 仍存在

# 列出目录内容
os.listdir(".")                  # 返回所有文件和目录名
os.listdir("folder")             # 返回 folder 内的内容

# 遍历目录树
for root, dirs, files in os.walk("."):
    print(f"目录: {root}")
    print(f"子目录: {dirs}")
    print(f"文件: {files}")
```

---

## 5. shutil 模块

```python
import shutil

shutil.copy("src.txt", "dst.txt")           # 复制文件
shutil.copytree("src_dir", "dst_dir")       # 复制目录
shutil.move("src.txt", "dst.txt")           # 移动文件/目录
shutil.rmtree("folder")                     # 删除目录树
shutil.make_archive("archive", "zip", "folder")  # 创建压缩包
shutil.unpack_archive("archive.zip", "extract_dir")  # 解压
```

---

## 6. pathlib 模块（现代方式）

```python
from pathlib import Path

# 创建路径对象
p = Path("folder/file.txt")

# 路径操作
p.exists()                # 文件是否存在
p.is_file()               # 是否是文件
p.is_dir()                # 是否是目录
p.mkdir(parents=True, exist_ok=True)  # 创建目录
p.rmdir()                 # 删除空目录
p.unlink()                # 删除文件

# 读取文件
content = p.read_text()
bytes = p.read_bytes()

# 写入文件
p.write_text("Hello")
p.write_bytes(b"bytes")

# 遍历目录
for item in Path(".").iterdir():
    print(item.name)

# glob 模式
for py_file in Path(".").glob("*.py"):
    print(py_file)

# 拼接路径
p = Path("folder") / "subfolder" / "file.txt"

# 获取各部分
print(p.parent)      # folder/subfolder
print(p.name)        # file.txt
print(p.stem)        # file
print(p.suffix)      # .txt
```

---

## 7. 编码问题

### 指定编码

```python
# 推荐始终指定 encoding
with open("test.txt", "r", encoding="utf-8") as f:
    content = f.read()

with open("test.txt", "w", encoding="utf-8") as f:
    f.write("中文内容")

# 处理编码错误
with open("test.txt", "r", encoding="utf-8", errors="replace") as f:
    content = f.read()
```

### 常见编码错误处理

```python
# errors 参数选项
# 'strict' - 默认，原生编码错误
# 'ignore' - 忽略错误字节
# 'replace' - 用 ? 替换错误字节
# 'surrogateescape' - 将错误字节转为代理字符
```

---

## 8. 实战练习

### 练习 1：文件复制工具

```python
import shutil
from pathlib import Path

def copy_file(src, dst):
    """复制文件"""
    shutil.copy(src, dst)
    print(f"已复制 {src} -> {dst}")

def copy_file_with_progress(src, dst):
    """带进度显示的文件复制"""
    src_size = Path(src).stat().st_size
    copied = 0

    with open(src, "rb") as fsrc:
        with open(dst, "wb") as fdst:
            while True:
                chunk = fsrc.read(1024 * 1024)  # 1MB
                if not chunk:
                    break
                fdst.write(chunk)
                copied += len(chunk)
                progress = copied / src_size * 100
                print(f"\r进度: {progress:.1f}%", end="")
    print("\n复制完成!")
```

### 练习 2：日志文件分析

```python
from pathlib import Path
from collections import Counter

def analyze_log(log_file):
    """分析日志文件，统计各级别日志数量"""
    log_levels = Counter()

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if "[ERROR]" in line:
                log_levels["ERROR"] += 1
            elif "[WARNING]" in line:
                log_levels["WARNING"] += 1
            elif "[INFO]" in line:
                log_levels["INFO"] += 1

    print("日志统计:")
    for level, count in log_levels.items():
        print(f"  {level}: {count}")

# 使用示例
# analyze_log("app.log")
```

### 练习 3：批量重命名

```python
from pathlib import Path

def batch_rename(folder, prefix="file_", start=1):
    """批量重命名文件"""
    folder = Path(folder)
    counter = start

    for file in sorted(folder.iterdir()):
        if file.is_file():
            new_name = f"{prefix}{counter:03d}{file.suffix}"
            new_path = folder / new_name
            file.rename(new_path)
            print(f"{file.name} -> {new_name}")
            counter += 1

# 使用示例
# batch_rename("images", prefix="photo_", start=1)
```

---

## 今日总结

- [ ] 掌握文件打开、读写、关闭
- [ ] 熟练使用 with 语句
- [ ] 理解文件指针和 seek 操作
- [ ] 学会使用 os/shutil/pathlib 操作文件和目录
- [ ] 注意编码问题，建议始终指定 utf-8

---

*第 6 天 / 330 天*
