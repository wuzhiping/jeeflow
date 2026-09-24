# 设计原理 04 · 扩展机制——拦截器、事件与 HandlerRegistry

> **来源**：https://jeeflow-doc.mldong.com/concepts/04-extensions
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**扩展机制原理参考**——理解拦截器 / 事件 / HandlerRegistry 三类扩展点的设计动机与边界，是判断"加新能力"该走哪条路径的基础。
>
> **本仓实测**：`vendor/jeeflow/extensions.py:31 FlowInterceptor(ABC)` + `:8 EventType(Enum)` + `:66 HandlerRegistry` + `builtin.py:162 register_builtin_assignments`（12 个内置 key）。
>
> **裁剪记录**：§1-§6 保留 + 加本仓实测；§7 6 语言表裁掉 5 语言仅留 Python。

---

## §1. 要解决什么问题

引擎核心必须零框架依赖，但业务方总需要"在流程跑起来的时候干点自己的事"：

- 审批通过后**发通知**（企业微信 / 钉钉 / 短信）
- 特定节点完成时**改业务单据状态**
- 参与者不是固定的人，而是**按业务规则算出来的**
- 决策分支不是表达式能表达的，要**写代码判断**

这些问题不解决，引擎就只能 demo 不能上线。解决方式就是三类扩展点：**拦截器、事件、处理器注册表**。

---

## §2. 三类扩展点总览

| 扩展点 | 时机 | 用途 |
|---|---|---|
| **FlowInterceptor** | 节点执行前后 | 横切逻辑（日志 / 统计 / 熔断）|
| **ProcessEventListener** | 流程生命周期 | 异步通知 / 集成（钉钉 / MQ）|
| **HandlerRegistry** | 运行时按名解析 | 动态参与者、动态决策 |

---

## §3. 拦截器（FlowInterceptor）

### 3.1 设计

```python
# vendor/jeeflow/extensions.py:31
class FlowInterceptor(ABC):
    """流程拦截器"""
    @abstractmethod
    async def pre_handle(self, node, instance) -> bool:
        """节点执行前；返回 false 中断该节点"""
        ...
    @abstractmethod
    async def post_handle(self, node, instance) -> None:
        """节点执行后（无论成败）"""
        ...
    @property
    def order(self) -> int:
        return 0
```

### 3.2 为什么 `pre_handle` 返回 `bool`？

拦截器需要能**阻止节点执行**——典型场景：审批节点要求前置条件满足才创建任务（如"该客户已实名认证才进入人工审核"）。`pre_handle` 返回 `false`，引擎跳过该节点的任务创建，流程停在原地。

> **本仓实测**（`vendor/jeeflow/engine.py:_handle_interceptor_pre`）：所有 `pre_handle` 按 `order` 升序执行，**任一返回 false 即中断**该节点后续流程。

### 3.3 执行顺序

```
所有拦截器按 order 升序执行 pre_handle（任一 false 即中断）
节点执行
所有拦截器按 order 降序执行 post_handle（对称的洋葱模型）
```

对称顺序保证"先注册的后收尾"，与中间件惯例一致。

### 3.4 与事件的区别

| 拦截器 | 事件 |
|---|---|
| 能阻止执行（✅ `pre_handle` 返回 false）| ❌ 不能 |
| 关注点：节点级横切 | 关注点：流程级通知 |
| 顺序敏感（✅ `order`）| ❌ 顺序不敏感（广播）|

**经验法则**：要"拦"用拦截器；要"通知"用事件；两者不要混。

---

## §4. 事件监听（ProcessEventListener）

### 4.1 事件清单（本仓实测 6 事件）

> **本仓实测**（`vendor/jeeflow/extensions.py:8 EventType(Enum)`）：

| 事件 | 触发时机 | 关键字段 |
|---|---|---|
| `PROCESS_START` | 启动流程 | `instanceId`, `operator` |
| `PROCESS_FINISH` | 到达 end（finish）| `instanceId`, `operator` |
| `PROCESS_REJECT` | 到达 end（reject）| `instanceId`, `operator` |
| `TASK_CREATE` | 任务落库后（**逐任务**；会签各一次）| `instanceId`, `taskId`, `taskName`, `operator` |
| `TASK_COMPLETE` | 任务完成 | `instanceId`, `taskId`, `taskName`, `operator` |
| `CC_CREATE` | 抄送人创建后（**逐抄送人**）| `instanceId`, `ccActorId` |

