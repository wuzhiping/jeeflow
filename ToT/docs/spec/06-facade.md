# 规范 06 · 统一门面（JeeflowFacade）完整接口文档

> **来源**：https://jeeflow-doc.mldong.com/spec/06-facade
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**统一门面契约参考**——理解每个 action 的输入参数 / 返回结构 / 设计语义是正确调用的前提。
>
> **本仓实现版本**：`vendor/jeeflow/facade.py:63 JeeflowFacade.flow(action, args)`；**实际 `/wf/{action}` 公开端点 = 57**（`./docs/openapi.json` 实测；2026-09-24 修正：原 PRD「38」为 v1.0.0 基线）。
> **facade 内部**：`_*` 私有方法约 83 个（路由方法）+ 25 个 internal helper（`_flow_with_trace` / `_verify` / `_deploy` 等）= 共 108 个下划线方法。
> **唯一 action 名 = 47**（`./docs/actions.md` 数；含 2 个公共别名 `startAndExecute` / `taskAddActor`）。
> **增量来源**：本仓新增 `transferAndAdd` / `delegate` / `delegateHistory` / `withForm` / `comment` / `extra` / `suspend` / `resume` / `stats/overview` / `stats/trend` / `stats/group` / `getJobCardContent` / `processDesignHis/page` 等 19 个。
>
> **裁剪记录**：§1 / §2 / §3 / §4.1-§4.6 / §5 / §7 保留 + 加本仓实测注解；§6 集成 SPI 表裁掉（属框架集成者职责）；失败 msg 文案表跨栈字面量统一保留。

---

## §1. 入口契约

```
flow(action, args) → {code, msg, data}
```

| 项 | 规范 |
|---|---|
| `action` | boot2/boot3 端点路径的短名（见 §3 清单）|
| `args` | 业务参数 Map（分页 / 过滤 / 表单 / operator 等）|
| 返回结构 | `{ "code": 0, "msg": "成功", "data": {...} }` |
| 失败码 | `code = 99999999`（引擎内统一），`msg` 为失败原因 |
| 异常处理 | 门面内部异常捕获转 `{code: 99999999, msg: 异常信息}`，不向上抛 |
| 未知 action | `{code: 99999999, msg: "未知 action: xxx"}` |

> **本仓实测**（`vendor/jeeflow/facade.py:63`）：`flow()` 通过 `_dispatch_action()` 路由到 `_processDefine_*` / `_processInstance_*` / `_processTask_*` / `_processDesign_*` / `_processSurrogate_*` 等 **57 个公开 action + ~83 个 _* 路由方法**（含 25 个 internal helper）；统一过 `_verify(args)` (facade.py:107) 参数校验、`_ok(data)` (facade.py:1795) / `_ok_with_stringify_ids(data)` (facade.py 内 `flow()` 调用点 :79 / :98) 出口封装。

**HTTP 约定**：

- 所有 action 走 **POST**，路径 `/wf/{action}`（vben5 风格）
- body = JSON 对象（`Content-Type: application/json`）
- 登录鉴权由集成方框架层完成，门面本身不感知登录态

---

## §2. 全局约定（10 子节）

### §2.1 统一响应

| code | 含义 |
|---|---|
| `0` | 成功 |
| `99999999` | 业务失败（msg 为原因）|
| 其他 | 集成方框架层错误（401 未登录 / 403 无权限等，由框架自身返回）|

### §2.2 分页结构（page 类 action）

```json
{
  "pageNum": 1,
  "pageSize": 10,
  "recordCount": 25,
  "totalPage": 3,
  "rows": [...]
}
```

**过滤参数**：`m_` 前缀三段式 `m_{别名}_{操作符}_{列名}`：

| 形式 | 示例 | 含义 |
|---|---|---|
| `m_{op}_{column}` | `m_EQ_taskName=leaveApply` | 主表 `t.task_name = 'leaveApply'` |
| `m_{alias}_{op}_{column}` | `m_t_LIKE_displayName=请假` | `t.display_name LIKE '%请假%'` |
| `m_pd_{op}_{column}` | `m_pd_LIKE_name=simple` | 实例列表按流程定义搜：`pd.name LIKE '%simple%'`（别名 `pd` → 关联的流程定义表） |

