# BDD #75 报销审批-会签PARALLEL (20260918020000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[提交报销]
    apply --> leader_review[直属审批]
    leader_review --> finance_sign{财务会签}
    finance_sign --> manager_review[经理审批]
    manager_review --> cashier_pay[出纳付款]
    cashier_pay --> end([结束])
```

## 场景
提交 2000 元报销，leader 直属审批 → 财务会签（leader + manager 并行完成）→ 经理审批 → 出纳付款

## 结果
- memory (8101): ✅ PASS
- pg (8102): ✅ PASS
