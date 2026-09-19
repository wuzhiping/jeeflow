# jeeFlow 部署指南

> 本文档描述如何在 **生产环境多节点** 部署 jeeFlow 引擎（BDD #1215 FIX-T92 §4.4.4 / 2026-09-20）。

---

## 1. 部署架构概览

```text
                  ┌────────────────┐
   Client UI ───► │  nginx / LB    │
                  │ (负载均衡/SSL) │
                  └────────┬───────┘
           ┌──────────────┼──────────────┐
           ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ jeeFlow  │   │ jeeFlow  │   │ jeeFlow  │   ← 多实例无状态
    │ Node 1   │   │ Node 2   │   │ Node 3   │
    │ :8101    │   │ :8101    │   │ :8101    │
    └────┬─────┘   └────┬─────┘   └────┬─────┘
         │              │              │
         └──────────────┼──────────────┘
                        ▼
              ┌──────────────────┐
              │   PostgreSQL     │   ← 共享持久化
              │   主库 + 只读副本│
              └──────────────────┘
```

### 关键设计

- **App 节点无状态**：所有状态都在 PostgreSQL，启动即可加入集群
- **数据库单一真相源**：集群不依赖内存广播，乐观锁 + 事务保证一致
- **横向扩容**：增删节点无需通知其他节点，nginx 自动识别

---

## 2. 系统要求

| 项目 | 最低 | 推荐 | 备注 |
|------|------|------|------|
| CPU  | 2 核 | 4 核+ | 受并发量驱动 |
| 内存 | 2 GB | 4 GB+ | Python + asyncpg pool |
| 磁盘 | 500 MB | 1 GB  | 代码 + 日志 |
| PG    | 13+  | 15+   | 需 `BIGINT`/`JSONB` |
| 网络  | 1 Gbps | 10 Gbps | 节点到 DB |

---

## 3. PostgreSQL 准备

### 3.1 创建数据库

```sql
CREATE DATABASE jeeflow OWNER jeeflow_user;
GRANT ALL PRIVILEGES ON DATABASE jeeflow TO jeeflow_user;
```

### 3.2 初始化表结构

```bash
PGPASSWORD=xxx psql -h <host> -U jeeflow_user -d jeeflow -f docs/pg_schema.sql
```

### 3.3 创建索引（FIX-T86 §4.4.2）

```sql
CREATE INDEX IF NOT EXISTS idx_wf_process_instance_version
  ON wf_process_instance(version);
CREATE INDEX IF NOT EXISTS idx_wf_process_task_state
  ON wf_process_task(task_state);
CREATE INDEX IF NOT EXISTS idx_wf_process_task_instance
  ON wf_process_task(process_instance_id);
```

### 3.4 配置连接池

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `JEEFLOW_PG_DSN`     | 无（必填）| `postgresql://user:pass@host:port/db` |
| `JEEFLOW_PG_POOL_MIN`| 2        | 连接池最小连接数 |
| `JEEFLOW_PG_POOL_MAX`| 10       | 连接池最大连接数 |

**推荐生产配置**：

| 节点规格 | POOL_MIN | POOL_MAX |
|---------|----------|----------|
| 4 核 4 GB    | 5  | 20 |
| 8 核 8 GB    | 10 | 40 |

> **建议**：所有 App 节点的 `POOL_MAX × 节点数 < PG `max_connections``（PG 默认 100）。

---

## 4. App 节点部署

### 4.1 节点 1（leader）启动

```bash
cd /opt/jeeflow
cp .env.example .env
# 编辑 .env
JEEFLOW_PORT=8101
JEEFLOW_BACKEND=postgres
JEEFLOW_PG_DSN=postgresql://jeeflow_user:xxx@pg-host:5432/jeeflow
JEEFLOW_PG_POOL_MIN=5
JEEFLOW_PG_POOL_MAX=20
LOG_LEVEL=INFO

nohup .venv/bin/python main_pg.py > /var/log/jeeflow-8101.log 2>&1 &
```

### 4.2 节点 2/3 启动

