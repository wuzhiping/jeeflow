# API Index · vendor/jeeflow 公开 API 速查

> **来源**：`vendor/jeeflow/*.py` 全部 `class` / `def` / `async def`（73 个公开符号）

> **与其他 API 文档的关系**（避免重复维护）：
> - 本表覆盖 **73 个公开 API**（按文件分组的 class/def/async def）
> - **59 个 `/wf/{action}` 端点**（门面层 HTTP 端点）→ 见 [`docs/actions.md`](../../docs/actions.md)
> - **11 个核心 action 详解**（含请求/响应字段表）→ 见 [`docs/api.md`](../../docs/api.md)
> - **AI Agent 调用协议**（config + Tools）→ 见 [`ToT/skills/flow-operator/SKILL.md`](../skills/flow-operator/SKILL.md)
>
> **自动核对**：`ToT/sop/health-check.py --dimension api --json` 输出本表覆盖率与 missing 列表
> **数据**：自动生成于 `ToT/sop/health-check.py --dimension api --json`

---

## 1. 按文件分组

### engine.py（1100+ 行，核心引擎）

| API | 行号 | 类型 | 签名 | 用途 |
|---|---|---|---|---|
| `Engine` | 35 | class | abstract | 引擎接口（5 个方法）|
| `EngineImpl` | 44 | class | extends Engine | 引擎实现（图遍历 + 决策 + 会签 + 驳回）|
| `_find_node` | 1141 | def | `(FlowModel, str) -> Optional[FlowNode]` | 节点查找 |
| `_follow_edges` | 1147 | def | `(FlowModel, str) -> list[FlowNode]` | 出边遍历 |
| `_sync_task_to_aggregate` | 1150 | def | `(ProcessInstance, ProcessTask)` | task → instance 同步 |
| `_is_delegate_allowed` | 999 | def | `(ProcessTask, str) -> bool` | 委派权限校验 |

### model.py（流程数据模型）

| API | 用途 |
|---|---|
| `FlowModel` | 流程模型（节点 + 边）|
| `FlowNode` | 节点 |
| `FlowEdge` | 边（带 expr + text.value）|
| `ProcessInstance` | 流程实例 |
| `ProcessTask` | 任务 |
| `ProcessDefine` | 流程定义 |
| `ProcessSurrogate` | 代理人 |
| `DefineRow` | 流程定义行（PG 持久化）|
| `InstanceRow` | 实例行 |
| `TaskRow` | 任务行 |
| `CcInstanceRow` | 抄送实例行 |
| `DefineState` (Enum) | DRAFT/PUBLISHED/DEPRECATED |
| `InstanceState` (Enum) | RUNNING/SUSPENDED/COMPLETED/TERMINATED |
| `TaskState` (Enum) | TODO/DONE/SKIP |
| `CountersignType` (Enum) | PARALLEL/SEQUENTIAL/VOTE/CUSTOM |
| `PerformType` (Enum) | NORMAL/DELEGATE/AGENT/ADD_SIGN/TRANSFER |
| `StorageType` (Enum) | MEMORY/JDBC |
| `SubmitType` (Enum) | AGREE/REJECT/JUMP/DELEGATE |
| `TaskType` (Enum) | APPROVE/NOTIFY/CC/CUSTOM |
| `EventType` (Enum) | PRE_COMMIT/POST_COMMIT/TASK_CREATED/TASK_COMPLETED/INSTANCE_STARTED/INSTANCE_ENDED |
| `FlowEdge` | 边 |

### spi.py（SPI 抽象）

| API | 用途 |
|---|---|
| `ProcessRepository` (ABC) | 持久化抽象 |
| `ProcessExtRepository` (ABC) | 扩展持久化 |
| `UserProvider` (ABC) | 用户信息提供 |
| `IDGenerator` (ABC) | ID 生成 |
| `ExpressionEvaluator` (ABC) | 表达式求值 |
| `QueryCondition` | 查询条件 |

### extensions.py

| API | 用途 |
|---|---|
| `EngineExtensions` | 引擎扩展点 |
| `FlowInterceptor` (ABC) | 拦截器 |
| `HandlerRegistry` | 处理器注册中心 |
| `EventType` | 事件枚举 |
| `ProcessEvent` | 事件对象 |

