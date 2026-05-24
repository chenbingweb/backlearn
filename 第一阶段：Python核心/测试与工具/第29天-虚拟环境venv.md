# 第 29 天：虚拟环境 venv、conda

## 学习目标

- 理解为什么需要虚拟环境
- 掌握 venv 的使用
- 了解 conda 的使用场景
- 学会在不同环境间切换

---

## 1. 为什么需要虚拟环境

### 问题场景

```
项目A 需要 requests==2.25.1
项目B 需要 requests==2.28.1

如果都装到全局，两个项目会冲突！
```

虚拟环境为每个项目创建独立的 Python 环境，隔离依赖。

---

## 2. venv（标准库）

### 创建虚拟环境

```bash
# 基本用法
python -m venv myenv

# 指定 Python 版本
python3.11 -m venv myenv

# 创建时排除 pip（最小环境）
python -m venv myenv --without-pip
```

### 激活/退出

```bash
# macOS/Linux
source myenv/bin/activate

# Windows
myenv\Scripts\activate.bat

# 退出
deactivate
```

### 使用虚拟环境

```bash
# 激活后，python 和 pip 指向虚拟环境
(myenv) $ which python
/Users/xxx/myenv/bin/python

(myenv) $ pip install requests
# 安装到虚拟环境，不影响全局
```

### 删除虚拟环境

```bash
# 直接删除目录即可
rm -rf myenv
```

---

## 3. 虚拟环境目录结构

```
myenv/
├── bin/              # 可执行文件（activate、python、pip）
│   ├── activate
│   ├── python
│   └── pip
├── include/          # C 头文件
├── lib/
│   └── python3.x/
│       └── site-packages/   # 安装的包
└── pyvenv.cfg        # 配置信息
```

---

## 4. 最佳实践

### 项目结构

```
my_project/
├── venv/                 # 虚拟环境（加 .gitignore）
├── src/                  # 源代码
├── tests/                # 测试
├── requirements.txt      # 依赖列表
└── .gitignore
```

### .gitignore

```gitignore
venv/
.env/
__pycache__/
*.pyc
```

### requirements.txt

```bash
# 导出当前环境的依赖
pip freeze > requirements.txt

# 从 requirements.txt 安装
pip install -r requirements.txt
```

```txt
# requirements.txt 示例
requests==2.28.1
flask==2.3.0
pytest==7.4.0
```

---

## 5. conda

### 适用场景

- 需要管理非 Python 依赖（如 C 库、CUDA）
- 数据科学/机器学习项目
- 需要多版本 Python 并存

### 基本命令

```bash
# 创建环境
conda create -n myenv python=3.11

# 激活
conda activate myenv

# 退出
conda deactivate

# 删除环境
conda remove -n myenv --all

# 列出所有环境
conda env list

# 导出环境
conda env export > environment.yml

# 从文件创建
conda env create -f environment.yml
```

### environment.yml

```yaml
name: myenv
channels:
  - defaults
  - conda-forge
dependencies:
  - python=3.11
  - numpy=1.24
  - pandas=2.0
  - pip:
    - requests==2.28.1
```

---

## 6. venv vs conda

| 特性 | venv | conda |
|------|------|-------|
| 来源 | Python 标准库 | Anaconda/Miniconda |
| 速度 | 快 | 较慢 |
| 非 Python 依赖 | 不支持 | 支持 |
| 多版本 Python | 需手动指定 | 内置支持 |
| 推荐场景 | 纯 Python 项目 | 数据科学、ML |

---

## 实战练习

### 练习 1：为项目创建虚拟环境

```bash
# 1. 创建项目目录
mkdir my_project && cd my_project

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活
source venv/bin/activate

# 4. 安装依赖
pip install requests flask

# 5. 导出依赖
pip freeze > requirements.txt

# 6. 验证
python -c "import requests; print(requests.__version__)"

# 7. 退出
deactivate
```

### 练习 2：切换 Python 版本

```bash
# 查看可用的 Python
ls -la /usr/bin/python*

# 用 Python 3.10 创建环境
python3.10 -m venv py310_env
source py310_env/bin/activate
python --version  # Python 3.10.x
```

---

## 今日总结

- [ ] 虚拟环境隔离项目依赖，避免冲突
- [ ] `python -m venv` 创建，`source venv/bin/activate` 激活
- [ ] `pip freeze > requirements.txt` 导出依赖
- [ ] conda 适合数据科学，支持非 Python 依赖
- [ ] 虚拟环境目录不要提交到 git

---

*第 29 天 / 330 天*
