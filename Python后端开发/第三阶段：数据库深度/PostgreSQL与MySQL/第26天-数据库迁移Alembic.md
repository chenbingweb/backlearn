# 第 26 天：数据库迁移 Alembic

## 学习目标

- 理解数据库迁移概念
- 掌握 Alembic 使用
- 学会版本管理
- 掌握数据迁移脚本

---

## 1. Alembic 简介

### 什么是 Alembic

```
Alembic - SQLAlchemy 数据库迁移工具

┌─────────────────────────────────────────┐
│              Alembic                    │
├─────────────────────────────────────────┤
│                                          │
│  migrations/                            │
│    ├── versions/                        │
│    │   ├── 001_initial.py               │
│    │   ├── 002_add_users.py             │
│    │   └── 003_add_orders.py            │
│    └── env.py                           │
│                                          │
│  alembic.ini                            │
│                                          │
└─────────────────────────────────────────┘

特点：
- 版本化管理数据库变更
- 支持回滚
- 自动生成迁移脚本
- 可自定义
```

---

## 2. 安装和配置

### 安装

```bash
pip install alembic
```

### 初始化

```bash
# 在项目目录初始化
alembic init migrations

# 目录结构
# alembic.ini          - 配置文件
# migrations/          - 迁移目录
# ├── env.py          - 环境配置
# ├── script.py.mako   - 脚本模板
# └── versions/        - 版本文件
```

### 配置 env.py

```python
# migrations/env.py

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# 导入你的模型
from sqlalchemy import create_engine
from models import Base  # 你的模型基类

# Alembic Config 对象
config = context.config

# 设置数据库 URL
config.set_main_option(
    'sqlalchemy.url',
    'postgresql://user:pass@localhost/mydb'
)

# 解释配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """运行离线模式（生成 SQL 但不连接数据库）"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """运行在线模式（直接连接数据库）"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 配置 alembic.ini

```ini
# alembic.ini

