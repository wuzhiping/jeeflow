# BDD #105 bdd-deploy-release (20260919050400)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> submit[提交发布]
    submit --> fork{并行}
    fork --> code_review{{代码评审}}
    fork --> tester_smoke[测试冒烟]
    code_review --> join{汇合}
    tester_smoke --> join
    join --> deploy_approve[部署审批]
    deploy_approve --> end([结束])
```

## 场景
并行：代码评审+测试冒烟→汇合→部署审批

## 数据源
`SPI_FOLDER=fdep` — 6 个研发用户 (dev01-dev06) + 4 个核心角色 (developer/tester/architect/tech_lead) + 3 个 SPI 节点角色 (cto/code_review/deploy_approve)

## 启动参数
```json
{
  "operator": "dev01",
  "title": "部署上线-v2.1.0",
  "assignees": {
    "submit": "dev01"
  },
  "variables": {
    "submitType": 0,
    "u_userId": "dev01",
    "u_realName": "陈伟",
    "f_release_version": "v2.1.0",
    "f_env": "production"
  }
}
```

## 步骤结果
- dev04: code_review (PASS)
- dev05: code_review (PASS)
- dev03: tester_smoke (PASS)
- dev05: deploy_approve (PASS)

## 结果
- memory (8101): ✅ PASS
- pg (8102): ✅ PASS
