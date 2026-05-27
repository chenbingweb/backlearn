# 第 49 天：数据库集成 SQLAlchemy

## 学习目标

- 了解 SQLAlchemy 的基本架构
- 掌握 ORM 模型定义
- 学会 CRUD 操作
- 理解 Session 与事务

---

## 1. SQLAlchemy 简介

### 两种使用方式

| 方式 | 说明 |
|------|------|
| ORM | 对象关系映射，用 Python 对象操作数据库 |
| Core | 纯 SQL 表达式，底层控制更精细 |

### 安装

```bash
pip install sqlalchemy
# 或完整版（包含异步支持）
pip install sqlalchemy[asyncio] aiosqlite
```

---

## 2. 数据库连接

### 连接字符串

```python
# SQLite
DATABASE_URL = "sqlite:///./app.db"
DATABASE_URL = "sqlite:///:memory:"  # 内存数据库

# PostgreSQL
DATABASE_URL = "postgresql://user:pass@localhost/dbname"

# MySQL
DATABASE_URL = "mysql+pymysql://user:pass@localhost/dbname"
```

### 创建 Engine

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 专用
    echo=True,  # 打印 SQL（开发用）
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 3. 定义模型

### Base 类

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 创建表

```python
from app.database import engine, Base

# 创建所有表
Base.metadata.create_all(bind=engine)

# 删除所有表
Base.metadata.drop_all(bind=engine)
```

### Alembic 迁移（推荐）

```bash
pip install alembic

# 初始化
alembic init alembic

# 生成迁移
alembic revision --autogenerate -m "create users table"

# 应用迁移
alembic upgrade head
```

---

## 4. CRUD 操作

### 创建

```python
from app.models import User
from app.database import SessionLocal

db = SessionLocal()

# 方式 1
user = User(username="alice", email="alice@example.com", hashed_password="xxx")
db.add(user)
db.commit()
db.refresh(user)  # 刷新，获取数据库生成的值

# 方式 2：批量创建
users = [
    User(username="alice", email="alice@example.com", hashed_password="xxx"),
    User(username="bob", email="bob@example.com", hashed_password="yyy"),
]
db.add_all(users)
db.commit()
```

### 读取

```python
# 获取一个
user = db.query(User).filter(User.id == 1).first()
user = db.query(User).filter(User.username == "alice").first()
user = db.query(User).filter(User.email.in_(["a@b.com", "c@d.com"])).first()

# 获取所有
users = db.query(User).all()

# 条件查询
users = db.query(User).filter(User.is_active == True).all()
users = db.query(User).filter(User.username.like("a%")).all()

# 排序
users = db.query(User).order_by(User.created_at.desc()).all()

# 分页
users = db.query(User).offset(0).limit(10).all()
```

### 更新

```python
user = db.query(User).filter(User.id == 1).first()
user.username = "new_username"
user.email = "new@example.com"
db.commit()
```

### 删除

```python
user = db.query(User).filter(User.id == 1).first()
db.delete(user)
db.commit()
```

---

## 5. 关系定义

### 一对多

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True)

    # 关系
    articles = relationship("Article", back_populates="author")


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"))

    # 关系
    author = relationship("User", back_populates="articles")
```

### 一对一

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    profile = relationship("Profile", back_populates="user", uselist=False)


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    bio = Column(String(500))

    user = relationship("User", back_populates="profile")
```

### 多对多

```python
# 中间表
article_tags = Table(
    "article_tags",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    title = Column(String(200))

    tags = relationship("Tag", secondary=article_tags, back_populates="articles")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    articles = relationship("Article", secondary=article_tags, back_populates="tags")
```

---

## 实战练习

### 练习：完整的用户模型

```python
# app/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    articles = relationship("Article", back_populates="author")


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(String, nullable=False)
    published = Column(Boolean, default=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User", back_populates="articles")
```

---

## 今日总结

- [ ] SQLAlchemy 提供 ORM 和 Core 两种方式
- [ ] `create_engine` 创建数据库连接
- [ ] `declarative_base` 定义模型基类
- [ ] `Column` 定义字段，`relationship` 定义关系
- [ ] `Session` 管理事务，`db.commit()` 提交
- [ ] `query().filter().first()` 查询单条
- [ ] `query().all()` 查询多条

---

*第 49 天 / 330 天*
*第二阶段：FastAPI 进阶 - SQLAlchemy*