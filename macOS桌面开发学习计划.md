# macOS 桌面开发学习计划

## 目标

- 方向：macOS 桌面应用开发
- 目标：能独立开发完整的 macOS 桌面应用
- 周期：约 6-8 个月（每天 2-3 小时）
- 前提：已有前端基础，编程思维已建立

---

## 技术路线选择

| 方案 | 技术栈 | 优势 | 劣势 |
|------|--------|------|------|
| **方案A（推荐）** | Swift + SwiftUI | 原生性能、官方支持、现代化 | 仅限 Apple 生态 |
| 方案B | Electron + Web | 跨平台、复用前端技能 | 体积大、性能一般 |
| 方案C | Flutter | 跨平台、UI 统一 | 非原生体验 |
| 方案D | Tauri | 轻量、安全 | 生态较新 |

**推荐路线：Swift + SwiftUI**（本计划基于此）

---

## 第一阶段：Swift 语言基础（30 天）

### Swift 基础语法（1-10 天）

- [ ] 第 1 天：Swift 简介、Playground 使用、变量与常量
- [ ] 第 2 天：数据类型（Int、Float、Double、String、Bool）
- [ ] 第 3 天：运算符、字符串插值、类型转换
- [ ] 第 4 天：数组（Array）、集合（Set）
- [ ] 第 5 天：字典（Dictionary）
- [ ] 第 6 天：条件语句（if、switch）
- [ ] 第 7 天：循环（for、while、repeat-while）
- [ ] 第 8 天：函数定义、参数标签、默认参数
- [ ] 第 9 天：闭包（Closure）、尾随闭包
- [ ] 第 10 天：阶段练习：命令行工具

### 面向对象（11-20 天）

- [ ] 第 11 天：结构体（struct）与类（class）
- [ ] 第 12 天：属性（存储属性、计算属性、属性观察器）
- [ ] 第 13 天：方法（实例方法、类型方法、mutating）
- [ ] 第 14 天：初始化器（init、 convenience init）
- [ ] 第 15 天：继承与多态
- [ ] 第 16 天：协议（Protocol）
- [ ] 第 17 天：扩展（Extension）
- [ ] 第 18 天：枚举（Enum）、关联值
- [ ] 第 19 天：泛型（Generics）
- [ ] 第 20 天：错误处理（Error、do-catch、throws）

### Swift 高级特性（21-30 天）

- [ ] 第 21 天：可选类型（Optional）、解包
- [ ] 第 22 天：guard 语句、可选链
- [ ] 第 23 天：内存管理、ARC、强引用循环
- [ ] 第 24 天：访问控制（public、private、internal）
- [ ] 第 25 天：协议扩展、默认实现
- [ ] 第 26 天：Associated Types
- [ ] 第 27 天：Result 类型、@escaping 闭包
- [ ] 第 28 天：Swift Package Manager
- [ ] 第 29 天：单元测试 XCTest
- [ ] 第 30 天：阶段项目：命令行计算器/工具

---

## 第二阶段：SwiftUI 基础（45 天）

### SwiftUI 核心概念（1-15 天）

- [ ] 第 1 天：SwiftUI 简介、Xcode 界面
- [ ] 第 2 天：View 协议、body 属性
- [ ] 第 3 天：Text、Image、基础修饰符
- [ ] 第 4 天：Stack 布局（VStack、HStack、ZStack）
- [ ] 第 5 天：Spacer、Divider、Padding
- [ ] 第 6 天：Button、Action
- [ ] 第 7 天：@State、状态管理基础
- [ ] 第 8 天：@Binding、父子视图通信
- [ ] 第 9 天：List、ForEach
- [ ] 第 10 天：NavigationView、NavigationLink
- [ ] 第 11 天：Form、Section、Picker
- [ ] 第 12 天：Toggle、Slider、Stepper
- [ ] 第 13 天：Sheet、Alert、ActionSheet
- [ ] 第 14 天：TabView
- [ ] 第 15 天：阶段项目：待办事项列表

### 数据与状态管理（16-30 天）

