# BDD #100 大综合流程 (20260919030000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[提交]
    apply --> leader_review[直属]
    leader_review --> type_decision{类型}
    type_decision -->|B| type_b[类型B]
    type_b --> finance_sign[财务]
    finance_sign --> manager_review[经理]
    manager_review --> cashier_pay[出纳]
    cashier_pay --> end([结束])
```

## 场景
大综合流程：决策+handler 7 节点（决策路由类型B→财务→经理→出纳）

## 结果
- memory (8101): ✅ PASS
- pg (8102): ✅ PASS
