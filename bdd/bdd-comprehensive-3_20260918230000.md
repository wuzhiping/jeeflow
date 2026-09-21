# BDD #96 bdd-comprehensive-3 (20260918230000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[提交]
    apply --> step1[步骤1]
    step1 --> step2[步骤2]
    step2 --> step3[步骤3]
    step3 --> step4[步骤4]
    step4 --> step5[步骤5]
    step5 --> end([结束])
```

## 场景
5 个 handler 节点串行

## 结果
- memory (8101): ❌ FAIL
- pg (8102): ❌ FAIL
