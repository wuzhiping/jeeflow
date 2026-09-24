# 第 6 章 · 发起与办理

> **来源**：https://jeeflow-doc.mldong.com/manual/06-start-and-approve
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**操作手册第 6 章**——发起页与办理弹窗的每个开关、submitType 路由语义、5 种退回方式与「撤回」的区别。
>
> **本仓实测**：基于 `vendor/jeeflow/facade.py`（`processInstance/startAndExecute`、`processTask/execute`、`processInstance/withdraw`、`processTask/transfer`）+ `engine.py` 9 submitType 路由。
>
> **裁剪记录**：§1 发起 + §2 办理（3 子节）+ §3 退回发起人后怎么办 + §4 撤回与重新发起 + §5 已办与抄送 + §6 想跳过某个节点**保留**+ 加本仓实测注解；§7 卡住了（8 排错）**重写为本仓实测**。

---

## §1. 发起

两个入口，效果一样：

| 入口 | 位置 |
|---|---|
| **发起申请**（推荐）| 工作流程 → 发起申请，按流程分类分组的卡片 |
| **流程定义列表** | 工作流程 → 流程定义，某行的 **发起** 按钮 |

点卡片右侧滑出 **启动流程** 抽屉，两个页签：**表单**（要填的业务数据）+ **流程图**（这条流程长什么样）。

要点：

- 带星号的字段必填，漏填点确认会红字提示
- 流程属性里开了 **是否发起时选人**，抽屉里会多一个选人框（`f_nextNodeOperator`），用来指定第一个审批节点由谁办
- 点 **确认** 走的是 `startAndExecute`：**发起申请节点由引擎自动办结**，所以你不会在自己的待办里看到"发起申请"

> **本仓实测**（`facade.py:155 _startAndExecute` + `engine.py:_resolve_actors`）：
>
> ```bash
> # facade 启动 + 自动完成申请节点
> POST /wf/processInstance/startAndExecute
> {
>   "processDefineId": "<id>",
>   "operator": "<发起人>",
>   "f_title": "...",
>   "f_amount": 1000,
>   "f_nextNodeOperator": "<可选指定第一步处理人>"
> }
> ```
>
> - `f_nextNodeOperator` 字段（**v1.6.0 起**）：发起时预指派第一个业务节点处理人，引擎自动转 `tf_nextNodeOperator`（最高优先，覆盖 `assignee` / `assignmentHandler`）
> - 同名流程有多个版本时，发起用的是**启用状态下的最新版本**
> - 详见 `../spec/06-facade.md` §2.7 + §4.2 + `../spec/04-engine-ops.md` §startAndExecute

---

## §2. 办理

审批人在 **我的待办** 里看到任务，点行末 **办理** 打开审批详情。

弹窗分三块：页签（详情 / 流程图 / 审批记录）、业务表单区、操作区域。

### 2.1 业务表单区

> 这个节点能看到哪些字段、能不能改，由 `manual/03-forms.md` §4 字段权限决定。演示数据里审批节点的请假字段全是灰的，只能看不能改。

### 2.2 操作区域

| 项 | 说明 |
|---|---|
| **审批意见** | **必填**，不填点任何按钮都会被拦下（`tf_approvalComment`） |
| 上传附件 | 选填，会随审批记录留痕（`tf_approvalAttachment`） |
| 指定下一节点处理人 | 勾上后必须选人，可选名单来自节点的候选配置（`tf_nextNodeOperator`）|
| 是否抄送 | 勾上后选抄送人，对方在 **我的抄送** 里能看到（`tf_ccActors`） |

> **本仓实测**（`facade.py:707 processTask_execute`）：`tf_*` 前缀变量在任务执行时透传，**不持久化**到实例变量（`f_*` 持久化）。详见 `../spec/04-engine-ops.md` §流程变量约定。

### 2.3 底部按钮（按节点 properties.operationButtons 控制显示）