- [ ] 第 16 天：@ObservableObject、@ObservedObject
- [ ] 第 17 天：@StateObject、生命周期
- [ ] 第 18 天：@Environment、环境变量
- [ ] 第 19 天：@AppStorage、UserDefaults
- [ ] 第 20 天：Combine 框架基础
- [ ] 第 21 天：Publisher、Subscriber
- [ ] 第 22 天：@Published、数据绑定
- [ ] 第 23 天：MVVM 架构模式
- [ ] 第 24 天：数据模型设计
- [ ] 第 25 天：JSON 解析、Codable
- [ ] 第 26 天：网络请求 URLSession
- [ ] 第 27 天：异步编程 async/await
- [ ] 第 28 天：Core Data 基础
- [ ] 第 29 天：数据持久化方案选择
- [ ] 第 30 天：阶段项目：笔记应用

### macOS 特有 UI（31-45 天）

- [ ] 第 31 天：macOS App 生命周期
- [ ] 第 32 天：WindowGroup、Scene
- [ ] 第 33 天：菜单栏（MenuBar）
- [ ] 第 34 天：工具栏（Toolbar）
- [ ] 第 35 天：侧边栏（Sidebar）
- [ ] 第 36 天：分割视图（NavigationSplitView）
- [ ] 第 37 天：状态栏图标（StatusBar）
- [ ] 第 38 天：Context Menu、右键菜单
- [ ] 第 39 天：拖拽（Drag and Drop）
- [ ] 第 40 天：快捷键（Keyboard Shortcuts）
- [ ] 第 41 天：多窗口管理
- [ ] 第 42 天：Settings/Preferences 窗口
- [ ] 第 43 天：文件拖放打开
- [ ] 第 44 天：窗口大小与布局适配
- [ ] 第 45 天：阶段项目：文件管理器

---

## 第三阶段：macOS 系统框架（45 天）

### Foundation 框架（1-15 天）

- [ ] 第 1 天：FileManager、文件系统操作
- [ ] 第 2 天：URL、路径处理
- [ ] 第 3 天：Date、DateFormatter、Calendar
- [ ] 第 4 天：Timer、定时任务
- [ ] 第 5 天：NotificationCenter、通知
- [ ] 第 6 天：UserDefaults、偏好设置
- [ ] 第 7 天：PropertyList、plist 文件
- [ ] 第 8 天：归档与解档（Archiving）
- [ ] 第 9 天：正则表达式 NSRegularExpression
- [ ] 第 10 天：Process、运行 Shell 命令
- [ ] 第 11 天：Pipe、进程间通信
- [ ] 第 12 天：OperationQueue、GCD 基础
- [ ] 第 13 天：DispatchQueue、异步队列
- [ ] 第 14 天：锁机制、线程安全
- [ ] 第 15 天：阶段项目：系统监控工具

### AppKit 集成（16-30 天）

- [ ] 第 16 天：SwiftUI 中使用 NSViewRepresentable
- [ ] 第 17 天：集成 AppKit 控件
- [ ] 第 18 天：NSWindow、自定义窗口
- [ ] 第 19 天：NSPanel、对话框
- [ ] 第 20 天：NSOpenPanel、文件选择
- [ ] 第 21 天：NSSavePanel、保存文件
- [ ] 第 22 天：NSAlert、确认对话框
- [ ] 第 23 天：NSPasteboard、剪贴板
- [ ] 第 24 天：NSSharingService、分享
- [ ] 第 25 天：NSWorkspace、打开外部应用
- [ ] 第 26 天：NSApplication、应用代理
- [ ] 第 27 天：菜单项动态更新
- [ ] 第 28 天：Dock 图标与弹窗
- [ ] 第 29 天：系统托盘/状态栏
- [ ] 第 30 天：阶段项目：剪贴板历史

### 高级功能（31-45 天）

- [ ] 第 31 天：沙盒机制、权限管理
- [ ] 第 32 天：辅助功能 Accessibility
- [ ] 第 33 天：Spotlight 索引
- [ ] 第 34 天：Quick Look 预览
- [ ] 第 35 天：Share Extension
- [ ] 第 36 天：Service 菜单
- [ ] 第 37 天：AppleScript 支持
- [ ] 第 38 天： Automator Action
- [ ] 第 39 天：签名与公证（Code Signing）
- [ ] 第 40 天：Sparkle 自动更新
- [ ] 第 41 天：崩溃报告收集
- [ ] 第 42 天：性能优化 Instrument
- [ ] 第 43 天：内存分析、泄漏检测
- [ ] 第 44 天：App 打包与分发
- [ ] 第 45 天：阶段项目：系统工具箱

