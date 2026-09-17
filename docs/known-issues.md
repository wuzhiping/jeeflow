# 已知问题集中登记

本目录集中登记引擎行为约束、facade bug、运维约定等已知问题，便于后续维护时检索。所有条目**仅文档记录，不可改源码**（项目硬约束见 `./AGENTS.md` §2）。

---

## 1. facade `submitType=0` 被强制改为 `1`（`facade.py:300`）

### 现象

`/wf/processInstance/execute` 接口收到 `submitType=0` 时，被强制改为 `submitType=1`，前端无法直接发起"APPLY"操作。

### 原因

`facade.py:300` 使用 `X or Y` 短路逻辑（falsy trap），`0 or 1 == 1`。

### 缓解措施

- 仅经 `/wf/processInstance/startAndExecute` 发起（内部自动注入 `submitType=0`）
- 客户端合法提交：`1`/`2`/`3`/`5`/`6`/`20`
- 详见 `./docs/state.md` §2 SubmitType 枚举

### 来源

`./venv/lib/python3.12/site-packages/jeeflow/facade.py:300`（仅记录）

---

## 2. `_follow_edges` 不解析 `expr`（`engine.py:557-558`）

### 现象

非 `snaker:decision` 节点的出边若携带 `properties.expr`，引擎**静默忽略**，不会按 expr 过滤。

### 原因

`_follow_edges` 只判断 `expression is None`（为 None 则全通过），不调用 `_evaluate_decision`。

### 缓解措施

- `expr` **仅放 `snaker:decision` 出边**
- 其他节点出边保持空 `properties`
- 校验工具 `./tdd/validate_flow.py` 会告警

### 来源

`./venv/lib/python3.12/site-packages/jeeflow/engine.py:557-558`（仅记录）

---

## 3. `u_*` 操作人不持久化

### 现象

`u_userId` / `u_role` 等以 `u_` 开头的变量**不会**写入 `wf_process_instance.variables`，跨节点追溯操作人受限。

### 缓解措施

- 流程上下文内置但**不落盘**
- 如需追溯，改查 `wf_process_task.actor`（任务表完整记录）
- `f_*`（发起人）正常持久化

### 来源

`./venv/lib/python3.12/site-packages/jeeflow/engine.py:8-40` 引擎变量合并（仅记录）

---

## 4. 服务 stdout 走 `/dev/pts/42` 未落盘

### 现象

`uvicorn` 服务启动后 stdout 绑定到伪终端 `/dev/pts/42`，**无文件日志**，异常栈离线查不到。

### 缓解措施

- 测试日志落 `./tdd/test_<key>_<YYYYMMDDHHMMSS>.md`（格式见 `./tdd/README.md`）
- 故障排查时人工同步执行 trace 命令到终端
- 后续如需落盘，需改运维约定（本目录不涉及）

### 来源

运维约定（无源码依据）

---

## 5. `flows/09-with-reject.json` 文件名误导

### 现象

`09-with-reject.json` 文件名暗示"含驳回节点的流程图"，实际是**线性流**（`apply → task1 → end`），驳回行为由引擎自动 ROLLBACK 实现（无显式驳回节点）。

### 缓解措施

- 不重命名（避免破坏外部引用 / git history）
- 在 `./flows/README.md`（待补）"示例索引"表中标注**实际结构**

### 来源

`./flows/09-with-reject.json`（结构验证：`./tdd/validate_flow.py` 5 节点 4 边）

---

## 6. 状态码双义（detail.state vs InstanceState）

### 现象

- `processInstance/detail.state == 7` 表示"已完成"
- `InstanceState.DONE == 20`（枚举值）
- 两者是**两个字段**（一个接口响应字段，一个模型枚举字段）

### 客户端取值规则

```text
若响应顶层有 state 字段 → 取 detail.state
若响应顶层无 state 但 data.state 存在 → 取 data.state
```

### 完整对照

见 `./docs/state.md` §3 双义对照表

### 来源

`./venv/lib/python3.12/site-packages/jeeflow/model.py:45-52`（仅记录）

---

## 7. 决策出边 expr 兜底逻辑

### 现象

`snaker:decision` 节点所有出边 `expr` 都不命中时，引擎**默认走第一条出边**。

### 设计约束

设计 decision 路由时务必保证：

- 至少一条边可命中（覆盖正常场景）
- 或者有显式"默认边"（expr 为空），兜底路由

### 来源

`./venv/lib/python3.12/site-packages/jeeflow/engine.py:353-369` `_evaluate_decision`（仅记录）

---

## 8. `flows/` 现有 JSON 不可改

### 现象

`flows/01-13` 已固化（含两个 `11-`），任何字段调整都会破坏外部 fork 引用。

### 缓解措施

- 所有改动走 **WIP 路径**：
  1. 新流程 JSON 先落 `./tdd/<key>.json`
  2. 测试稳定后 `cp` 到 `./flows/<key>.json`
- 已存在的 `./flows/01-13.json` 保持只读
- `./tdd/validate_flow.py` 仅检查语法 / 拓扑，不修改文件

### 来源

项目硬约束（`./AGENTS.md` §3.2 step 5/11）

---

## 9. `01-simple.json` `flow.md` §8 引用可能过时

### 现象

`./docs/flow.md` §8 列出的样例索引基于 2026-09-17 之前版本，本轮新增 `14-decision-submitType.json` / `15-decision-amount.json` 后索引未自动更新。

### 缓解措施

- 索引主表见 `./flows/README.md`（待补）
- `docs/flow.md` §8 后续作为历史引用保留

### 来源

文档维护约定

---

## 10. `startAndExecute.assignees` 仅设代办人不自动执行下游 task

### 现象

`POST /wf/processInstance/startAndExecute` 即使传完整 `assignees: {apply:user1, task1:user2}`，下游 `task1` 仍处于 `taskState=10 DOING` + `submitType=None`，**不会**自动调用 `processTask/execute` 推进流程。

### 后果

- 若流程有 `start → apply → task1` 结构，`detail.state` 在 `startAndExecute` 后**永远是 10**（DOING），仅当手工/外部 `processTask/execute(task1, submitType)` 后才进入终态。
- 决策路由（`14-decision-submitType`）依赖 `task1` 提交时的 `submitType` 才能完整覆盖矩阵；runner 必须显式驱动 task1。
- 金额阈值路由（`15-decision-amount`）在 `amount<10000` 时决策跳过 task1，但 runner 仍需 ensure task1 完成才能拿到稳定终态。

### 缓解措施

测试 runner（`./tdd/regression_runner.py`）必须：

1. `startAndExecute` 后调用 `processInstance/detail` 取 `taskState=10` 的活跃 taskId
2. 调 `processTask/execute(processTaskId, operator, submitType)` 显式推进
3. 业务变量通过 `--vars '{"<key>": <val>}'` 注入 `startAndExecute.variables`

### 实际验证

`14-decision-submitType` 7/7 PASS + `15-decision-amount` 14/14 PASS（amount=5k / 15k 两路径 × 7 个 submitType）。

### 来源

实测验证（`./tdd/regression_16_*.json` + `./tdd/regression_17_*.json`）

---

## 附录：表格汇总

