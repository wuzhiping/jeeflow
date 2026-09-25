# CC · 04 · 系统管理运维审计

> **Persona**：运维工程师 + DBA + 安全审计员
> **时间预算**：偶发（事件驱动）+ 每周 1-2h 巡检 + 季度审计
> **典型任务**：部署 / 监控 / 故障定位 / 备份恢复 / 合规审计 / 容量规划

---

## 1. Persona Profile

| 维度 | 内容 |
|---|---|
| 角色 | SRE / DBA / 安全审计员 / 系统架构师 |
| 工具 | curl / Prometheus / Grafana / git / DB 客户端 |
| 痛点 | 部署步骤散落 / 监控指标无文档 / 故障时不知看哪个接口 / 审计难追溯 |
| 期望 | 一键部署 / 一图全览 / 故障 5 分钟定位 / 审计日志随时查 |
| 成功标志 | MTTR ≤ 15 分钟 / 季度审计 0 不合规 |

---

## 2. Evidence（事实现状）

| 维度 | 数据 | 来源 |
|---|---|---|
| 监控端点数 | **3 + 7 = 10 个** | `grep '@app\.(get\|post).*monitoring\\|/healthz\\|/version\\|/metrics\\|/admin' main_common.py` |
| 健康检查 | `/healthz` (UP/DOWN/pg) + `/version` (4 字段) + `/api/admin/health` (详细) | `main_common.py:829/848/865` |
| 指标 | `/metrics` (Prometheus 格式) | `main_common.py:1284` |
| 流程统计 | `/api/admin/stats/overview` / `/api/admin/stats/trend` / `/api/admin/stats/group` | `main_common.py:950/973/985` |
| 链路追踪 | `/api/admin/trace` / `/api/admin/trace/spans/{trace_id}` | `main_common.py:1465/1473` |
| 过期清理 | `/api/admin/expire/scan` (POST) | `main_common.py:1094` |
| 部署文档 | `ToT/docs/guides/06-deployment.md` | `ls ToT/docs/guides/06-*` |
| 健康度工具 | ✅ `ToT/sop/health-check.py` (5 维度 100/100) | `ToT/sop/health-check.py` |
| 监控 dashboard 文档 | ❌ 无（知道端点但不知阈值）| 缺失 |
| 故障 runbook | ❌ 无 | 缺失 |
| 审计日志字段说明 | ❌ 无（仅 `tracing` 字段，无审计语义）| 缺失 |

---

## 3. 当前缺口（Gaps）

1. **故障 runbook 缺失**：监控指标出来了不知道意味着什么 / 该看哪个接口
2. **阈值文档缺失**：PG pool idle 多少告警？/ `/api/admin/stats/overview` 哪几个字段需要告警？
3. **审计日志语义不明**：trace span 字段含义未文档化
4. **部署 checklist 不全**：`guides/06-deployment.md` 是通用指南，缺本仓具体步骤
5. **容量规划无基线**：不知道 1000 用户/天的资源占用

---

## 4. 短期行动计划（4 周）

### A1. 监控仪表盘解读
- **位置**：`ToT/CC/monitoring-dashboard.md`（新建）
- **内容**：
  - 10 个监控端点速查表：
    | 端点 | 含义 | 健康阈值 | 告警阈值 |
    |---|---|---|---|
    | `/healthz` | 进程存活 | `status=UP` + `pg=ok` | `pg=down` 立即告警 |
    | `/version` | 版本对齐 | N/A | 与 git tag 不符 → 部署未同步 |
    | `/api/admin/health` | 详细健康 | `checks.pg.status=ok` | `engine_cache.size>max*0.9` |
    | `/metrics` | Prometheus 指标 | N/A | 见各项阈值 |
    | `/api/admin/stats/overview` | 流程统计 | instance.completed/started ratio | ratio < 0.5 → 积压 |
    | `/api/admin/stats/trend` | 时序趋势 | N/A | 同比下降 > 30% 异常 |
    | `/api/admin/stats/group` | 分组统计 | N/A | 单用户积压 > 50 |
    | `/api/admin/trace` | 链路追踪 | N/A | p99 > 5s 告警 |
    | `/api/admin/trace/spans/{id}` | 单 span 详情 | N/A | error span > 0 |
    | `/api/admin/expire/scan` (POST) | 过期清理 | N/A | 每次清理 > 1000 需关注 |
- **ETA**：W1 末
- **成功标准**：新人能根据表格自己配 Grafana

### A2. 故障 Runbook（5 个常见场景）
- **位置**：`ToT/CC/runbook.md`（新建）
- **内容**（每个场景：现象 → 排查步骤 → 恢复 → 事后）：
  1. **`/healthz` 返回 `pg=down`**：检查 PG 连接 → `ps aux | grep postgres` → 看连接池 `pool._closing`
  2. **`/api/admin/stats/overview` instance 积压飙升**：按 group 看 → 找积压任务最重的用户 → 通知或加签
  3. **`/metrics` request latency p99 飙升**：看 trace → 找慢 span → 是引擎慢还是 DB 慢
  4. **部署后 `/version` 与 git tag 不符**：检查 `__init__.py` 是否被 `release.sh` 更新 → 重跑 `release.sh`
  5. **`/api/admin/expire/scan` 清理失败**：看返回的 error → 检查 PG 锁 → 重试
- **ETA**：W2 末
- **成功标准**：MTTR 15 分钟达标

