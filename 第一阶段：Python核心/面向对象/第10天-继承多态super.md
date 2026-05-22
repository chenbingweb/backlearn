# 第 10 天：继承、多态、super()

## 学习目标

- 掌握类的继承机制
- 理解方法重写
- 学会使用 super()
- 理解多态的概念和应用

---

## 1. 继承基础

### 什么是继承

继承允许一个类（子类）获得另一个类（父类）的属性和方法。

```python
class Animal:           # 父类/基类
    def __init__(self, name):
        self.name = name

    def speak(self):
        raise NotImplementedError("子类必须实现此方法")

    def move(self):
        print(f"{self.name} 在移动")

class Dog(Animal):      # 子类/派生类
    def speak(self):
        print(f"{self.name}: 汪汪！")

class Cat(Animal):      # 子类/派生类
    def speak(self):
        print(f"{self.name}: 喵喵！")

dog = Dog("Buddy")
cat = Cat("Kitty")

dog.speak()   # Buddy: 汪汪！
cat.speak()   # Kitty: 喵喵！
dog.move()    # Buddy 在移动
```

### 继承的语法

```python
class Parent:
    pass

class Child(Parent):    # 单继承
    pass

class GrandChild(Child):  # 多级继承
    pass
```

---

## 2. super() 函数

### 调用父类方法

```python
class Animal:
    def __init__(self, name, age):
        self.name = name
        self.age = age
        print(f"Animal.__init__ 被调用")

    def introduce(self):
        print(f"我是 {self.name}，{self.age} 岁")

class Dog(Animal):
    def __init__(self, name, age, breed):
        super().__init__(name, age)  # 调用父类 __init__
        self.breed = breed            # 子类自己的属性
        print(f"Dog.__init__ 被调用")

    def introduce(self):
        super().introduce()           # 调用父类方法
        print(f"品种: {self.breed}")   # 添加新内容

dog = Dog("Buddy", 3, "金毛")
dog.introduce()
# 我是 Buddy，3 岁
# 品种: 金毛
```

### 为什么要用 super()

```python
# 不用 super() 的问题
class A:
    def __init__(self):
        print("A")

class B(A):
    def __init__(self):
        A.__init__(self)   # 硬编码父类名
        print("B")

# 使用 super() 更灵活
class C(A):
    def __init__(self):
        super().__init__()  # 自动找到正确的父类
        print("C")
```

### MRO（方法解析顺序）

```python
class A:
    def method(self):
        print("A")

class B(A):
    def method(self):
        print("B")

class C(A):
    def method(self):
        print("C")

class D(B, C):  # 多重继承
    pass

d = D()
d.method()  # B（按 MRO 顺序）

# 查看 MRO
print(D.__mro__)
# (<class 'D'>, <class 'B'>, <class 'C'>, <class 'A'>, <class 'object'>)
```

---

## 3. 方法重写

### 完全重写

```python
class Parent:
    def show(self):
        print("Parent")

class Child(Parent):
    def show(self):
        print("Child")  # 完全重写

c = Child()
c.show()  # Child
```

### 扩展父类方法

```python
class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

    def __str__(self):
        return f"Rectangle({self.width}x{self.height})"

class Square(Rectangle):
    def __init__(self, side):
        super().__init__(side, side)

    def __str__(self):
        return f"Square({self.width})"

sq = Square(5)
print(sq)         # Square(5)
print(sq.area())  # 25
```

---

## 4. 多态

### 多态的概念

多态是指不同类的对象对同一消息做出不同的响应。

```python
class Animal:
    def speak(self):
        raise NotImplementedError

class Dog(Animal):
    def speak(self):
        return "汪汪"

class Cat(Animal):
    def speak(self):
        return "喵喵"

class Duck(Animal):
    def speak(self):
        return "嘎嘎"

# 多态：同一个接口，不同表现
def animal_speak(animal: Animal):
    print(animal.speak())

animals = [Dog(), Cat(), Duck()]
for animal in animals:
    animal_speak(animal)
# 汪汪
# 喵喵
# 嘎嘎
```