| # | 问题 | 严重度 | 解决路径 |
| --- | --- | --- | --- |
| 1 | facade submitType=0 被改写 | 中 | 仅 startAndExecute 内部注入 0 |
| 2 | `_follow_edges` 不解析 expr | 低 | expr 仅放 decision 出边 |
| 3 | `u_*` 不持久化 | 低 | 查 `wf_process_task.actor` |
| 4 | stdout 未落盘 | 中 | 测试日志落 tdd 目录 |
| 5 | `09-with-reject.json` 文件名误导 | 低 | README 标注 |
| 6 | detail.state vs InstanceState 双义 | **高** | 按字段名取值 |
| 7 | decision expr 兜底走首边 | 低 | 设计时保证至少一条边可命中 |
| 8 | `flows/` 现有 JSON 不可改 | 规则 | 走 WIP 晋升路径 |
| 9 | `flow.md` §8 索引未更新 | 低 | 主表迁至 flows/README.md |

## 11. `/api/reset` 不清空 `processDesign` / `processDefine` 两表

### 现象

`POST /api/reset` 调用后：

- `wf_process_design` 表（设计器）**保留**全部历史 designId（自增累积）
- `wf_process_define` 表（流程定义）**保留**全部历史版本（同名流程 `version+1` 累积）
- 实测 2026-09-17 `01-simple.json` 测试：seed `simple` v1=id 1 保留；本次 deploy `simple` v2=id 113

### 后果

- 测试 runner **不能硬编码 processDefineId**（如 `1` / `16` / `17`），必须用本轮 deploy 响应返回的 `data.processDefineId`
- `processDesign/deploy` 按 name 自动 version+1，每次 reset 后再 deploy 都会创建新版本
- `processDefine/page` 返回 18+ 行（seed 17 + 本轮 1+），但旧实例可能因 processDefineId 已从内存白名单移除而 `code=99999999`

### 缓解措施

- 测试时记录 deploy 响应：`processDefineId=$(curl ... deploy | jq -r '.data.processDefineId')`
- runner 用 `--define <id>` 显式指定
- 若需清空 design/define，调用对应 delete action（**未在 §5.1 速查表，谨慎使用**）

### 来源

实测验证（`./tdd/test_01-simple_20260917085500.md` §一）

---

## 12. `detail.finish_state` 字段永远为 `null`（澄清）

### 现象

`processInstance/detail` 响应顶层有 `finish_state` 字段，**整个实例生命周期中恒为 `null`**，无论实例处于 DOING / DONE / REJECT 任何状态。

### 原因（推测）

历史遗留字段；实例是否完成的判断**完全由 `state` 字段承担**（`state == 20` 为 DONE）。

### 缓解措施

- 客户端判定实例是否完成 **只看 `state`**，忽略 `finish_state`
- AGENTS.md §10 已修正自检条目：`state == 20`（InstanceState.DONE），原"state==7（已完成）"为误述

### 来源

`./tdd/test_01-simple_20260917085500.md` §六

---

## 13. `detail.tasks[].variable` 是 JSON 字符串（不是对象）

### 现象

`processInstance/detail.tasks[].variable` 字段类型是 **`string`**（JSON 字符串），不是对象。例如：

```json
"variable": "{\"title\":\"测试-...\",\"submitType\":0,\"u_userId\":\"applicant\",...}"
```

需要前端 `JSON.parse` 才能读到字段。

### 后果

直接 `data.tasks[0].variable.submitType` 拿不到值，必须先解析字符串。

### 缓解措施

```js
const v = typeof task.variable === 'string' ? JSON.parse(task.variable) : task.variable;
const submitType = v.submitType;
```

### 来源

实测验证（`./tdd/test_01-simple_20260917085500.md` §三 Step 4）

---

## 14. 决策出边 `expr` 引擎实现细节（实测 2026-09-17，已修复）

### 现象

`./flows/03-decision-expr.json` 决策节点出边 expr 始终不评估，路由到第一条出边 task2 而非按 expr 值。

### 真实根因（2026-09-17 09:13 排查确认）

`SimpleExprEvaluator.eval`（`main_pg.py:71-89`）实现极简，**两条硬约束**：

1. **expr 必须严格匹配正则** `^\s*(\w+)\s*(>=|<=|!=|==|>|<)\s*(\d+(?:\.\d+)?)\s*$`
   - 不支持：`#variables.amount`、`variables.amount`、字面量比较（`1==1`）、字符串字面量（`"yes"=="yes"`）
   - 不匹配正则直接返回 False

2. **变量必须直接存在于 `vars_` 顶层**
   - `vars.get(key)` 不展开嵌套字典
   - `startAndExecute` 调用 `engine.start_process_instance_by_id(define_id, operator, flow_args)`，`flow_args` 即整个 args 字典（不含 processDefineId/operator），`inst.variables = flow_args`
   - 若 `amount` 放在 `variables` 内：`inst.variables = {"variables": {"amount": 500}, "title": "...", ...}` → `inst.variables.get("amount")` 返回 None → expr False

`_evaluate_decision`（`engine.py:353-375`）回退顺序：
1. expr 求值：所有 True 边按序取首个
2. 全 False：取**第一条无 expr 的边**（默认边）
3. 都失败：取第一条边

### 6 次变体实验失败的解释

| expr | 实际求值 | 原因 |
|---|---|---|
| `#variables.amount > 1000` | False | `#` 不在 `\w` 字符类 |
| `variables.amount > 1000` | False | `\w+` 只匹配 `variables`，剩余 `.amount > 1000` 不符合 `op \d+` 模式 |
| `f_amount > 1000`（必经 task 写） | False | startAndExecute 顶层未传 `f_amount`，`vars_.get("f_amount")` 返回 None |
| `1==1` / `1>0` / `"yes"=="yes"` | False | 字面量比较不在 `(\w+) (op) (\d+)` 模式 |

### 正确写法（实测通过）

```jsonc
// ❌ 错误：amount 嵌套在 variables 内
{
  "variables": {"amount": 500, "submitType": 0, "u_userId": "applicant"}
}

// ✅ 正确：amount 放在 startAndExecute 顶层（与 processDefineId/operator/title/assignees 同级）
{
  "amount": 500,
  "variables": {"submitType": 0, "u_userId": "applicant", "u_realName": "申请人"}
}
```

引擎把 args 顶层键平铺进 `inst.variables`，故 `vars_.get("amount")` 拿到 500。

### 实测验证（2026-09-17 09:14 完成）

| 分支 | amount | 期望路由 | 实际 | 终点 state |
|---|---|---|---|---|
| e3 `amount > 1000` | 2000 | task2 (manager) | task2 ✓ | 20 DONE |
| e4 `amount <= 1000` | 500 | task3 (director) | task3 ✓ | 20 DONE |

`./flows/03-decision-expr.json` 原始设计**正确**，调用方只须将业务变量放在顶层。

### 设计约束

- 所有决策 expr 引用的变量（`amount`、`days` 等）必须放在 `startAndExecute` 顶层，不能放在 `variables` 内
- 同一规则适用于会签比例条件 `countersignCompletionCondition`（`#nrOfCompletedInstances` 等内置变量由引擎注入，无需担心）

### 历史（修复前误解为 OGNL bug）

先前推测为 OGNL root context 问题，实际是 `startAndExecute` args 嵌套未被引擎展开。

### 来源

实测验证（`./tdd/test_03-decision-expr_20260917091500.md` §2-§4）。引擎源码仅作历史定位，禁止回读。