操作符：`EQ` `LIKE` `GT` `LT` `GE` `LE` `IN` …（标准 SQL 语义）。

### §2.3 id 字符串契约（重要）

- 引擎 id 为 **64 位雪花 / BIGINT**——超 JS `2^53` 丢精度
- **本仓实测**（`vendor/jeeflow/facade.py:2444 _stringify_ids`）：递归处理 dict / list / dataclass；id 类字段（`id` / `endswith Id`）int → str；dataclass 分支（issues/76 FIX）收口"嵌套 dataclass 列表整表外泄 int id"
- **嵌套对象同契约**：列表 / 嵌套行（如 `processDesign/detail` 的 `his[]`、`processInstance/detail` 的 `tasks[]` / `activeTaskList[]`）的 `id` / `*Id` 键与顶层同契约
- **前端**：把 id 当字符串处理（不做数值运算、不 `parseInt`）
- **集成层硬要求**：`Long→ToStringSerializer` 必须配到宿主 Web 层（mldong-boot2/3/4 的 `WebMvcConfig` 已配；裸 Spring Boot 需自查）

### §2.4 时间格式

- 一律 `yyyy-MM-dd HH:mm:ss`（如 `2026-08-06 10:30:00`）
- 空值返回 `null`
- **基准由宿主注入时钟决定**（issues/120）——本仓 Python 取宿主系统时间

### §2.5 operator 约定

| action | 过滤列 | 语义 |
|---|---|---|
| `processInstance/page` | `t.operator EQ operator` | 我发起的实例 |
| `processTask/todoList` | `actor_ids contains operator` | 我参与（未办结）|
| `processTask/doneList` | `t.operator EQ operator AND t.task_state <> 10` | 我办理的（不含发起人；含撤回 30 / 终止 40 / 废弃 99）|
| `processInstance/ccList` | `cc.actor_id EQ operator` | 抄送给我的 |

> `operator` 为空 → `doneList` / `ccList` 返回**空页**，不得返回全库（issues/117 §7）。

### §2.6 鉴权与权限码

- 引擎不依赖任何鉴权框架，只通过 `IActionPermissionProvider` SPI 提供「action → 权限码」映射
- 默认映射规则：`wf:{action.replace('/', ':')}`（如 `processDefine/page` → `wf:processDefine:page`）
- OR 语义：`processDefine/detail` → `wf:processDefine:detail` 或 `wf:processDesign:listByType`
- **登录即可访问**（放行）：`processInstance/detail` / `highLight` / `approvalRecord` / `bizData` / `processTask/detail` / `addCandidate` / `latest` / `getAssigneeTextData` / **`stats/overview` / `stats/trend` / `stats/group`**
- 集成方惯例：超级管理员（如 `superAdmin`）放行一切

### §2.7 表单数据约定

| 前缀 | 位置 | 含义 |
|---|---|---|
| `f_` | 发起参数 / 实例变量 | 发起表单字段（`f_amount` / `f_reason`…）|
| `tf_` | 任务执行参数 / 任务变量 | 任务表单字段（`tf_approvalComment` / `tf_approvalAttachment` / `tf_nextNodeOperator` / `tf_ccActors`）|

- 实例 / 任务行中 **`ext`** = 变量 JSON 对象（issues/124 立法：变量唯一对外出口）
- `taskFormData` = 带 `tf_` 前缀的字段（同时输出带前缀 + 去前缀两个副本）
- 发起时 `f_nextNodeOperator` 预指派（执行时自动转 `tf_nextNodeOperator`）

### §2.8 submitType 枚举

