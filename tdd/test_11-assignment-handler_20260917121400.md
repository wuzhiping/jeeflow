# 11-assignment-handler 覆盖测试

- **测试时间**：2026-09-17 12:14:00
- **测试类型**：按 docs/AGENTS.md §5 完整流程
- **关联流程**：`./flows/11-assignment-handler.json`
- **关联已知问题**：`./docs/known-issues.md §18`（SPI 修复后已通过）

## 1. 设计概览

```
节点：start → task1(FormFieldAssigneeHandler) → task2(OperatorAssignmentHandler) → task3(DeptLeaderAssignmentHandler) → task4(TaskRoleAssigneeHandler) → end
无 apply 节点：task1 由 FormFieldAssigneeHandler 用 f_task1 字段解析 actor
```

| 节点 | Handler | actor 来源 |
|---|---|---|
| task1 | FormFieldAssigneeHandler | `vars.f_task1="user1"` → user1 |
| task2 | OperatorAssignmentHandler | `inst.operator="user1"` → user1 |
| task3 | DeptLeaderAssignmentHandler | `find_dept_leaders("D01")` → ["leader"] |
| task4 | TaskRoleAssigneeHandler | `find_by_role("task4")` → ["userC"] |

## 2. 部署

reset → save (name=assignment-handler) → deploy → processDefineId=113 ✅

## 3. 启动 + 执行

```bash
curl -X POST /wf/processInstance/startAndExecute -d '{
  "processDefineId": 113, "operator":"user1",
  "assignees":"user1",
  "variables":{"submitType":1, "f_task1":"user1", "f_task2":"user1", "f_task3":"user1",
               "u_userId":"user1", "u_deptId":"D01"}
}'
```

→ instanceId=91765188574133

启动后 task1 自动完成（FormFieldAssigneeHandler 用 f_task1=user1 解析），剩 task2(user1) DOING

执行 user1 → leader → userC，全部 code:0

## 4. 校验

### 4.1 detail

```
state=20 (DONE)  active=0
  task1  state=20 actorIds=['user1']    ← FormFieldAssigneeHandler
  task2  state=20 actorIds=['user1']    ← OperatorAssignmentHandler
  task3  state=20 actorIds=['leader']   ← DeptLeaderAssignmentHandler (D01)
  task4  state=20 actorIds=['userC']    ← TaskRoleAssigneeHandler (role=task4)
```

### 4.2 approvalRecord

```
task1  operator=user1
task2  operator=user1
task3  operator=leader
task4  operator=userC
```

✅ 4/4 handler 全部正确解析 actor

## 5. AGENTS.md §10 自检

- [x] save + deploy code:0
- [x] startAndExecute 返回 processInstanceId
- [x] 走完所有 task，state==20
- [x] approvalRecord 节点顺序符合设计（task1/2/3/4）
- [x] 4 个内置 handler 全部正确解析 actor
- [x] SPI 数据正确加载（task4 role=userC）
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘
- [x] 环境重置

## 6. 复盘

**确认 §18 已修复**：本次 4/4 handler 通过，state=20 DONE，与已知问题 §18 描述「SPI 数据缺失 → task4 卡死」修复后行为一致。

无新发现。task1 自动执行（FormFieldAssigneeHandler）后剩 task2，runner actor 序列应跳过 task1。

## 7. 结论

✅ **PASS** — 11-assignment-handler 全流程符合设计，4/4 handler 正确解析。