| 按钮 | submitType | 引擎方法 | 效果 |
|---|---|---|---|
| 同意 | `1` AGREE | `execute_process_task` | 按条件分支流转到下一节点 |
| 不同意 | `2` REJECT | `execute_and_jump_to_end` | 实例置为已拒绝，流程结束 |
| 退回上一步 | `3` ROLLBACK | `execute_and_jump_task`（血缘版）| 退回上一个审批节点，由上一个人重办 |
| 退回发起人 | `6` ROLLBACK_TO_OPERATOR | `execute_and_jump_to_first_task_node` | 实例仍在进行中，给**发起人**建一条新待办 |
| 跳转 | `4` JUMP | `execute_and_jump_task(target=task_name)` | 选一个可达节点直接跳过去 |
| 加签 | — | — | 仅会签节点：临时追加处理人 |
| 会签不同意 | `20` COUNTERSIGN_DISAGREE | `execute_process_task` + `countersignDisagreeFlag=1` | 仅 `ONE_VOTE_VETO` 模式直接推进整单 |

> **本仓实测 9 submitType 路由**（`engine.py` + `facade.py`）：
>
> - 退回 / 跳转 / 拒绝 走不同引擎方法（详见 `../spec/04-engine-ops.md` §退回上一步）
> - 跳转需要**显式传** `task_name`（`jumpAbleTaskNameList` 获取）
> - `submitType=3/4` 的 `task_name` / `target_task_name` 参数可放**顶层**或**`variables` 内**（facade 兼容两位置）—— **不传 taskName** 默认按 ROLLBACK 行为覆写 `assignee`
>
> 详见 `../spec/06-facade.md` §2.8 + `../spec/04-engine-ops.md` §submitType 协议 + `../docs/known-issues.md §118`。

---

## §3. 退回发起人后怎么办

审批人点 **退回发起人** 后，发起人的 **我的待办** 会出现一条待办：

发起人进去改表单（该节点上字段是可编辑的）、补审批意见，再点 **同意**（`submitType=5 RE_APPLY` 重新提交），流程按新的条件分支重新往下走。

**这是唯一「改单重提」的路径**——**拒绝**（`submitType=2`）是直接结束，**没有重来的机会**。

> **本仓实测**（`engine.py:272 _handle_jump_to_first_task`）：
>
> - 第一个任务节点重新执行，参与者强制为发起人（`inst.operator`）
> - 实例保持 `state=10 DOING`
> - 新任务 `task_parent_id` 记录发起人节点历史关系
>
> 详见 `../spec/04-engine-ops.md` §退回发起人。

| 行为对比 | 退回发起人（`submitType=6`）| 拒绝（`submitType=2`）| 退回上一步（`submitType=3`）|
|---|---|---|---|
| 实例状态 | `10` 进行中 | `45` 已拒绝 | `10` 进行中 |
| 后续任务 | 新建给发起人 | 全部 ABANDON | 新建给上一步办理人 |
| 业务语义 | 审批不通过可改 | 流程彻底否决 | 审批不通过回到上游 |
| 引擎方法 | `execute_and_jump_to_first_task_node` | `execute_and_jump_to_end` | `execute_and_jump_task`（血缘版）|

---

## §4. 撤回与重新发起

在 **我发起的** 里，进行中的实例可以：

| 操作 | 效果 |
|---|---|
| **撤回** | 实例置为已撤回（`state=30`），审批人的待办同时清空（级联）|
| **抄送给** | 主动把这条单子抄送给别人 |
| **详情** | 看表单、流程图高亮、审批记录 |

撤回后可以重新发起一条新的。

> **本仓实测**（`facade.py:565 processInstance_withdraw`）：
>
> - 3 条归属判据：① operator = 实例发起人；② operator = 实例任一进行中任务的参与者；③ operator ∈ {`flow.auto`, `flow.admin`}
> - 缺 operator → 报 `99999999` + `operator 必填`（**不回落到 `user1`**）
> - 进行中任务级联置 `WITHDRAW(30)`；已完成(20) / 已终止(40) 任务行**不被改写**
> - 跨栈字面量统一 msg（`spec/06-facade.md` §失败 msg 表）
>
> 详见 `../spec/06-facade.md` §4.2 + `../ToT/guides/05-scenarios.md` 场景一。

