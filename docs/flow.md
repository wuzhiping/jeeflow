# Flow JSON 定义规范

本文档定义 jeeFlow 流程模型 JSON 的结构、字段语义与解析路径。JSON 在设计器面板保存、在引擎驱动流转时被解析执行。

> **📌 2026-09-19 决策**：本项目**独立使用 Python 引擎**，JSON 规范**不再考虑 Java 端兼容**。
> - `custom.methodName` 字段已标记冗余（v1.9.0+）
> - `assignmentHandler` 仅注册简化版 FQCN（v1.9.0+）
> - 节点 id 命名仍保留 `^[A-Za-z0-9_]+$`（理由：JSON key / URL 路由安全，非 Java 兼容）
>
> 详见 `vendor/README.md §8` + `docs/AGENTS.md §6 #2`。

---

## 1. 存储与解析

| 项 | 值 |
| --- | --- |
| 表 | `wf_process_define` |
| 列 | `content TEXT`（见 `docs/pg_schema.sql:12`） |
| 写入 | `POST /wf/processDesign/deploy`（设计器面板）→ `facade._deploy`（`facade.py:204`）`json.loads(content)` 取 `name/displayName/type`，落表 `wf_process_define` |
| 读取 | `POST /wf/processInstance/start` / `complete_task` 等流程动作触发，`engine.py:202` `parse_flow_model(json.loads(def_.content))` 还原 `FlowModel` |
| 范例 | `flows/01-simple.json` ~ `flows/13-countersign-one-vote-veto.json`（15 个真实样例） |

---

## 2. 顶层结构（FlowModel）

来源：`jeeflow/model.py:8-14` + `_KNOWN_MODEL = {name,displayName,type,nodes,edges}`（`model.py:316`）。

**后端选择（2026-09-17 §36 新增）**：
- 本项目提供两个后端入口：`main.py`（内存 / `MemoryRepository`）和 `main_pg.py`（PG / `JdbcRepository`）
- 两者**引擎核心一致**（共享 `jeeflow/engine.py`），但**行为细节有差异**（见下方速查表）
- 详见 `./docs/known-issues.md §36`

| 行为 | main.py（内存） | main_pg.py（PG） | 推荐测试后端 |
|---|---|---|---|
| 拦截器未注册 | **静默通过** code=0 | **抛错** code=99999999 | **main_pg.py** |
| ID 格式 | 整数 1, 2, 113（UPSERT 累计）| 19 位雪花 ID | 均可 |
| reset 行为 | 清 instances/tasks/actors/cc/designs | + TRUNCATE PG 表 | 均可 |
| `v1.5.x` 修复 | main.py 含 v1.5.1/2/3 | main_pg.py 含 v1.5.1-PG/2-PG/3-PG | 均可 |

**测试建议**：
- 拦截器相关行为（postInterceptors/handler FQCN）→ 用 **main_pg.py**（严格抛错，便于发现）
- 其他场景 → main.py 即可

```json
{
  "name": "simple",                          // 流程 key（必填，全局唯一，字母数字下划线）
  "displayName": "简单审批流程",              // 中文名（设计器列表/标题展示）
  "type": "approval",                        // 流程类型，默认 "approval"（facade._deploy 处兜底）
  "instanceUrl": "/form/apply",              // 可选，前端发起跳转路径
  "preInterceptors": "",                     // 可选，前置拦截器（仅 mixed-mode 样例 10-mixed-mode.json 出现）
  "postInterceptors": "",                    // 可选，后置拦截器（同上）
  "nodes": [ ... ],                          // 节点数组
  "edges": [ ... ]                           // 边数组
}
```

`parse_flow_model` 严格过滤未知字段，写入额外键（如设计器 UI 元数据）会被丢弃。

`type` 已知值：`"approval"`（默认）、`"business"`（见 `flows/10-mixed-mode.json`，对应业务流）。`preInterceptors` / `postInterceptors` 当前样例为空串，预留扩展点。

**type=approval vs business（实测 2026-09-17 BDD Task 19）**：
- 引擎对两种 type 处理**无差异**（路由/状态/任务流转一致）
- 仅用于前端 UI 分类 / 报表分类（业务流与审批流视觉区分）
- 测试中两者行为完全一致

**`preInterceptors` 字段状态（2026-09-17 BDD Task 19 实测）**：
- 当前 Python 引擎**静默未生效**（已知问题 §34）：`_resolve_interceptors` 只读 `postInterceptors`
- 写 `preInterceptors` 不会抛错，但无任何效果（pre_handle 不被调用）
- **建议**：当前版本不要使用 preInterceptors，只用 postInterceptors

