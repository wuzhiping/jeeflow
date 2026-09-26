# 设计原理 01 · 架构总览

> **来源**：https://jeeflow-doc.mldong.com/concepts/01-architecture
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**架构理解参考**——理解 5 层架构、DDD 聚合根分层、一次请求生命周期是把握引擎行为的基础。
>
> **本仓实测**：基于 `vendor/jeeflow/*` + `main_common.py` + `facade.py`。
>
> **裁剪记录**：§1 / §2 / §3 保留 + 加本仓实测定位；§4 / §5 6 语言路径表裁掉 5 语言仅留 Python；§6 差异备忘裁掉 5 语言仅留 Python 2 项。

---

## §1. 为什么这么设计

工作流引擎的本质是：**把"流程定义"变成"一系列待办任务"**。围绕这个本质，jeeflow 的架构做了三个关键决策：

### 决策一：引擎核心零框架依赖

| 不做 | 为什么 |
|---|---|
| 不依赖 ORM | 存储是 SPI，引擎不关心 SQL / 方言 |
| 不依赖 Web 框架 | 引擎是纯逻辑库，HTTP 是 demo 的事 |
| 不依赖 DI 容器 | 用 `HandlerRegistry`（自写 IoC）替代 |
| 不依赖表达式库 | 决策表达式走 SPI，业务方自己选实现 |

> **本仓实测**：`vendor/jeeflow/` 仅依赖 Python 3.10+ 标准库（`abc` / `dataclasses` / `enum` / `typing` 等），无任何第三方依赖；`main_common.py` 是入口装配层（含可选的 DB-API 2.0 / asyncpg 连接）。

### 决策二：领域逻辑收敛到聚合根（DDD）

不采用"贫血模型 + 上帝服务类"（逻辑全堆在 `EngineImpl`），而是：

```
任务状态转换、任务创建、驳回、完成 —— 都是 ProcessInstance / ProcessTask 的行为
引擎只做三件事：解析流程定义、遍历节点、调用聚合根
```

> **本仓实测**（`vendor/jeeflow/model.py:112 ProcessInstance` + `:230 ProcessTask`）：聚合根封装状态转换、参与者追加、任务完成、废弃等业务规则；引擎 `Engine`（接口，`engine.py:35`）/ `EngineImpl`（实现，`engine.py:44`）只做编排（流程遍历、决策求值、参与者解析、仓储调用）。详见 `../spec/03-state-machine.md` + `../spec/04-engine-ops.md` + `../concepts/09-core-types.md §1`。

### 决策三：引擎不做业务决策，只定契约

引擎**不自动执行**第一个任务、**不决定**驳回后怎么办——这些是调用方的约定：

- `startAndExecute`：启动后自动完成申请节点（调用方实现）
- `submitType=2(REJECT)`：跳结束（实例 45）；退回发起人用 `submitType=6`（调用方实现）

> 引擎与调用方的边界详见 `../spec/04-engine-ops.md`。

---

## §2. 分层架构

```
┌─────────────────────────────────────────────────┐
│                  调用方（业务层）                  │
│   demo API / 业务服务 / jeeflow-ui              │
└──────────────────────┬──────────────────────────┘
                       │ 遵守契约（startAndExecute / submitType）
┌──────────────────────▼──────────────────────────┐
│              引擎编排层（EngineImpl）             │
│   · 加载/解析流程定义（LogicFlow JSON → FlowModel）│
│   · 节点遍历（executeNode / followEdges）         │
│   · 决策求值（表达式 / Registry / 扩展）           │
│   · 参与者解析（assignee / assignmentHandler）    │
│   · 事件发布 / 拦截器调度                          │
├─────────────────────────────────────────────────┤
│              领域层（DDD 聚合根）                  │
│   ProcessInstance：completeTask / finish / reject│
│   ProcessTask：finish / abandon / isAllowed      │
├─────────────────────────────────────────────────┤
│               SPI 接口层                         │
│   ProcessRepository（必须）                      │
│   UserProvider / IDGenerator / ExprEvaluator    │
└──────────────────────┬──────────────────────────┘
                       │ 依赖注入（构造器 / 注册表）
┌──────────────────────▼──────────────────────────┐
│              仓储实现（适配层）                    │
│   内存仓储（测试） / JDBC / MyBatis / SQLAlchemy  │
└─────────────────────────────────────────────────┘
```

