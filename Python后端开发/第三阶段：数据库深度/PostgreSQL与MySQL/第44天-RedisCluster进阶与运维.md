# 第 44 天：Redis Cluster 进阶与运维

## 学习目标

- 深入理解 Redis Cluster 架构
- 掌握集群运维操作
- 学会故障处理
- 掌握扩缩容操作

---

## 1. Redis Cluster 深入理解

### 集群通信

```markdown
集群节点间通信：

┌─────────────────────────────────────────────────┐
│                   Gossip 协议                     │
├─────────────────────────────────────────────────┤
│  每个节点定期向其他节点发送：                       │
│  1. 自己的状态                                   │
│  2. 知道的其他节点状态                             │
│  3. 配置信息                                     │
└─────────────────────────────────────────────────┘

Gossip 优点：
- 去中心化，无需中心协调
- 故障检测自动进行
- 扩缩容自动传播

Gossip 缺点：
- 状态同步有延迟
- 可能传播过期信息
```

### 槽迁移

```markdown
槽迁移过程：

阶段1：目标节点准备接收
       目标节点：CLUSTER SETSLOT <slot> IMPORTING <source_node_id>

阶段2：源节点准备迁出
       源节点：CLUSTER SETSLOT <slot> MIGRATING <target_node_id>

阶段3：客户端重定向
       ASK 重定向（临时）
       MOVED 重定向（永久）

阶段4：完成迁移
       所有节点更新槽归属
```

### 故障检测

```markdown
故障检测过程：

1. 主观下线（SDOWN）
   - 节点向目标节点发送 PING
   - 超过 node-timeout 未收到 PONG
   - 该节点认为目标节点下线

2. 客观下线（ODOWN）
   - 主节点收到其他主节点的 SDOWN 报告
   - 多数主节点认为该节点下线
   - 触发故障转移

3. 故障转移
   - 从节点被选为新主节点
   - 向集群广播消息
   - 更新所有节点的配置
```

---

## 2. 集群运维

### 节点管理

```bash
# 查看集群状态
redis-cli -c -p 7000 CLUSTER INFO

# 查看所有节点
redis-cli -c -p 7000 CLUSTER NODES

# 节点角色
# myself,master - 主节点
# master - 主节点
# slave - 从节点
# handshake - 握手状态
# fail? - 主观下线
# fail - 客观下线

# 添加从节点
redis-cli -c -p 7000 CLUSTER REPLICATE <master-node-id>

# 查看从节点列表
redis-cli -c -p 7000 INFO REPLICATION

# 移除从节点
redis-cli -c -p 7000 CLUSTER FORGET <node-id>
```

### 槽管理

```bash
# 查看槽分布
redis-cli -c -p 7000 CLUSTER SLOTS

# 重新分配槽
redis-cli --cluster reshard 127.0.0.1:7000

# 交互式重新分配
# 1. 选择目标节点
# 2. 选择源节点（可以多个）
# 3. 输入要迁移的槽数量

# 平衡槽分布
redis-cli --cluster rebalance 127.0.0.1:7000

# 迁移指定槽
redis-cli --cluster reshard 127.0.0.1:7000 \
  --cluster-from <source-node-id> \
  --cluster-to <target-node-id> \
  --cluster-slots <slot-count>
```

### 扩缩容

```bash
# ============ 扩容步骤 ============

# 1. 启动新节点
redis-server --port 7006 --cluster-enabled yes

# 2. 添加新节点到集群
redis-cli --cluster add-node 127.0.0.1:7006 127.0.0.1:7000

# 3. 为新节点添加从节点（可选）
redis-cli --cluster add-node 127.0.0.1:7007 127.0.0.1:7000 \
  --cluster-slave --cluster-master-id <new-master-id>

# 4. 重新分配槽
redis-cli --cluster rebalance 127.0.0.1:7000 \
  --cluster-weight <new-node-id>=1.5

# ============ 缩容步骤 ============

# 1. 将槽迁出
redis-cli --cluster rebalance 127.0.0.1:7000 \
  --cluster-weight <node-to-remove>=0

# 2. 删除从节点
redis-cli --cluster del-node 127.0.0.1:7007 <node-id>

# 3. 删除主节点
redis-cli --cluster del-node 127.0.0.1:7006 <node-id>
```