| code | 枚举 | 语义 | 引擎方法 |
|---|---|---|---|
| `0` | `APPLY` | 发起申请 | `executeProcessTask` |
| `1` | `AGREE` | 同意 | `executeProcessTask` |
| `2` | `REJECT` | 拒绝（流程直接结束）| `executeAndJumpToEnd` |
| `3` | `ROLLBACK` | 退回上一步（血缘版）| `executeAndJumpTask(target=null)` |
| `4` | `JUMP` | 跳转到指定节点（需 `taskName`）| `executeAndJumpTask(target=taskName)` |
| `5` | `RE_APPLY` | 重新提交 | `executeProcessTask` |
| `6` | `ROLLBACK_TO_OPERATOR` | 退回发起人 | `executeAndJumpToFirstTaskNode` |
| `7` | `TRANSFER` | 转办（不走 `execute`）| `removeTaskActor` + `addTaskActor` |
| `20` | `COUNTERSIGN_DISAGREE` | 会签拒绝（ONE_VOTE_VETO 才直接推进）| `executeProcessTask` |

### §2.9 状态枚举

| 状态 | code |
|---|---|
| 任务 DOING / FINISHED / WITHDRAW / INTERRUPT / PENDING / ABANDON | 10 / 20 / 30 / 40 / 50 / 99 |
| 实例 state 同任务枚举 + 45 REJECT | — |
| performType 0=普通 / 1=会签 | 兼容字符串 `'1'`/`'ALL'`/`'COUNTERSIGN'` |
| define state 1=启用 / 0=停用 | `upAndDown` 切换 |
| design isDeployed 1=已部署 / 0=未部署 | — |

### §2.10 抄送（CC）

- 发起抄送：`startAndExecute` 参数带 `f_ccActors`
- 任务中抄送：`execute` 参数带 `tf_ccActors`
- 手动抄送：`processInstance/createCCInstance`

---

## §3. action 清单（本仓 57 个 `/wf/` 端点）

> **本仓实测**（`./docs/openapi.json` 2026-09-21 实测）：**57 个 `/wf/{action}` 公开端点**（2026-09-24 修正：原 PRD「38」为 v1.0.0 基线）。
> **facade.py 实际**：108 个 `_*` 方法（83 路由 + 25 internal helper）；唯一 action 名 = 47（`./docs/actions.md`，含 2 别名）。

| 分组 | action | 数量 |
|---|---|---|
| 流程定义 | `processDefine/{page,detail,startAndExecute,deploy,redeploy,remove,upAndDown,getLastByName,getJobCardContent}` | **9** |
| 流程实例 | `processInstance/{page,export,detail,startAndExecute,rollback,doingList,withdraw,bizData,highLight,approvalRecord,getAssigneeTextData,createCCInstance,updateCCStatus,ccList,suspend,resume,stats_overview,stats_trend,stats_group}` | **19** |
| 流程任务 | `processTask/{todoList,doneList,execute,detail,jumpAbleTaskNameList,candidatePage,surrogate,addCandidate,removeCandidate,latest,transfer,transferAndAdd,comment,extra,delegate,delegateHistory,withForm}` | **17** |
| 流程设计 | `processDesign/{page,designHis_page,detail,save,update,updateDefine,deploy,redeploy,remove,listByType}` | **10** |
| 委托代理 | `processSurrogate/{page,save,update,detail,remove}` | **5** |
| 审计 | `auditLog/export` | **1** |

> 未配置 `IProcessExtRepository` 时，`processDesign/*` / `processSurrogate/*` 报错；未注入 `metaTableReader`（jeeflow-persist）时 `bizData` 明确报错（facade.py:1091）。

---

## §4. action 详解（要点）

### §4.1 processDefine/*

| action | 必填参数 | data 结构要点 |
|---|---|---|
| `page` | 分页 / 过滤 | rows: `id/name/displayName/type/state/version` + 审计字段 |
| `detail` | `id` | + `jsonObject`（流程 JSON 图）|
| `startAndExecute` | `processDefineId` / `operator` | `{processInstanceId}` |
| `deploy` | 流程 JSON 顶层展开（或 `content`）| `{processDefineId}`；按 `name` 自动 `version+1` |
| `redeploy` | `processDefineId` + 流程 JSON | `null`（成功空）|
| `remove` | `id` 或 `ids[]` | `null` |
| `upAndDown` | `id`/`ids[]` + `state`(或 `opType`) | `null` |

### §4.2 processInstance/*

