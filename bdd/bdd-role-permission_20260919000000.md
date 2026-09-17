# BDD #97 bdd-role-permission (20260919000000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[提交]
    apply --> dept_leader[部门领导]
    dept_leader --> hr_review[HR审查]
    hr_review --> end([结束])
```

## 场景
角色权限测试

## 结果
- memory (8101): ✅ PASS
- pg (8102): ✅ PASS