---

## 3. Python 客户端进阶

### 客户端选择

```python
# 1. redis-py-cluster（推荐）
from rediscluster import RedisCluster

startup_nodes = [
    {'host': '127.0.0.1', 'port': 7000},
    {'host': '127.0.0.1', 'port': 7001},
    {'host': '127.0.0.1', 'port': 7002},
]

rc = RedisCluster(
    startup_nodes=startup_nodes,
    decode_responses=True,
    skip_full_coverage_check=True,
    max_connections_per_node=True
)

# 2. 槽计算
def get_slot(key):
    """计算 key 的槽"""
    import crc16
    return crc16.crc16(key.encode()) % 16384

# 3. 哈希标签
# 确保相关 key 在同一槽
rc.set('user:{1001}:profile', data)
rc.set('user:{1001}:orders', data)
```

### 跨槽操作

```python
# Cluster 不支持跨槽的原子操作
# 但可以分批处理

def mget_cluster(rc, keys):
    """跨槽 MGET"""
    # 按槽分组
    slots = {}
    for key in keys:
        slot = get_slot(key)
        if slot not in slots:
            slots[slot] = []
        slots[slot].append(key)

    # 分槽获取
    result = {}
    for slot, slot_keys in slots.items():
        # 同一槽的 key 可以批量获取
        values = rc.mget(slot_keys)
        for k, v in zip(slot_keys, values):
            result[k] = v

    return result


def mset_cluster(rc, data_dict):
    """跨槽 MSET"""
    # 按槽分组
    slots = {}
    for key, value in data_dict.items():
        slot = get_slot(key)
        if slot not in slots:
            slots[slot] = {}
        slots[slot][key] = value

    # 分槽写入
    for slot, slot_data in slots.items():
        rc.mset(slot_data)
```

### 故障处理

```python
from rediscluster import RedisCluster
import redis

class ClusterClient:
    """带故障处理的集群客户端"""

    def __init__(self, startup_nodes):
        self.startup_nodes = startup_nodes
        self.rc = RedisCluster(
            startup_nodes=startup_nodes,
            decode_responses=True,
            skip_full_coverage_check=True
        )

    def get_node_by_slot(self, slot):
        """根据槽获取节点"""
        return self.rc.get_node_from_slot(slot)

    def execute_with_retry(self, func, *args, **kwargs):
        """带重试的执行"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except redis.RedisClusterException as e:
                if 'MOVED' in str(e) or 'ASK' in str(e):
                    # 客户端自动处理重定向
                    # 重建连接
                    self.rc = RedisCluster(
                        startup_nodes=self.startup_nodes,
                        decode_responses=True,
                    )
                else:
                    if attempt == max_retries - 1:
                        raise
```

---

## 4. 故障处理

### 常见故障

```markdown
常见故障及处理：

1. 主节点宕机
   - 自动故障转移
   - 从节点升级为主节点
   - 无需人工干预

2. 多个主节点宕机
   - 集群不可用
   - 需要人工干预
   - 恢复宕机节点

3. 网络分区
   - 可能产生脑裂
   - 少数派分区无法写入
   - 分区恢复后同步数据

4. 槽迁移中断
   - 保持数据一致性
   - 重新发起迁移
   - 避免写入冲突
```

### 故障恢复

```bash
# ============ 主节点故障恢复 ============

# 1. 查看集群状态
redis-cli -c -p 7000 CLUSTER NODES

# 2. 如果从节点还在，修复主节点
# 方式1：重启原主节点
# 方式2：将从节点提升为主节点
redis-cli -c -p 7002 CLUSTER FAILOVER

# 3. 如果主从节点都故障
# 需要手动重新分配槽

# ============ 网络分区恢复 ============

# 1. 检查分区间数据
redis-cli -c -p 7000 CLUSTER INFO

# 2. 网络恢复后自动同步
# 不需要手动操作

# ============ 数据不一致处理 ============

# 1. 使用 RDB/AOF 恢复
# 停止集群
# 恢复数据
# 重启集群

# 2. 使用 redis-cli --cluster import
# 从其他集群导入数据
redis-cli --cluster import 127.0.0.1:7000 \
  --cluster-from <source-cluster> \
  --cluster-copy
```

