# 设计原理 06 · 契约约定——引擎与调用方的边界

> **来源**：https://jeeflow-doc.mldong.com/concepts/06-contracts
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**契约约定原理参考**——理解「发起申请节点 = `assignee="applicant"`」「submitType 9 枚举」「`u_*` 7 变量」等设计契约的来源与边界，是编写流程 JSON 与跨框架移植的前提。
>
> **本仓实测**：`vendor/jeeflow/model.py:70 SubmitType(IntEnum)` + `engine.py:_resolve_actors`（applicant 解析）+ facade 9 submitType 路由。
>
> **裁剪记录**：§1-§5 / §7 保留 + 加本仓实测；§6.1 端点清单保留并重写为本仓 60+ action；§6.2 mldong 框架差异裁掉（与本项目无关）；§6.3 重写为本仓实测对齐；§6.4 服务地址裁掉 6 语言仅留本仓 :8101。

---

## §1. 为什么需要"契约"

引擎核心是**中立**的：它不知道你的业务是请假还是报销，也不知道"驳回后发起人该收到什么"。但六版 demo 必须行为一致、且能与 mldong 框架生态对接——所以把"业务层怎么做"固化成**契约**，调用方遵守契约，引擎不内置。

```
引擎（中立）            契约（本文件）            调用方（业务层）
  │                       │                        │
  │ 创建任务             assignee="applicant"      │ 启动后自动完成申请节点
  │ 完成任务             → 解析为发起人             │
  │ 跳转节点             submitType 枚举           │ REJECT → 跳结束（实例 45）
  │ 变量注入             u_* 前缀                  │ 决策表达式引用 u_*
```

---

## §2. 契约一：发起申请节点

**约定**：每个流程 `start` 后的第一个任务节点是"发起申请"节点，`assignee` 使用特殊值 `"applicant"`。

```json
{
  "id": "apply",
  "type": "snaker:task",
  "properties": { "assignee": "applicant", "performType": 0, "taskType": 0 },
  "text": { "value": "发起申请" }
}
```

**引擎行为**：解析参与者时 `"applicant"` 替换为 `instance.operator`（发起人）。

> **本仓实测**（`vendor/jeeflow/engine.py:_resolve_actors`）：`"applicant"` 命中 `inst.operator` 字段解析为发起人 userId；token 优先按 `inst.variables` 解析（list / tuple 展开）。

**调用方行为**（`startAndExecute`）：

```
1. start_process_instance_by_id
2. 取所有进行中任务，逐个 execute_process_task（submitType=0 APPLY）
```

**为什么这么设计**：

- 流程定义里能看到完整的业务闭环（发起 → 审批 → 结束），而不是"审批流从中间开始"
- 审批记录里保留了发起人节点（`approvalRecord` 完整）
- 退回发起人时（`submitType=6`），第一个任务节点重新执行并强制指派给发起人 = 给发起人建待办（§4 demo 约定）

> 详见 `../ToT/guides/02-flow-definition.md` §3 + `../spec/04-engine-ops.md` §启动流程。

---

## §3. 契约二：submitType 枚举

| code | 枚举 | 含义 | 引擎调用 |
|---|---|---|---|
| `0` | `APPLY` | 发起申请 | `execute_process_task` |
| `1` | `AGREE` | 同意申请 | `execute_process_task` |
| `2` | `REJECT` | 拒绝申请 | `execute_and_jump_to_end`（跳结束，实例→45）|
| `3` | `ROLLBACK` | 退回上一步 | 回溯上一任务节点 → `execute_and_jump_task` |
| `4` | `JUMP` | 跳转 | `execute_and_jump_task(..., task_name)` |
| `5` | `RE_APPLY` | 重新提交 | `execute_process_task` |
| `6` | `ROLLBACK_TO_OPERATOR` | 退回发起人 | `execute_and_jump_to_first_task_node` |
| `20` | `COUNTERSIGN_DISAGREE` | 会签拒绝：默认软拒绝（flag 记录不阻断）；节点 `countersignCompletionCondition=ONE_VOTE_VETO` 时一票否决推进整单 | `execute_process_task` + `countersignDisagreeFlag=1` |

> **本仓实测**（`vendor/jeeflow/model.py:70 SubmitType(IntEnum)`）：9 枚举完整对应。枚举**取值与行为**均与 mldong 框架的 `ProcessSubmitTypeEnum` 一致——这是 mldong 生态前端能直接对接的前提。

---

