# 07-countersign-ratio PG 后端覆盖测试

- **测试时间**：2026-09-17 12:42:00
- **后端**：PG
- **关联流程**：`./flows/07-countersign-ratio.json`

## 1. 设计概览

```
start → apply(applicant) → task1(PARALLEL [userA,B,C,D], 2人通过即流转) → end
countersignCompletionCondition: #nrOfCompletedInstances==2
```

## 2. 部署

reset → save → deploy pdid=1789615036473000 ✅

## 3. 启动 + 执行

→ instanceId=91765797371934

执行 userA + userB → 2/4 通过 → state=20

## 4. 校验

```
state=20 (DONE)
  apply  state=20 actorIds=['user1']
  task1  state=20 actorIds=['userA']
  task1  state=20 actorIds=['userB']
  task1  state=99 actorIds=['userC']    ← ABANDON
  task1  state=99 actorIds=['userD']    ← ABANDON
```

✅ 比例条件 2/4 触发 → 剩余 task1 ABANDON (state=99) — 与之前 docs/state.md §5 改进一致

## 5. AGENTS.md §10 自检

- [x] save + deploy code:0
- [x] startAndExecute 返回 processInstanceId
- [x] state==20
- [x] 比例条件正确触发
- [x] 剩余子任务 ABANDON (state=99)
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘
- [x] 环境重置

## 6. 复盘

无新发现。PG 后端 ratio+ABANDON 行为与 sqlite 一致，验证了 `docs/state.md §5` 的改进。

## 7. 结论

✅ **PASS** — 07-countersign-ratio PG 全流程符合设计。
