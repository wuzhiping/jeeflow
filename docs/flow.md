# Flow JSON 定义规范

本文档定义 jeeFlow 流程模型 JSON 的结构、字段语义与解析路径。JSON 在设计器面板保存、在引擎驱动流转时被解析执行，跨 Python/Java 通用。

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

### 3.2 start / end / fork / join

`properties` 通常仅 `{width, height}` 设计器尺寸字段，无业务属性。`start` 是 `engine.execute_process_task` 流程入口锚点；`end` 决定 `inst.finish()` 或 `inst.reject()`（依据 `KEY_SUBMIT_TYPE`，`engine.py:339-349`）。

### 3.3 task 节点 properties

来源：`engine.py:282-313, 377-413` + `flows/01-simple.json`、`flows/05-countersign-parallel.json`、`flows/06-countersign-sequential.json`。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `assignee` | string | 否（与 `assignmentHandler` 互斥） | 处理人解析：`"applicant"`=发起人；`"leader"`=运营占位；逗号分隔多值；或流程变量 token（`f_xxx`/`xxx`，`engine.py:265-275`） |
| `assignmentHandler` | string | 否 | 处理器全限定类名（Java 类名约定，跨语言通用，见 §6） |
| `form` | string | 否 | 表单 key（前端按 key 渲染；空串合法，见 10-mixed-mode.json task3） |
| `taskType` | int | 是 | `0`=主审 `1`=副审（旁审）`2`=记录（`TaskType` 枚举，`model.py:80`）；样例 `04-fork-join.json` taskB 与 `10-mixed-mode.json` task3 均用 1 |
| `performType` | int/string | 是 | `0`/ `"0"`=普通，`1`/ `"1"`/`"ALL"`/`"COUNTERSIGN"`=会签；引擎容错解析（`engine.py:382-386`） |
| `countersignType` | string | 会签时必填 | `"PARALLEL"` 并行；`"SEQUENTIAL"` 串行（`engine.py:282, 387`） |
| `countersignCompletionCondition` | string | 否 | 会签完成条件；可放 `properties` 根下，也可放 `properties.field` 内。两种取值：① Activiti 表达式，如 `"#nrOfCompletedInstances==2"`（`flows/07`）；② 常量 `"ONE_VOTE_VETO"` 一票否决（`flows/13`） |
| `candidateUsers` | string | 否 | 候选人名单（逗号分隔）。可直接放 `properties` 根下（`flows/12-candidate-page.json`）也可放 `field` 内（`flows/05/06/07/13`）。前端候选人组件按此过滤 |
| `candidateGroups` | string | 否 | 候选角色组（同上两种位置，逗号分隔） |
| `field` | object | 否 | 字段集合：可放 `candidateUsers` / `candidateGroups` / `countersignCompletionCondition` / `PERMISSION_xxx`（任务字段权限，1=只读、2=隐藏，见 §5） |

### 3.4 decision 节点 properties

`engine._evaluate_decision`（`engine.py:353-375`）按出边 `properties.expr` 依次求值，第一个真值即沿该边。`properties.expr` 可空（默认边），`handleClass` 兼容 Java 扩展点（样例 03-decision-expr.json 与 10-mixed-mode.json 均保留 `"handleClass": ""` 占位，当前未触发，留作后续扩展）。

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

来源：`flows/08-custom-node.json` + 引擎入口（`TYPE_CUSTOM` 与 `TYPE_TASK` 共用 `_create_task`，但 custom 不建任务，触发外部处理器）。

> ⚠️ **实测（2026-09-17 复测 08-custom-node）**：引擎**未实现** `clazz/methodName/args/val` 四个字段的反射调用。custom 节点被当 task 处理，要求 `assignee`/`assignmentHandler` 解析 actors；否则 `_create_task` 在 actors=[] 时 return，流程卡死。详见 `./known-issues.md` §16 + `./tdd/test_08-custom-node_20260917101500.md`。

| 字段 | 说明 |
| --- | --- |
| `clazz` | 外部处理器类全限定名（Java 约定） |
| `methodName` | 调用方法名 |
| `args` | 入参（字符串，可为流程变量） |
| `val` | 返回值写入变量名 |

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

```json
"field": {
  "PERMISSION_f_leaveType": 1,                // 1=只读
  "PERMISSION_days": 2                        // 2=隐藏
}
```

引擎在 `execute_process_task`（`engine.py:200-203`）按 `PERMISSION_` 前缀过滤提交入参 `_filter_field_by_perm`，只读/隐藏字段不进入实例变量。

---

## 6. 参与者处理器（assignmentHandler）

`flows/11-assignment-handler.json` 给出全部内置处理器全限定名（与 Java 类名一致，`builtin.py:13-22`）：

| 处理器 | 行为 |
| --- | --- |
| `com.mldong.jeeflow.interceptor.impl.OperatorAssignmentHandler` | 兜底 `inst.operator`（发起人） |
| `com.mldong.jeeflow.interceptor.impl.FormFieldAssigneeHandler` | 按 `f_<nodeId>` / `<nodeId>` / 去数字后缀匹配表单字段值 |
| `…OrgUserAssignmentHandlers$DeptLeaderAssignmentHandler` | 当前操作人部门领导 |
| `…OrgUserAssignmentHandlers$DeptMainLeaderAssignmentHandler` | 操作人部门分管领导 |
| `…OrgUserAssignmentHandlers$ApplicantDeptLeaderAssignmentHandler` | 发起人部门领导 |
| `…OrgUserAssignmentHandlers$ApplicantDeptMainLeaderAssignmentHandler` | 发起人部门分管领导 |
| `…OrgUserAssignmentHandlers$TaskRoleAssigneeHandler` | 按角色（`roleCode = nodeId`） |

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

`SubmitType` 是实例变量 `submitType` 的枚举值（`jeeflow/model.py:45-52`，仅文档记录，不可改），决定任务节点执行后路由走向。

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