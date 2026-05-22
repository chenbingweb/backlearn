# 第 17 天：生成器、yield、迭代器协议

## 学习目标

- 理解迭代器和可迭代对象的区别
- 掌握生成器的创建和使用
- 理解 yield 关键字的工作原理
- 学会使用生成器表达式

---

## 1. 迭代器协议

### 可迭代对象 vs 迭代器

```python
# 可迭代对象（Iterable）：可以被 for 循环遍历
my_list = [1, 2, 3]
my_str = "hello"
my_dict = {"a": 1, "b": 2}

# 迭代器（Iterator）：可以逐个返回元素的对象
iterator = iter(my_list)
print(next(iterator))  # 1
print(next(iterator))  # 2
print(next(iterator))  # 3
# print(next(iterator))  # StopIteration!
```

### 迭代器协议

一个对象要成为迭代器，必须实现两个方法：

- `__iter__()`：返回迭代器自身
- `__next__()`：返回下一个元素，没有则抛出 StopIteration

```python
class CountDown:
    """倒数迭代器"""
    def __init__(self, start):
        self.start = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.start <= 0:
            raise StopIteration
        self.start -= 1
        return self.start + 1

# 使用
count = CountDown(5)
for num in count:
    print(num)  # 5, 4, 3, 2, 1
```

### 可迭代对象（不是迭代器）

```python
class Range:
    """自定义 range"""
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __iter__(self):
        """返回一个新的迭代器"""
        return RangeIterator(self.start, self.end)

class RangeIterator:
    """Range 的迭代器"""
    def __init__(self, start, end):
        self.current = start
        self.end = end

    def __iter__(self):
        return self

    def __next__(self):
        if self.current >= self.end:
            raise StopIteration
        num = self.current
        self.current += 1
        return num

# 可以多次遍历
r = Range(1, 5)
print(list(r))  # [1, 2, 3, 4]
print(list(r))  # [1, 2, 3, 4]  ← 可以重复遍历！
```

---

## 2. 生成器

### 什么是生成器

生成器是使用 `yield` 关键字的函数，调用时返回一个生成器对象。

```python
def simple_generator():
    yield 1
    yield 2
    yield 3

# 调用生成器函数返回生成器对象
gen = simple_generator()
print(type(gen))  # <class 'generator'>

print(next(gen))  # 1
print(next(gen))  # 2
print(next(gen))  # 3
# print(next(gen))  # StopIteration
```

### 生成器的工作原理

```python
def count_up_to(n):
    count = 1
    while count <= n:
        yield count  # 暂停，返回 count
        count += 1   # 下次从这里继续

# 使用
counter = count_up_to(5)
for num in counter:
    print(num)  # 1, 2, 3, 4, 5
```

### yield 的状态保存

```python
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# 生成无限斐波那契数列
fib = fibonacci()
for _ in range(10):
    print(next(fib), end=" ")  # 0 1 1 2 3 5 8 13 21 34
```

---

## 3. 生成器表达式

```python
# 列表推导式（一次性生成所有数据）
squares_list = [x**2 for x in range(1000000)]  # 内存占用大

# 生成器表达式（惰性求值）
squares_gen = (x**2 for x in range(1000000))   # 几乎不占内存

print(sum(squares_gen))  # 可以逐个处理

# 使用场景
lines = (line.strip() for line in open("large_file.txt"))
valid_lines = (line for line in lines if line)
word_counts = (len(line.split()) for line in valid_lines)
total_words = sum(word_counts)  # 逐行处理，内存友好
```

---

## 4. yield from

### 委托给子生成器

```python
def sub_generator():
    yield 1
    yield 2
    yield 3

def main_generator():
    yield "start"
    yield from sub_generator()  # 委托给子生成器
    yield "end"

print(list(main_generator()))  # ['start', 1, 2, 3, 'end']
```

### 嵌套列表展平

```python
def flatten(nested):
    """展平嵌套列表"""
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item

nested = [1, [2, [3, 4], 5], 6, [7]]
print(list(flatten(nested)))  # [1, 2, 3, 4, 5, 6, 7]
```

---

## 5. send() 和双向通信

```python
def accumulator():
    total = 0
    while True:
        value = yield total  # 接收 send 的值，返回 total
        if value is None:
            break
        total += value

acc = accumulator()
next(acc)  # 预激生成器

print(acc.send(10))   # 10
print(acc.send(20))   # 30
print(acc.send(5))    # 35
acc.close()
```

---

## 6. 生成器的优势

| 特性 | 列表 | 生成器 |
|------|------|--------|
| 内存占用 | 存储所有元素 | 只存当前状态 |
| 惰性求值 | 否 | 是 |
| 无限序列 | 不可能 | 可以 |
| 复用性 | 可以多次遍历 | 只能遍历一次 |

---

## 实战练习

### 练习 1：文件读取生成器

```python
def read_lines(filename):
    """逐行读取大文件"""
    with open(filename, "r") as f:
        for line in f:
            yield line.strip()

def grep(pattern, lines):
    """过滤包含模式的行"""
    for line in lines:
        if pattern in line:
            yield line

def count_words(lines):
    """统计每行的单词数"""
    for line in lines:
        yield len(line.split())

# 管道式处理
lines = read_lines("data.txt")
matched = grep("error", lines)
word_counts = count_words(matched)
total = sum(word_counts)
```

### 练习 2：自定义 range

```python
def my_range(start, stop=None, step=1):
    if stop is None:
        start, stop = 0, start
    while (step > 0 and start < stop) or (step < 0 and start > stop):
        yield start
        start += step

print(list(my_range(5)))        # [0, 1, 2, 3, 4]
print(list(my_range(1, 10, 2)))  # [1, 3, 5, 7, 9]
print(list(my_range(10, 0, -2)))  # [10, 8, 6, 4, 2]
```

### 练习 3：无限质数生成器

```python
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def primes():
    """无限质数生成器"""
    n = 2
    while True:
        if is_prime(n):
            yield n
        n += 1

p = primes()
first_20 = [next(p) for _ in range(20)]
print(first_20)
```

---

## 今日总结

- [ ] 迭代器实现 `__iter__` 和 `__next__`
- [ ] 生成器使用 `yield` 暂停和恢复执行
- [ ] 生成器表达式比列表推导式更省内存
- [ ] `yield from` 委托给子生成器
- [ ] `send()` 实现与生成器的双向通信
- [ ] 生成器适合处理大数据流和无限序列

---

*第 17 天 / 330 天*