[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os

sqlalchemy.url = postgresql://user:pass@localhost/mydb

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic
```

---

## 3. 基本命令

### 生成迁移

```bash
# 自动生成（检测模型变化）
alembic revision --autogenerate -m "add users table"

# 手动生成
alembic revision -m "add users table"
```

### 执行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade +2

# 降级到上一个版本
alembic downgrade -1

# 降级到初始版本
alembic downgrade base

# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 查看详细信息
alembic history --verbose
```

### 其他命令

```bash
# 检查是否有待执行迁移
alembic check

# 生成 SQL 脚本（不执行）
alembic upgrade head --sql > migration.sql

# 合并迁移
alembic merge head "merge point"
```

---

## 4. 迁移脚本编写

### 自动生成脚本

```python
# migrations/versions/001_initial.py

"""add users table

Revision ID: abc123
Revises:
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'abc123'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.create_index('ix_users_username', 'users', ['username'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
```

### 手动编写迁移

```python
# migrations/versions/002_add_orders.py

"""add orders table

Revision ID: def456
Revises: abc123
Create Date: 2024-01-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'def456'
down_revision = 'abc123'  # 依赖上一个版本
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_no', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_no')
    )
    op.create_index('ix_orders_user_id', 'orders', ['user_id'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_orders_user_id', table_name='orders')
    op.drop_table('orders')
```

---

## 5. 常见操作

### 添加列

```python
def upgrade() -> None:
    # 添加新列
    op.add_column('users', sa.Column('phone', sa.String(length=20), nullable=True))

    # 添加带默认值的列（PostgreSQL）
    op.add_column('users', sa.Column('status', sa.String(length=20), server_default='active'))

def downgrade() -> None:
    op.drop_column('users', 'phone')
```

### 删除列

```python
def upgrade() -> None:
    op.drop_column('users', 'phone')

def downgrade() -> None:
    op.add_column('users', sa.Column('phone', sa.String(length=20), nullable=True))
```

### 修改列

```python
def upgrade() -> None:
    # 修改类型
    op.alter_column('users', 'phone', type_=sa.String(length=30))

    # 修改默认值
    op.alter_column('users', 'status', server_default='inactive')

    # 修改 nullable
    op.alter_column('users', 'email', nullable=False)

def downgrade() -> None:
    op.alter_column('users', 'phone', type_=sa.String(length=20))
    op.alter_column('users', 'status', server_default=None)
    op.alter_column('users', 'email', nullable=True)
```

### 添加约束

```python
def upgrade() -> None:
    # 添加外键
    op.create_foreign_key(
        'fk_orders_user',
        'orders', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )

    # 添加唯一约束
    op.create_unique_constraint('uq_users_email', 'users', ['email'])

    # 添加检查约束
    op.create_check_constraint(
        'ck_orders_amount_positive',
        'orders',
        'total_amount > 0'
    )

def downgrade() -> None:
    op.drop_constraint('fk_orders_user', 'orders', type_='foreignkey')
    op.drop_constraint('uq_users_email', 'users', type_='unique')
    op.drop_constraint('ck_orders_amount_positive', 'orders')
```

### 数据迁移

```python
def upgrade() -> None:
    # 创建新表
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        # ...
    )

    # 迁移数据
    op.execute("""
        INSERT INTO user_profiles (user_id, bio)
        SELECT id, NULLIF(bio, '') FROM users WHERE bio IS NOT NULL
    """)

    # 删除旧列
    op.drop_column('users', 'bio')

def downgrade() -> None:
    # 恢复数据
    op.execute("""
        UPDATE users SET bio = (SELECT bio FROM user_profiles WHERE user_profiles.user_id = users.id)
    """)
    op.drop_table('user_profiles')
```

---

## 6. Python API 使用

### 在代码中运行迁移

```python
from alembic.config import Config
from alembic import command

# 创建配置
alembic_cfg = Config("alembic.ini")

# 执行迁移
command.upgrade(alembic_cfg, "head")

# 回滚
command.downgrade(alembic_cfg, "-1")

# 生成迁移
command.revision(alembic_cfg, message="add products", autogenerate=True)
```

### 集成到应用

```python
# app.py
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine

def init_db():
    """初始化数据库"""
    engine = create_engine('postgresql://user:pass@localhost/mydb')

    # 运行所有迁移
    alembic_cfg = Config('alembic.ini')
    command.upgrade(alembic_cfg, 'head')

# 或者在启动时检查
def on_startup():
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config('alembic.ini')
    command.check(alembic_cfg)  # 检查是否有待执行迁移
    command.upgrade(alembic_cfg, 'head')
```

---

## 7. 实战练习

### 多数据库迁移

```python
# migrations/env.py

def run_migrations_online() -> None:
    """多数据库配置"""
    # 主库
    main_config = config.get_section(config.config_ini_section)
    main_config['sqlalchemy.url'] = 'postgresql://user:pass@localhost/maindb'

    # 从库（只读）
    # 可以为不同连接执行相同迁移

    connectable = engine_from_config(
        main_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()
```

### 分支管理

```bash
# 创建分支
alembic revision -m "add feature" --branch-label=feature

# 查看分支
alembic branches

# 合并分支到主支
alembic merge head "merge-feature" --branch-label=feature
```

---

## 今日总结

- [ ] Alembic：SQLAlchemy 的数据库迁移工具
- [ ] `alembic init` 初始化，`alembic revision` 创建迁移
- [ ] `alembic upgrade head` 升级，`alembic downgrade` 降级
- [ ] `--autogenerate` 自动检测模型变化
- [ ] 迁移脚本：upgrade() 和 downgrade()
- [ ] 可添加列、删除列、添加约束、迁移数据
- [ ] `alembic history` 查看历史，`alembic current` 查看当前版本

---

*第 26 天 / 330 天*
*Python 后端 - 数据库迁移 Alembic*
