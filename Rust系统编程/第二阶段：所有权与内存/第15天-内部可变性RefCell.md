# 第 15 天：内部可变性 RefCell

## 学习目标

- 理解内部可变性模式
- 掌握 RefCell 的使用
- 了解运行时借用检查
- 学习 Rc<RefCell<T>> 组合

---

## 1. 内部可变性

### 什么是内部可变性

Rust 通常通过 `&mut` 强制可变性的独占性：

```rust
let mut x = 5;
let y = &mut x;  // ✅
let z = &mut x;  // ❌ 不能同时有两个可变引用
```

**内部可变性**：允许在持有不可变引用的情况下修改数据。

```rust
use std::cell::RefCell;

fn main() {
    let x = RefCell::new(5);

    let y = x.borrow();     // 不可变借用
    println!("y = {}", y);
    drop(y);                // 显式释放

    let z = x.borrow_mut(); // 可变借用
    *z = 10;
    println!("z = {}", z);
}
```

### RefCell 的原理

```
编译时检查 (借用规则):
  &T     → 不可变引用
  &mut T → 可变引用（独占）

运行时检查 (RefCell):
  borrow()     → 检查当前没有可变借用
  borrow_mut() → 检查当前没有任何借用
  违反规则 → 运行时 panic（不是编译错误）
```

---

## 2. RefCell 基础用法

### 创建和访问

```rust
use std::cell::RefCell;

fn main() {
    let cell = RefCell::new(5);

    // 不可变借用
    let value = cell.borrow();
    println!("值: {}", *value);  // 5
    drop(value);  // 释放借用

    // 可变借用
    let mut value = cell.borrow_mut();
    *value += 1;
    println!("值: {}", *value);  // 6
    drop(value);

    // 再次不可变借用
    let value = cell.borrow();
    println!("值: {}", *value);  // 6
}
```

### 运行时 panic

```rust
use std::cell::RefCell;

fn main() {
    let cell = RefCell::new(5);

    let _borrow1 = cell.borrow_mut();
    let _borrow2 = cell.borrow_mut();  // ❌ panic! 运行时错误
}
```

输出：
```
thread 'main' panicked at 'already borrowed: BorrowMutError'
```

⚠️ RefCell 把编译期检查推迟到运行时，**panic 表示程序逻辑有 bug**。

---

## 3. RefCell 使用场景

### 场景1：需要可变但只能拿到不可变引用

```rust
use std::cell::RefCell;

struct Messenger {
    messages: RefCell<Vec<String>>,
}

impl Messenger {
    fn new() -> Messenger {
        Messenger {
            messages: RefCell::new(Vec::new()),
        }
    }

    // &self 而不是 &mut self
    fn send(&self, msg: &str) {
        self.messages.borrow_mut().push(String::from(msg));
    }

    fn show_messages(&self) {
        for msg in self.messages.borrow().iter() {
            println!("{}", msg);
        }
    }
}

fn main() {
    let messenger = Messenger::new();
    messenger.send("Hello");
    messenger.send("World");
    messenger.show_messages();
}
```

### 场景2：mock 对象

```rust
use std::cell::RefCell;

trait Logger {
    fn log(&self, msg: &str);
}

struct MockLogger {
    logged: RefCell<Vec<String>>,
}

impl MockLogger {
    fn new() -> MockLogger {
        MockLogger {
            logged: RefCell::new(vec![]),
        }
    }
}

impl Logger for MockLogger {
    fn log(&self, msg: &str) {
        self.logged.borrow_mut().push(String::from(msg));
    }
}

fn process(logger: &dyn Logger) {
    logger.log("开始处理");
    logger.log("处理完成");
}

fn main() {
    let mock = MockLogger::new();
    process(&mock);

    println!("记录的消息: {:?}", mock.logged.borrow());
}
```

---

## 4. Rc<RefCell<T>> 组合

### 共享 + 可变

```rust
use std::rc::Rc;
use std::cell::RefCell;

#[derive(Debug)]
struct User {
    name: String,
    age: u32,
}

fn main() {
    let user = Rc::new(RefCell::new(User {
        name: String::from("Alice"),
        age: 30,
    }));

    let user2 = Rc::clone(&user);
    let user3 = Rc::clone(&user);

    println!("初始: {:?}", user.borrow());

    // 通过任一引用修改
    user2.borrow_mut().age = 31;
    user3.borrow_mut().name.push_str(" Smith");

    println!("修改后: {:?}", user.borrow());
    println!("引用计数: {}", Rc::strong_count(&user));
}
```

