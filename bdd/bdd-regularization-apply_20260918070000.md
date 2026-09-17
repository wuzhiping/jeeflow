# BDD #80 bdd-regularization-apply (20260918070000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[提交转正]
    apply --> leader_review[直属评价]
    leader_review --> hr_review[HR审查]
    hr_review --> manager_approve[经理批准]
    manager_approve --> end([结束])
```

## 场景
员工转正申请 3 个月

## 结果
- memory (8101): ❌ FAIL
- pg (8102): ❌ FAIL
