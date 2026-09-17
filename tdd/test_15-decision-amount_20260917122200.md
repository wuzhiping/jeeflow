# 15-decision-amount 覆盖测试

- **测试时间**：2026-09-17 12:22:00
- **测试类型**：按 docs/AGENTS.md §5 完整流程（双分支）
- **关联流程**：`./flows/15-decision-amount.json`
- **关联已知问题**：`./docs/known-issues.md §21`（Issue D 修复后已通过）

## 1. 设计概览

```
节点：start → apply(user1) → decision1 → {task1(user2) if amount>=10000 | end}
决策 expr:
  decision1→task1 expr='amount >= 10000'
  decision1→end expr='amount < 10000'
```

## 2. 部署

reset → save (name=15-decision-amount) → deploy → processDefineId=113 ✅

## 3. 启动（双分支）

### Test A: amount=500 (<10000 → decision→end, 无 task1)

```bash
curl -X POST /wf/processInstance/startAndExecute -d '{
  "processDefineId": 113, "operator":"user1",
  "assignees":{"apply":"user1"},
  "variables":{"submitType":1, "f_applyUser":"user1", "f_purpose":"reg15-low", "u_userId":"user1", "u_realName":"用户1"},
  "amount": 500      ← 顶层
}'
```

→ instanceId=91765335784772

启动后 decision 评估 → amount<10000 → end → state=20 DONE（无需 task1 actor）

### Test B: amount=15000 (>=10000 → decision→task1)

```bash
... "amount": 15000 ...
```

→ instanceId=91765336411462

启动后 decision → task1(user2) DOING → user2 execute → state=20

## 4. 校验

### 4.1 Test A detail

```
state=20 (DONE)  active=0
  apply  state=20
```

approvalRecord: apply(user1) ✅ — task1 未创建（决策走 end）

### 4.2 Test B detail

```
state=20 (DONE)  active=0
  apply  state=20
  task1  state=20
```

approvalRecord: apply(user1) → task1(user2) ✅

## 5. AGENTS.md §10 自检

- [x] save + deploy code:0
- [x] startAndExecute 返回 processInstanceId（2 次）
- [x] 走完所有 task，state==20
- [x] approvalRecord 节点顺序符合设计
- [x] decision expr `amount >= 10000` / `amount < 10000` 正确路由
- [x] amount **顶层传递**（Issue D 修复后）
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘
- [x] 环境重置

## 6. 复盘

**确认 §21 已修复（Issue D）**：
- `amount` 顶层传递，decision expr `vars_.get("amount")` 能正确取值
- 修复方式：`main.py`+`main_pg.py` monkey-patch `facade.flow`，startAndExecute 前把 args["variables"] 字典展开到 args 顶层

无新发现。decision 行为符合设计：
- amount=500 → end（决策评估 amount<10000 为真）
- amount=15000 → task1(user2)（决策评估 amount>=10000 为真）

## 7. 结论

✅ **PASS** — 15-decision-amount 双分支符合设计，Issue D 修复有效。