**`postInterceptors` 字段**：
- 逗号分隔拦截器名 → 从 `engine.ext.interceptor_registry` 取
- 已注册：`pre_handle` 在节点执行前调用（返回 False 阻断流转）；`post_handle` 在节点执行后调用
- **未注册时立即抛 ValueError 阻断流程启动**（engine.py:528）— 不静默跳过

---

## 3. 节点类型与 properties

来源：`jeeflow/model.py:35-41` 七个常量；`engine.py` 各处读 properties。

### 3.1 通用字段

```json
{
  "id": "task1",                             // 节点唯一编码（节点名），必填，跨实例引用
  "type": "snaker:task",                     // 节点类型，见下表
  "x": 300, "y": 200,                        // 设计器坐标
  "properties": { ... },                     // 类型相关属性
  "text": { "value": "上级审批" }            // 节点展示文本
}
```

| type 常量 | 字面量 | 语义 |
| --- | --- | --- |
| `TYPE_START` | `snaker:start` | 起始节点，每流程 1 个 |
| `TYPE_END` | `snaker:end` | 结束节点，允许多个（多分支汇合） |
| `TYPE_TASK` | `snaker:task` | 任务节点（人工审批） |
| `TYPE_DECISION` | `snaker:decision` | 决策/排他网关，按表达式选边 |
| `TYPE_FORK` | `snaker:fork` | 并行分支发起 |
| `TYPE_JOIN` | `snaker:join` | 并行汇合（无活跃任务时放行） |
| `TYPE_CUSTOM` | `snaker:custom` | 自定义节点（外部处理器） |
| `TYPE_CALL_ACTIVITY` | `snaker:callActivity` | 子流程触发节点 (FIX-T73 §3.1.2) |

### 3.7 callActivity 子流程节点 (FIX-T73 §3.1.2)

```json
{
  "id": "sub_flow",
  "type": "snaker:callActivity",
  "properties": {
    "processDefineName": "leave-approval-sub",  // 子流程 name (必填, 按最新版本)
    "assignee": "user2"                         // 子流程发起人 (缺省 = 主流程 operator)
  }
}
```

行为:
1. 引擎查找 `wf_process_define` 中 name = `processDefineName` 的最新一版
2. 启动子实例, parentId = 主实例 id
3. 写 `childInstanceId` 到主实例 vars_[`<node.id>`_childInstanceId]
4. 不阻塞主流程, 立即推进至下游节点
5. 子实例完成时通过 §3.1.1 联动回写主实例 `parentStatus`

约束:
- 子流程必须先于主流程 deploy (引擎启动时按 name 查 definition)
- callActivity 节点属性 `formKey` 可选, 但不强制 (用于子流程表单复用)
- 主流程中可混合 callActivity 与 task/decision, 但 callActivity 不创建 task, 不阻塞流转

§3.1.1 主子状态联动 (FIX-T72): `ProcessInstance.parentStatus` 字段
- `None` (默认, 子未完成)
- `"CHILD_DONE"` (子实例 DONE → state=20)
- `"CHILD_REJECT"` (子实例 REJECT → state=45)

### 3.2 start / end / fork / join

`properties` 通常仅 `{width, height}` 设计器尺寸字段，无业务属性。`start` 是 `engine.execute_process_task` 流程入口锚点；`end` 决定 `inst.finish()` 或 `inst.reject()`（依据 `KEY_SUBMIT_TYPE`，`engine.py:339-349`）。

**流程图连通性约束（2026-09-17 §30 新增）**：

| # | 约束 | 说明 |
| --- | --- | --- |
| 1 | 所有 task / decision / fork / join 节点必须至少有一条出边 | 终点 end 节点除外；无出边的中间节点永不被流转 |
| 2 | end 节点必须至少有一条入边（来自 task / decision / join） | 禁止"孤立 end"——若无任何节点指向，永不触发，实例卡 state=10 |
| 3 | 流程图自检：扫描 `edges` 中 `sourceNodeId` 集合，若某非 end 节点无出边 ⇒ 设计错误 | 见 `./tdd/fix-multi-in-edge-join-fix_20260917130500.md` 反例与修复 |

### 3.3 task 节点 properties