### 鸭子类型

Python 是动态类型语言，不强制要求继承同一个父类。

```python
class Dog:
    def speak(self):
        return "汪汪"

class Cat:
    def speak(self):
        return "喵喵"

class Person:
    def speak(self):
        return "你好"

# 只要有 speak 方法就可以
for obj in [Dog(), Cat(), Person()]:
    print(obj.speak())
```

---

## 5. 抽象基类

### abc 模块

```python
from abc import ABC, abstractmethod

class Animal(ABC):
    @abstractmethod
    def speak(self):
        pass

    @abstractmethod
    def move(self):
        pass

class Dog(Animal):
    def speak(self):
        print("汪汪")

    def move(self):
        print("狗在跑")

# animal = Animal()  # TypeError!
dog = Dog()
dog.speak()
```

---

## 6. isinstance 和 issubclass

```python
class Animal:
    pass

class Dog(Animal):
    pass

dog = Dog()

print(isinstance(dog, Dog))      # True
print(isinstance(dog, Animal))   # True
print(isinstance(dog, object))   # True

print(issubclass(Dog, Animal))   # True
print(issubclass(Dog, object))   # True
```

---

## 实战练习

### 练习 1：员工管理系统

```python
from abc import ABC, abstractmethod

class Employee(ABC):
    def __init__(self, name, base_salary):
        self.name = name
        self.base_salary = base_salary

    @abstractmethod
    def calculate_salary(self):
        pass

    def __str__(self):
        return f"{self.name}: ¥{self.calculate_salary()}"

class SalariedEmployee(Employee):
    """固定薪资员工"""
    def calculate_salary(self):
        return self.base_salary

class HourlyEmployee(Employee):
    """时薪员工"""
    def __init__(self, name, hourly_rate, hours_worked):
        super().__init__(name, 0)
        self.hourly_rate = hourly_rate
        self.hours_worked = hours_worked

    def calculate_salary(self):
        return self.hourly_rate * self.hours_worked

class CommissionEmployee(Employee):
    """提成员工"""
    def __init__(self, name, base_salary, sales, commission_rate):
        super().__init__(name, base_salary)
        self.sales = sales
        self.commission_rate = commission_rate

    def calculate_salary(self):
        return self.base_salary + self.sales * self.commission_rate

# 使用
employees = [
    SalariedEmployee("Alice", 10000),
    HourlyEmployee("Bob", 100, 160),
    CommissionEmployee("Charlie", 5000, 100000, 0.05)
]

for emp in employees:
    print(emp)
```

### 练习 2：图形类层次

```python
import math
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        pass

    @abstractmethod
    def perimeter(self):
        pass

class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

    def perimeter(self):
        return 2 * (self.width + self.height)

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return math.pi * self.radius ** 2

    def perimeter(self):
        return 2 * math.pi * self.radius

class Triangle(Shape):
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def area(self):
        s = self.perimeter() / 2
        return math.sqrt(s * (s - self.a) * (s - self.b) * (s - self.c))

    def perimeter(self):
        return self.a + self.b + self.c

# 使用
shapes = [
    Rectangle(5, 3),
    Circle(5),
    Triangle(3, 4, 5)
]

for shape in shapes:
    print(f"{type(shape).__name__}: 面积={shape.area():.2f}, 周长={shape.perimeter():.2f}")
```

---

## 今日总结

- [ ] 继承使用 `class Child(Parent)` 语法
- [ ] `super()` 调用父类方法，支持多重继承
- [ ] 方法重写时可以先调用 `super().method()` 再扩展
- [ ] 多态：不同对象对同一消息有不同响应
- [ ] 抽象基类用 `@abstractmethod` 强制子类实现
- [ ] Python 支持鸭子类型

---

*第 10 天 / 330 天*
