# 规范 04 · 引擎核心操作

> **来源**：https://jeeflow-doc.mldong.com/spec/04-engine-ops
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**引擎核心操作语义契约**——理解每个操作的执行语义是设计 submitType 路由与排查卡死实例的基础。
>
> **本仓实现版本**：基于 `vendor/jeeflow/engine.py` + `model.py:70 SubmitType(IntEnum)` + `model.py:112 ProcessInstance` + `:230 ProcessTask` 聚合根方法。
>
> **裁剪记录**：启动 / 完成任务 / 驳回 / 跳转 / 退回上一步 / 会签 / 流程变量约定 / 聚合根方法清单全部保留 + 加本仓实测注解；各语言实现位置表裁掉仅留本仓 Python 路径。

---

## submitType 全枚举（本仓实测）

> **本仓实现**：`vendor/jeeflow/model.py:70 SubmitType(IntEnum)` —— 9 个值。

| code | 名称 | 语义 | 落地 |
|---|---|---|---|
| `0` | `APPLY` | 发起 / 重新提交 | 推进流程 |
| `1` | `AGREE` | 同意 | 推进流程 |
| `2` | `REJECT` | 拒绝 | 实例 → 45 REJECT + 余者 ABANDON |
| `3` | `ROLLBACK` | 退回上一步 | 新建上一节点任务（血缘版） |
| `4` | `JUMP` | 跳转到指定节点 | 重新执行目标节点输出边 |
| `5` | `RE_APPLY` | 重新提交 | 同 `APPLY` |
| `6` | `ROLLBACK_TO_OPERATOR` | 退回发起人 | 强制指派给 `inst.operator`，实例保持 10 |
| `7` | `DELEGATE` | 转办 | `processTask/delegate` 端点（F-69）|
| `20` | `COUNTERSIGN_DISAGREE` | 会签拒绝 | 一票否决模式立即流转 + 余者 ABANDON |

> **提交类型不可跨实例**：每个 submitType 仅当次操作留痕，**不随行复活**——退回上一步新建的待办**不带** `submitType` 键（详见下文「退回上一步」第 5 条）。

---

## 启动流程

```
start_process_instance_by_id(define_id, operator, args) → ProcessInstance
```

**语义**：

1. 加载流程定义，解析为 ProcessModel
2. 创建 ProcessInstance（`state=10 DOING`）
3. 保存实例到仓库
4. 执行 start 节点 → 遍历输出边 → 创建第一个任务（发起申请节点，actor=发起人）
5. 任务的 actor 根据 `assignee` / `assignmentHandler` 解析
6. 保存任务和参与者记录

**startAndExecute 契约**（调用方约定，引擎不内置）：

```
start_and_execute(define_id, operator, args) → ProcessInstance
```

1. 调用 `start_process_instance_by_id`
2. 获取所有进行中任务，逐个自动完成（`submitType=0 APPLY`）
3. 流程由此推进到第一个真正的审批节点

> 引擎不自动执行第一个任务——这是调用方的职责（mldong 框架模式），本仓 `/wf/processInstance/startAndExecute` 端点遵循此契约。

---

## 完成任务

```
execute_process_task(task_id, operator, args) → ProcessInstance
```

**语义**：

1. 加载任务 → 校验权限（actor 包含 operator；`flow.admin` / `flow.auto` 恒放行，见下）
2. 任务状态 10→20，记录操作人和完成时间
3. 执行当前节点 → 遍历输出边 → 创建下一批任务
4. 若下一节点为 end → 实例状态 10→20（完成）
5. 若下一节点为 task → 创建新任务（解析 actor）
6. 若下一节点为 decision → 评估表达式 → 选择分支
7. 若下一节点为 fork → 并行创建多条路径的任务
8. 保存变更

### 系统代执行（flow.auto / flow.admin）

> v1.0.1（集成反馈④）：对齐 mldong 框架 boot2/boot3 语义。

- **权限放行**：`operator = "flow.auto"`（自动执行，发起即提交）或 `"flow.admin"`（超级管理员）时，任务权限校验直接通过，无需在参与者列表内（**忽略大小写**）。
- **变量注入跳过**：`flow.auto` / `flow.admin` 不是真实用户——引擎执行时不调用 UserProvider 注入 `u_*` 变量，流程变量保持既有值。需要 `u_*` 反映实际执行人时，由调用方（如 `startAndExecute`）在 args 中显式携带。
- **发起即提交（startAndExecute）**：启动流程后，调用方获取 doing 任务，以 `flow.auto` 逐个自动完成（`submitType=APPLY`），把流程推进到第一个真正的审批节点——apply 节点参与者为发起人（`applicant`），由 `flow.auto` 代执行，语义等价于发起人亲自提交。

---

## 驳回

```
execute_and_jump_to_end(task_id, operator, args) → ProcessInstance
```

