# 第 46 天：异常处理与 HTTPException

## 学习目标

- 掌握 HTTPException 的使用
- 学会自定义异常类
- 理解全局异常处理器
- 掌握错误响应标准化

---

## 1. HTTPException

### 基础用法

```python
from fastapi import FastAPI, HTTPException, status

app = FastAPI()

items = {1: {"name": "Foo"}, 2: {"name": "Bar"}}


@app.get("/items/{item_id}")
def read_item(item_id: int):
    if item_id not in items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return items[item_id]
```

响应：
```json
{
  "detail": "Item not found"
}
```

### 自定义响应头

```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    if item_id not in items:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "Resource not found"},
        )
    return items[item_id]
```

### 常用状态码快捷方式

```python
from fastapi import status

status.HTTP_200_OK          # 200
status.HTTP_201_CREATED     # 201
status.HTTP_400_BAD_REQUEST # 400
status.HTTP_401_UNAUTHORIZED # 401
status.HTTP_403_FORBIDDEN   # 403
status.HTTP_404_NOT_FOUND   # 404
status.HTTP_422_UNPROCESSABLE_ENTITY # 422
status.HTTP_500_INTERNAL_SERVER_ERROR # 500
```

---

## 2. 自定义异常类

### 定义业务异常

```python
class BusinessException(Exception):
    """业务异常基类"""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class NotFoundException(BusinessException):
    def __init__(self, resource: str):
        super().__init__(404, f"{resource} 不存在")


class PermissionDeniedException(BusinessException):
    def __init__(self):
        super().__init__(403, "权限不足")


class ValidationException(BusinessException):
    def __init__(self, field: str, message: str):
        super().__init__(400, f"{field}: {message}")
```

### 抛出业务异常

```python
@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = find_user(user_id)
    if not user:
        raise NotFoundException("用户")
    return user


@app.delete("/users/{user_id}")
def delete_user(user_id: int, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise PermissionDeniedException()
    ...
```

---

## 3. 全局异常处理器

### 注册异常处理器

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()


# 处理自定义业务异常
@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=exc.code,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": None,
        },
    )


# 处理 FastAPI 的 HTTPException
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None,
        },
    )


# 处理请求验证错误
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 422,
            "message": "请求参数验证失败",
            "errors": errors,
        },
    )


# 处理所有未捕获的异常
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": None,
        },
    )
```

### 统一的响应格式

```python
from typing import Generic, TypeVar, Any
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    code: int
    message: str
    data: T | None = None


class ErrorResponse(BaseModel):
    code: int
    message: str
    errors: list[dict] | None = None
```

---

## 4. 验证错误美化

### 自定义验证错误响应

```python
@app.exception_handler(RequestValidationError)
async def custom_validation_handler(request: Request, exc: RequestValidationError):
    error_messages = []

    for error in exc.errors():
        loc = error.get("loc", [])
        field = loc[-1] if loc else "unknown"
        msg = error.get("msg", "")

        # 美化错误信息
        if error.get("type") == "missing":
            error_messages.append(f"字段 '{field}' 不能为空")
        elif error.get("type") == "type_error.integer":
            error_messages.append(f"字段 '{field}' 必须是整数")
        elif "max_length" in error.get("type", ""):
            limit = error.get("ctx", {}).get("limit_value", "")
            error_messages.append(f"字段 '{field}' 最多 {limit} 个字符")
        else:
            error_messages.append(f"字段 '{field}': {msg}")

    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "参数校验失败",
            "errors": error_messages,
        },
    )
```

---

## 5. 异常处理最佳实践

### 异常分层

```
HTTPException      → 路由层直接使用
BusinessException  → 业务逻辑层
ValidationError    → Pydantic 自动抛出
Exception          → 兜底捕获
```

### 不要在深层抛出 HTTPException

```python
# ❌ 不好：业务层依赖 HTTP 概念
class UserService:
    def get_user(self, user_id: int):
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(404, "User not found")  # 业务层不应该知道 HTTP
        return user

# ✅ 好：业务层用业务异常
class UserService:
    def get_user(self, user_id: int):
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user:
            raise NotFoundException("用户")  # 业务异常
        return user

# 在路由层转换为 HTTP 异常
@app.get("/users/{user_id}")
def get_user(user_id: int, service: UserService = Depends()):
    try:
        return service.get_user(user_id)
    except NotFoundException:
        raise HTTPException(404, detail="用户不存在")
```

---

## 实战练习

### 练习：完整的异常处理体系

```python
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()


# ========== 自定义异常 ==========
class AppException(Exception):
    def __init__(self, code: int, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code


class ResourceNotFound(AppException):
    def __init__(self, resource: str = "资源"):
        super().__init__(1001, f"{resource}不存在", 404)


class DuplicateResource(AppException):
    def __init__(self, resource: str = "资源"):
        super().__init__(1002, f"{resource}已存在", 409)


class Unauthorized(AppException):
    def __init__(self):
        super().__init__(1003, "未授权", 401)


class Forbidden(AppException):
    def __init__(self):
        super().__init__(1004, "禁止访问", 403)


# ========== 异常处理器 ==========
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message, "data": None},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = [f"{'->'.join(str(x) for x in e['loc'])}: {e['msg']}" for e in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={"code": 422, "message": "参数错误", "errors": errors},
    )


# ========== 路由 ==========
users = {}


@app.post("/users")
def create_user(user_id: int, name: str):
    if user_id in users:
        raise DuplicateResource("用户")
    users[user_id] = {"id": user_id, "name": name}
    return {"code": 200, "message": "创建成功", "data": users[user_id]}


@app.get("/users/{user_id}")
def get_user(user_id: int):
    if user_id not in users:
        raise ResourceNotFound("用户")
    return {"code": 200, "message": "成功", "data": users[user_id]}


@app.get("/protected")
def protected():
    raise Unauthorized()
```

---

## 今日总结

- [ ] `HTTPException` 用于路由层返回 HTTP 错误响应
- [ ] 自定义业务异常类，解耦业务层和 HTTP 层
- [ ] `@app.exception_handler()` 注册全局异常处理器
- [ ] 统一错误响应格式，方便前端处理
- [ ] 美化验证错误信息，提升用户体验
- [ ] 异常处理器优先级：具体异常 > 通用异常
- [ ] 始终保留一个 `Exception` 兜底处理器

---

*第 46 天 / 330 天*
*第二阶段：Web 框架与 API - 异常处理*
