# 第 55 天：WebSocket 支持

## 学习目标

- 理解 WebSocket 协议
- 掌握 FastAPI WebSocket 端点
- 实现实时通信功能
- 学会处理连接管理

---

## 1. WebSocket 简介

### HTTP vs WebSocket

| 特性 | HTTP | WebSocket |
|------|------|----------|
| 连接 | 短连接（请求-响应）| 长连接 |
| 方向 | 客户端请求，服务端响应 | 双向通信 |
| 主动推送 | 需轮询/SSE | 服务器主动推送 |
| 适用场景 | REST API | 实时应用、游戏、聊天 |

### 协议握手

```
HTTP 请求（升级）        WebSocket 连接
─────────────────      ─────────────────
GET /ws HTTP/1.1       客户端 ←→ 服务器
Upgrade: websocket      双向通信
Sec-WebSocket-Key: ...  持久连接
                        任意时刻推送
```

---

## 2. FastAPI WebSocket

### 基本端点

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"收到: {data}")
    except WebSocketDisconnect:
        print("客户端断开连接")
```

### 客户端 HTML

```html
<script>
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onopen = () => console.log("连接成功");

    ws.onmessage = (event) => {
        console.log("收到:", event.data);
    };

    ws.send("Hello, Server!");
</script>
```

---

## 3. 连接管理

### 管理活跃连接

```python
from fastapi import FastAPI, WebSocket
from typing import List

app = FastAPI()

# 活跃连接列表
active_connections: List[WebSocket] = []


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            # 广播给所有人
            for connection in active_connections:
                await connection.send_text(f"用户 {user_id}: {data}")
    except Exception:
        pass
    finally:
        active_connections.remove(websocket)
```

### 连接池（更安全）

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict

app = FastAPI()

# 按用户 ID 存储连接
connections: Dict[int, WebSocket] = {}


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    connections[user_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            # 处理消息
            await broadcast(f"用户 {user_id}: {data}")
    except WebSocketDisconnect:
        del connections[user_id]


async def broadcast(message: str):
    for connection in connections.values():
        try:
            await connection.send_text(message)
        except Exception:
            pass
```

---

## 4. JSON 消息

### 消息格式约定

```python
from pydantic import BaseModel
from typing import Literal

class WSMessage(BaseModel):
    type: str  # "chat", "notification", "system"
    data: dict
    sender_id: int | None = None


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()

    try:
        while True:
            # 接收 JSON
            raw_data = await websocket.receive_text()
            message = WSMessage.model_validate_json(raw_data)

            # 处理不同类型
            if message.type == "chat":
                await broadcast_chat(user_id, message)
            elif message.type == "notification":
                await send_notification(message)

    except WebSocketDisconnect:
        pass
```

### JSON 响应

```python
async def send_json(websocket: WebSocket, message_type: str, data: dict):
    response = {
        "type": message_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
    }
    await websocket.send_json(response)
```

---

## 5. WebSocket + Redis

### 发布/订阅模式

```python
import redis.asyncio as redis
import json

redis_client = None


async def init_redis():
    global redis_client
    redis_client = redis.from_url("redis://localhost")


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()

    # 订阅用户频道
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"user:{user_id}")

    try:
        while True:
            # 接收客户端消息
            try:
                data = await websocket.receive_text()
                # 处理消息...
            except Exception:
                pass

            # 检查 Redis 消息
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                await websocket.send_text(message["data"])

    finally:
        await pubsub.unsubscribe(f"user:{user_id}")
```

---

## 6. 实时通知示例

### 完整实现

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel
from datetime import datetime
import asyncio

app = FastAPI()


class Notification(BaseModel):
    user_id: int
    title: str
    message: str
    created_at: datetime = datetime.utcnow()


# 存储活跃连接
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        self.active_connections.pop(user_id, None)

    async def send_notification(self, user_id: int, notification: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(notification)


manager = ConnectionManager()


@app.websocket("/ws/notifications/{user_id}")
async def notification_websocket(user_id: int, websocket: WebSocket):
    await manager.connect(user_id, websocket)
    try:
        while True:
            # 保持连接
            data = await websocket.receive_text()
            # 处理心跳等
    except WebSocketDisconnect:
        manager.disconnect(user_id)


@app.post("/notifications/{user_id}")
async def send_notification(user_id: int, notification: Notification):
    await manager.send_notification(user_id, notification.model_dump(mode="json"))
    return {"status": "sent"}
```

---

## 今日总结

- [ ] WebSocket 提供双向实时通信
- [ ] `websocket.accept()` 接受连接
- [ ] `receive_text()`/`send_text()` 收发消息
- [ ] `WebSocketDisconnect` 处理断开
- [ ] 连接管理：用字典按用户 ID 存储
- [ ] `send_json()` 发送 JSON 格式
- [ ] Redis Pub/Sub 实现跨服务推送

---

*第 55 天 / 330 天*
*第二阶段：FastAPI 进阶 - WebSocket*