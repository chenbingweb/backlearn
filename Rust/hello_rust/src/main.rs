use chrono::Local;
const MAX_AGE:u32= 1000_000;
fn main() {
    println!("Hello, world!");
    println!("{},{}!","hello","Rust");
    println!("{name}今年{age}岁",name="lili",age="23");
    let now = Local::now();
    println!("当前时间: {}", now.format("%Y-%m-%d %H:%M:%S"));
    println!("最大年龄: {}", MAX_AGE);
    let i:u8=0;
    let c = i.checked_add(1);
    println!("c: {:?}", c.unwrap());
    println!("i: {}", i);
    let t = true;
    println!("t: {}", t);
    if t {
        println!("t is true");
    }
    else {
        println!("t is false");
    }

    let tup:(i32,f64,&str) = (1,2.0,"hello");
    println!("tup: {:?}", tup);
    let (x,y,z) = tup;
    println!("x: {}", x);
    println!("y: {}", y);
    println!("z: {}", z);
    println!("z.len(): {}", z.len());
    println!("z-: {}", tup.2);

    let a = [1,2,3,4,5];
    let b: [i32; 5] =[1,2,3,4,5];
    let c =[3;4];

    println!("a: {:?}", a);
    println!("b: {:?}", b);
    println!("c: {:?}", c);

    let slice = &a[1..3];
    println!("slice: {:?}", slice);
    println!("slice.len(): {}", slice.len());
    println!("add:{}", add(1,2));

    let y = {
        let a=1;
        let b=2;
        a+b
    };
    println!("y: {}", y);
    let i = rloop();
    println!("i: {}", i);

    let num = 10;
    match num {
        10 => println!("num is 10"),
        _ => println!("num is not 10"),
    }
}

fn add(a: i32, b: i32) -> i32 {
    a + b
}

fn rloop() -> i32 {
    let mut i = 0;
    loop {
        println!("hello world");
        i += 1;
        if i > 5 {
            break i;
        }
    }
}
