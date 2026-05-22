# 第 1 天：Swift 简介、Playground 使用、变量与常量

## 学习目标

- 了解 Swift 语言的特点和发展
- 学会使用 Xcode Playground
- 掌握变量和常量的定义与使用
- 理解类型推断机制

---

## 1. Swift 简介

### 什么是 Swift

Swift 是 Apple 于 2014 年推出的编程语言，用于开发 iOS、macOS、watchOS 和 tvOS 应用。

### Swift 特点

- **安全**：类型安全、可选类型、内存安全
- **快速**：接近 C++ 的性能
- **现代**：支持函数式编程、协议 oriented 编程
- **开源**：源代码公开，跨平台（Linux）
- **易读**：语法接近自然语言

### Swift 版本

- Swift 5.x：当前主流版本，ABI 稳定
- Swift 6.0：引入完整的并发安全检查

---

## 2. 开发环境搭建

### 安装 Xcode

```
1. 打开 Mac App Store
2. 搜索 "Xcode"
3. 点击安装（约 10GB+）
```

### 验证安装

```bash
swift --version
# 输出类似：swift-driver version: 1.90.11.1 Apple Swift version 5.10
```

### 使用 REPL

```bash
swift
```

在终端输入 `swift` 进入交互式环境，可以像 Python 一样直接执行代码。

---

## 3. Playground 使用

### 创建 Playground

```
1. 打开 Xcode
2. File → New → Playground
3. 选择 "Blank" 模板
4. 命名并保存
```

### Playground 界面

```
左侧：代码编辑区
右侧：实时结果显示区（Results Sidebar）
底部：控制台输出（Console）
```

### 基本操作

```swift
// 在 Playground 中编写代码，右侧会实时显示结果
let greeting = "Hello, Swift!"
print(greeting)

// 点击右侧结果可以查看详细信息
let numbers = [1, 2, 3, 4, 5]
// 右侧会显示: [1, 2, 3, 4, 5]
```

### 辅助功能

```swift
// 添加分页
//: [上一页](@previous)
//: [下一页](@next)

// 富文本注释
/*:
 # 标题
 ## 副标题
 - 列表项1
 - 列表项2
 */
```

---

## 4. 变量与常量

### 常量（let）

```swift
// 使用 let 声明常量，一旦赋值不可修改
let pi = 3.14159
let appName = "MyApp"
let maxUsers = 100

// 错误示例
// pi = 3.14  // 编译错误: Cannot assign to value: 'pi' is a 'let' constant
```

### 变量（var）

```swift
// 使用 var 声明变量，可以修改
var score = 0
score = 100
score = 200

var userName = "Alice"
userName = "Bob"
```

### 类型推断

```swift
// Swift 会自动推断类型
let integer = 42           // Int
let floating = 3.14        // Double
let text = "Hello"         // String
let flag = true            // Bool

// 显式声明类型
let explicitInt: Int = 42
let explicitDouble: Double = 3.14
let explicitString: String = "Hello"
let explicitBool: Bool = true
```

### 命名规则

```swift
// 基本规则
let userName = "Alice"      // 驼峰命名法
let _private = "secret"     // 以下划线开头
let 你好 = "Hello"           // 支持 Unicode（不推荐）

// 可以包含 emoji
let 🐶 = "dog"
print(🐶)
```

### 输出与字符串插值

```swift
let name = "Swift"
let version = 5

// 字符串插值
print("Hello, \(name)!")
// 输出: Hello, Swift!

print("当前版本: \(version)")
// 输出: 当前版本: 5

// 复杂表达式
let a = 10
let b = 20
print("\(a) + \(b) = \(a + b)")
// 输出: 10 + 20 = 30
```

---

## 5. 注释

```swift
// 单行注释

/*
 多行注释
 可以写多行
 */

/*
 多行注释可以嵌套
 /* 这是嵌套的注释 */
 嵌套结束
 */

// MARK: - 分割线
// TODO: 待完成
// FIXME: 需要修复
// HACK: 临时方案
```

---

## 6. 分号使用

```swift
// Swift 不需要分号
let x = 10
let y = 20

// 同一行多条语句需要分号
let a = 10; let b = 20
```

---

## 7. 实战练习

### 练习 1：个人信息卡片

```swift
let name = "张三"
let age = 25
let city = "北京"
let isStudent = false

print("===== 个人信息 =====")
print("姓名: \(name)")
print("年龄: \(age)")
print("城市: \(city)")
print("学生: \(isStudent ? "是" : "否")")
```

### 练习 2：常量与变量的区别

```swift
let birthYear = 1999       // 出生年份，不会变
var currentYear = 2024     // 当前年份，每年会变
var age = currentYear - birthYear

print("出生年份: \(birthYear)")
print("当前年份: \(currentYear)")
print("年龄: \(age)")

// 模拟过了一年
currentYear = 2025
age = currentYear - birthYear
print("明年年龄: \(age)")

// birthYear = 2000  // 错误！常量不能修改
```

---

## 今日总结

- [ ] Swift 是 Apple 的现代编程语言，安全、快速、开源
- [ ] 使用 Xcode Playground 进行交互式学习
- [ ] `let` 声明常量，`var` 声明变量
- [ ] Swift 支持类型推断，也可显式声明类型
- [ ] 使用 `\()` 进行字符串插值

---

## 课后作业

1. 在 Playground 中创建一个「商品信息」变量集合（名称、价格、库存、是否上架）
2. 尝试修改一个 `let` 常量，观察编译错误
3. 使用字符串插值打印格式化的商品信息

---

*第 1 天 / 180 天*
