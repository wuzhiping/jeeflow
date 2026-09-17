# 11-assignment-handler PG 后端覆盖测试

- **测试时间**：2026-09-17 12:54:00
- **后端**：PG
- **关联流程**：`./flows/11-assignment-handler.json`

## 1. 设计概览

4 个 task 节点，4 个内置 handler：
- task1: FormFieldAssigneeHandler → f_task1=user1
- task2: OperatorAssignmentHandler → inst.operator=user1
- task3: DeptLeaderAssignmentHandler → find_dept_leaders("D01") → [leader]
- task4: TaskRoleAssigneeHandler → find_by_role("task4") → [userC]

## 2. 部署

reset → save → deploy pdid=1789615394192000 ✅

## 3. 启动 + 执行

→ instanceId=91766163676218

执行 user1 → leader → userC，全部 code=0

## 4. 校验

```
state=20 (DONE)
  task1  state=20 actorIds=['user1']
  task2  state=20 actorIds=['user1']
  task3  state=20 actorIds=['leader']
  task4  state=20 actorIds=['userC']
```

✅ 4/4 handler 全部正确解析 actor

## 5. AGENTS.md §10 自检

- [x] save + deploy code:0
- [x] startAndExecute 返回 processInstanceId
- [x] state==20
- [x] 4 handler 正确解析
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘
- [x] 环境重置

## 6. 复盘

无新发现。PG 后端 4 个内置 handler 行为与 sqlite 完全一致。

## 7. 结论

✅ **PASS** — 11-assignment-handler PG 全流程符合设计。