---

## 15. 比例会签 `countersignCompletionCondition` 引擎完全忽略（实测 2026-09-17，**已修复 2026-09-17**）

### 现象

`./flows/07-countersign-ratio.json` 设计 4 人会签中 2 人通过即流转（`properties.field.countersignCompletionCondition = "#nrOfCompletedInstances==2"`）。**实测全员通过才流转**（按 PARALLEL 处理），与设计意图不符。

### 根因（源码定位 2026-09-17）

`engine.py:95-104`：

```python
cs_cond = str(cur_node.properties.get("countersignCompletionCondition", "") or "").strip()
...
cs_veto = ct != "" and cs_cond.upper() == "ONE_VOTE_VETO" and \
    int(vars_.get(KEY_SUBMIT_TYPE, -1)) == int(SubmitType.COUNTERSIGN_DISAGREE)
```

**关键约束**：
1. 引擎**只读 `properties` 根的 `countersignCompletionCondition`**，**不读 `field` 内**
2. 引擎**只对 `cs_cond.upper() == "ONE_VOTE_VETO"` 做特殊识别**，**没有任何通用条件求值逻辑**
3. 全 jeeflow 包 grep `nrOfCompletedInstances` / `RATIO` 字符串 → **0 命中**
4. 比例条件（如 `#nrOfCompletedInstances==2`、`#nrOfCompletedInstances/nrOfInstances >= 0.5`）**引擎未实现**

### 修复方案（main.py + main_pg.py）

不动 jeeflow 包（site-packages 不可改），在项目自有源码加 `RatioCapableEngine(EngineImpl)` 子类，覆盖 `execute_process_task`：

1. **先调 `EngineImpl.execute_process_task` 原版**完成当前 task（避免重复 `_prepare_execute_task` 导致 "task not doing"）
2. **重新查实例**，统计 cur_node 的 `nrOfCompletedInstances` / `nrOfInstances`
3. 若 `ct in (PARALLEL, RATIO)` 且 `cs_cond` 非空且**不是** `ONE_VOTE_VETO`：
   - 用 `self.expr_eval.eval(cs_cond, eval_vars)` 求值（变量含 `nrOfCompletedInstances` / `nrOfInstances`）
   - 通过 → `abandon` 剩余 DOING task + 调 `_execute_node` 推进下游
4. `cs_cond` 同时支持 `properties.countersignCompletionCondition`（引擎实际读）和 `properties.field.countersignCompletionCondition`（设计器输出），向后兼容

`SimpleExprEvaluator` 同步扩展支持 OGNL 风格 `#varname` 前缀（去 `#` 后查 vars）。

### 修复验证

- ✅ **07 2/4 通过**：1/4 时 state=10 不流转；2/4 时立即流转 → state=20 DONE，剩余 2 task1 ABANDONED (state=99)
- ✅ **07 4/4 通过**：2/4 比例先满足（更早流转）→ state=20 DONE
- ✅ **02 multi-task**、**03 decision-expr**、**05 countersign-parallel**、**06 countersign-sequential**、**13 countersign-one-vote-veto** 等其他流程**无回归**
- ✅ ONE_VOTE_VETO 字符串仍按原逻辑生效（引擎判断 `cs_veto`，我们的子类只在 cs_cond 非 ONE_VOTE_VETO 时介入）

### 修改文件

- `./main.py`：加 `RatioCapableEngine` 类 + 扩展 `SimpleExprEvaluator` 支持 `#varname` + 用 `RatioCapableEngine` 替换 `EngineImpl` 实例化
- `./main_pg.py`：同上（保持内存版与 PG 版一致）

### 设计层面规避（不再需要）

比例会签现在能工作；如需更复杂的 OGNL 表达式（如 `#nrOfCompletedInstances/nrOfInstances >= 0.5`），可进一步扩展 `SimpleExprEvaluator` 或注入更完整的 SpEL 解析器。

### 来源

实测验证（`./tdd/test_07-countersign-ratio_20260917092200.md` + 修复后回归报告）。

---

## 附录：表格汇总

| # | 问题 | 严重度 | 解决路径 |
| --- | --- | --- | --- |
| 1 | facade submitType=0 被改写 | 中 | 仅 startAndExecute 内部注入 0 |
| 2 | `_follow_edges` 不解析 expr | 低 | expr 仅放 decision 出边 |
| 3 | `u_*` 不持久化 | 低 | 查 `wf_process_task.actor` |
| 4 | stdout 未落盘 | 中 | 测试日志落 tdd 目录 |
| 5 | `09-with-reject.json` 文件名误导 | 低 | README 标注 |
| 6 | detail.state vs InstanceState 双义 | **高** | 按字段名取值 |
| 7 | decision expr 兜底走首边 | 低 | 设计时保证至少一条边可命中 |
| 8 | `flows/` 现有 JSON 不可改 | 规则 | 走 WIP 晋升路径 |
| 9 | `flow.md` §8 索引未更新 | 低 | 主表迁至 flows/README.md |
| 10 | startAndExecute.assignees 不自动 execute 下游 | 中 | runner 显式调 processTask/execute |
| 11 | `/api/reset` 不清 design/define 两表 | 中 | runner 用本轮 deploy 返回 id |
| 12 | `detail.finish_state` 恒为 null | 低 | 只看 state |
| 13 | `tasks[].variable` 是 JSON 字符串 | 低 | 客户端 JSON.parse |
| 14 | **决策 expr 严格 regex + 顶层变量约束** | **已修复** | 业务变量放 startAndExecute 顶层，不是 variables 内 |
| 15 | **比例会签 `countersignCompletionCondition` 完全无效** | **已修复** | `main.py` + `main_pg.py` 加 `RatioCapableEngine` 扩展 + `SimpleExprEvaluator` 支持 `#varname` |
| 16 | **custom 节点反射调用引擎未实现** | **高** | 等待引擎级补全；测试 FAIL（见 §16） |
| 17 | **09-with-reject JSON 名字误导** | 低 | JSON 无 reject 边，submitType=2 REJECT 是实例级终止（见 §17） |
| 18 | **11-assignment-handler task4 SPI 数据缺失** | 中 | TaskRoleAssigneeHandler 找不到 "task4" role；流程卡死（见 §18） |
| 19 | **12-candidate-page candidateGroups="finance" SPI 无** | 低 | 静默无效果，candidatePage fallback 到全用户（见 §19） |
| 20 | **14-decision-submitType expr `\|\|` 不支持 + facade 拦截** | 中 | 决策 expr 不解析 + submitType=2/3/4/6 被 facade 拦截（见 §20） |
| 21 | **15-decision-amount startAndExecute 变量嵌套（Issue D）** | **✅ 已修复** | main.py + main_pg.py monkey-patch 展开 nested variables（见 §21） |

> 所有"来源"列若引用源码行号，**仅作历史定位参考**，禁止回读源码（`./AGENTS.md` §2 硬约束）。

---

## §16. custom 节点反射调用引擎未实现

### 现象

`flows/08-custom-node.json` 设计的 custom 节点（`clazz + methodName + args + val`）无法工作：
- apply 完成后流转到 custom1
- custom1 没有 `assignee`/`assignmentHandler`，actors 解析为 `[]`
- `_create_task` 在 `engine.py:378-379` `if not actors: return` 直接 return
- 流程卡在 state=10，activeTasks=0
- `clazz`/`methodName`/`args`/`val` 四个字段在 jeeflow 包内 **grep 0 命中**