---

## 5. 监控与运维

### 监控指标

```python
def get_cluster_stats(rc):
    """获取集群统计"""
    info = rc.info('cluster')

    return {
        'cluster_state': info.get('cluster_state'),
        'cluster_slots_assigned': info.get('cluster_slots_assigned'),
        'cluster_slots_ok': info.get('cluster_slots_ok'),
        'cluster_slots_pfail': info.get('cluster_slots_pfail'),
        'cluster_known_nodes': info.get('cluster_known_nodes'),
        'cluster_size': info.get('cluster_size'),
        'cluster_current_epoch': info.get('cluster_current_epoch'),
        'cluster_my_epoch': info.get('cluster_my_epoch'),
    }

def get_node_stats(rc):
    """获取节点统计"""
    nodes_info = rc.cluster('nodes').split('\n')
    nodes = []

    for line in nodes_info:
        if not line:
            continue

        parts = line.split()
        if len(parts) < 8:
            continue

        node_id, flags, master_id, ping_sent, pong_recv, ip_port, _, *rest = parts

        nodes.append({
            'node_id': node_id,
            'flags': flags,
            'master_id': master_id if master_id != '-' else None,
            'ip_port': ip_port.split('@')[0],
            'connected': 'connected' in flags,
            'master': 'master' in flags,
            'slave': 'slave' in flags,
            'myself': 'myself' in flags,
        })

    return nodes

def check_cluster_health(rc):
    """检查集群健康"""
    stats = get_cluster_stats(rc)
    nodes = get_node_stats(rc)

    alerts = []

    # 检查集群状态
    if stats['cluster_state'] != 'ok':
        alerts.append({
            'level': 'critical',
            'message': f'集群状态异常: {stats["cluster_state"]}'
        })

    # 检查槽分配
    if stats['cluster_slots_assigned'] != 16384:
        alerts.append({
            'level': 'warning',
            'message': f'槽未完全分配: {stats["cluster_slots_assigned"]}/16384'
        })

    # 检查离线节点
    offline_nodes = [n for n in nodes if not n['connected'] and n['master']]
    if offline_nodes:
        alerts.append({
            'level': 'critical',
            'message': f'{len(offline_nodes)} 个主节点离线'
        })

    return {
        'stats': stats,
        'nodes': nodes,
        'alerts': alerts,
        'healthy': len([a for a in alerts if a['level'] == 'critical']) == 0
    }
```

### 自动化运维

```python
import schedule

def daily_cluster_check():
    """日常集群检查"""
    rc = RedisCluster(startup_nodes=startup_nodes)

    health = check_cluster_health(rc)

    if not health['healthy']:
        send_alert(health['alerts'])

    # 检查槽分布均衡
    stats = get_cluster_stats(rc)
    nodes = get_node_stats(rc)

    masters = [n for n in nodes if n['master'] and n['connected']]
    if len(masters) > 0:
        avg_slots = stats['cluster_slots_assigned'] / len(masters)
        # 检查是否有节点槽数偏差超过 20%
        for node in masters:
            node_slots = get_slots_for_node(rc, node['node_id'])
            if abs(len(node_slots) - avg_slots) / avg_slots > 0.2:
                alerts.append({
                    'level': 'warning',
                    'message': f'节点 {node["ip_port"]} 槽分布不均衡'
                })

schedule.every().hour.do(daily_cluster_check)
```

---

## 今日总结

- [ ] Gossip 协议：节点间去中心化通信
- [ ] 槽迁移：ASK/MOVED 重定向
- [ ] 故障检测：SDOWN → ODOWN → 故障转移
- [ ] 扩缩容：`--cluster rebalance` 重新分配槽
- [ ] 跨槽操作：按槽分组批量处理
- [ ] 监控指标：集群状态、槽分配、节点连接

---

*第 44 天 / 330 天*
*Python 后端 - Redis Cluster 进阶与运维*
