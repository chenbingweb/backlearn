# 第 13 天：智能指针 Box

## 学习目标

- 理解智能指针的概念
- 掌握 Box 的使用场景
- 理解递归类型
- 了解 Deref 和 Drop Trait

---

## 1. 什么是智能指针

### 指针 vs 智能指针

```
普通指针：只是一个地址，无额外功能
智能指针：像指针一样工作，但拥有元数据和能力
    - 自动内存管理（如 Box）
    - 引用计数（如 Rc）
    - 运行时借用检查（如 RefCell）
```

### 智能指针的特征

- 实现 `Deref` Trait：可以像引用一样解引用
- 实现 `Drop` Trait：超出作用域时自动清理资源

---

## 2. Box

### 基本用法

`Box<T>` 是在**堆上**分配内存的最简单方式：

```rust
fn main() {
    // b 在栈上，5 在堆上
    let b = Box::new(5);
    println!("b = {}", b);  // 自动解引用
}
```

内存布局：
```
栈            堆
┌─────┐      ┌─────┐
│ Box │─────→│  5  │
│ ptr │      └─────┘
└─────┘
```

### 使用场景

**场景1：编译期未知大小的类型**

```rust
enum List {
    Cons(i32, Box<List>),  // Box 让递归类型有确定大小
    Nil,
}

use List::{Cons, Nil};

fn main() {
    let list = Cons(1, Box::new(Cons(2, Box::new(Cons(3, Box::new(Nil))))));
}
```

**场景2：大量数据转移所有权**

```rust
fn main() {
    let data = Box::new([0u8; 1000000]);  // 1MB 数据在堆上

    // 转移所有权只需复制指针（8 字节），不是 1MB
    let data2 = data;
    // data 不可用
}
```

**场景3： trait 对象**

```rust
trait Animal {
    fn speak(&self);
}

struct Dog;
struct Cat;

impl Animal for Dog {
    fn speak(&self) { println!("Woof!"); }
}

impl Animal for Cat {
    fn speak(&self) { println!("Meow!"); }
}

fn main() {
    // Box<dyn Animal> 是 trait 对象
    let animals: Vec<Box<dyn Animal>> = vec![
        Box::new(Dog),
        Box::new(Cat),
    ];

    for animal in animals {
        animal.speak();
    }
}
```

---

## 3. 递归类型详解

### 为什么需要 Box

```rust
// ❌ 错误：编译器无法计算大小
enum List {
    Cons(i32, List),  // List 包含 List，大小无限递归
    Nil,
}
```

```rust
// ✅ 正确：Box 有确定大小（指针大小）
enum List {
    Cons(i32, Box<List>),  // Box 是固定大小的指针
    Nil,
}
```

### 实现链表

```rust
#[derive(Debug)]
enum List {
    Cons(i32, Box<List>),
    Nil,
}

use List::{Cons, Nil};

impl List {
    fn new() -> List {
        Nil
    }

    fn prepend(self, elem: i32) -> List {
        Cons(elem, Box::new(self))
    }

    fn len(&self) -> usize {
        match self {
            Cons(_, tail) => 1 + tail.len(),
            Nil => 0,
        }
    }

    fn to_string(&self) -> String {
        match self {
            Cons(head, tail) => format!("{} -> {}", head, tail.to_string()),
            Nil => String::from("Nil"),
        }
    }
}

fn main() {
    let list = List::new()
        .prepend(3)
        .prepend(2)
        .prepend(1);

    println!("链表: {}", list.to_string());
    println!("长度: {}", list.len());
}
```

---

## 4. Deref Trait

### 自定义解引用

```rust
use std::ops::Deref;

struct MyBox<T>(T);

impl<T> MyBox<T> {
    fn new(x: T) -> MyBox<T> {
        MyBox(x)
    }
}

impl<T> Deref for MyBox<T> {
    type Target = T;

    fn deref(&self) -> &T {
        &self.0
    }
}

fn main() {
    let x = 5;
    let y = MyBox::new(x);

    assert_eq!(5, x);
    assert_eq!(5, *y);  // 调用 y.deref()
}
```

### 强制解引用（Deref Coercion）

```rust
fn hello(name: &str) {
    println!("Hello, {}!", name);
}

fn main() {
    let m = Box::new(String::from("Rust"));
    hello(&m);  // 自动转换: &Box<String> → &String → &str
}
```

转换链：
```
&m: &Box<String>
  ↓ deref()
  &String
  ↓ deref()
  &str
```

---

## 5. Drop Trait