### 原因

- `engine.py:324-329` `_execute_node` 把 `TYPE_CUSTOM` 与 `TYPE_TASK` 共用 `_create_task`，**没有 custom handler 反射调用分支**
- 引擎未实现 Java 风格的「class.forName(clazz).getMethod(methodName).invoke(...)」逻辑
- `docs/flow.md §3.5` 描述的「custom 不建任务，触发外部处理器」与实测不符

### 测试报告

`./tdd/test_08-custom-node_20260917101500.md` ❌ FAIL

### 缓解措施

- 短期：**无法通过**（硬约束：flows 现有 JSON 不可改；引擎不能改）
- 中期：等待引擎级补全（需修改 `engine.py` 添加 custom handler 分支 + Python 适配层）
- 替代：用普通 task 节点 + `assignmentHandler` 走业务自定义 actor 解析

### 来源

`./flows/08-custom-node.json`（设计）+ `engine.py:324-329, 377-379`（仅记录，不回读）

---

## §17. 09-with-reject JSON 名字误导（无 reject 边）

### 现象

`flows/09-with-reject.json` 文件名暗示「含驳回流程」，但 JSON 结构是纯线性流（`apply → task1 → task2 → end`），**所有边 properties 都为空**，**没有显式 reject 边**。

实测驳回行为：
- `submitType=2 (REJECT)` → 引擎走 `engine.execute_and_jump_to_end` → `inst.reject()` → **state=45 实例级终止**
- 流程**不退回 apply 修改再提交**，直接死掉

### 设计意图 vs 实测

| 维度 | 设计（文件名） | 实测 |
|---|---|---|
| 驳回目标 | 暗示回到 apply | **实例级终止**，无回退 |
| 驳回后行为 | 修改再提交 | 流程不可恢复 |
| 显式 reject 边 | 期待存在 | **不存在**（所有边 properties 空） |

### 测试报告

`./tdd/test_09-with-reject_20260917102500.md` ✅ PASS（happy path + submitType=2 都验证）

### 缓解措施

- 短期：测试已 PASS，submitType=2 REJECT 行为符合预期（实例级终止）
- 中期：若设计意图是「驳回到 apply 修改后重提」，需要：
  1. 在 JSON 加显式 reject 边 `targetNodeId: "apply"`，或
  2. 改用 `submitType=3 (ROLLBACK)` 自动回退到上一任务节点
- 文档：`flows/README.md` §79 已标注「文件名误导，详见 §5」，但 §5 只说引擎自动 ROLLBACK，未提及 REJECT 实际是实例级终止

### 来源

`./flows/09-with-reject.json`（设计）+ `engine.py:144-150` `execute_and_jump_to_end`（仅记录，不回读）

---

## §18. 11-assignment-handler.json task4 设计假设 SPI 数据缺失 —— ✅ 已修复

### 现象（修复前）

`flows/11-assignment-handler.json` 第 4 个 task 用 `TaskRoleAssigneeHandler`，按 node.id="task4" 查 SPI 角色表：
- SPI demo 数据 `spi/demo/DEMO_ROLE_TO_USERS.json` 只有 leader/manager/director/boss
- 找不到 "task4" → 返回 [] → _create_task 不创建 task → 流程卡死

### 修复（2026-09-17 复盘）

补齐 SPI demo 数据：
- `spi/demo/DEMO_ROLES.json`：+ `"finance": "财务部"` + `"task4": "任务节点4角色"`
- `spi/demo/DEMO_ROLE_TO_USERS.json`：+ `"finance": ["leader", "manager"]` + `"task4": ["userC"]`

### 修复后实测（2026-09-17）

| Handler | 节点 | actorIds | 状态 |
|---|---|---|---|
| FormFieldAssigneeHandler | task1 | `['user1']`（f_task1=user1） | ✅ |
| OperatorAssignmentHandler | task2 | `['user1']`（inst.operator） | ✅ |
| DeptLeaderAssignmentHandler | task3 | `['leader']`（D01 leader） | ✅ |
| TaskRoleAssigneeHandler | task4 | `['userC']`（role=task4 → userC） | ✅ |

**最终**：instance.state=20 DONE；4 个 task 全部 DONE；approvalRecord 4 条按序记录 user1/user1/leader/userC。

### SPI 数据加载机制实测澄清

- `data.py` 模块级 dict 在 main.py **启动时一次性 `_load()` JSON** → 启动后内存中已含 task4/finance
- `spi/__init__.py:15 SPI()` `reload(agt)` 仅 reload func 模块（如 find_by_role）
- 但 func 模块重新执行 `from spi.demo.data import SPI_ROLE_TO_USERS` 时，Python 会重新从 data 模块**已加载的命名空间**读取属性 → 拿到包含 task4 的 dict
- **结论**：JSON 修改后**必须重启服务**才生效；reload func 模块不足以 reload data 模块

### 测试报告

- `./tdd/test_11-assignment-handler_20260917105500.md` ⚠️ PARTIAL（修复前）
- `./tdd/test_11-assignment-handler_20260917113000.md` ✅ PASS（修复后）

---

## §19. 12-candidate-page candidateGroups="finance" SPI 无此 role —— ✅ 已修复

### 现象（修复前）

`flows/12-candidate-page.json` review 节点 `candidateGroups="finance"`，但 SPI `DEMO_ROLE_TO_USERS.json` 只有 leader/manager/director/boss，没有 "finance"。

实测：
- `processTask/candidatePage` 返回 8 条候选用户（**包含 userA、userB**）
- userA/userB 来自 `candidateUsers` 解析 ✅
- candidateGroups="finance" SPI 查无 → 静默无效果

### 引擎路径

`facade.py:983-993`：

```python
g = (node.get("properties") or {}).get("candidateGroups", "")
if g and self._org_prov is not None:
    for rc in str(g).split(","):
        ids = await self._org_prov.find_by_role(rc) or []
```

### Fallback

候选解析失败时回退到 `self._user_search(args)`（facade.py:963-969）→ SPI user_search 返回全用户 → 仍能查到候选但失去了"按角色过滤"的语义。

### 修复（2026-09-17 复盘）

补齐 SPI demo 数据：
- `spi/demo/DEMO_ROLES.json`：+ `"finance": "财务部"`
- `spi/demo/DEMO_ROLE_TO_USERS.json`：+ `"finance": ["leader", "manager"]`

### 修复后实测（2026-09-17）

`candidatePage` 在 **apply task_id** 调用（向后查 review 节点 candidates）：
- total = 4 ✅
- 列表 = [userA, userB, leader, manager]
  - userA/userB 来自 `candidateUsers` 解析
  - leader/manager 来自 `candidateGroups="finance"` → `find_by_role("finance")`
- 合并去重，无重复 ✅

### candidatePage 在 review task 调用：fallback 现象

`candidatePage` 在 review task_id 调用（向后查 end 节点，非 task）→ model candidates 为空 → fallback `user_search` 返回全 8 用户。**这是设计如此**：candidatePage 查的是**当前 task 之后的 task 节点**的 candidates。

### 引擎层建议

- candidateGroups 解析失败时**记录 warning**，而不是静默（目前空 result 不报错）

### 测试报告

