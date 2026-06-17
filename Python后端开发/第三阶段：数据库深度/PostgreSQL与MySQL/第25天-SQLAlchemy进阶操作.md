# 第 25 天：SQLAlchemy 进阶操作

## 学习目标

- 掌握高级查询技巧
- 学会关联查询
- 掌握事务和批量操作
- 理解性能优化

---

## 1. 高级查询

### 链式调用

```python
# 链式查询
users = (
    session.query(User)
    .filter(User.is_active == True)
    .filter(User.email.like('%@example.com'))
    .order_by(User.created_at.desc())
    .limit(10)
    .all()
)

# 分页
def get_users_page(page=1, page_size=20):
    offset = (page - 1) * page_size
    return (
        session.query(User)
        .order_by(User.id)
        .limit(page_size)
        .offset(offset)
        .all()
    )
```

### 子查询

```python
from sqlalchemy import func, select

# 标量子查询
subquery = (
    session.query(func.count(Order.id))
    .filter(Order.user_id == User.id)
    .scalar_subquery()
)

users = session.query(
    User.id,
    User.username,
    subquery.label('order_count')
).all()

# 表子查询
from sqlalchemy import literal_column

subquery = (
    session.query(
        Order.user_id,
        func.sum(Order.total_amount).label('total')
    )
    .group_by(Order.user_id)
    .subquery()
)

results = session.query(
    User.username,
    subquery.c.total
).join(subquery, User.id == subquery.c.user_id).all()
```

### CTE（公用表表达式）

```python
from sqlalchemy import cte

# CTE 查询
orders_cte = (
    session.query(
        Order.user_id,
        func.count(Order.id).label('order_count'),
        func.sum(Order.total_amount).label('total_amount')
    )
    .where(Order.status == 'completed')
    .group_by(Order.user_id)
    .cte('order_stats')
)

results = (
    session.query(
        User.username,
        orders_cte.c.order_count,
        orders_cte.c.total_amount
    )
    .join(orders_cte, User.id == orders_cte.c.user_id)
    .all()
)
```

### 窗口函数

```python
from sqlalchemy import func, over, Window

# ROW_NUMBER
subquery = (
    session.query(
        User.username,
        func.row_number().over(partition_by=User.status, order_by=User.created_at.desc()).label('rn')
    ).subquery()
)

results = session.query(subquery).filter(subquery.c.rn <= 5).all()

# LAG
subquery = (
    session.query(
        Order.user_id,
        Order.created_at,
        Order.total_amount,
        func.lag(Order.total_amount).over(
            partition_by=Order.user_id,
            order_by=Order.created_at
        ).label('prev_amount')
    ).subquery()
)

# 计算增长
results = session.query(
    Order.user_id,
    Order.total_amount,
    (Order.total_amount - func.coalesce(subquery.c.prev_amount, 0)).label('growth')
).all()
```

---

## 2. 关联查询

### JOIN 操作

```python
# INNER JOIN
results = (
    session.query(User.username, Order.order_no)
    .join(Order, User.id == Order.user_id)
    .all()
)

# LEFT JOIN
results = (
    session.query(User.username, Order.order_no)
    .outerjoin(Order, User.id == Order.user_id)
    .all()
)

# 多表 JOIN
results = (
    session.query(
        User.username,
        Order.order_no,
        OrderItem.quantity,
        Product.name
    )
    .join(Order, User.id == Order.user_id)
    .join(OrderItem, Order.id == OrderItem.order_id)
    .join(Product, OrderItem.product_id == Product.id)
    .filter(Order.status == 'completed')
    .all()
)
```

### 预加载（Eager Loading）

```python
from sqlalchemy.orm import selectinload, joinedload, subqueryload

# 问题：N+1 查询
# user = session.query(User).first()
# for order in user.orders:  # 每条记录触发一次查询

# 解决方案 1：joinedload（自动 JOIN）
user = (
    session.query(User)
    .options(joinedload(User.orders))
    .filter(User.id == 1)
    .first()
)
# user.orders 已加载，不会再查询

# 解决方案 2：selectinload（独立查询）
users = (
    session.query(User)
    .options(selectinload(User.orders))
    .limit(10)
    .all()
)
# 为所有用户一次性加载订单

# 解决方案 3：子查询
users = (
    session.query(User)
    .options(subqueryload(User.orders))
    .all()
)
```