> **官方 6 语言映射**：上游列 6 语言事件名差异（Java `PROCESS_INSTANCE_START` / Go `EventProcessStart` / Python `PROCESS_START` 等），但**触发语义统一**——集成层按**语义**对齐。Python 字符串枚举，码值无需跨栈对齐。

### 4.2 监听器怎么写（本仓实测）

```python
# vendor/jeeflow/extensions.py:95
event_listener: Optional[Callable[[ProcessEvent], Awaitable[None]]] = None
```

```python
# 本仓实测监听器写法（单回调形态）
from jeeflow import EngineExtensions, EventType, ProcessEvent

async def on_event(evt: ProcessEvent):
    if evt.type == EventType.TASK_CREATE:
        await dingtalk.send(f"新待办：taskId={evt.taskId}")
    elif evt.type == EventType.PROCESS_FINISH:
        await dingtalk.send(f"流程完成：instanceId={evt.instanceId}")
    # ...

ext = EngineExtensions(event_listener=on_event)
engine.set_extensions(ext)
```

### 4.3 为什么事件不带"业务上下文"？

事件只带 `instanceId / taskId / ccActorId`，业务方需要更多数据时**自己查仓储**。刻意不带完整快照：

- 避免事件体膨胀
- 避免监听器拿到过期数据
- 事件是"通知发生了"，不是"传输数据"

### 4.4 触发时机与"事件 → 消息"职责边界

**引擎只 fire 事件，不保证任何副作用落库。** 事件是引擎对外的唯一通知通道；把「事件 → 业务副作用」（典型：wf 流程站内信 TODO / NOTICE）的**字段组装 + 持久化**是**集成层职责**。

触发时机（6 事件挂载点）：

| 事件 | 引擎保证 |
|---|---|
| `PROCESS_START` | 实例已创建 |
| `TASK_CREATE` | 任务行已写入 `wf_task`（监听器可按 `taskId` 反查）|
| `TASK_COMPLETE` | 任务已完成（聚合根 finish 已落）|
| `PROCESS_FINISH` | 实例已落最终态 FINISHED |
| `PROCESS_REJECT` | 实例已落最终态 REJECT |
| `CC_CREATE` | 抄送实例行已写入 `wf_cc_instance` |

**集成层"事件 → 消息"标准装配**：

| 事件 | 消息类型 | 接收人 |
|---|---|---|
| `TASK_CREATE` | **TODO** 待办 | 任务处理人（`actorIds` 过滤：去空 / 仅纯数字 / 去重）|
| `PROCESS_FINISH` / `PROCESS_REJECT` | **NOTICE** 通知 | 发起人（`createUser`）|
| `CC_CREATE` | **NOTICE** 抄送知会 | 事件直传 `ccActorId`（免反查 cc 表）|
| `PROCESS_START` / `TASK_COMPLETE` | — | 不产生消息 |

**集成层 3 条铁律**：

1. **开关**：提供消息开关（默认开），关闭时监听器直接跳过（性能零损耗）
2. **全局兜底**：消息组装 / 落库的任何异常只记日志，**绝不打断审批主流程**
3. **接收人过滤**：去空、仅纯数字 ID、去重；过滤后为空则不发

> **本仓实测补充**（`vendor/jeeflow/extensions.py:95`）：
>
> - `event_listener` 是**单个** async 回调（Python 引擎特性，区别于 Java / Rust 的监听器数组）
> - publisher 逐监听器调用，**单监听器异常只记日志、不传播**——不得影响引擎主流程
> - 「事件 → 消息」字段组装 + 落库是**集成层职责**——引擎核心不含、不依赖这条链路

---

## §5. HandlerRegistry（自写 IoC）

### 5.1 为什么需要它

流程定义里写的是**字符串**（`assignmentHandler: "deptLeaderHandler"`），运行时引擎需要把这个字符串变成可调用的处理器。这就是注册表：**按名字找到实例**。

```
流程定义 JSON                    Registry
┌──────────────────┐           ┌──────────────────┐
│ assignmentHandler:│  ──名字──▶│ deptLeaderHandler│──▶ 返回 [userId]
│ "deptLeaderHandler"│          │  (已注册实例)      │
└──────────────────┘           └──────────────────┘
```

### 5.2 设计（本仓实测）