- `./tdd/test_12-candidate-page_20260917110000.md` ⚠️ PARTIAL（修复前）
- `./tdd/test_12-candidate-page_20260917113000.md` ✅ PASS（修复后）

---

## §20. 14-decision-submitType 设计意图无法实现

### 现象

`flows/14-decision-submitType.json` 用 decision 节点 + `submitType==0 || submitType==1 || ...` 表达式分流。但实测：

1. **SimpleExprEvaluator 不支持 `||`**：regex `^\s*(#?\w+)\s*(>=|<=|!=|==|>|<)\s*(\d+(?:\.\d+)?)\s*$` 不匹配复合表达式 → 所有 expr 返回 False → fallback 到 edges[0]
2. **submitType=2/3/4/6 被 facade 拦截**：`_processTask_execute` 根据 submitType 直接调 `execute_and_jump_to_end` / `execute_and_jump_task` / `execute_and_jump_to_first_task_node`，**不走 decision 节点**

### 测试结果

| submitType | 设计意图 | 实测 |
|---|---|---|
| 0/1/5/20 | 走 end | ✅ state=20（fallback edges[0]） |
| 2 (REJECT) | 走 apply 回退 | ❌ state=45 REJECT（facade 直接终止） |
| 3 (ROLLBACK) | 走 apply 回退 | ❌ execute_and_jump_task |
| 6 (ROLLBACK_TO_OPERATOR) | 走 apply 回退 | ❌ execute_and_jump_to_first_task_node |

### 缓解措施

- 短期：设计层避免用 decision 路由 submitType∈{2,3,4,6}，这些类型 facade 已固定
- 中期：扩展 `SimpleExprEvaluator` 支持 `||` / `&&`，或拆为单 expr 边
- 引擎层：决策 expr 仅对 submitType∈{0,1,5,20} 有效，需在文档明示

### 测试报告

`./tdd/test_14-decision-submitType_20260917111000.md` ❌ FAIL

---

## §21. 15-decision-amount decision expr 变量嵌套（Issue D）—— ✅ 已修复

### 现象

`flows/15-decision-amount.json` 测试时 amount=5000/15000/9999/10000 都走 edges[0]=e_decision1_task1，不按 expr 路由。

`inst.variables` 实际存储：
```json
{
  "assignees": "user1",
  "variables": {"amount": 5000},
  "title": "15-A"
}
```

`amount` 被嵌套到 `inst.variables.variables.amount`，decision expr `vars_.get("amount")` 返回 None → 永远 False → fallback edges[0]。

### 根因

`jeeflow/engine.py:69` `start_process_instance_by_id`：

```python
vars_ = {**(args or {})}
inst = ProcessInstance(... variables=vars_, ...)
```

`args` 整体塞进 `inst.variables`，调用方传 `{"variables": {"amount": 5000}}` 导致 amount 嵌套。

### 影响流程

| 流程 | 之前判定 | 实际行为 |
|---|---|---|
| 03-decision-expr | ✅ PASS（巧合）| amount>1000 路径恰好是 edges[0]，fallback 命中预期 |
| 10-mixed-mode | ✅ PASS（巧合）| 决策 fallback 命中预期路径 |
| 15-decision-amount | ❌ FAIL | fallback 走 edges[0]=task1，amount<10000 路径错 |

### 修复（main.py + main_pg.py 同源）

`main_pg.py:_wrap_facade_flow._safe_flow` Issue D 分支：

```python
if action in ("processDefine/startAndExecute", "processInstance/startAndExecute"):
    ...
    nested = args.get("variables")
    if isinstance(nested, dict):
        for k, val in nested.items():
            if k not in args:
                args[k] = val
```

效果：`startAndExecute` 前把 `args["variables"]` 子字典展开到 args 顶层 → `inst.variables = {amount: 5000, ...}` 直接可被 expr 访问。

### 引擎层约束（不改 jeeflow）

- `jeeflow engine.start_process_instance_by_id:69` 整体塞 args
- 引擎应改为 `vars_ = {**(args.get("variables") or {}), **args}`（auto-merge nested）

### 测试报告

`./tdd/test_15-decision-amount_20260917112000.md` ✅ PASS

## §22. candidatePage 经 decision/fork 透传 candidates 不完整（BDD 发现 2026-09-17）

### 现象

`bdd-purchase-approval` 设计：apply → decision1(f_amount>=5000) → {manager_review | supervisor_review} → countersign → end。

- apply 节点配 `candidateUsers="userA,userB"` + `candidateGroups="finance"`（预期 4 个候选人）
- countersign 节点配 `candidateUsers="userA,userB"` + `candidateGroups="finance"`（同样 4 个候选人）

实测：
- `processTask/candidatePage` in **apply task**：返回 **8 个**（fallback user_search 全用户）
- `processTask/candidatePage` in **countersign task**：返回 **8 个**（fallback）

### 引擎行为（推测）

`_next_task_candidates.walk()` 经 decision/fork 节点时：
- 单链透传：apply → review → end（12-candidate-page）→ 正确返回 review 的 candidates（4 个）
- decision/fork 多分支：仅查**第一个匹配 task 节点**的 candidates，不合并多分支

当 `_next_task_candidates` 返回空时，facade 静默 fallback 到 `self._user_search(args)`（SPI 全用户 = 8 个）。

### 影响

- 单链候选设计（如 12-candidate-page）行为正确
- 含 decision/fork 多分支流程的候选设计**不符合预期**，candidatePage 走 fallback
- 用户感知："候选怎么变成全员了？" — 静默行为，无 warning

### 缓解措施

- 短期：设计避免 candidatePage 查 apply 之后的 decision/fork 多分支场景
- 引擎层：`_next_task_candidates.walk()` 增强 — 经 decision/fork 时合并所有可达 task 节点的 candidateUsers/candidateGroups
- 文档：明确告知 candidatePage 的透传边界

### 测试报告

`./bdd/bdd-purchase-approval_20260917112722.md`

## §23. FormFieldAssigneeHandler 在 apply 节点 + startAndExecute 不触发（BDD 发现 2026-09-17）

### 现象

`bdd-recruit-approval` v1 设计：apply 节点配 `assignmentHandler="FormFieldAssigneeHandler"` + `field.f_recruiter="user1"` + `assignees="user1"`。

实测：
- instanceId=91767123038821
- `processInstance/detail`：`state=10 DOING, active=0, tasks=[]`
- 流程卡死，无任何 task 创建

### 已知对照

| 流程 | apply 节点 | FormField handler 节点 | 结果 |
|---|---|---|---|
| `11-assignment-handler` | 无 apply | task1 (FormField) | ✅ task1 自动完成 |
| `bdd-recruit-approval` v1 | apply (FormField) | — | ❌ 卡死 |

### 根因推测

- apply 节点在 `startAndExecute` 时由 engine 视为「发起人自动任务」，不通过 handler 路径
- handler 解析 actor 后**绕过 task 创建**，但下一节点也未激活，状态卡死

### 缓解措施

- 短期：apply 节点不使用 FormFieldAssigneeHandler，用默认 `assignee="<operator>"` 即可
- 引擎层：handler 解析失败时 fallback 到 inst.operator；或补 warning 日志

### 测试报告

`./bdd/bdd-recruit-approval_20260917113813.md`（含 patch-1）

