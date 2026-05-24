# 第 48 天：项目练习 - 用户管理 API

## 学习目标

- 综合运用 FastAPI 基础知识
- 完成一个完整的用户管理 API
- 实践依赖注入、异常处理、文档配置
- 编写接口测试

---

## 项目需求

### 功能需求

1. **用户注册** — 用户名、邮箱、密码
2. **用户登录** — 返回 JWT Token
3. **获取当前用户** — 需要认证
4. **更新用户信息** — 部分更新
5. **修改密码** — 需要旧密码验证
6. **用户列表** — 管理员权限，分页

### 技术要求

- Pydantic 模型验证
- 依赖注入做认证
- 统一异常处理
- Swagger 文档
- 响应模型过滤敏感字段

---

## 项目结构

```
user-api/
├── main.py           # 入口
├── models.py         # Pydantic 模型
├── auth.py           # 认证依赖
├── exceptions.py     # 自定义异常
├── handlers.py       # 异常处理器
├── database.py       # 模拟数据库
└── routers/
    ├── __init__.py
    ├── users.py      # 用户路由
    └── auth.py       # 认证路由
```

---

## 完整代码

### models.py

```python
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    bio: Optional[str] = Field(None, max_length=500)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    bio: Optional[str] = Field(None, max_length=500)


class UserOut(UserBase):
    id: int
    is_active: bool = True
    role: str = "user"

    class Config:
        from_attributes = True


class UserInDB(UserOut):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    username: str
    password: str
```

### database.py

```python
from models import UserInDB

# 内存数据库（实际项目用 PostgreSQL）
users_db: dict[int, UserInDB] = {}
next_id = 1


def get_user_by_username(username: str) -> UserInDB | None:
    for user in users_db.values():
        if user.username == username:
            return user
    return None


def get_user_by_id(user_id: int) -> UserInDB | None:
    return users_db.get(user_id)


def create_user(user: UserInDB) -> UserInDB:
    global next_id
    user.id = next_id
    users_db[next_id] = user
    next_id += 1
    return user


def update_user(user_id: int, data: dict) -> UserInDB | None:
    if user_id not in users_db:
        return None
    user = users_db[user_id]
    for key, value in data.items():
        if value is not None and hasattr(user, key):
            setattr(user, key, value)
    return user


def list_users(skip: int = 0, limit: int = 20) -> list[UserInDB]:
    return list(users_db.values())[skip : skip + limit]


def delete_user(user_id: int) -> bool:
    if user_id in users_db:
        del users_db[user_id]
        return True
    return False
```

### auth.py

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from database import get_user_by_username

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_admin(current_user = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user
```

### exceptions.py

```python
class AppException(Exception):
    def __init__(self, code: int, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code


class UserExistsException(AppException):
    def __init__(self):
        super().__init__(1001, "用户已存在", 409)


class UserNotFoundException(AppException):
    def __init__(self):
        super().__init__(1002, "用户不存在", 404)


class InvalidCredentialsException(AppException):
    def __init__(self):
        super().__init__(1003, "用户名或密码错误", 401)


class ForbiddenException(AppException):
    def __init__(self):
        super().__init__(1004, "权限不足", 403)
```

### handlers.py

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from exceptions import AppException


def register_handlers(app):
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
            content={"code": 422, "message": "参数验证失败", "errors": errors},
        )
```

### routers/auth.py

```python
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from models import Token, UserCreate, UserOut
from database import get_user_by_username, create_user
from auth import (
    verify_password, get_password_hash, create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from exceptions import UserExistsException, InvalidCredentialsException

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(user: UserCreate):
    if get_user_by_username(user.username):
        raise UserExistsException()

    hashed = get_password_hash(user.password)
    db_user = create_user({
        "username": user.username,
        "email": user.email,
        "bio": user.bio,
        "hashed_password": hashed,
    })
    return db_user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise InvalidCredentialsException()

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token}
```

### routers/users.py

```python
from fastapi import APIRouter, Depends, Query
from typing import List
from models import UserOut, UserUpdate, PasswordChange
from database import get_user_by_id, update_user, list_users, delete_user
from auth import get_current_user, get_current_admin, verify_password, get_password_hash
from exceptions import UserNotFoundException, ForbiddenException

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/me", response_model=UserOut)
def get_me(current_user = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_me(update: UserUpdate, current_user = Depends(get_current_user)):
    user = update_user(current_user.id, update.model_dump(exclude_unset=True))
    return user


@router.post("/me/password")
def change_password(data: PasswordChange, current_user = Depends(get_current_user)):
    if not verify_password(data.old_password, current_user.hashed_password):
        raise ForbiddenException()

    update_user(current_user.id, {"hashed_password": get_password_hash(data.new_password)})
    return {"message": "密码修改成功"}


@router.get("/", response_model=List[UserOut])
def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    admin = Depends(get_current_admin),
):
    return list_users(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, current_user = Depends(get_current_user)):
    # 只能看自己的，管理员可以看所有
    if current_user.role != "admin" and current_user.id != user_id:
        raise ForbiddenException()

    user = get_user_by_id(user_id)
    if not user:
        raise UserNotFoundException()
    return user


@router.delete("/{user_id}", status_code=204)
def remove_user(user_id: int, admin = Depends(get_current_admin)):
    if not delete_user(user_id):
        raise UserNotFoundException()
    return None
```

### main.py

```python
from fastapi import FastAPI
from routers import auth, users
from handlers import register_handlers

app = FastAPI(
    title="用户管理 API",
    description="完整的用户认证和管理系统",
    version="1.0.0",
)

# 注册异常处理器
register_handlers(app)

# 注册路由
app.include_router(auth.router)
app.include_router(users.router)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)
```

---

## 安装依赖

```bash
pip install fastapi uvicorn python-jose passlib bcrypt
```

---

## 测试 API

```bash
# 1. 注册
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "Hello1234",
    "bio": "你好世界"
  }'

# 2. 登录
curl -X POST "http://localhost:8000/auth/login" \
  -d "username=alice&password=Hello1234"

# 3. 获取当前用户
curl "http://localhost:8000/users/me" \
  -H "Authorization: Bearer <token>"

# 4. 更新信息
curl -X PATCH "http://localhost:8000/users/me" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"bio": "更新后的简介"}'

# 5. 修改密码
curl -X POST "http://localhost:8000/users/me/password" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"old_password": "Hello1234", "new_password": "World5678"}'
```

---

## 今日总结

- [ ] 综合运用路由、模型、依赖注入完成完整 API
- [ ] 使用 JWT + OAuth2 实现认证
- [ ] 响应模型过滤密码等敏感字段
- [ ] 自定义异常 + 全局处理器统一错误格式
- [ ] 依赖链实现权限控制（登录 -> 活跃用户 -> 管理员）
- [ ] Swagger 文档自动生成
- [ ] 下一章将进入 FastAPI 进阶：数据库、缓存、异步

---

*第 48 天 / 330 天*
*第二阶段：Web 框架与 API - FastAPI 基础项目*