| action | 必填参数 | data 结构要点 |
|---|---|---|
| `page` | `operator` + 分页 | rows: `id/parentId/processDefineId/state/businessNo/operator/ext/createTime/...` |
| `detail` | `id` | + `formData` / `jsonObject` / `tasks[]` / `activeTaskList[]` |
| `startAndExecute` | `processDefineId` / `operator` / `f_*` | `{processInstanceId}` |
| `withdraw` | `id` / **`operator`**（硬必填）| `null`；3 条归属判据（发起人 / 进行中任务 actor / `flow.auto`+`flow.admin`）|
| `bizData` | `processInstanceId`（或 `id`）| 业务表行（需 jeeflow-persist + `metaTableReader`）|
| `suspend` / `resume` | `id` | `null`；FIX-T70 |
| `stats_overview` | `start`/`end`/`stateIn` | 11 项全局指标卡；登录即可访问 |
| `stats_trend` | `start`/`end`/`granularity` | 桶数组（`hour`/`day`/`week`/`month`）|
| `stats_group` | `dimension`(9 个) / `start`/`end` / `limit` | Top N（按 count 降序）|

### §4.3 processTask/*（本仓 17 个 action）

**taskVo 通用字段**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 任务 id |
| `processInstanceId` | string | 实例 id |
| `taskName` | string | 节点名（模型节点 id）|
| `displayName` | string | 节点显示名 |
| `taskType` | string | 任务类型（task/start 等）|
| `performType` | int | 0 普通 / 1 会签 |
| `taskState` | int | 状态（§2.9）|
| `operator` | string | 当前操作人 id |
| `formKey` | string | 表单 key |
| `taskParentId` | string | **上一步任务 id**（血缘版 ROLLBACK 前驱指针）|
| `taskActorIdList` | string[] | 参与人列表 |
| `taskFormData` | object | `tf_*` 任务表单数据（带前缀+去前缀副本）|

**核心 action 列表**：

| action | 必填参数 | data 要点 |
|---|---|---|
| `todoList` | `operator` + 分页 | rows = taskRow + 审计/定义冗余/`ext`（任务变量为空时回退实例变量）|
| `doneList` | `operator` + 分页 | 同 todoList |
| `execute` | `processTaskId` / `operator` / `submitType` | `null` |
| `detail` | `id` / `operator` | taskVo + `executable` / `ext.isFirstTaskNode` / `jsonObject` / `taskModel` |
| `jumpAbleTaskNameList` | `processInstanceId` | `[{label, value}]` |
| `candidatePage` | `processTaskId`（或 `id`）| 候选 rows（含 `id`/`realName`/`userId`/`deptName`）|
| `surrogate` / `addCandidate` | `processTaskId` + `actorIds` | `null`；**追加不清空** |
| `transfer` | `processTaskId` / `fromActor` / `toActor` / `operator` | `null`；详见失败 msg 文案 |
| **`transferAndAdd`**（本仓独有，F-75）| `processTaskId` / `fromActor` / `toActor` + `actorIds` | 转移+追加，原子操作 |
| **`delegate`**（本仓独有，F-69）| `processTaskId` / `operator` / `targetUserId` | 任务级委派 |
| **`delegateHistory`**（本仓独有，F-74）| `processTaskId` | 委派历史查询 |
| **`withForm`**（本仓独有，F-76）| `processTaskId` / `formKey` | task 级表单绑定 |
| **`comment`** / **`extra`**（本仓独有）| `processTaskId` | 任务评论 / 额外变量 |
| `latest` | `processInstanceId` | taskVo（第一个 DOING 任务）或 `null` |

> **本仓实测变量出口立法**（issues/124）：变量唯一对外出口是 `ext`（实例侧）与 `instanceExt`（任务行侧）；`variable` 原串与 `variables` 全集**不是契约字段**。变量为空时 `ext` 出空对象 `{}`，不出缺键/null。

### §4.4 processDesign/*（需 IProcessExtRepository）

> 设计稿（草稿）≠ 定义（发布产物）：save/updateDefine 存草稿快照（历史表），deploy 才生成流程定义。**设计稿内容变更后 `isDeployed` 自动置 0**。

