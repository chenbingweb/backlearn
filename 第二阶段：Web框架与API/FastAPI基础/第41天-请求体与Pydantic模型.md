# 第 41 天：请求体与 Pydantic 模型验证

## 学习目标

- 掌握 Pydantic 模型定义
- 理解请求体验证流程
- 学会嵌套模型和字段验证
- 掌握模型配置和别名

---

## 1. Pydantic 基础

### 什么是 Pydantic

Pydantic 是基于 Python 类型提示的数据验证库：
- 自动数据解析和验证
- 类型强制转换
- 详细的错误信息
- IDE 完美支持

### 基础模型定义

```python
from pydantic import BaseModel


class User(BaseModel):
    name: str
    age: int
    email: str

# 创建实例
user = User(name="Alice", age=30, email="alice@example.com")

# 自动验证
# user = User(name="Bob", age="not_int")  # ValidationError
```

### 可选字段与默认值

```python
from typing import Optional


class Item(BaseModel):
    name: str
    description: Optional[str] = None   # 可选
    price: float
    tax: float = 0.0                    # 有默认值

# 可以省略 description 和 tax
item = Item(name="Foo", price=50.0)
```

### Python 3.10+ 语法

```python
class Item(BaseModel):
    name: str
    description: str | None = None   # Optional 的简写
    price: float
    tax: float = 0.0
```

---

## 2. FastAPI 中的请求体

### POST 请求体

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float = 0.0


@app.post("/items/")
def create_item(item: Item):
    item_dict = item.model_dump()     # Pydantic v2 用法
    if item.tax:
        item_dict["total"] = item.price + item.tax
    return item_dict
```

请求：
```json
POST /items/
{
  "name": "iPhone",
  "price": 6999.0,
  "tax": 0.1
}
```

### PUT 请求体

```python
@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.model_dump()}
```

### 请求体 + 路径参数 + 查询参数混合

```python
@app.put("/items/{item_id}")
def update_item(
    item_id: int = Path(..., ge=1),
    item: Item,
    q: str | None = Query(None),
):
    result = {"item_id": item_id, **item.model_dump()}
    if q:
        result["q"] = q
    return result
```

参数解析规则：
- 路径中的参数 → 路径参数
- 单一模型参数 → 请求体
- 其他 → 查询参数

---

## 3. 字段验证

### Field 验证器

```python
from pydantic import BaseModel, Field


class Item(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        title="商品名称",
        description="商品的显示名称",
    )
    price: float = Field(
        ...,
        gt=0,
        description="必须大于0",
    )
    tax: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="税率 0-1",
    )
    tags: list[str] = Field(default_factory=list)
```

### 字段类型约束

```python
from pydantic import EmailStr, HttpUrl


class User(BaseModel):
    username: str = Field(..., pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr                          # 邮箱格式验证
    website: HttpUrl | None = None           # URL 格式验证
    age: int = Field(..., ge=0, le=150)
```

### 自定义验证器

```python
from pydantic import BaseModel, field_validator


class User(BaseModel):
    username: str
    password: str
    confirm_password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("用户名只能包含字母和数字")
        return v.lower()

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("两次输入的密码不一致")
        return v
```

### 模型级别验证

```python
from pydantic import BaseModel, model_validator


class DateRange(BaseModel):
    start: date
    end: date

    @model_validator(mode="after")
    def check_dates(self):
        if self.end <= self.start:
            raise ValueError("结束日期必须晚于开始日期")
        return self
```

---

## 4. 嵌套模型

### 模型嵌套

```python
class Image(BaseModel):
    url: str
    name: str


class Item(BaseModel):
    name: str
    price: float
    images: list[Image] = []   # 嵌套模型列表


# 请求 JSON
{
  "name": "手机",
  "price": 3999,
  "images": [
    {"url": "http://.../1.jpg", "name": "正面"},
    {"url": "http://.../2.jpg", "name": "背面"}
  ]
}
```

### 深嵌套

```python
class Address(BaseModel):
    city: str
    street: str
    zipcode: str


class Profile(BaseModel):
    bio: str | None = None
    avatar: str | None = None


class User(BaseModel):
    name: str
    email: str
    address: Address          # 嵌套
    profile: Profile | None = None
    friends: list["User"] = []  # 自引用
```

---

## 5. 模型配置

### Config 配置

```python
class Item(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,    # 自动去除首尾空格
        str_to_lower=True,             # 字符串转小写
        validate_assignment=True,      # 赋值时也验证
        extra="forbid",                # 禁止额外字段
    )

    name: str
    price: float
```

### 字段别名

```python
class User(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,         # 允许用原名赋值
    )

    name: str = Field(alias="userName")
    email: str = Field(alias="userEmail")

# JSON 中: {"userName": "Alice", "userEmail": "a@b.com"}
```

### 排除字段

```python
class User(BaseModel):
    name: str
    email: str
    password: str = Field(exclude=True)   # 序列化时排除

user = User(name="Alice", email="a@b.com", password="secret")
print(user.model_dump())  # {"name": "Alice", "email": "a@b.com"}
```

---

## 6. 请求体特殊类型

### 多个请求体参数

```python
@app.put("/items/{item_id}")
def update_item(
    item_id: int,
    item: Item,              # 请求体 1
    user: User,              # 请求体 2（自动包装为 key）
    importance: int = Body(...),  # 单个 Body 参数
):
    return {
        "item_id": item_id,
        "item": item,
        "user": user,
        "importance": importance,
    }
```

### 嵌入单个 Body 参数

```python
@app.put("/items/{item_id}")
def update_item(
    item_id: int,
    item: Item = Body(embed=True),   # 嵌入为 {"item": {...}}
):
    ...
```

### Body 中的 Field

```python
class Item(BaseModel):
    name: str
    description: str | None = Field(
        None,
        title="描述",
        max_length=300,
    )
```

---

## 实战练习

### 练习 1：用户注册接口

```python
from pydantic import BaseModel, Field, EmailStr, field_validator
from fastapi import FastAPI

app = FastAPI()


class UserRegister(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_]+$",
    )
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str
    age: int = Field(..., ge=13, le=120)
    bio: str | None = Field(None, max_length=500)

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

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("两次输入的密码不一致")
        return v


@app.post("/register")
def register(user: UserRegister):
    return {
        "message": "注册成功",
        "username": user.username,
        "email": user.email,
    }
```

### 练习 2：测试验证错误

用 Swagger UI 测试以下错误场景：
1. 用户名少于 3 个字符
2. 密码没有大写字母
3. 两次密码不一致
4. 年龄小于 13
5. 邮箱格式错误

---

## 今日总结

- [ ] Pydantic `BaseModel` 定义数据结构，自动验证
- [ ] `Field()` 提供字段级验证约束
- [ ] `@field_validator` 自定义字段验证逻辑
- [ ] `@model_validator` 模型级别验证
- [ ] 嵌套模型表示复杂数据结构
- [ ] `ConfigDict` 配置模型行为
- [ ] FastAPI 自动将请求 JSON 解析为 Pydantic 模型
- [ ] 验证失败自动返回 422 错误和详细信息

---

*第 41 天 / 330 天*
*第二阶段：Web 框架与 API - Pydantic 模型*