### facade.py（API 层，约 2500 行）

**关键 actions**（来自 `docs/actions.md`）：

| # | Action | 函数 | 行号 | 用途 |
|---|---|---|---|---|
| 20 | `processInstance/startAndExecute` | `_processInstance_startAndExecute` | 145 | 启动并执行 |
| 32 | `processTask/todoList` | `_processTask_todoList` | 279 | 待办列表 |
| 45 | `processTask/delegate` | `_processTask_delegate` | 1602 | 任务委派（字段 `targetUserId`）|
| 46 | `processTask/delegateHistory` | `_processTask_delegateHistory` | 1647 | 委派历史 |
| 21 | `processInstance/withdraw` | `_processInstance_withdraw` | 252 | 撤回 |
| 24 | `processInstance/approvalRecord` | `_processInstance_approvalRecord` | 816 | 审批记录 |
| 25 | `processInstance/getAssigneeTextData` | `_processInstance_getAssigneeTextData` | 831 | 审批人文本化 |

### builtin.py（8 个 assignment handler）

| Handler | 用途 |
|---|---|
| `OperatorAssignmentHandler` | 指定操作人 |
| `FormFieldAssigneeHandler` | 表单字段指定 |
| `DeptLeaderAssignmentHandler` | 部门领导 |
| `DeptMainLeaderAssignmentHandler` | 部门主领导 |
| `ApplicantDeptLeaderAssignmentHandler` | 申请人部门领导 |
| `ApplicantDeptMainLeaderAssignmentHandler` | 申请人部门主领导 |
| `TaskRoleAssigneeHandler` | 任务角色 |
| `register_builtin_assignments` | 注册入口 |

### repository.py / memory.py

| API | 用途 |
|---|---|
| `JdbcRepository` | PG 实现 |
| `MemoryRepository` | 内存实现 |
| `MemoryExtRepository` | 内存扩展 |
| `MySqlAdapter` / `PostgresAdapter` | DB 适配 |
| `TsIDGenerator` | Twitter Snowflake |
| `JdbcDynamicTableWriter` / `JdbcTableReader` | 动态表读写 |
| `MetaTableReader` / `MetaTableWriter` | 元表读写 |
| `AsyncJdbcTableReader` / `AsyncMetaTableReader` | 异步版本 |

### verify.py（本仓独有，699 行）

| API | 用途 |
|---|---|
| `VerifyIssue` | 校验问题 |
| `verify_flow(flow, variables)` | 返回 (errors, warnings, infos) |
| `format_issues(issues)` | 格式化输出 |

---

## 2. 关键字段对照表

| 字段名 | 类型 | 出现位置 | 备注 |
|---|---|---|---|
| `id` / `processInstanceId` / `processTaskId` / `processDefineId` | string | 所有 facade API | **PG 雪花 ID 必须用字符串**（JS Number > 2^53 丢精度）|
| `operator` | string | 所有需要「人」的 API | 工号，不是姓名 |
| `targetUserId` | string | `processTask/delegate` | ⚠️ 不是 `assignee`（FB-0009）|
| `submitType` | string | `processTask/execute` | `AGREE` / `REJECT` / `JUMP` / `DELEGATE` |
| `taskType` | string (PG) | instance/task 表 | PG `VARCHAR(64)` |
| `performType` | string (PG) | task 表 | 同上 |

---

## 3. 数据流对照

```
client (curl/前端)
    ↓ POST /wf/<action>
facade.py:_<func>(args)
    ↓
engine.py:EngineImpl.<method>
    ↓
assignment handler (builtin.py)
    ↓
FDEP / SPI 实现
    ↓
repository (JdbcRepository / MemoryRepository)
    ↓
PG / 内存
```

---

## 4. 升级兼容 API

**breaking change 风险**（升级时必须测）：
- 任何 `id` 字段类型变化（int → string 已经发生过）
- `submitType` / `performType` 枚举值变化
- 新增 / 删除 SPI 方法

详见 [`ToT/CC/upgrade-migration.md`](./upgrade-migration.md)（01 plan A2 待建）

---

**版本**：v1.11.1 · **来源**：故事 001（郭开发查 delegate 字段定义）→ 01 persona review