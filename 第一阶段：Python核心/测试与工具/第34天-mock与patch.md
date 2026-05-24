# 第 34 天：mock 与 patch

## 学习目标

- 理解为什么需要 mock
- 掌握 unittest.mock 的基本用法
- 学会使用 pytest-mock
- 了解 patch 的各种模式

---

## 1. 为什么需要 Mock

### 问题场景

```python
import requests

def get_weather(city):
    """获取天气"""
    response = requests.get(f"https://api.weather.com/{city}")
    return response.json()

def test_get_weather():
    # 问题1: 测试依赖外部 API，网络不稳定会失败
    # 问题2: 测试速度慢
    # 问题3: 无法控制返回数据
    result = get_weather("Beijing")
    assert "temperature" in result
```

### Mock 解决什么

- **隔离测试**：不依赖外部服务
- **控制返回值**：测试各种边界情况
- **提高速度**：避免真实网络/数据库操作
- **验证行为**：确认代码调用了预期的依赖

---

## 2. unittest.mock 基础

### Mock 对象

```python
from unittest.mock import Mock

# 创建一个 mock
mock = Mock()

# 调用任何方法/属性都返回新的 Mock
print(mock.some_method())        # <Mock name='mock.some_method()' id='...'>
print(mock.any_attribute)        # <Mock name='mock.any_attribute' id='...'>

# 设置返回值
mock.get.return_value = {"temperature": 25}
print(mock.get())                # {"temperature": 25}

# 设置 side_effect（每次调用返回不同值）
mock.rand.side_effect = [1, 2, 3]
print(mock.rand())  # 1
print(mock.rand())  # 2
print(mock.rand())  # 3
```

### 验证调用

```python
from unittest.mock import Mock

mock = Mock()

# 执行操作
mock.do_something("arg1", key="value")

# 验证被调用过
mock.do_something.assert_called()

# 验证调用参数
mock.do_something.assert_called_with("arg1", key="value")

# 验证调用次数
mock.do_something.assert_called_once()

# 查看所有调用记录
print(mock.do_something.call_count)      # 1
print(mock.do_something.call_args)       # call('arg1', key='value')
print(mock.method_calls)                 # [call.do_something('arg1', key='value')]
```

---

## 3. patch 装饰器

### 基本用法

```python
from unittest.mock import patch
import requests

def get_user(user_id):
    response = requests.get(f"https://api.example.com/users/{user_id}")
    return response.json()

# 方式1: 装饰器
@patch("requests.get")
def test_get_user(mock_get):
    mock_get.return_value.json.return_value = {"name": "Alice"}

    result = get_user(123)

    assert result["name"] == "Alice"
    mock_get.assert_called_with("https://api.example.com/users/123")

# 方式2: 上下文管理器
def test_get_user_with_context():
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"name": "Bob"}

        result = get_user(456)

        assert result["name"] == "Bob"
```

### patch 多个对象

```python
@patch("module.send_email")
@patch("module.log_activity")
def test_user_registration(mock_log, mock_email):
    """注意: 装饰器顺序是从下往上"""
    register_user("alice@example.com")

    mock_email.assert_called_once()
    mock_log.assert_called_once()
```

### patch.object

```python
from unittest.mock import patch

class Database:
    def query(self, sql):
        pass

# 只 patch 某个对象的方法
@patch.object(Database, "query")
def test_database(mock_query):
    mock_query.return_value = [(1, "Alice")]

    db = Database()
    result = db.query("SELECT * FROM users")

    assert result[0][1] == "Alice"
```

---

## 4. pytest-mock

### 安装

```bash
pip install pytest-mock
```

### mocker fixture

```python
def test_with_mocker(mocker):
    """pytest-mock 提供 mocker fixture"""

    # patch
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.json.return_value = {"temp": 25}

    result = get_weather("Beijing")
    assert result["temp"] == 25

def test_spy(mocker):
    """间谍模式：包装真实对象，记录调用"""

    class Calculator:
        def add(self, a, b):
            return a + b

    calc = Calculator()

    # 包装方法，但仍执行真实逻辑
    spy = mocker.spy(calc, "add")

    result = calc.add(2, 3)

    assert result == 5
    spy.assert_called_once_with(2, 3)

def test_stub(mocker):
    """stub: 完全替换对象"""

    mock_db = mocker.Mock()
    mock_db.get_user.return_value = {"id": 1, "name": "Alice"}

    service = UserService(mock_db)
    user = service.get_user(1)

    assert user["name"] == "Alice"
```

---

## 5. Mock 最佳实践

### 不要过度 mock

```python
# 不好的做法：mock 自己的代码
@patch("my_module.UserValidator")
def test_user_creation(mock_validator):
    # 测试自己的代码却 mock 了自己的代码...
    pass

# 好的做法：mock 外部依赖
@patch("requests.post")
def test_api_call(mock_post):
    # mock 外部 HTTP 调用
    pass
```

### 使用 spec 限制 Mock

```python
from unittest.mock import Mock

class Calculator:
    def add(self, a, b):
        pass

    def subtract(self, a, b):
        pass

# 只允许 Calculator 的方法
mock_calc = Mock(spec=Calculator)
mock_calc.add(1, 2)       # OK
mock_calc.multiply(2, 3)  # AttributeError!
```

### Mock 异常

```python
mock = Mock()

# 模拟异常
mock.risky_operation.side_effect = ConnectionError("Network down")

with pytest.raises(ConnectionError):
    mock.risky_operation()
```

---

## 实战练习

### 练习：测试发送邮件功能

```python
# email_service.py
import smtplib
from email.mime.text import MIMEText

def send_welcome_email(to_address, name):
    """发送欢迎邮件"""
    msg = MIMEText(f"欢迎, {name}!")
    msg["Subject"] = "欢迎注册"
    msg["From"] = "noreply@example.com"
    msg["To"] = to_address

    with smtplib.SMTP("smtp.example.com") as server:
        server.send_message(msg)

    return True
```

```python
# test_email_service.py
from unittest.mock import patch, Mock
import pytest
from email_service import send_welcome_email

@patch("smtplib.SMTP")
def test_send_welcome_email(mock_smtp_class):
    # 设置 mock
    mock_server = Mock()
    mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_server)
    mock_smtp_class.return_value.__exit__ = Mock(return_value=False)

    # 调用
    result = send_welcome_email("alice@example.com", "Alice")

    # 验证
    assert result is True
    mock_smtp_class.assert_called_once_with("smtp.example.com")
    mock_server.send_message.assert_called_once()

    # 验证邮件内容
    call_args = mock_server.send_message.call_args[0][0]
    assert call_args["To"] == "alice@example.com"
    assert "Alice" in call_args.get_payload()
```

---

## 今日总结

- [ ] Mock 隔离测试，不依赖外部服务
- [ ] `Mock()` 创建模拟对象，`return_value` 设置返回值
- [ ] `assert_called_with` 验证调用参数
- [ ] `@patch("module.function")` 替换模块函数
- [ ] `mocker.patch` 是 pytest 的便捷方式
- [ ] 只 mock 外部依赖，不要 mock 自己的核心业务逻辑

---

*第 34 天 / 330 天*