```
初始: User { name: "Alice", age: 30 }
修改后: User { name: "Alice Smith", age: 31 }
引用计数: 3
```

### 共享的链表（可变）

```rust
use std::rc::Rc;
use std::cell::RefCell;

#[derive(Debug)]
struct Node {
    value: i32,
    next: Option<Rc<RefCell<Node>>>,
}

fn main() {
    let first = Rc::new(RefCell::new(Node {
        value: 1,
        next: None,
    }));

    let second = Rc::new(RefCell::new(Node {
        value: 2,
        next: Some(Rc::clone(&first)),
    }));

    // 修改 first 的值
    first.borrow_mut().value = 10;

    println!("first: {:?}", first.borrow());
    println!("second: {:?}", second.borrow());
}
```

---

## 5. Cell<T>

### 只能 Copy 类型

```rust
use std::cell::Cell;

fn main() {
    let cell = Cell::new(5);

    // get: 复制值（要求 T: Copy）
    let value = cell.get();
    println!("值: {}", value);

    // set: 设置新值
    cell.set(10);
    println!("新值: {}", cell.get());
}
```

`Cell<T>` 比 `RefCell<T>` 更轻量，但只能用于实现了 `Copy` 的类型。

### Cell vs RefCell

| 特性 | Cell<T> | RefCell<T> |
|------|---------|------------|
| 适用类型 | Copy 类型 | 任意类型 |
| 获取值 | get() 复制 | borrow() 返回引用 |
| 运行时检查 | 无 | 有（borrow 计数）|
| 开销 | 更小 | 稍大 |

---

## 6. 内部可变性选择指南

```
单线程：
  T: Copy    → Cell<T>
  T: !Copy   → RefCell<T>
  共享+可变   → Rc<RefCell<T>>

多线程：
  T: Copy + Send  → Atomic 类型
  T: Send         → Mutex<T> / RwLock<T>
  共享+可变       → Arc<Mutex<T>>
```

---

## 实战练习

### 练习 1：计数器

```rust
use std::cell::RefCell;

struct Counter {
    count: RefCell<u32>,
}

impl Counter {
    fn new() -> Counter {
        Counter {
            count: RefCell::new(0),
        }
    }

    fn increment(&self) {
        *self.count.borrow_mut() += 1;
    }

    fn get(&self) -> u32 {
        *self.count.borrow()
    }
}

fn main() {
    let counter = Counter::new();

    counter.increment();
    counter.increment();
    counter.increment();

    println!("计数: {}", counter.get());
}
```

### 练习 2：可变的共享缓存

```rust
use std::rc::Rc;
use std::cell::RefCell;
use std::collections::HashMap;

struct Cache {
    data: RefCell<HashMap<String, String>>,
}

impl Cache {
    fn new() -> Cache {
        Cache {
            data: RefCell::new(HashMap::new()),
        }
    }

    fn get(&self, key: &str) -> Option<String> {
        self.data.borrow().get(key).cloned()
    }

    fn set(&self, key: &str, value: &str) {
        self.data.borrow_mut().insert(String::from(key), String::from(value));
    }
}

fn main() {
    let cache = Rc::new(Cache::new());

    let c1 = Rc::clone(&cache);
    let c2 = Rc::clone(&cache);

    c1.set("host", "localhost");
    c2.set("port", "8080");

    println!("host: {:?}", cache.get("host"));
    println!("port: {:?}", cache.get("port"));
}
```

### 练习 3：判断输出

```rust
use std::cell::RefCell;

fn main() {
    let cell = RefCell::new(5);

    let b1 = cell.borrow();
    let b2 = cell.borrow();

    println!("{}, {}", *b1, *b2);

    // let b3 = cell.borrow_mut();  // ?
}
```

答案：✅ 可以编译，因为 b1 和 b2 都是不可变借用。但如果取消注释 b3 那行会 panic，因为不能同时有不可变和可变借用。

---

## 今日总结

- [ ] 内部可变性：在不可变引用下修改数据
- [ ] `RefCell<T>` 运行时检查借用规则，违反则 panic
- [ ] `borrow()` 获取不可变引用，`borrow_mut()` 获取可变引用
- [ ] `Cell<T>` 用于 Copy 类型，更轻量
- [ ] `Rc<RefCell<T>>` 实现多所有者 + 内部可变性
- [ ] 运行时 panic 表示程序有 bug，不是编译错误
- [ ] 选择：Copy 用 Cell，非 Copy 用 RefCell，多线程用 Mutex/RwLock

---

*第 15 天 / 86 天*
*第二阶段：所有权与内存 - RefCell 内部可变性*
