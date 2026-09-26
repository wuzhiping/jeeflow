# 设计原理 09 · 核心类型——Engine 接口 / Row 数据 / Enum 状态

> **来源**：本仓 + `vendor/jeeflow/*.py` 内省（无对应上游 doc，因是内部类型）
> **定位**：补齐 API 覆盖——`Engine` / `CountersignType` / `DefineRow` / `InstanceRow` / `TaskRow` 等 14 个公开类型在 ToT/docs 此前未独立记录。
>
> **本仓实测**：`vendor/jeeflow/engine.py:35-43` + `model.py` + `spi.py`。
>
> **裁剪记录**：上游无对应 doc（属于本仓设计沉淀）。结构 §1 Engine 接口 / §2 数据 Row / §3 状态 Enum。

---

## §1. Engine 抽象接口

`vendor/jeeflow/engine.py:35-43`

```python
class Engine:
    """引擎接口——所有引擎必须实现的契约"""

    async def start_process_instance_by_id(self, define_id, operator, args=None) -> ProcessInstance
    async def execute_process_task(self, task_id, operator, args=None) -> ProcessInstance
    async def execute_and_jump_to_end(self, task_id, operator, args=None) -> ProcessInstance
    async def execute_and_jump_task(self, task_id, operator, args=None, target_task_name=None) -> ProcessInstance
    async def execute_and_jump_to_first_task_node(self, task_id, operator, args=None) -> ProcessInstance
```

**5 个核心方法**：
| 方法 | 用途 |
|---|---|
| `start_process_instance_by_id` | 启动流程实例 |
| `execute_process_task` | 执行当前任务（审批/驳回）|
| `execute_and_jump_to_end` | 跳转到结束 |
| `execute_and_jump_task` | 跳转到指定任务 |
| `execute_and_jump_to_first_task_node` | 跳回第一个任务节点 |

**实现**：`EngineImpl`（`engine.py:44`）—— 1100+ 行实现引擎逻辑，包括图遍历、决策、会签、驳回、抄送。

**测试替身**：`MemoryEngineImpl`（如存在）—— 内存版，用于单元测试。

---

## §2. 数据 Row 类型（持久化层）

| 类 | 文件 | 用途 |
|---|---|---|
| `DefineRow` | `repository.py` | 流程定义行 |
| `DefineState` | `repository.py` | 定义状态枚举 |
| `InstanceRow` | `repository.py` | 流程实例行 |
| `InstanceState` | `repository.py` | 实例状态枚举 |
| `TaskRow` | `repository.py` | 任务行 |
| `TaskState` | `repository.py` | 任务状态枚举 |
| `InstanceStatsRow` | `repository.py` | 实例统计行（admin 用）|
| `TaskStatsRow` | `repository.py` | 任务统计行（admin 用）|
| `CcInstanceRow` | `repository.py` | 抄送实例行 |
| `ProcessTask` | `model.py` | 任务领域对象 |
| `ProcessInstance` | `model.py` | 实例领域对象 |
| `ProcessDefine` | `model.py` | 定义领域对象 |
| `ProcessSurrogate` | `model.py` | 代理人 |

**设计模式**：每张 PG 表对应一个 `XxxRow` 类（dataclass-like），领域对象 `Xxx`（如 `ProcessDefine`）承载业务方法。

**状态机映射**：
```
DefineRow.defState  ←→ DefineState (DRAFT/PUBLISHED/DEPRECATED)
InstanceRow.state   ←→ InstanceState (RUNNING/SUSPENDED/COMPLETED/TERMINATED)
TaskRow.state       ←→ TaskState (TODO/DONE/SKIP)
```

---

## §3. 状态 / 类型 Enum

