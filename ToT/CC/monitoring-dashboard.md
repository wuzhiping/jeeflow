# Monitoring Dashboard · 10 监控端点解读

> **读者**：04 运维（陈 DBA 类角色）
> **数据源**：`main_common.py` 监控端点

---

## 10 端点速查表

| # | 端点 | 行号 | 含义 | 健康阈值 | 告警阈值 |
|---|---|---|---|---|---|
| 1 | `GET /healthz` | 829 | 进程存活 | `status=UP` + `pg=ok` | `pg=down` 立即 P0 |
| 2 | `GET /version` | 848 | 版本对齐 | N/A | 与 git tag 不符 → 部署未同步 |
| 3 | `GET /api/admin/health` | 865 | 详细健康 | `checks.pg.status=ok` | `engine_cache.size > max*0.9` |
| 4 | `GET /metrics` | 1284 | Prometheus | N/A | 见各项 |
| 5 | `GET /api/admin/stats/overview` | 950 | 流程统计 | ratio > 0.5 | ratio < 0.3 P2 |
| 6 | `GET /api/admin/stats/trend` | 973 | 时序趋势 | N/A | 同比下降 > 30% P1 |
| 7 | `GET /api/admin/stats/group` | 985 | 分组 | N/A | 单用户积压 > 50 P2 |
| 8 | `POST /api/admin/expire/scan` | 1094 | 过期清理 | N/A | 单次清理 > 1000 P2 |
| 9 | `GET /api/admin/trace` | 1465 | 链路追踪 | N/A | p99 > 5s P1 |
| 10 | `GET /api/admin/trace/spans/{id}` | 1473 | 单 span | error span > 0 P1 | |

---

## 端点 1 · /healthz（最重要）

**返回示例**：
```json
{
  "status": "UP",
  "backend": "python",
  "version": "1.11.1",
  "version_full": "1.11.1+3d8c930c",
  "git_sha": "3d8c930c",
  "build_time": "2026-09-25T03:26:41Z",
  "pg": "ok"
}
```

**告警规则**：

```yaml
- alert: HealthzDown
  expr: up{job="jeeFlow"} == 0
  for: 30s
  severity: P0
  action: 立即重启

- alert: HealthzPgDown
  expr: jeeFlow_healthz_pg_status == "down"
  for: 30s
  severity: P0
  action: 检查 PG + 连接池
```

---

## 端点 3 · /api/admin/health（详细健康）

**返回示例**：
```json
{
  "status": "UP",
  "backend": "python",
  "version": "1.11.1",
  "checks": {
    "pg": {
      "status": "ok",
      "pool_size": 10,
      "idle": 2,
      "min_size": 2,
      "max_size": 20
    },
    "repo": {"status": "ok"},
    "engine_cache": {"status": "ok", "size": 5, "max": 100},
    "process": {"status": "ok", "active_instances": 23}
  }
}
```

**PG pool 阈值（关键）**：

| idle / max | 状态 | 行动 |
|---|---|---|
| > 50% | 🟢 健康 | - |
| 20-50% | 🟡 关注 | 监控趋势 |
| 10-20% | 🟠 警告 | 准备扩容 |
| < 10% | 🔴 异常 | 立即扩容 / 限流 |

**详细 PG pool runbook** → [`../CC/runbook.md §PG pool 耗尽`](../CC/runbook.md)

---

## 端点 4 · /metrics（Prometheus 格式）

**关键指标**（自定义 jeeFlow 命名空间）：

| 指标 | 类型 | 用途 |
|---|---|---|
| `jeeFlow_request_duration_seconds` | histogram | 请求延迟 |
| `jeeFlow_request_total` | counter | 请求总数 |
| `jeeFlow_request_errors_total` | counter | 错误数 |
| `jeeFlow_active_instances` | gauge | 活跃实例数 |
| `jeeFlow_active_tasks` | gauge | 活跃 task 数 |
| `jeeFlow_pg_pool_idle` | gauge | PG 连接池空闲数 |

**Prometheus 告警规则示例**：

```yaml
- alert: HighErrorRate
  expr: rate(jeeFlow_request_errors_total[5m]) / rate(jeeFlow_request_total[5m]) > 0.05
  for: 5m
  severity: P1
  action: 排查最近发布 + trace 错误 span

- alert: PgPoolExhausted
  expr: jeeFlow_pg_pool_idle < 2
  for: 5m
  severity: P1
  action: 扩容 / kill 长连接

- alert: HighLatency
  expr: histogram_quantile(0.99, rate(jeeFlow_request_duration_seconds_bucket[5m])) > 5
  for: 5m
  severity: P1
  action: 看 trace 慢 span
```

---

## 端点 5-7 · 流程统计

**5 · /api/admin/stats/overview**：
```json
{
  "total": 1234,
  "running": 50,
  "completedToday": 23,
  "completedThisWeek": 156,
  "backlogRate": 0.04
}
```

**告警阈值** → [`../../docs/spec/kpi-dictionary.md §KPI 1`](../../docs/spec/kpi-dictionary.md)

**6 · /api/admin/stats/trend**：返回 7d/30d 时序数据
**7 · /api/admin/stats/group**：按用户/部门/流程分组

---

## 端点 8-10 · 运维操作

**8 · POST /api/admin/expire/scan**：清理过期 instance
- 默认 cron：每天凌晨 2 点
- 手动触发：`curl -X POST .../api/admin/expire/scan`
- 告警：单次清理 > 1000 → 可能是流程设计 bug

**9 · /api/admin/trace**：返回最近的链路追踪
- 默认 limit=20
- 过滤：`?processInstanceId=12345` 或 `?processTaskId=12345`

**10 · /api/admin/trace/spans/{trace_id}**：单 trace 详情

---

## 仪表盘建议（Grafana）

```
┌─────────────────────────────────────────┐
│ Top: Service UP + Version Match          │
├──────────────────┬──────────────────────┤
│ Request Rate     │ Error Rate           │
├──────────────────┼──────────────────────┤
│ Latency p50/p95  │ PG Pool Idle         │
├──────────────────┴──────────────────────┤
│ Backlog by Operator (top 10)            │
├─────────────────────────────────────────┤
│ Recent Trace Errors (last 1h)           │
└─────────────────────────────────────────┘
```

---

**版本**：v1.11.1 · **来源**：故事 001（陈 DBA 看 PG pool 阈值）→ 04 persona review