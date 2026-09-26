# 规范 02 · 流程定义配置项完整参考（属性字典）

> **来源**：https://jeeflow-doc.mldong.com/spec/02-flow-definition
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**流程定义权威参考**——所有 `properties` 字段、顶层字段、节点类型、边属性的官方解释。
>
> **本仓实现版本**：基于 `vendor/jeeflow/model.py:316 _KNOWN_MODEL = {name,displayName,type,nodes,edges}` 解析器；本仓 Python 引擎 `parse_flow_model` 严格过滤未知字段，写入额外键（如设计器 UI 元数据）会被丢弃。
>
> **裁剪记录**：§1 / §2 / §3 / §4 / §4.1 / §4.2 / §5 / §8 / §9 / §10 保留 + 加本仓实现注解；§6 / §7 重写为本仓实际实现（callActivity / custom 三字段）；§11 原文保留 + 补本仓高频坑。

---

## 1. JSON 结构总览

```json5
{
  // ── 顶层（引擎解析）──
  "name": "leave",            // 流程编码（唯一，deploy 版本管理键）
  "displayName": "请假审批",   // 流程显示名称
  "type": "approval",         // 流程类型
  "expireTime": "2026-12-31", // 流程期望完成时间
  "relTableName": "biz_leave",// 关联业务表名（bizData 回显）
  "persistMode": "ARCHIVE",   // 业务落表模式（persist）
  "postInterceptors": ["..."],// 流程级后置拦截器
  "preInterceptors": ["..."], // 流程级前置拦截器
  "instanceUrl": "...",       // 实例详情 URL（预留）
  "instanceNoClass": "...",   // 业务号生成类（预留）
  // ── LogicFlow 图 ──
  "nodes": [ /* 见 §3 */ ],
  "edges": [ /* 见 §9 */ ]
}
```

**节点（LogicFlow 标准字段）**：

```json5
{
  "id": "apply",          // 节点唯一编码 → 任务名 taskName（全流程唯一）
  "type": "snaker:task",  // 节点类型（接受带/不带前缀两种写法，见 §3）
  "x": 250, "y": 200,     // 画布坐标（设计器布局，引擎不参与执行）
  "text": { "value": "发起申请" },  // 显示名称 displayName（引擎读取位置）
  "properties": { /* 引擎扩展属性，见 §4~§8 */ }
}
```

> 兼容：`type` 接受 `snaker:task` 与 `task` 两种写法（设计器导出带前缀，手写可省略）。
>
> **本仓实测**（`vendor/jeeflow/model.py:9 class FlowModel` + `parse_flow_model` 函数）：未知字段**严格丢弃**——写入额外键（如设计器 UI 元数据）不会存入实例变量，也不参与执行。如需任务回显，写入 `properties` 内任一命名键即可（运行时透传）。

---

## 2. 顶层属性（流程级）

> **本仓实测**（`vendor/jeeflow/model.py:366 _KNOWN_MODEL = {"name", "displayName", "type", "nodes", "edges"}` 5 个字段 + `parse_flow_model`）：引擎**严格过滤未知字段**——`_KNOWN_MODEL` 外字段（如 `expireTime` / `relTableName` / `persistMode` / `instanceUrl` / `preInterceptors` / `postInterceptors` / `instanceNoClass` / 5 个前端字段）写入**额外键**会被丢弃，不参与引擎执行；如需任务回显，写入 `properties` 内任一命名键即可（运行时透传）。注：`_KNOWN_MODEL` 仅 5 个**核心引擎字段**，`preInterceptors` / `postInterceptors` 等由 facade 单独解析（详见 `vendor/jeeflow/facade.py:155 _startAndExecute`）。

