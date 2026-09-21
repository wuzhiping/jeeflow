# BDD #138 加签 / 减签 (20260919 165000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[申请]
    apply --> review[主管 leader]
    review --> end([结束])
```

## 场景
- addCandidate: 给 task 加新 actor
- removeCandidate: 减 actor

## 测试结果

| 用例 | 期望 | 实测 | 结论 |
|------|------|------|------|
| addCandidate userA | 成功 | 成功 | ✅ |
| userA todoList (加签后) | 1 条 | 1 条 | ✅ |
| removeCandidate userA | 成功 | 成功 | ✅ (FIX-T40 修复后) |
| userA todoList (减签后) | 0 条 | 0 条 | ✅ |

## 🐛 BUG 发现 + 修复

### Bug: `_processTask_removeCandidate` 端点未注册

**现象**：
```
[未知 action: processTask/removeCandidate]
```

**根因**：facade.py 实现了 `_taskAddActor`（共用于 addCandidate / surrogate），
但 `_processTask_removeCandidate` 方法未注册到 action 路由表。
底层 `repo.remove_task_actor` 已存在（spiral.py + base.py + memory.py），
但 facade 缺转发。

**修复（FIX-T40 2026-09-19）**：
- `vendor/jeeflow/facade.py:_processTask_removeCandidate` 新增方法
- 调 `self._repo.remove_task_actor(task_id, actor_ids)`
- 异常处理：缺 processTaskId/actorIds 抛 ValueError

## 结果
- memory (8101): ✅ PASS
- pg (8102): ⏭️ 暂未跑