来源：`engine.py:282-313, 377-413` + `flows/01-simple.json`、`flows/05-countersign-parallel.json`、`flows/06-countersign-sequential.json`。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `assignee` | string | 否（与 `assignmentHandler` 互斥） | 处理人解析：`"applicant"`=发起人；`"leader"`=运营占位；逗号分隔多值；或流程变量 token（`f_xxx`/`xxx`，`engine.py:265-275`）|
| `assignmentHandler` | string | 否 | 处理器注册 key（`EngineExtensions.registry` 内 `HandlerRegistry` 注册的 key，FQCN 风格字符串，见 §6） |
| `form` | string | 否 | 表单 key（前端按 key 渲染；空串合法，见 10-mixed-mode.json task3） |
| `taskType` | int | 是 | `0`=主审 `1`=副审（旁审）`2`=记录（`TaskType` 枚举，`model.py:80`）；**FIX-T30 (2026-09-18) 透传落库**；样例 `04-fork-join.json` taskB 与 `10-mixed-mode.json` task3 均用 1 |
| `performType` | int/string | 是 | `0`/ `"0"`=普通，`1`/ `"1"`/`"ALL"`/`"COUNTERSIGN"`=会签；引擎容错解析（`engine.py:382-386`） |
| `countersignType` | string | 会签时必填 | `"PARALLEL"` 并行；`"SEQUENTIAL"` 串行（`engine.py:282, 387`） |
| `countersignCompletionCondition` | string | 否 | 会签完成条件；可放 `properties` 根下，也可放 `properties.field` 内。两种取值：① Activiti 表达式，如 `"#nrOfCompletedInstances==2"`（`flows/07`）；② 常量 `"ONE_VOTE_VETO"` 一票否决（`flows/13`） |
| `candidateUsers` | string | 否 | 候选人名单（逗号分隔）。可直接放 `properties` 根下（`flows/12-candidate-page.json`）也可放 `field` 内（`flows/05/06/07/13`）。前端候选人组件按此过滤 |
| `candidateGroups` | string | 否 | 候选角色组（同上两种位置，逗号分隔） |
| `field` | object | 否 | 字段集合：可放 `candidateUsers` / `candidateGroups` / `countersignCompletionCondition` / `PERMISSION_xxx`（任务字段权限，1=只读、2=隐藏，见 §5） |

**assignee 解析规则（实测 2026-09-17 §35）**：
- `"applicant"` → `inst.operator`（流程发起人）
- `inst.variables` 中存在的 key → 查变量值（list/tuple 展开）
- 其他字符串 → **直接当 userId**（**不查 SPI 角色映射**）
- 多值：逗号分隔，逐个解析
- 角色映射仅通过 `assignmentHandler="...TaskRoleAssigneeHandler"` 实现（§25）

**actor 复用（实测 2026-09-17 BDD Task 20）**：
- 同一 userId 可在不同 taskName 节点分别作为 actor
- assignee 在每个节点独立解析
- BDD Task 20 中 leader 在 team_lead 和 hr_review 节点各处理一次（taskName 不同）

**candidateUsers/candidateGroups 行为（实测 2026-09-17 BDD Task 18 + 21）**：
- **仅用于后继任务节点选人**（`processTask/candidatePage` API，**非当前任务**）
- **不参与 actor 解析**（actor 仍由 assignee / handler 决定）
- 测试时 actor 必须是真实 user id（如 `leader`），不能是占位字符串

**candidatePage API 实际语义（实测 2026-09-17 §37）**：
- 必传参数 `processTaskId`（当前任务 ID）
- **不是**按 operator 查候选任务（operator 参数不影响结果）
- 行为：查当前任务**后继节点**的 candidateUsers/candidateGroups
- 后继节点无 candidate 字段 → 回落 user_search 钩子（返回 SPI 全量用户）
- 用于前端"任务完成后下一步选人组件"，不要用于"我的待办"

**submitType 路由（实测 2026-09-17 BDD Task 17）**：

| submitType | 值 | 引擎行为 | 用途 |
|---|---|---|---|
| APPLY | 0 | execute_process_task | startAndExecute 自动注入 |
| AGREE | 1 | execute_process_task | 同意/通过 |
| REJECT | 2 | execute_and_jump_to_end | 驳回 → state=45 |
| ROLLBACK | 3 | execute_and_jump_task | 跳到指定 taskName（需 args.taskName） |
| RE_APPLY | 5 | execute_process_task | 重提（语义同 AGREE） |
| ROLLBACK_TO_OPERATOR | 6 | execute_and_jump_to_first_task_node | 跳到流程图第一个 task 节点 |
| COUNTERSIGN_DISAGREE | 20 | execute_process_task + disagreeFlag | 会签否决（ONE_VOTE_VETO 场景） |

注意：`submitType=2` REJECT **不走 decision**，facade 拦截后直接调 `execute_and_jump_to_end`（state=45）；decision 节点只看 submitType 1/5/20（其他 fallback 到首边）。

