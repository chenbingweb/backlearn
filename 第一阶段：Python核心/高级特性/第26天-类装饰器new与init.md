# 第 26 天：类装饰器、__new__ 与 __init__

## 学习目标

- 理解 __new__ 和 __init__ 的区别
- 掌握类装饰器的编写
- 了解元类的概念
- 学会使用 __call__ 方法

---

## 1. __new__ vs __init__

### 执行顺序

```python
class Demo:
    def __new__(cls, *args, **kwargs):
        print(f"1. __new__ 创建实例: {cls}")
        instance = super().__new__(cls)
        return instance

    def __init__(self, value):
        print(f"2. __init__ 初始化实例: {value}")
        self.value = value

d = Demo(42)
# 1. __new__ 创建实例: <class 'Demo'>
# 2. __init__ 初始化实例: 42
```

### 关键区别

| | __new__ | __init__ |
|--|---------|----------|
| 调用时机 | 创建实例之前 | 创建实例之后 |
| 第一个参数 | cls（类） | self（实例） |
| 返回值 | 新实例 | None |
| 用途 | 控制实例创建 | 初始化实例 |

### __new__ 的应用：单例

```python
class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

s1 = Singleton()
s2 = Singleton()
print(s1 is s2)  # True
```

### __new__ 的应用：不可变子类

```python
class PositiveInt(int):
    """只允许正整数"""
    def __new__(cls, value):
        if value < 0:
            raise ValueError("必须为正数")
        return super().__new__(cls, value)

n = PositiveInt(10)
print(n)  # 10
# PositiveInt(-5)  # ValueError!
```

---

## 2. 类装饰器

### 用函数装饰类

```python
def singleton(cls):
    """类装饰器：将类变成单例"""
    instances = {}
    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return wrapper

@singleton
class Database:
    def __init__(self, url):
        self.url = url
        print(f"连接: {url}")

db1 = Database("localhost")
db2 = Database("remote")
print(db1 is db2)    # True
print(db1.url)       # localhost
```

### 用类装饰类

```python
class AutoRepr:
    """自动添加 __repr__ 的装饰器类"""
    def __init__(self, cls):
        self.cls = cls
        self.cls.__repr__ = self._make_repr()

    def _make_repr(self):
        def __repr__(instance):
            attrs = ", ".join(
                f"{k}={v!r}"
                for k, v in instance.__dict__.items()
            )
            return f"{instance.__class__.__name__}({attrs})"
        return __repr__

    def __call__(self, *args, **kwargs):
        return self.cls(*args, **kwargs)

@AutoRepr
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

p = Person("Alice", 25)
print(p)  # Person(name='Alice', age=25)
```

---

## 3. __call__ 方法

让类的实例可以像函数一样被调用。

```python
class Multiplier:
    def __init__(self, factor):
        self.factor = factor

    def __call__(self, value):
        return value * self.factor

double = Multiplier(2)
triple = Multiplier(3)

print(double(5))   # 10
print(triple(5))   # 15
```

### 实现计数器

```python
class Counter:
    def __init__(self, start=0):
        self.count = start

    def __call__(self, step=1):
        self.count += step
        return self.count

    def reset(self):
        self.count = 0

counter = Counter()
print(counter())     # 1
print(counter())     # 2
print(counter(5))    # 7
counter.reset()
print(counter())     # 1
```

---

## 4. 元类基础

元类是创建类的类。默认的元类是 type。

```python
class Meta(type):
    """自定义元类"""
    def __new__(mcs, name, bases, namespace):
        print(f"创建类: {name}")
        # 可以修改 namespace
        namespace["created_by"] = "Meta"
        return super().__new__(mcs, name, bases, namespace)

class MyClass(metaclass=Meta):
    x = 10

print(MyClass.created_by)  # Meta
```

### 自动注册子类

```python
class PluginMeta(type):
    """自动注册插件的元类"""
    registry = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if name != "Plugin":
            PluginMeta.registry[name] = cls
        return cls

class Plugin(metaclass=PluginMeta):
    pass

class ImagePlugin(Plugin):
    pass

class VideoPlugin(Plugin):
    pass

print(PluginMeta.registry)
# {'ImagePlugin': <class '__main__.ImagePlugin'>, ...}
```

---

## 实战练习

### 练习 1：自动属性验证装饰器

```python
def validated(**validators):
    """类装饰器：自动验证属性"""
    def decorator(cls):
        original_init = cls.__init__

        def new_init(self, **kwargs):
            for field, validator in validators.items():
                if field in kwargs:
                    if not validator(kwargs[field]):
                        raise ValueError(f"{field} 验证失败")
            original_init(self, **kwargs)

        cls.__init__ = new_init
        return cls
    return decorator

@validated(
    age=lambda x: x >= 0,
    email=lambda x: "@" in x
)
class User:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

u = User(name="Alice", age=25, email="alice@example.com")
# User(name="Bob", age=-1)  # ValueError!
```

### 练习 2：可调用缓存类

```python
import functools

class Memoize:
    """可调用缓存"""
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        if args not in self.cache:
            self.cache[args] = self.func(*args)
        return self.cache[args]

    def clear(self):
        self.cache.clear()

@Memoize
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print(fibonacci(100))
print(f"缓存了 {len(fibonacci.cache)} 个结果")
```

---

## 今日总结

- [ ] `__new__` 创建实例，`__init__` 初始化实例
- [ ] 类装饰器可以修改类的行为
- [ ] `__call__` 让实例可调用
- [ ] 元类控制类的创建过程
- [ ] 元类适合实现框架级功能

---

*第 26 天 / 330 天*
