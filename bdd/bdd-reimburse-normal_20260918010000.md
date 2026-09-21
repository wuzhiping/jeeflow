# BDD #74 报销审批-普通模式 (20260918010000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[提交报销]
    apply --> leader_review[直属领导]
    leader_review --> decision{金额<3千?}
    decision -->|是| manager_review[经理审批]
    decision -->|否| boss_review[总经理审批]
    manager_review --> cashier_pay[出纳付款]
    boss_review --> cashier_pay
    cashier_pay --> end([结束])
```

## 场景
提交办公用品报销 1500 元（<3千 → manager 分支），完整 7 节点流程

## 结果
- memory (8101): ✅ PASS
- pg (8102): ✅ PASS

## 流程最终状态
- memory: state=20
- pg: state=20
