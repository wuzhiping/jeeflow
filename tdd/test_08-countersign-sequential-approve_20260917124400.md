# 08-countersign-sequential-approve PG 后端覆盖测试

- **测试时间**：2026-09-17 12:44:00
- **后端**：PG
- **关联流程**：`./flows/08-countersign-sequential-approve.json`

## 1. 设计概览

```
start → apply(applicant) → task1(SEQUENTIAL [userA,userB]) → approve(leader) → end
```

## 2. 部署

reset → save → deploy pdid=1789615058034000 ✅

## 3. 启动 + 执行

→ instanceId=91765819451428

执行 userA → userB → leader，全部 code=0 → state=20

## 4. 校验

```
state=20 (DONE)
  apply   state=20
  task1   state=20
  task1   state=20
  approve state=20
```

## 5. AGENTS.md §10 自检

- [x] save + deploy code:0
- [x] startAndExecute 返回 processInstanceId
- [x] state==20
- [x] SEQUENTIAL + approve 顺序衔接正确
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘
- [x] 环境重置

## 6. 复盘

无新发现。

## 7. 结论

✅ **PASS** — 08-countersign-sequential-approve PG 全流程符合设计。