**比例会签（N/M 通过）扩展（实测 2026-09-17 BDD Task 16）**：
- `countersignType=PARALLEL` + `countersignCompletionCondition="#nrOfCompletedInstances>=K"`
- 每次 task 完成时 evaluate 表达式；true → **abandon 剩余 DOING**（taskState=99 ABANDON）+ 推进下游
- RatioCapableEngine 扩展（`main_pg.py:93-155`）

### 3.4 decision 节点 properties

`engine._evaluate_decision`（`engine.py:_evaluate_decision`）按出边 `properties.expr` 依次求值，第一个真值即沿该边。`properties.expr` 可空（默认边）。

> **历史字段**：`handleClass` 是 v1.0.x 时期预留的扩展点字段（Java 反射式 decision handler）。Python 引擎 v1.9.0 起**不再使用**该字段；如需扩展决策逻辑，参考 `custom` 节点（§3.5）+ `EngineExtensions.decision_handler`。

> 已知：Python 引擎 `_evaluate_decision` **不调用 `IDecisionHandler`**（register_decision 无效）。详见 `./known-issues.md §46`。要实现多条件路由请用嵌套 decision + expr。

**decision 兜底边（实测 2026-09-17 §33）**：
- 决策节点按 edge 顺序评估 expr，首个 true 即流转
- 所有 expr 都不匹配 → **fallback 到第一条出边**（即使 `expr=""`）
- 设计建议：第一条出边用 `expr=""`（默认/兜底），后续出边用显式 expr

**多条件分支处理（实测 2026-09-17 BDD Task 16）**：
- `SimpleExprEvaluator` 不支持 `&&` / `||`，单 expr 仅单 key op number
- 多条件需用**多层 decision 串接**（decision_low → decision_high → ...）
- 详见 §3.4 expr 约束 + 多层 decision 样例 `bdd/bdd-expense-ratio-tiered_20260917132000.json`

**decision 与 submitType 路由（实测 2026-09-17 BDD Task 17）**：
- decision 节点只看 submitType 1/5/20（其他 fallback 到首边）
- submitType=2 REJECT 不走 decision，facade 拦截后直接 `execute_and_jump_to_end`（state=45）
- submitType=6 ROLLBACK_TO_OPERATOR 不走 decision，直接跳到流程图第一个 task 节点

> ✅ **决策 expr 实测约束（2026-09-17 已解决）**：
> - `SimpleExprEvaluator.eval`（`main_pg.py:71-89`）严格匹配正则 `^\s*(\w+)\s*(>=|<=|!=|==|>|<)\s*(\d+(?:\.\d+)?)\s*$`
> - 不支持 OGNL 路径（`#variables.*` / `variables.*`）、字面量比较（`1==1`）、字符串字面量（`"yes"=="yes"`）；不匹配直接返回 False
> - 变量必须直接存在于 `vars_` 顶层：`vars.get(key)` 不展开嵌套字典
> - **正确写法**：业务变量（`amount`、`days`、`leaveType` 等）放在 `startAndExecute` 顶层（与 `processDefineId`/`operator`/`title`/`assignees` 同级），**不要放在 `variables` 内**：
>   ```jsonc
>   // ❌ 错误
>   {"variables": {"amount": 500, "submitType": 0}}
>   // ✅ 正确
>   {"amount": 500, "variables": {"submitType": 0, "u_userId": "applicant", "u_realName": "申请人"}}
>   ```
> - **回退顺序**：所有 expr False → 取第一条无 expr 的边（默认边）→ 取第一条边

### 3.5 custom 节点 properties

来源：`flows/08-custom-node.json` + 引擎入口（`engine.py:_execute_node` 拆出 `TYPE_CUSTOM` 分支 → `_execute_custom_node`）。

> ✅ **v1.9.0 FIX-T38 已实现**：custom 节点通过 `EngineExtensions.custom_handler_registry` 调度，handler 签名 `async def(node, inst, vars_, args) -> Any`。详见 `known-issues.md §16` + `tdd/test_fix37_fix38_20260919_143000.md`。

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `clazz` | 是 | handler 注册 key（在 `EngineExtensions.custom_handler_registry` 注册的字符串，可 FQCN 风格或自定义短名） |
| `methodName` | 否 | 冗余字段（保留向前兼容，无业务语义） |
| `args` | 否 | 入参字符串（handler 自行解析为 dict/JSON/逗号分隔/任意格式） |
| `val` | 否 | 返回值写入变量名（缺省不写；`result is None` 也不写） |

**行为**：
1. 触发前后调 `_fire_pre` / `_fire_post` 拦截器（同其他节点）
2. 调 `handler(node, inst, vars_, args)` → 写回 `vars_[val]`
3. **不创建 task**，直接 `_follow_edges` 推进下游
4. handler 抛错向上冒泡（不静默）
5. handler 未注册 / `clazz` 缺省 → 抛 `ValueError`（v1.8.0 之前静默，FIX-T17 改进）