---

## 第四阶段：网络与数据（30 天）

### 网络编程（1-15 天）

- [ ] 第 1 天：URLSession、HTTP 请求
- [ ] 第 2 天：GET、POST、JSON 解析
- [ ] 第 3 天：下载文件、进度跟踪
- [ ] 第 4 天：上传文件
- [ ] 第 5 天：WebSocket 通信
- [ ] 第 6 天：Alamofire 第三方库
- [ ] 第 7 天：网络状态监听
- [ ] 第 8 天：缓存策略
- [ ] 第 9 天：身份验证（Token、OAuth）
- [ ] 第 10 天：RESTful API 封装
- [ ] 第 11 天：GraphQL 基础
- [ ] 第 12 天：后台下载/上传
- [ ] 第 13 天： Bonjour 服务发现
- [ ] 第 14 天：本地网络通信
- [ ] 第 15 天：阶段项目：API 测试工具

### 数据存储（16-30 天）

- [ ] 第 16 天：Core Data 深入
- [ ] 第 17 天：数据模型关系
- [ ] 第 18 天：NSFetchRequest、查询
- [ ] 第 19 天：数据迁移
- [ ] 第 20 天：SQLite.swift
- [ ] 第 21 天：Realm 数据库
- [ ] 第 22 天：JSON 序列化
- [ ] 第 23 天：XML 解析
- [ ] 第 24 天：CSV 处理
- [ ] 第 25 天：YAML 配置
- [ ] 第 26 天：Keychain 安全存储
- [ ] 第 27 天：iCloud 同步
- [ ] 第 28 天：CloudKit 基础
- [ ] 第 29 天：数据备份与恢复
- [ ] 第 30 天：阶段项目：密码管理器

---

## 第五阶段：进阶与实战（30 天）

### 进阶主题（1-15 天）

- [ ] 第 1 天：SwiftUI 动画基础
- [ ] 第 2 天：过渡动画、matchedGeometryEffect
- [ ] 第 3 天：自定义绘图 Canvas、Path
- [ ] 第 4 天：图表框架 Charts
- [ ] 第 5 天：MapKit 地图集成
- [ ] 第 6 天：WebView WKWebView
- [ ] 第 7 天：PDF 生成与显示
- [ ] 第 8 天：图片处理 CoreImage
- [ ] 第 9 天：视频播放 AVFoundation
- [ ] 第 10 天：音频录制与播放
- [ ] 第 11 天：通知中心小组件
- [ ] 第 12 天：Siri Shortcuts 集成
- [ ] 第 13 天：Apple Intelligence / ML
- [ ] 第 14 天：Create ML 模型训练
- [ ] 第 15 天：阶段项目：多媒体播放器

### 综合实战（16-30 天）

- [ ] 第 16-20 天：项目一：Markdown 编辑器
  - 实时预览、文件树、语法高亮
- [ ] 第 21-25 天：项目二：HTTP 客户端（类似 Postman）
  - 请求构建、响应展示、历史记录
- [ ] 第 26-30 天：项目三：个人知识库
  - 笔记、标签、搜索、同步

---

## 学习资源

| 类型 | 推荐资源 |
|------|----------|
| 官方文档 | [Swift.org](https://swift.org)、[Apple Developer](https://developer.apple.com) |
| 教程 | Hacking with Swift、RayWenderlich |
| 书籍 | 《Swift 编程权威指南》、《SwiftUI by Tutorials》 |
| 视频 | Stanford CS193p（免费） |
| 社区 | Stack Overflow、Swift Forums |

---

## 开发工具

- **Xcode**：主要 IDE（Mac App Store 下载）
- **Playground**：快速验证代码
- **Simulator**：模拟器测试
- **Instruments**：性能分析
- **SF Symbols**：系统图标库

---

## 进度跟踪表

| 阶段 | 开始日期 | 完成日期 | 状态 |
|------|----------|----------|------|
| 第一阶段：Swift 语言 |  |  |  |
| 第二阶段：SwiftUI 基础 |  |  |  |
| 第三阶段：macOS 系统框架 |  |  |  |
| 第四阶段：网络与数据 |  |  |  |
| 第五阶段：进阶与实战 |  |  |  |

---

*创建于 2026/05/21*
