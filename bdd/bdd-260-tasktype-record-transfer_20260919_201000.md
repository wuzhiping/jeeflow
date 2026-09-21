# BDD #260: taskType=2 RECORD 自动完成 + FIX-T55

**时间**: 2026-09-19 20:10
**状态**: ✅ PASS
**章节**: §94 补充 (FIX-T55)
**BUG 发现**: taskType=2/3 引擎不识别

## 背景

taskType 字段定义（FIX-T30 2026-09-18 透传）：
- 0 = 主审（DEFAULT）
- 1 = 副审（SECONDARY, §94 已验证）
- 2 = 记录（RECORD, 设计意图：自动跳过，不需人办）
- 3 = 转交（TRANSFER, 设计意图：流程内转交）

引擎现状：
- 仅落库 taskType 字段
- 不识别 2/3，按主审处理
- 流程卡在 RECORD 节点等 actor 提交

## 测试结果

### Before FIX-T55
| 场景 | 期望 | 实际 |
|------|------|------|
| RECORD 节点自动完成 | active=leader | ❌ active=[record] 卡住 |
| TRANSFER 节点 | 任意 actor 可办 | ✅ (因引擎不区分，按普通 task) |

### After FIX-T55
| 场景 | 期望 | 实际 |
|------|------|------|
| RECORD 自动完成 + 推进 | active=leader, record=state=20 | ✅ |
| 普通 taskType=0 | active=leader 等办 | ✅ |
| TRANSFER (taskType=3) | 按普通 task 处理（保留设计余地） | ✅ |

## FIX-T55 实现

`vendor/jeeflow/engine.py`:

1. `_create_task` 末尾加：
```python
if task_type == 2:
    nt.taskState = TaskState.DONE
    nt.finishTime = now
    await self.repo.update_task(nt)
    await self._fire_event(ProcessEvent(EventType.TASK_COMPLETE, inst.id, nt.id, node.id, operator))
    self._last_created_record_done = True
```

2. `_execute_node` 末尾加：
```python
if getattr(self, "_last_created_record_done", False):
    for n in _follow_edges(flow, node.id):
        await self._execute_node(flow, inst, n, operator, vars_)
```

## 设计决策

- **taskType=2 RECORD**：立即置 DONE + 推进下游（自动留痕）
- **taskType=3 TRANSFER**：暂不实现特殊语义（保留作 future work）
  - 设计可能：把当前任务转给他人，类似 _processTask_transfer 但在节点层
  - 当前用 addCandidate/transfer endpoint 替代

## 累计

- BDD 任务: 260
- 修复 BUG: 55 (FIX-T1~T55)
- verify 规则: 24