| Enum | 取值 | 用途 |
|---|---|---|
| `CountersignType` | `PARALLEL` / `SEQUENTIAL` / `VOTE` / `CUSTOM` | 会签四模式 |
| `DefineState` | `DRAFT` / `PUBLISHED` / `DEPRECATED` | 流程定义状态 |
| `InstanceState` | `RUNNING` / `SUSPENDED` / `COMPLETED` / `TERMINATED` | 流程实例状态 |
| `TaskState` | `TODO` / `DONE` / `SKIP` | 任务状态 |
| `PerformType` | `NORMAL` / `DELEGATE` / `AGENT` / `ADD_SIGN` / `TRANSFER` | 任务执行类型 |
| `StorageType` | `MEMORY` / `JDBC` | 仓库存储类型 |
| `SubmitType` | `AGREE` / `REJECT` / `JUMP` / `DELEGATE` | 提交类型 |
| `TaskType` | `APPROVE` / `NOTIFY` / `CC` / `CUSTOM` | 任务类型 |
| `EventType` | `PRE_COMMIT` / `POST_COMMIT` / `TASK_CREATED` / `TASK_COMPLETED` / `INSTANCE_STARTED` / `INSTANCE_ENDED` | 引擎 6 事件 |

**会签四模式**（§1 `concepts/03-execution-engine.md`）：
- `PARALLEL` — 所有人同时收到，全完成才推进
- `SEQUENTIAL` — 按顺序签，前一个完成下一个才收到
- `VOTE` — 投票制，过半同意
- `CUSTOM` — 自定义策略

**执行类型**（`PerformType`）：审批任务可能的执行方式——普通/委托/代理/加签/转办。

---

## §4. SPI 接口

`vendor/jeeflow/spi.py`：

| SPI | 用途 |
|---|---|
| `ProcessRepository` | 流程持久化抽象 |
| `ProcessExtRepository` | 扩展持久化（设计历史/草稿）|
| `UserProvider` | 用户信息提供 |
| `IDGenerator` | ID 生成策略 |
| `ExpressionEvaluator` | 表达式求值（决策/抄送等）|
| `QueryCondition` | 查询条件封装（spi.py:9）|

**实现**：
- `JdbcRepository`（PG）+ `MemoryRepository`（内存）实现 `ProcessRepository`
- `MemoryExtRepository`（`memory.py:564/672`）实现 `ProcessExtRepository`
- `OrgUserProvider`（mldong 集成）实现 `UserProvider`
- `TsIDGenerator`（Twitter Snowflake）实现 `IDGenerator`

---

## §5. Flow 数据结构

`vendor/jeeflow/model.py:26`：

| 类 | 用途 |
|---|---|
| `FlowModel` | 流程模型（节点 + 边集合）|
| `FlowNode` | 节点（start/task/decision/fork/join/end/custom/callActivity）|
| `FlowEdge` | 边（source → target，决策边带 expr + text.value）|

**关系**：
```
FlowModel
 ├── nodes: list[FlowNode]
 └── edges: list[FlowEdge]   # 通过 sourceNodeId/targetNodeId 与 nodes 关联
```

**引擎遍历**（§3 `concepts/03-execution-engine.md`）：任务完成后，引擎通过 `task.taskName` 在 FlowModel.nodes 里反查节点，再 `follow_edges` 找到下一个节点。

---

## §6. 校验工具

`vendor/jeeflow/verify.py`（本仓独有扩展——非上游提供）：

| API | 用途 |
|---|---|
| `VerifyIssue` | 校验问题（severity + path + message + fix）|
| `verify_flow(flow, variables)` | 校验流程定义合法性，返回 (errors, warnings, infos) |
| `format_issues(issues)` | 格式化问题列表为可读字符串 |

**用途**：发布流程定义前静态检查，避免运行时崩溃（参见 `manual/07-verify-and-troubleshoot.md`）。

---

## §7. 与其他概念 doc 的关系

- 引擎执行原理 → `concepts/03-execution-engine.md`（图遍历、决策、会签）
- 引擎扩展点 → `concepts/04-extensions.md`（拦截器/事件）
- 持久化 PG schema → `spec/01-data-model.md`（9 张表）
- 状态机 → `spec/03-state-machine.md`
- 引擎操作 API → `spec/04-engine-ops.md`

---

## §8. 后续

- [ ] 补全 `Engine` 抽象类的 Python Protocol typing
- [ ] 提取 `Row` 类的 dataclass 字段为 typed dict
- [x] 验证 `MemoryExtRepository` 真实存在（`memory.py:564/672`）— ✅