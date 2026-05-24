# 第 47 天：OpenAPI 与 Swagger 文档

## 学习目标

- 理解 OpenAPI 规范
- 掌握 FastAPI 自动文档的生成
- 学会自定义文档信息
- 了解文档优化技巧

---

## 1. OpenAPI 简介

### 什么是 OpenAPI

OpenAPI 规范（原 Swagger）是一种描述 REST API 的标准格式：
- 接口路径、方法、参数
- 请求/响应数据结构
- 认证方式
- 生成 SDK 和文档

### FastAPI 自动生成

```python
from fastapi import FastAPI

app = FastAPI(
    title="我的 API",
    description="这是一个示例 API 文档",
    version="1.0.0",
)

# 自动生成:
# /docs    → Swagger UI
# /redoc   → ReDoc 文档
# /openapi.json → OpenAPI 规范 JSON
```

---

## 2. 配置 API 元信息

### 应用级别配置

```python
app = FastAPI(
    title="电商后台 API",
    description="""
    ## 功能

    * 用户管理
    * 商品管理
    * 订单管理

    ## 认证

    使用 Bearer Token，在 Header 中传递：
    `Authorization: Bearer <token>`
    """,
    version="2.0.0",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "技术支持",
        "url": "http://example.com/contact/",
        "email": "support@example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)
```

### 禁用文档

```python
# 生产环境禁用
app = FastAPI(docs_url=None, redoc_url=None)

# 自定义文档路径
app = FastAPI(
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)
```

---

## 3. 路由文档配置

### 路由描述

```python
@app.get(
    "/items/{item_id}",
    summary="获取单个商品",
    description="根据商品 ID 获取商品详细信息，包括库存、价格等",
    response_description="商品详细信息",
    deprecated=False,
)
def read_item(item_id: int):
    """
    ## 获取商品

    - **item_id**: 商品唯一标识
    - 返回商品完整信息

    ## 错误码

    - 404: 商品不存在
    """
    return {"item_id": item_id}
```

### 标签组织

```python
@app.get("/users", tags=["用户管理"])
def list_users(): ...

@app.post("/users", tags=["用户管理"])
def create_user(): ...

@app.get("/orders", tags=["订单管理"])
def list_orders(): ...

@app.get("/products", tags=["商品管理"])
def list_products(): ...
```

### 标签元信息

```python
tags_metadata = [
    {
        "name": "用户管理",
        "description": "用户注册、登录、信息修改",
        "externalDocs": {
            "description": "详细文档",
            "url": "https://example.com/users",
        },
    },
    {
        "name": "订单管理",
        "description": "订单创建、查询、取消",
    },
]

app = FastAPI(openapi_tags=tags_metadata)
```

---

## 4. 响应文档

### 多状态码响应

```python
from fastapi import FastAPI
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str

class Error(BaseModel):
    code: int
    message: str


@app.get(
    "/users/{user_id}",
    response_model=User,
    responses={
        200: {"description": "成功", "model": User},
        404: {"description": "用户不存在", "model": Error},
        500: {"description": "服务器错误", "model": Error},
    },
)
def get_user(user_id: int):
    return {"id": user_id, "name": "Alice"}
```

---

## 5. 安全文档

### Bearer Token

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


@app.get("/secure", dependencies=[Depends(security)])
def secure_endpoint():
    return {"message": "安全接口"}
```

### OAuth2

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

app = FastAPI(
    swagger_ui_init_oauth={
        "clientId": "your-client-id",
        "clientSecret": "your-client-secret",
        "appName": "你的应用",
    }
)


@app.get("/users/me")
def read_users_me(token: str = Depends(oauth2_scheme)):
    return {"token": token}
```

---

## 6. 自定义 OpenAPI

### 修改自动生成的 OpenAPI

```python
from fastapi.openapi.utils import get_openapi


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="自定义 API",
        version="3.0.0",
        description="这是自定义 OpenAPI",
        routes=app.routes,
    )

    # 添加全局安全设置
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"bearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
```

---

## 7. 文档导出

### 导出 OpenAPI JSON

```bash
# 启动后下载
curl http://localhost:8000/openapi.json > openapi.json
```

### 生成客户端 SDK

```bash
# 安装 openapi-generator
npm install -g @openapitools/openapi-generator-cli

# 生成 Python 客户端
openapi-generator-cli generate \
  -i openapi.json \
  -g python \
  -o ./python-client

# 生成 TypeScript 客户端
openapi-generator-cli generate \
  -i openapi.json \
  -g typescript-axios \
  -o ./ts-client
```

---

## 实战练习

### 练习：完整的文档配置

```python
from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

tags_metadata = [
    {"name": "认证", "description": "登录、注册、Token 刷新"},
    {"name": "用户", "description": "用户信息管理"},
    {"name": "系统", "description": "健康检查、系统信息"},
]

app = FastAPI(
    title="企业级 API",
    description="## 简介\n\n这是企业级后台管理系统的 API 接口文档。\n\n## 认证\n\n所有接口（除登录外）都需要 Bearer Token。",
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.post("/token", tags=["认证"], summary="获取访问令牌")
def login():
    """
    使用用户名和密码换取访问令牌。

    - 令牌有效期 30 分钟
    - 刷新令牌有效期 7 天
    """
    return {"access_token": "xxx", "token_type": "bearer"}


@app.get("/users/me", tags=["用户"], summary="获取当前用户信息")
def read_users_me(token: str = Depends(oauth2_scheme)):
    """获取当前登录用户的详细信息"""
    return {"username": "alice"}


@app.get("/health", tags=["系统"], summary="健康检查")
def health_check():
    """检查服务是否正常运行"""
    return {"status": "ok"}
```

打开 `/docs` 查看效果：
- 左侧按标签分组
- 每个接口有描述和参数说明
- 可以在线测试接口

---

## 今日总结

- [ ] FastAPI 自动生成 `/docs` (Swagger) 和 `/redoc` (ReDoc)
- [ ] `FastAPI()` 配置全局文档信息：title、description、version
- [ ] 路由用 `tags` 分组、`summary` 写摘要、docstring 写详细说明
- [ ] `responses` 参数定义多状态码响应模型
- [ ] 可以自定义 `app.openapi` 函数修改生成的 OpenAPI
- [ ] OpenAPI JSON 可导出用于生成客户端 SDK
- [ ] 好的文档减少沟通成本，提升开发效率

---

*第 47 天 / 330 天*
*第二阶段：Web 框架与 API - OpenAPI 文档*
