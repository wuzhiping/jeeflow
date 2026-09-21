# BDD #98 bdd-variable-pass (20260919010000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[提交变量]
    apply --> step1[接收]
    step1 --> step2[传递]
    step2 --> end([结束])
```

## 场景
变量在节点间传递

## 结果
- memory (8101): ❌ FAIL
- pg (8102): ❌ FAIL