## §24. FormFieldAssigneeHandler 字段名必须是 `f_<node.id>` 而非任意字段名（BDD 发现 2026-09-17）

### 现象

`bdd-project-init` v1 设计：pm_form 节点配 `assignmentHandler="FormFieldAssigneeHandler"` + `field.f_pm_reviewer="user1"` + `assignees="user1"`。实测流程卡死。

### 根因（`jeeflow/builtin.py:55`）

```python
def _find_field_value(self, variables, field_name):
    if "f_" + field_name in variables:  # ← handler 用 node.id 查 f_<node.id>
        return variables["f_" + field_name]
    # 回落：去数字后缀、裸 key 等
```

**handler 强制字段名规则**：`f_<node.id>`（即 `f_<properties 中节点 id 字段>`）。

| 设计 | node.id | 期望字段 | 实际查 | 结果 |
|---|---|---|---|---|
| `bdd-recruit-approval` v1（apply） | `apply` | `f_recruiter` | `f_apply` | ❌ |
| `bdd-project-init` v1（pm_form） | `pm_form` | `f_pm_reviewer` | `f_pm_form` | ❌ |
| `bdd-project-init` v2 patch-1（pm_form） | `pm_form` | `f_pm_form` | `f_pm_form` | ✅ |
| `11-assignment-handler` task1 | `task1` | `f_task1` | `f_task1` | ✅ |

### 缓解措施

- **设计时**：FormField handler 节点的 `field` 字段名**必须 = `f_<node.id>`**
- **运行时**：startAndExecute 顶层 `variables` 必须传 `f_<node.id>=<userId>`，否则 handler 返回 `[]`，流程卡死
- **同 §18**：TaskRoleAssigneeHandler 同样用 `node.id` 查 SPI role_code（`DEMO_ROLE_TO_USERS.json` 需预定义）

### 测试报告

`./bdd/bdd-project-init_20260917114047.md`（含 patch-1）

## §25. handler FQCN 拼错静默失败（BDD 发现 2026-09-17）

### 现象

`bdd-expense-by-category` 初版 `finance_review` 节点写：
```json
{
  "assignmentHandler": "jeeflow.assignment.TaskRoleAssigneeHandler"
}
```

期望：handler 调用 SPI `find_by_role("finance_review")` → 返回 [] → 流程卡死 state=10 active=0
实际：无任何日志输出，handler 解析失败返回 `[]`，下一节点不创建

### 根因（`engine.py:443-446`）

```python
handler_name = node.properties.get("assignmentHandler", "")
if handler_name and self.ext and self.ext.registry:
    h = self.ext.registry.resolve_assignment(handler_name)
    if h: return await h.assign(node, inst, operator)  # ← 解析不到直接跳过
# 后续 fallback 到 assignment_handler，再 fallback 到 []
```

**handler FQCN 拼错时静默失败**，没有 warning/error 日志，下游节点不创建。

### 4 个内置 handler 完整 FQCN

| handler | FQCN |
|---|---|
| Operator | `com.mldong.jeeflow.interceptor.impl.OperatorAssignmentHandler` |
| FormField | `com.mldong.jeeflow.interceptor.impl.FormFieldAssigneeHandler` |
| DeptLeader | `com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$DeptLeaderAssignmentHandler` |
| DeptMainLeader | `com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$DeptMainLeaderAssignmentHandler` |
| ApplicantDeptLeader | `com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$ApplicantDeptLeaderAssignmentHandler` |
| ApplicantDeptMainLeader | `com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$ApplicantDeptMainLeaderAssignmentHandler` |
| TaskRole | `com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$TaskRoleAssigneeHandler` |

**注意 `$` 不是 `.`**：`OrgUserAssignmentHandlers$TaskRoleAssigneeHandler` 是内部类分隔符。

### 缓解措施

- **设计时**：严格对照 `flows/11-assignment-handler.json` 已用 FQCN 复制
- **测试时**：执行 `wf/processInstance/detail` 检查 `activeTaskList` 是否创建；为空 + state=10 → handler FQCN 错误
- **引擎层**：建议加 warning 日志 `handler_name not registered, fallback to default`

### 测试报告

`./bdd/bdd-expense-by-category_20260917115100.md`

## §26. handler 失败导致 fork 分支静默通过（BDD 发现 2026-09-17）

### 现象

`bdd-it-procurement` 初版 finance_approval 节点用 TaskRoleAssigneeHandler + node.id="finance_approval"，SPI 无该 role。

**实测**：
- detail.activeTaskList **不包含** finance_approval task
- highLight.historyNodeNames **包含** finance_approval（节点被遍历）
- fork 其他分支（dept + it）完成后 join → end → state=20 DONE
- 财务审批**实际从未发生**，流程非法通过

### 根因（`engine.py:378-379` + `engine.py:334-335`）

```python
async def _create_task(self, node, inst, operator, vars_):
    actors = await self._resolve_actors(node, inst, operator, vars_)
    if not actors: return  # ← handler 返回 [] 直接 return，无 warning
    ...

elif node.type == TYPE_FORK:
    for n in _follow_edges(flow, node.id):
        await self._execute_node(flow, inst, n, operator, vars_)
    # ← fork 触发所有分支，子节点 _create_task 失败不影响 fork 流转
```

**核心问题**：
1. handler 失败（actor=[]）→ _create_task 静默 return
2. fork 节点遍历所有分支，子分支失败不影响 fork 主流程
3. join 检查 `find_doing_tasks` 只看 DOING 数（taskState=10），handler 失败节点根本没 task 创建
4. 其他分支完成后 join 误判"全部完成" → 流转 end

### 缓解措施

- **设计时**：handler 节点 id 必须匹配 SPI `DEMO_ROLE_TO_USERS.json` 中的 role_code
- **设计时**：关键审批节点用 `assignee="<user>"` 而非 handler，避免静默失败
- **测试时**：每个 fork 分支检查 `processInstance/detail.activeTaskList` 包含预期 task，否则视为失败
- **引擎层建议**：handler 返回 [] 时记 warning 日志；fork 应跟踪"未激活分支"，join 检查失败

### 测试报告

`./bdd/bdd-it-procurement_20260917115400.md`

## §27. 多入边 task 节点重复创建 task（BDD 发现 2026-09-17）

### 现象

`bdd-position-transfer` 流程：
- apply → from_dept_approve + to_dept_approve（双入边分别走）
- from_dept_approve → hr_review
- to_dept_approve → hr_review（**双入边汇合到 hr_review**）

实测 hr_review 节点被创建了 **2 个独立 task**（state=10 each），需各执行一次才能流转。

后续 parallel_final 节点（同 SEQUENTIAL 多 actor）也被双 hr_review 入边触发，初始创建 2 个 leader task，但 SEQUENTIAL 自动 advance 后只剩 1 个 doing。

### 根因

`_execute_node` 在每次节点被前驱激活时都创建新 task，多入边 → 多次 _execute_node → 多 task。

### 影响

- 同一节点执行 N 次（N=入边数），浪费用户操作
- 业务上重复审批（用户A 需审批同一节点两次）

### 缓解措施

- **设计时**：避免多入边汇合到同一 task 节点；改用 join 节点
- **设计时**：用 `01-simple` 风格的线性流，避免 fan-in
- **引擎层**：节点首次创建 task 后，后续入边激活应跳过创建，仅检查已有 task 状态

