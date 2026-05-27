# 第 52 天：用户认证 JWT

## 学习目标

- 理解 JWT 的结构和原理
- 掌握 JWT 的创建和验证
- 实现登录认证接口
- 学会保护 API 端点

---

## 1. JWT 简介

### JWT 结构

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOiJhbGljZSIsImlhdCI6MTUxNjIzOTAyMn0.K1Jz0cJW_xyz123
   ↓ Header                    ↓ Payload                   ↓ Signature
```

| 部分 | 内容 | 说明 |
|------|------|------|
| Header | `{"alg": "HS256", "typ": "JWT"}` | 加密算法 |
| Payload | `{"sub": "123", "username": "alice"}` | 存放数据 |
| Signature | HMAC 签名 | 防篡改验证 |

### JWT vs Session

| 特性 | JWT | Session |
|------|-----|---------|
| 存储 | 客户端 | 服务端（Redis） |
| 扩展性 | 跨服务共享 | 需共享存储 |
| 性能 | 无查询开销 | 需查询 |
| 失效控制 | 困难（需黑名单）| 简单（删除即可）|
| 适用场景 | API、无状态 | 有状态、需即时失效 |

---

## 2. 安装和配置

### 安装依赖

```bash
pip install python-jose passlib bcrypt python-multipart
```

### 配置密钥

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

settings = Settings()
```

---

## 3. JWT 操作

### 创建 Token

```python
from datetime import datetime, timedelta
from jose import jwt

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()

    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


# 使用
token = create_access_token(
    data={"sub": str(user.id), "username": user.username},
    expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
)
```

### 验证 Token

```python
from jose import JWTError, jwt
from fastapi import HTTPException, status

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

### 解析 Token

```python
payload = verify_token(token)
user_id = payload.get("sub")
username = payload.get("username")
```

---

## 4. 密码处理

### 哈希密码

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# 使用
hashed = get_password_hash("mysecretpassword")
is_valid = verify_password("mysecretpassword", hashed)
```

### 注册时哈希密码

```python
async def register(user: UserCreate, db: AsyncSession):
    # 检查用户是否存在
    existing = await get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    # 创建用户（密码哈希）
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
```

---

## 5. 认证端点

### OAuth2PasswordBearer

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user(int(user_id), db)
    if user is None:
        raise credentials_exception
    return user
```

### 登录接口

```python
from fastapi.security import OAuth2PasswordRequestForm

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_username(db, form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )
    return {"access_token": access_token, "token_type": "bearer"}
```

### 保护端点

```python
@router.get("/me", response_model=UserOut)
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.get("/users/{user_id}", response_model=UserOut)
async def read_user(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    user = await get_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user
```

---

## 6. 完整的 Auth 模块

### schemas.py

```python
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
```

### auth.py

```python
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401)

    user = await get_user(int(user_id), db)
    if user is None:
        raise HTTPException(status_code=401)
    return user
```

---

## 今日总结

- [ ] JWT = Header + Payload + Signature
- [ ] `jose` 库用于创建和验证 JWT
- [ ] `passlib + bcrypt` 用于密码哈希
- [ ] `OAuth2PasswordBearer` 从请求头提取 Token
- [ ] `Depends(get_current_user)` 保护端点
- [ ] `form_data.username` + `form_data.password` 获取登录信息
- [ ] 生产环境密钥要放到环境变量

---

*第 52 天 / 330 天*
*第二阶段：FastAPI 进阶 - JWT 认证*