### A3. 审计日志字段手册
- **位置**：`ToT/CC/audit-fields.md`（新建）
- **内容**：
  - 链路追踪字段：
    - `trace_id` / `span_id` / `parent_id`：层级关系
    - `operation`：动作名（如 `processTask/execute`）
    - `operator`：操作人
    - `args`：输入参数（注意敏感字段脱敏）
    - `result.code`：0 = 成功
    - `duration_ms`：耗时
  - 审计关注点：
    - 敏感操作（delegate / transfer）必须留痕
    - 失败操作（result.code != 0）必须可追
    - 跨租户/跨部门操作需 highlight
- **ETA**：W2 末
- **成功标准**：审计员能独立查 1 个事故的全链路

### A4. 部署 checklist（本仓具体步骤）
- **位置**：`ToT/CC/deploy-checklist.md`（新建）
- **内容**：
  - **首次部署**：
    1. 克隆 → 跑 `bash ToT/sop/release.sh vX.Y.Z`（自动更新 `__init__.py`）
    2. 启动：`python3 -m uvicorn main_pg:app --port 8102`（PG 模式）
    3. 验证：`curl http://localhost:8102/healthz` → `status=UP`
    4. 验证：`curl http://localhost:8102/version` → `version=X.Y.Z`
    5. 验证：`curl http://localhost:8102/api/admin/health` → 详细健康
  - **升级部署**：
    1. `git pull` → `bash release.sh vX.Y.Z`
    2. graceful shutdown：`kill -TERM <pid>`（uvicorn 处理 in-flight 请求）
    3. 启动新版本 → 验证版本号
    4. 看 `/api/admin/trace` 5 分钟确认无 error spike
  - **回滚**：
    1. `git checkout <prev-tag>` → 重启 → 验证
- **ETA**：W3 末
- **成功标准**：新人按 checklist 独立完成首次部署

### A5. 容量基线 + 监控告警阈值
- **位置**：`ToT/CC/capacity-baseline.md`（新建）
- **内容**：
  - **当前基线**（待采集）：
    - 单实例支撑并发：~50 实例（待实测）
    - PG 表增长：每实例 ~10 行 × 5 表 = 50 行
    - 内存：每实例 ~5KB
  - **告警阈值建议**：
    - `/healthz` 持续 `pg=down` 30s → P0
    - `/metrics` request error rate > 5% → P1
    - `/api/admin/stats/overview` 总积压 > 200 → P2
    - 磁盘使用 > 80% → P2
    - PG connection pool idle < 10% → P2
- **ETA**：W4 末
- **成功标准**：告警噪音 < 5 条/天

### A6. 健康度门禁（CI 防退化）
- **位置**：`ToT/sop/release.sh` Step 0（与 01-engine-developer A6 共用）
- **动作**：把 `health-check.py --json` 加进 release 流水线
- **ETA**：W4 末
- **成功标准**：手动跑一次确认 < 100 阻断

---

## 5. 反馈闭环（Feedback Loop）

| 渠道 | 内容 | 频率 |
|---|---|---|
| `feedback/04-ops-audit-<seq>.md` | 故障 / 监控盲点 / 部署坑 | 事件驱动 |
| `feedback/_routes/04-*.md`（来自 **03-participant**）| 参与者反馈中带 `system-perf` / `system-down` / `audit-trace` | 每周自动分流 |
| postmortem（事故后 24h 内） | RCA + action items | 事件后 |
| 季度容量评审 | 趋势 + 扩缩容 | 季度 |
| 季度合规审计 | 审计日志完整度 + 权限 | 季度 |

**反馈处理 SLA**：
- P0（生产故障）：15 分钟内
- P1（监控盲点）：1 周内补
- P2（容量建议）：季度评审
- **来自 03-participant 的 system-down**：立刻（最高优）——参与者已经感知系统不可用

---

## 5.5 ★ 来自参与者反馈的接收（飞轮下游）

本 plan 是飞轮的 3 个下游之一。参与者反馈中带以下标签的会自动路由到本 plan：

| 反馈标签 | 触发行动 | 路由工具 |
|---|---|---|
| `system-perf` + 卡顿超时 | A1 监控仪表盘调阈值 + A5 容量基线 | `feedback-triage.py` |
| `system-down` + 服务挂 | A2 runbook + 紧急响应 | `feedback-triage.py` |
| `audit-trace` + 查不到链路 | A3 审计日志手册补充 | `feedback-triage.py` |
| `bug` + 涉及监控端点 | A1 监控端点解读表 | `feedback-triage.py` |

**闭环要求**：
- 修复/补充后，在 `feedback/_routes/04-<seq>.md` 标注 `状态: 已闭环`
- 同步到 `feedback/03-participant-<seq>.md` 的 `## 闭环` 字段
- 同步更新 `ToT/CC/runbook.md` 或 `ToT/CC/monitoring-dashboard.md`

---

## 6. Success Metrics（量化）

| 指标 | 当前 | 目标（4 周末）|
|---|---|---|
| 监控端点解读表 | 0 | 1 个完整表（10 个端点）|
| 故障 runbook | 0 | ≥ 5 个场景 |
| 审计日志手册 | 0 | 1 个 doc |
| 部署 checklist | 0 | 1 个 doc |
| 容量基线 | 0 | 1 个 doc |
| **MTTR** | 未知基线 | ≤ 15 分钟 |
| 季度审计不合规项 | 0 | 持续 0 |
| 健康度门禁 | 未启用 | 已启用 + 0 退化 |

---

## 7. 跨 Persona 引用

- ← 01-engine-developer：API 升级影响监控端点兼容性
- ← 02-process-designer：流程退步会反映在 `/api/admin/stats/overview`
- → ToT/docs/guides/06-deployment.md：通用部署指南（CC 是本仓具体）
- → ToT/sop/health-check.py：综合健康度（也可作监控源）
- → ToT/sop/release.sh：升级 + 版本同步