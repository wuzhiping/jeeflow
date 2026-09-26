# ToT/CC · 共享反馈通道

> **关键变化（2026-09-25）**：03-participant 是飞轮中枢；其他 3 个 plan 通过 `feedback-triage.py` 自动接收 03 的反馈。
>
> **不再 4 个平行的反馈通道**；而是**1 个中枢入口 + 3 个下游自动路由**。

---

## 飞轮入口（only one）

```
参与者 → feedback/03-participant-<seq>.md
              ↓
      feedback-triage.py（自动分流）
              ↓
   ┌──────────┼──────────┐
   ↓          ↓          ↓
01-engine   02-designer  04-ops
              ↓
       修复/补充
              ↓
       闭环回写 03
              ↓
       FAQ/5分钟卡更新
              ↓
       飞轮加速
```

---

## 反馈文件命名规范

```
feedback/<persona 编号>-<seq>-<简短标题>.md
```

| 编号 | Persona | 入口类型 |
|---|---|---|
| 03 | 业务流程参与者 | **飞轮中枢入口**（主要来源）|
| 01 | 引擎开发升级 | 下游路由（来自 03 `bug`）|
| 02 | 业务流程设计管理者 | 下游路由（来自 03 `design-issue` / `process-gap`）|
| 04 | 系统管理运维审计 | 下游路由（来自 03 `system-perf` / `system-down` / `audit-trace`）|

**示例**：
- `03-001-verify-flow-async-issue.md`（参与者反馈，路由到 01）
- `03-002-countersign-vote-stuck.md`（参与者反馈，路由到 02）
- `03-003-pg-pool-exhausted.md`（参与者反馈，路由到 04）
- `01-001-upgrade-migration-missing.md`（直接给 01 的，少见）

---

## 反馈模板

```markdown
# Feedback: <seq> - <标题>

> **Persona**: 03
> **Date**: YYYY-MM-DD
> **Reporter**: <name/role>
> **Severity**: P0/P1/P2

## 现象（What happened）
<具体场景，无虚构建议>

## 影响（Impact）
<影响范围 / 频次 / 用户数>

## 期望（What we want）
<理想状态>

## 已尝试（What I tried）
<已做的自救步骤>

## 证据（Evidence）
<reference: 文件:行号 / curl 输出 / 截图 / 日志片段>

## 标签（Tags）
<必填：`bug` / `design-issue` / `process-gap` / `system-perf` / `system-down` / `audit-trace` / `doc-gap` / `ux-issue`>
```

**闭环字段**（修复后由 01/02/04 owner 加）：
```markdown
## 闭环
**Closed by**: <plan owner>
**Closed at**: YYYY-MM-DD
**Action**: <PR/commit/FAQ 更新>
**Synced to**: <ToT/CC/faq.md 或 ToT/CC/runbook.md 等>
```

---

## 自动分流规则（feedback-triage.py）

| 标签 | 路由到 | 优先级 |
|---|---|---|
| `bug` | 01-engine-developer | P0/P1 → 48h |
| `design-issue` | 02-process-designer | P0/P1 → 48h |
| `process-gap` | 02-process-designer | P1 → 1 周 |
| `system-perf` | 04-ops-audit | P0 → 24h |
| `system-down` | 04-ops-audit | **P0 → 立刻** |
| `audit-trace` | 04-ops-audit | P1 → 1 周 |
| `doc-gap` | 03-participant（自身）| P2 → 季度 |
| `ux-issue` | 03-participant（自身）| P2 → 季度 |

**触发命令**：
```bash
# 每周一 CI 自动跑
python3 ToT/sop/feedback-triage.py
# 生成 feedback/_routes/<plan>-<seq>.md + _triage-report.md
```

---

## 反馈处理 SLA

| 严重度 | 含义 | 响应时间 | 解决时间 |
|---|---|---|---|
| **P0** | 阻塞生产 / 全员受影响 | 15 分钟 | 4 小时 |
| **P1** | 单点问题 / 可绕过 | 当天 | 1 周 |
| **P2** | 改进建议 / 体验 | 季度评审 | 季度 |

---

## 飞轮健康指标

| 指标 | 计算 | 当前 | 目标 |
|---|---|---|---|
| 月分流条目数 | `feedback/03-*` → 01/02/04 数 | 0 | ≥ 8 |
| 闭环率 | 已闭环条目 / 总条目 | N/A | ≥ 70% |
| 平均闭环时长 | ship → 写回 FAQ | N/A | ≤ 4 周 |
| 自助解决率 Δ | (本月 - 上月) | N/A | +5% |

---

## 当前反馈记录

| ID | Persona | 标题 | Severity | 路由到 | 状态 | 文件 |
|---|---|---|---|---|---|---|
| （暂无，飞轮刚启动）| | | | | | |

**每周一**：自动跑 `feedback-triage.py` → 输出 `_triage-report.md`

---

## 飞轮季度回顾模板

```markdown
# CC 飞轮季度回顾 · YYYY Q?

## 指标
- 反馈总量：N
- 已分流：N (X%)
- 已闭环：N (Y%)
- 自助解决率：X% (Δ +Y%)
- 月度 RPM：N

## Top 3 路由条目（按闭环时长）
1. <标题> - 闭环 X 天
2. ...

## 飞轮卡点
1. ...
2. ...

## 下季度动作
1. ...
2. ...
```