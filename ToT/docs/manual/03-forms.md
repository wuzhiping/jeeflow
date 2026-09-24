# 第 3 章 · 表单：发起时填什么，审批时看什么

> **来源**：https://jeeflow-doc.mldong.com/manual/03-forms
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**操作手册第 3 章**——表单是流程能跑的前提。本章覆盖**字段权限 / f_ 前缀 / 任务表单绑定 / 数据模型与流程变量映射**等核心契约。
>
> **本仓实测**：基于 `vendor/jeeflow/docs/flow.md` §3.3 + `persist.py:453 _is_editable` + `model.py:177 ProcessInstance.variables`。
>
> **裁剪记录**：§1 两种表单（元数据 vs 自定义 Vue 组件）+ §2 元数据表单（数据模型 + 模型字段）+ §3 绑定到流程（流程级 / 节点级）**保留**并加本仓实测；§4 字段权限 + §5 表单与条件分支 + §7 卡住了（6 排错）**保留并重写为本仓实测**；§6 已知缺陷（前端 Vue 组件白屏）**整段裁剪**（本项目不输出 UI）。

---

## §1. 两种表单，先用第一种

| 类型 | 怎么来 | 适用 |
|---|---|---|
| **元数据表单** | 在线开发 → 数据模型 + 模型字段，无需写代码 | 绝大多数业务表单，**推荐** |
| **自定义 Vue 组件表单** | 前端工程里放一个 `wf-form` / `tf-form` 组件，由开发提供 | 复杂交互、需要前端逻辑 |

> **本仓实测**：本仓 `vendor/jeeflow/` 是**纯引擎实现**——表单渲染由前端 `jeeflow-ui` 负责（不在本仓范围）。设计师只需在流程 JSON 节点 `properties.form` 字段声明「表单 key」，具体前端按 key 渲染对应表单组件。详见 `../spec/02-flow-definition.md` §4 任务节点 properties。

---

## §2. 元数据表单：数据模型 + 模型字段

**在线开发 → 数据模型**。

每个数据模型 = 一张表 = 一张表单。行操作里 **模型字段** 是配表单字段的地方：

每个字段关心 4 列：

| 列 | 说明 |
|---|---|
| **字段名称** | 落库列名，同时是**流程变量名**（加 `f_` 前缀，如 `days` → `f_days`），条件表达式引用的就是它 |
| **字段注释** | 表单上显示的标签 |
| **组件名称** | 控件类型：`Input` / `InputNumber` / `Textarea` / `ApiDict`（字典下拉）/ `ApiSelect`（用户下拉）/ `ApiTreeSelect`（部门树）/ `DatePicker` / `TableLink` 等 |
| **允许为空** | 关掉后发起时该字段必填，前端和引擎都会拦 |

> **本仓实测**（`vendor/jeeflow/persist.py:_extract_fields`）：
>
> ```python
> for k, v in instance.variables.items():
>     if include_form_fields and k.startswith(prefix) and len(k) > len(prefix):
>         name = k[len(prefix):]                                    # 去 f_ 前缀
>         data[name] = v                                            # 写入业务表
> ```
>
> - `f_` 前缀是**架构契约**——实例变量中所有 `f_*` 字段对应发起表单的业务字段
> - 落库时**自动去前缀**（`f_days` → `days`）
> - 字段名与表达式引用完全一致（详见 §5）

---

## §3. 把表单绑到流程上

### 3.1 流程级：实例启动表单

设计器里画布空白处点右键 → **流程属性** → **实例启动表单** 选 **元数据表单**。

选完出现 **设计表单** 按钮，点它会先让你选怎么开始：

| 入口 | 行为 |
|---|---|
| 直接编辑（空白表单）| 从零拖一张内嵌表单，表单结构随流程定义一起存 |
| 从数据模型导入 | 把某个数据模型的字段拉进来当表单，**最省事** |
| 跳转到表单设计页 | 去 **在线开发** 的独立表单设计页 |

> **本仓实测**（`vendor/jeeflow/model.py:316 _KNOWN_MODEL`）：流程顶层 JSON 字段不存表单定义（仅存 `name` / `displayName` / `type` / `nodes` / `edges`）；表单结构由前端在「实例启动表单」字段绑定数据模型 ID。引擎核心**不感知**表单 UI——只读 `f_*` 字段值。

### 3.2 节点级：任务表单

选中节点 → **表单配置** → **任务表单**，从下拉里选。**不选则该节点办理时只有审批意见区，没有业务表单**。

> **本仓实测**（`vendor/jeeflow/docs/flow.md §3.3`）：任务节点 `properties.form` 字段即表单 key：
>
> ```json
> {
>   "id": "task1",
>   "type": "snaker:task",
>   "properties": {
>     "form": "leave-form",
>     "assignee": "leader",
>     "taskType": 0,
>     "performType": 0
>   }
> }
> ```
>
> 详见 `../spec/02-flow-definition.md` §4 任务节点 properties 字典。

---

## §4. 字段权限：谁能改哪几栏

