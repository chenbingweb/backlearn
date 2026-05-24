# 第 45 天：Cookie、Session 与 Header

## 学习目标

- 掌握请求头的读取和设置
- 学会 Cookie 的读写操作
- 了解 Session 的原理和实现
- 掌握安全相关的 Cookie 属性

---

## 1. HTTP Header

### 读取请求头

```python
from fastapi import FastAPI, Header

app = FastAPI()


@app.get("/headers/")
def read_headers(
    user_agent: str | None = Header(None),
    x_request_id: str | None = Header(None, alias="X-Request-ID"),
    accept_language: list[str] | None = Header(None),
):
    return {
        "user_agent": user_agent,
        "x_request_id": x_request_id,
        "accept_language": accept_language,
    }
```

注意：
- Header 参数名自动将 `_` 转为 `-`
- 使用 `alias` 显式指定原始名称
- 多值 Header 用 `list[str]`

### 必需的 Header

```python
@app.get("/require-header/")
def require_header(
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    return {"api_key": x_api_key}
```

### 设置响应头

```python
from fastapi import Response


@app.get("/set-headers/")
def set_headers(response: Response):
    response.headers["X-Process-Time"] = "0.0123"
    response.headers["X-Request-ID"] = "abc-123"
    response.headers["Cache-Control"] = "no-cache"
    return {"message": "ok"}
```

---

## 2. Cookie

### 读取 Cookie

```python
from fastapi import Cookie


@app.get("/read-cookie/")
def read_cookie(
    session_id: str | None = Cookie(None),
    user_pref: str | None = Cookie(None),
):
    return {
        "session_id": session_id,
        "user_pref": user_pref,
    }
```

### 设置 Cookie

```python
from fastapi import Response


@app.post("/login/")
def login(response: Response, username: str):
    response.set_cookie(
        key="session_id",
        value=f"session_{username}",
        max_age=1800,          # 30分钟（秒）
        httponly=True,         # 禁止 JS 访问
        secure=True,           # 仅 HTTPS 传输
        samesite="lax",        # CSRF 防护
    )
    return {"message": "登录成功"}
```

### Cookie 安全属性

| 属性 | 作用 |
|------|------|
| `httponly=True` | 禁止 JavaScript 读取，防 XSS |
| `secure=True` | 仅 HTTPS 传输 |
| `samesite="lax"` | 跨站请求限制，防 CSRF |
| `samesite="strict"` | 严格模式，完全禁止跨站 |
| `max_age` | 过期时间（秒） |
| `expires` | 具体过期时间点 |
| `path` | Cookie 生效路径 |
| `domain` | Cookie 生效域名 |

### 删除 Cookie

```python
@app.post("/logout/")
def logout(response: Response):
    response.delete_cookie(key="session_id")
    return {"message": "已登出"}
```

### 多个 Cookie

```python
@app.get("/read-all-cookies/")
def read_all_cookies(
    session: str | None = Cookie(None),
    theme: str | None = Cookie(None),
    lang: str | None = Cookie(None),
):
    return {
        "session": session,
        "theme": theme,
        "lang": lang,
    }
```

---

## 3. Session 实现

### 基于 Cookie 的简单 Session

```python
import json
import base64
import secrets
from fastapi import FastAPI, Cookie, Response

app = FastAPI()

# 内存 session 存储（生产环境用 Redis）
sessions = {}


def create_session(data: dict) -> str:
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = data
    return session_id


def get_session(session_id: str | None) -> dict | None:
    if session_id and session_id in sessions:
        return sessions[session_id]
    return None


def destroy_session(session_id: str):
    sessions.pop(session_id, None)


@app.post("/login/")
def login(response: Response, username: str):
    session_id = create_session({"username": username, "role": "user"})
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=3600,
    )
    return {"message": "登录成功"}


@app.get("/me/")
def me(session_id: str | None = Cookie(None)):
    session = get_session(session_id)
    if not session:
        return {"error": "未登录"}
    return session


@app.post("/logout/")
def logout(response: Response, session_id: str | None = Cookie(None)):
    destroy_session(session_id)
    response.delete_cookie(key="session_id")
    return {"message": "已登出"}
```

### Session 中间件方式

```python
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-change-in-production",
    max_age=3600,
)


@app.post("/login/")
def login(request: Request, username: str):
    request.session["username"] = username
    return {"message": "登录成功"}


@app.get("/me/")
def me(request: Request):
    username = request.session.get("username")
    if not username:
        return {"error": "未登录"}
    return {"username": username}


@app.post("/logout/")
def logout(request: Request):
    request.session.clear()
    return {"message": "已登出"}
```

---

## 4. 安全最佳实践

### 安全 Cookie 配置

```python
# 生产环境配置
response.set_cookie(
    key="session_id",
    value=session_id,
    max_age=3600,
    httponly=True,     # ✅ 防 XSS
    secure=True,       # ✅ 仅 HTTPS
    samesite="strict", # ✅ 防 CSRF
    path="/",
)
```

### 防止 Session 固定攻击

```python
@app.post("/login/")
def login(request: Request, response: Response, username: str):
    # 登录成功后更换 session ID
    request.session.clear()
    request.session["username"] = username
    ...
```

---

## 实战练习

### 练习：完整的认证流程

```python
from fastapi import FastAPI, Cookie, Response, HTTPException, Depends
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key="change-this-in-production-!!!",
    max_age=3600,
)


def require_login(request: Request):
    if "user_id" not in request.session:
        raise HTTPException(status_code=401, detail="请先登录")
    return request.session


@app.post("/login")
def login(request: Request, response: Response, username: str, password: str):
    # 简化验证
    if password != "123456":
        raise HTTPException(status_code=400, detail="密码错误")

    request.session["user_id"] = f"user_{username}"
    request.session["username"] = username
    return {"message": "登录成功", "username": username}


@app.get("/me")
def me(session: dict = Depends(require_login)):
    return {"user_id": session["user_id"], "username": session["username"]}


@app.get("/dashboard")
def dashboard(session: dict = Depends(require_login)):
    return {"message": f"欢迎, {session['username']}"}


@app.post("/logout")
def logout(request: Request, response: Response):
    request.session.clear()
    return {"message": "已登出"}
```

---

## 今日总结

- [ ] `Header()` 读取请求头，`_` 自动转 `-`
- [ ] `Cookie()` 读取 Cookie，`Response.set_cookie()` 设置 Cookie
- [ ] Cookie 安全属性：`httponly`、`secure`、`samesite`
- [ ] Session 本质是服务端存储 + Cookie 传递 session_id
- [ ] 生产环境 Session 应该用 Redis，不要存内存
- [ ] Starlette 的 `SessionMiddleware` 提供便捷的 Session 支持
- [ ] 登录后更换 session ID 防止 Session 固定攻击

---

*第 45 天 / 330 天*
*第二阶段：Web 框架与 API - Cookie 与 Session*
