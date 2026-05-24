# 第 30 天：pip / pipenv / poetry 依赖管理

## 学习目标

- 掌握 pip 的高级用法
- 了解 pipenv 的工作流
- 学会使用 poetry 管理依赖
- 理解依赖锁定的重要性

---

## 1. pip 进阶

### 安装指定版本

```bash
pip install requests==2.28.1          # 精确版本
pip install requests>=2.25,<3.0       # 版本范围
pip install requests~=2.28.0          # 兼容版本（>=2.28.0,<2.29）
```

### 从各种源安装

```bash
# 从 requirements.txt
pip install -r requirements.txt

# 从 Git 仓库
pip install git+https://github.com/user/repo.git

# 从本地目录（可编辑安装）
pip install -e ./my_package

# 从 wheel 文件
pip install ./package-1.0-py3-none-any.whl
```

### 其他常用命令

```bash
pip list                    # 列出已安装包
pip show requests           # 查看包详情
pip uninstall requests      # 卸载
pip install --upgrade requests   # 升级
pip check                   # 检查依赖冲突
pip cache purge             # 清理缓存
```

---

## 2. requirements.txt 格式

```txt
# 精确版本
requests==2.28.1

# 版本范围
flask>=2.0,<3.0

# 可选依赖标记
requests[security]>=2.25

# 开发依赖（手动注释标记）
pytest==7.4.0       # dev
black==23.0.0       # dev
```

### 分离依赖

```txt
# requirements.txt（生产依赖）
flask==2.3.0
requests==2.28.1

# requirements-dev.txt（开发依赖，包含生产）
-r requirements.txt
pytest==7.4.0
black==23.0.0
mypy==1.0.0
```

---

## 3. pipenv

### 特点

- 自动管理虚拟环境
- 同时维护 `Pipfile`（依赖）和 `Pipfile.lock`（锁定版本）
- 取代 requirements.txt

### 基本用法

```bash
# 安装 pipenv
pip install pipenv

# 进入项目目录
 cd my_project

# 安装包（自动创建虚拟环境）
pipenv install requests

# 安装开发依赖
pipenv install pytest --dev

# 激活虚拟环境
pipenv shell

# 运行命令（不进入 shell）
pipenv run python app.py

# 从 Pipfile 安装所有依赖
pipenv install

# 生成 requirements.txt（兼容）
pipenv requirements > requirements.txt
```

### Pipfile

```toml
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
requests = "==2.28.1"
flask = "==2.3.0"

[dev-packages]
pytest = "==7.4.0"

[requires]
python_version = "3.11"
```

---

## 4. poetry（推荐）

### 特点

- 现代依赖管理 + 打包发布一体化
- 精确的依赖解析
- 更快的锁定文件生成
- `pyproject.toml` 标准格式

### 安装

```bash
# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# 验证
poetry --version
```

### 基本用法

```bash
# 创建新项目
poetry new my_project

# 或初始化现有项目
poetry init

# 添加依赖
poetry add requests
poetry add pytest --group dev

# 安装所有依赖（从 pyproject.toml + poetry.lock）
poetry install

# 激活虚拟环境
poetry shell

# 运行命令
poetry run python app.py

# 更新依赖
poetry update

# 导出 requirements.txt
poetry export -f requirements.txt --output requirements.txt
```

### pyproject.toml

```toml
[tool.poetry]
name = "my-project"
version = "0.1.0"
description = ""
authors = ["Your Name <you@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
requests = "^2.28.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
black = "^23.0.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

---

## 5. 三种工具对比

| 特性 | pip + venv | pipenv | poetry |
|------|-----------|--------|--------|
| 依赖文件 | requirements.txt | Pipfile + Pipfile.lock | pyproject.toml + poetry.lock |
| 虚拟环境 | 手动管理 | 自动管理 | 自动管理 |
| 依赖解析 | 基本 | 较好 | 精确 |
| 打包发布 | 需 setuptools | 不支持 | 内置支持 |
| 速度 | 快 | 慢 | 中等 |
| 推荐度 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 实战练习

### 练习 1：用 poetry 管理项目

```bash
# 1. 创建项目
poetry new todo_app
cd todo_app

# 2. 添加依赖
poetry add click
poetry add pytest --group dev

# 3. 查看结构
cat pyproject.toml

# 4. 安装并运行
poetry install
poetry run python -c "import click; print(click.__version__)"
```

### 练习 2：依赖冲突解决

```bash
# 查看当前依赖树
poetry show --tree

# 查看是否有冲突
poetry check

# 查看过时依赖
poetry show --outdated
```

---

## 今日总结

- [ ] pip 是基础，掌握版本指定和源切换
- [ ] requirements.txt 用注释区分 dev/prod 依赖
- [ ] pipenv 自动管理环境，但速度较慢
- [ ] poetry 是现代推荐方案，依赖解析精确
- [ ] 锁定文件（poetry.lock / Pipfile.lock）确保环境一致

---

*第 30 天 / 330 天*
