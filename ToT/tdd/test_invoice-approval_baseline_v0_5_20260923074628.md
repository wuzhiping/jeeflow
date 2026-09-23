# Baseline · invoice-approval · v0.5 · 20260923074628

> **目的**：流程自动化生成的 baseline（用 `tdd-flow.py --save-baseline`）
> **原始测试**：`ToT/tdd/test_invoice-approval_20260923074628.md`
> **原始数据**：`ToT/tdd/test_invoice-approval_baseline_v0_5_20260923074628.json`

---

# TDD Test Log · invoice-approval · 20260923074628

**SPI_FOLDER**: `dev`  |  **operator**: `u_fdp_pm`
**global_top_vars**: `{"tf_manager": "u_bob", "tf_treasurer": "u_carol"}`
**mode**: 自定义 scenarios (3 个)

## 1. 静态校验

- validate_flow: **6 nodes, 6 edges**, 0 errors, 0 warnings

## 2. 引擎 verify_flow

- errors: **0**, warnings: **2**, patterns: **0**
  - ⚠️  [W013] decision 节点[decision_amount] 有 2 条出边, 全部带 expr (无默认边)。如数据不满足任一 expr, 引擎会兜底走第一条边 (可能导致孤儿 task)。建议: 加一条 expr="" 的默认边作为兜底。
  - ⚠️  [W014] 流程含 snaker:decision 节点. 部署后请立即回归决策路由 (e.g. 跑 1 个决策分支样例, 验证 _cleanup_orphan_decision_tasks 不抛 TypeError). 历史 BUG: FIX-T11

## 3. 引擎实跑

### small path (instance=92283687934977) — variable=`{"amount": 500, "purpose": "办公"}` — top_vars=`{"tf_manager": "u_bob", "tf_treasurer": "u_carol"}`

**最终 state**: `DONE (20)`

| task | state | operator | actors |
|------|-------|----------|--------|
| submit             | DONE   | u_fdp_pm   | ['u_fdp_pm'] |
| pay                | DONE   | flow.auto  | ['u_carol'] |

### big path (instance=92283687946244) — variable=`{"amount": 8000, "purpose": "服务器"}` — top_vars=`{"tf_manager": "u_bob", "tf_treasurer": "u_carol"}`

**最终 state**: `DONE (20)`

| task | state | operator | actors |
|------|-------|----------|--------|
| submit             | DONE   | u_fdp_pm   | ['u_fdp_pm'] |
| approve            | DONE   | flow.auto  | ['u_bob'] |
| pay                | DONE   | flow.auto  | ['u_carol'] |

### reject path (instance=92283687960584) — variable=`{"amount": 8000, "purpose": "服务器"}` — top_vars=`{"tf_manager": "u_bob", "tf_treasurer": "u_carol"}`

**最终 state**: `DONE (20)`

| task | state | operator | actors |
|------|-------|----------|--------|
| submit             | DONE   | u_fdp_pm   | ['u_fdp_pm'] |
| approve            | DONE   | flow.auto  | ['u_bob'] |
| submit             | DONE   | flow.auto  | ['u_fdp_pm'] |
| approve            | DONE   | flow.auto  | ['u_bob'] |
| pay                | DONE   | flow.auto  | ['u_carol'] |

## 4. 总结

- static errors: **0**
- engine errors: **0**
- small final: **DONE**
- big final: **DONE**
- reject final: **DONE**

## 5. 原始数据

机器可读原始响应：与本文件同目录的 `.json` 文件（含 deploy / start / execute / detail 全量响应）
