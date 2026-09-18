# BDD 任务 #118: taskType=1 SECONDARY 副审

## 目标
验证 FIX-T30 修复后 taskType=1 副审节点落库 taskType=1

## 流程
apply → secondary_review(taskType=1) → end

## 实测
- apply taskType=0
- secondary_review taskType=1 ✓

## 结论
✅ **PASS**：FIX-T30 (2026-09-18 §83) 修复后 taskType 透传正常工作

## 引擎行为
- `vendor/jeeflow/engine.py:411-419` 读 node.properties.taskType
- `vendor/jeeflow/model.py:185` create_task 加 task_type 参数
- 内存版 _task_row + PG 版 _map_task_row 都透传字段
