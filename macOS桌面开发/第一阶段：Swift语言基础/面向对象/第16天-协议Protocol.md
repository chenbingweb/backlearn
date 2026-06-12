# 第 16 天：协议（Protocol）

## 学习目标

- 理解协议的概念
- 掌握协议的定义和遵循
- 学会协议属性和方法要求
- 理解协议继承和组合

---

## 1. 协议基础

### 定义协议

```swift
protocol Drawable {
    func draw()
    var color: String { get set }
}
```

### 遵循协议

```swift
struct Circle: Drawable {
    var color: String
    var radius: Double

    func draw() {
        print("绘制\(color)圆形，半径\(radius)")
    }
}

struct Rectangle: Drawable {
    var color: String
    var width: Double
    var height: Double

    func draw() {
        print("绘制\(color)矩形")
    }
}
```

### 使用协议类型

```swift
func render(_ shape: Drawable) {
    shape.draw()
}

let circle = Circle(color: "红色", radius: 5)
let rect = Rectangle(color: "蓝色", width: 10, height: 5)

render(circle)  // 绘制红色圆形，半径5.0
render(rect)    // 绘制蓝色矩形
```

---

## 2. 协议属性要求

### 属性要求

```swift
protocol Identifiable {
    var id: Int { get } // 只读属性
    var name: String { get set }  // 可读写属性
}

struct User: Identifiable {
    let id: Int
    var name: String
}

let user = User(id: 1, name: "Alice")
print(user.id)   // 1
print(user.name)  // Alice
```

### 类型属性要求

```swift
protocol Configurable {
    static var defaultConfig: Configurable { get }
    static func createDefault() -> Configurable
}

class AppConfig: Configurable {
    var apiEndpoint: String

    init(apiEndpoint: String) {
        self.apiEndpoint = apiEndpoint
    }

    static var defaultConfig: Configurable {
        return AppConfig(apiEndpoint: "https://api.example.com")
    }

    static func createDefault() -> Configurable {
        return defaultConfig
    }
}
```

---

## 3. 协议方法要求

### 实例方法要求

```swift
protocol Calculatable {
    func calculate() -> Double
    mutating func reset()
}

struct Calculator: Calculatable {
    var value: Double = 0

    func calculate() -> Double {
        return value * 2
    }

    mutating func reset() {
        value = 0
    }
}
```

### 类型方法要求

```swift
protocol Factory {
    static func create() -> Self
}

class Product: Factory {
    var name: String

    init(name: String) {
        self.name = name
    }

    static func create() -> Product {
        return Product(name: "默认产品")
    }
}

let product = Product.create()
print(product.name)  // 默认产品
```

---

## 4. 协议继承

### 基本继承

```swift
protocol Printable {
    func printDescription()
}

protocol Serializable: Printable {
    func serialize() -> String
}
```

### 多协议继承

```swift
protocol A { func methodA() }
protocol B { func methodB() }
protocol C: A, B { }

class MyClass: C {
    func methodA() { print("A") }
    func methodB() { print("B") }
}
```

---

## 5. 协议组合

### Protocol Composition

```swift
protocol Named {
    var name: String { get }
}

protocol Aged {
    var age: Int { get }
}

// 同时遵循两个协议
struct Person: Named, Aged {
    var name: String
    var age: Int
}

func greet(_ person: Named & Aged) {
    print("你好，\(person.name)，\(person.age)岁")
}

let person = Person(name: "Alice", age: 30)
greet(person)  // 你好，Alice，30岁
```

---

## 6. 协议扩展

### 默认实现

```swift
protocol Printable {
    var description: String { get }
}

extension Printable {
    var description: String {
        return "默认描述"
    }
}

struct Item: Printable { }

let item = Item()
print(item.description)  // 默认描述
```

### 协议扩展添加方法

```swift
protocol Math {
    func add(_ a: Double, _ b: Double) -> Double
}

extension Math {
    func add(_ a: Double, _ b: Double) -> Double {
        return a + b
    }

    func multiply(_ a: Double, _ b: Double) -> Double {
        return a * b
    }
}

struct BasicMath: Math { }
// BasicMath 自动获得 add 和 multiply 实现
```

---

## 7. 常用标准库协议

### Equatable

```swift
struct Point: Equatable {
    var x: Double
    var y: Double
}

// 自动生成 ==运算符
let p1 = Point(x: 1, y: 2)
let p2 = Point(x: 1, y: 2)
print(p1 == p2)  // true
```

### Comparable

```swift
struct Student: Comparable {
    var name: String
    var score: Int

    static func < (lhs: Student, rhs: Student) -> Bool {
        return lhs.score < rhs.score
    }
}

let students = [
    Student(name: "Bob", score: 85),
    Student(name: "Alice", score: 92)
]

print(students.sorted())  // 按 score排序
```

### CustomStringConvertible

```swift
struct Dog: CustomStringConvertible {
    var name: String
    var breed: String

    var description: String {
        return "Dog(\(name), \(breed))"
    }
}

let dog = Dog(name: "Max", breed: "金毛")
print(dog)  // Dog(Max, 金毛)
```

---

## 实战练习

### 练习 1：定义数据协议

```swift
protocol DataStore {
    var count: Int { get }
    mutating func save(_ item: String)
    mutating func load() -> String?
    mutating func clear()
}

struct MemoryStore: DataStore {
    private var items: [String] = []

    var count: Int { items.count }

    mutating func save(_ item: String) {
        items.append(item)
    }

    mutating func load() -> String? {
        return items.isEmpty ? nil : items.removeFirst()
    }

    mutating func clear() {
        items.removeAll()
    }
}

// 使用
var store = MemoryStore()
store.save("item1")
store.save("item2")
print(store.count)    // 2
print(store.load()!) // item1
print(store.count)   // 1
store.clear()
print(store.count)   // 0
```

### 练习 2：多重协议

```swift
protocol Logger {
    func log(_ message: String)
}

protocol TimestampLogger: Logger {
    var timestamp: Date { get }
}

extension TimestampLogger {
    func log(_ message: String) {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        let time = formatter.string(from: timestamp)
        print("[\(time)] \(message)")
    }
}

class SystemLogger: TimestampLogger {
    var timestamp: Date { Date() }
}

let logger = SystemLogger()
logger.log("系统启动")  // [2024-01-01 12:00:00] 系统启动
```

---

## 今日总结

- [ ] 协议定义方法/属性签名，由具体类型实现
- [ ] 结构体/类通过 `:`遵循协议
- [ ] 协议属性要求 `{ get }`（只读）或 `{ get set }`（可写）
- [ ] 协议可以继承（`protocol A: B`）
- [ ] 协议组合 `A & B` 要求同时遵循多个协议
- [ ] 协议扩展可提供默认实现
- [ ] 常用标准协议：`Equatable`、`Comparable`、`CustomStringConvertible`

---

*第 16 天 / 330 天*
*macOS 开发 - Swift 协议*