# 用户指南 02 · 流程定义

> **来源**：https://jeeflow-doc.mldong.com/guides/02-flow-definition
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的流程 JSON 编写参考。
> **裁剪记录**：§1 / §4 原文保留；§2.1 / §2.2 / §2.3 / §2.3.1 / §2.4 / §2.5 / §3 / §5 / §6 保留并加本仓对齐注解；§7 设计器整段裁剪（本项目不输出 UI）。

> **与其他流程文档的关系**（避免重复维护）：
> - 本文档 = **设计者视角入门**（10 节流程 JSON 写法 + 例子），249 行
> - **机器视角完整规范**（存储 / 字段枚举 / 解析路径，684 行）→ 见 [`docs/flow.md`](../../../../docs/flow.md)
> - **5 个本仓典型模式**（多级 / 跳转 / 会签 / 驳回 / 条件分支）→ 见 [`../patterns/`](../patterns/)
>
> **何时更新本文**：JSON 写法有新模式时；字段定义变化 → 改 `docs/flow.md`，本文只引用。

---

## 1. 顶层结构

```json5
{
  "name": "leave",           // 流程编码（唯一）
  "displayName": "请假审批",  // 流程显示名称
  "type": "approval",        // 流程类型
  "nodes": [...],            // 节点列表
  "edges": [...]             // 边列表
}
```

---

## 2. 节点编写规范

### 2.1 流程骨架（必守 3 条）

```
1. 只有一个 start（snaker:start）
2. 只有一个 end（snaker:end）——分支必须汇合到同一个结束节点
3. start 后第一个任务节点必须是"发起申请"节点：
   assignee = "applicant"（引擎解析为发起人）
```

> **本仓补充第 4 条**（FIX-T34 deploy 校验）：**节点 id 必须严格匹配 `^[A-Za-z0-9_]+$`**——禁止空格 / `-` / 中文 / 特殊字符。理由：JSON key / URL 路由 / SQL 列名三处皆依赖此正则。详见 `../docs/known-issues.md §93`。

### 2.2 节点类型

| type | 必填 properties | 说明 |
|---|---|---|
| `snaker:start` | - | 开始 |
| `snaker:end` | - | 结束 |
| `snaker:task` | `assignee` 或 `assignmentHandler` | 任务节点 |
| `snaker:decision` | 出边 `expr` | 条件分支 |
| `snaker:fork` | - | 并行分支 |
| `snaker:join` | - | 并行合并 |
| `snaker:custom` | `customClass` | 自定义节点 |
| `snaker:subprocess` | `subProcessKey` | 子流程 |

> **本仓节点类型映射**：上游 `snaker:subprocess` 在本仓对应实现为 **`snaker:callActivity`**（FIX-T73 §3.1.2），必填属性为 `processDefineName`（子流程 name）+ 可选 `assignee` / `formKey`。详见 `../docs/flow.md §3.7`。

### 2.3 任务节点字段参考（完整）

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | ✅ | 节点编码（唯一）→ 任务名 |
| `displayName`（`text.value`）| ✅ | 显示名称 |
| `assignee` | 二选一 | 固定参与者，逗号分隔多人；`"applicant"` = 发起人 |
| `assignmentHandler` | 二选一 | 动态参与者注册名（见下方内置清单）|
| `form` | - | 表单标识 → formKey |
| `taskType` | - | 0=主办 1=协办 |
| `performType` | - | 0=普通 1=会签 |
| `countersignType` | 会签时 | `PARALLEL` / `SEQUENTIAL` / `RATIO` |
| `candidateUsers` | - | 候选人：逗号分隔 userId（candidatePage 可选名单）|
| `candidateGroups` | - | 候选人：逗号分隔角色标识（candidatePage 可选名单，v1.6.0）|
| `expireTime` | - | 期望完成时间 |
| `preInterceptors` / `postInterceptors` | - | 节点拦截器注册名 |

> **本仓 properties 位置双语义**（FIX-T113 实测）：`candidateUsers` / `candidateGroups` / `countersignCompletionCondition` / `PERMISSION_*` **可放 `properties` 根下，也可放 `properties.field` 内**——两种位置引擎均识别，但混用易读性差，建议同一流程统一一种。
>
> **本仓 PERMISSION 字段前缀硬约束**：字段名必须为 **`PERMISSION_f_<name>`** 形式（FIX-DOC-1），权限码 `1`=只读 / `2`=编辑 / `3`=隐藏。

