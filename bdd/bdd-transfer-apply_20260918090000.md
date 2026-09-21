# BDD #82 bdd-transfer-apply (20260918090000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[提交调岗]
    apply --> old_leader_approve[原部门]
    old_leader_approve --> new_leader_approve[新部门]
    new_leader_approve --> hr_review[HR审核]
    hr_review --> manager_approve[经理]
    manager_approve --> end([结束])
```

## 场景
员工调岗申请 跨部门

## 结果
- memory (8101): ❌ FAIL
- pg (8102): ❌ FAIL
