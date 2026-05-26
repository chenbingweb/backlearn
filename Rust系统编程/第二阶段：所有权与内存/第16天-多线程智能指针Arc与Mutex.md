# 第 16 天：多线程智能指针 Arc 与 Mutex

## 学习目标

- 理解 Arc 线程安全的引用计数
- 掌握 Mutex 互斥锁的使用
- 学习 RwLock 读写锁
- 了解 Send 和 Sync Trait

---

## 1. Arc：线程安全的 Rc

### Arc 基本用法

`Arc<T>`（Atomic Reference Counted）是线程安全的 `Rc<T>`：

```rust
use std::sync::Arc;
use std::thread;

fn main() {
    let data = Arc::new(5);

    let data_clone = Arc::clone(&data);
    let handle = thread::spawn(move || {
        println!("子线程: {}", data_clone);
    });

    println!("主线程: {}", data);
    handle.join().unwrap();
}
```

### Arc 的内部实现

```
Arc 使用原子操作（Atomic）管理引用计数：
- strong_count: AtomicUsize
- weak_count: AtomicUsize

原子操作保证线程安全，但比 Rc 的普通整数操作稍慢。
```

### Arc vs Rc

| 特性 | Rc<T> | Arc<T> |
|------|-------|--------|
| 线程安全 | 否 | 是（原子操作）|
| 性能 | 更快 | 稍慢 |
| 适用场景 | 单线程 | 多线程 |

---

## 2. Mutex：互斥锁

### 基本用法

```rust
use std::sync::Mutex;

fn main() {
    let m = Mutex::new(5);

    {
        let mut num = m.lock().unwrap();  // 获取锁
        *num = 6;                          // 修改数据
    } // 锁在这里自动释放

    println!("m = {:?}", m);
}
```

### 多线程共享数据

```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];

    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            let mut num = counter.lock().unwrap();
            *num += 1;
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("结果: {}", *counter.lock().unwrap());  // 10
}
```

### 避免死锁

```rust
use std::sync::{Arc, Mutex};

fn main() {
    let a = Arc::new(Mutex::new(1));
    let b = Arc::new(Mutex::new(2));

    // 错误：可能导致死锁
    // 线程1: lock(a) → lock(b)
    // 线程2: lock(b) → lock(a)

    // 正确：总是以相同顺序获取锁
    let mut num1 = a.lock().unwrap();
    let mut num2 = b.lock().unwrap();
    *num1 += *num2;
}
```

### lock() 返回的 MutexGuard

```rust
use std::sync::Mutex;

fn main() {
    let m = Mutex::new(5);

    let guard = m.lock().unwrap();
    println!("锁定: {}", *guard);
    // guard 离开作用域自动释放锁
}
```

`lock()` 返回 `LockResult<MutexGuard<T>>`：
- `Ok(guard)` — 获取锁成功
- `Err(PoisonError)` — 其他线程 panic 导致锁中毒

---

## 3. RwLock：读写锁

### 读多写少的场景

```rust
use std::sync::RwLock;

fn main() {
    let lock = RwLock::new(5);

    // 多个读锁可以同时持有
    let r1 = lock.read().unwrap();
    let r2 = lock.read().unwrap();
    println!("读: {}, {}", *r1, *r2);
    drop(r1);
    drop(r2);

    // 写锁独占
    let mut w = lock.write().unwrap();
    *w += 1;
    println!("写后: {}", *w);
}
```

### RwLock vs Mutex

| 特性 | Mutex | RwLock |
|------|-------|--------|
| 读 | 独占 | 共享 |
| 写 | 独占 | 独占 |
| 适用场景 | 读写均衡 | 读多写少 |
| 开销 | 较小 | 稍大 |

---

## 4. Send 和 Sync Trait

### 自动派生规则

```
Send: 类型可以在线程间转移所有权
  - 几乎所有类型都是 Send
  - Rc 不是 Send

Sync: 类型可以在线程间共享引用（&T 是 Send）
  - 如果 &T 是 Send，则 T 是 Sync
  - RefCell 不是 Sync（没有同步机制）
  - Mutex<T> 是 Sync（即使 T 不是）
```

### 类型分类

| 类型 | Send | Sync |
|------|------|------|
| i32, String | ✅ | ✅ |
| Rc<T> | ❌ | ❌ |
| RefCell<T> | ✅ | ❌ |
| Arc<T> | ✅ | ✅（T: Sync）|
| Mutex<T> | ✅ | ✅（T: Send）|

