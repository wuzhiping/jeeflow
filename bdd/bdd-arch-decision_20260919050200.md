# BDD #103 bdd-arch-decision (20260919050200)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> submit[提交议题]
    submit --> architect_review[架构师评审]
    architect_review --> cto_approve[CTO批准]
    cto_approve --> end([结束])
```

## 场景
架构师评审→CTO批准

## 数据源
`SPI_FOLDER=fdep` — 6 个研发用户 (dev01-dev06) + 4 个核心角色 (developer/tester/architect/tech_lead) + 3 个 SPI 节点角色 (cto/code_review/deploy_approve)

## 启动参数
```json
{
  "operator": "dev04",
  "title": "架构决策-微服务拆分",
  "assignees": {
    "submit": "dev04"
  },
  "variables": {
    "submitType": 0,
    "u_userId": "dev04",
    "u_realName": "徐静",
    "f_decision_topic": "微服务拆分方案",
    "f_impact": "高"
  }
}
```

## 步骤结果
- dev04: architect_review (PASS)
- dev06: cto_approve (PASS)

## 结果
- memory (8101): ✅ PASS
- pg (8102): ✅ PASS
