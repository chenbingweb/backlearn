# 第 43 天：Redis Cluster 集群

## 学习目标

- 理解 Redis 集群架构
- 掌握集群部署配置
- 学会客户端路由
- 掌握集群故障转移

---

## 1. Redis Cluster 架构

### 为什么需要集群

```markdown
单机 Redis 问题：
┌─────────────────────────────────────┐
│            单机 Redis                  │
├─────────────────────────────────────┤
│  容量限制：物理内存上限                 │
│  并发限制：单机 CPU 处理能力            │
│  可用性：宕机则服务不可用              │
└─────────────────────────────────────┘

集群解决方案：
┌─────────┬─────────┬─────────┐
│ Node 1  │ Node 2  │ Node 3  │
│ Master  │ Master  │ Master  │
├─────────┼─────────┼─────────┤
│ Slave 1 │ Slave 2 │ Slave 3 │
└─────────┴─────────┴─────────┘

- 容量分片：数据分布在多个节点
- 并发提升：多节点并行处理
- 高可用：主从复制 + 故障转移
```

### 数据分片

```markdown
Redis Cluster 使用 16384 个槽（slot）进行分片

┌────────────────────────────────────────────────────┐
│                  16384 个槽                        │
├──────┬──────┬──────┬──────┬──────┬──────┬─────────┤
│ 0    │ 5460 │ 5461 │10922 │10923 │16383 │         │
│      │      │      │      │      │      │         │
│ Master1│ Master2│ Master3│ Master4│ Master5│ Master6│
│(从)  │ (从)  │ (从)  │ (从)  │ (从)  │ (从)   │
└──────┴──────┴──────┴──────┴──────┴──────┴─────────┘

数据分配：CRC16(key) mod 16384 = slot

节点扩容时：重新分配槽，数据迁移
```

### 集群结构

```
┌─────────────────────────────────────────────────────┐
│                   Redis Cluster                       │
├─────────────┬─────────────┬─────────────────────────┤
│   节点 1    │   节点 2    │       节点 3            │
│  Master A   │  Master B   │      Master C            │
│ (0-5460)   │(5461-10922) │    (10923-16383)        │
├─────────────┼─────────────┼─────────────────────────┤
│  Slave A'   │  Slave B'   │       Slave C'          │
│ (从属A)    │ (从属B)     │      (从属C)            │
└─────────────┴─────────────┴─────────────────────────┘
```

---

## 2. 集群部署

### 配置文件

```bash
# redis-node-1.conf
port 6379
cluster-enabled yes
cluster-config-file nodes-6379.conf
cluster-node-timeout 15000
cluster-replica-validity-factor 10
cluster-migration-barrier 1
daemonize no

# 节点 2
port 6380
cluster-enabled yes
cluster-config-file nodes-6380.conf
...

# 节点 3
port 6381
cluster-enabled yes
cluster-config-file nodes-6381.conf
...
```

### 启动集群

```bash
# 启动所有节点
redis-server redis-node-1.conf
redis-server redis-node-2.conf
redis-server redis-node-3.conf
redis-server redis-node-4.conf
redis-server redis-node-5.conf
redis-server redis-node-6.conf

# 创建集群
redis-cli --cluster create \
  127.0.0.1:6379 \
  127.0.0.1:6380 \
  127.0.0.1:6381 \
  127.0.0.1:6382 \
  127.0.0.1:6383 \
  127.0.0.1:6384 \
  --cluster-replicas 1
```

### Docker Compose 部署

```yaml
version: '3.8'

services:
  redis-node1:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --port 6379
    ports:
      - "6379:6379"
    volumes:
      - redis1:/data

  redis-node2:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --port 6379
    ports:
      - "6380:6379"
    volumes:
      - redis2:/data

  redis-node3:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --port 6379
    ports:
      - "6381:6379"
    volumes:
      - redis3:/data

  redis-node4:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --port 6379
    ports:
      - "6382:6379"
    volumes:
      - redis4:/data

  redis-node5:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --port 6379
    ports:
      - "6383:6379"
    volumes:
      - redis5:/data

  redis-node6:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --port 6379
    ports:
      - "6384:6379"
    volumes:
      - redis6:/data

volumes:
  redis1:
  redis2:
  redis3:
  redis4:
  redis5:
  redis6:
```

