# 06-countersign-sequential 覆盖测试（按 AGENTS.md §5 全流程）

- **测试时间**：2026-09-17 12:00:00
- **测试类型**：按 docs/AGENTS.md §5 完整流程
- **关联流程**：`./flows/06-countersign-sequential.json`

## 1. 设计概览

```
节点：start → apply(applicant) → task1(SEQUENTIAL [userA,userB]) → end
会签配置：performType=1, countersignType=SEQUENTIAL, assignee="userA,userB"
```

## 2. 部署（§5.3）

reset → save → deploy → processDefineId=113 ✅

## 3. 启动 + 执行（§5.4-§5.5）

→ instanceId=91764857514236

启动后 active=1（仅 userA 一个 task1，与 SEQUENTIAL 语义一致）：
- task1(userA) DOING

执行：userA → userB，全部 code:0

## 4. 校验（§5.6）

### 4.1 detail

```
state=20 (DONE)  active=0
  apply  state=20 actorIds=['user1']
  task1  state=20 actorIds=['userA']
  task1  state=20 actorIds=['userB']
```

### 4.2 approvalRecord

```
apply  operator=user1
task1  operator=userA
task1  operator=userB
```

✅ SEQUENTIAL：userA 完成 → userB 才开始 → userB 完成 → state=20

## 5. AGENTS.md §10 自检

- [x] §5.3 save + deploy code:0
- [x] §5.4 startAndExecute 返回 processInstanceId
- [x] §5.5 走完所有 task，state==20
- [x] §5.6 approvalRecord 顺序符合 SEQUENTIAL 设计
- [x] §5.6 activeTaskList 启动时只有 1 个 task（userA），符合 SEQUENTIAL
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘
- [x] 环境重置

## 6. 复盘

无新发现。SEQUENTIAL 行为符合设计：
- 启动时只创建 userA 一个 task1 实例
- userA 完成后创建 userB 的 task1 实例
- userB 完成后流转到 end

## 7. 结论

✅ **PASS** — 06-countersign-sequential 全流程符合设计。