**依赖方向**（自上而下单向）：

```
调用方 → 引擎编排层 → 领域层 → SPI → 仓储实现
```

> **本仓实测**：
> - 领域层**不依赖**引擎层（聚合根不知道 `EngineImpl` 的存在）
> - 引擎层依赖领域层和 SPI
> - 仓储实现依赖 SPI
> - 入口装配层（`main_common.py`）是**唯一**允许同时引用引擎 + SPI + 仓储的层——这也是为什么 `main_common.py` 是「门面装配」而非业务逻辑。

---

## §3. 一次请求的生命周期

以"启动流程"为例，时序：

```
调用方              EngineImpl           ProcessInstance      Repository
  │  startAndExecute    │                       │                    │
  │────────────────────▶│                       │                    │
  │                     │ find_define_by_id ───▶│                    │
  │                     │ JSON → FlowModel       │                    │
  │                     │ create（工厂）────────▶│                    │
  │                     │ save_instance ────────▶│                    │
  │                     │ 事件：PROCESS_START    │                    │
  │                     │ execute_node(start)    │                    │
  │                     │   └─ follow_edges      │                    │
  │                     │   └─ create_task ─────▶│                    │
  │                     │   └─ save_task ────────▶│                    │
  │                     │   事件：TASK_CREATE     │                    │
  │                     │ 完成申请节点（契约）    │                    │
  │                     │   └─ complete_task ───▶│                    │
  │                     │   └─ update_task ──────▶│                    │
  │                     │ execute_node(审批节点) │                    │
  │◀────────────────────│ 返回 ProcessInstance   │                    │
```

> **本仓实测时序点**（`vendor/jeeflow/facade.py:155 _startAndExecute` + `facade.py:84 _flow_with_trace`）：
>
> 1. `facade._startAndExecute(args)` 接收 `processDefineId` / `operator` / `f_*` args
> 2. `engine.find_define_by_id(define_id)` 异步加载 `ProcessDefine`
> 3. `json.loads(define.content)` 解 JSON → `parse_flow_model` 还原 `FlowModel`
> 4. `ProcessInstance.create(operator=operator)` 工厂创建（`state=10`）
> 5. `await repo.save_instance(inst)` 持久化
> 6. `await _fire_event(ProcessEvent(type=PROCESS_START, ...))`
> 7. `execute_node(start)` → `follow_edges` → 找到 `apply` 节点
> 8. `_resolve_actors(node)` 解析 assignee / assignmentHandler
> 9. `ProcessTask.create(...)` 工厂创建任务
> 10. `await repo.save_task(task)` + `repo.add_task_actor(task.id, actors)` 持久化
> 11. `await _fire_event(ProcessEvent(type=TASK_CREATE, ...))`
> 12. startAndExecute 契约：自动完成 apply 节点（`submitType=0`），推进到下一审批节点
>
> 事件挂载点（`TASK_CREATE` 在任务落库后逐任务 fire；办结/拒绝 fire `INSTANCE_END`）及 "事件 → 消息" 职责边界，见 `../concepts/04-extensions.md`（后续整理）+ `../ToT/guides/04-extensions.md` §5。

---

## §4. 六语言模块对照（本仓 Python 仅）

> **裁剪说明**：上游列出 6 语言路径表，本项目仅 Python 实现，仅保留 Python 列。

| 层 | 本仓 Python 路径 |
|---|---|
| 引擎编排 | `vendor/jeeflow/engine.py` |
| 领域层 | `vendor/jeeflow/model.py` |
| SPI | `vendor/jeeflow/spi.py` |
| 扩展 | `vendor/jeeflow/extensions.py` + `vendor/jeeflow/builtin.py` + `vendor/jeeflow/metadata.py` |
| Registry | `vendor/jeeflow/extensions.py`（`HandlerRegistry`）+ `metadata.py:102` |
| 内存仓储 | `vendor/jeeflow/memory.py` |
| PG 仓储 | `vendor/jeeflow/repository/jdbc.py`（含 `JdbcRepository` / `JdbcProcessExtRepository`） |
| 持久化（persist）| `vendor/jeeflow/persist.py`（`DynamicTableWriter` / `JdbcDynamicTableWriter` / `PersistPostInterceptor`） |
| 元数据（persist-meta）| `vendor/jeeflow/meta.py`（`StorageType` / `FieldMeta` / `TableMeta` / `MetaTableWriter` / `MetaTableReader`） |
| Facade 门面 | `vendor/jeeflow/facade.py`（57 个 /wf/ 端点） |
| 入口装配 | `main_common.py`（`apply_extensions` / `build_*_handlers`） |
| 启动入口 | `main.py`（内存后端，:8101）/ `main_pg.py`（PG 后端，:8101） |