---

## 3. 集群管理命令

### 节点管理

```bash
# 查看集群信息
redis-cli -c -p 6379 CLUSTER INFO

# 查看节点列表
redis-cli -c -p 6379 CLUSTER NODES

# 节点角色说明
# master-ID slot1,slot2,...  slave-of master-ID

# 添加节点
redis-cli --cluster add-node 127.0.0.1:6385 127.0.0.1:6379

# 删除节点
redis-cli --cluster del-node 127.0.0.1:6385 node-id

# 设置为主从
redis-cli -c -p 6385 CLUSTER REPLICATE master-node-id
```

### 槽管理

```bash
# 查看槽分布
redis-cli -c -p 6379 CLUSTER SLOTS

# 重新分配槽
redis-cli --cluster reshard 127.0.0.1:6379

# 迁移槽步骤
# 1. 指定目标节点
# 2. 指定源节点（可以是多个）
# 3. 指定迁移槽数量

# 平衡槽分布
redis-cli --cluster rebalance 127.0.0.1:6379
```

### 故障转移

```bash
# 手动故障转移（从节点执行）
redis-cli -c -p 6382 CLUSTER FAILOVER

# 触发条件
# 1. 主节点不可达（超过 node-timeout）
# 2. 手动 FAILOVER 命令
# 3. 集群管理员介入
```

---

## 4. Python 客户端

### redis-py-cluster

```bash
pip install redis-py-cluster
```

```python
from rediscluster import RedisCluster

# 集群连接
startup_nodes = [
    {'host': '127.0.0.1', 'port': 6379},
    {'host': '127.0.0.1', 'port': 6380},
    {'host': '127.0.0.1', 'port': 6381},
]

rc = RedisCluster(
    startup_nodes=startup_nodes,
    decode_responses=True,
    skip_full_coverage_check=True
)

# 集群操作
rc.set('name', 'Alice')      # 自动路由到正确节点
value = rc.get('name')

# MGET/MSET 自动分片
rc.mset({'k1': 'v1', 'k2': 'v2', 'k3': 'v3'})
rc.mget(['k1', 'k2', 'k3'])
```

### 槽计算

```python
import crc16

def get_slot(key):
    """计算 key 对应的槽"""
    # Redis 集群使用 CRC16 计算槽
    return crc16.crc16(key.encode()) % 16384

# 示例
print(get_slot('user:1001'))  # 例如：5460
print(get_slot('order:2001')) # 例如：12345
```

### 哈希标签

```python
# 哈希标签：确保相关 key 在同一槽
# 语法：{tag}actual_key

# user:1001:profile 和 user:1001:orders 会在同一槽
rc.set('user:{1001}:profile', '{"name":"Alice"}')
rc.set('user:{1001}:orders', '[1,2,3]')

# 不使用哈希标签
rc.set('user:1001:profile', '...')  # 可能在槽 A
rc.set('user:1002:orders', '...')    # 可能在槽 B
```

---

## 5. 集群高可用

### 故障检测

```markdown
故障检测流程：

1. 节点间心跳（PING/PONG）
   - 每秒发送一次
   - 超过 node-timeout（默认15秒）未响应认为宕机

2. 主观下线（SDOWN）
   - 单个节点认为其他节点不可达

3. 客观下线（ODOWN）
   - 多数主节点认为某节点不可达
   - 需要 >= (N/2 + 1) 个主节点同意

4. 故障转移
   - 从节点自动升级为主节点
   - 其他节点更新配置
   - 故障节点恢复后成为从节点
```

### 故障转移过程

```markdown
主节点 A 宕机：
      │
      ▼
从节点 A' 检测到主节点不可达
      │
      ▼
从节点 A' 发起 FAILOVER 请求
      │
      ▼
其他主节点投票同意
      │
      ▼
A' 成为新主节点
      │
      ▼
A' 向集群广播 NEW NODE 消息
      │
      ▼
其他节点更新配置
      │
      ▼
原主节点 A 恢复，成为 A' 的从节点
```

### 脑裂问题