---

## 5. 多线程编程模式

### 模式1：工作线程池

```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let data = Arc::new(Mutex::new(vec![1, 2, 3, 4, 5]));
    let results = Arc::new(Mutex::new(Vec::new()));

    let mut handles = vec![];

    for i in 0..5 {
        let data = Arc::clone(&data);
        let results = Arc::clone(&results);

        let handle = thread::spawn(move || {
            let val = data.lock().unwrap()[i];
            let squared = val * val;
            results.lock().unwrap().push(squared);
        });

        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("结果: {:?}", results.lock().unwrap());
}
```

### 模式2：消息传递

```rust
use std::sync::mpsc;
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel();

    thread::spawn(move || {
        let val = String::from("来自子线程的消息");
        tx.send(val).unwrap();
    });

    let received = rx.recv().unwrap();
    println!("收到: {}", received);
}
```

### 模式3：共享状态 + 消息

```rust
use std::sync::{mpsc, Arc, Mutex};
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel();
    let counter = Arc::new(Mutex::new(0));

    for i in 0..3 {
        let tx = tx.clone();
        let counter = Arc::clone(&counter);

        thread::spawn(move || {
            let mut count = counter.lock().unwrap();
            *count += 1;
            tx.send(format!("线程 {} 完成", i)).unwrap();
        });
    }

    drop(tx);  // 关闭发送端

    for msg in rx {
        println!("{}", msg);
    }

    println!("总计: {}", *counter.lock().unwrap());
}
```

---

## 实战练习

### 练习 1：并发计数器

```rust
use std::sync::{Arc, Mutex};
use std::thread;

struct ConcurrentCounter {
    value: Arc<Mutex<i32>>,
}

impl ConcurrentCounter {
    fn new() -> ConcurrentCounter {
        ConcurrentCounter {
            value: Arc::new(Mutex::new(0)),
        }
    }

    fn increment(&self) {
        let mut val = self.value.lock().unwrap();
        *val += 1;
    }

    fn get(&self) -> i32 {
        *self.value.lock().unwrap()
    }

    fn clone(&self) -> ConcurrentCounter {
        ConcurrentCounter {
            value: Arc::clone(&self.value),
        }
    }
}

fn main() {
    let counter = ConcurrentCounter::new();
    let mut handles = vec![];

    for _ in 0..100 {
        let c = counter.clone();
        let handle = thread::spawn(move || {
            c.increment();
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("最终计数: {}", counter.get());
}
```

### 练习 2：共享的日志系统

```rust
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

#[derive(Debug)]
struct Logger {
    messages: Arc<Mutex<Vec<String>>>,
}

impl Logger {
    fn new() -> Logger {
        Logger {
            messages: Arc::new(Mutex::new(Vec::new())),
        }
    }

    fn log(&self, msg: &str) {
        let mut messages = self.messages.lock().unwrap();
        messages.push(String::from(msg));
    }

    fn get_messages(&self) -> Vec<String> {
        self.messages.lock().unwrap().clone()
    }

    fn clone(&self) -> Logger {
        Logger {
            messages: Arc::clone(&self.messages),
        }
    }
}

fn main() {
    let logger = Logger::new();
    let mut handles = vec![];

    for i in 0..5 {
        let log = logger.clone();
        let handle = thread::spawn(move || {
            log.log(&format!("线程 {} 启动", i));
            thread::sleep(Duration::from_millis(10));
            log.log(&format!("线程 {} 完成", i));
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    for msg in logger.get_messages() {
        println!("{}", msg);
    }
}
```

---

## 今日总结

- [ ] `Arc<T>` 是线程安全的引用计数，用原子操作
- [ ] `Mutex<T>` 互斥锁，同一时间只有一个线程能访问数据
- [ ] `RwLock<T>` 读写锁，多个读或一个写
- [ ] `lock()` 返回 `MutexGuard`，离开作用域自动释放
- [ ] `Send` 表示可以跨线程转移所有权
- [ ] `Sync` 表示可以跨线程共享引用
- [ ] `Arc<Mutex<T>>` 是多线程共享可变数据的标准组合
- [ ] 避免死锁：总是以相同顺序获取多个锁
- [ ] `mpsc::channel()` 用于线程间消息传递

---

*第 16 天 / 86 天*
*第二阶段：所有权与内存 - Arc 与 Mutex*
