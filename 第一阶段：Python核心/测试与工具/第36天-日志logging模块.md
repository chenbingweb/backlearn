# 第 36 天：日志 logging 模块

## 学习目标

- 掌握 Python logging 模块的使用
- 理解日志级别和处理器
- 学会配置日志格式
- 了解日志最佳实践

---

## 1. 为什么用 logging 而不是 print

| print | logging |
|-------|---------|
| 输出到 stdout | 可输出到文件、网络、邮件等 |
| 无法分级 | 有 DEBUG/INFO/WARNING/ERROR/CRITICAL 级别 |
| 无法关闭 | 可配置输出哪些级别 |
| 无时间戳 | 可包含时间、模块、行号等信息 |
| 难定位 | 可追踪到具体代码位置 |

---

## 2. 基础用法

### 最简单的日志

```python
import logging

# 默认级别是 WARNING，所以 DEBUG 和 INFO 不会输出
logging.debug("调试信息")
logging.info("普通信息")
logging.warning("警告信息")    # 会输出
logging.error("错误信息")      # 会输出
logging.critical("严重错误")   # 会输出
```

### 基本配置

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,                    # 输出 DEBUG 及以上级别
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="app.log",                     # 输出到文件
    filemode="a",                           # 追加模式
)

logging.info("应用启动")
```

---

## 3. 日志级别

| 级别 | 数值 | 用途 |
|------|------|------|
| DEBUG | 10 | 调试细节 |
| INFO | 20 | 正常流程信息 |
| WARNING | 30 | 警告，但不影响运行 |
| ERROR | 40 | 错误，部分功能失败 |
| CRITICAL | 50 | 严重错误，程序可能崩溃 |

```python
# 设置级别
logger.setLevel(logging.DEBUG)

# 动态调整
if verbose:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
```

---

## 4. 创建 Logger

### 推荐方式（非 root logger）

```python
import logging

# 创建 logger（按模块命名是惯例）
logger = logging.getLogger(__name__)

# 创建处理器
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("app.log")

# 设置级别
console_handler.setLevel(logging.INFO)
file_handler.setLevel(logging.DEBUG)

# 创建格式器
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# 添加处理器
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# 使用
logger.info("用户登录")
logger.error("数据库连接失败")
```

### 日志层次

```
root logger
├── myapp          (logger.getLogger("myapp"))
│   ├── myapp.db   (logger.getLogger("myapp.db"))
│   └── myapp.api  (logger.getLogger("myapp.api"))
└── thirdparty     (第三方库)
```

```python
# 子 logger 继承父 logger 的配置
db_logger = logging.getLogger("myapp.db")
api_logger = logging.getLogger("myapp.api")

db_logger.info("查询用户")    # 输出: myapp.db - INFO - 查询用户
api_logger.error("请求失败")  # 输出: myapp.api - ERROR - 请求失败
```

---

## 5. 处理器类型

| 处理器 | 用途 |
|--------|------|
| StreamHandler | 输出到控制台 |
| FileHandler | 输出到文件 |
| RotatingFileHandler | 自动轮转文件（按大小） |
| TimedRotatingFileHandler | 按时间轮转 |
| SMTPHandler | 发送邮件 |
| SysLogHandler | 写入系统日志 |

### 文件轮转

```python
from logging.handlers import RotatingFileHandler

# 文件最大 10MB，保留 5 个备份
handler = RotatingFileHandler(
    "app.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

# 生成: app.log, app.log.1, app.log.2, ... app.log.5
```

### 按时间轮转

```python
from logging.handlers import TimedRotatingFileHandler

# 每天 midnight 轮转
handler = TimedRotatingFileHandler(
    "app.log",
    when="midnight",
    interval=1,
    backupCount=7  # 保留7天
)
```

---

## 6. JSON 格式日志

```python
import logging
import json
from pythonjsonlogger import jsonlogger

# 安装: pip install python-json-logger

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(name)s %(levelname)s %(message)s"
)
logHandler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# 输出 JSON 格式
logger.info("用户操作", extra={"user_id": 123, "action": "login"})
# {"asctime": "2024-01-15 10:30:00", "name": "root", "levelname": "INFO", "message": "用户操作", "user_id": 123, "action": "login"}
```

---

## 7. 日志最佳实践

### 不要这样做

```python
# ❌ 字符串拼接（性能差）
logger.debug("用户 " + user_id + " 登录")

# ❌ 异常信息丢失
try:
    risky()
except:
    logger.error("出错了")  # 没有异常信息！
```

### 推荐做法

```python
# ✅ 使用 % 格式化（不使用时不会计算）
logger.debug("用户 %s 登录", user_id)

# ✅ 记录异常
import traceback

try:
    risky()
except Exception:
    logger.exception("操作失败")  # 自动记录堆栈

# 或
logger.error("操作失败", exc_info=True)
```

### 结构化日志

```python
# ✅ 使用 extra 添加上下文
logger.info(
    "订单创建成功",
    extra={
        "order_id": order.id,
        "user_id": order.user_id,
        "amount": order.amount,
    }
)
```

---

## 实战练习

### 练习：为应用配置完整的日志系统

```python
# logger_config.py
import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logger(name, log_file=None, level=logging.INFO):
    """配置日志"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 控制台输出
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )
    console.setFormatter(console_fmt)
    logger.addHandler(console)

    # 文件输出
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_fmt = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)

    return logger
```

```python
# app.py
from logger_config import setup_logger

logger = setup_logger("myapp", "myapp.log")

def process_order(order_id):
    logger.info("开始处理订单", extra={"order_id": order_id})
    try:
        # 处理逻辑
        result = do_something()
        logger.info("订单处理完成", extra={"order_id": order_id, "result": result})
        return result
    except Exception:
        logger.exception("订单处理失败", extra={"order_id": order_id})
        raise
```

---

## 今日总结

- [ ] 用 logging 替代 print，支持分级和灵活配置
- [ ] `getLogger(__name__)` 创建模块级 logger
- [ ] Handler 控制输出目标，Formatter 控制格式
- [ ] `RotatingFileHandler` 自动轮转日志文件
- [ ] `logger.exception()` 自动记录异常堆栈
- [ ] 用 `extra` 添加上下文，方便日志分析

---

*第 36 天 / 330 天*
