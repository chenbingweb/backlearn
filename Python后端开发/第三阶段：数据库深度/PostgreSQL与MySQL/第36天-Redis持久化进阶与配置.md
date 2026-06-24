# 第 36 天：Redis 持久化进阶与配置

## 学习目标

- 深入理解 RDB 机制
- 深入理解 AOF 机制
- 掌握持久化配置优化
- 学会备份恢复策略

---

## 1. RDB 深入理解

### 触发时机

```bash
# 1. 自动触发（根据 save 配置）
# redis.conf
save 900 1      # 900秒内至少1次修改
save 300 100    # 300秒内至少100次修改
save 60 10000   # 60秒内至少10000次修改

# 2. 手动触发
BGSAVE          # 后台保存，不阻塞
SAVE            # 同步保存，阻塞（大数据量可能几十秒）

# 3. 关闭自动保存
redis-cli CONFIG SET save ""
```

### RDB 流程

```markdown
BGSAVE 执行流程：

1. fork() 创建子进程
   - 复制页表（写时复制）
   - 不复制实际数据

2. 子进程遍历内存
   - 写入临时文件 dump.rdb.tmp
   - 使用 COPY ON WRITE 读取数据

3. 完成后通知主进程
   - 主进程重命名临时文件
   - 替换旧的 dump.rdb

4. 父进程继续处理请求
```

### COPY ON WRITE

```
fork 时刻                        写入新数据后
┌─────────────┐                  ┌─────────────┐
│  父进程     │                  │  父进程     │
│  内存页 A   │ ──── fork ────► │  内存页 A'  │
│  (引用+1)   │                  │  (COW)     │
└─────────────┘                  └─────────────┘
       │                                │
       │                                ▼
       │                         ┌─────────────┐
       │                         │  子进程     │
       │                         │  内存页 A   │
       │                         │  (不变)    │
       │                         └─────────────┘
```

---

## 2. AOF 深入理解

### 同步策略对比

```markdown
appendfsync 的三种策略：

┌─────────────────────────────────────────────────────────────┐
│  always     │  everysec        │  no                        │
├─────────────────────────────────────────────────────────────┤
│  每次写入   │  每秒一次        │  由系统决定                 │
│  同步到磁盘 │  同步到磁盘      │  何时写入由内核决定         │
├─────────────────────────────────────────────────────────────┤
│  数据最完整 │  最多丢失1秒数据 │  可能丢失较多样数据         │
│  性能最低  │  性能适中        │  性能最好                   │
│  IO 开销大 │  推荐使用        │  适合对数据不敏感的场景     │
└─────────────────────────────────────────────────────────────┘
```

### AOF 重写机制

```markdown
AOF 文件会随时间不断增大，因为记录了所有操作

例如：
  INCR counter    # 执行1000次
  INCR counter    # 文件中有1000条记录
  ...             # 但最终值只是一个数字

重写原理：
  读取当前数据状态
  用一条命令替代历史操作
  INCR counter -> SET counter 1000
```

### AOF 重写配置

```bash
# 自动重写配置
auto-aof-rewrite-percentage 100  # 文件大小超过上次 100% 时重写
auto-aof-rewrite-min-size 64mb   # 最小 64MB 才触发重写

# 示例：
# 上次 AOF 文件 100MB
# 现在 AOF 文件达到 200MB
# 触发重写

# AOF 损坏修复
redis-check-aof --fix appendonly.aof
```

---

## 3. 持久化配置实践

### 开发环境

```bash
# redis-dev.conf
# 开发环境：优先性能

# RDB
save 900 1
save 300 100
save 60 10000

# AOF
appendonly no           # 开发环境关闭 AOF
# appendfilename "appendonly-dev.aof"

# 内存
maxmemory 512mb
maxmemory-policy allkeys-lru
```

### 生产环境

```bash
# redis-prod.conf
# 生产环境：数据安全优先

# RDB
save 900 1
save 300 100
save 60 10000

# AOF
appendonly yes
appendfilename "appendonly-prod.aof"
appendfsync everysec
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
aof-use-rdb-preamble yes  # 混合持久化

# 内存
maxmemory 4gb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# 备份
dir /data/redis
dbfilename dump-prod.rdb
```

### Docker 环境

```bash
# docker-compose.yml
redis:
  image: redis:7-alpine
  command: >
    redis-server
    --appendonly yes
    --appendfsync everysec
    --rdbcompression yes
    --maxmemory 2gb
    --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data
  environment:
    - REDIS_PASSWORD=your_password
```

---

## 4. 备份恢复策略

### 备份脚本