```bash
# 节点 2
JEEFLOW_PORT=8101 ... nohup .venv/bin/python main_pg.py > /var/log/jeeflow-8102.log 2>&1 &

# 节点 3
JEEFLOW_PORT=8101 ... nohup .venv/bin/python main_pg.py > /var/log/jeeflow-8103.log 2>&1 &
```

### 4.3 健康检查

```bash
for port in 8101 8102 8103; do
  curl -sf http://node${port}:8101/healthz | jq .
done
```

预期：

```json
{"status":"UP","backend":"postgres","pg":"up","pool":{"min":5,"max":20,"size":3}}
```

---

## 5. 负载均衡（Nginx）

### 5.1 upstream 配置

```nginx
upstream jeeflow_backend {
    least_conn;
    server 10.0.0.11:8101 max_fails=3 fail_timeout=10s;
    server 10.0.0.12:8101 max_fails=3 fail_timeout=10s;
    server 10.0.0.13:8101 max_fails=3 fail_timeout=10s;
    keepalive 32;
}

server {
    listen 443 ssl;
    server_name jeeflow.example.com;

    ssl_certificate     /etc/ssl/certs/jeeflow.crt;
    ssl_certificate_key /etc/ssl/private/jeeflow.key;

    location / {
        proxy_pass http://jeeflow_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_read_timeout 60s;
    }

    location = /healthz {
        access_log off;
        proxy_pass http://jeeflow_backend;
    }
}
```

### 5.2 路由策略

| 策略 | 推荐 | 适用 |
|------|------|------|
| `round_robin` | ⭐⭐ | 节点性能一致 |
| `least_conn`  | ⭐⭐⭐ | 长连接场景（流程实例 1+ 小时） |
| `ip_hash`     | ⭐    | 不推荐，会破坏乐观锁下的负载均衡 |

---

## 6. Session / 锁一致性

### 6.1 乐观锁保证

`JdbcRepository.update_instance(inst, expected_version=inst.version)`：

```sql
UPDATE wf_process_instance
SET state = ?, version = version + 1
WHERE id = ? AND version = ?
```

- **Node A** 读取 version=5，更新成功 (version=6)
- **Node B** 用 version=5 更新 → `UPDATE 0` 返回 `False`
- Node B 业务方需重新读取 + 重试

### 6.2 重试建议

业务方（如 UI / 调用方）在收到 `997003` (`OPTIMISTIC_LOCK_FAILED`) 时：

```python
for attempt in range(3):
    inst = await repo.find_instance_by_id(inst_id)
    result = await facade.flow("processInstance/approve", ...)
    if result["code"] != 997003:
        break
    await asyncio.sleep(0.1 * (2 ** attempt))  # 指数退避
```

### 6.3 节点故障切换

| 故障 | 表现 | 自动恢复 |
|------|------|----------|
| 单节点崩溃 | nginx `max_fails=3` 摘除 | ⭐ 是 |
| PG 主库故障 | 全部写入失败 | 由 PG 主备切换（Patroni 等） |
| 网络分区 | 节点拒绝响应 | nginx 摘除 |

---

## 7. 定时任务（替代 Celery）

### 7.1 expire scan（FIX-T91 §4.4.3）

```cron
# /etc/cron.d/jeeflow
*/5 * * * * curl -sf -X POST http://localhost:8101/api/admin/expire/scan > /dev/null
```

### 7.2 stats 统计（可选）

```cron
0 * * * * curl -sf http://localhost:8101/api/admin/stats/overview >> /var/log/jeeflow-stats.log
```

---

## 8. 监控与告警

### 8.1 Prometheus 接入

```yaml
scrape_configs:
  - job_name: 'jeeflow'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['node1:8101','node2:8101','node3:8101']
```

### 8.2 关键告警规则

```yaml
groups:
- name: jeeflow
  rules:
  - alert: JeeFlowDown
    expr: up{job="jeeflow"} == 0
    for: 1m
  - alert: JeeFlowActiveInstancesHigh
    expr: wf_active_instances > 10000
    for: 5m
  - alert: JeeFlowTaskDurationP99
    expr: histogram_quantile(0.99, wf_task_duration_seconds) > 30
    for: 5m
```

### 8.3 日志聚合

推荐 ELK / Loki，将 `/var/log/jeeflow-*.log` 接入，结构化字段：

