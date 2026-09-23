# Iteration #6 · 2026-09-22 · 3 阶段环境流水线

> **驱动**：用户口头指令 "我们提供和开发同步的快速实验环境 ... 1. 用户可以先本地memory 完成闭环测试 2.上传至组织服务器 3.正式发布流程，具体sop待定"
> **意义**：把"哪个环境做什么"显式化 —— local → org → customer 3 阶段管道

---

## 1. 时间线（30 分钟）

| 时段 | 工作 | 产出 |
|------|------|------|
| **0~5 min** | 盘点：4 server 不够，加 org-server = 5 server 3 阶段 | 蓝图 |
| **5~10 min** | 更新 `servers.json`：加 org-server + tier/risk_level/ai_can_push/ai_can_reset 字段 | 配置 |
| **10~15 min** | 写 `env-pipeline.md` SOP（10 节）| SOP |
| **15~20 min** | 写 `promote.py` CLI 工具（list/status/push/request-promote/promote/rollback）| 工具 |
| **20~25 min** | `ea-compliance.py` §9.7 加 4 项检查 | 自验证 |
| **25~30 min** | 演示 + 写 iteration + 更新 README/roadmap | 飞轮 |

---

## 2. 闭环示意

```
   ┌── "开发者说想 3 阶段发布" ──┐
   ↓                              │
  盘点现有 4 server               │
   ↓                              │
  加 org-server = 3 阶段          │
   ↓                              │
  加 tier/risk_level/ai_can_*    │
   ↓                              │
  写 env-pipeline.md SOP         │
   ↓                              │
  写 promote.py CLI              │
   ↓                              │
  ea-compliance.py §9.7 +4 项    │
   ↓                              │
  35/35 PASS                      │
   ↓                              │
  演示 push/request-promote/promote│
   ↓                              │
  写 iterations/<date>_env-pipeline│
   ↓                              │
  → 飞轮自转第 5 圈 ✅ ──────────┘
```

---

## 3. 3 阶段流水线（落地版）

| 阶段 | Server | Tier | Risk | AI Push | AI Reset | 场景 |
|------|--------|------|------|---------|----------|------|
| 1. Local | `local-memory` (8101) | stage-1-dev | low | ✅ | ✅ | 快速迭代 |
| 1. Local | `local-pg` (8102) | stage-1-dev | low | ✅ | ✅ | 集成测试 |
| 2. Org | `org-server` | stage-2-staging | medium | ✅ | ❌ | 团队共享验证 |
| 3. Customer | `customer-test` (abc.feg.cn) | stage-3-prod | high | ❌ | ❌ | 客户正式 |
| 3. Production | `production-future` | stage-3-prod | critical | ❌ | ❌ | 未来生产 |

**核心原则**：**越接近生产，约束越严**。Local 全自动，Customer 强制人工审批。

---

## 4. promote.py 工具能力

| 子命令 | 用途 | 谁用 |
|--------|------|------|
| `list` | 列出所有 server + tier + AI 能力 | 所有人 |
| `status <flow>` | 看 flow 在各环境的部署状态 | 开发者 |
| `push <flow> from-to` | 自动推（仅 local→org）| AI |
| `request-promote <flow>` | 生成 promote 请求（不实际推）| 开发者 |
| `promote <flow> from-to --confirm-ai` | 实际推（org→customer，需审批标志）| AI（人工审批后）|
| `rollback <flow> from-to` | 回滚（customer→org 等反向）| AI |

**演示边界**（已验证）：
- ✅ `push local-memory-to-local-pg` → 自动推
- ✅ `request-promote fdep` → 生成审批请求
- ✅ `promote fdep org-to-customer WITHOUT --confirm-ai` → 拒绝
- ✅ `promote fdep org-to-customer WITH --confirm-ai` → 检查 `ai_can_push=false` → 拒绝（强制走人工）
- ✅ `list` → 5 server 完整展示
- ✅ `status fdep` → 4 server 部署状态（org-server url 未设）

---

## 5. ADR

| 决策 | 选择 | 理由 |
|------|------|------|
| 加 org-server 而非重用现有 server | **新加** | Local = 单人开发；Org = 团队协作；Customer = 客户；3 层分离清晰 |
| ai_can_push 在 customer=false | **是** | 推 customer 必须人工审批（高风险） |
| ai_can_reset 在 org=false | **是** | reset org 可能影响同事 |
| 用 tier 字段而非 stage | **tier** | 未来可加 tier-4 (backup) 等 |
| promote.py 是 CLI 不是 API | **CLI** | 直接 `python3` 调用；不增加 HTTP 服务面 |
| 必须 --confirm-ai flag | **是** | 双保险：CLI flag + server ai_can_push 检查 |

---

## 6. 度量（飞轮转 6 次的累积）

| 指标 | Iter#1 | Iter#2 | Iter#3 | Iter#4 | Iter#5 | **Iter#6** | 累积 |
|------|--------|--------|--------|--------|--------|------------|------|
| SOP | 10 | 11 | 12 | 13 | 13 | **14** | 14 |
| §9 检查项 | 0 | 27 | 31 | 31 | 31 | **35** | 35 |
| Servers | 4 | 4 | 4 | 4 | 4 | **5** | 5 |
| 设计模式 | 0 | 8 | 9 | 10 | 10 | **11** | 11 |
| 迭代记录 | 1 | 2 | 3 | 4 | 5 | **6** | 6 |
| **可发布性** | ❌ | ❌ | ❌ | ❌ | ❌ | **✅** | - |

**关键变化**：从"只能 local 测试"→"可走 3 阶段发布"。

---

## 7. 闭环证据

```
迭代前 #5:
  - 4 server（local + customer），AI 全权或受限二选一
  - 没有显式的"开发 → 验证 → 发布"管道
  - 推 customer 必须看 customer-data-reset 留档
  ↓
加 org-server + tier + ai_can_* 字段
  ↓
写 env-pipeline.md SOP（10 节）
  ↓
写 promote.py CLI（6 子命令）
  ↓
ea-compliance §9.7 +4 项 → 35/35 PASS
  ↓
演示完整流程（含所有边界条件）
  ↓
迭代后 #6:
  - 5 server × 3 tier × 权限矩阵
  - CLI 工具（list / status / push / request-promote / promote / rollback）
  - 边界条件全部正确处理
  - 飞轮转 5 圈
```

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-22** | **第六轮迭代**：3 阶段环境流水线（local → org → customer）。① `servers.json` 加 org-server + tier/risk_level/ai_can_push/ai_can_reset 字段；② 新建 `env-pipeline.md` SOP（10 节）；③ 新建 `promote.py` CLI（6 子命令）；④ `ea-compliance.py` §9.7 加 4 项检查（35/35 PASS）；⑤ 新增 Pattern 11；⑥ 飞轮自转第 5 圈。 |