# BDD #95 综合场景2 (20260918220000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[提交]
    apply --> fork{并行}
    fork --> finance_sign[财务]
    fork --> manager_review[经理]
    finance_sign --> join{汇合}
    manager_review --> join
    join --> amount_decision{金额}
    amount_decision -->|<1万| low_pay[低额付款]
    amount_decision -->|≥1万| high_review[高额复核]
    low_pay --> end([结束])
    high_review --> end
```

## 场景
综合场景2 fork+join+决策路由（财务+经理并行→汇合→金额决策→低额/高额）

## 结果
- memory (8101): ✅ PASS
- pg (8102): ✅ PASS
