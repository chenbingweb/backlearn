# 第 8 天：类定义、self、__init__

## 学习目标

- 理解面向对象编程的核心概念
- 掌握 Python 类的定义方式
- 理解 self 的作用
- 掌握 __init__ 初始化方法

---

## 1. 面向对象基础

### 什么是面向对象

面向对象编程（OOP）是一种编程范式，将数据和操作数据的方法封装在一起。

核心概念：
- **类（Class）**：对象的蓝图/模板
- **对象（Object）**：类的实例
- **属性（Attribute）**：对象的数据
- **方法（Method）**：对象的行为

### 生活中的类比

```
类（Class）   →  汽车设计图
对象（Object） →  一辆具体的汽车
属性           →  颜色、品牌、价格
方法           →  启动、加速、刹车
```

---

## 2. 定义类

### 基本语法

```python
class Dog:
    """狗的类"""
    pass

# 创建实例
my_dog = Dog()
print(type(my_dog))  # <class '__main__.Dog'>
```

### 添加方法

```python
class Dog:
    """狗的类"""

    def bark(self):
        """叫"""
        print("汪汪！")

    def run(self):
        """跑"""
        print("狗在跑")

# 创建实例并调用方法
my_dog = Dog()
my_dog.bark()   # 汪汪！
my_dog.run()    # 狗在跑
```

---

## 3. self 详解

### 什么是 self

`self` 代表类的实例本身，是方法的第一个参数（必须显式写出）。

```python
class Person:
    def say_hello(self):
        print(f"self 的 id: {id(self)}")
        print("Hello!")

p = Person()
print(f"p 的 id: {id(p)}")
p.say_hello()

# 输出：
# p 的 id: 140234567890
# self 的 id: 140234567890  ← 相同！
```

### self 的本质

```python
class Person:
    def greet(self, name):
        print(f"Hello, {name}!")

p = Person()

# 两种方式等价
p.greet("Alice")        # 常规调用
Person.greet(p, "Bob")  # 通过类调用，手动传 self
```

### 忘记写 self 的错误

```python
class Wrong:
    def method():           # 错误！缺少 self
        print(" wrong")

w = Wrong()
w.method()  # TypeError: method() takes 0 positional arguments but 1 was given
```

---

## 4. __init__ 初始化方法

### 基本用法

```python
class Dog:
    def __init__(self, name, age):
        """初始化方法，创建实例时自动调用"""
        self.name = name
        self.age = age

# 创建实例时传参
my_dog = Dog("Buddy", 3)
print(my_dog.name)  # Buddy
print(my_dog.age)   # 3
```

### 带默认参数的 __init__

```python
class Cat:
    def __init__(self, name, age=1, color="白色"):
        self.name = name
        self.age = age
        self.color = color

# 多种创建方式
cat1 = Cat("咪咪")
cat2 = Cat("花花", 2)
cat3 = Cat("黑黑", 3, "黑色")

print(f"{cat1.name}, {cat1.age}岁, {cat1.color}")  # 咪咪, 1岁, 白色
```

### __init__ 不是必须的

```python
class Simple:
    """没有 __init__ 也可以"""
    def show(self):
        print("简单类")

s = Simple()
s.show()
```

---

## 5. 实例属性

### 在 __init__ 中定义

```python
class Student:
    def __init__(self, name, score):
        self.name = name      # 实例属性
        self.score = score    # 实例属性

    def show_info(self):
        print(f"{self.name}: {self.score}分")

s1 = Student("Alice", 90)
s2 = Student("Bob", 85)

s1.show_info()  # Alice: 90分
s2.show_info()  # Bob: 85分
```

### 动态添加属性

```python
class Person:
    def __init__(self, name):
        self.name = name

p = Person("Alice")
p.age = 25        # 动态添加属性
p.city = "北京"    # 动态添加属性

print(p.age)   # 25
print(p.city)  # 北京
```

### 动态删除属性

```python
del p.age
# print(p.age)  # AttributeError
```

---

## 6. 实例方法

```python
class Calculator:
    def __init__(self, value=0):
        self.value = value

    def add(self, n):
        self.value += n
        return self

    def subtract(self, n):
        self.value -= n
        return self

    def get_result(self):
        return self.value

# 链式调用
calc = Calculator()
result = calc.add(10).subtract(3).add(5).get_result()
print(result)  # 12
```

---

## 7. 类文档字符串

```python
class BankAccount:
    """
    银行账户类

    Attributes:
        owner (str): 账户持有人
        balance (float): 账户余额

    Methods:
        deposit(amount): 存款
        withdraw(amount): 取款
    """

    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount):
        """存款"""
        if amount > 0:
            self.balance += amount
        return self.balance

    def withdraw(self, amount):
        """取款"""
        if 0 < amount <= self.balance:
            self.balance -= amount
            return amount
        return 0

# 查看文档
print(BankAccount.__doc__)
print(BankAccount.deposit.__doc__)
```

---

## 8. 类与实例的关系

```python
class Person:
    def __init__(self, name):
        self.name = name

# 每个实例独立
p1 = Person("Alice")
p2 = Person("Bob")

p1.name = "Alice2"
print(p1.name)  # Alice2
print(p2.name)  # Bob（不受影响）
```

---

## 实战练习

### 练习 1：图书类

```python
class Book:
    def __init__(self, title, author, price):
        self.title = title
        self.author = author
        self.price = price

    def get_info(self):
        return f"《{self.title}》作者：{self.author}，价格：¥{self.price}"

    def discount(self, percent):
        """打折，percent 是折扣百分比（如 20 表示八折）"""
        self.price *= (1 - percent / 100)
        return self

book = Book("Python编程", "张三", 100)
print(book.get_info())
book.discount(20)
print(f"打折后：¥{book.price:.2f}")
```

### 练习 2：用户类

```python
class User:
    def __init__(self, username, password):
        self.username = username
        self._password = password  # 约定：私有属性
        self.is_logged_in = False

    def login(self, password):
        if password == self._password:
            self.is_logged_in = True
            return True
        return False

    def logout(self):
        self.is_logged_in = False

    def show_status(self):
        status = "已登录" if self.is_logged_in else "未登录"
        print(f"{self.username}: {status}")

# 使用
user = User("alice", "123456")
user.show_status()           # alice: 未登录
user.login("wrong")          # 失败
user.show_status()           # alice: 未登录
user.login("123456")         # 成功
user.show_status()           # alice: 已登录
user.logout()
user.show_status()           # alice: 未登录
```

### 练习 3：温度转换器类

```python
class Temperature:
    def __init__(self, celsius=0):
        self.celsius = celsius

    @property
    def fahrenheit(self):
        return self.celsius * 9 / 5 + 32

    @fahrenheit.setter
    def fahrenheit(self, value):
        self.celsius = (value - 32) * 5 / 9

    @property
    def kelvin(self):
        return self.celsius + 273.15

    def __str__(self):
        return f"{self.celsius}°C = {self.fahrenheit:.2f}°F = {self.kelvin:.2f}K"

# 使用
temp = Temperature(25)
print(temp)
# 25°C = 77.00°F = 298.15K

temp.fahrenheit = 100
print(temp)
# 37.78°C = 100.00°F = 310.93K
```

---

## 今日总结

- [ ] 类是对象的模板，使用 `class` 关键字定义
- [ ] `self` 代表实例本身，必须作为第一个参数
- [ ] `__init__` 是初始化方法，创建实例时自动调用
- [ ] 实例属性在每个实例中独立存在
- [ ] 可以动态添加和删除实例属性

---

*第 8 天 / 330 天*