| 字段 | 类型 | 引擎 | 说明 |
|---|---|---|---|
| `name` | string | ✅ | 流程编码（唯一）——deploy 版本管理键（同 name 从 0 递增）；bizData 表名回落 |
| `displayName` | string | ✅ | 流程显示名称 |
| `type` | string | ✅ | 流程类型（`listByType` 分组键）；本仓实测 `approval` vs `business` 引擎处理**无差**（仅前端 UI 分类，见 `../ToT/guides/06-deployment.md` §5.1 + `../docs/flow.md §2 type=approval vs business`）|
| `expireTime` | string | ✅ | 流程期望完成时间 |
| `relTableName` | string | ✅ | 关联业务表名——`bizData` 回显定位表；缺省回落 `name` |
| `persistMode` | string | ✅ | 业务落表模式：`ARCHIVE`（缺省）/ `SYNC`，见 `../ToT/guides/08-persist.md` |
| `preInterceptors` | string[] | ✅ | 流程级前置拦截器注册名（逗号分隔/数组）；**v1.9.0+ FIX-T34 已修复生效**（老版本静默不生效，见 `../docs/known-issues.md §34`）|
| `postInterceptors` | string[] | ✅ | 流程级后置拦截器注册名——persist 办理节点权限判定路径，**必须配置**（未注册 `engine.py:1054 _resolve_interceptors` 抛错）|
| `instanceUrl` | string | 预留 | 实例详情 URL（前端用）|
| `instanceNoClass` | string | 预留 | 业务号生成类（前端 / 集成方用）|
| `selectUserOnInitiate` | int | 前端 | 发起时选择处理人（0/1）|
| `enableCcActors` | int | 前端 | 发起页抄送开关（0/1）|
| `enableApplyReason` | int | 前端 | 发起页申请理由开关（0/1）|
| `enableAttachment` | int | 前端 | 发起页附件开关（0/1）|
| `enableFieldPerm` | int | 前端 | 字段权限开关（0/1）|

---

## 3. 节点公共属性（全部节点通用）

| 字段 | 引擎 | 说明 |
|---|---|---|
| `id` | ✅ | 节点唯一编码 → 任务名 taskName |
| `type` | ✅ | 节点类型（8 种，见下）|
| `text.value` | ✅ | 显示名称 displayName |
| `properties.name` | ✅ | 唯一编码（钉钉模式设计器写入，与 `id` 对应）|
| `preInterceptors` | ✅ | 节点前置拦截器注册名（逗号分隔多注册名）|
| `postInterceptors` | ✅ | 节点后置拦截器注册名（persist 模型级执行后触发）|
| `x` / `y` / `layout` | 布局 | 画布坐标/布局（引擎不参与执行）|

**节点类型总览**：

| type（兼容写法）| 说明 | 必填 properties |
|---|---|---|
| `snaker:start` / `start` | 开始 | - |
| `snaker:end` / `end` | 结束（**全流程只能有一个**）| - |
| `snaker:task` / `task` | 任务节点 | `assignee` 或 `assignmentHandler` |
| `snaker:decision` / `decision` | 条件分支 | 出边 `expr` |
| `snaker:fork` / `fork` | 并行分支 | - |
| `snaker:join` / `join` | 并行合并 | - |
| `snaker:custom` / `custom` | 自定义节点 | `clazz` |
| `snaker:subprocess` / `subprocess` | 子流程 | `form` |

> **本仓节点类型映射**：
> - 上游 `snaker:subprocess` 在本仓对应实现为 **`snaker:callActivity`**（FIX-T73 §3.1.2，详见 `../docs/flow.md §3.7`），必填 `processDefineName` 而非 `form` + `version`
> - **本仓节点 id 硬约束**（FIX-T34 §93）：**严格 `^[A-Za-z0-9_]+$`**——禁止空格 / `-` / 中文 / 特殊字符。理由：JSON key / URL 路由 / SQL 列名三处皆依赖
>
> **发起申请节点约定（mldong 框架契约）**：`start` 后第一个任务节点必须是"发起申请"节点，`assignee = "applicant"`（引擎解析为流程发起人）。引擎不自动执行该节点，由调用方（`startAndExecute`）启动后自动完成，流程推进到真正的审批节点。

