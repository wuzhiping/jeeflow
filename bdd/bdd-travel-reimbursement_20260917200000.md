# BDD Task 2: 差旅报销审批（bdd-travel-reimbursement_20260917200000）

## 流程设计
- 提交报销 (apply, applicant=user1)
- 部门审批 (dept_approve, assignee=leader)
- 财务初审会签 (finance_check, assignmentHandler=TaskRoleAssigneeHandler, PARALLEL)
- 费用分类决策 (category_decision, f_travelType=='domestic' && f_amount<30000)
- 经理审批 (manager_approve, handler) OR 总经理审批 (boss_approve, handler)
- 财务终审会签 (finance_final, handler, PARALLEL)
- 出纳付款 (cashier_pay, handler)
- 结束

## SPI 角色
- `finance_check` = `finance_final` = ['leader', 'manager']
- `manager_approve` = ['manager']
- `boss_approve` = ['boss']
- `cashier_pay` = ['cashier']（新增 cashier 用户，post='出纳'）

## 测试场景
- 提交北京出差 2万元（国内 <3万）
- 走 category_decision → manager_approve 分支

## 测试结果（双端 PASS）
- memory (8101): leader→leader→manager→manager→leader→manager→cashier ✅ state=20
- pg (8102): leader→leader→manager→manager→leader→manager→cashier ✅ state=20

## 关键修复
1. JSON key 与 node.id 一致：handler 节点 properties 没设 roleCode 时 fallback 用 node.id
2. 新增用户必须在 DEMO_USERS.json 含 post 字段（get_user SPI 依赖 info['post']）
3. cashier_pay 是 handler 节点（非 assignment 字段）— 需要 properties.assignmentHandler