| action | 必填参数 | data 要点 |
|---|---|---|
| `page` / `designHis_page` | 分页 / 过滤 | 分页结构 + 行字段 |
| `detail` | `id` | + `jsonObject`（最新设计稿）+ `his[]`（历史快照）|
| `save` | `id`（可选）+ `name`/`displayName` + `content`（可选）| `{id}`；UPSERT（name 唯一键复用行 id）|
| `update` | `id` + 字段 | `null`（只改基本信息不写快照）|
| `updateDefine` | `processDesignId` + 设计 JSON | `null`；快照入库 + 置未部署 |
| `deploy` | `id` | `{processDefineId}` |
| `redeploy` | `id` | `{processDefineId}`（原地替换）|
| `remove` | `id` / `ids[]` | `null` |
| `listByType` | 无 | `{type: items[]}`；item 含 `processDesignId` / `processDefineId` / **`processDefineState`**（前端"发起按钮可用性"硬依赖）/ `jsonObject` |

> **`listByType` 分组序契约**：map → 有序数组时按 type 数值优先升序（数值型在前，非数值型在后）。该序由集成层 map→array 转换处保证，前端不再排序。

### §4.5 processSurrogate/*（运行期语义 + 台账 CRUD）

**v1.9.0 起内置、默认开启**（issues/116）。运行期语义 6 条：

1. **时机**：任务参与者解析完成后、参与者落库前，对**每个** actor 查一次生效委托
2. **动作**：命中则把 `surrogate` **追加**为该任务参与人；**授权人保留**，任一可办
3. **默认开启、可显式关闭**：集成方可注册空实现 / 配置开关关闭
4. **未配置 `IProcessExtRepository` 时静默跳过**
5. **查询判据**（跨栈同答案）：
   - 空 `processName` = 全部流程兜底
   - 时间窗：`start_time <= now <= end_time`
   - 自委托过滤：`surrogate <> operator`
   - **`enabled` 读写两侧分别定**：读侧只有 `1` 生效（白名单判定）；写侧键缺失 → 落 1，空串/脏值 → 落 0
6. 内存仓与 SQL 仓**两条路径都要满足第 5 条**

| action | 必填参数 | data 要点 |
|---|---|---|
| `page` | 分页 / 过滤 | rows: 委托行全字段 |
| `save` | `processName`/`surrogate`/`startTime`/`endTime`/`enabled` | `{id}` |
| `update` | `id` + 全字段 | `{id}`；operator 缺省保留原值 |
| `detail` | `id` | 单条委托行 |
| `remove` | `ids[]`（或 `id`）| `null`；空数组**报错禁止静默成功** |

### §4.6 视图端点

| action | 必填参数 | data 要点 |
|---|---|---|
| `processDefine/getLastByName` | `processDefineName` | `{id,name,displayName,type,state,version}` |
| `processDefine/getJobCardContent` | `processDefineId` + `nodeId` | Job Card markdown（按 ID 加密安全路径）|
| `processInstance/highLight` | `id` | `activeNodeNames` / `historyNodeNames` / `historyEdgeNames` / `nodeProgress` |
| `processInstance/approvalRecord` | `id` | rows: `taskName/displayName/taskType/performType/taskState/operator/finishTime/ext` |
| `processInstance/getAssigneeTextData` | `id` + `includeNodeName` | `[{value, label}]`（发起页徽标）|
| `processInstance/createCCInstance` | `processInstanceId` / `actorIds[]` / `operator` | `null` |
| `processInstance/updateCCStatus` | `processInstanceId` / `operator` | `null`（标记自己已读）|
| `processInstance/ccList` | `operator` + 分页 | 分页结构（行同 processInstance/page）|

---

## §5. 请求/响应示例

### 发起请假流程

```bash
POST /wf/processInstance/startAndExecute
{
  "processDefineId": "1864123456789012480",
  "operator": "zhangwei",
  "f_reason": "年假回乡",
  "f_days": 5,
  "f_startDate": "2026-08-10",
  "f_nextNodeOperator": "lina",
  "f_ccActors": ["chenjing"]
}
# 200 → { "code": 0, "msg": "成功", "data": { "processInstanceId": "1864123456789012999" } }
```

