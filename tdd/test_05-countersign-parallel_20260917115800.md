# 05-countersign-parallel 覆盖测试（按 AGENTS.md §5 全流程）

- **测试时间**：2026-09-17 11:58:00
- **测试类型**：按 docs/AGENTS.md §5 完整流程
- **关联流程**：`./flows/05-countersign-parallel.json`

## 1. 设计概览

```
节点：start → apply(applicant) → task1(PARALLEL [userA,userB,userC]) → end
边：start→apply, apply→task1, task1→end
会签配置：performType=1, countersignType=PARALLEL, assignee="userA,userB,userC"
```

## 2. 部署（§5.3）

reset → save → deploy → processDefineId=113 ✅

## 3. 启动 + 执行（§5.4-§5.5）

→ instanceId=91764826799256

启动后并行 active=3（每个 assignee 一个 task1 实例）：
- task1(userA) DOING
- task1(userB) DOING
- task1(userC) DOING

执行顺序 userA → userB → userC，全部 code:0

## 4. 校验（§5.6）

### 4.1 detail

```
state=20 (DONE)  active=0
  apply  state=20 actorIds=['user1']
  task1  state=20 actorIds=['userA']
  task1  state=20 actorIds=['userB']
  task1  state=20 actorIds=['userC']
```

### 4.2 approvalRecord

```
apply  operator=user1
task1  operator=userA
task1  operator=userB
task1  operator=userC
```

✅ PARALLEL 全员通过才流转（与 AGENTS.md §5.8 表注一致：实测**全员通过才流转**）

## 5. AGENTS.md §10 自检

- [x] §5.3 save + deploy code:0
- [x] §5.4 startAndExecute 返回 processInstanceId
- [x] §5.5 走完所有 task，state==20
- [x] §5.6 approvalRecord 节点顺序符合设计（3 个 task1 + apply）
- [x] §5.6 PARALLEL 全员通过后 state=20
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘
- [x] 环境重置

## 6. 复盘

无新发现。PARALLEL 行为符合 AGENTS.md §5.8 修正：
- "原表写 PARALLEL '任一通过即流转'，实测**全员通过才流转**"
- 3 个 userA/B/C 顺序执行后 state=20

## 7. 结论

✅ **PASS** — 05-countersign-parallel 全流程符合设计。