---

## 4. 任务节点 properties 完整字典（snaker:task）

| 字段 | 类型 | 引擎 | 说明 |
|---|---|---|---|
| `assignee` | string | ✅ | 固定参与者：逗号分隔多人；`applicant` = 发起人；token 优先按流程变量 key 解析 |
| `assignmentHandler` | string | ✅ | 动态参与者注册名（内置清单见 `../ToT/guides/07-assignment-handlers.md`）|
| `form` | string | ✅ | 表单标识 → formKey（发起页/办理页表单定位）|
| `taskType` | int | ✅ | 0=主办 1=协办 2=记录（FIX-T30 透传落库；taskType=2 自动完成不等待人工 execute，见 `../docs/flow.md §3.3` taskType 设计陷阱）|
| `performType` | int/string | ✅ | 0=普通参与 1=会签；**兼容字符串 `'1'`/`'ALL'`/`'COUNTERSIGN'`** |
| `countersignType` | string | ✅ | 会签模式：`PARALLEL`（并行）/ `SEQUENTIAL`（串行）/ `RATIO`（阈值）|
| `countersignCompletionCondition` | string | ✅ | 会签完成条件表达式；特殊值 `ONE_VOTE_VETO`（忽略大小写）= 一票否决 |
| `candidateUsers` | string | ⚠️ | 候选人 userId 列表（逗号分隔）——**不生成 actor**，供 `candidatePage` 选人；可放 `properties` 根或 `properties.field` 内（FIX-T113 实测）|
| `candidateGroups` | string | ⚠️ | 候选角色标识（逗号分隔）|
| `candidateHandler` | string | ⚠️ | 动态候选人处理注册名 |
| `reminderTime` | string | ✅ | 提醒时间（如 `10:00`）|
| `reminderRepeat` | string | ✅ | 重复提醒间隔 |
| `expireTime` | string | ✅ | 期望完成时间 |
| `autoExecute` | string | ✅ | 自动执行配置 |
| `callback` | string | ✅ | 回调处理注册名（任务完成回调）|
| `preInterceptors` | string[] | ✅ | 前置拦截器 |
| `postInterceptors` | string[] | ✅ | 后置拦截器（persist 写库/权限判定）|
| `field` | object | ✅ | 字段权限声明（见 §4.1）|
| 其他任意键 | any | ext | 不识别 → 存入节点扩展属性 `ext`（任务变量回显，不参与执行）|

> **本仓实现性差异（5 字段）**：
>
> | 字段 | 本仓状态 | 设计师实践 |
> |---|---|---|
> | `candidateHandler` | **未实现** | 流程 JSON 写了不会生效；候选人解析走 `candidateUsers` / `candidateGroups` |
> | `reminderTime` / `reminderRepeat` | **未实现**（无内置提醒机制）| 设计师需自行扩展 `EventType.TASK_COMPLETE` 监听器 |
> | `autoExecute` | **未实现** | 用 `taskType=2` 记录模式自动完成（不等人工）|
> | `callback` | **未实现** | 用 `postInterceptors` 替代 |
>
> 详见 `../docs/flow.md §3.3` + `../docs/known-issues.md` 全文。

### 4.1 字段权限（field，SYNC persist 用）

- 声明位置：任务节点 `properties.field`
- **键格式双兼容**（v1.8.1+ issues/25）：`PERMISSION_{表单字段全名}`（含 `f_` 前缀，前端 vben5-wf 约定，**优先**） 与 `PERMISSION_{去前缀名}`（旧格式，兼容）
- 值：`1`=只读 / `2`=可编辑 / `3`=隐藏（**缺省=可编辑**）
- 办理入口过滤：按任务节点权限过滤后再入流程变量——上游只读不可被下游绕过
- 状态列：优先 `{节点ID}_{状态码}` 列，无则 `{节点ID}` 列

### 4.2 会签（countersign）行为