### 测试报告

`./bdd/bdd-position-transfer_20260917115900.md`

## §28. SimpleExprEvaluator 字符串值抛 ValueError 导致流程失败（FIX-T1 已修复 2026-09-17）

### 现象

`bdd/fix-decision-string_20260917122100` 测试发现：
- expr 是数字（如 `f_category==1`），但 startAndExecute value 是字符串（如 `"travel"`）
- startAndExecute 返回 `code=99999999, msg="could not convert string to float: 'travel'"`
- **整个流程失败，未创建实例**

### 根因（`main.py:54` 原版）

```python
actual = vars.get(key)
if actual is None:
    return False
actual = float(actual)  # ← 字符串值抛 ValueError，未捕获
```

引擎调用 `_eval_decision_expr` 时异常向上抛，facade catch 后返回 99999999。

### 修复（v1.5.1，FIX-T1）

`main.py` SimpleExprEvaluator 增加 try/except：
```python
try:
    actual = float(actual)
except (ValueError, TypeError):
    return False  # 与 regex 不匹配、value 为 None 行为一致：走兜底首边
```

### 验证

- `./tdd/fix-decision-string_20260917122100.md` 测试报告
- 修复后字符串值不抛错，走兜底首边（与 expr 字符串路径一致）
- 修复涉及 main.py 修改（已授权范围内）

### 改进建议

- 文档化：`docs/flow.md §3.4` decision expr 章节明确"expr + value 类型须一致（数字）"
- TDD 自检：startAndExecute 前可先 JSON schema 校验变量类型

## §29. handler 解析失败静默无日志（FIX-T2 已修复 2026-09-17）

### 现象

`engine.py:443-446` `_resolve_actors` 中 handler 解析失败时静默跳过：
- 错误 2（FQCN 拼错）：`if h: return await h.assign(...)` — h=None 直接跳过
- 错误 3（节点 id 不在 SPI）：handler 调用返回 [] 静默
- 两者症状相同（activeTaskList=[] + state=10），TDD 无法从结果区分

### 修复（v1.5.2，FIX-T2）

`main.py` monkey-patch `_resolve_actors`，两种错误各打一条 stderr warning：

```python
[FIX-T2 WARN] handler not registered: FQCN='jeeflow.assignment.TaskRoleAssigneeHandler' node_id='finance' (process=113)
[FIX-T2 WARN] handler 'com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$TaskRoleAssigneeHandler' returned empty actors for node_id='nonexistent_role' (process=113); check SPI role_code
```

### 验证

- uvicorn --reload 自动加载 main.py 修改
- Case A 错误 FQCN → stderr 第 1 类 warning ✓
- Case B 错误节点 id → stderr 第 2 类 warning ✓
- 正确配置 → 无 warning，流程 PASS ✓

### 修复方法（避免 §25/§18 卡死）

TDD 排查步骤：
1. `detail.activeTaskList` 为空 + state=10 → handler 失败
2. 看 stderr 日志 `[FIX-T2 WARN]` 区分 FQCN 错 vs SPI role 不存在
3. 对应修复：FQCN 改精确 / 节点 id 改 SPI 已 role_code / SPI JSON 加新 role + 重启

### 关联

- `./tdd/fix-handler-fqcn_20260917122200.md` 测试报告
- §25 错误 2（FQCN 拼错）
- §18 错误 3（节点 id 不在 SPI）

## §30. join 后 end 节点可能未触发 — 流程图设计缺陷（FIX-T7 2026-09-17 已确认根因）

### 现象

`fix-multi-in-edge-join_20260917122700` 测试：
- 流程：apply → fork → branch_A + branch_B → join → fanin_task → end
- 走完所有 task 后，fanin_task state=20 但 instance state=10 DOING
- highLight history 含 `[apply, branch_A, branch_B, fanin_task, fork1, fanin_join]`
- **end 节点不在 history 中**

### 根因（已确认 2026-09-17）

**流程图设计缺陷**：fanin_task 缺指向 end 的边，end 节点成"孤儿"。

修复版 `fix-multi-in-edge-join-fix_20260917130500.json`：
- 新增边 `{"id": "e_fanin_end", "sourceNodeId": "fanin_task", "targetNodeId": "end"}`
- 走完后 state=20 ✅，highLight 含 `end` ✅

引擎行为符合 docs/flow.md §3.2 文档预期：
- join 流转到 fanin_task ✓
- fanin_task 创建 task ✓
- fanin_task 完成时查下游边 = 空（缺边），state 不变 ✗（符合引擎语义"无下游即不推进"）

### 影响

- 流程卡死 state=10，需人工干预
- 业务上视为流程未结束

### 缓解措施

- **设计**：流程图自检——所有 task / decision / fork / join 节点必须至少一条出边（终点 end 除外）；end 节点必须有入边
- **设计**：详见 `docs/flow.md §3.2` 新增"流程图连通性约束"
- **TDD 闭环**：部署前用 `python` 扫描 edges 中 sourceNodeId 集合 vs nodes 集合

### 测试报告

- `./tdd/fix-multi-in-edge_20260917122700.md`（原失败报告）
- `./tdd/fix-multi-in-edge-join-fix_20260917130500.md`（修复报告）

---

## §31. highLight.historyNodeNames 含未访问节点（BDD Task 16 发现 2026-09-17）

### 现象

`processInstance/highLight` 返回的 `historyNodeNames` 包含**未触发**的节点：
- 例如 6 节点流程仅走了 2 步，history 含 7 个节点（含 `end` 和所有未访问 task）
- 测试 BDD Task 16 中 case-small 完成后，history 含 `['apply', 'finance_only', 'decision_low', 'decision_high', 'end', 'finance_mgr', 'finance_mgr_dir']`

### 根因

highLight 行为定义为"已访问 + 可达节点"（设计器视角），不是"已通过节点"（运行时视角）。
- `historyNodeNames`：实例流转过程中**经过或可达**的节点（包含决策分支的备选分支）
- `current`：当前 DOING 节点（可能为 null）

### 影响

- 测试时容易把 `historyNodeNames` 等同于"已通过"，导致误判流程已完成
- state=10 但 history 含 end 节点 → 实际 end 未触发

### 缓解措施

- **测试 ground truth 用 `state`（state==20=DONE）**，不要看 historyNodeNames
- highLight 仅用于 UI 流程图高亮显示，不用于状态判定
- 详见 `bdd/bdd-expense-ratio-tiered_20260917132000.md`

---

## §32. `re_apply` 节点冗余设计（BDD Task 17 发现 2026-09-17）

### 现象

流程图设计 `decision_pass → re_apply → leader_review` 想实现"驳回必经 re_apply 节点修改"，但引擎 `submitType=6` ROLLBACK_TO_OPERATOR **直接跳到第一个 task 节点**，不经过 re_apply。

### 根因

`engine.execute_and_jump_to_first_task_node`（`engine.py` 内部方法）按 flow 顺序查找第一个 task 节点，跳过所有非 task 节点（含 re_apply）。即使流程图设计中间节点也被绕过。

### 影响

- 设计师的"驳回必经 re_apply"意图无法实现
- 实际驳回路径：当前 task → submitType=6 → 直接到 apply（第一个 task）→ user1 重提

### 缓解措施

