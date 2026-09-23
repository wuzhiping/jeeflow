# SOP: 3 阶段环境流水线 (env-pipeline)

> **所属**：组织 SOP 集（与 `env-config` / `customer-data-reset` 互补）
> **场景**：流程定义的"本地快速实验 → 组织服务器验证 → 客户正式发布"完整生命周期
> **永久规则**：见 `ToT/README.md` §1 + §11 + `ToT/ea/roadmap.md` §5 Pattern 11
> **配套工具**：`ToT/sop/promote.py`（CLI 助手：list / status / push / promote）

---

## 1. 适用场景

| ✅ 适用 | ❌ 不适用 |
|--------|-----------|
| 新流程定义完成本地测试后推到共享环境 | 仅本地调试（用 `local-memory` 即可）|
| 跨开发者协作（团队共用 org server）| 单人项目（用 `local-pg` 即可）|
| 客户服务器正式发布（需 SOP 例外审批）| 紧急 hotfix（直接改客户服务器，但需留档）|

## 2. 核心原则

> **不在客户服务器做实验**，不在组织服务器做探索。

| 层 | 角色 | 数据敏感度 | 风险 | 允许的操作 |
|----|------|------------|------|-----------|
| **Stage 1: Local** | 开发者本人 | 无（启动即空）| 0（重启清空）| AI 全权：push / reset / 改 |
| **Stage 2: Org** | 团队 | 中（团队共享）| 中（可能影响同事）| AI 推 / 不可 reset |
| **Stage 3: Customer / Prod** | 客户 / 真实用户 | 高（客户数据）| 高（一旦出错影响业务）| AI 推需人工审批；reset 需 SOP 例外 |

**越接近生产，约束越严。**

## 3. 3 阶段流水线（流程定义生命周期）

```
   ┌──────────────────┐  push  ┌──────────────────┐  promote  ┌──────────────────┐
   │  Stage 1: Local  │ ──────→ │   Stage 2: Org   │ ────────→ │ Stage 3: Customer│
   │  (memory / PG)   │  自动   │   (shared dev)   │  人工审批  │   (production)  │
   │                  │         │                  │            │                  │
   │ • 闭环测试       │         │ • 跨人协作验证    │            │ • 客户业务试用    │
   │ • 快速迭代       │         │ • CI 跑通        │            │ • 监控 / 留档     │
   │ • 完整性 30-60%  │         │ • 完整性 60-90%  │            │ • 完整性 90%+    │
   └──────────────────┘         └──────────────────┘            └──────────────────┘
        ↑ AI 全权                        ↑ AI 可推                       ↑ AI 受限
```

## 4. 每个阶段的详细操作

### Stage 1 · Local（快速实验）

| 操作 | 执行方 | 工具 |
|------|--------|------|
| 写 flow.json | 人工 | $EDITOR |
| 写 Job Cards | AI 半自动 | `gen-job-cards.py` |
| 启动服务器 | 人工 | `python -m uvicorn main:app --port 8101` |
| 部署 + 冒烟 | AI | `auto_deploy_fdep()`（main_common 内嵌）|
| 跑 demo 闭环 | AI | `flow_completeness.py` + `tdd-flow.py` |
| 完整性达标（≥30% → 60%）| AI | 跑 `ea-compliance.py` |

**可丢失**：可接受 — 启动即空数据，重启清零。

### Stage 2 · Org（团队验证）

| 操作 | 执行方 | 工具 |
|------|--------|------|
| 推送 flow.json 到 org server | AI（半自动）| `promote.py push <flow> local-to-org` |
| 在 org server 跑完整 smoke test | AI | `promote.py status <flow>` + curl /wf/... |
| 跨开发者协作 | 团队 | git / Slack / IM |
| 跑完整 TDD baseline | AI | `promote.py` 调用 `tdd-flow.py` against org |
| 完整性达标（≥60% → 90%）| AI | `ea-compliance.py` against org |

