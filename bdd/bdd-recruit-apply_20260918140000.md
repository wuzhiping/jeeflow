# BDD #87 bdd-recruit-apply (20260918140000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[提交招聘]
    apply --> recruit_leader[直属]
    recruit_leader --> recruit_hr[HR]
    recruit_hr --> recruit_boss[总经理]
    recruit_boss --> end([结束])
```

## 场景
招聘前端工程师 2 人

## 结果
- memory (8101): ✅ PASS
- pg (8102): ✅ PASS
