# BDD #79 bdd-overtime-apply (20260918060000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[提交加班]
    apply --> leader_approve[直属]
    leader_approve --> decision{时长<4h?}
    decision -->|是| manager_approve[经理]
    decision -->|否| boss_approve[总经理]
    manager_approve --> hr_record[HR记录]
    boss_approve --> hr_record
    hr_record --> end([结束])
```

## 场景
加班 2 小时（<4h 走经理审批）

## 结果
- memory (8101): ✅ PASS
- pg (8102): ✅ PASS
