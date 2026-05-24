# 第 33 天：pytest fixtures、conftest.py

## 学习目标

- 理解 fixture 的概念
- 掌握 fixture 的生命周期
- 学会使用 conftest.py 共享 fixtures
- 了解 fixture 的作用域和自动使用

---

## 1. 什么是 Fixture

Fixture 是为测试提供**预设环境**（数据、对象、资源）的机制。

### 没有 fixture 的问题

```python
def test_user_can_login():
    db = Database()           # 重复代码
    db.connect()
    user = User("Alice", db)   # 重复代码
    assert user.login("password")

def test_user_can_logout():
    db = Database()           # 重复代码
    db.connect()
    user = User("Alice", db)   # 重复代码
    assert user.logout()
```

### 使用 fixture

```python
import pytest

@pytest.fixture
def user():
    db = Database()
    db.connect()
    return User("Alice", db)

def test_user_can_login(user):   # 自动注入 fixture
    assert user.login("password")

def test_user_can_logout(user):  # 每次测试都获得新的 user
    assert user.logout()
```

---

## 2. Fixture 基础

### 创建和使用

```python
import pytest

@pytest.fixture
def sample_list():
    return [1, 2, 3, 4, 5]

def test_length(sample_list):
    assert len(sample_list) == 5

def test_sum(sample_list):
    assert sum(sample_list) == 15
```

### 带清理逻辑的 fixture

```python
@pytest.fixture
def temp_file():
    # setup: 测试前执行
    f = open("test.txt", "w")
    f.write("test data")
    f.close()

    yield "test.txt"   # 返回值给测试函数

    # teardown: 测试后执行
    import os
    os.remove("test.txt")

def test_file_exists(temp_file):
    assert os.path.exists(temp_file)
# 测试结束后，temp_file 自动删除
```

---

## 3. Fixture 作用域

| 作用域 | 执行频率 | 用途 |
|--------|---------|------|
| `function`（默认） | 每个测试函数 | 大多数情况 |
| `class` | 每个测试类 | 类级别资源 |
| `module` | 每个模块 | 模块级别资源 |
| `package` | 每个包 | 包级别资源 |
| `session` | 整个测试会话 | 数据库连接等 |

```python
@pytest.fixture(scope="module")
def database():
    db = Database()
    db.connect()
    yield db
    db.disconnect()

@pytest.fixture(scope="function")
def user(database):
    # 每个测试函数都新建用户
    # 但共享同一个数据库连接
    return User("Alice", database)
```

---

## 4. conftest.py

`conftest.py` 是 pytest 的共享配置文件，放在测试目录中，该目录及子目录的测试都能使用其中的 fixtures。

```
tests/
├── conftest.py          # 根级别 fixtures
├── unit/
│   ├── conftest.py      # unit 级别 fixtures
│   └── test_*.py
└── integration/
    └── test_*.py
```

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session")
def db_connection():
    """全局数据库连接"""
    conn = create_connection()
    yield conn
    conn.close()

@pytest.fixture
def clean_db(db_connection):
    """每个测试前清空数据"""
    db_connection.execute("DELETE FROM users")
    db_connection.commit()
    return db_connection
```

```python
# tests/unit/test_user.py
# 自动使用 conftest.py 中的 fixtures

def test_create_user(clean_db):
    # clean_db 来自 conftest.py
    user = create_user("Alice", db=clean_db)
    assert user.name == "Alice"
```

---

## 5. Fixture 高级用法

### 参数化 Fixture

```python
@pytest.fixture(params=["sqlite", "postgres"])
def database(request):
    """用不同数据库运行同一组测试"""
    if request.param == "sqlite":
        db = SQLiteDB()
    else:
        db = PostgresDB()
    yield db
    db.cleanup()

# 这个测试会运行两次：一次 sqlite，一次 postgres
def test_query(database):
    result = database.query("SELECT 1")
    assert result == 1
```

### 自动使用的 Fixture

```python
@pytest.fixture(autouse=True)
def setup_teardown():
    """每个测试自动执行，无需显式传入"""
    print("测试开始")
    yield
    print("测试结束")

def test_something():  # 不需要传入 setup_teardown
    assert True
```

### Fixture 工厂模式

```python
@pytest.fixture
def make_user():
    """返回一个工厂函数"""
    users = []

    def _make_user(name):
        user = User(name)
        users.append(user)
        return user

    yield _make_user

    # 清理所有创建的用户
    for user in users:
        user.delete()

def test_multiple_users(make_user):
    user1 = make_user("Alice")
    user2 = make_user("Bob")
    assert len([user1, user2]) == 2
```

---

## 6. 内置 Fixtures

```python
def test_example(tmp_path, capsys, monkeypatch):
    # tmp_path: 临时目录 Path 对象
    file = tmp_path / "test.txt"
    file.write_text("hello")
    assert file.read_text() == "hello"

    # capsys: 捕获输出
    print("hello world")
    captured = capsys.readouterr()
    assert captured.out == "hello world\n"

    # monkeypatch: 临时修改环境
    monkeypatch.setenv("API_KEY", "test-key")
    assert os.environ["API_KEY"] == "test-key"
```

| Fixture | 用途 |
|---------|------|
| `tmp_path` | 临时目录 |
| `tmp_path_factory` | 创建临时目录 |
| `capsys` | 捕获 stdout/stderr |
| `caplog` | 捕获日志 |
| `monkeypatch` | 临时修改对象/环境 |
| `request` | 访问测试上下文 |

---

## 实战练习

### 练习：测试 API 客户端

```python
# conftest.py
import pytest

class MockAPI:
    """模拟 API 服务"""
    def __init__(self):
        self.users = {}
        self._id = 1

    def create_user(self, name):
        user = {"id": self._id, "name": name}
        self.users[self._id] = user
        self._id += 1
        return user

    def get_user(self, user_id):
        return self.users.get(user_id)

    def delete_user(self, user_id):
        return self.users.pop(user_id, None)

@pytest.fixture
def api():
    """每个测试提供干净的 API 实例"""
    return MockAPI()

@pytest.fixture
def sample_user(api):
    """创建一个示例用户"""
    return api.create_user("Alice")
```

```python
# test_api.py
def test_create_user(api):
    user = api.create_user("Bob")
    assert user["name"] == "Bob"
    assert user["id"] == 1

def test_get_user(api, sample_user):
    found = api.get_user(sample_user["id"])
    assert found["name"] == "Alice"

def test_delete_user(api, sample_user):
    deleted = api.delete_user(sample_user["id"])
    assert deleted is not None
    assert api.get_user(sample_user["id"]) is None
```

---

## 今日总结

- [ ] Fixture 提供测试所需的预设环境
- [ ] `yield` 前是 setup，后是 teardown
- [ ] `scope` 控制 fixture 的执行频率
- [ ] `conftest.py` 共享 fixtures 给同级和子目录
- [ ] `@pytest.fixture(autouse=True)` 自动使用
- [ ] `tmp_path`、`capsys`、`monkeypatch` 等内置 fixtures 很有用

---

*第 33 天 / 330 天*