### 延迟加载控制

```python
# lazy 参数控制关系加载方式
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    orders = relationship('Order', lazy='select')      # 默认：延迟加载
    orders = relationship('Order', lazy='joined')      # 自动 JOIN
    orders = relationship('Order', lazy='selectin')    # 独立查询
    orders = relationship('Order', lazy='subquery')    # 子查询
    orders = relationship('Order', lazy='dynamic')      # 返回查询对象
```

---

## 3. 事务控制

### 基本事务

```python
from sqlalchemy.exc import SQLAlchemyError

def transfer_funds(from_user_id, to_user_id, amount):
    try:
        # 开启事务
        with session.begin():
            # 扣款
            from_user = session.query(User).filter(User.id == from_user_id).with_for_update().first()
            if from_user.balance < amount:
                raise ValueError("余额不足")

            from_user.balance -= amount

            # 收款
            to_user = session.query(User).filter(User.id == to_user_id).with_for_update().first()
            to_user.balance += amount

        # 提交（自动）
        return True
    except SQLAlchemyError as e:
        session.rollback()
        raise e

# 使用 with session.begin() 自动 commit/rollback
```

### 行级锁

```python
# SELECT ... FOR UPDATE
user = (
    session.query(User)
    .filter(User.id == 1)
    .with_for_update()
    .first()
)

# 锁定多行
users = (
    session.query(User)
    .filter(User.id.in_([1, 2, 3]))
    .with_for_update()
    .all()
)

# 指定锁模式
from sqlalchemy import update

stmt = (
    update(Order)
    .where(Order.id == order_id)
    .values(status='paid')
    .returning(Order.id, Order.status)
)
result = session.execute(stmt)
```

### 保存点

```python
# 使用保存点
session.begin_nested()  # 创建保存点
try:
    # 执行操作
    session.add(Order(...))
    session.flush()

    # 嵌套事务回滚
    session.rollback nested_savepoint
except:
    session.rollback(nested_savepoint)
    # 外层事务继续

# 或者使用 savepoint
savepoint = session.begin_nested()
try:
    # 操作
    session.commit()
except:
    savepoint.rollback()
```

---

## 4. 批量操作

### 批量插入

```python
from sqlalchemy.dialects.postgresql import insert

# 方式 1：add_all + bulk_save_objects
users = [User(username=f'user{i}', email=f'user{i}@example.com') for i in range(1000)]
session.bulk_save_objects(users)
session.commit()

# 方式 2：insert from select
from sqlalchemy import insert
stmt = insert(User).from_select(
    ['username', 'email'],
    session.query(User.username, User.email).filter(User.id > 100)
)
session.execute(stmt)
session.commit()

# 方式 3：PostgreSQL INSERT ... ON CONFLICT
from sqlalchemy.dialects.postgresql import insert as pg_insert

stmt = pg_insert(User).values([
    {'username': 'alice', 'email': 'alice@example.com'},
    {'username': 'bob', 'email': 'bob@example.com'},
])
stmt = stmt.on_conflict_do_update(
    index_elements=['username'],
    set_={'email': stmt.excluded.email}
)
session.execute(stmt)
session.commit()
```

### 批量更新

```python
# 方式 1：update where
session.query(User).filter(User.status == 'inactive').update(
    {'is_active': False, 'updated_at': datetime.utcnow()}
)
session.commit()

# 方式 2：case when
from sqlalchemy import case

session.query(User).update(
    {User.level: case(
        (User.points > 10000, 'Platinum'),
        (User.points > 5000, 'Gold'),
        (User.points > 1000, 'Silver'),
        else_='Bronze'
    )}
)
session.commit()

# 方式 3：批量更新多个字段
session.execute(
    update(User)
    .where(User.id.in_(user_ids))
    .values(
        status='active',
        updated_at=datetime.utcnow()
    )
)
session.commit()
```

---

## 5. 复杂映射

### 多对多关系