- `trace_id`：全链路追踪
- `inst_id`：实例级检索
- `task_id`：任务级检索
- `level`：ERROR/WARN/INFO

---

## 9. 备份与恢复

### 9.1 PG 备份

```bash
# 每日全量
pg_dump -Fc jeeflow > /backup/jeeflow-$(date +%Y%m%d).dump

# 每 5 分钟 WAL 归档（增量）
# postgresql.conf
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'
```

### 9.2 恢复

```bash
pg_restore -d jeeflow /backup/jeeflow-20260920.dump
```

### 9.3 流程定义恢复（应用层）

```bash
# 流程定义 (JSON) 版本化存在 ./flows/
git pull origin main   # 拉取新版本流程
# 重新部署
curl -X POST http://jeeFlow:8101/wf/processDesign/deploy -d '...'
```

---

## 10. 滚动升级

### 10.1 步骤

```bash
# 1. 拉取新代码
cd /opt/jeeflow && git pull

# 2. 同步 vendor 到 site-packages
cp vendor/jeeflow/{*.py,repository/*.py} .venv/lib/python3.12/site-packages/jeeflow/

# 3. 摘除节点（nginx）
# nginx -s reload  # 重载 upstream 移除节点

# 4. 停止老版本
pkill -f main_pg.py

# 5. 启动新版本
nohup .venv/bin/python main_pg.py > /var/log/jeeflow-8101.log 2>&1 &

# 6. 健康检查通过后，重新加入 nginx upstream
# nginx -s reload
```

### 10.2 数据库迁移

```bash
# 仅追加（DDL 向后兼容）
psql -d jeeflow -f migrations/001_add_column_xxx.sql
```

破坏性变更（重命名 / 类型变更）需停机维护。

---

## 11. 灾难恢复

### 11.1 PG 主库完全损坏

1. 启动 PG 副本提升为主
2. 修改所有 App 节点的 `JEEFLOW_PG_DSN`
3. 重启 App 节点

预计 RTO：5 分钟（人工介入）

### 11.2 全部节点故障但 PG 完好

1. 启动 App 节点（新机器）
2. 自动恢复（无状态设计）

预计 RTO：1 分钟

---

## 12. 容量规划

| 业务规模 | 节点数 | PG 规格 | 备注 |
|---------|--------|---------|------|
| 1 万实例 / 日 | 2 | 4 核 8 GB | 单实例足够 |
| 10 万实例 / 日 | 4 | 8 核 16 GB | 配合只读副本 |
| 100 万实例 / 日 | 8+ | 16 核 32 GB | 读写分离 + 分库 |

实测：`/tmp/stress_test.py` 100 并发 / 250ms（PG 端，1 节点）。

---

## 13. 安全清单

- [x] **HTTPS**：nginx 终止 SSL
- [x] **JWT/Token**：业务网关层校验，本引擎无内置 auth
- [x] **PG 加密**：连接字符串建议 `?sslmode=require`
- [x] **密钥管理**：DSN 走 `Vault` / `K8s Secret`
- [x] **日志脱敏**：handler FQCN 中勿带密码

---

## 14. 故障排查速查

| 现象 | 排查命令 |
|------|----------|
| 节点 502 | `curl /healthz` + `/var/log/jeeflow-*.log` |
| PG 连接耗尽 | `SELECT count(*) FROM pg_stat_activity;` |
| 乐观锁冲突 | 日志 grep `OPTIMISTIC_LOCK` |
| 内存膨胀 | `ps aux \| grep python \| awk '{print $4}'` |
| 流程定义错乱 | `/wf/processDesign/page` 查 `version` |

---

## 15. 参考

- §4.4.1 PG connection pool：`main_pg.py` `JEEFLOW_PG_POOL_MIN/MAX`（FIX-T90）
- §4.4.2 实例乐观锁：`vendor/jeeflow/repository/base.py` `update_instance`（FIX-T87）
- §4.4.3 异步任务：`main_common.py` `admin_expire_scan`（FIX-T91）
- §4.3.3 后端集成：`docs/integration.md`（FIX-T87 / FIX-T90）
- §4.1.3 Prometheus 指标：`docs/openapi.json`（FIX-T85）`/metrics`
