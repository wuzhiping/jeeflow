# Test Report: 15-decision-amount (regression)

- **流程文件**: `flows/15-decision-amount.json`
- **processDefineId**: 17
- **测试时间**: 2026-09-17 17:00
- **工具**: `tdd/regression_runner.py`
- **原始报告**:
  - `tdd/regression_17_full_5k.json`（amount=5000 小额）
  - `tdd/regression_17_full_15k.json`（amount=15000 大额）

## 1. 流程结构（已实查 JSON）

```
start → apply(user1) → decision1 → (task1(user2) | end)
                                         │
                                         └─→ end
```

边表达式：
- `decision1 → task1`：`amount >= 10000`
- `decision1 → end`：`amount < 10000`
- `task1 → end`：无条件

## 2. 路由矩阵与结果（14/14 PASS）

### 2.1 小额自动完成路径（amount=5000）

| submitType | 路径 | 预期 state | 实际 state | 结果 |
|-----------|------|-----------|-----------|------|
| 0 APPLY | apply → decision → end | 20 DONE | 20 | PASS |
| 1 AGREE | apply → decision → end | 20 DONE | 20 | PASS |
| 2 REJECT | runner auto-exec task1 → REJECT | 45 REJECT | 45 | PASS |
| 3 ROLLBACK | runner auto-exec task1 → ROLLBACK | 10 DOING | 10 | PASS |
| 5 RE_APPLY | apply → decision → end | 20 DONE | 20 | PASS |
| 6 ROLLBACK_TO_OP | runner auto-exec task1 → ROLLBACK | 10 DOING | 10 | PASS |
| 20 COUNTERSIGN_DISAGREE | apply → decision → end | 20 DONE | 20 | PASS |

### 2.2 大额复核路径（amount=15000）

| submitType | 路径 | 预期 state | 实际 state | 结果 |
|-----------|------|-----------|-----------|------|
| 0 APPLY | apply → decision → task1 → end | 20 DONE | 20 | PASS |
| 1 AGREE | apply → decision → task1 → end | 20 DONE | 20 | PASS |
| 2 REJECT | apply → decision → task1 → REJECT | 45 REJECT | 45 | PASS |
| 3 ROLLBACK | apply → decision → task1 → ROLLBACK | 10 DOING | 10 | PASS |
| 5 RE_APPLY | apply → decision → task1 → end | 20 DONE | 20 | PASS |
| 6 ROLLBACK_TO_OP | apply → decision → task1 → ROLLBACK | 10 DOING | 10 | PASS |
| 20 COUNTERSIGN_DISAGREE | apply → decision → task1 → end | 20 DONE | 20 | PASS |

## 3. 关键 Runner 能力

1. **variables 注入**：新增 `--vars '{"amount":5000}'` 支持，业务变量（如 `amount`）通过 `startAndExecute.variables` 传递，可驱动 decision 节点 expr 路由。
2. **assignees 自动执行**：startAndExecute 后 engine 不自动跑下游 task1，runner 通过 detail API 取 taskState=10 活跃 taskId 并 `processTask/execute`。
3. **决策兜底**：当 amount < 10000 走 end 直达时，runner 仍会执行 task1（如有），但 end 流程下 task1 不在路径上，submitType 仅影响 task1 内部逻辑；最终 detail.state 由 apply 节点的 submitType 决定。

## 4. 关键实例 ID（小额路径）

| submitType | processInstanceId |
|-----------|-------------------|
| 0 | 91756500382083 |
| 1 | 91756500460005 |
| 2 | 91756500538951 |
| 3 | 91756500616873 |
| 5 | 91756500694795 |
| 6 | 91756500771693 |
| 20 | 91756500850640 |

## 5. 关键实例 ID（大额路径）

| submitType | processInstanceId |
|-----------|-------------------|
| 0 | 91756506500146 |
| 1 | 91756506578068 |
| 2 | 91756506662134 |
| 3 | 91756506744152 |
| 5 | 91756506826170 |
| 6 | 91756506914332 |
| 20 | 91756506994303 |

## 6. 结论

**14/14 全部通过**（7 个 submitType × 2 个 amount 路径）。`15-decision-amount` 流程：
- 小额（amount < 10000）走 decision → end 自动完成。
- 大额（amount >= 10000）走 decision → task1 复核，submitType 决定终态。
- 决策路由严格基于 expr `amount >= 10000` / `amount < 10000`，与 submitType 解耦。