```python
# vendor/jeeflow/extensions.py:66 HandlerRegistry
class HandlerRegistry:
    """仿 Spring IoC：按名称注册/解析处理器"""

    def __init__(self):
        self._assignments: dict[str, IAssignmentHandler] = {}
        self._decisions: dict[str, IDecisionHandler] = {}

    def register_assignment(self, name: str, handler: IAssignmentHandler):
        self._assignments[name] = handler

    def register_decision(self, name: str, handler: IDecisionHandler):
        self._decisions[name] = handler

    def resolve_assignment(self, name: str) -> Optional[IAssignmentHandler]:
        return self._assignments.get(name)

    def resolve_decision(self, name: str) -> Optional[IDecisionHandler]:
        return self._decisions.get(name)
```

```python
# IAssignmentHandler 接口（vendor/jeeflow/extensions.py:50）
class IAssignmentHandler(ABC):
    @abstractmethod
    async def assign(self, node, instance, operator: str) -> list[str]:
        """返回参与者列表（operator: 当前任务操作人，issues/16 对齐 Java Execution.getOperator）"""
        ...
```

> **`operator` 参数**（v1.6.0，集成反馈 16）：对齐 Java `Execution.getOperator()`——区分「当前任务操作人」（如"当前人部门领导"）与「流程发起人」（`instance.operator`）。

### 5.2.1 内置通用 handler（v1.6.0，开箱即用）

> **本仓实测**（`vendor/jeeflow/builtin.py:170-183`）：注册 **12 个 key** —— **7 个简化版主用 + 5 个完整版别名**（兼容历史 FQCN）。

| 注册名（流程定义里写的 `assignmentHandler` 值）| 语义 |
|---|---|
| `com.mldong.jeeflow.interceptor.impl.OperatorAssignmentHandler` | 流程发起人（`instance.operator`；兜底 `"apply.operator"`）|
| `com.mldong.jeeflow.interceptor.impl.FormFieldAssigneeHandler` | 按表单字段值分配：节点名精确匹配变量字段；`task_01` 类编号后缀自动去掉再匹配（`task_01` → `task`）|
| `com.mldong.jeeflow.interceptor.impl.DeptLeaderAssignmentHandler` | 当前任务操作人部门领导 |
| `com.mldong.jeeflow.interceptor.impl.DeptMainLeaderAssignmentHandler` | 当前任务操作人部门分管领导 |
| `com.mldong.jeeflow.interceptor.impl.ApplicantDeptLeaderAssignmentHandler` | 流程发起人部门领导 |
| `com.mldong.jeeflow.interceptor.impl.ApplicantDeptMainLeaderAssignmentHandler` | 流程发起人部门分管领导 |
| `com.mldong.jeeflow.interceptor.impl.TaskRoleAssigneeHandler` | 任务节点唯一编码关联角色（roleCode = 节点 id）|

> **完整版别名**（兼容历史 FQCN，本项目同时注册）：
> - `…OrgUserAssignmentHandlers$DeptLeaderAssignmentHandler`
> - `…OrgUserAssignmentHandlers$DeptMainLeaderAssignmentHandler`
> - `…OrgUserAssignmentHandlers$ApplicantDeptLeaderAssignmentHandler`
> - `…OrgUserAssignmentHandlers$ApplicantDeptMainLeaderAssignmentHandler`
> - `…OrgUserAssignmentHandlers$TaskRoleAssigneeHandler`
>
> **新流程建议用简化版主用名**；历史流程用完整版别名仍能跑。

- `OperatorAssignmentHandler` / `FormFieldAssigneeHandler` 是**纯引擎语义**，零外部依赖
- 组织维度 handler（部门领导 / 分管领导 / 角色）通过 `OrgUserProvider` SPI 取数据（详见 `../spec/05-spi.md`）——**业务方只实现数据接口，不写 handler**，消灭各集成方重复实现

**本仓注册方式**：

```python
# main_common.py:build_assignment_handlers()
from jeeflow import register_builtin_assignments, HandlerRegistry

def build_assignment_handlers(user_prov, org_prov):
    registry = HandlerRegistry()
    register_builtin_assignments(
        registry,
        user_prov=user_prov,
        org_prov=org_prov,
    )
    return registry
```

```python
# 应用到 engine（main_common.py:apply_extensions）
from main_common import apply_extensions
registry = build_assignment_handlers(user_prov, org_prov)
apply_extensions(engine, registry=registry)
```

### 5.3 解析优先级（参与者）

```
resolve_actors(node):
  1. assignee 非空            → 固定参与者（含 "applicant" → 发起人）
  2. tf_nextNodeOperator 变量  → 动态指定下一节点处理人（最高优先）
  3. Registry 按名解析         → 动态参与者（推荐）
  4. 都没有                   → 不创建任务
```