### 2.3.1 内置 assignmentHandler 注册名（v1.6.0）

以下注册名**四语言通用**（同一份流程 JSON 跨语言无需改动），语义对齐 boot4。 **每个 handler 的适用场景 / 配置示例 / 参数与注意事项见 [07 · 参与者解析（内置 handler 清单）](./07-assignment-handlers)**：

| 注册名 | 参与者 |
|---|---|
| `com.mldong.jeeflow.interceptor.impl.OperatorAssignmentHandler` | 流程发起人（兜底 `apply.operator`）|
| `com.mldong.jeeflow.interceptor.impl.FormFieldAssigneeHandler` | 表单字段值：节点名精确匹配变量字段；`task_01` 编号后缀自动去掉匹配 `task` |
| `com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$DeptLeaderAssignmentHandler` | 当前任务操作人部门领导 |
| `…$DeptMainLeaderAssignmentHandler` | 当前任务操作人部门分管领导 |
| `…$ApplicantDeptLeaderAssignmentHandler` | 流程发起人部门领导 |
| `…$ApplicantDeptMainLeaderAssignmentHandler` | 流程发起人部门分管领导 |
| `…$TaskRoleAssigneeHandler` | 任务节点编码关联角色（roleCode = 节点 `id`）|

> -   组织维度 handler 的数据来自 `OrgUserProvider` SPI（见 [SPI 设计](./../concepts/05-spi-design)）， 业务方只实现数据接口
> -   字段值支持逗号分隔字符串 / 数组；`FormFieldAssigneeHandler` 示例：节点 `id: "task1"`， 发起参数 `{"task1": "userA,userB"}` → 参与者 `userA,userB`
> -   自定义 handler：注册名 = 你在 `HandlerRegistry` 注册的名字（Java 为类全限定名，引擎反射加载）

> ⚠️ **本仓实现性差异（v1.9.0 起关键）**：本仓 `vendor/jeeflow/builtin.py:170-183` **同时注册 12 个 key** —— **7 个简化版主用 + 5 个完整版别名**（兼容历史）。
>
> | 注册形态 | FQCN 形式 | 用途 |
> |---|---|---|
> | 简化版主用 | `com.mldong.jeeflow.interceptor.impl.<HandlerName>` | v1.9.0+ 新流程主用 |
> | 完整版别名 | `com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$<HandlerName>` | 兼容历史流程 JSON |
>
> - **不再**「写了 `OrgUserAssignmentHandlers$*` 嵌套类 → 引擎 `ValueError(handler 未注册)`」——别名注册后历史 JSON 可继续运行；
> - **新流程**建议统一用简化版主用名（详见 `../ToT/guides/07-assignment-handlers.md` §2 速查表）；
> - `TaskRoleAssigneeHandler` 的 `role_code` **双轨制**（FIX-T8 §68，`builtin.py:143`）：优先 `properties.roleCode`（Java 设计器规范字段），回落 `node.id`；
> - 详见 `../docs/flow.md §6` + `../docs/known-issues.md §67/§68` + `../ToT/guides/07-assignment-handlers.md`。

### 2.4 决策节点

```
节点 properties:
  expr: "amount > 1000"          # 节点级默认表达式（可选）
  decisionHandler: "xxx"         # 自定义决策器注册名（可选）

出边 properties:
  expr: "amount > 1000"          # 分支条件（决策节点出边必填）
出边 text.value:
  "金额>1000"                    # 分支标签（钉钉模式渲染在线上）
```

**决策路由规则**：引擎按出边顺序求值，第一个 expr 为真的边获胜；无 expr 的出边作为默认分支。

> **本仓兜底语义**（BUG-2 / FIX-T112 §113）：若**所有** `expr` 评估失败且**没有**显式默认边（`expr=""`），引擎兜底走**第一条**出边，可能创建孤儿 DOING task。设计建议：① 多分支决策节点**显式加默认边** `expr=""`；② 引擎层 `_cleanup_orphan_decision_tasks` 兜底（W014 警告）。