```markdown
Redis Cluster 脑裂：

    ┌─────────────────┐
    │   网络分区      │
    └─────────────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐ ┌─────────┐
│ 分区 1  │ │ 分区 2  │
│ A(B主)  │ │ A'(C主) │
│ C(从)   │ │ B(从)   │
└─────────┘ └─────────┘

问题：两个分区都认为自己是主节点，都接受写入

解决：
- Redis Cluster 要求写入多数派节点才算成功
- 分区 1 只有 1 个主节点（需要 2 个）
- 分区 2 只有 1 个主节点（需要 2 个）
- 两个分区都无法写入
```

---

## 6. 集群客户端路由

### MOVED 重定向

```bash
# 客户端连接到任意节点
redis-cli -c -p 6379

# 尝试获取 key
GET user:1001
# 返回：MOVED 5460 127.0.0.1:6380
# 客户端自动重定向到正确节点
```

### ASK 重定向

```bash
# 数据迁移时的临时重定向
# MOVED：永久重定向，槽已迁移完成
# ASK：临时重定向，槽迁移中

GET user:1001
# 返回：ASK 12345 127.0.0.1:6380
# 客户端先发送 ASKING，再到目标节点获取
```

### Python 客户端自动处理

```python
from rediscluster import RedisCluster

rc = RedisCluster(...)

# 客户端自动处理 MOVED/ASK 重定向
# 程序员无需关心槽分布

# 但需要注意：
# 1. 不支持跨槽操作（除非使用哈希标签）
# 2. Pipeline 只能包含同一槽的 key
```

### 跨槽操作

```python
# ❌ 不支持：多个槽的 key 无法在同一命令中
rc.mget(['key1', 'key2', 'key3'])  # 可能在不同槽

# ✅ 支持：使用哈希标签确保在同一槽
rc.mget(['user:{1001}:profile', 'user:{1001}:orders'])

# ✅ 支持：单槽操作
rc.set('user:{1001}:profile', 'data')
rc.get('user:{1001}:profile')
```

---

## 7. 集群监控

### 查看集群状态

```python
def get_cluster_info(rc):
    """获取集群信息"""
    info = rc.info('cluster')
    return {
        'cluster_state': info.get('cluster_state'),
        'cluster_slots_assigned': info.get('cluster_slots_assigned'),
        'cluster_slots_ok': info.get('cluster_slots_ok'),
        'cluster_nodes': info.get('cluster_nodes'),
    }

def get_nodes_info(rc):
    """获取所有节点信息"""
    nodes = rc.cluster('nodes').split('\n')
    result = []

    for node in nodes:
        if not node:
            continue

        parts = node.split()
        # 格式：node-id role ip:port @ master slots
        result.append({
            'node_id': parts[0],
            'role': parts[1],
            'address': parts[2].split('@')[0],
        })

    return result
```

### 健康检查

```python
import redis
from rediscluster import RedisCluster

def health_check_cluster(startup_nodes):
    """集群健康检查"""
    try:
        rc = RedisCluster(
            startup_nodes=startup_nodes,
            decode_responses=True,
            skip_full_coverage_check=True
        )

        # 检查所有节点
        all_healthy = True
        node_status = {}

        for node in startup_nodes:
            try:
                r = redis.Redis(host=node['host'], port=node['port'])
                r.ping()
                node_status[f"{node['host']}:{node['port']}"] = 'UP'
            except:
                node_status[f"{node['host']}:{node['port']}"] = 'DOWN'
                all_healthy = False

        # 检查槽分布
        slots_info = rc.cluster('slots')

        return {
            'healthy': all_healthy,
            'node_status': node_status,
            'slots_info': slots_info,
        }

    except Exception as e:
        return {
            'healthy': False,
            'error': str(e)
        }
```

---

## 今日总结

- [ ] Redis Cluster：16384 个槽分片
- [ ] 节点角色：Master + Slave
- [ ] 故障转移：从节点自动升级
- [ ] 写入多数派：`N/2 + 1` 节点确认
- [ ] MOVED 重定向：永久槽迁移
- [ ] ASK 重定向：迁移中临时重定向
- [ ] 哈希标签：`{tag}key` 确保同槽

---

*第 43 天 / 330 天*
*Python 后端 - Redis Cluster 集群*