> **本节与 `spec/02-flow-definition.md` §4.1 完全对应**——上游表设计已对齐本仓实测。

先在 **流程属性** 里把 **启用字段权限** 打开，然后每个节点都能对该表单的字段单独设权限：

| 值 | 界面 | 效果 |
|---|---|---|
| `1` | 只读 | 看得到、改不了（审批页表单整片变灰就是这个）|
| `2` | 可编辑 | 正常填写 |
| `3` | 不可见 | 该节点上不出现这个字段 |

**典型配法**：

- 发起节点：把业务字段设为可编辑（`2`）
- 审批节点：全设只读（`1`）
- 特殊审批节点（如「财务复核」）：把 `amount` 单独放开可编辑（`2`），其他仍只读

> **本仓实测双键格式**（`vendor/jeeflow/persist.py:453 _is_editable`，v1.8.1+ issues/25）：
>
> ```json
> {
>   "id": "task1",
>   "type": "snaker:task",
>   "properties": {
>     "assignee": "leader",
>     "field": {
>       "PERMISSION_f_title": 1,
>       "PERMISSION_amount": 2
>     }
>   }
> }
> ```
>
> - **优先** `PERMISSION_f_{表单字段全名}`（前端 vben5-wf 设计器约定）
> - **兼容** `PERMISSION_{去前缀名}`（v1.8.0 首版格式）
> - 缺省 = `2` 可编辑
>
> 详见 `../spec/02-flow-definition.md` §4.1 + `../spec/09-persist.md` §4.2 字段权限。
>
> **v1.8.2 起引擎办理入口过滤**（FB-0011 / FIX-DOC-4 §115）：被拒值（`1` / `3`）在入变量前即被剔除，**被拒值无法经流程变量落到下游节点写入**——上游只读不可被绕过。详见 `../docs/known-issues.md §115`。

---

## §5. 表单与条件分支的关系

> **关键契约**：条件分支的表达式引用的是流程变量，即 **`f_` + 字段名称**。

请假申请的两条分支示例：

```
f_days <= 3     → 直接结束
f_days > 3      → 进分管领导审批
```

> **本仓实测**（`vendor/jeeflow/engine.py:1381 _eval_decision_expr` + `SimpleExprEvaluator`，FIX-T37 §20）：
>
> - 表达式支持 `#var` 与直接变量名两种写法：`#f_days > 3` / `f_days > 3` 等价
> - 字段名**区分大小写**——`f_Days` ≠ `f_days`
>
> **字段名改过一次，分支表达式也要跟着改**，否则条件恒不成立、流程会走默认分支（决策路由第一条出边）。
>
> 详见 `../ToT/guides/02-flow-definition.md` §5 决策表达式。

---

## §7. 卡住了看这里（重写为本仓实测）

| 现象 | 原因 | 处理 |
|---|---|---|
| 发起抽屉里是空的 | 实例启动表单没选，或选了元数据表单但没有对应数据模型 | 按 §3.1 选表单；确认关联业务表在数据模型里存在 |
| 办理弹窗只有审批意见 | 节点没绑任务表单 | §3.2 选上再部署 |
| 审批页字段能改，本该只读 | 未启用字段权限，或该节点该字段设成了可编辑 | §4 |
| 表单加了字段但流程里看不到 | 只改了数据模型，没重新导入并部署 | 设计表单 → 从数据模型导入 → 保存 → 部署 |
| 条件分支不按预期走 | 表达式里的变量名与字段名不一致（区分大小写）| §5，对齐 `f_<字段名>` |
| **本仓实测补充**：`taskType=2` RECORD 模式自动完成，**不等待人工 execute** | 节点 properties.taskType 误设为 `2`（记录模式）| 改回 `0`（主办）或 `1`（协办），详见 `../docs/flow.md §3.3 taskType 设计陷阱` |

> **本仓实测警示**（`vendor/jeeflow/engine.py:466 _create_task`）：taskType=2 创建后**自动完成**——`taskState=20` 直接进审批记录，下游节点（`TODO` 节点）**不出现**在待办列表。设计师期望"汇合后由人办理"应使用 `taskType=0`（主办）。详见 `../ToT/guides/02-flow-definition.md` §4 + `../docs/known-issues.md`。

---

## 跨文档交叉引用

- 节点 properties 完整字典（含 `form` / `taskType` / `performType` / `field`）：`../spec/02-flow-definition.md` §4
- 字段权限 1/2/3 + 双键格式（PERMISSION_f_* 优先）：`../spec/02-flow-definition.md` §4.1
- f_ 前缀 + tf_ 前缀 + u_ 前缀分工：`../spec/04-engine-ops.md` §流程变量约定 + `../docs/known-issues.md §115`
- 业务落库 ARCHIVE/SYNC + 字段权限过滤实测：`../spec/09-persist.md` §4.2
- 决策表达式语法 + `#var` 前缀：`../ToT/guides/02-flow-definition.md` §5
- 节点 properties 21 字段 5 项未实现注解：`../ToT/guides/02-flow-definition.md` §4