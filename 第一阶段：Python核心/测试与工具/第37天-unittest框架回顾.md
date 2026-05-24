# 第 37 天：unittest 框架回顾

## 学习目标

- 了解 unittest 框架的基本用法
- 对比 unittest 和 pytest
- 学会在项目中混合使用两者
- 掌握 unittest.mock 的高级用法

---

## 1. unittest 基础

unittest 是 Python 标准库自带的测试框架。

### 基本测试类

```python
import unittest

class TestMath(unittest.TestCase):
    """测试数学运算"""

    def test_addition(self):
        self.assertEqual(1 + 1, 2)

    def test_subtraction(self):
        self.assertEqual(5 - 3, 2)

    def test_multiplication(self):
        self.assertEqual(2 * 3, 6)

# 运行测试
if __name__ == "__main__":
    unittest.main()
```

运行：

```bash
python test_math.py
# 或
python -m unittest test_math
```

---

## 2. unittest 断言方法

```python
class TestAssertions(unittest.TestCase):
    def test_equal(self):
        self.assertEqual(1 + 1, 2)           # ==
        self.assertNotEqual(1 + 1, 3)        # !=

    def test_true_false(self):
        self.assertTrue(1 == 1)
        self.assertFalse(1 == 2)
        self.assertIsNone(None)
        self.assertIsNotNone("hello")

    def test_in(self):
        self.assertIn(3, [1, 2, 3])
        self.assertNotIn(4, [1, 2, 3])

    def test_exceptions(self):
        with self.assertRaises(ZeroDivisionError):
            1 / 0

        with self.assertRaisesRegex(ValueError, "invalid"):
            raise ValueError("invalid input")

    def test_almost_equal(self):
        self.assertAlmostEqual(0.1 + 0.2, 0.3)  # 浮点数比较

    def test_greater(self):
        self.assertGreater(5, 3)
        self.assertGreaterEqual(5, 5)
        self.assertLess(3, 5)
```

---

## 3. setUp / tearDown

```python
class TestDatabase(unittest.TestCase):
    def setUp(self):
        """每个测试方法前执行"""
        self.db = Database()
        self.db.connect()
        self.db.execute("CREATE TABLE users (id INT, name TEXT)")

    def tearDown(self):
        """每个测试方法后执行"""
        self.db.execute("DROP TABLE users")
        self.db.disconnect()

    def test_insert(self):
        self.db.execute("INSERT INTO users VALUES (1, 'Alice')")
        result = self.db.query("SELECT * FROM users")
        self.assertEqual(len(result), 1)

    def test_delete(self):
        self.db.execute("INSERT INTO users VALUES (1, 'Alice')")
        self.db.execute("DELETE FROM users WHERE id=1")
        result = self.db.query("SELECT * FROM users")
        self.assertEqual(len(result), 0)
```

### 类级别 setUpClass / tearDownClass

```python
class TestHeavyResource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """整个测试类只执行一次"""
        cls.resource = HeavyResource()
        cls.resource.start()

    @classmethod
    def tearDownClass(cls):
        cls.resource.stop()

    def test_operation1(self):
        result = self.resource.do_something()
        self.assertTrue(result)

    def test_operation2(self):
        result = self.resource.do_another_thing()
        self.assertTrue(result)
```

---

## 4. unittest vs pytest

| 特性 | unittest | pytest |
|------|----------|--------|
| 来源 | 标准库 | 第三方 |
| 写法 | 类 + 方法 | 函数（更简洁） |
| 断言 | self.assertXxx() | assert（原生） |
| fixture | setUp/tearDown | @pytest.fixture（更强大） |
| 参数化 | 需子测试 | @pytest.mark.parametrize |
| 插件生态 | 少 | 丰富 |
| 兼容性 | - | 能运行 unittest 测试 |

---

## 5. 用 pytest 运行 unittest

pytest 可以**直接运行 unittest 测试**，无需修改。

```bash
# 运行 unittest 测试（用 pytest）
pytest test_math.py

# 混合运行
pytest tests/  # 同时运行 unittest 和 pytest 风格的测试
```

### 在 unittest 中使用 pytest fixture

```python
import unittest
import pytest

class TestWithPytestFixture(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setup_fixture(self, tmp_path):
        """在 unittest 中使用 pytest fixture"""
        self.temp_dir = tmp_path

    def test_file_creation(self):
        file = self.temp_dir / "test.txt"
        file.write_text("hello")
        self.assertTrue(file.exists())
```

---

## 6. unittest.mock 回顾

```python
from unittest import TestCase
from unittest.mock import patch, Mock

class TestAPI(TestCase):
    @patch("requests.get")
    def test_fetch_user(self, mock_get):
        mock_get.return_value.json.return_value = {"name": "Alice"}

        user = fetch_user(1)

        self.assertEqual(user["name"], "Alice")
        mock_get.assert_called_once()

    def test_with_mock_object(self):
        mock_db = Mock()
        mock_db.get_user.return_value = {"id": 1, "name": "Bob"}

        service = UserService(mock_db)
        user = service.get_user(1)

        self.assertEqual(user["name"], "Bob")
        mock_db.get_user.assert_called_with(1)
```

---

## 实战练习

### 练习：将 unittest 测试改写为 pytest

```python
# unittest 版本
test_calculator_unittest.py
import unittest

class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()

    def test_add(self):
        self.assertEqual(self.calc.add(2, 3), 5)

    def test_divide_by_zero(self):
        with self.assertRaises(ValueError):
            self.calc.divide(10, 0)

if __name__ == "__main__":
    unittest.main()
```

任务：改写成 pytest 风格。

---

## 今日总结

- [ ] unittest 是标准库，无需安装
- [ ] `TestCase` + `assertXxx()` 方法
- [ ] `setUp/tearDown` 每个测试前后执行
- [ ] `setUpClass/tearDownClass` 类级别执行一次
- [ ] pytest 可以运行 unittest 测试
- [ ] 新项目推荐 pytest，老项目可逐步迁移

---

*第 37 天 / 330 天*
