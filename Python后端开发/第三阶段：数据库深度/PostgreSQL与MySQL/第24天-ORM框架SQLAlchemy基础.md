# 第 24 天：ORM 框架 SQLAlchemy 基础

## 学习目标

- 理解 ORM 概念
- 掌握 SQLAlchemy 使用
- 学会模型定义
- 掌握基本 CRUD 操作

---

## 1. ORM 概念

### 什么是 ORM

```
ORM（Object-Relational Mapping）
对象-关系映射

┌─────────────┐         ┌─────────────┐
│   Python    │  ORM     │   Database  │
│   Objects   │ <────--> │   Tables    │
│             │          │             │
│  User(id=1) │          │  users(id=1)│
│    .name    │          │  name       │
│    .email   │          │  email      │
└─────────────┘          └─────────────┘

优点：
- 不用写 SQL
- 类型安全
- 可移植（换数据库只需改配置）
- 自动防止 SQL 注入

缺点：
- 复杂查询性能差
- 学习成本
- 灵活度低于 SQL
```

---

## 2. SQLAlchemy 架构

### 核心组件

```
┌─────────────────────────────────────────┐
│              SQLAlchemy                 │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │      ORM (Object Relational)    │   │
│  │  - Session                       │   │
│  │  - Mapper                        │   │
│  │  - Query                         │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   Core (Expression Language)    │   │
│  │  - Table                         │   │
│  │  - Column                        │   │
│  │  - Select/Insert/Update/Delete   │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │      Engine / Connection        │   │
│  │  - Connection Pool               │   │
│  │  - Dialect (PostgreSQL/MySQL)   │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

---

## 3. 安装和配置

### 安装

```bash
pip install sqlalchemy
pip install psycopg2-binary    # PostgreSQL
pip install pymysql            # MySQL
```

### 数据库连接

```python
from sqlalchemy import create_engine

# PostgreSQL
engine = create_engine(
    "postgresql://user:password@localhost:5432/mydb",
    echo=True,  # 打印 SQL
    pool_size=10,
    max_overflow=20
)

# MySQL
engine = create_engine(
    "mysql+pymysql://user:password@localhost:3306/mydb?charset=utf8mb4",
    echo=True,
    pool_size=10
)

# SQLite（测试用）
engine = create_engine(
    "sqlite:///./test.db",
    echo=True
)

# 连接参数
engine = create_engine(
    "postgresql://user:password@localhost:5432/mydb",
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,    # 连接前检测
    pool_recycle=3600,     # 连接回收时间
)
```

---

## 4. 模型定义

### 基本模型

```python
from sqlalchemy import (
    Column, Integer, String, Boolean,
    DateTime, Date, Text, Numeric,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 表级约束
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_username', 'username'),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
```

### 关系定义

```python
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    # ... 其他字段

    # 一对多关系
    orders = relationship('Order', back_populates='user')

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    total_amount = Column(Numeric(10, 2), default=0)

    # 反向引用
    user = relationship('User', back_populates='orders')
```

### 复杂关系

```python
class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    parent_id = Column(Integer, ForeignKey('categories.id'))

    # 自引用关系
    parent = relationship('Category', remote_side=[id], backref='children')
    products = relationship('Product', back_populates='category')

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))

    category = relationship('Category', back_populates='products')
    order_items = relationship('OrderItem', back_populates='product')

class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer, default=1)

    order = relationship('Order', back_populates='items')
    product = relationship('Product', back_populates='order_items')
```

### 创建表

```python
from sqlalchemy.orm import sessionmaker

# 创建引擎
engine = create_engine("sqlite:///./test.db", echo=True)

# 创建所有表
Base.metadata.create_all(engine)

# 删除所有表
Base.metadata.drop_all(engine)

# 创建 Session
Session = sessionmaker(bind=engine)
session = Session()
```

---

## 5. 基本 CRUD

### Create（插入）

```python
# 方式 1：直接创建对象
user = User(
    username='alice',
    email='alice@example.com',
    password_hash='hashed_password'
)
session.add(user)
session.commit()

# 方式 2：批量插入
users = [
    User(username='user1', email='user1@example.com', password_hash='hash1'),
    User(username='user2', email='user2@example.com', password_hash='hash2'),
    User(username='user3', email='user3@example.com', password_hash='hash3'),
]
session.add_all(users)
session.commit()

# 方式 3：flush 获取 ID
session.add(user)
session.flush()  # 此时 user.id 已生成，但未 commit
print(user.id)
session.commit()
```

### Read（查询）

```python
# 获取一条
user = session.query(User).filter(User.id == 1).first()
user = session.query(User).filter_by(id=1).first()

# 获取全部
users = session.query(User).all()

