# Runbook · 5 个常见故障场景

> **读者**：04 运维（陈 DBA 类角色）
> **原则**：每个场景 = 现象 → 排查 → 恢复 → 事后

---

## 场景 1 · /healthz 返回 `pg=down`

**现象**：监控告警 `HealthzPgDown`
**紧急度**：🔴 P0

### 排查

```bash
# 1. 看详细健康
curl -s http://localhost:8102/api/admin/health | jq '.checks.pg'
# → {"status": "down", "pool_size": 0, "idle": 0, "max_size": 20}

# 2. PG 进程是否在
ps aux | grep postgres

# 3. PG 端口是否通
pg_isready -h localhost -p 5432

# 4. 看应用日志最近 PG 错误
journalctl -u jeeFlow --since "10 minutes ago" | grep -i 'pg\|postgres'
```

### 恢复

**情况 A · PG 挂了**
```bash
sudo systemctl restart postgresql
# 等待 30 秒
curl http://localhost:8102/healthz  # 验证
```

**情况 B · 应用 PG 连接池耗尽**
```bash
# 看具体连接
SELECT pid, usename, application_name, state FROM pg_stat_activity WHERE datname='jeeflow';

# 杀掉长连接（>10 分钟）
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
  WHERE datname='jeeflow' AND state='idle in transaction' 
  AND query_start < now() - interval '10 minutes';
```

**情况 C · PG schema 不存在**
```bash
psql -U jeeFlow -d jeeflow -f scripts/init_schema.sql
# 重启应用
sudo systemctl restart jeeFlow
```

### 事后

- 写 postmortem：根因 + 行动项
- 若反复出现：考虑连接池扩容 + 加 `pgBouncer`

---

## 场景 2 · /api/admin/stats/overview instance 积压飙升

**现象**：`backlogRate > 30%` 告警
**紧急度**：🟠 P1

### 排查

```bash
# 1. 看哪个流程积压最重
curl -s http://localhost:8102/api/admin/stats/group | jq '.by_define | sort_by(.running) | reverse | .[0:5]'

# 2. 看哪个用户积压最多
curl -s http://localhost:8102/api/admin/stats/group | jq '.by_operator | sort_by(.todo) | reverse | .[0:10]'

# 3. 看具体 task 卡在哪
curl -sX POST http://localhost:8102/wf/processTask/todoList -d '{"operator":"<heavy_user>"}' | jq
```

### 恢复

**情况 A · 单用户积压**
- IM 通知该用户处理
- 短期：临时委派给副手

**情况 B · 某流程定义 bug**
- 看 `processInstance/highLight` 找卡点节点
- 临时：手动跳过该节点（PG 直接 update 状态）

**情况 C · 系统性卡死**
- 重启应用（不会丢数据，PG 持久化）
- 同时排查代码 bug

### 事后

- 通知流程管理员（02 张 HR）优化流程定义
- KPI 字典参考 [`../../docs/spec/kpi-dictionary.md`](../../docs/spec/kpi-dictionary.md)

---

## 场景 3 · /metrics request latency p99 飙升

**现象**：`HighLatency` 告警（p99 > 5s）
**紧急度**：🟡 P1（如果是 p95 + 持续）

### 排查

```bash
# 1. 看 trace 找慢 span
curl -s "http://localhost:8102/api/admin/trace?limit=20" | jq '.spans[] | select(.duration_ms > 5000) | {trace_id, operation, duration_ms}'

# 2. 单 span 详情
curl -s "http://localhost:8102/api/admin/trace/spans/<trace_id>" | jq

# 3. 看是 DB 慢还是引擎慢
# DB 慢：span 里看到 await execute(sql) > 3s
# 引擎慢：span 里看到 engine method > 3s
```

### 恢复

**情况 A · DB 慢**
- 看 PG 慢查询：`SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;`
- 加索引 / 优化 SQL

**情况 B · 引擎慢（图遍历深）**
- 看是否有人为超复杂流程（节点 > 100）
- 看 `_def_cache` 命中

**情况 C · 网络/资源**
- `top` / `free -h` 看资源
- `iostat` 看 IO

### 事后

- 加慢请求自动 trace
- 引擎性能基线（待 04 plan A5）

---

## 场景 4 · 部署后 /version 与 git tag 不符

**现象**：`/version` 返回的 version / git_sha 与 git tag 不一致
**紧急度**：🟠 P1（可能不是新版本）

### 排查

```bash
# 1. 看 /version
curl -s http://localhost:8102/version | jq

# 2. 看服务器实际代码版本
cd /opt/jeeFlow
git log --oneline -1
git describe --tags

# 3. 看 __init__.py
grep -E "__version__|__git_sha__" vendor/jeeflow/__init__.py
```

### 恢复

```bash
# 1. 重跑 release.sh 更新版本
bash ToT/sop/release.sh vX.Y.Z

# 2. 重启
sudo systemctl restart jeeFlow

# 3. 验证
curl -s http://localhost:8102/version | jq
```

### 事后

- 在 CI 里加：部署前必须跑 release.sh
- 加 `/version` 与 git tag 一致性检查

---

## 场景 5 · /api/admin/expire/scan 清理失败

**现象**：`expire/scan` 返回 error 或清理数量异常
**紧急度**：🟡 P2

### 排查

```bash
# 1. 看应用日志
journalctl -u jeeFlow --since "1 hour ago" | grep -i 'expire'

# 2. 看 PG 是否有锁
SELECT pid, state, query FROM pg_stat_activity 
  WHERE datname='jeeflow' AND state LIKE '%lock%';

# 3. 看 instance 表是否有遗留
SELECT COUNT(*) FROM process_instance WHERE ended_at < now() - interval '90 days';
```

### 恢复

**情况 A · 长锁**
```bash
# 杀掉 lock 的连接
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
  WHERE datname='jeeflow' AND state='idle in transaction';
```

**情况 B · schema 不一致**
- 跑 `scripts/repair_schema.sql`

**情况 C · 磁盘满**
- `df -h` / 清理 PG WAL

### 事后

- 加 `expire/scan` 监控指标
- 加自动重试

---

## 附录 · 常用命令速查

```bash
# 看进程
ps aux | grep uvicorn

# 看端口
ss -tlnp | grep 8102

# 看日志
journalctl -u jeeFlow -f

# 看 PG 状态
pg_isready -h localhost

# 看连接
SELECT count(*) FROM pg_stat_activity WHERE datname='jeeflow';

# 重启服务
sudo systemctl restart jeeFlow

# 健康检查
curl http://localhost:8102/healthz
curl http://localhost:8102/version
```

---

**版本**：v1.11.1 · **来源**：故事 001（陈 DBA 接到 PG pool 告警）→ 04 persona review