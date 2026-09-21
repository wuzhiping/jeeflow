# BDD Task 4: 合同审批（bdd-contract-approval_20260917220000）

## 流程设计
- 提交合同 (apply, applicant=user1)
- 法务初审 (legal_review, handler=director)
- 金额决策 (amount_decision, 三分支：<5万/5-50万/>=50万)
- 部门审批 OR 公司审批 OR 董事会审批
- 合同签订会签 (sign_contract, PARALLEL)
- 结束

## SPI 角色
- `legal_review` = ['director']
- `dept_approve` = ['leader']
- `company_approve` = ['manager']
- `board_approve` = ['boss']
- `sign_contract` = ['director', 'boss']

## 测试场景
- 80 万元合同 → 走 board_approve 分支
- director 法务 → boss 董事会 → director+boss 会签

## 测试结果（双端 PASS）
- memory (8101): director→boss→director+boss ✅ state=20
- pg (8102): director→boss→director+boss ✅ state=20