> **本仓无前端**：本项目不输出 UI（PRD §3「不做什么」）；前端统一由上游 [jeeflow-ui](https://github.com/mldong/jeeflow-ui) 提供（Vue3 + mldong-flow-designer-plus），对接任一后端。

---

## §5. 关键源码位置（本仓 Python 仅）

> **裁剪说明**：仅保留 Python 路径。

| 主题 | 本仓 Python 路径 |
|---|---|
| 引擎入口 | `vendor/jeeflow/engine.py:44 EngineImpl` |
| 聚合根 | `vendor/jeeflow/model.py:112 ProcessInstance` + `:230 ProcessTask` |
| 仓储 SPI | `vendor/jeeflow/spi.py:16 ProcessRepository(ABC)` |
| 内存仓储 | `vendor/jeeflow/memory.py:MemoryRepository` |
| PG 仓储 | `vendor/jeeflow/repository/jdbc.py` |
| 流程定义解析 | `vendor/jeeflow/model.py:_parse_flow_model`（`8` 行起）|
| 拦截器注册表 | `vendor/jeeflow/extensions.py:66 HandlerRegistry` |
| 内置 assignment handler | `vendor/jeeflow/builtin.py:162 register_builtin_assignments` |
| 持久化拦截器 | `vendor/jeeflow/persist.py:307 PersistPostInterceptor` |
| 元数据驱动 | `vendor/jeeflow/meta.py:141 MetaTableWriter` + `:293 MetaTableReader` |
| Facade 入口 | `vendor/jeeflow/facade.py:63 JeeflowFacade.flow` |
| 测试样本 | `flows/01-17`（**19 个 sample**，含 2 个同号 08/11）+ `bdd/`（1131 个 BDD）+ `tdd/`（19 个 TDD baseline）|

---

## §6. 与其他语言差异备忘（本仓 Python 仅）

> **裁剪说明**：上游列 6 语言差异（Go 命名 / Python 命名 / Node/Python 异步 / Node 领域层 / Python 领域层 / Rust 异步），本项目仅 Python 相关。

| 差异点 | 本仓 Python 实测 |
|---|---|
| **命名** | 全部 `snake_case`（`find_define_by_id` / `save_instance` / `add_task_actor`）—— 与上游 Java camelCase / Go PascalCase / Rust snake_case 保持对齐（`vendor/jeeflow/spi.py`） |
| **异步** | 引擎方法返回 `awaitable`（`async def find_define_by_id(...)`），上层 `async/await` 链（`facade.py` / `engine.py` / `spi.py`） |
| **领域层实现** | `@dataclass + 方法` —— 行为与 Java class 等价，字段声明更简洁（`model.py:112` / `:230`）|
| **Facade 出口 id 字符串化** | `_stringify_ids` 递归处理 dict / list / dataclass；dataclass 分支（issues/76 FIX）收口"嵌套 dataclass 列表整表外泄 int id"（`facade.py:2444`）|
| **id 雪花精度** | PG 后端 19 位雪花 ID 走 `_stringify_ids` 出口转字符串；JS 端按字符串处理（避免 `>2^53` 精度丢失）|

---

> **设计者实操**：本节是引擎架构的"鸟瞰图"。若设计者需深挖某个组件的实现位置，按 §4 / §5 表查 `vendor/jeeflow/<file>.py:<line>` 即可。
>
> 后续 concepts 系列（02-08）将按相同模式逐 link 整理；当前文件位于 `ToT/docs/concepts/01-architecture.md`。