**注册示例**（`main_common.py:build_custom_handlers`）：
```python
def build_custom_handlers() -> dict:
    return {
        "com.mldong.jeeflow.test.TestCustomHandler": _builtin_custom_test_handler,
    }
```

---

## 4. 边（FlowEdge）

来源：`jeeflow/model.py:26-31` + `engine.py:355-375`。

```json
{
  "id": "e3",
  "sourceNodeId": "decision1",
  "targetNodeId": "task2",
  "properties": {
    "expr": "amount > 1000"                   // decision 出边：条件表达式
  },
  "text": { "value": "金额>1000" }            // 边标签（设计器展示，可选）
}
```

`expr` 仅对 `snaker:decision` 出边生效，引擎按顺序求值。`engine._evaluate_decision` 兜底：无 expr 边 → 默认路径；全失败 → 首条边。

> SimpleExprEvaluator 仅支持 `#var <op> number`（FIX-T1 v1.5.1）和 `#var==str`/`#var!=str`（FIX-T3 v1.6.0）。多条件须嵌套 decision 串联，详见 `./known-issues.md §33 / §47`。

`properties` 可省略或置 `{}`（`flows/10-mixed-mode.json` 多条非 decision 边）；`text` 可省略。

---

## 4a. 命名约定（来自样例）

**节点 id**：

| 样例 | 命名 |
| --- | --- |
| `flows/01-02-09-11-12` | `apply`（申请人填报，必备）+ `task1`（或 review 等语义名） |
| `flows/02-multi-task` | `apply` → `task1` → `task2` → `task3` → `end`（线性递增） |
| `flows/03-decision-expr` | `decision1`（决策网关统一后缀） |
| `flows/04-fork-join` | `fork1` / `join1`（分支/合并） |
| `flows/04-fork-join` | `taskA` / `taskB`（并行分支字母命名） |
| `flows/08-custom-node` | `custom1`（自定义节点） |
| `flows/05/06/07/13` | `task1`（会签任务，assignee 多值） |
| `flows/12-candidate-page` | `apply` + `task1`（流程 key 是 `candidate-flow`） |

**边 id**：

| 样例 | 命名 |
| --- | --- |
| `flows/01/02/03/09/11` | `e1`, `e2`, `e3` 递增 |
| `flows/04-fork-join` | `e_apply_1`, `e_apply_2`, `e_fork1_1`, `e_join1_1`（源节点+序号） |
| `flows/05-countersign-parallel` | `e1`, `e2`, `e3`（线性会签也是递增） |

边 id 跨实例不要求唯一，引擎按 `(sourceNodeId, targetNodeId)` 查表，id 仅作设计器索引。

---

## 5. 字段权限（field.PERMISSION_）

任务节点 `properties.field.PERMISSION_<fkey>` 控制办理界面字段读写，参考 `flows/01-simple.json:49-52`：

> PERMISSION_* 字段仅作元数据透传，引擎不做强制校验（前端控制）。详见 `./known-issues.md §49`。

```json
"field": {
  "PERMISSION_f_leaveType": 1,                // 1=只读
  "PERMISSION_days": 2                        // 2=隐藏
}
```

引擎在 `execute_process_task`（`engine.py:200-203`）按 `PERMISSION_` 前缀过滤提交入参 `_filter_field_by_perm`，只读/隐藏字段不进入实例变量。

### 5.1 权限码语义（FIX-DOC-1 2026-09-18）

| 权限码 | 含义 | 引擎行为 |
|--------|------|----------|
| `1` | 只读 | 提交时该字段被剔除，实例变量保留原值 |
| `2` | 编辑 | 提交时该字段正常写入实例变量 |
| `3` | 隐藏 | 提交时该字段被剔除，**实例变量也不可见**（前端不回传） |

### 5.2 JSON key 规范（FIX-DOC-1）

⚠️ **关键**：`field` 节点下 key **必须**以 `PERMISSION_` 前缀开头，否则引擎**完全忽略**该字段。

```json
// ✅ 正确格式
"field": {
  "PERMISSION_f_amount": "1",  // 只读
  "PERMISSION_f_secret": "2"   // 编辑
}

// ❌ 错误格式（直接写 f_xxx：引擎不识别，权限完全失效）
"field": {
  "f_amount": "1",
  "f_secret": "2"
}
```

引擎代码 `engine.py:_filter_field_by_perm`：

