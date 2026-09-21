# BDD-DEV-014 dev-task-type-mixed (20260921231000)

## 流程设计

```mermaid
flowchart LR
    start([开始]) --> apply[提交<br/>taskType=0]
    apply --> main_review[主审<br/>u_be_lead<br/>taskType=0]
    apply --> assist_review[副审<br/>u_arch<br/>taskType=1]
    main_review --> join1{join1}
    assist_review --> join1
    join1 --> record_node[自动记录<br/>u_rd_dir<br/>taskType=2 RECORD]
    record_node --> end([结束])
```

## 场景

任务类型混合演示：apply + 主审 + 副审 + 自动记录。

## 用到的能力

- fork 显式定义（apply 同时 fork 到 main_review + assist_review）
- `taskType=0` (主审) + `taskType=1` (副审) + `taskType=2` (RECORD 自动完成) 混合
- join 节点汇合后 RECORD 节点自动完成

## 校验

| 节点 | taskType | 期望行为 | 实际 |
|---|---|---|---|
| apply | 0 | actor 处理 | ✅ u_be_eng |
| main_review | 0 | actor 处理 | ✅ u_be_lead |
| assist_review | 1 | actor 处理 | ✅ u_arch |
| record_node | 2 | 自动完成 (operator="") | ✅ operator="" |

## 引擎行为 (FIX-T30 + FIX-T55)

- `taskType=2` RECORD 节点创建后立即 taskState=20 DONE + finishTime=now (BDD #260 FIX-T55 2026-09-19)
- 引擎透传 `node.properties.taskType` 字段 (FIX-T30 §3.3 2026-09-18)
- 触发 `_follow_edges` 推进下游节点

## 结果

- memory (8101): ✅ **PASS**（3 种 taskType 混合）
- pg (8102): skipped