**语义**：

1. 校验权限
2. 任务状态 10→20
3. 实例状态 10→45（已拒绝）
4. 废弃其他进行中的任务（状态 →99）

> **退回发起人 vs 驳回的区别**（业务上常混淆）：
>
> | 字段 | 驳回（`submitType=2 REJECT`）| 退回发起人（`submitType=6 ROLLBACK_TO_OPERATOR`）|
> |---|---|---|
> | 实例状态 | 10 → 45（**终结**）| 10（**保持进行中**）|
> | 后续任务 | 全部 ABANDON | 创建新 task 给发起人 |
> | 业务语义 | 流程被否决，不可再继续 | 发起人改单后重提，流程继续 |
> | 引擎方法 | `execute_and_jump_to_end` | `execute_and_jump_to_first_task_node` |

---

## 跳转

```
execute_and_jump_task(task_id, operator, args, target_task_name) → ProcessInstance
```

**语义**：

1. 校验权限
2. 任务状态 10→20
3. 在已完成的节点中找到 `target_task_name`，重新执行其输出边
4. 废弃当前未完成的任务

---

## 退回上一步（submitType=3 / ROLLBACK）

```
execute_and_jump_task(task_id, operator, args, target_task_name=None) → ProcessTask[]
```

> **本仓实测实现**（`vendor/jeeflow/engine.py:239` + `:245`）：`ROLLBACK` 路径对齐 Java `rejectTask` 语义。

**语义（本仓实测 8 步血缘版）**：

1. **序言**：校验权限 → 当前任务 10→20
2. **上一步来源 = 数据血缘**：读当前任务行的 `task_parent_id`，按它取那条历史任务行（**不按模型入边拓扑推**——拓扑版在分支/回环流会回到本实例没走过的节点）
3. **守卫 `canRejected(current, parent)`**：自当前节点的入边递归回溯，命中 `parent` 放行；入边来源是 `fork` / `join` / `start` 时**跳过该条入边**（不是"穿越"，所以分支任务想退到 fork 之前的节点会被判不通过）；其余来源节点递归
4. **无血缘**（`task_parent_id` 为 NULL 或 0）→ 引擎异常「上一步任务ID为空，无法驳回至上一步处理」，**不得静默不建单**
5. **新任务 = 上一步行复活**：节点属性（`task_name` / `display_name` / `task_type` / `perform_type` / `form_key`）取该行节点，状态 10；`variable` **只带数据类键**——保留 `f_*`（申请内容）、`u_*`（发起人快照）、`autoGenTitle`、`isFirstTaskNode`，**剔除** `submitType` / `taskName` / `tf_*` / `csv_*` 等控制类残留
6. **参与者 = 上一步行的 `operator`**（当年办上一步那个人）；若该行 `variable.isFirstTaskNode == true` 即首任务节点行，参与者改取该行 `variable.u_userId` = **流程发起人**
7. `expire_time` 按**被回退的那个**节点的到期表达式重算；实例保持 `DOING(10)`
8. 新行的 `task_parent_id` 随行拷贝（= "上一步的上一步"，与 mldong-boot2 现状一致）

> **本仓提交剔除**（step 5 关键）：剔 `tf_*` 是刻意为之——非必填字段第一次填了、第二次不填时，整包克隆会把上次提交值带进新待办，用户会看到"我没提交这个怎么显示了"。⇒ 新待办的任务级表单从空白开始。

> **不变量**：引擎每次新建任务行必写 `task_parent_id`（发起 execution 无当前任务时写 `0`）与 `variable.isFirstTaskNode`（该行节点是否 start 直接后继）。该标记属**引擎控制键**：出口 `taskRowToMap` 判「任务变量是否为空 ⇒ 回退实例变量」（issues/82-3 契约）时**必须先忽略控制键**——否则新建任务的 ext 从此永不再回退，实例变量在待办列表里静默丢失。

> **FIX-T114 §118 实测警示**（详见 `../ToT/guides/02-flow-definition.md` §场景一 + `../docs/known-issues.md §118`）：
> - `submitType=3/4` 的 `task_name` / `target_task_name` 参数可放在**顶层**或 **`variables` 内**，facade 已兼容两位置
> - **若不传 taskName**（默认 ROLLBACK），引擎按 FIX-T36 §52 行为覆写 `assignee = 前任务完成人 or operator`，原 assignee 失去 re-process 能力
> - **设计师期望原 assignee 重新处理**时**必须显式传 taskName**

---

## 会签

会签在普通任务基础上增加：

- **并行会签**：为每个 actor 创建独立任务，全部完成才驱动下一步
- **串行会签**：一次只创建一个任务，完成后创建下一个 actor 的任务
- **按比例会签**：完成率达到阈值即驱动下一步