# 条件查询
users = session.query(User).filter(User.is_active == True).all()
users = session.query(User).filter(User.email.like('%@example.com')).all()

# 排序
users = session.query(User).order_by(User.created_at.desc()).all()

# 分页
users = session.query(User).limit(10).offset(20).all()

# 聚合查询
from sqlalchemy import func

count = session.query(func.count(User.id)).scalar()
avg_amount = session.query(func.avg(Order.total_amount)).scalar()

# 分组
from sqlalchemy import func
results = session.query(
    User.status,
    func.count(User.id)
).group_by(User.status).all()
```

### Update（更新）

```python
# 方式 1：修改对象属性
user = session.query(User).filter(User.id == 1).first()
user.email = 'new_email@example.com'
session.commit()

# 方式 2：批量更新
session.query(User).filter(User.is_active == False).update(
    {'is_active': True}
)
session.commit()

# 方式 3：使用 SQL 表达式
from sqlalchemy import update
stmt = update(User).where(User.id == 1).values(email='new@example.com')
session.execute(stmt)
session.commit()
```

### Delete（删除）

```python
# 删除单个对象
user = session.query(User).filter(User.id == 1).first()
session.delete(user)
session.commit()

# 批量删除
session.query(User).filter(User.created_at < '2024-01-01').delete()
session.commit()

# 使用 SQL
from sqlalchemy import delete
stmt = delete(User).where(User.id.in_([1, 2, 3]))
session.execute(stmt)
session.commit()
```

---

## 6. 查询表达式

### 常用过滤

```python
from sqlalchemy import and_, or_, not_

# AND
session.query(User).filter(
    and_(User.is_active == True, User.email.like('%@example.com'))
).all()

# 简化写法
session.query(User).filter(
    User.is_active == True,
    User.email.like('%@example.com')
).all()

# OR
session.query(User).filter(
    or_(User.id == 1, User.id == 2)
).all()

# NOT
session.query(User).filter(
    not_(User.is_active == True)
).all()

# IN
session.query(User).filter(User.id.in_([1, 2, 3])).all()

# BETWEEN
session.query(Order).filter(
    Order.total_amount.between(100, 500)
).all()

# LIKE
session.query(User).filter(User.email.like('%@gmail.com')).all()

# IS NULL / IS NOT NULL
session.query(User).filter(User.phone.is_(None)).all()
session.query(User).filter(User.phone.isnot(None)).all()
```

### 字符串操作

```python
# 字符串函数
from sqlalchemy import func

session.query(
    func.upper(User.username)
).all()

session.query(
    func.length(User.username)
).all()

session.query(
    func.substring(User.email, 1, 5)
).all()
```

### 日期操作

```python
from sqlalchemy import extract

# 提取年
session.query(Order).filter(
    extract('year', Order.created_at) == 2024
).all()

# 提取月
session.query(Order).filter(
    extract('month', Order.created_at) == 1
).all()
```

---

## 7. 实战练习

### 完整示例

```python
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timedelta

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship('Order', back_populates='user')

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    order_no = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    total_amount = Column(Numeric(10, 2), default=0)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='orders')

    def __repr__(self):
        return f"<Order(id={self.id}, order_no='{self.order_no}')>"

# 创建引擎和会话
engine = create_engine('sqlite:///./ecommerce.db', echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# 创建用户
user = User(username='alice', email='alice@example.com', password_hash='hash123')
session.add(user)
session.commit()

# 创建订单
for i in range(5):
    order = Order(
        order_no=f'ORD{user.id}{i:04d}',
        user_id=user.id,
        total_amount=(i + 1) * 100,
        status='completed' if i < 3 else 'pending'
    )
    session.add(order)
session.commit()

# 查询用户及其订单
user = session.query(User).filter(User.username == 'alice').first()
print(f"User: {user.username}, Orders: {len(user.orders)}")

# 查询统计
from sqlalchemy import func
stats = session.query(
    User.username,
    func.count(Order.id).label('order_count'),
    func.sum(Order.total_amount).label('total_spent')
).join(Order).group_by(User.username).all()

for username, count, total in stats:
    print(f"{username}: {count} orders, ${total or 0}")

session.close()
```

---

## 今日总结

- [ ] ORM：将数据库表映射为 Python 对象
- [ ] SQLAlchemy：Engine、Session、Model
- [ ] 模型定义：继承 `Base`，定义 `__tablename__`
- [ ] CRUD：`session.add()`、`query.filter()`、`commit()`
- [ ] 关系：`relationship`、`back_populates`
- [ ] 查询：`func.count`、`func.sum`、分组聚合

---

*第 24 天 / 330 天*
*Python 后端 - ORM 框架 SQLAlchemy 基础*