### 待办列表

```bash
POST /wf/processTask/todoList
{ "operator": "lina", "pageNum": 1, "pageSize": 10 }
# 200 → { code:0, data: { pageNum:1, pageSize:10, recordCount:1, totalPage:1, rows:[...] } }
```

### 审批

```bash
POST /wf/processTask/execute
{
  "processTaskId": "1864123456789013111",
  "operator": "lina",
  "submitType": 1,
  "tf_approvalComment": "同意，注意行程安全",
  "tf_nextNodeOperator": "wangqiang",
  "tf_ccActors": ["zhaomin"]
}
# 200 → { code:0, msg:"成功", data:null }
```

### 跳转（submitType=4）

```bash
# Step 1: 取可跳转节点
POST /wf/processTask/jumpAbleTaskNameList
{ "processInstanceId": "1864123456789012999" }
# → data: [{"label":"部门审批","value":"node_1"}, ...]

# Step 2: 跳转
POST /wf/processTask/execute
{ "processTaskId": "...", "submitType": 4, "taskName": "node_2" }
```

### 错误示例

```json
// HTTP 200，以 body code 判断业务成败
{ "code": 99999999, "msg": "流程定义不存在", "data": null }
```

---

## 失败 msg 跨栈统一文案（八栈必同字面量）

> **引擎失败码恒 `99999999`**，细粒度原因只由 `msg` 承载。下表为跨栈字面量统一文案（设计者调 API 时可直接据此判断失败原因）。

| 场景 | msg（逐字）|
|---|---|
| 撤回/转办/加签等缺 `operator` | `operator 必填` |
| `fromActor` 参数缺失或空 | `fromActor 必填` |
| `toActor` 参数缺失或空 | `toActor 必填` |
| 撤回人不在归属判据内 | `无权限撤回该流程实例` |
| 转办操作人非 fromActor 且非 auto/admin | `无权限转办该任务` |
| `fromActor` 不在该任务参与者里 | `原办理人不是该任务参与人` |
| `toActor` 已是该任务参与者 | `目标人已是该任务参与人` |
| 任务非进行中 | `任务非进行中，不可转办` |
| 退回上一步·无血缘（`task_parent_id` NULL/0）| `上一步任务ID为空，无法驳回至上一步处理` |
| 退回上一步·`canRejected` 守卫不过 | `无法驳回至上一步处理，请确认上一步骤并非fork、join、suprocess以及会签任务` |

> ⚠️ **码不进文案**：`20010007` / `20010008`（引擎层 `WfErrEnum` 内部码）**只留在引擎内部**，对外 `msg` 一律用上表逐字文案、不带码数字前缀。

---

## §7. 六语言行为对齐说明（本仓实测重点）

| 关注点 | 约定 |
|---|---|
| **id 出口** | 一律字符串（Node 全链路 string；Go/Python `stringifyIDs`；Java 集成层 `ToStringSerializer`；PHP 出口字符串化；Rust facade `stringify_ids`）|
| **performType** | 接受数字或字符串 `'1'`/`'ALL'`/`'COUNTERSIGN'` |
| **时间** | `yyyy-MM-dd HH:mm:ss` 字符串 |
| **分页** | `{pageNum, pageSize, recordCount, totalPage, rows}` |
| **批量入参** | 删除/启停类 action 统一 `{ids}` 数组优先、单 `{id}` 兼容——`ids`/`id` 缺失或空数组**一律报错**，禁止静默成功 |
| **响应** | `{code, msg, data}` |
| **撤回** | 实例 + 全部进行中任务同步置 WITHDRAW（级联持久化）|
| **发起抄送** | `f_ccActors`；任务抄送 `tf_ccActors` |
| **动态参与人** | 未配置静态候选时，nodeProgress 不返回该节点（成员未知）|
| **Surrogate 跨栈** | 见 §4.5 6 条运行期语义（内存仓与 SQL 仓必须同答案）|
| **变量出口** | `ext` 唯一对外出口（issues/124），`variable` 原串不在契约字段 |