### 2.5 会签节点

```json
{
  "id": "countersign",
  "type": "snaker:task",
  "properties": {
    "assignee": "userA,userB,userC",
    "performType": 1,
    "countersignType": "PARALLEL"
  },
  "text": { "value": "会签审批" }
}
```

| 模式 | 行为 |
|---|---|
| `PARALLEL` | 每个参与者一个任务，全部完成才推进 |
| `SEQUENTIAL` | 一次一个任务，完成后下一个参与者 |
| `RATIO` | 阈值完成即推进（完成条件表达式：计划中）|

> **本仓会签三模式实际实现**（与上游文字略不同）：
>
> | 模式 | 本仓实现方式 | 关键差异 |
> |---|---|---|
> | `PARALLEL`（全员通过）| `performType=1 + countersignType=PARALLEL`，**无** `countersignCompletionCondition` | 全部 `submitType=0` 通过才流转；剩余 taskState 仍 10，**不自动废弃** |
> | `SEQUENTIAL`（按顺序审）| `performType=1 + countersignType=SEQUENTIAL` | 仅最后一个通过即流转 |
> | `RATIO`（比例完成）| `performType=1 + countersignType=PARALLEL` + `countersignCompletionCondition` 表达式 | OGNL 表达式，引擎注入 `nrOfCompletedInstances` / `nrOfInstances` 变量；命中即流转，余者 ABANDON |
> | 一票否决 | `performType=1 + countersignType=PARALLEL` + `countersignCompletionCondition="ONE_VOTE_VETO"` | 任一 reject 立即流转 state=45 + 余者 ABANDON |
>
> ⚠️ **RATIO 与 ONE_VOTE_VETO 二选一**：字段值为**表达式** → 比例模式（放弃一票否决）；字段值为**字符串 "ONE_VOTE_VETO"** → 一票否决（放弃比例）。**两种语义互斥，不可复合**（FB-0008）。详见 `../docs/flow.md §3.3` + `../docs/known-issues.md §113`。

---

## 3. 边

```json5
{
  "id": "e1",
  "sourceNodeId": "start",   // 起点节点 id
  "targetNodeId": "apply",   // 终点节点 id
  "properties": { "expr": "amount > 1000" },  // 决策分支条件
  "text": { "value": "金额>1000" }            // 分支标签（决策/fork 边建议必填）
}
```

**建议**：decision 出边、fork 出边都写 `text.value` 标签——钉钉模式渲染在分支线上，没有标签线上是空的。

> **本仓 task 节点多出边警告**（FIX-T110 §111 + verify W012）：**task 节点不应有多条无条件出边**。引擎 `engine.py:1147 _follow_edges` 遍历所有出边不分流；当 task 节点 ≥2 出边且 target 含 end 节点时，end 会被提前遍历 → `inst.finish()` → instance.state=20 DONE，**但同时创建的 DOING task 因 instance.state=20 而无法 `execute`**（code=99999999）。
>
> - 需要分支时**用 decision 节点分隔**（每条 decision 出边配显式 `expr`），或用 fork 节点（必须 join 汇合）；
> - verify 规则 **W012** 会在 deploy 时警告此反模式（不阻塞 save/deploy）。

---

## 4. 完整示例（标准骨架）

```json
{
  "name": "leave",
  "displayName": "请假审批",
  "type": "approval",
  "nodes": [
    { "id": "start", "type": "snaker:start", "x": 100, "y": 200, "properties": {}, "text": { "value": "开始" } },
    { "id": "apply", "type": "snaker:task", "x": 250, "y": 200,
      "properties": { "form": "apply-form", "assignee": "applicant", "taskType": 0, "performType": 0 },
      "text": { "value": "发起申请" } },
    { "id": "leader", "type": "snaker:task", "x": 400, "y": 200,
      "properties": { "form": "leave-form", "assignee": "leader", "taskType": 0, "performType": 0 },
      "text": { "value": "组长审批" } },
    { "id": "end", "type": "snaker:end", "x": 550, "y": 200, "properties": {}, "text": { "value": "结束" } }
  ],
  "edges": [
    { "id": "e1", "sourceNodeId": "start", "targetNodeId": "apply", "properties": {} },
    { "id": "e2", "sourceNodeId": "apply", "targetNodeId": "leader", "properties": {} },
    { "id": "e3", "sourceNodeId": "leader", "targetNodeId": "end", "properties": {} }
  ]
}
```

