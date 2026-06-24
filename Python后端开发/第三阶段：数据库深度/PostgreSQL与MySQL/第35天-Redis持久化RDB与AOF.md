# 第 35 天：Redis 持久化 RDB 与 AOF

## 学习目标

- 理解 Redis 持久化机制
- 掌握 RDB 快照原理
- 掌握 AOF 追加原理
- 学会选择持久化策略

---

## 1. 持久化概述

### 为什么需要持久化

```
Redis 内存数据 ────────────────────────► Redis 重启
        │                                      │
        │ 丢失                                 │ 恢复
        ▼                                      ▼
    所有数据                          从 RDB 或 AOF 恢复
```

### 两种持久化方式

| 特性 | RDB | AOF |
|------|-----|-----|
| 原理 | 定时快照 | 记录所有写命令 |
| 文件大小 | 小（紧凑） | 大（积累） |
| 恢复速度 | 快 | 慢 |
| 数据完整性 | 可能丢失数据 | 可配置完整性 |
| IO 类型 | 阻塞 | 非阻塞（后台） |
| 体重 | 重 | 轻 |

---

## 2. RDB 快照

### 配置

```bash
# redis.conf

# 触发规则
save 900 1        # 900秒内1次修改
save 300 100      # 300秒内100次修改
save 60 10000     # 60秒内10000次修改

# 禁用 RDB（注释所有 save）
# save ""

# 文件名
dbfilename dump.rdb

# 存储路径
dir /var/lib/redis

# 压缩
rdbcompression yes

# 错误检查
rdbchecksum yes
```

### 手动触发

```bash
# 阻塞保存（主进程执行）
BGSAVE

# 保存状态查询
LASTSAVE

# 后台保存状态
INFO persistence
# rdb_changes_since_last_save: 0
# rdb_bgsave_in_progress: 0
```

### RDB 流程

```
主进程 ────────────────────────────────────────────►
    │                                                 │
    │  fork() 创建子进程                              │
    ▼                                                 │
子进程 ────────────────────────────────────────────►
    │                                                 │
    │  遍历所有数据库                                 │
    ▼                                                 │
  写入 ──► dump.rdb.tmp（临时文件）                   │
    │                                                 │
    │  完成                                           │
    ▼                                                 │
重命名 ──► dump.rdb（替换旧文件）                      │
    │                                                 │
    ▼                                                 │
子进程退出 ◄──────────────────────────────────────────
```

### 优缺点

```
✅ 优点：
- 文件紧凑，适合备份
- 恢复速度快
- fork() 子进程，不阻塞主进程

❌ 缺点：
- 可能丢失上次快照后的数据
- fork() 需要额外内存
- 数据量大时，fork 时间长
```

---

## 3. AOF 追加

### 配置

```bash
# redis.conf

# 开启 AOF
appendonly yes

# 文件名
appendfilename "appendonly.aof"

# 存储路径（与 RDB 共用 dir）
dir /var/lib/redis

# 同步策略
appendfsync everysec   # 每秒同步（默认）
appendfsync always     # 每次写入
appendfsync no         # 由系统决定

# 重写策略
auto-aof-rewrite-percentage 100  # 文件大小超过 100% 时重写
auto-aof-rewrite-min-size 64mb   # 最小 64MB 才重写

# AOF 重写方式
aof-rewrite-inject-sync yes      # 支持重写时同步
```

### AOF 流程

```
主进程 ────────────────────────────────────────────►
    │                                                 │
    │  执行写命令                                     │
    ▼                                                 │
写入 ──► aof_buf（缓冲区）                            │
    │                                                 │
    │  事件循环                                      │
    ▼                                                 │
是否同步？ ──► yes ──► 写入 aof 文件                 │
    │                                                 │
    │ no                                             │
    ▼                                                 │
系统决定何时写入                                     │
```

### AOF 重写

```bash
# 手动触发重写
BGREWRITEAOF

# 查看状态
INFO persistence
# aof_rewrite_in_progress: 0
# aof_last_rewrite_time_sec: 0.123
```

### 重写原理

```
aof 文件（100MB）                     aof_rewrite.tmp（30MB）
┌────────────────────┐               ┌────────────────────┐
│ SET a 1            │               │ SET a 100           │
│ SET a 2            │  ────────►   │ SET b 200          │
│ SET a 3            │              │ SET c 300          │
│ INCR a             │              └────────────────────┘
│ ... (1000万条)      │
└────────────────────┘
```