```python
# 定义多对多关系
from sqlalchemy import Table, Column, Integer, ForeignKey

order_product = Table(
    'order_products',
    Base.metadata,
    Column('order_id', Integer, ForeignKey('orders.id'), primary_key=True),
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True)
)

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    products = relationship('Product', secondary=order_product, back_populates='orders')

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    orders = relationship('Order', secondary=order_product, back_populates='products')

# 使用
order = session.query(Order).filter(Order.id == 1).first()
order.products.append(Product(name='New Product'))
session.commit()
```

### 继承映射

```python
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Person(Base):
    __tablename__ = 'persons'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    email = Column(String(100))

class Employee(Person):
    __tablename__ = 'employees'
    id = Column(Integer, ForeignKey('persons.id'), primary_key=True)
    salary = Column(Numeric(10, 2))
    department = Column(String(50))

# 单表继承
class Customer(Person):
    __tablename__ = 'customers'
    id = Column(Integer, ForeignKey('persons.id'), primary_key=True)
    credit_limit = Column(Numeric(10, 2))
    customer_type = Column(String(20))

    __mapper_args__ = {
        'polymorphic_identity': 'customer',
        'concrete': True  # 具体表继承
    }
```

---

## 6. 性能优化

### 查询优化

```python
# 1. 只查询需要的列
result = session.query(
    User.id, User.username, User.email
).filter(User.is_active == True).all()

# 2. 使用 exists 而非 IN
from sqlalchemy import exists
has_orders = session.query(
    exists().where(Order.user_id == User.id)
).scalar()

# 3. 分段处理大数据
BATCH_SIZE = 1000
offset = 0
while True:
    batch = session.query(User).limit(BATCH_SIZE).offset(offset).all()
    if not batch:
        break
    process_users(batch)
    session.expire_all()  # 清除缓存
    offset += BATCH_SIZE
```

### 连接池配置

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "postgresql://user:pass@localhost/mydb",
    poolclass=QueuePool,
    pool_size=10,           # 基础连接数
    max_overflow=20,        # 最大溢出
    pool_pre_ping=True,     # 连接检测
    pool_recycle=3600,      # 连接回收
    pool_timeout=30,         # 获取连接超时
    echo_pool=True          # 打印连接池日志
)
```

---

## 7. 实战练习

### 完整 CRUD 封装

```python
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Numeric
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
from contextlib import contextmanager

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@contextmanager
def get_session():
    """上下文管理器，自动管理 session"""
    engine = create_engine('sqlite:///./app.db', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

class ProductRepository:
    """产品仓储"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, name: str, price: float, stock: int = 0) -> Product:
        product = Product(name=name, price=price, stock=stock)
        self.session.add(product)
        self.session.flush()
        return product

    def get_by_id(self, product_id: int) -> Product:
        return self.session.query(Product).filter(Product.id == product_id).first()

    def get_all(self, limit: int = 100, offset: int = 0):
        return (
            self.session.query(Product)
            .order_by(Product.id)
            .limit(limit)
            .offset(offset)
            .all()
        )

    def update_stock(self, product_id: int, quantity_change: int) -> bool:
        product = self.get_by_id(product_id)
        if not product:
            return False
        new_stock = product.stock + quantity_change
        if new_stock < 0:
            raise ValueError("库存不足")
        product.stock = new_stock
        return True

    def delete(self, product_id: int) -> bool:
        product = self.get_by_id(product_id)
        if not product:
            return False
        self.session.delete(product)
        return True

# 使用
with get_session() as session:
    repo = ProductRepository(session)

    # 创建
    product = repo.create("iPhone", 9999.00, 100)

    # 查询
    p = repo.get_by_id(1)
    print(f"Product: {p.name}, Price: {p.price}")

    # 更新库存
    repo.update_stock(1, -5)

    # 删除
    repo.delete(2)
```

---

## 今日总结

- [ ] 子查询和 CTE：`scalar_subquery()`、`cte()`
- [ ] 窗口函数：`over()`、`row_number()`、`lag()`
- [ ] JOIN：`join()`、`outerjoin()`、`joinedload()`
- [ ] 预加载：`selectinload`、`subqueryload`
- [ ] 事务：`session.begin()`、`with_for_update()`
- [ ] 批量操作：`bulk_save_objects`、批量 INSERT/UPDATE
- [ ] 性能优化：按需查询字段、分段处理

---

*第 25 天 / 330 天*
*Python 后端 - SQLAlchemy 进阶操作*