| 模式 | 行为 | 推进条件 |
|---|---|---|
| `PARALLEL` | 每个参与者一个独立任务 | 全部完成 |
| `SEQUENTIAL` | 一次一个任务，完成后流转给下一个参与者 | 全部完成 |
| `RATIO` | 每人一个任务 | 完成数满足 `countersignCompletionCondition` |
| 一票否决（`ONE_VOTE_VETO`）| `countersignCompletionCondition` 设为 `ONE_VOTE_VETO`（忽略大小写）时，任一成员 `submitType=20` 会签不同意 → 节点立即推进 | 否决者提交即合并 |

**会签推进/否决后的残留处理**：节点合并（merged）推进下一节点时，该节点仍 DOING 的会签任务一律废弃（taskState=99），不留孤儿待办。

**会签拒绝（submitType=20）的默认语义 = 软拒绝**：未配置 `ONE_VOTE_VETO` 时，否决者任务正常完成、`countersignDisagreeFlag=1` 记录为流程变量（供下游节点作参考），流程**不阻断**，按常规模式等待推进。

> ⚠️ **本仓实测铁律**（FB-0008 §113 + FB-0012 §116）：
> - 字段值 = **表达式** → 比例模式；字段值 = **字符串 "ONE_VOTE_VETO"** → 一票否决模式。**两种语义互斥**，不可复合
> - submitType=20 仅 **会签 task → end 直连**时生效；后接 decision 节点会截断 cs_veto 路径
> - 详见 `../ToT/guides/02-flow-definition.md` §2.5 + `../docs/known-issues.md §113/§116`

---

## 5. 决策节点 properties（snaker:decision）

| 字段 | 位置 | 引擎 | 说明 |
|---|---|---|---|
| `expr` | 节点 | ✅ | 节点级默认表达式（可选）|
| `handleClass` | 节点 | ✅ | 自定义决策器处理类注册名（本仓对应 `EngineExtensions.decision_handler` 或 `HandlerRegistry.register_decision`，详见 `../ToT/guides/04-extensions.md` §3）|
| `expr` | **出边** | ✅ | 分支条件表达式——**决策出边必填（首条满足者胜）** |
| `text.value` | 出边 | ✅ | 分支标签（钉钉模式渲染在线上）|

**决策路由规则**：引擎按出边顺序求值，第一条 `expr` 为真的边获胜；无 `expr` 的出边作为默认分支（兜底）。表达式语法见 `../ToT/guides/02-flow-definition.md` §5。

> **本仓兜底语义**（BUG-2 / FIX-T112 §113）：若**所有** `expr` 评估失败且**没有**显式默认边（`expr=""`），引擎兜底走**第一条**出边，可能创建孤儿 DOING task。设计建议：① 多分支决策节点**显式加默认边** `expr=""`；② 引擎层 `_cleanup_orphan_decision_tasks` 兜底（W014 警告）。

---

## 6. 自定义节点 properties（snaker:custom）

> **本仓实际实现**（v1.9.0+ FIX-T38 §16）：上游列 4 字段（`clazz` / `methodName` / `args` / `val`），本仓简化实现为 **3 字段** —— `clazz` + `args` + `val`。

| 字段 | 引擎 | 说明 |
|---|---|---|
| `clazz` | ✅ | 处理器类路径 / 注册 key（必填）|
| `args` | ✅ | 参数变量（逗号分隔的变量 key）|
| `val` | ✅ | 返回值写入的变量 key |

```json
{
  "id": "call_external_api",
  "type": "snaker:custom",
  "properties": {
    "clazz": "com.mldong.jeeflow.test.TimestampHandler",
    "args": "f_amount,f_userId",
    "val": "tf_external_result"
  }
}
```

