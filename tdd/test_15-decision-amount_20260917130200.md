# 15-decision-amount PG 后端覆盖测试

- **测试时间**：2026-09-17 13:02:00
- **后端**：PG
- **关联流程**：`./flows/15-decision-amount.json`

## 1. 设计概览

```
start → apply(user1) → decision1 → {task1(user2) [amount>=10000] | end}
```

## 2. 部署

reset → save → deploy pdid=1789615493800000 ✅

## 3. 启动（双分支）

### Test A: amount=500 (<10000 → end)

→ instanceId=91766265672781 → state=20（task1 未创建）

### Test B: amount=15000 (>=10000 → task1)

→ instanceId=91766266302543 → 执行 user2 → state=20

## 4. 校验

| 测试 | amount | state | 行为 |
|---|---|---|---|
| A | 500 | 20 | decision→end ✅ |
| B | 15000 | 20 | decision→task1(user2) ✅ |

## 5. AGENTS.md §10 自检

- [x] save + deploy code:0
- [x] startAndExecute 返回 processInstanceId（2 次）
- [x] state==20（两条分支）
- [x] decision expr 正确路由
- [x] amount 顶层传递（Issue D 修复）
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘
- [x] 环境重置

## 6. 复盘

无新发现。PG 后端 decision 行为与 sqlite 一致。

## 7. 结论

✅ **PASS** — 15-decision-amount PG 双分支符合设计。
