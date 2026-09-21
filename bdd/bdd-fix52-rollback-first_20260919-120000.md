# BDD 任务 #124: §52 ROLLBACK 跳首任务 actor 错位修复

## 目标
验证 ROLLBACK 跳首任务节点时 actor 正确为发起人（修复前为前任务完成人）

## 流程
start1 → apply(user1) → task1(leader) → end1

## 修复前
- leader task1 submitType=3 ROLLBACK
- apply 被重新激活，actorIds=['leader']（应为 ['user1']）
- user1 todoList 看不到 apply → 流程卡 state=10

## 根因
- `engine.py:184-185` ROLLBACK 路径调 `_rollback_actors` + `_create_task_with_actors`
- `_rollback_actors` 返回 `[task.actorId]` = ['leader']（前任务完成人）
- 复用 Java rejectTask 语义，**与"跳首任务"场景错位**

## 修复（FIX-T36 2026-09-19）
`engine.py:177-195` `execute_and_jump_task` ROLLBACK 路径：
- 检测目标节点是否首任务（`_is_first_task_node`）
- 首任务：`prev.properties["assignee"] = inst.operator`（发起人）
- 非首任务：`prev.properties["assignee"] = task.actorId or operator`（前任务完成人，保留 Java 语义）
- 走 `_execute_node` 替代 `_create_task_with_actors`
- 触发 §27 FIX-T35 修复（悲观锁+去重）

## 实测
1. ROLLBACK 跳首任务：user1 apply todo = 1 ✓
2. ROLLBACK 跳非首任务：leader task0 todo = 1（保留 Java 语义）✓
3. JUMP 跳首任务：user1 apply todo = 1（无回归）✓
4. ROLLBACK_TO_OPERATOR (submitType=6)：user1 apply todo = 1 ✓
5. 完整跑通：state=20 DONE ✓

## 改动
- `vendor/jeeflow/engine.py` `execute_and_jump_task` ROLLBACK 路径 +8 行
- 移除 `_rollback_actors` + `_create_task_with_actors` 直接调用

## 结论
✅ **PASS**：§52 ROLLBACK 跳首任务 actor 错位修复