> **本仓 handler 签名**（`vendor/jeeflow/persist.py` + `engine.py:_handle_custom_node`）：
>
> ```python
> async def handler(node, inst, vars_, args) -> Any:
>     """node = 当前节点 / inst = ProcessInstance / vars_ = 流程变量 dict / args = 节点 properties.args 字符串"""
>     # 返回值自动写入 vars_[properties.val]
> ```
>
> - 注册：`main_common.py:build_custom_handlers()` 注册 `EngineExtensions.custom_handler_registry`
> - 未注册抛 `ValueError(handler 未注册: ...)`（**不静默跳过**）
> - 示例：`com.mldong.jeeflow.test.TimestampHandler` / `TestCustomHandler` / `AppendVarsHandler`（详见 `../main_common.py:348 build_custom_handlers`）

---

## 7. 子流程节点 properties（snaker:subprocess）

> **本仓对应节点类型**：**`snaker:callActivity`**（FIX-T73 §3.1.2），上游 `snaker:subprocess` + `form` / `version` 在本仓**不识别**，必须用 callActivity。

```json
{
  "id": "sub_call",
  "type": "snaker:callActivity",
  "properties": {
    "processDefineName": "sub-flow",   // 子流程 name（必填，按最新版本）
    "assignee": "user2",                // 子流程发起人（缺省 = 主流程 operator）
    "formKey": "sub-form"               // 可选（用于子流程表单复用，不强制）
  }
}
```

| 字段 | 引擎 | 说明 |
|---|---|---|
| `processDefineName` | ✅ | 子流程 name（**必填**）|
| `assignee` | ✅ | 子流程发起人（缺省 = 主流程 operator）|
| `formKey` | ✅（可选）| 子流程表单复用 |

**行为**：
1. 引擎查找 `wf_process_define` 中 `name = processDefineName` 的最新一版
2. 启动子实例，`parentId` = 主实例 id
3. 写 `childInstanceId` 到主实例 `vars_[<node.id>_childInstanceId]`
4. **不阻塞主流程**，立即推进至下游节点
5. 子实例完成时通过 `parentStatus` 字段联动回写主实例

> **本仓主子状态联动**（FIX-T72 §3.1.1）：`ProcessInstance.parent_status` 取值 `CHILD_DONE`（子 DONE）/ `CHILD_REJECT`（子 REJECT）。

---

## 8. 开始 / 结束 / 并行节点

- `snaker:start` / `snaker:end`：无专属属性（仅公共属性）
- `snaker:fork` / `snaker:join`：无专属属性——fork 出边建议写 `text.value` 分支标签

> **本仓 join 节点语义**（FIX-T35 §30）：显式汇合点，无活跃任务时放行至下游；即便 FIX-T35 后已支持隐式 join，**推荐**加 join 节点（流程图可视化清晰 + 防 task 节点多条无条件出边陷阱 F-110）。

---

## 9. 边属性（edges）

```json5
{
  "id": "e1",
  "sourceNodeId": "start",     // 起点节点 id
  "targetNodeId": "apply",     // 终点节点 id
  "properties": { "expr": "amount > 1000" },  // 决策分支条件
  "text": { "value": "金额>1000" }            // 分支标签（决策/fork 边建议必填）
}
```

| 字段 | 引擎 | 说明 |
|---|---|---|
| `sourceNodeId` / `targetNodeId` | ✅ | 起止节点 |
| `properties.expr` | ✅ | 决策出边条件表达式 |
| `text.value` | ✅ | 分支标签（钉钉模式渲染在线上，决策/fork 边建议必填）|

> **本仓边 id 命名**：与节点 id 一致，须严格 `^[A-Za-z0-9_]+$`（FIX-T34 同一 regex 同时校验节点 / 边 id）。

---

## 10. 完整示例（标准骨架）

