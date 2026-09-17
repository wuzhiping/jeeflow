# 07-countersign-ratio 覆盖测试（按 AGENTS.md §5 全流程）

- **测试时间**：2026-09-17 12:02:00
- **测试类型**：按 docs/AGENTS.md §5 完整流程
- **关联流程**：`./flows/07-countersign-ratio.json`

## 1. 设计概览

```
节点：start → apply(applicant) → task1(PARALLEL [userA,B,C,D], 2人通过即流转) → end
会签配置：performType=1, countersignType=PARALLEL,
         field.countersignCompletionCondition="#nrOfCompletedInstances==2"
assignee="userA,userB,userC,userD"
```

## 2. 部署（§5.3）

reset → save → deploy → processDefineId=113 ✅

## 3. 启动 + 执行（§5.4-§5.5）

→ instanceId=91764885879135

启动后并行 active=4：
- task1(userA/B/C/D) DOING

执行 userA → userB，2 人通过 → 立即流转到 end

## 4. 校验（§5.6）

### 4.1 detail

```
state=20 (DONE)  active=0
  apply  state=20 actorIds=['user1']
  task1  state=20 actorIds=['userA']
  task1  state=20 actorIds=['userB']
  task1  state=99 actorIds=['userC']    ← ⚠️ ABANDON
  task1  state=99 actorIds=['userD']    ← ⚠️ ABANDON
```

### 4.2 approvalRecord

```
apply  operator=user1
task1  operator=userA
task1  operator=userB
task1  operator=                       ← 空（ABANDON task）
task1  operator=                       ← 空（ABANDON task）
```

### 4.3 highLight

```
history=['apply', 'task1', 'end']  active=[]
```

✅ 比例会签 2/4 通过后 state=20，剩余 2 子任务 ABANDONED（state=99）

## 5. AGENTS.md §10 自检

- [x] §5.3 save + deploy code:0
- [x] §5.4 startAndExecute 返回 processInstanceId
- [x] §5.5 走完所有 task，state==20
- [x] §5.6 approvalRecord 节点顺序符合设计
- [x] §5.6 比例条件 `#nrOfCompletedInstances==2` 正确触发
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘
- [x] 环境重置

## 6. 复盘

### 6.1 新发现：TaskState=99 ABANDON

**现象**：比例会签满足完成条件后，未完成的子任务被设为 `taskState=99`，且 `approvalRecord` 中 `operator` 为空。

**改进 docs/state.md §5**：

补充 `taskState=99 (ABANDON)` 枚举值，并注明 2026-09-17 07-countersign-ratio 实测来源。改动见 docs/state.md §5。

### 6.2 已知引擎行为

`RatioCapableEngine.execute_process_task`（docs/known-issues.md §7 已记录）会在条件满足时：
1. 完成当前 task（`super().execute_process_task`）
2. 检查条件
3. 流转到下一节点
4. **将所有 doing 状态的会签子任务设为 ABANDON**

这是 RatioCapableEngine 扩展的预期行为，**不视为 bug**。

## 7. 结论

✅ **PASS** — 07-countersign-ratio 全流程符合设计，比例条件正确触发，子任务 ABANDON 行为已记录。

## 8. docs 改动

- `./docs/state.md §5`：补 `TaskState=99 ABANDON` 枚举 + 实测来源