```python
perm = field_perm.get(f"PERMISSION_f_{name}")  # 必须是 PERMISSION_f_xxx
if perm is None:
    perm = field_perm.get(f"PERMISSION_{name}")  # 兼容 PERMISSION_xxx（去 f_ 前缀）
```

实测 6 项断言（双端 PASS）见 `./known-issues.md §82`。

### 5.3 委托代理（surrogate）

> ⚠️ 当前实现缺自动展开：委托关系**不影响** `processTask/todoList` 的 actor 过滤，需手动 `processTask/surrogate` addCandidate。

**API**：
- 创建委托：`/wf/processSurrogate/save` `{operator, surrogate, processName, startTime, endTime, enabled}`
- 我的委托：`/wf/processSurrogate/page` `{operator, pageNum, pageSize}`
- 委托 addCandidate：`/wf/processTask/surrogate` `{processTaskId, actorIds}`（与 `addCandidate` 等价）

**委托 ≠ 自动代办**：userA 委托给 userB 后，userB 仍需调用 surrogate addCandidate 才能在 todoList 看到 userA 的任务。

详细测试见 `./known-issues.md §82`。

---

## 6. 参与者处理器（assignmentHandler）

`flows/11-assignment-handler.json` 给出全部内置处理器（注册 key 在 `EngineExtensions.registry` / `HandlerRegistry`，`builtin.py:13-22`）：

| 处理器 | 行为 |
| --- | --- |
| `com.mldong.jeeflow.interceptor.impl.OperatorAssignmentHandler` | 兜底 `inst.operator`（发起人） |
| `com.mldong.jeeflow.interceptor.impl.FormFieldAssigneeHandler` | 按 `f_<nodeId>` / `<nodeId>` / 去数字后缀匹配表单字段值 |
| `…OrgUserAssignmentHandlers$DeptLeaderAssignmentHandler` | 当前操作人部门领导 |
| `…OrgUserAssignmentHandlers$DeptMainLeaderAssignmentHandler` | 操作人部门分管领导 |
| `…OrgUserAssignmentHandlers$ApplicantDeptLeaderAssignmentHandler` | 发起人部门领导 |
| `…OrgUserAssignmentHandlers$ApplicantDeptMainLeaderAssignmentHandler` | 发起人部门分管领导 |
| `…OrgUserAssignmentHandlers$TaskRoleAssigneeHandler` | 按角色（`roleCode = nodeId`） |

**多 handler 链路设计（实测 2026-09-17 §38 / BDD Task 22）**：

不同 handler 可在同一流程串联，每个节点独立解析 actor：

| 节点 id | handler | SPI / 字段要求 |
|---|---|---|
| `finance` | TaskRole | node.id="finance" 匹配 SPI DEMO_ROLE_TO_USERS.finance=['leader','manager'] |
| `approver` | FormField | node.id="approver" 查 `vars.f_approver="userB"` |
| `deptleader` | DeptLeader | node.id 任意（不影响解析），SPI find_dept_leaders + operator.u_deptId |

**关键约束**：
1. handler FQCN 必须精确（拼错静默失败 / FIX-T2 warning）
2. 节点 id 与 SPI role_code / 字段名一致（`f_<node.id>` 字段名约束 §24）
3. actor 多值但 performType=0 → 引擎接受多 actor 列表但只创建 1 个 task（**非会签**）
4. handler 链路独立性：每个 handler 解析自己的 actor，前一个不影响后一个
5. SPI data.py 模块级 dict 启动时一次性加载，修改 JSON 后**必须重启服务**才生效（§17）

---

## 7. 引擎变量 KEY（系统前缀）

来源：`jeeflow/engine.py:8-40`，实例 variables 中以这些 key 流转：

| 常量 | 值前缀 | 含义 |
| --- | --- | --- |
| `KEY_SUBMIT_TYPE` | `submitType` | 提交类型（`SubmitType` 枚举） |
| `KEY_BUSINESS_NO` | `businessNo` | 业务流水号 |
| `KEY_USER_ID` / `KEY_REAL_NAME` / `KEY_DEPT_ID` / `KEY_DEPT_NAME` / `KEY_POST_ID` / `KEY_POST_NAME` | `u_` 前缀 | 当前操作人/发起人信息（issues/97：操作人 u_* 不写回实例） |
| `KEY_NEXT_NODE_OPERATOR` | `tf_` 前缀 | 下一节点动态指定处理人（最高优先级，覆写 assignee） |
| `KEY_PROCESS_START_NEXT_NODE_OPERATOR` | `f_` 前缀 | 流程发起时下一节点指定处理人 |
| `KEY_AUTO_ID` | `flow.auto` | 自动发起人 ID |
| `KEY_ADMIN_ID` | `flow.admin` | 管理员 ID |
| `KEY_AUTO_GEN_TITLE` | — | 自动生成标题开关 |

