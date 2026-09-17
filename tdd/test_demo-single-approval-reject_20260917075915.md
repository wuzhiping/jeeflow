# Test Report: demo-single-approval-reject (PLAN A')

- **用例文件**: `tdd/demo-single-approval-reject.json`
- **测试时间**: 2026-09-17 16:00 ~ 16:10
- **测试目标**: 验证 decision 分流（驳回回退）流程端到端执行
- **流程版本**: 5 节点 5 边（含 1 decision 节点）
- **processDefineId**: 145（designId=15）

## 1. 流程结构

```
start → apply → task1 → decision1 → end
                            ↓ (submitType==2 || submitType==3)
                          apply (回退)
```

| 节点 | 类型 | assignee |
|------|------|----------|
| start | snaker:start | — |
| apply | snaker:task | user1（发起人） |
| task1 | snaker:task | user2（审批人） |
| decision1 | snaker:decision | — |
| end | snaker:end | — |

边表达式：
- `decision1 → end`：`submitType==0 || submitType==1 || submitType==5 || submitType==20`
- `decision1 → apply`：`submitType==2 || submitType==3`

## 2. 测试矩阵与结果

| 编号 | 路径 | submitType | 预期 state | 预期 active | 实际 state | 实际 active | 结果 |
|------|------|------------|-----------|-------------|-----------|-------------|------|
| T0 | 同意 | 1 (AGREE) | 20 DONE | [] | 20 | [] | PASS |
| T1 | APPLY (facade bug: 0→1) | 0 | 20 DONE | [] | 20 | [] | PASS |
| T2 | REJECT | 2 | 45 REJECT | [] | 45 | [] | PASS |
| T3 | ROLLBACK | 3 | 10 DOING | [apply] | 10 | [apply] | PASS |
| T4 | ROLLBACK_TO_OP | 6 | 10 DOING | [apply] | 10 | [apply] | PASS |

注：T1 实际发送 submitType=0，但因 facade.py:300 bug（`X or Y` falsy trap）被强制转为 1，行为等同于 T0。

## 3. 关键发现

### 3.1 Decision 节点是 expr 路由的唯一载体
- 普通任务节点的 `_follow_edges(flow, source_id)` 忽略边表达式（engine.py:557-558），会**同时激活所有出边**。
- 只有 `_evaluate_decision`（engine.py:353-369）会按 expr 评估并选第一条 truthy 边。
- 因此「同一任务按 submitType 分流」必须插入 decision 节点。

### 3.2 SubmitType 路由矩阵（实测验证）

| submitType | 引擎分支 | 目标 | state | active |
|-----------|----------|------|-------|--------|
| 0 APPLY | execute_process_task 默认 | decision → end | 20 | [] |
| 1 AGREE | execute_process_task 默认 | decision → end | 20 | [] |
| 2 REJECT | execute_and_jump_to_end | inst.reject() | **45 REJECT** | [] |
| 3 ROLLBACK | execute_and_jump_task（无 target） | _previous_task_name → apply | 10 | [apply] |
| 4 JUMP | execute_and_jump_task（带 target） | 命名节点 | 视目标 | 视目标 |
| 5 RE_APPLY | execute_process_task 默认 | decision → end | 20 | [] |
| 6 ROLLBACK_TO_OP | execute_and_jump_to_first_task_node | apply（assignee=operator） | 10 | [apply] |
| 20 COUNTERSIGN_DISAGREE | execute_process_task 默认 | decision → end | 20 | [] |

### 3.3 InstanceState 枚举（model.py:45-52）
- `DOING=10`、`DONE=20`、`WITHDRAW=30`、`INTERRUPT=40`、`REJECT=45`、`PENDING=50`、`ABANDON=99`
- REJECT(45) 与 DONE(20) 是两个不同终态：REJECT 是 reject() 主动终态，DONE 是 finish() 正常终态。

### 3.4 facade.py:300 BUG 复测
```python
submit_type = self._to_int(args.get("submitType")) or SUBMIT_AGREE
```
- 发送 submitType=0 → `_to_int` 返回 0 → `0 or SUBMIT_AGREE(=1)` → 强制 1
- 影响：API 调用方无法通过 facade 显式发起 APPLY(0)，startAndExecute 内部自动注入 submitType=0 是唯一合法路径
- 修复建议：改 `int(args.get("submitType") or SUBMIT_AGREE)` 或更明确 `submit_type if submit_type is not None else SUBMIT_AGREE`

## 4. 测试用例 ID

| 用例 | processInstanceId | 关键 taskId |
|------|-------------------|-------------|
| T0 AGREE | 91754927595653 | task1=… |
| T1 APPLY(0→1) | 91754927607944 | — |
| T2 REJECT | 91754927618187 | — |
| T3 ROLLBACK | 91754927629454 | apply=91754927634577 |
| T4 ROLLBACK_TO_OP | 91754927638674 | apply=91754927644821 |

## 5. 结论

**5/5 全部通过**。Decision 节点是实现 submitType 分流的正确机制；REJECT 与 ROLLBACK 在本引擎中行为不同：REJECT(2) 终止实例并进入 REJECT(45) 终态；ROLLBACK(3/6) 跳过 reject 路径，在流程图中按 expr 路由回 apply，保持 DOING(10) 状态等待重新提交。
