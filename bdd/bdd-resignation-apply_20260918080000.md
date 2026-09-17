# BDD #81 bdd-resignation-apply (20260918080000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[提交离职]
    apply --> leader_confirm[直属确认]
    leader_confirm --> hr_approve[HR批准]
    hr_approve --> manager_approve[经理批准]
    manager_approve --> end([结束])
```

## 场景
员工离职申请

## 结果
- memory (8101): ✅ PASS
- pg (8102): ✅ PASS