### 自定义清理逻辑

```rust
struct CustomSmartPointer {
    data: String,
}

impl Drop for CustomSmartPointer {
    fn drop(&mut self) {
        println!("释放 CustomSmartPointer，数据: '{}'", self.data);
    }
}

fn main() {
    let c = CustomSmartPointer {
        data: String::from("我的数据"),
    };
    println!("CustomSmartPointer 创建");
    // c 在这里离开作用域，自动调用 drop
}
```

输出：
```
CustomSmartPointer 创建
释放 CustomSmartPointer，数据: '我的数据'
```

### 提前释放

```rust
fn main() {
    let c = CustomSmartPointer {
        data: String::from("提前释放"),
    };

    drop(c);  // 提前释放
    println!("CustomSmartPointer 已提前释放");
}
```

⚠️ 不能手动调用 `c.drop()`，必须用 `std::mem::drop` 函数。

---

## 6. Box 与所有权

```rust
fn main() {
    let b = Box::new(5);
    let b2 = b;  // 所有权移动
    // println!("{}", b);  // ❌ b 已移动

    println!("{}", b2);  // ✅
}
```

```rust
fn main() {
    let mut b = Box::new(5);
    *b += 1;  // 解引用后修改
    println!("{}", b);  // 6
}
```

---

## 实战练习

### 练习 1：二叉树

```rust
#[derive(Debug)]
struct TreeNode<T> {
    value: T,
    left: Option<Box<TreeNode<T>>>,
    right: Option<Box<TreeNode<T>>>,
}

impl<T> TreeNode<T> {
    fn new(value: T) -> TreeNode<T> {
        TreeNode {
            value,
            left: None,
            right: None,
        }
    }

    fn insert_left(&mut self, value: T) {
        self.left = Some(Box::new(TreeNode::new(value)));
    }

    fn insert_right(&mut self, value: T) {
        self.right = Some(Box::new(TreeNode::new(value)));
    }
}

fn main() {
    let mut root = TreeNode::new(1);
    root.insert_left(2);
    root.insert_right(3);

    println!("{:?}", root);
}
```

### 练习 2：自定义智能指针

```rust
use std::ops::Deref;

struct MyBox<T> {
    value: T,
}

impl<T> MyBox<T> {
    fn new(value: T) -> MyBox<T> {
        MyBox { value }
    }
}

impl<T> Deref for MyBox<T> {
    type Target = T;
    fn deref(&self) -> &T {
        &self.value
    }
}

impl<T> Drop for MyBox<T> {
    fn drop(&mut self) {
        println!("MyBox 被释放");
    }
}

fn main() {
    let b = MyBox::new(42);
    println!("值: {}", *b);
}
```

### 练习 3：实现一个栈

```rust
#[derive(Debug)]
struct Stack<T> {
    head: Option<Box<Node<T>>>,
}

#[derive(Debug)]
struct Node<T> {
    value: T,
    next: Option<Box<Node<T>>>,
}

impl<T> Stack<T> {
    fn new() -> Stack<T> {
        Stack { head: None }
    }

    fn push(&mut self, value: T) {
        let new_node = Box::new(Node {
            value,
            next: self.head.take(),
        });
        self.head = Some(new_node);
    }

    fn pop(&mut self) -> Option<T> {
        self.head.take().map(|node| {
            self.head = node.next;
            node.value
        })
    }

    fn peek(&self) -> Option<&T> {
        self.head.as_ref().map(|node| &node.value)
    }

    fn is_empty(&self) -> bool {
        self.head.is_none()
    }
}

fn main() {
    let mut stack = Stack::new();
    stack.push(1);
    stack.push(2);
    stack.push(3);

    println!("栈顶: {:?}", stack.peek());
    println!("弹出: {:?}", stack.pop());
    println!("弹出: {:?}", stack.pop());
    println!("是否为空: {}", stack.is_empty());
}
```

---

## 今日总结

- [ ] 智能指针实现了 `Deref` 和 `Drop` Trait
- [ ] `Box<T>` 在堆上分配，栈上只存指针
- [ ] Box 用于：递归类型、大对象转移、trait 对象
- [ ] `Deref` 允许自定义解引用行为
- [ ] `Deref Coercion` 自动转换引用类型
- [ ] `Drop` 在值离开作用域时自动调用
- [ ] `std::mem::drop` 提前释放值
- [ ] 链表、二叉树等递归数据结构需要 Box

---

*第 13 天 / 86 天*
*第二阶段：所有权与内存 - Box 智能指针*
