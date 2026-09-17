# BDD Task 25: 嵌套多层 decision + 自定义变量（PASS）

- **时间**：2026-09-17 14:04:00（TS=20260917140400）
- **JSON 定义**：`./bdd/bdd-nested-decision_20260917140400.json`
- **服务**：main.py（PID 3435402）

## 1. 场景设计

按金额自动路由到不同审批人：

| 金额 | 路径 |
|---|---|
| < 1000 | apply → dec_low → mgr_review → notify → end |
| 1000-5000 | apply → dec_low → dec_mid → dir_review → notify → end |
| >= 5000 | apply → dec_low → dec_mid → dec_high → ceo_review → notify → end |

**3 层嵌套 decision 链** + 6 条 expr 边（每层 2 条 expr）。

## 2. 测试结果

| Case | amount | 实际路径 | 审批人 | 结果 |
|---|---|---|---|---|
| 500 | 0-1000 | dec_low → mgr_review | manager | state=20 ✅ |
| 3000 | 1000-5000 | dec_low → dec_mid → dir_review | director | state=20 ✅ |
| 8000 | >= 5000 | dec_low → dec_mid → dec_high → ceo_review | boss | state=20 ✅ |

**全部 PASS** ✅

## 3. 关键发现

1. **嵌套 decision 工作**：每层 decision 独立 expr 求值，匹配走对应边，否则走下一层或默认边
2. **自定义变量**：startAndExecute variables.amount → vars.amount → expr `#amount<1000` 生效
3. **变量命名**：engine.py 用 `vars.get(key)`，所以 `f_amount` 也可读，但 expr 用 `amount` 即可（注入到 inst.variables）
4. **expr 默认值 fallback**：所有 expr false → 第一条出边（§33 已记录）
5. **decision 节点无 actor**：不需要 assignee，是纯路由节点
6. **分支汇聚**：3 条 review 任务都汇到 notify（多入边节点）

## 4. 引擎变量注入路径

```
startAndExecute variables.amount=500
→ engine.start_process_instance_by_id(args)
→ inst.variables["amount"]=500 (以及 f_amount 通过解包)
→ execute_process_task 时 vars_=inst.variables
→ expr_eval.eval("#amount<1000", vars_)
→ vars_.get("amount")=500 → True
```

**注意**：v1.5.0 在 main.py `_safe_flow` wrapper 把 nested variables 解包到 args 顶层（§34 已记录）

## 5. 文档改进

- docs/flow.md §3.4 增强：嵌套 decision 设计模式 + 变量注入路径
- docs/known-issues.md 无新增（行为符合预期）

## 6. 后续

- Task 26: 委派场景 (submitType=3 ROLLBACK)
