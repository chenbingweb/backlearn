# 第 39 天：FastAPI 入门与环境搭建

## 学习目标

- 了解 FastAPI 的核心特性与优势
- 搭建 FastAPI 开发环境
- 编写第一个 FastAPI 应用
- 理解 ASGI 与 Uvicorn

---

## 1. 为什么选择 FastAPI

### FastAPI 核心特性

| 特性 | 说明 |
|------|------|
| **高性能** | 基于 Starlette 和 Pydantic，性能接近 Node.js 和 Go |
| **类型提示** | 全自动数据验证、序列化、文档生成 |
| **自动生成文档** | 自动生成交互式 OpenAPI/Swagger UI |
| **异步支持** | 原生支持 async/await |
| **依赖注入** | 强大的依赖注入系统 |
| **IDE 友好** | 完整的类型支持，代码补全和错误检查 |

### 性能对比（Requests/second）

```
Go:     ~70,000
NodeJS: ~40,000
FastAPI: ~18,000
Flask:  ~2,000
Django: ~1,500
```

---

## 2. 环境搭建

### 创建项目

```bash
# 创建项目目录
mkdir fastapi-demo && cd fastapi-demo

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 安装依赖
pip install fastapi uvicorn[standard]

# 保存依赖
pip freeze > requirements.txt
```

### 项目结构

```
fastapi-demo/
├── main.py           # 入口文件
├── requirements.txt  # 依赖列表
└── venv/             # 虚拟环境
```

---

## 3. 第一个 FastAPI 应用

### Hello World

```python
# main.py
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}


@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
```

### 运行应用

```bash
# 开发模式（自动重载）
uvicorn main:app --reload

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

参数说明：
- `main:app` — main.py 中的 app 对象
- `--reload` — 代码变更自动重启（仅开发）
- `--host` — 绑定地址
- `--port` — 端口
- `--workers` — 工作进程数

### 访问应用

```
http://localhost:8000          # Hello World
http://localhost:8000/items/42 # 路径参数
http://localhost:8000/docs     # Swagger UI 文档
http://localhost:8000/redoc    # ReDoc 文档
```

---

## 4. ASGI 与 Uvicorn

### 什么是 ASGI

```
WSGI（旧）          ASGI（新）
同步               异步
一次一个请求        并发处理
不支持 WebSocket   支持 WebSocket
```

### Uvicorn 架构

```
浏览器请求
    ↓
Nginx（可选反向代理）
    ↓
Uvicorn（ASGI 服务器）
    ↓
FastAPI（ASGI 应用）
```

---

## 5. 路由 HTTP 方法

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/users")      # 获取资源
def list_users():
    return [{"id": 1, "name": "Alice"}]


@app.post("/users")     # 创建资源
def create_user():
    return {"id": 2, "created": True}


@app.put("/users/{id}") # 全量更新
def update_user(id: int):
    return {"id": id, "updated": True}


@app.patch("/users/{id}") # 部分更新
def partial_update(id: int):
    return {"id": id, "patched": True}


@app.delete("/users/{id}") # 删除资源
def delete_user(id: int):
    return {"id": id, "deleted": True}
```

---

## 6. 路由组织技巧

### 使用 tags 分组

```python
@app.get("/users", tags=["用户管理"])
def list_users():
    ...

@app.post("/users", tags=["用户管理"])
def create_user():
    ...

@app.get("/orders", tags=["订单管理"])
def list_orders():
    ...
```

### 使用 APIRouter（后续详细讲）

```python
from fastapi import APIRouter

user_router = APIRouter(prefix="/users", tags=["用户管理"])

@user_router.get("/")
def list_users():
    ...
```

---

## 实战练习

### 练习 1：创建基础 API

```python
# main.py
from fastapi import FastAPI

app = FastAPI(title="我的第一个 API", version="1.0.0")


@app.get("/")
def root():
    return {"app": "FastAPI Demo", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/info")
def app_info():
    return {
        "framework": "FastAPI",
        "language": "Python",
        "docs_url": "/docs",
    }
```

运行并验证：
1. 访问 `/` 返回应用信息
2. 访问 `/health` 返回状态 ok
3. 访问 `/docs` 查看自动生成的 Swagger 文档
4. 在 Swagger UI 中点击 `Try it out` 测试接口

### 练习 2：熟悉 Swagger UI

打开 `http://localhost:8000/docs`，观察：
- 每个路由的 HTTP 方法、路径
- 自动生成的请求参数
- 响应数据结构
- 可点击的 `Try it out` 按钮

---

## 今日总结

- [ ] FastAPI 基于 Starlette + Pydantic，性能高、开发快
- [ ] `pip install fastapi uvicorn[standard]` 安装
- [ ] `uvicorn main:app --reload` 运行开发服务器
- [ ] `@app.get/post/put/patch/delete()` 定义路由
- [ ] 自动文档在 `/docs`（Swagger）和 `/redoc`
- [ ] ASGI 是异步网关接口，Uvicorn 是 ASGI 服务器

---

*第 39 天 / 330 天*
*第二阶段：Web 框架与 API - FastAPI 入门*
