# BDD #148 混合会签（fork/join + PARALLEL ALL + ONE_VOTE_VETO + SEQUENTIAL）(20260919 181000)

## 流程设计

```mermaid
flowchart TD
    start([开始]) --> apply[申请人]
    apply --> fork1{分支}
    fork1 --> parallel[并行会签<br/>userA,B,C]
    fork1 --> veto[一票否决<br/>leader,manager,director]
    parallel --> join1[汇合]
    veto --> join1
    join1 --> seq[串行会签<br/>user1→userA→userB]
    seq --> boss[总经理]
    boss --> end([结束])
```

## 测试用例

### Case 1: 全部同意
| 步骤 | 操作 | 节点 | 状态 |
|------|------|------|------|
| 1 | startAndExecute | apply → fork1 → 2 branches | ✓ |
| 2 | userA/B/C 同意 | parallel 完成 (3/3) | ✓ |
| 3 | leader/manager/director 同意 | veto 完成 (3/3) | ✓ |
| 4 | join1 汇合 | 进入 seq_review | ✓ |
| 5 | user1 → userA → userB | 串行会签 | ✓ |
| 6 | boss 同意 | state=20 DONE | ✓ |

### Case 2: 一票否决 (leader REJECT submitType=20)
**修复前**：
- instance state = 45 ✓
- veto_review: leader=20, manager/director=99 ✓
- **parallel_review: 仍 state=10 DOING** ❌
- userA/B/C todo 仍可见 ❌

**修复后**（FIX-T47 2026-09-19）：
- instance state = 45 ✓
- veto_review: leader=20, manager/director=99 ✓
- **parallel_review: 全部 state=99 ABANDONED** ✓
- userA/B/C todo 全部清空 ✓

## 🐛 BUG #148 + 修复

### Bug: 一票否决只清本节点 DOING，未清整个 instance 的 DOING
- 位置：`vendor/jeeflow/engine.py:execute_process_task:161-166`
- 原代码：`remaining = await self.repo.find_doing_tasks(inst.id, [cur_node.id])` 限定本节点
- 现象：fork 出来的其他分支 task 仍 state=10 DOING，用户 todoList 仍可见
- 影响：与"instance 已 REJECT"语义矛盾

### 修复（FIX-T47 2026-09-19）
```python
if cs_veto:
    # ...
    # BDD #148 FIX-T47：废弃 instance 全部 DOING 任务
    all_remaining = await self.repo.find_doing_tasks(inst.id)  # 无 task_names 限制
    for t in all_remaining:
        t.taskState = TaskState.ABANDONED
        t.updateTime = now
        t.updateUser = operator
        await self.repo.update_task(t)
        _sync_task_to_aggregate(inst, t)
    await self.repo.update_instance(inst)
```

## 验证

| 字段 | 修复前 | 修复后 |
|------|--------|--------|
| inst.state | 45 | 45 ✓ |
| parallel_review task state | 10 | 99 ✓ |
| userA todo count | 1 | 0 ✓ |
| userB todo count | 1 | 0 ✓ |
| userC todo count | 1 | 0 ✓ |

## 结果
- memory (8101): ✅ PASS