> 会签的 actor 存储在流程变量中：`{COUNTERSIGN_PREFIX}_{taskName}_operatorList`（本仓具体常量名见 `vendor/jeeflow/engine.py:CS_*`）
>
> 三种模式 + 一票否决 + 拓扑约束详见 `../ToT/guides/02-flow-definition.md` §2.5。

---

## 流程变量约定

引擎自动注入以下变量（前缀 `u_` 表示用户信息）：

| 变量名 | 来源 | 说明 |
|---|---|---|
| `u_userId` | `IUserProvider` | 当前操作人 ID |
| `u_realName` | `IUserProvider` | 当前操作人姓名 |
| `u_deptId` | `IUserProvider` | 部门 ID |
| `u_deptName` | `IUserProvider` | 部门名称 |
| `u_postId` | `IUserProvider` | 岗位 ID |
| `u_postName` | `IUserProvider` | 岗位名称 |
| `autoGenTitle` | 引擎自动生成 | `${realName}的${displayName}-${时间}` |
| `BUSINESS_NO` | 业务方传入 | 业务流水号 |
| `submitType` | 操作时传入 | 全枚举见 §submitType 表 |
| `isFirstTaskNode` | 引擎建单时写入 | **引擎控制键**——判「任务变量是否为空」时须忽略 |

> **关键约束**（FB-0011 / FIX-DOC-4 §115）：
> - `u_*` 仅在执行上下文，**不写回实例变量**——详细见 `../ToT/guides/02-flow-definition.md` §2.3 注解
> - `submitType` **仅当次操作留痕，不随行复活**——退回上一步新建的待办**不带**该键
> - `f_*`（启动时）持久化到 `inst.variables`，跨 task 可见；`tf_*`（执行时）运行时透传，**不持久化**，决策 expr 读不到

---

## 聚合根方法清单（跨语言 DDD 契约）

> **本仓实现**：`vendor/jeeflow/model.py:112 ProcessInstance` + `:230 ProcessTask`（dataclass + 方法）。引擎薄编排（`engine.py:execute_node` / `decision evaluation` / `actor resolution` / `repository`），业务规则收敛到聚合根。

### ProcessInstance（聚合根）

| 行为 | 说明 |
|---|---|
| `create` | 工厂——创建流程实例（state=10）|
| `complete_task(task, operator, vars)` | 完成任务（子实体状态转换 + 实例变量合并）|
| `abandon_task(task)` | 废弃单个任务 |
| `abandon_all_doing()` | 废弃所有进行中任务 |
| `finish()` | 流程完成（state 10→20）|
| `reject()` | 驳回（state 10→45）|
| `add_variable(vars)` | 追加流程变量 |
| `create_task(...)` | 创建任务（子实体工厂）|
| `get_doing_tasks()` / `get_done_tasks()` | 查询 |
| `is_all_tasks_finished()` | join 合并判断 |

### ProcessTask（子实体）

| 行为 | 说明 |
|---|---|
| `finish(operator, vars)` | 完成任务（10→20，记录操作人/完成时间）|
| `abandon(abandoned_by)` | 废弃（10→99，FIX-T111 §112）|
| `is_allowed(operator)` | 参与者权限判断 |
| `is_doing()` / `is_finished()` | 状态判断 |

### 本仓 Python 实现位置

| 角色 | 本仓位置 |
|---|---|
| 聚合根 | `vendor/jeeflow/model.py:112 ProcessInstance` + `:230 ProcessTask` |
| 引擎（薄编排）| `vendor/jeeflow/engine.py` |
| submitType 枚举 | `vendor/jeeflow/model.py:70 SubmitType(IntEnum)` |
| 流程变量常量 | `vendor/jeeflow/engine.py:KEY_NEXT_NODE_OPERATOR` 等 |

> 引擎保留：流程遍历（`execute_node`）、决策求值、参与者解析、仓储调用。任务状态转换/创建等业务规则一律收敛到聚合根。

---

## 设计者实践速查

| 场景 | submitType | 实例终态 | 关键参数 |
|---|---|---|---|
| 同意 / 通过 | `1` AGREE | 推进或 → 20 DONE | — |
| 拒绝（流程否决）| `2` REJECT | → 45 REJECT + 余者 ABANDON | — |
| 退回上一步 | `3` ROLLBACK | 保持 10 DOING | 可选 `task_name` / `target_task_name` |
| 跳转指定节点 | `4` JUMP | 保持 10 DOING | **必须显式传** `task_name` |
| 重新提交（驳回后）| `0` APPLY / `5` RESUBMIT | 推进 | — |
| 退回发起人 | `6` ROLLBACK_TO_OPERATOR | 保持 10 DOING | — |
| 转办 | `7` DELEGATE | 保持 10 DOING | `target_user_id` |
| 会签拒绝 | `20` COUNTERSIGN_DISAGREE | → 45 REJECT（一票否决模式）| 仅 ONE_VOTE_VETO 生效 |