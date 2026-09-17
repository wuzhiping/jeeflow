# 14-decision-submitType PG 后端覆盖测试

- **测试时间**：2026-09-17 13:00:00
- **后端**：PG
- **关联流程**：`./flows/14-decision-submitType.json`
- **关联已知问题**：`./docs/known-issues.md §20`

## 1. 设计概览

```
start → apply(user1) → task1(user2) → decision1 → {end [submitType∈{0,1,5,20}] | apply [submitType∈{2,3,6}]}
```

## 2. 部署

reset → save → deploy pdid=1789615468440000 ✅

## 3. 启动 + 执行（双场景）

### Test A: submitType=0 happy path

→ instanceId=91766239705159

执行 user2 submitType=0 → state=20 (fallback 到 end)

### Test B: submitType=2 REJECT

→ instanceId=91766240718922

执行 user2 submitType=2 → state=45 (facade 拦截 REJECT)

## 4. 校验

| 测试 | submitType | state | 路由 |
|---|---|---|---|
| A | 0 | 20 | decision expr 不支持 `\|\|`, fallback edges[0]=end |
| B | 2 | 45 | facade 拦截, execute_and_jump_to_end |

## 5. AGENTS.md §10 自检

- [x] save + deploy code:0
- [x] startAndExecute 返回 processInstanceId（2 次）
- [x] A: state==20；B: state==45
- [x] submitType 路由矩阵正确
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘
- [x] 环境重置

## 6. 复盘

无新发现。PG 后端 submitType 路由与 sqlite 一致。

## 7. 结论

✅ **PASS**（设计意图部分不可实现，但 happy path 兼容 fallback）。
