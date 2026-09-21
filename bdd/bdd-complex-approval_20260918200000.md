# BDD #93 bdd-complex-approval (20260918200000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[提交]
    apply --> leader_review[直属]
    leader_review --> fork{并行}
    fork --> finance_sign{{财务会签}}
    fork --> manager_approve[经理]
    finance_sign --> join{汇合}
    manager_approve --> join
    join --> type_decision{类型}
    type_decision -->|项目| boss_approve[总经理]
    type_decision -->|报销| cashier_pay[出纳]
    boss_approve --> end([结束])
    cashier_pay --> end
```

## 场景
复杂审批 5 种能力 fork+join+decision+cs+handler

## 结果
- memory (8101): ❌ FAIL
- pg (8102): ❌ FAIL