> **本仓实测**（`vendor/jeeflow/engine.py:874 _resolve_actors`）：`tf_nextNodeOperator` 优先级高于 Registry；`assignee` 与 `assignmentHandler` 互斥时 `assignee` 优先（静态优先于动态）。
>
> 详见 `../ToT/guides/07-assignment-handlers.md` §1。

### 5.4 决策解析优先级

```
evaluate_decision(node):
  1. Registry 的 decision_handler
  2. 扩展注入的 DecisionHandler
  3. 出边 expr 表达式求值
```

> **本仓实测**（`vendor/jeeflow/engine.py:1381 _eval_decision_expr` + `SimpleExprEvaluator`）：
>
> - 详细决策 3 优先级 + 表达式兜底语义（FIX-T112）：`../concepts/03-execution-engine.md` §4
> - 完整决策节点字段：`../ToT/guides/02-flow-definition.md` §5

### 5.5 为什么不用真正的 Spring？

- 引擎核心零依赖：不能引入 Spring / Guice
- 引擎不需要"对象生命周期管理"——处理器是无状态的，一个 `dict` 就够了
- 集成方若用 Spring，只需在启动时把 Bean 注册进 Registry（适配 3 行代码）

> 集成示例详见 `../ToT/guides/10-mldong-integration.md` §3.1。

---

## §6. 扩展点挂载位置（引擎内部）

```
execute_node(node):
  pre_handle（拦截器）              ←── 拦截器
  ├── create_task → resolve_actors ←── Registry / 扩展
  │     └─ 任务落库后 → fire TASK_CREATE   ←── 事件监听器（逐任务，会签各一次）
  ├── evaluate_decision           ←── Registry / 扩展 / 表达式
  post_handle（拦截器）

启动流程时       → fire PROCESS_START（InstanceStart）
到达 end 节点时  → fire PROCESS_FINISH / PROCESS_REJECT
                   （Java / Rust 统一 fire PROCESS_INSTANCE_END，办结与拒绝都触发）
```

> **挂载方式因语言而异**：
>
> | 语言 | 监听器形态 |
> |---|---|
> | Java / Rust | `ServiceContext` 装配（Java 需集成层显式 `put` / `register`）|
> | Go / Node | `EngineExtensions.listeners` 数组 |
> | **Python（本仓）** | **`EngineExtensions.event_listener` 单回调**（`extensions.py:95`）|
> | PHP（1.3.8 起）| 静态 `ProcessEventListenerRegistry::register`（ServiceProvider `boot()` 显式注册）|

---

## §7. 六语言实现对照（本仓 Python 仅）

> **裁剪说明**：仅保留 Python 列。

| 主题 | 本仓 Python 实现 |
|---|---|
| 拦截器 | `vendor/jeeflow/extensions.py:31 FlowInterceptor(ABC)`（`pre_handle` / `post_handle` / `order` 三方法）|
| 事件枚举 | `vendor/jeeflow/extensions.py:8 EventType(Enum)`（6 事件：`PROCESS_START` / `PROCESS_FINISH` / `PROCESS_REJECT` / `TASK_CREATE` / `TASK_COMPLETE` / `CC_CREATE`）|
| 事件字段 | `extensions.py:18 ProcessEvent`（`type` / `instanceId` / `taskId` / `taskName` / `operator` / `ccActorId`）|
| 事件挂载形态 | `EngineExtensions.event_listener`（**单回调** async callable）|
| Handler Registry | `extensions.py:66 HandlerRegistry`（`register_assignment` / `register_decision` / `resolve_assignment` / `resolve_decision`）|
| 内置 assignment | `builtin.py:162 register_builtin_assignments`（12 个 key：7 简化版主用 + 5 完整版别名）|
| 决策 Registry | `extensions.py:50 IDecisionHandler(ABC)`（`async def decide(node, instance, vars) -> str`）|
| 自定义节点 | `extensions.py` + `EngineExtensions.custom_handler_registry`（`async def handler(node, inst, vars_, args) -> Any`）|

---

## 跨文档交叉引用

- 引擎核心操作的拦截器 / 事件挂载点：`../concepts/03-execution-engine.md` §8
- 拦截器 / 事件 / HandlerRegistry 用法：`../ToT/guides/04-extensions.md`
- 内置 12 handler key 详解：`../ToT/guides/07-assignment-handlers.md` §2
- SPI 接口契约（`ProcessRepository` / `UserProvider` / `OrgUserProvider`）：`../spec/05-spi.md`
- 失败 msg 跨栈字面量统一（10 条文案）：`../spec/06-facade.md`「失败 msg 跨栈统一文案」