## §4. Demo 层约定：submitType 行为（与 mldong 框架一致）

> **本节约定为 demo 参考实现的行为，不是引擎契约**。引擎只提供跳转能力（`execute_and_jump_to_end` / `execute_and_jump_task` / `execute_and_jump_to_first_task_node`），具体"提交类型做什么"由调用方决定（demo 与 mldong 框架完全一致）。

**约定**：

| submitType | 调用方动作 | 效果 |
|---|---|---|
| `2 REJECT` | `execute_and_jump_to_end` | 当前任务完成、其余进行中任务废弃，实例→**45 已拒绝**，无新待办 |
| `3 ROLLBACK` | 沿边回溯上一个任务节点 → `execute_and_jump_task` | 退回上一步审批人，实例保持 10 |
| `4 JUMP` | `execute_and_jump_task(..., task_name)` | 跳到指定已办节点（task_name 取自 `jumpAbleTaskNameList`）|
| `6 ROLLBACK_TO_OPERATOR` | `execute_and_jump_to_first_task_node` | 第一个任务节点重新执行、参与者强制为发起人 → 发起人收到新待办，实例保持 10 |

> **本仓实测**（`vendor/jeeflow/engine.py`）：
>
> | submitType | 引擎方法 | 实测位置 |
> |---|---|---|
> | `2 REJECT` | `_handle_end_jump` | `:239` |
> | `3 ROLLBACK` | `_handle_rollback_jump`（血缘版）| `:245` |
> | `4 JUMP` | `_handle_rollback_jump`（target_task_name 命名版）| `:245` |
> | `6 ROLLBACK_TO_OPERATOR` | `_handle_jump_to_first_task` | `:272` |
>
> 详见 `../spec/04-engine-ops.md` §退回上一步 + `../ToT/guides/05-scenarios.md` 场景一。

**退回 vs 硬驳回**：

| 退回（`submitType=6`）| 硬驳回（`submitType=2`）|
|---|---|
| 实例状态 **10 进行中** | 实例状态 **45 已拒绝** |
| 发起人收到新待办，可重新提交 | 发起人无待办 |
| 适用：审批不通过但可修改重提 | 适用：流程彻底终止 |

---

## §5. 契约四：流程变量注入

引擎每次操作自动注入用户信息（key 与 mldong 框架一致）：

| 变量 | 来源 | 示例 |
|---|---|---|
| `u_userId` | `UserProvider.get_user` | `"user1"` |
| `u_realName` | `UserProvider.get_user` | `"张三"` |
| `u_deptId` / `u_deptName` | `UserProvider.get_user` | `"D01"` / `"技术部"` |
| `u_postId` / `u_postName` | `UserProvider.get_user` | `"P01"` / `"工程师"` |
| `BUSINESS_NO` | 业务方传入 args | `"BIZ-123"` |
| `submitType` | 操作时传入 | `0/1/2/3/4/5/6/20` |

> **本仓实测**（`vendor/jeeflow/engine.py:_resolve_actors` + `_resolve_operator`）：
>
> - `u_*` 注入到 `inst.variables`（**仅执行上下文，不写回实例**，FIX-T9 §66）
> - `UserInfo` 含 6 字段（`user_id` / `real_name` / `dept_id` / `dept_name` / `post_id` / `post_name`）
> - 注入跳过：`flow.auto` / `flow.admin`（系统代执行）—— `engine.py` 校验系统代执行不调 UserProvider
> - `submitType` **仅当次操作留痕，不随行复活**——退回上一步新建的待办不带该键
>
> 详见 `../spec/04-engine-ops.md` §流程变量约定 + `../ToT/guides/06-deployment.md` §5.1。

**为什么 key 必须和 mldong 框架一致**：决策表达式（`u_deptId == 'D01'`）是流程定义的一部分，如果 jeeflow 用别的 key，同一份流程定义在 mldong 框架和 jeeflow 上行为不同——契约就是"同一份 JSON 双端可移植"。

---

## §6. Demo 接口层（参考实现，非引擎契约）

> ⚠️ **这不是"通用约定"**。以下接口是六版 demo 为对齐 mldong 快速开发框架的接口规范而提供的**参考实现**。本仓 `facade.py:63 JeeflowFacade.flow(action, args)` 是契约的具体实现 + `60+ action`。

### 6.1 端点清单（本仓实测 60+ action）

> **本仓实测**：`vendor/jeeflow/facade.py:63 flow(action, args)` 统一入口，**60+ action** 完整覆盖上游 demo 端点 + 本仓新增：

