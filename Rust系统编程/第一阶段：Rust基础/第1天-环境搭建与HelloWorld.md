# 第 1 天：环境搭建与 Hello World

## 学习目标

- 安装 Rust 工具链
- 掌握 Cargo 基本用法
- 配置开发环境
- 编写并运行第一个 Rust 程序

---

## 1. 安装 Rust

### 使用 rustup（推荐）

```bash
# macOS / Linux
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 安装完成后，加载环境变量
source $HOME/.cargo/env

# 验证安装
rustc --version
cargo --version
```

### rustup 常用命令

```bash
# 更新 Rust
rustup update

# 切换 stable/nightly
rustup default stable
rustup default nightly

# 安装组件
rustup component add rustfmt      # 代码格式化
rustup component add clippy       # 静态检查
rustup component add rust-src     # 标准库源码

# 安装工具链
rustup target add wasm32-unknown-unknown
```

---

## 2. Cargo 包管理器

### Cargo 是什么

Cargo 是 Rust 的构建系统和包管理器：
- 编译代码
- 管理依赖
- 运行测试
- 生成文档

### 常用命令

```bash
# 创建新项目
cargo new hello_world           # 二进制项目
cargo new my_lib --lib          # 库项目

# 构建
 cargo build                    # 开发模式（带调试信息）
cargo build --release          # 发布模式（优化）

# 运行
cargo run
cargo run --release

# 测试
cargo test
cargo test -- --nocapture       # 显示 println! 输出

# 检查（不生成可执行文件，更快）
cargo check

# 格式化代码
cargo fmt

# 静态检查
cargo clippy

# 生成文档
cargo doc --open

# 添加依赖
cargo add serde
cargo add tokio --features full
```

---

## 3. 配置开发环境

### VS Code 推荐配置

插件：
- **rust-analyzer** — Rust 语言服务器（必备）
- **CodeLLDB** — 调试器
- **Even Better TOML** — Cargo.toml 语法高亮
- **Crates** — 依赖版本管理

`.vscode/settings.json`：
```json
{
  "rust-analyzer.cargo.features": "all",
  "rust-analyzer.checkOnSave.command": "clippy",
  "editor.formatOnSave": true,
}
```

---

## 4. 第一个程序

### 项目结构

```bash
cargo new hello_rust
cd hello_rust
tree
```

```
hello_rust/
├── Cargo.toml      # 项目配置和依赖
├── .gitignore
└── src/
    └── main.rs     # 入口文件
```

### Cargo.toml

```toml
[package]
name = "hello_rust"
version = "0.1.0"
edition = "2021"

[dependencies]
```

### main.rs

```rust
fn main() {
    println!("Hello, Rust!");
}
```

### 运行

```bash
cargo run
#   Compiling hello_rust v0.1.0
#    Finished dev [unoptimized + debuginfo] target(s)
#     Running `target/debug/hello_rust`
# Hello, Rust!
```

---

## 5. 基础语法初探

### println! 宏

```rust
fn main() {
    // 基本输出
    println!("Hello, World!");

    // 占位符
    println!("{}, {}!", "Hello", "Rust");

    // 命名参数
    println!("{greeting}, {name}!", greeting = "Hello", name = "Rust");

    // 格式化数字
    println!("Pi = {:.2}", 3.14159);  // Pi = 3.14
    println!("Binary: {:b}", 10);      // Binary: 1010
    println!("Hex: {:x}", 255);        // Hex: ff
}
```

### 注释

```rust
// 单行注释

/*
 * 多行注释
 */

/// 文档注释（给函数/结构体）
fn documented_function() {}

//! crate 级别文档注释（写在文件开头）
```

---

## 6. 了解编译过程

### Rust 编译流程

```
源代码 (.rs)
    ↓
rustc 编译
    ↓
中间表示 (HIR → MIR)
    ↓
LLVM IR
    ↓
机器码
```

### 开发 vs 发布模式

| 模式 | 编译速度 | 运行速度 | 调试 | 大小 |
|------|----------|----------|------|------|
| dev (debug) | 快 | 慢 | 有 | 大 |
| release | 慢 | 快 | 无 | 小 |

```bash
# 开发模式（默认）
cargo build
# 输出：target/debug/hello_rust

# 发布模式
 cargo build --release
# 输出：target/release/hello_rust
```

---

## 实战练习

### 练习 1：个人信息输出

```rust
fn main() {
    let name = "Alice";
    let age = 25;
    let is_student = true;

    println!("姓名: {}", name);
    println!("年龄: {}", age);
    println!("是否学生: {}", is_student);
}
```

### 练习 2：添加依赖并使用

在 `Cargo.toml` 中添加：
```toml
[dependencies]
chrono = "0.4"
```

```rust
use chrono::Local;

fn main() {
    let now = Local::now();
    println!("当前时间: {}", now.format("%Y-%m-%d %H:%M:%S"));
}
```

### 练习 3：使用 cargo fmt 和 clippy

```bash
# 格式化代码
cargo fmt

# 运行检查
cargo clippy

# 运行测试
cargo test
```

---

## 今日总结

- [ ] `rustup` 安装和管理 Rust 工具链
- [ ] `cargo` 是 Rust 的构建系统和包管理器
- [ ] `cargo new` 创建项目，`cargo run` 运行，`cargo build` 构建
- [ ] `println!` 是宏，不是函数，用 `!` 标识
- [ ] `cargo fmt` 格式化，`cargo clippy` 静态检查
- [ ] Rust 有 `dev` 和 `release` 两种构建模式
- [ ] 文档注释用 `///`，Crate 文档用 `//!`

---

*第 1 天 / 86 天*
*第一阶段：Rust 基础 - 环境搭建*
