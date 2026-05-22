# 第 25 天：元编程、type() 动态创建类

## 学习目标

- 理解元编程的概念
- 掌握 type() 动态创建类
- 了解 exec 和 eval
- 学会使用 inspect 模块

---

## 1. 什么是元编程

元编程是编写能够操作代码的代码。Python 中一切皆对象，包括类本身。

```python
class MyClass:
    pass

# 类也是对象
print(type(MyClass))  # <class 'type'>
print(type(int))      # <class 'type'>
print(type(str))      # <class 'type'>
```

---

## 2. type() 动态创建类

### type(name, bases, namespace)

```python
# 普通方式
class Person:
    def __init__(self, name):
        self.name = name

    def greet(self):
        return f"Hello, I'm {self.name}"

# 用 type 动态创建（等价）
Person = type("Person", (), {
    "__init__": lambda self, name: setattr(self, "name", name),
    "greet": lambda self: f"Hello, I'm {self.name}"
})

p = Person("Alice")
print(p.greet())  # Hello, I'm Alice
```

### 带继承

```python
def say_hello(self):
    return f"Hello from {self.name}"

# 创建 Animal 类
Animal = type("Animal", (), {
    "__init__": lambda self, name: setattr(self, "name", name)
})

# 创建 Dog 类继承 Animal
Dog = type("Dog", (Animal,), {
    "bark": lambda self: "Woof!",
    "say_hello": say_hello
})

dog = Dog("Buddy")
print(dog.name)       # Buddy
print(dog.bark())     # Woof!
print(dog.say_hello())  # Hello from Buddy
```

### 带类属性

```python
MyClass = type("MyClass", (), {
    "x": 10,
    "y": 20,
    "sum": classmethod(lambda cls: cls.x + cls.y)
})

print(MyClass.x)       # 10
print(MyClass.sum())   # 30
```

---

## 3. 动态添加方法

```python
class Person:
    def __init__(self, name):
        self.name = name

def greet(self):
    return f"Hello, I'm {self.name}"

def farewell(self):
    return f"Goodbye from {self.name}"

# 动态添加方法到类
Person.greet = greet
Person.farewell = farewell

p = Person("Alice")
print(p.greet())     # Hello, I'm Alice
print(p.farewell())  # Goodbye from Alice
```

---

## 4. exec 和 eval

### eval：执行表达式

```python
x = 10
result = eval("x + 5")  # 15

# 带环境
code = "a + b"
result = eval(code, {"a": 1, "b": 2})  # 3
```

### exec：执行语句

```python
code = """
def hello(name):
    return f"Hello, {name}"

result = hello("World")
"""

namespace = {}
exec(code, namespace)
print(namespace["result"])  # Hello, World
```

⚠️ **安全警告**：不要执行不受信任的代码！

---

## 5. inspect 模块

```python
import inspect

def example(a, b=10, *args, c=20, **kwargs):
    pass

# 获取参数信息
sig = inspect.signature(example)
for name, param in sig.parameters.items():
    print(f"{name}: {param.kind.name}, default={param.default}")

# 获取源码
print(inspect.getsource(example))

# 获取类层次
class A: pass
class B(A): pass
print(inspect.getmro(B))  # (<class 'B'>, <class 'A'>, <class 'object'>)
```

---

## 实战练习

### 练习 1：ORM 风格的类生成器

```python
def create_model(name, **fields):
    """动态创建数据模型类"""
    def __init__(self, **kwargs):
        for field_name, field_type in fields.items():
            value = kwargs.get(field_name)
            if value is not None and not isinstance(value, field_type):
                raise TypeError(f"{field_name} 必须是 {field_type}")
            setattr(self, field_name, value)

    def __repr__(self):
        attrs = ", ".join(f"{k}={getattr(self, k)!r}" for k in fields)
        return f"{name}({attrs})"

    def to_dict(self):
        return {k: getattr(self, k) for k in fields}

    return type(name, (), {
        "__init__": __init__,
        "__repr__": __repr__,
        "to_dict": to_dict,
        "_fields": fields,
    })

# 使用
User = create_model("User", name=str, age=int, email=str)

user = User(name="Alice", age=25, email="alice@example.com")
print(user)
print(user.to_dict())
```

### 练习 2：JSON 到类

```python
import json

def json_to_class(name, json_data):
    """从 JSON 数据动态创建类"""
    data = json.loads(json_data) if isinstance(json_data, str) else json_data

    def __init__(self, **kwargs):
        for key in data:
            setattr(self, key, kwargs.get(key, data[key]))

    def __repr__(self):
        attrs = ", ".join(f"{k}={getattr(self, k)!r}" for k in data)
        return f"{name}({attrs})"

    return type(name, (), {
        "__init__": __init__,
        "__repr__": __repr__,
    })

# 使用
json_data = '{"x": 10, "y": 20, "color": "red"}'
Point = json_to_class("Point", json_data)

p = Point(x=5, y=10)
print(p)  # Point(x=5, y=10, color='red')
```

---

## 今日总结

- [ ] `type(name, bases, namespace)` 动态创建类
- [ ] 类创建后可以动态添加方法和属性
- [ ] `eval` 执行表达式，`exec` 执行语句
- [ ] `inspect` 模块用于内省代码
- [ ] 元编程用于框架和库的开发

---

*第 25 天 / 330 天*