---

## 4. 同步策略详解

### everysec（推荐）

```markdown
每秒钟同步一次，可能丢失最多 1 秒的数据

主线程 ──► 写命令 ──► aof_buf ──► 定时同步（1秒）
                                    │
                                    ▼
                              写入磁盘

最多丢失 1 秒的写命令
```

### always

```markdown
每次写入都同步，数据最完整，性能最差

主线程 ──► 写命令 ──► aof_buf ──► 同步写入磁盘
                              │
                              ▼
                          每次都同步

几乎不丢失数据，但 IO 开销大
```

### no

```markdown
由操作系统决定何时写入，性能最好，数据最不安全

主线程 ──► 写命令 ──► aof_buf ──► 操作系统决定
                                          │
                                          ▼
                                    可能几秒后才写入

可能丢失未知时间的数据
```

---

## 5. 混合持久化

### 配置

```bash
# redis.conf
aof-use-rdb-preamble yes
```

### 原理

```
Redis 重启时：
1. 先加载 RDB（快速）
2. 再应用 RDB 后的 AOF增量（完整）

启动 ──► 加载 RDB ──► 应用 AOF 增量 ──► 就绪
         (快)           (增量)
```

### 优势

```
✅ RDB 优点：快速恢复
✅ AOF 优点：完整数据

结合两者优势：
- 启动快（RDB 部分）
- 数据完整（RDB 之后的增量）
```

---

## 6. Python 配置示例

```python
import redis

# RDB 配置连接
r = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    # RDB 相关参数（通过 CONFIG SET 动态设置）
)

# 查看持久化状态
def get_persistence_info():
    info = r.info('persistence')
    return {
        'rdb_enabled': info.get('rdb_changes_since_last_save'),
        'rdb_bgsave_in_progress': info.get('rdb_bgsave_in_progress'),
        'aof_enabled': info.get('aof_enabled'),
        'aof_rewrite_in_progress': info.get('aof_rewrite_in_progress'),
        'aof_last_write_status': info.get('aof_last_write_status'),
    }

# 手动触发 RDB 保存
def save_rdb():
    # 同步保存
    r.save()

    # 异步保存（后台）
    r.bgsave()

    return r.lastsave()

# 手动触发 AOF 重写
def rewrite_aof():
    r.bgrewriteaof()
```

### Docker 配置

```yaml
# docker-compose.yml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --appendfsync everysec
  volumes:
    - redis_data:/data

# 备份脚本
```

```bash
#!/bin/bash
# 备份 Redis 数据

BACKUP_DIR=/backups
DATE=$(date +%Y%m%d_%H%M%S)

# 复制 AOF 文件
cp /data/appendonly.aof $BACKUP_DIR/appendonly.$DATE.aof

# 复制 RDB 文件
cp /data/dump.rdb $BACKUP_DIR/dump.$DATE.rdb

# 保留最近 7 天
find $BACKUP_DIR -mtime +7 -delete
```

---

## 7. 持久化策略选择

### 选择建议

| 场景 | 推荐策略 | 原因 |
|------|---------|------|
| 数据重要，不能丢失 | AOF always | 最高完整性 |
| 兼顾性能和数据 | AOF everysec + RDB | 常用方案 |
| 数据可部分丢失 | RDB only | 性能最好 |
| 大数据量 | 混合持久化 | 启动快 |

### 配置模板

```bash
# 高可用配置
# redis.conf

# RDB
save 900 1
save 300 100
save 60 10000
dbfilename dump.rdb
dir /var/lib/redis
rdbcompression yes
rdbchecksum yes

# AOF
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
aof-use-rdb-preamble yes
```

---

## 今日总结

- [ ] RDB：定时快照，文件紧凑，恢复快，可能丢数据
- [ ] AOF：记录写命令，完整性高，文件较大
- [ ] `appendfsync everysec`：每秒同步，推荐策略
- [ ] AOF 重写：压缩文件，BGREWRITEAOF
- [ ] 混合持久化：RDB + AOF 增量，启动快且完整
- [ ] RDB：`BGSAVE`、`SAVE`、`LASTSAVE`

---

*第 35 天 / 330 天*
*Python 后端 - Redis 持久化 RDB 与 AOF*
