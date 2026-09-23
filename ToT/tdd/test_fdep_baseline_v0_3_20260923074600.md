# Baseline · fdep · v0.3 · 20260923074600

> **目的**：流程自动化生成的 baseline（用 `tdd-flow.py --save-baseline`）
> **原始测试**：`ToT/tdd/test_fdep_20260923074600.md`
> **原始数据**：`ToT/tdd/test_fdep_baseline_v0_3_20260923074600.json`

---

# TDD Test Log · fdep · 20260923074600

**SPI_FOLDER**: `dev`  |  **operator**: `u_fdp_pm`
**mode**: 自定义 scenarios (3 个)

## 1. 静态校验

- validate_flow: **10 nodes, 10 edges**, 0 errors, 0 warnings

## 2. 引擎 verify_flow

- errors: **0**, warnings: **2**, patterns: **0**
  - ⚠️  [W008] 节点 [decision_intake]→[stage_pm] 有 2 条边 (冗余)
  - ⚠️  [W014] 流程含 snaker:decision 节点. 部署后请立即回归决策路由 (e.g. 跑 1 个决策分支样例, 验证 _cleanup_orphan_decision_tasks 不抛 TypeError). 历史 BUG: FIX-T11

## 3. 引擎实跑

### happy path (instance=92283659665409)

**最终 state**: `DONE (20)`

| task | state | operator | actors |
|------|-------|----------|--------|
| stage_intake       | DONE   | u_fdp_pm   | ['u_fdp_pm'] |
| stage_pm           | DONE   | flow.auto  | ['u_fdp_pm'] |
| stage_design       | DONE   | flow.auto  | ['u_fdp_pm'] |
| stage_dev          | DONE   | flow.auto  | ['u_fdp_pm'] |
| stage_review       | DONE   | flow.auto  | ['u_fdp_pm'] |
| stage_feedback     | DONE   | flow.auto  | ['u_fdp_pm'] |

### reject path (instance=92283659699208)

**最终 state**: `REJECT (45)`

| task | state | operator | actors |
|------|-------|----------|--------|
| stage_intake       | DONE   | u_fdp_pm   | ['u_fdp_pm'] |
| stage_pm           | DONE   | flow.auto  | ['u_fdp_pm'] |

### resurrect path (instance=92283659707403)

**最终 state**: `DONE (20)`

| task | state | operator | actors |
|------|-------|----------|--------|
| stage_intake       | DONE   | u_fdp_pm   | ['u_fdp_pm'] |
| stage_pm           | DONE   | flow.auto  | ['u_fdp_pm'] |
| stage_intake       | DONE   | flow.auto  | ['u_fdp_pm'] |
| stage_pm           | DONE   | flow.auto  | ['u_fdp_pm'] |
| stage_design       | DONE   | flow.auto  | ['u_fdp_pm'] |
| stage_dev          | DONE   | flow.auto  | ['u_fdp_pm'] |
| stage_review       | DONE   | flow.auto  | ['u_fdp_pm'] |
| stage_feedback     | DONE   | flow.auto  | ['u_fdp_pm'] |

## 4. 总结

- static errors: **0**
- engine errors: **0**
- happy final: **DONE**
- reject final: **REJECT**
- resurrect final: **DONE**

## 5. 原始数据

机器可读原始响应：与本文件同目录的 `.json` 文件（含 deploy / start / execute / detail 全量响应）
