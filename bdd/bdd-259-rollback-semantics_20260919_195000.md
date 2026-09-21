# BDD #259: ROLLBACK 多种 sub-语义 + FIX-T54

**时间**: 2026-09-19 19:50
**状态**: ✅ PASS
**章节**: §99 补充 (FIX-T54)
**BUG 发现**: ROLLBACK 不支持 targetTaskName 参数

## BUG 描述

facade._processTask_execute 路由：
```python
elif submit_type == SUBMIT_ROLLBACK:
    await self._engine.execute_and_jump_task(task_id, operator, flow_args)
```

**问题**：
- 不读 `targetTaskName` 参数
- 即便客户端传了，也被忽略
- 行为总是"退上一节点"（Snaker/Java 默认）
- target=ghost 没 raise（应与 JUMP 一致）

## FIX-T54 (2026-09-19)

```python
elif submit_type == SUBMIT_ROLLBACK:
    # FIX-T54：ROLLBACK 也支持 targetTaskName
    target = str(args.get("taskName") or args.get("targetTaskName") or "")
    await self._engine.execute_and_jump_task(task_id, operator, flow_args, target)
```

**语义**：
- 有 targetTaskName → 跳指定节点（与 JUMP 一致）
- 无 targetTaskName → 退回上一任务节点（Snaker/Java 默认，向后兼容）

## 测试结果

| 场景 | 输入 | 期望 | 实际 |
|------|------|------|------|
| 1. 退上一节点 | no target | active=[apply] | ✅ active=[apply] |
| 2. 跳首任务 | targetTaskName=apply | active=[apply] | ✅ active=[apply] |
| 3. 节点不存在 | targetTaskName=ghost | raise | ✅ raise ValueError |

## 引擎行为（已存在）

`engine.execute_and_jump_task` 已有完整逻辑：
- 找到 target 节点
- 校验 type
- 首任务节点 actor 强制为 inst.operator（§99 FIX-T36 修复）
- 走 `_execute_node` 复用 §27 FIX-T35 悲观锁

## 累计

- BDD 任务: 259
- 修复 BUG: 54 (FIX-T1~T54)