```bash
#!/bin/bash
# backup-redis.sh

BACKUP_DIR=/backups/redis
DATE=$(date +%Y%m%d_%H%M%S)
REDIS_HOST=localhost
REDIS_PORT=6379

# 创建备份目录
mkdir -p $BACKUP_DIR

# RDB 备份
redis-cli -h $REDIS_HOST -p $REDIS_PORT BGSAVE
echo "RDB backup started"

# 等待备份完成
while [ $(redis-cli -h $REDIS_HOST -p $REDIS_PORT LASTSAVE) == $(redis-cli -h $REDIS_HOST -p $REDIS_PORT INFO persistence | grep rdb_last_save_time | cut -d: -f2) ]; do
    sleep 1
done

# 复制 RDB 文件
cp /data/dump.rdb $BACKUP_DIR/dump.$DATE.rdb

# 复制 AOF 文件（如果存在）
if [ -f /data/appendonly.aof ]; then
    cp /data/appendonly.aof $BACKUP_DIR/appendonly.$DATE.aof
fi

# 压缩备份
cd $BACKUP_DIR
tar czf redis.$DATE.tar.gz dump.$DATE.rdb appendonly.$DATE.aof
rm -f dump.$DATE.rdb appendonly.$DATE.aof

# 保留最近 7 天备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: redis.$DATE.tar.gz"
```

### 恢复流程

```bash
# 1. 停止 Redis
redis-cli shutdown

# 2. 备份当前数据
mv /data/dump.rdb /data/dump.rdb.bak
mv /data/appendonly.aof /data/appendonly.aof.bak

# 3. 复制备份文件
cp /backups/redis/dump.20240101.rdb /data/dump.rdb

# 4. 启动 Redis
redis-server /path/to/redis.conf

# 5. 验证数据
redis-cli INFO keyspace
redis-cli KEYS "*"

# 6. 如果需要，恢复 AOF
# redis-cli CONFIG SET appendonly yes
# redis-cli BGREWRITEAOF
```

### 在线恢复

```python
import redis
import shutil
import time

class RedisBackupManager:
    """Redis 备份管理器"""

    def __init__(self, redis_client):
        self.r = redis_client

    def create_backup(self, backup_dir):
        """创建备份"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')

        # 触发 RDB 保存
        self.r.bgsave()

        # 等待保存完成
        while True:
            info = self.r.info('persistence')
            if info.get('rdb_save_last_c实体_status') == 'ok':
                break
            time.sleep(0.5)

        # 复制文件（需要知道文件路径）
        dump_path = '/data/dump.rdb'
        backup_path = f'{backup_dir}/dump.{timestamp}.rdb'
        shutil.copy(dump_path, backup_path)

        return backup_path

    def restore_from_backup(self, backup_path):
        """从备份恢复"""
        # 停止写入
        # 需要停止应用或切换到只读模式

        # 复制备份文件
        shutil.copy(backup_path, '/data/dump.rdb')

        # 重启 Redis
        self.r.shutdown(nosave=True)
        # 然后启动 Redis
```

---

## 5. 性能优化

### 持久化与性能

```markdown
RDB 和 AOF 对性能的影响：

RDB：
- fork() 需要复制页表（约几十 MB）
- COW 机制，内存修改时才复制
- 子进程执行期间，父进程写入时需要复制内存页

AOF：
- everysec：每秒一次 fsync，性能影响小
- always：每次写入都 fsync，性能影响大
- always vs everysec：性能差 10 倍左右

优化建议：
1. 使用 SSD 存储 RDB/AOF 文件
2. AOF 使用 everysec 策略
3. 开启混合持久化
4. 合理配置 save 规则，减少 RDB 生成频率
```

### 监控指标

```python
def get_persistence_stats(r):
    """获取持久化统计"""
    info = r.info('persistence')

    return {
        # RDB
        'rdb_save_in_progress': info.get('rdb_save_in_progress'),
        'rdb_last_save_time': info.get('rdb_last_save_time'),
        'rdb_changes_since_last_save': info.get('rdb_changes_since_last_save'),

        # AOF
        'aof_enabled': info.get('aof_enabled'),
        'aof_rewrite_in_progress': info.get('aof_rewrite_in_progress'),
        'aof_current_size': info.get('aof_current_size'),
        'aof_base_size': info.get('aof_base_size'),
        'aof_pending_rewrite': info.get('aof_pending_rewrite'),

        # Buffer
        'aof_buffer_length': info.get('aof_buffer_length'),
        'aof_rewrite_buffer_length': info.get('aof_rewrite_buffer_length'),
    }
```

---

## 今日总结

- [ ] RDB：`BGSAVE` 后台保存，COW 机制
- [ ] AOF：`appendfsync everysec` 推荐策略
- [ ] AOF 重写：减少文件大小，`BGREWRITEAOF`
- [ ] 混合持久化：`aof-use-rdb-preamble yes`
- [ ] 备份：定期备份 RDB + AOF 文件
- [ ] 恢复：停止 Redis，替换文件，重启

---

*第 36 天 / 330 天*
*Python 后端 - Redis 持久化进阶与配置*