---

## §5. 已办与抄送

| 视图 | 含义 |
|---|---|
| **我的已办**（`processTask/doneList`）| 自己办过的任务，只有 **详情**。operator 过滤 = `t.operator EQ operator AND t.task_state <> 10`，**含**撤回(30) / 终止(40) / 废弃(99) |
| **我的抄送**（`processInstance/ccList`）| 别人抄送给我的单子，只有查看权，不产生待办。`cc.actor_id EQ operator` |

> **本仓实测**（`facade.py:654 processTask_doneList` + `:1457 processInstance_ccList`）：详见 `../spec/06-facade.md` §2.5 operator 约定。

---

## §6. 想跳过某个节点

三种办法，按侵入性从小到大：

1. **办理时点跳转**，直接选目标节点（`submitType=4 JUMP`）
2. **条件分支表达式写得足够宽**，本来就该跳
3. **改流程重新部署**（只影响新发起的实例）

> **本仓实测**（`engine.py:_handle_rollback_jump:245`）：
>
> - 跳转必须**显式传 `taskName`**（从 `processTask/jumpAbleTaskNameList` 端点获取可选节点列表）
> - 不传 `taskName` 默认按 ROLLBACK 行为覆写 `assignee`（FIX-T114 §118）
>
> 详见 `../spec/04-engine-ops.md` §跳转。

---

## §7. 卡住了看这里（重写为本仓实测）

| 现象 | 原因 | 处理 |
|---|---|---|
| 点确认没反应也没报错 | 表单里有必填项没填 | 看红字提示 |
| 待办列表里找不到自己的单子 | 参与人解析没派到你名下，或已被别人办掉 | 见 `manual/05-participants.md`；到 **我发起的 → 详情 → 审批记录** 看实际派给了谁 |
| 审批意见填了仍提示必填 | 输入后未失焦，受控组件没同步 | 点一下别处再提交（前端问题，非本仓引擎）|
| 想改已提交的单子 | 已办节点不可回改 | 让当前办理人 **退回发起人**（`submitType=6`），或自己撤回后重发 |
| 撤回后审批人还能看到 | 审批人页面未刷新 | 刷新待办；任务已随撤回删除（`processInstance/withdraw` 级联清空进行中任务）|
| 委托没生效 | 不在授权时间段内，或流程名称选错 | 检查 **我的委托** 那条记录的流程 / 时间段 / 是否启用 |
| **本仓实测补充**：跳转报 `上一步任务ID为空，无法驳回至上一步处理` | ROLLBACK 时任务 `task_parent_id` 为 `NULL` 或 `0`（如发起首条节点无上游） | 退回上一步**仅对有上游历史任务的节点生效**；首条节点请用「退回发起人」或「驳回拒绝」|
| **本仓实测补充**：submitType=20 不生效 | 会签 task 后接了 decision 节点（截断 cs_veto）| 一票否决仅在 task → end **直连**时生效（FB-0012 §116）；请调整流程拓扑 |

---

## 跨文档交叉引用

- `startAndExecute` 契约 + `f_nextNodeOperator` 预指派：`../spec/04-engine-ops.md` §启动流程
- 9 submitType 路由 + 失败 msg 跨栈字面量：`../spec/06-facade.md` §2.8 + 「失败 msg 跨栈统一文案」
- 退回发起人 vs 拒绝 vs 退回上一步对比：`../spec/04-engine-ops.md` §驳回与跳转
- 撤回 3 条归属判据 + 级联落库：`../spec/06-facade.md` §4.2 processInstance/withdraw
- 我的已办 / 我的抄送 operator 过滤口径：`../spec/06-facade.md` §2.5
- 字段权限控制可改字段：`manual/03-forms.md` §4
- 参与人解析 4 优先级 + 7 handler：`manual/05-participants.md` §1 + §3
- 跳转必须显式传 taskName（FIX-T114 §118）：`../docs/known-issues.md §118`