---

## 7a. SubmitType 路由矩阵

`SubmitType` 是实例变量 `submitType` 的枚举值（`vendor/jeeflow/model.py:69-78`，**可修改但需测后**），决定任务节点执行后路由走向。

> ROLLBACK 重审机制详见 `./known-issues.md §52`，submitType=2 REJECT → state=45 详见 §43。

| submitType | 字面含义 | 引擎行为 | 实测终态（`processInstance/detail.state`） | 备注 |
| --- | --- | --- | --- | --- |
| 0 | 发起 / 开始 | `startAndExecute` 内部自动注入 | `state=20`（DONE） | 唯一合法 APPLY 路径；客户端禁止直接传 0（详见 §10 bug #1） |
| 1 | 同意 / 批准 | 直达下一节点；遇 end 触发 `inst.finish()` | `state=20` | 最常见 |
| 2 | 驳回（拒绝） | 遇 end 触发 `inst.reject()` | `state=45`（REJECT） | 标记实例 REJECT |
| 3 | 退回 | 跳回首任务节点 `apply` | `state=10`（DOING，活跃任务=apply） | 重新激活 apply |
| 5 | 转发 / 转办 | 改派下一节点处理人 | `state=20`（经下一节点） | 通常配合 `tf_<nodeId>` |
| 6 | 退回发起人 | 跳回 `apply` | `state=10`（DOING） | 与 submitType=3 等价路径 |
| 20 | 提交 / 继续 | 直达下一节点 | `state=20` | 与 submitType=1 同义 |

实测端点：

| 场景 | 端点 | 备注 |
| --- | --- | --- |
| 起批 + 首节点同意 | `POST /wf/processInstance/startAndExecute` | body `variables.submitType=1` 模拟首节点同意；submitType=0 由 facade 内部注入 |
| 中间节点同意/驳回/退回 | `POST /wf/processInstance/execute` | body 含 `processTaskId` + `submitType` |

实测来源：`./tdd/test_demo-single-approval-reject_20260917075915.md`（5/5 PASS）。

约束：

- ⚠ 客户端禁止直接传 `submitType=0`；facade 强制改写为 1（见 §10 bug #1）。合法客户端提交：`1`/`2`/`3`/`5`/`6`/`20`。
- ⚠ `state=20` 是 `processInstance/detail.state` 字段（`InstanceState.DONE`），实测 `detail.finish_state` 字段整个生命周期恒为 null（弃用）。完整枚举见 `./docs/state.md`。

---

## 8. 完整样例索引

| 文件 | 演示场景 | 关键字段 |
| --- | --- | --- |
| `flows/01-simple.json` | start → apply → task1 → end（4 节点） | `field.PERMISSION_f_leaveType:1, PERMISSION_days:2` |
| `flows/02-multi-task.json` | 多任务节点串行 | `apply→task1→task2→task3→end`，三 task 各自 assignee |
| `flows/03-decision-expr.json` | 决策节点 + 出边 `expr` | `decision1` 出 `amount>1000` / `amount<=1000` |
| `flows/04-fork-join.json` | 分支/合并（taskB 副审） | `fork1→taskA/taskB→join1`，taskB `taskType:1` |
| `flows/05-countersign-parallel.json` | 并行会签 | `performType=1, countersignType=PARALLEL`，assignee `userA,userB` |
| `flows/06-countersign-sequential.json` | 串行会签 | `countersignType=SEQUENTIAL` |
| `flows/07-countersign-ratio.json` | 比例会签 | `countersignCompletionCondition: "#nrOfCompletedInstances==2"`（放 `field` 内） |
| `flows/08-countersign-sequential-approve.json` | 串行会签 + 后接 approve 任务 | `task1` 串行会签后并联 `approve` 出边 |
| `flows/08-custom-node.json` | custom 节点（`clazz/methodName/args/val`） | `custom1` 触发 `execute()`，结果写变量 |
| `flows/09-with-reject.json` | 驳回路径 | apply→task1→end，task1 可 reject |
| `flows/10-mixed-mode.json` | 混合模式（`type:"business"`） | 顶层 `preInterceptors/postInterceptors`；task3 `taskType:1`；含 custom1 |
| `flows/11-assignee-vars.json` | assignee 变量解析 | `assignee: "deptLeader"`、`"userA,userB"` 等变量 token |
| `flows/11-assignment-handler.json` | 全部内置 `assignmentHandler` | 列示 7 个 FQCN，与 §6 对应 |
| `flows/12-candidate-page.json` | 候选人分页（flow key=`candidate-flow`） | 节点级 `candidateUsers/candidateGroups`（properties 根下） |
| `flows/13-countersign-one-vote-veto.json` | 一票否决会签 | `countersignCompletionCondition: "ONE_VOTE_VETO"` |

