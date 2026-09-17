# 15-decision-amount 测试日志

**日期**：2026-09-17 11:20
**测试文件**：`./flows/15-decision-amount.json`
**结论**：✅ **PASS**（含 Issue D 修复）

---

## 1. 流程结构（5 节点 / 5 边）

```
start → apply(user1) → decision1 → ┬─ task1(user2) (amount >= 10000)
                                    └─ end (amount < 10000)
                                    ↓
                                    end ←─── (task1 → end)
```

## 2. 测试矩阵

| 测试 | amount | 期望路径 | 实测 state | 实测路由 |
|---|---|---|---|---|
| 15-A | 5000 | decision1 → end | 20 DONE | ✅ |
| 15-B | 15000 | decision1 → task1(user2) → end | 20 DONE | ✅ |
| 15-C | 10000 | decision1 → task1 (==10000 >=) | 20 DONE | ✅ |
| 15-D | 9999 | decision1 → end | 20 DONE | ✅ |

**全部 PASS** ✅

## 3. 发现的关键 Bug（Issue D）—— 已修复

### 3.1 现象

第一次测试发现：amount=5000 时走 task1 而非 end；amount=15000 时也走 task1（fallback edges[0]=e_decision1_task1）。

`inst.variables` 实际存储为：
```json
{
  "assignees": "user1",
  "variables": {"amount": 5000},   ← 嵌套！
  "title": "15-A",
  ...
}
```

`decision1` 求值时 `vars_.get("amount")` 返回 `None` → `SimpleExprEvaluator` 返回 False → 两条 expr 边都 False → fallback 到 edges[0]。

### 3.2 根因

`jeeflow/engine.py:69` `start_process_instance_by_id`：

```python
vars_ = {**(args or {})}
inst = ProcessInstance(... variables=vars_, ...)
```

`args` 整体作为 `inst.variables`。调用方传 `{variables: {amount: 5000}}` → `amount` 被嵌套到 `inst.variables.variables.amount`。

`_prepare_execute_task:207` 合并：
```python
vars_ = {**base_vars, **task.variables, **args}
```

`base_vars = inst.variables`，所以 `vars_["amount"]` 不存在 → expr 永远 False。

### 3.3 修复（main.py + main_pg.py 同源）

`main_pg.py:243-265` `_wrap_facade_flow._safe_flow` 加 Issue D 分支：

```python
if action in ("processDefine/startAndExecute", "processInstance/startAndExecute"):
    v = args.get("processDefineId")
    ...
    # Issue D：业务 variables 嵌套解包
    nested = args.get("variables")
    if isinstance(nested, dict):
        for k, val in nested.items():
            if k not in args:
                args[k] = val
```

`main.py:142-159` 同样 monkey-patch `facade.flow`。

效果：startAndExecute 前把 `args["variables"]` 子字典展开到 args 顶层，让 `inst.variables = {amount: 5000, ...}` 直接可被 expr 访问。

## 4. 测试细节（修复后）

### 15-A: amount=5000

```
startAndExecute {amount: 5000}
  → apply 完成
  → decision1 评估 expr:
    - e_decision1_task1 expr="amount >= 10000" → 5000 >= 10000 False
    - e_decision1_end expr="amount < 10000" → 5000 < 10000 True ✓
  → 走 end
state=20 DONE
```

### 15-B: amount=15000

```
startAndExecute {amount: 15000}
  → apply 完成
  → decision1: amount >= 10000 True ✓
  → task1 (user2)
  → user2 execute submitType=1
  → end
state=20 DONE
```

## 5. 影响范围

### 5.1 受影响的流程（重新验证）

| 流程 | 之前状态 | 修复后状态 |
|---|---|---|
| 03-decision-expr | ❓ 巧合 PASS（amount>1000 是 edges[0]）| ✅ 真实 expr 路由 |
| 10-mixed-mode | ✅ PASS（巧合）| ✅ 真实 expr 路由 |
| 15-decision-amount | ❌ FAIL | ✅ PASS |

**之前报告 03/10 PASS 是巧合**：决策 fallback 到 edges[0]，恰好匹配测试预期路径。

### 5.2 引擎层约束（不改 jeeflow）

- `jeeflow engine.start_process_instance_by_id:69` 把 `args` 整体塞到 `inst.variables`
- 应改为 `vars_ = {**(args.get("variables") or args or {})}`（展开 nested）
- 或 `vars_ = {**args.pop("variables", {}), **args}`

### 5.3 main.py 与 main_pg.py 同步

两文件独立维护，Issue D 修复需两处都加。`main_pg.py` 在 `_wrap_facade_flow._safe_flow`；`main.py` 直接 monkey-patch `facade.flow`。

## 6. 服务

- 旧 PID 3365271（main_pg.py）→ asyncpg 缺失退出
- 新 PID 3378915（main.py + JEEFLOW_PG_DSN 占位环境变量）
- backend: python（sqlite 落盘）
- 8101 健康 UP

## 7. 文档同步

- `docs/known-issues.md §21` 新增（Issue D 已修复）
- `docs/AGENTS.md §5.3` 加 startAndExecute variables 解包提示
- `docs/state.md §5` 决策 expr 路由矩阵：变量必须顶层
- `flows/README.md` 15 标 PASS
