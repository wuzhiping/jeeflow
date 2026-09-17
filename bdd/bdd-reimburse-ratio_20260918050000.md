# BDD #78 bdd-reimburse-ratio (20260918050000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[提交报销]
    apply --> finance_ratio{{财务比例会签2/3}}
    finance_ratio --> cashier_pay[出纳付款]
    cashier_pay --> end([结束])
```

## 场景
3人会签 2/3 通过，leader+manager 完成即可推进

## 结果
- memory (8101): ❌ FAIL
- pg (8102): ❌ FAIL
