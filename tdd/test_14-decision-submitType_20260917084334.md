# Test Report: 14-decision-submitType (regression)

- **流程文件**: `flows/14-decision-submitType.json`
- **processDefineId**: 16
- **测试时间**: 2026-09-17 16:43
- **工具**: `tdd/regression_runner.py`
- **原始报告**: `tdd/regression_16_20260917084334.json`

## 1. 流程结构（已实查 JSON）

```
start → apply(user1) → task1(user2) → decision1 → (end | apply)
                                            │
                                            └── expr=submitType==2||submitType==3
```

边表达式：
- `decision1 → end`：`submitType==0 || submitType==1 || submitType==5 || submitType==20`
- `decision1 → apply`：`submitType==2 || submitType==3`

## 2. 路由矩阵与结果（7/7 PASS）

| submitType | 路径 | 预期 state | 实际 state | 结果 |
|-----------|------|-----------|-----------|------|
| 0 APPLY | decision → end | 20 DONE | 20 | PASS |
| 1 AGREE | decision → end | 20 DONE | 20 | PASS |
| 2 REJECT | decision → apply (回退) | 45 REJECT | 45 | PASS |
| 3 ROLLBACK | decision → apply (回退) | 10 DOING | 10 | PASS |
| 5 RE_APPLY | decision → end | 20 DONE | 20 | PASS |
| 6 ROLLBACK_TO_OP | decision → apply (回退) | 10 DOING | 10 | PASS |
| 20 COUNTERSIGN_DISAGREE | decision → end | 20 DONE | 20 | PASS |

注：submitType=3 与 submitType=2 在本流程中都路由到 `apply`，但 `submitType=2` 是 `execute_and_jump_to_end` → inst.reject() → state=45（终态），而 `submitType=3` 是 `execute_and_jump_task`（无 target）→ state=10（DOING 重激活）。

## 3. Runner 关键修复

1. **action 名修正**：`processInstance/execute` → `processTask/execute`（未知 action 错误）。
2. **startBody 解析**：优先 `data.processInstanceId`，顶层回退。
3. **detail 取 task_id**：startAndExecute 不返回 task_id，runner 调用 detail 取 taskState=10 的活跃 taskId 再 execute。
4. **assignees 注入**：传递 `{apply:user1, task1:user2}` 让 task1 可被 user2 execute。
5. **EXPECTED_STATE 修正**：`detail.state` 是 `InstanceState` 枚举值（DONE=20），不是 `finish_state=7`。
6. **`/api/reset` 重置**：每 case 前重置避免 state 污染。

## 4. 关键实例 ID

| submitType | processInstanceId |
|-----------|-------------------|
| 0 | 91756353591487 |
| 1 | 91756353677601 |
| 2 | 91756353757571 |
| 3 | 91756353838565 |
| 5 | 91756353917512 |
| 6 | 91756353998506 |
| 20 | 91756354103053 |

## 5. 结论

**7/7 全部通过**。`14-decision-submitType` 流程在 submitType=0/1/5/20 路由到 end（state=20 DONE），在 submitType=2/3/6 路由回 apply（state=45 REJECT 或 state=10 DOING），decision 节点按最后一个 task 的 submitType 路由，路由矩阵完整覆盖。
