# 第 56 天：后台任务 Celery

## 学习目标

- 理解任务队列的概念
- 掌握 Celery 异步任务
- 学会使用 Redis 作为 broker
- 实现定时任务

---

## 1. 任务队列简介

### 为什么要用任务队列

| 操作 | 同步 | 异步（Celery）|
|------|------|---------------|
| 发送邮件 | 等待发送完成 | 立即返回，异步发送 |
| 生成报表 | 等待生成 | 立即返回，后台生成 |
| 批量处理 | 顺序执行 | 并行分发执行 |
| 爬虫抓取 | 串行请求 | 并发多 worker |

### Celery 架构

```
App → Redis → Celery Worker → 执行任务
        ↑
      结果存储
```

---

## 2. 安装和配置

### 安装

```bash
pip install celery redis
```

### Celery 配置

```python
# app/celery_config.py
from celery import Celery

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

# 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 分钟超时
    worker_prefetch_multiplier=4,
)
```

---

## 3. 定义任务

### 基本任务

```python
# app/tasks.py
from app.celery_config import celery_app
import time


@celery_app.task
def send_email(to: str, subject: str, body: str):
    """发送邮件任务"""
    print(f"发送邮件到 {to}")
    time.sleep(2)  # 模拟发送时间
    print(f"邮件已发送: {subject}")
    return {"status": "sent", "to": to}


@celery_app.task
def process_report(report_id: int):
    """生成报表"""
    print(f"生成报表 {report_id}")
    time.sleep(5)
    print("报表已生成")
    return {"report_id": report_id, "status": "completed"}
```

### 路由配置

```python
@celery_app.task(name="tasks.send_email", bind=True)
def send_email(self, to: str, subject: str, body: str):
    # bind=True 时，self 是任务对象
    print(f"任务 ID: {self.request.id}")
    ...
```

---

## 4. 调用任务

### 异步调用

```python
# FastAPI 端点
from fastapi import FastAPI
from app.tasks import send_email

app = FastAPI()


@app.post("/send-email")
async def send_email_endpoint(to: str, subject: str, body: str):
    # 立即返回任务 ID
    task = send_email.delay(to, subject, body)
    return {"task_id": task.id, "status": "pending"}
```

### 检查任务状态

```python
@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    task = send_email.AsyncResult(task_id)

    if task.state == "PENDING":
        response = {"state": task.state, "status": "等待执行"}
    elif task.state == "SUCCESS":
        response = {"state": task.state, "result": task.result}
    elif task.state == "FAILURE":
        response = {"state": task.state, "error": str(task.info)}
    else:
        response = {"state": task.state}

    return response
```

### 等待结果

```python
# 同步等待（不推荐在 FastAPI 中使用）
@app.post("/send-email-sync")
async def send_email_sync(to: str, subject: str, body: str):
    task = send_email.delay(to, subject, body)
    result = task.get(timeout=30)  # 等待最多 30 秒
    return result
```

---

## 5. 定时任务

### 配置 beat

```python
# app/celery_config.py
celery_app.conf.beat_schedule = {
    "every-5-minutes-cleanup": {
        "task": "tasks.cleanup_expired_sessions",
        "schedule": 300.0,  # 5 分钟
    },
    "daily-report-at-midnight": {
        "task": "tasks.generate_daily_report",
        "schedule": crontab(hour=0, minute=0),
    },
}
```

### Crontab 表达式

```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # 每天凌晨 2 点
    "daily-at-2am": {
        "task": "tasks.backup_database",
        "schedule": crontab(hour=2, minute=0),
    },
    # 每周一早上 9 点
    "weekly-monday-9am": {
        "task": "tasks.send_weekly_digest",
        "schedule": crontab(hour=9, minute=0, day_of_week=1),
    },
    # 每月 1 号凌晨
    "monthly-report": {
        "task": "tasks.generate_monthly_report",
        "schedule": crontab(0, 0, day_of_month=1),
    },
}
```

---

## 6. 任务链与组

### 任务链

```python
from celery import chain

# 顺序执行
@app.post("/process-order/{order_id}")
async def process_order(order_id: int):
    # 先验证，再支付，最后发货
    chain(
        validate_order.s(order_id),
        process_payment.s(),
        ship_order.s(),
    ).delay()
    return {"status": "processing"}
```

### 任务组

```python
from celery import group

# 并行执行
@app.post("/bulk-notification")
async def send_bulk_notification(user_ids: list[int]):
    group(
        send_email.s(user_id, "公告", "内容")
        for user_id in user_ids
    ).delay()
    return {"status": "sent", "count": len(user_ids)}
```

### 回调

```python
@celery_app.task
def process_data(data: str):
    return f"Processed: {data}"


@celery_app.task
def notify_complete(result):
    print(f"处理完成: {result}")


# 链接 + 回调
process_data.s("test data") | notify_complete.s()
```

---

## 7. 启动服务

### 启动 Worker

```bash
# 启动 Worker
celery -A app.celery_config worker --loglevel=info

# 指定队列
celery -A app.celery_config worker -Q celery,email --loglevel=info
```

### 启动 Beat（定时任务）

```bash
celery -A app.celery_config beat --loglevel=info
```

### 启动 Redis（Broker）

```bash
redis-server
```

---

## 实战练习

### 练习：图片处理任务

```python
# app/tasks.py
from app.celery_config import celery_app
from PIL import Image
import io


@celery_app.task(bind=True)
def generate_thumbnail(self, image_id: int, size: tuple[int, int]):
    """生成缩略图"""
    # 1. 从数据库获取图片信息
    image = get_image(image_id)
    if not image:
        self.update_state(state="FAILURE", meta="Image not found")
        return

    self.update_state(state="PROCESSING", meta={"progress": 50})

    # 2. 处理图片
    img = Image.open(image.path)
    img.thumbnail(size)
    thumb_io = io.BytesIO()
    img.save(thumb_io, format="JPEG")

    # 3. 保存缩略图
    save_thumbnail(image_id, thumb_io.getvalue())

    return {"image_id": image_id, "thumbnail": f"/images/{image_id}_thumb.jpg"}
```

---

## 今日总结

- [ ] 任务队列用于异步执行耗时任务
- [ ] Celery = Worker + Broker(Redis) + Backend
- [ ] `@celery_app.task` 定义任务
- [ ] `.delay()` 异步调用，`.get()` 同步等待
- [ ] `AsyncResult` 检查任务状态
- [ ] `beat_schedule` 配置定时任务
- [ ] `crontab` 表达式精确控制执行时间

---

*第 56 天 / 330 天*
*第二阶段：FastAPI 进阶 - Celery 任务队列*