**不可 reset**：可能影响同事的实例。

### Stage 3 · Customer（正式发布）

| 操作 | 执行方 | 工具 |
|------|--------|------|
| 申请发布 | 人工（**必须**） | `promote.py request-promote <flow>` |
| **审批** | 人工（产品负责人） | SOP 例外审批留档 |
| 推送 flow.json | AI（受限）| `promote.py promote <flow> org-to-customer` |
| 跑冒烟测试 | AI | `promote.py status <flow>` |
| 写发布留档 | AI | 自动写 `ToT/customer-resets/<ts>_release_<flow>.md` |
| 监控 | AI + 人工 | `dashboard` + 告警 |

**重大风险**：客户数据。reset 走 `customer-data-reset.md` SOP 例外审批。

## 5. 命令清单（promote.py）

```bash
# === 列出所有 server + 状态 ===
python3 ToT/sop/promote.py list

# === 查看某 flow 在各环境的 defineId + 最近 instance ===
python3 ToT/sop/promote.py status fdep

# === 推 local → org（自动） ===
python3 ToT/sop/promote.py push fdep local-to-org

# === 推 org → customer（需人工确认） ===
python3 ToT/sop/promote.py request-promote fdep    # 1. 生成 promote 请求
# （人工审批后）
python3 ToT/sop/promote.py promote fdep org-to-customer  # 2. AI 执行

# === 回滚（org → local） ===
python3 ToT/sop/promote.py rollback fdep org-to-local
```

## 6. 自动化范围

| 操作 | Local | Org | Customer |
|------|-------|-----|----------|
| push flow.json | ✅ AI 自动 | ✅ AI 半自动 | ⚠️ AI + 人工审批 |
| reset 数据 | ✅ AI 自动 | ❌ AI 不可 | ⚠️ 需 SOP 例外 |
| smoke test | ✅ AI 自动 | ✅ AI 自动 | ✅ AI 自动 |
| ea-compliance | ✅ AI 自动 | ✅ AI 自动 | ✅ AI 自动 |
| fix bug | ✅ AI 自动 | ⚠️ 人工 review | ⚠️ 人工 fix |

## 7. 与其他 SOP 的关系

| SOP | 关系 |
|-----|------|
| `env-config.md` | 本 SOP 是 env-config 的"提升策略"维度 |
| `customer-data-reset.md` | Stage 3 的 reset 走这个 SOP（例外审批）|
| `engine-deploy.md` | 引擎代码 push（vs 流程定义 push）走这个 SOP |
| `ea-compliance.md` | 每个 stage 跑完都要过 compliance |
| `flow-design.md` | 流程设计 SOP（3 阶段都遵循）|

## 8. 风险与回滚

| 风险 | 缓解 |
|------|------|
| org server 推错 flow 损坏共享数据 | 推前必跑 `flow_completeness.py` ≥60% |
| customer 推错无法快速回滚 | 推前必须 human 审批 + 推完后立刻人工 confirm |
| org server reset 影响同事 | ai_can_reset=false（需人工操作）|
| pipeline 步骤被绕过 | `ea-compliance.py` §9.7 自动检查 pipeline 一致性 |

## 9. 关联文档

- `ToT/config/servers.json` — 服务器配置（含 tier / risk_level / ai_can_*）
- `ToT/sop/promote.py` — 提升 CLI 工具
- `ToT/sop/env-config.md` — 配置管理（互补）
- `ToT/sop/customer-data-reset.md` — Stage 3 reset SOP
- `ToT/ea/roadmap.md §5 Pattern 11` — 3 阶段流水线 pattern

## 10. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-22** | **初稿**：3 阶段环境流水线（local → org → customer）+ 自动化范围 + 命令清单 + 与其他 SOP 关系。配套 `ToT/sop/promote.py` 工具 + `servers.json` 加 tier/risk_level/ai_can_* 字段。 |