---

## 9. 速查表

| 关注点 | 字段/位置 |
| --- | --- |
| 流程 key | 顶层 `name` |
| 流程类型 | 顶层 `type`（默认 `approval`，可选 `business`） |
| 拦截器 | 顶层 `preInterceptors/postInterceptors`（当前样例空串，预留） |
| 节点编号 | `node.id`（任务 taskName 等于 nodeId） |
| 处理人 | `node.properties.assignee` 或 `assignmentHandler` |
| 会签配置 | `performType=1` + `countersignType=PARALLEL/SEQUENTIAL`；完成条件放 `properties` 根或 `field` 下 |
| 候选人 | `node.properties.candidateUsers/candidateGroups`（根或 `field` 下，逗号分隔） |
| 决策条件 | `edge.properties.expr`（decision 出边） |
| 表单 key | `node.properties.form`（可空串） |
| 字段权限 | `node.properties.field.PERMISSION_<fkey>`（1=只读，2=隐藏） |
| 动态指定处理人 | 变量 `tf_<nodeId>`（执行时）、`f_<nodeId>`（发起时） |
| 实例变量合并 | `KEY_SUBMIT_TYPE`、`f_*`、`u_*`（发起人持久化、操作人不持久化） |

---

## 10. 已知问题集中登记

本节集中登记引擎行为约束、facade bug、运维约定等已知问题，便于后续维护时检索。所有条目**仅文档记录，不可改源码**。

| # | 问题 | 影响范围 | 替代方案 / 缓解措施 | 来源 |
| --- | --- | --- | --- | --- |
| 1 | facade `submitType=0` 被强制改为 `1`（`X or Y` falsy trap，`facade.py:300`） | 客户端无法直接 `submitType=0` | 仅经 `startAndExecute`（内部自动注入 0）；客户端合法提交：`1`/`2`/`3`/`5`/`6`/`20` | `./venv/.../jeeflow/facade.py:300`（仅记录） |
| 2 | `_follow_edges` 不解析 `expr`（`engine.py:557-558`） | 非 `snaker:decision` 节点出边 `expr` 被静默忽略 | `expr` 仅放 `snaker:decision` 出边；其他节点出边保持空 `properties` | `./venv/.../jeeflow/engine.py:557-558`（仅记录） |
| 3 | `u_*` 操作人不持久化到实例变量（`KEY_USER_ID` 等） | 跨节点操作人无法在 `wf_process_instance.variables` 追溯 | 流程上下文内置，但不落盘；如需追溯，改用 `wf_process_task.actor` | `./venv/.../jeeflow/engine.py:8-40`（仅记录） |
| 4 | 服务 stdout 走 `/dev/pts/42` 未落盘 | 离线排查异常栈受限 | 测试日志落到 `./tdd/test_<key>_<YYYYMMDDHHMMSS>.md`（见 `./tdd/README.md`） | 运维约定 |
| 5 | `flows/09-with-reject.json` 文件名误导 | 实为线性流（`apply→task1→end`），驳回靠引擎自动 ROLLBACK；不是"含驳回节点的流程图" | 不重命名（避免破坏外部引用），在 `./flows/README.md`（待补）加注说明 | `./flows/09-with-reject.json` |
| 6 | 状态码双义：`detail.finish_state` 恒为 null（弃用），`detail.state` 才是 `InstanceState` 枚举（DONE=20/REJECT=45/DOING=10 等） | 客户端易混 | 只看 `detail.state`；枚举见 `./docs/state.md` §3 | `./venv/.../jeeflow/model.py:45-52`（仅记录） |
| 7 | 决策出边 `expr` 兜底逻辑 | 全失败 → 首条边；无 expr → 默认边 | 设计 decision 路由时务必保证至少一条边可命中（含默认边） | `./venv/.../jeeflow/engine.py:353-369`（仅记录） |
| 8 | `flows/` 现有 JSON 不可改 | 01-13 已固化（含两个 `11-`），所有改动走新增 + 晋升路径 | 新流程 JSON 先落 `./tdd/<key>.json`，测试稳定后 `cp` 晋升 `./flows/<key>.json` | `./flows/`（项目约定） |

> 表格中"来源"列若引用源码行号，仅作历史定位参考，**禁止回读源码**，所有字段语义以本文档和 `./docs/actions.md` 为准。
---

