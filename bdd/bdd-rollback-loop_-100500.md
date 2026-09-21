# BDD 任务 #113: ROLLBACK 跳回首任务节点

## 目标
测试 `submitType=3 ROLLBACK + taskName=apply` 跳回首任务节点

## 流程
apply → task1 → task2 → end

## 实测
1. startAndExecute (apply 跑完)
2. leader task1 submitType=3 taskName=apply
3. **预期**：apply 重新激活，actor=发起人 user1
4. **实测**：apply state=10 但 actorIds=['leader'] ❌
5. user1 在 todoList 看不到 apply — 流程卡 state=10

## 结论
❌ **§52 仍存 BUG 复现**

## 根因
- `vendor/jeeflow/engine.py:174-200` execute_and_jump_task
- _execute_node(target) → _create_task → _resolve_actors 解析出 ['leader']（前任务完成人）
- 期望 ['user1']（发起人）

## 修复建议
- 修 execute_and_jump_task 跳首任务时显式传 tf_nextNodeOperator=inst.operator
- 或在 _is_first_task_node 检测后改 properties.assignee 时同步修改 vars_

## 优先级
中（submitType=6 可替代）