```json
{
  "name": "leave",
  "displayName": "请假审批",
  "type": "approval",
  "relTableName": "biz_leave",
  "persistMode": "SYNC",
  "nodes": [
    { "id": "start", "type": "snaker:start", "x": 100, "y": 200, "properties": {}, "text": { "value": "开始" } },
    { "id": "apply", "type": "snaker:task", "x": 250, "y": 200,
      "properties": { "form": "apply-form", "assignee": "applicant", "taskType": 0, "performType": 0 },
      "text": { "value": "发起申请" } },
    { "id": "leader", "type": "snaker:task", "x": 400, "y": 200,
      "properties": { "form": "leave-form", "assignee": "leader", "taskType": 0, "performType": 0,
        "postInterceptors": ["persistPost"] },
      "text": { "value": "组长审批" } },
    { "id": "decision1", "type": "snaker:decision", "x": 550, "y": 200, "properties": {}, "text": { "value": "金额判断" } },
    { "id": "end", "type": "snaker:end", "x": 700, "y": 200, "properties": {}, "text": { "value": "结束" } }
  ],
  "edges": [
    { "id": "e1", "sourceNodeId": "start", "targetNodeId": "apply", "properties": {} },
    { "id": "e2", "sourceNodeId": "apply", "targetNodeId": "leader", "properties": {} },
    { "id": "e3", "sourceNodeId": "leader", "targetNodeId": "decision1", "properties": {} },
    { "id": "e4", "sourceNodeId": "decision1", "targetNodeId": "end",
      "properties": { "expr": "amount > 1000" }, "text": { "value": "金额>1000" } },
    { "id": "e5", "sourceNodeId": "decision1", "targetNodeId": "end",
      "properties": {}, "text": { "value": "默认" } }
  ]
}
```

> **本仓对应示例**：`../flows/10-mixed-mode.json`（混合模式：fork + join + decision + 会签组合）+ `../flows/03-decision-expr.json`（决策表达式）。

---

## 11. 常见错误对照

| 错误 | 现象 | 修复 |
|---|---|---|
| 多个 end 节点 | 分支各自结束 | 汇合到同一个 end |
| 申请节点缺 assignee | 启动后无任务 | 加 `"assignee": "applicant"` |
| 决策出边缺 expr | 走默认分支（第一条无 expr 边）| 每条出边补 expr |
| 决策/fork 边缺 text | 线上无标签 | 补 `text.value` |
| 节点 id 重复 | 任务名冲突 | 保证 id 全流程唯一 |
| custom 写 `customClass` | 解析不出 clazz，节点不执行 | 用 `clazz` |
| 属性拼写错误 | 静默进 ext，行为不生效 | 对照本表逐键核对 |

> **本仓补充 7 条高频坑**（基于 `../docs/known-issues.md` + `../docs/BUGS.md` 实战统计）：
>
> | 错误 | 现象 | 修复 |
> |---|---|---|
> | **节点 id 含空格 / `-` / 中文** | deploy 时 regex 拒绝 `^[A-Za-z0-9_]+$` | 改纯字母数字下划线（FIX-T34 §93）|
> | **task 节点多条无条件出边** | instance.state=20 DONE 但下游 task 卡 DOING | 用 decision 节点分隔或 fork+join（FIX-T110 §111 / W012）|
> | **decision 节点所有 expr 评估失败** | 兜底走第一条边，可能创建孤儿 DOING task | 加显式默认边 `expr=""`（FIX-T112 §113 / W013）|
> | **PERMISSION_* 字段名错** | 字段权限不生效 | 必须 `PERMISSION_f_<name>` 前缀（FIX-DOC-1 §82）|
> | **countersignCompletionCondition 字段值混用** | 比例能力 / 一票否决能力互斥 | 表达式 → 比例；字符串 `ONE_VOTE_VETO` → 一票否决，二选一（FB-0008 §113）|
> | **assignmentHandler FQCN 拼写错或未注册** | 引擎走默认 = `inst.operator` / 抛 `ValueError(handler 未注册)` | 严格照 `com.mldong.jeeflow.interceptor.impl.*` 简化版 + 本仓 SPI 注册（§67）|
> | **`preInterceptors` 写了但未生效**（老版本） | 静默不抛错（v1.9.0 前）；v1.9.0+ FIX-T34 已修复 | 用 `postInterceptors` 或升级 v1.9.0（§34）|