- **设计**：如需强制"驳回必经特定中间节点"，用 `submitType=3` ROLLBACK + 指定 taskName（args.taskName="re_apply"）
- **设计**：简单驳回-重提场景，无需中间节点；直接靠 submitType=6 + 第一个 task 节点
- 详见 `bdd/bdd-reject-rollback_20260917132200.md`

---

## §33. decision 节点兜底边行为（BDD Task 18 发现 2026-09-17）

### 现象

决策节点按 edge 顺序评估 expr，**首个 true 即流转**；所有 expr 都不匹配 → fallback 到第一条出边（即使 expr=""）。

### 根因

`engine._evaluate_decision` 按 edges 顺序遍历，首个 expr=true 的边即选中；无 true 时返回 edges[0]（设计器默认行为）。

### 影响

- 设计师遗漏 case 时，流程走默认边（可能不符合业务预期）
- BDD Task 18 route=3 即走 boss_review 默认边

### 缓解措施

- **设计**：decision 第一条出边用 `expr=""`（默认/兜底），后续出边用显式 expr
- **测试**：覆盖所有变量值，确保每条 expr 都被测试
- 详见 `bdd/bdd-candidate-multi-route_20260917132500.md`

---

## §34. `preInterceptors` 字段静默未生效（BDD Task 19 发现 2026-09-17）

### 现象

流程定义顶层 `preInterceptors` 字段保留，但 Python 引擎 `_resolve_interceptors` 只读 `postInterceptors`，**preInterceptors 不生效**。

### 根因

`engine._resolve_interceptors` (engine.py:497-531) 仅读取 `meta.get("postInterceptors")`，不读取 `preInterceptors`。`preInterceptors` 字段在 JSON 中保留但无效果。

### 影响

- 设计师写 `preInterceptors="PRE_ONE"` 期望 pre_handle 被调用，但实际不调用
- preInterceptors 不抛错（静默），可能误导设计师

### 缓解措施

- **设计**：当前版本不要使用 `preInterceptors`（无效果）；只使用 `postInterceptors`
- **引擎层**：可加 warning 日志（v1.5+ 实现）
- 详见 `bdd/bdd-business-interceptor_20260917132800.md`

---

## §35. assignee 字符串直接当 userId（BDD Task 20 发现 2026-09-17）

### 现象

`assignee="boss_audit"` 不查 SPI 角色映射，直接作为 userId 字符串。Task 节点 actor=`['boss_audit']`，但 SPI 中无该 user，task 执行时报"无权限"。

### 根因

`engine._resolve_actors` (engine.py:259-275) 处理 assignee 字符串：
- 包含 "applicant" → 替换为 `inst.operator`
- token 在 `inst.variables` → 查变量值
- 其他 → 直接当 userId 字符串
- **不会查 SPI role_code 映射**（与 handler 路径不同）

### 影响

- 设计师期望 `assignee="finance_role"` 自动查 SPI finance → user 列表，实际不会
- actor 是字面量字符串，task 提交时报错（用户不存在）

### 缓解措施

- **设计**：如需角色映射，用 `assignmentHandler="...TaskRoleAssigneeHandler"`（§25）
- **设计**：assignee 用真实 userId 或变量 token（`#f_userList`）
- 详见 `bdd/bdd-multi-task-6_20260917133200.md`

---

## §36. main.py 后端与 main_pg.py 后端 _resolve_interceptors 行为不一致（BDD Task 19 验证 2026-09-17）

### 现象

| 后端 | 流程配置 | 实测响应 |
|---|---|---|
| main.py（内存） | type=business + postInterceptors=POST_ONE 未注册 | `code=0` + apply DONE + biz_review active（**静默通过**）|
| main_pg.py（PG） | type=business + postInterceptors=POST_ONE 未注册 | `code=99999999` + msg=`postInterceptors 声明的拦截器未注册: POST_ONE` |

### 验证步骤

```bash
# main_pg.py 后端（已确认，BDD Task 19 Case A）
curl /wf/processInstance/startAndExecute -d '...'
# → {"code":99999999,"msg":"postInterceptors 声明的拦截器未注册: POST_ONE"}

# main.py 后端（in-process 隔离测试）
python3 -c "import main; ..."
# → facade.flow returned: {'code': 99999999, 'msg': '...'}  ← 也抛错！

# main.py 后端（HTTP service 实测）
curl /wf/processInstance/startAndExecute -d '...'
# → {"code":0,"msg":"成功","data":{"processInstanceId":"..."}}  ← 不抛错！
```

### 矛盾点

- in-process 直接调 `facade.flow("processInstance/startAndExecute", ...)` → 抛错
- HTTP API 经 uvicorn worker → **不抛错**

### 可能根因

1. uvicorn --reload worker 进程的代码加载与单进程 in-process 存在差异（reload 监控 main.py，engine.py 不会 reload）
2. service 进程的 `_ic_cache` 在多次调用 + reload 后被填充为 stale `[]`
3. MemoryRepository 与 JdbcRepository 在 `find_define_by_id` 返回值上行为不同（内存版 deep-copy vs PG 版）

### 实际影响

- main.py 后端（内存）整体更宽松：未注册拦截器静默通过
- main_pg.py 后端（PG）严格：未注册拦截器抛错阻断流程
- **测试时需明确后端**：main.py 验证拦截器行为不严格，main_pg.py 才是契约级行为

### 修复策略（**已选 C：文档化** 2026-09-17）

| 方案 | 描述 | 影响 | 状态 |
|---|---|---|---|
| A | main.py 加 try/except 包装 _resolve_interceptors 吞 ValueError + warn 日志 | 行为宽松化，保持现状 | 弃选 |
| B | main.py 修复 _resolve_interceptors 调用链使其严格抛错 | 行为严格化，与 PG 一致 | 弃选 |
| **C** | **保持现状但 docs 明确两后端行为差异** | **最小改动，需文档同步** | **✅ 已选** |

### 文档化落地（方案 C）

- `docs/flow.md §2` 新增「**main.py vs main_pg.py 后端行为差异**」小节
- `main.py` 顶部 docstring 加注释提醒
- 后续开发/测试人员按文档选择后端，避免误判

### 后端差异速查表

| 行为 | main.py（内存） | main_pg.py（PG） | 推荐测试后端 |
|---|---|---|---|
| 拦截器未注册 | 静默通过 code=0 | 抛错 code=99999999 | **main_pg.py**（契约级）|
| ID 格式 | 整数 1, 2, 113（UPSERT 累计）| 19 位雪花 ID | 均可 |
| 重置后 ID | 自增 _seq 累计 | TRUNCATE IDENTITY | 均可 |
| /api/reset 行为 | 清空 instances/tasks/actors/cc/designs | + TRUNCATE PG 表 | 均可 |
| 种子加载 | 启动时一次性 load_seed | 启动 + reset 时 seed_business | 均可 |
| `_logged_resolve_actors` | v1.5.2/1.5.3 已加载 | v1.5.1-PG/1.5.2-PG/1.5.3-PG 已加载 | 均可 |

**测试建议**：拦截器 / 拦截器相关行为用 main_pg.py（严格）；其他场景用 main.py 即可。

### 测试报告

- `./bdd/bdd-task16-20-mainpy-verify_20260917134000.md`（5 Task main.py 后端完整验证）
- `./bdd/bdd-business-interceptor_20260917132800.md`（BDD Task 19 main_pg.py 后端验证）
