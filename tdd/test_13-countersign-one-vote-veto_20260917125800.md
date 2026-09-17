# 13-countersign-one-vote-veto PG 后端覆盖测试

- **测试时间**：2026-09-17 12:58:00
- **后端**：PG
- **关联流程**：`./flows/13-countersign-one-vote-veto.json`

## 1. 设计概览

```
start → apply(applicant) → task1(PARALLEL [userA,userB,userC], ONE_VOTE_VETO) → end
```

## 2. 部署

reset → save → deploy pdid=1789615443734000 ✅

## 3. 启动 + 执行

→ instanceId=91766214405186

执行 userA DISAGREE (submitType=20) → code:0 → ONE_VOTE_VETO 触发

## 4. 校验

```
state=20 (DONE)
  apply  state=20
  task1  state=20           ← userA DISAGREE 完成
  task1  state=99           ← ABANDON (userB)
  task1  state=99           ← ABANDON (userC)
```

✅ ONE_VOTE_VETO 行为正确：任意 DISAGREE 立即流转 + 剩余 ABANDON

## 5. AGENTS.md §10 自检

- [x] save + deploy code:0
- [x] startAndExecute 返回 processInstanceId
- [x] state==20
- [x] ONE_VOTE_VETO 字符串条件正确识别
- [x] 剩余子任务 ABANDON (state=99)
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘
- [x] 环境重置

## 6. 复盘

无新发现。PG 后端 ONE_VOTE_VETO + ABANDON 行为与 sqlite 一致。

## 7. 结论

✅ **PASS** — 13-one-vote-veto PG 全流程符合设计。
