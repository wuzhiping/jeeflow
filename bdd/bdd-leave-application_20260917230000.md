# BDD Task 5: 请假申请（bdd-leave-application_20260917230000）

## 流程设计
- 提交请假 (apply, applicant=user1)
- 直接主管审批 (direct_leader, handler=leader)
- 天数决策 (days_decision, 二分支：3-7天/≥7天)
- 经理审批 OR 总经理审批
- HR 备案 (hr_record, handler=director)
- 结束

## SPI 角色
- `direct_leader` = ['leader']
- `manager_approve` = ['manager']
- `boss_approve` = ['boss']
- `hr_record` = ['director']

## 测试场景
- 10 天年假 → 走 boss_approve 分支
- leader → boss → director → end

## 测试结果（双端 PASS）
- memory (8101): leader→boss→director ✅ state=20
- pg (8102): leader→boss→director ✅ state=20
