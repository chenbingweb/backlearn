# 第 31 天：pytest 基础、安装与配置

## 学习目标

- 理解测试的重要性
- 掌握 pytest 的安装和基本用法
- 学会编写第一个测试
- 了解 pytest 的目录规范

---

## 1. 为什么需要测试

### 没有测试的问题

```python
def add(a, b):
    return a + b

# 手动测试
print(add(1, 2))  # 3
print(add(-1, 1)) # 0
# ... 每次改代码都要手动跑一遍？
```

### 自动化测试的好处

- **回归保护**：改代码后自动验证没破坏原有功能
- **文档作用**：测试用例展示代码的使用方式
- **设计驱动**：写测试迫使你思考接口设计
- **重构信心**：有测试才敢大胆重构

---

## 2. 安装 pytest

```bash
# 用 pip
pip install pytest

# 或用 poetry
poetry add pytest --group dev

# 验证安装
pytest --version
```

---

## 3. 第一个测试

### 测试文件命名规则

- 测试文件：`test_*.py` 或 `*_test.py`
- 测试函数：`test_` 前缀
- 测试类：`Test` 前缀（不需要继承任何东西）

### 基本示例

```python
# test_math.py
def test_addition():
    assert 1 + 1 == 2

def test_subtraction():
    assert 5 - 3 == 2
```

运行：

```bash
pytest test_math.py
```

输出：

```
test_math.py::test_addition PASSED
test_math.py::test_subtraction PASSED
```

---

## 4. 测试自己的代码

```python
# calculator.py
def add(a, b):
    return a + b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

```python
# test_calculator.py
from calculator import add, divide

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_divide():
    assert divide(10, 2) == 5.0
    assert divide(7, 2) == 3.5

def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)
```

---

## 5. pytest 常用命令

```bash
# 运行当前目录所有测试
pytest

# 运行指定文件
pytest test_calculator.py

# 运行指定函数
pytest test_calculator.py::test_add

# 运行匹配名称的测试
pytest -k "add"           # 名称包含 add
pytest -k "not slow"      # 排除 slow

# 详细输出
pytest -v                 # verbose
pytest -vv                # 更详细

# 遇到第一个失败就停止
pytest -x

# 失败时进入 PDB
pytest --pdb

# 只运行上次失败的
pytest --lf

# 生成覆盖率报告
pytest --cov=calculator --cov-report=html
```

---

## 6. 项目测试目录结构

```
my_project/
├── src/
│   └── my_project/
│       ├── __init__.py
│       └── calculator.py
├── tests/
│   ├── __init__.py
│   ├── test_calculator.py
│   └── test_utils.py
├── pyproject.toml
└── README.md
```

### pyproject.toml 配置

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
```

---

## 实战练习

### 练习 1：测试字符串工具函数

```python
# string_utils.py
def reverse(s):
    return s[::-1]

def is_palindrome(s):
    s = s.lower().replace(" ", "")
    return s == s[::-1]

def count_words(s):
    return len(s.split())
```

```python
# test_string_utils.py
from string_utils import reverse, is_palindrome, count_words

def test_reverse():
    assert reverse("hello") == "olleh"
    assert reverse("") == ""
    assert reverse("a") == "a"

def test_is_palindrome():
    assert is_palindrome("racecar") is True
    assert is_palindrome("hello") is False
    assert is_palindrome("A man a plan a canal Panama") is True

def test_count_words():
    assert count_words("hello world") == 2
    assert count_words("") == 0
    assert count_words("one") == 1
```

### 练习 2：测试类

```python
# bank.py
class BankAccount:
    def __init__(self, balance=0):
        self.balance = balance

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self.balance += amount

    def withdraw(self, amount):
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
```

```python
# test_bank.py
from bank import BankAccount

def test_initial_balance():
    account = BankAccount(100)
    assert account.balance == 100

def test_deposit():
    account = BankAccount()
    account.deposit(50)
    assert account.balance == 50

def test_deposit_negative():
    account = BankAccount()
    with pytest.raises(ValueError):
        account.deposit(-10)

def test_withdraw():
    account = BankAccount(100)
    account.withdraw(30)
    assert account.balance == 70

def test_withdraw_too_much():
    account = BankAccount(10)
    with pytest.raises(ValueError):
        account.withdraw(100)
```

---

## 今日总结

- [ ] 测试自动化验证代码正确性
- [ ] pytest 通过 `test_` 前缀自动发现测试
- [ ] `assert` 进行断言，`pytest.raises` 测试异常
- [ ] 测试目录放在 `tests/` 下
- [ ] `pytest -v` 详细输出，`-k` 过滤测试

---

*第 31 天 / 330 天*
