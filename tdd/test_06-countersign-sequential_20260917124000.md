# 06-countersign-sequential PG 后端覆盖测试

- **测试时间**：2026-09-17 12:40:00
- **后端**：PG
- **关联流程**：`./flows/06-countersign-sequential.json`

## 1. 设计概览

```
start → apply(applicant) → task1(SEQUENTIAL [userA,userB]) → end
```

## 2. 部署

reset → save → deploy pdid=1789615014460000 ✅

## 3. 启动 + 执行

→ instanceId=91765774829594

启动 active=1 (userA) → execute → active=1 (userB) → execute → state=20

## 4. 校验

```
state=20 (DONE)
  apply  state=20
  task1  state=20
  task1  state=20
```

## 5. AGENTS.md §10 自检

- [x] save + deploy code:0
- [x] startAndExecute 返回 processInstanceId
- [x] state==20
- [x] SEQUENTIAL 顺序正确
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘
- [x] 环境重置

## 6. 复盘

无新发现。

## 7. 结论

✅ **PASS** — 06-countersign-sequential PG 全流程符合设计。
