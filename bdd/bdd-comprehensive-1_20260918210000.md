# BDD #94 bdd-comprehensive-1 (20260918210000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[提交]
    apply --> level_decision{层级}
    level_decision -->|1| low_path[低]
    level_decision -->|2| mid_path[中]
    level_decision -->|3| high_path[高]
    low_path --> end([结束])
    mid_path --> end
    high_path --> end
```

## 场景
三层决策路由（f_level=1）

## 结果
- memory (8101): ✅ PASS
- pg (8102): ✅ PASS