> **本仓对应示例**：上述骨架与本仓 `flows/01-simple.json` 几乎同构（id 命名 `task1` vs `leader`）。可作为 baseline 复制后改造。

---

## 5. 决策表达式

表达式求值走 `ExpressionEvaluator` SPI，demo 内置了简单数值比较：

```
amount > 1000
amount <= 1000
u_deptId == 'D01'        # 变量前缀 u_ 为引擎注入的用户信息
finalAmount >= 5000
```

生产接入时按需选型（Java 用 SpEL、Python 用 simpleeval 等），引擎不内置。

> **本仓决策表达式实际能力**（`vendor/jeeflow/engine.py` 内联实现；`SimpleExprEvaluator` 类不存在，详见 `ToT/docs/diffs.md` §3-6；FIX-T37 §20）：上游 demo 仅支持数值比较过于简化，本仓实际支持：
>
> | 能力 | 语法 | 示例 |
> |---|---|---|
> | 数值比较 | `>` `<` `>=` `<=` `==` `!=` | `amount > 1000` |
> | 逻辑运算 | `&&` `\|\|` `!` | `#amount >= 5000 && #urgent == 1` |
> | 变量访问 | 直接变量名 或 `#var` | `amount` / `#amount` / `#f_amount`（带 f_ 前缀） |
> | 字符串字面量 | 单/双引号 | `u_deptId == 'D01'` |
> | 算术运算 | `+` `-` `*` `/` `%` | `#f_amount * 0.1` |
>
> ⚠️ **不在能力范围**：函数调用 / 对象方法 / 数组下标 / 三元表达式。如需复杂条件，需扩展 `ExpressionEvaluator` SPI 自定义。

---

## 6. 常见错误

| 错误 | 现象 | 修复 |
|---|---|---|
| 多个 end 节点 | 分支各自结束 | 汇合到同一个 end |
| 申请节点缺 assignee | 启动后无任务 | 加 `"assignee": "applicant"` |
| 决策出边缺 expr | 走默认分支（第一个无 expr 边）| 每条出边补 expr |
| 决策/fork 边缺 text | 线上无标签 | 补 `text.value` |
| 节点 id 重复 | 任务名冲突 | 保证 id 全流程唯一 |

> **本仓高频坑补充**（基于 `../docs/known-issues.md` + `../docs/BUGS.md` 实战统计）：
>
> | 错误 | 现象 | 修复 |
> |---|---|---|
> | **节点 id 含空格 / `-` / 中文** | deploy 时 regex 拒绝 `^[A-Za-z0-9_]+$` | 改纯字母数字下划线（FIX-T34 §93）|
> | **task 节点多条无条件出边** | instance.state=20 DONE 但下游 task 卡 DOING | 用 decision 节点分隔或 fork+join（F-110 / W012）|
> | **decision 节点所有 expr 评估失败** | 兜底走第一条边，可能创建孤儿 DOING task | 加显式默认边 `expr=""`（FIX-T112 / W013）|
> | **PERMISSION_* 字段名错** | 字段权限不生效 | 必须 `PERMISSION_f_<name>` 前缀（FIX-DOC-1 §82）|
> | **countersignCompletionCondition 字段值混用** | 比例能力 / 一票否决能力互斥 | 表达式 → 比例；字符串 `ONE_VOTE_VETO` → 一票否决，二选一（FB-0008 §113）|
> | **assignmentHandler FQCN 拼写错或未注册** | 引擎走默认 = `inst.operator` / 抛 `ValueError(handler 未注册)` | 严格照 `com.mldong.jeeflow.interceptor.impl.*` 简化版 + 本仓 SPI 注册（§67）|
> | **`preInterceptors` 写了但未生效** | 静默不抛错（v1.9.0 前）；v1.9.0+ FIX-T34 已修复 | 用 `postInterceptors` 或升级 v1.9.0（§34）|