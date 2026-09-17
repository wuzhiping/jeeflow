# BDD Task 3: 用车申请审批（bdd-vehicle-request_20260917210000）

## 流程设计
- 提交用车申请 (apply, applicant=user1)
- 车队派车 (fleet_dispatch, handler=manager)
- FORK（并行）:
  - 司机确认 (driver_confirm, handler=userA/userB)
  - 用车人确认 (user_confirm, handler=userC)
- JOIN（汇合）
- 行程结束 (trip_finish, handler=user1)
- 用车评价 (rate, handler=user1)
- 结束

## SPI 角色
- `fleet_dispatch` = ['manager']
- `driver_confirm` = ['userA', 'userB']（任一司机）
- `user_confirm` = ['userC']
- `trip_finish` = `rate` = ['user1']

## 测试场景
- 接客户去机场，3 乘客，14:00 出发，指定司机 userA

## 测试结果（双端 PASS）
- memory (8101): manager→(userA + userC 并行)→user1→user1 ✅ state=20
- pg (8102): manager→(userA + userC 并行)→user1→user1 ✅ state=20
- **fork/join 完美工作**：driver_confirm 和 user_confirm 同时进行，都完成后 join 推进
