# 14-decision-submitType 测试日志

**日期**：2026-09-17 11:10
**测试文件**：`./flows/14-decision-submitType.json`
**结论**：❌ **FAIL** — 设计意图（按 submitType 走 decision 分流）无法实现

---

## 1. 流程结构（5 节点 / 5 边）

```
start → apply(user1) → task1(user2) → decision1 → ┬─ end (submitType∈{0,1,5,20})
                                                    └─ apply (submitType∈{2,3,6})
```

## 2. 设计意图

通过 decision1 节点按 submitType 分流：
- `submitType∈{0,1,5,20}` → 走 end
- `submitType∈{2,3,6}` → 走 apply 回退

## 3. 实测根因

### 3.1 decision expr 含 `||` 不被 SimpleExprEvaluator 解析

`main.py:43-60`：

```python
class SimpleExprEvaluator(ExpressionEvaluator):
    async def eval(self, expr: str, vars: dict):
        m = re.match(r"^\s*(#?\w+)\s*(>=|<=|!=|==|>|<)\s*(\d+(?:\d+)?)\s*$", expr)
        if not m:
            return False
        ...
```

**regex 不支持 `||` 复合表达式**。decision expr：
- `submitType==0 || submitType==1 || submitType==5 || submitType==20` → regex 不匹配 → 返回 False
- `submitType==2 || submitType==3 || submitType==6` → regex 不匹配 → 返回 False

**所有 expr 都返回 False**，fallback 到 `edges[0] = e_decision1_end` → end → state=20。

### 3.2 submitType=2/3/6 被 facade 拦截

`facade.py:295-315` `_processTask_execute`：

```python
if submit_type == SUBMIT_REJECT:                  # 2
    await self._engine.execute_and_jump_to_end(task_id, operator, flow_args)
elif submit_type == SUBMIT_ROLLBACK:              # 3
    await self._engine.execute_and_jump_task(task_id, operator, flow_args)
elif submit_type == SUBMIT_JUMP:                  # 4
    ...
elif submit_type == SUBMIT_ROLLBACK_TO_OPERATOR:  # 6
    await self._engine.execute_and_jump_to_first_task_node(task_id, operator, flow_args)
elif submit_type == SUBMIT_COUNTERSIGN_DISAGREE:  # 20
    flow_args["countersignDisagreeFlag"] = 1
    await self._engine.execute_process_task(task_id, operator, flow_args)
```

**submitType=2/3/6/4 全部由 facade 路由**，根本不调 `execute_process_task`，**不走 decision 节点**。

只有 `submitType=0/1/5/20`（普通 execute_process_task 路径）才会评估 decision。

## 4. 测试矩阵

| 测试 | submitType | 设计意图 | 实测 |
|---|---|---|---|
| A | 0 (APPLY) | end | ✅ state=20（fallback 到 e_decision1_end） |
| B | 2 (REJECT) | apply 回退 | ❌ state=45 REJECT（facade 直接终止，未走 decision） |
| C | 1 (AGREE) | end | ✅ state=20（fallback 到 e_decision1_end） |

**所有情况都没真正走到 decision 分流逻辑**。

## 5. 关键发现

### 5.1 facade 拦截优先级

submitType 路由分两层：

| submitType | facade 层路径 | 是否走 decision |
|---|---|---|
| 0/1/5/20 | `execute_process_task` | ✅ 是 |
| **2** | `execute_and_jump_to_end`（state=45 REJECT） | ❌ 否 |
| **3** | `execute_and_jump_task`（无 target 时回退 first task node） | ❌ 否 |
| **4** | `execute_and_jump_task(target_task_name)` | ❌ 否 |
| **6** | `execute_and_jump_to_first_task_node` | ❌ 否 |

**decision 节点只能路由 submitType∈{0,1,5,20}**。

### 5.2 SimpleExprEvaluator 不支持复合表达式

只支持：
- `<key> <op> <number>`：单 key op number
- `#<key> <op> <number>`：OGNL 风格前缀
- ops: `>` / `>=` / `<` / `<=` / `==` / `!=`

**不支持**：`||` / `&&` / `IN` / 列表 / 函数

### 5.3 引擎修复建议

- **SimpleExprEvaluator 扩展**支持 `||` / `&&`（与 §14 一致）
- 或设计层：把每个 submitType 拆为单边（如 `submitType==0` / `submitType==1` / ...），第一条匹配即流转

## 6. 文档同步

- `docs/known-issues.md §20` 新增
- `docs/flow.md §3.4`：SimpleExprEvaluator 不支持复合表达式
- `docs/state.md §4` SubmitType 路由矩阵：2/3/4/6 由 facade 拦截，不走 decision

## 7. 结论

| 项 | 状态 |
|---|---|
| 流程部署 | ✅ |
| startAndExecute | ✅ |
| submitType=0 → end | ✅ state=20（fallback 巧合） |
| submitType=2 → apply 回退 | ❌ facade 直接 REJECT（state=45） |
| submitType=1 → end | ✅ state=20（fallback 巧合） |
| decision expr 求值 | ❌ `||` 不支持，所有 expr 返回 False |
| submitType=3/6 | ❌ 未测试（同样被 facade 拦截） |

**整体**：❌ FAIL（设计意图无法实现）

## 8. 服务

PID 3365271 在 8101 运行中，healthz UP。