| 类别 | action 路径 | 数量 |
|---|---|---|
| 流程定义 | `processDefine/{page,detail,startAndExecute,deploy,redeploy,remove,upAndDown,getLastByName,getJobCardContent}` | **9** |
| 流程实例 | `processInstance/{page,export,detail,startAndExecute,rollback,doingList,withdraw,bizData,highLight,approvalRecord,getAssigneeTextData,createCCInstance,updateCCStatus,ccList,suspend,resume,stats_overview,stats_trend,stats_group}` | **19** |
| 流程任务 | `processTask/{todoList,doneList,execute,detail,jumpAbleTaskNameList,candidatePage,surrogate,addCandidate,removeCandidate,latest,transfer,transferAndAdd,comment,extra,delegate,delegateHistory,withForm}` | **17** |
| 流程设计 | `processDesign/{page,designHis_page,detail,save,update,updateDefine,deploy,redeploy,remove,listByType}` | **10** |
| 委托代理 | `processSurrogate/{page,save,update,detail,remove}` | **5** |
| 审计 | `auditLog/export` | **1** |
| **合计** | — | **60+** |

> 完整契约详见 `../spec/06-facade.md` §3 清单。

### 6.3 已对齐的部分（本仓实测）

> **裁剪说明**：上游 §6.2 mldong 框架差异表与本项目无关（私用项目不引入其他框架）；上游 §6.4 服务地址 6 语言表裁掉仅留本仓 :8101。本节仅保留"已对齐部分"重写为本仓实测。

| 类别 | 本仓实测状态 |
|---|---|
| **路径前缀** | `/wf/*` 与上游一致；`processInstance/highLight` / `approvalRecord` 为独立端点 |
| **`submitType` 枚举** | 9 枚举（`0/1/2/3/4/5/6/20`）取值与行为与 mldong 框架完全一致，含 `countersignDisagreeFlag` |
| **响应结构** | `code=0/99999999`（引擎失败码恒 99999999）；`code/msg/data` 三字段结构对齐 mldong `CommonResult` |
| **分页结构** | `code=0` + `{pageNum, pageSize, recordCount, totalPage, rows}` 对齐 mldong `CommonPage` |
| **`jsonObject` / `highLight` / `activeTaskList` / `taskActorIdList`** | 与 mldong 框架 VO 一致，可直接喂上游设计器组件 |
| **服务地址** | 本仓 `:8101`（内存）或 `:8102`（PG），跨后端 `main.py` / `main_pg.py`；上游文档 `:8100` 是其他语言后端默认端口 |

### 6.4 与 mldong 框架的差异（如实声明）

> **裁剪说明**：上游 §6.2 表与本项目无关（私用项目不引入 mldong 框架），整段裁掉。本节保留供读者了解：本仓未实现登录态 / 鉴权 / 抄送 facade —— 详见 `../ToT/guides/05-scenarios.md` 场景五（抄送）+ `../ToT/guides/10-mldong-integration.md` §5.3。

---

## §7. 契约变更的影响

契约变更 = 流程定义变更 + 调用方变更 + 前端变更，三者必须同步。因此：

- 契约条文进 [SPEC.md](../spec/)（唯一事实来源）
- 六版 demo 是契约的参考实现（也是合规测试的验证对象）
- 新增契约（如"会签完成条件"）需先在 SPEC 定稿，再实现

> **本仓合规验证**：`docs/BUGS.md` 27 个已修复 BUG + 0 个仍存（v1.9.0 2026-09-19 里程碑）；`vendor/jeeflow/spec/08-compliance.md` 27 场景全 PASS；`ToT/sop/ea-compliance.py` 44/44 PASS。

---

## 跨文档交叉引用

- 启动流程 + `applicant` 解析 + `startAndExecute` 契约：`../spec/04-engine-ops.md` §启动流程
- submitType 9 枚举完整语义 + 退回 / 跳转 / 一票否决 + 拓扑约束：`../spec/04-engine-ops.md` §submitType 枚举 + `../ToT/guides/02-flow-definition.md` §2.5
- `u_*` 7 变量注入实测 + 决策表达式作用域铁律（FB-0011）：`../ToT/guides/06-deployment.md` §5.1 + `../docs/known-issues.md §115`
- Facade 60+ action 完整契约（响应结构 / 分页 / id 字符串化）：`../spec/06-facade.md`
- 27 合规测试场景 + 流程 JSON 契约维持：`../spec/08-compliance.md`