# 规范 05 · SPI 接口

> **来源**：https://jeeflow-doc.mldong.com/spec/05-spi
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**SPI 接口契约参考**——理解哪些接口由引擎调用、哪些必须由业务方实现、哪些可选。
>
> **本仓实现版本**：`vendor/jeeflow/spi.py` 定义 6 个 ABC（`ProcessRepository` / `UserProvider` / `OrgUserProvider` / `IDGenerator` / `ExpressionEvaluator` / `ProcessExtRepository`）。
>
> **裁剪记录**：IProcessRepository / IUserProvider / IOrgUserProvider / 可选 SPI 4 接口 / 事务约定 / IProcessExtRepository / SurrogateInterceptor 全部保留 + 加本仓实测注解；各语言实现位置表 + 跨语言对照表裁掉仅留本仓 Python 路径；多数据库参考实现裁掉。

---

## IProcessRepository（必选）

> **本仓实现**：`vendor/jeeflow/spi.py:16 ProcessRepository(ABC)`。本仓含 **30+ 方法**——上游 19 + 本仓额外 10+（统计 / 分页）。
>
> **必须由业务方实现**：PG 后端走 `JdbcRepository`（`vendor/jeeflow/repository/jdbc.py`）；内存后端走 `MemoryRepository`（`vendor/jeeflow/memory.py`）；自定义业务库需实现 ABC 全方法。

| 类别 | 上游方法 | 本仓实测 |
|---|---|---|
| **流程定义 CRUD** | `findDefineById` / `saveDefine` / `updateDefine` / `updateDefineState` / `removeDefine` | ✅ 全实现；本仓额外含 `find_define_by_name`（v1.1.0 Facade deploy 版本管理）|
| **实例 CRUD** | `findInstanceById` / `saveInstance` / `updateInstance` | ✅ |
| **任务 CRUD** | `findTaskById` / `saveTask` / `updateTask` | ✅ |
| **任务查询** | `findDoingTasks` / `findDoneTasks` / `findHistoryTasks` / `findTaskActors` | ✅ |
| **参与者** | `addTaskActor` / `removeTaskActor` | ⚠️ `addTaskActor` 语义 = **追加**（v1.3.0 修复；JDBC 参考实现 v1.2.0 曾为覆盖）|
| **抄送** | `createCcInstance` / `updateCcStatus` / `pageCcInstances` | ✅ |
| **本仓实测补充** | — | `lock_instance_for_update`（悲观锁，§27 修复，PG 走 `SELECT ... FOR UPDATE`）；10 个 `stats_*` 统计查询；5 个 `page_*` 核心表分页 |

> **`addTaskActor` 语义警示**（v1.3.0 修复）：**追加**——查已有参与者、去重后仅插入新增，不清空原参与者。加签 / 委托后原处理人保留可办。**转办**（摘原人）走门面 `processTask/transfer`，内部即 `removeTaskActor(from_actor)` + `addTaskActor(to_actor)`。**集成方不要在薄壳里自拼摘人 SQL 绕过引擎**。
>
> **悲观锁**（`lock_instance_for_update`，spi.py:55）：§27 修复（2026-09-19）——防止多入边 task 节点在并发场景下重复创建 task（PG/MySQL 后端 `SELECT ... FOR UPDATE`；内存后端单进程无需锁；SQLite 单线程不严格）。**必须在 `with_tx` 事务内调用才有效**。
>
> **`update_instance` 级联**（v1.0.1）：`update_instance(inst)` 级联持久化聚合根内任务状态变更——撤回 / 挂起 / 废弃等聚合命令改完任务状态后，**随 `update_instance` 同一连接落库**。前提：聚合根内任务副本反映最新状态（引擎在完成任务后会同步聚合内任务副本）。

---

## IUserProvider（必选）

> **本仓实现**：`vendor/jeeflow/spi.py:157 UserProvider(ABC)`，1 个方法 + UserInfo 6 字段。

```python
class UserInfo:
    user_id: str
    real_name: str
    dept_id: str
    dept_name: str
    post_id: str
    post_name: str

class UserProvider(ABC):
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[UserInfo]: ...
```

> **设计者视角**：流程执行时引擎调用 `get_user(operator)` 注入 `u_userId` / `u_realName` / `u_deptId` / `u_deptName` / `u_postId` / `u_postName` 6 个变量到流程上下文（**仅执行上下文，不写回实例**）。本仓 `main_common.py` 内置示例 `UserProvider`，业务方接入时实现真实数据源（数据库 / LDAP / 远程服务）。

---

## IOrgUserProvider（必选）

> **本仓实现**：`vendor/jeeflow/spi.py:161 OrgUserProvider(ABC)`，3 方法与上游完全对齐。

```python
class OrgUserProvider(ABC):
    @abstractmethod
    async def find_dept_leaders(self, dept_id: str) -> list[str]:
        """部门领导（deptId → 领导 userId 列表）"""
    @abstractmethod
    async def find_dept_main_leaders(self, dept_id: str) -> list[str]:
        """部门分管领导"""
    @abstractmethod
    async def find_by_role(self, role_code: str) -> list[str]:
        """按角色取人"""
```

**4 条行为约定**（上游）：

1. 返回 `null` / 空列表 = 该组织维度无匹配用户 → 内置 handler 返回空参与者 → **任务不创建**
2. **消费方双场景复用**：内置组织 AssignmentHandler（任务参与者） + `candidateGroups` 候选解析（`candidatePage` 可选名单）
3. 组织数据**只通过本接口获取**——禁止在 handler 里直连组织服务（隔离可测试性）
4. **未注入本 SPI 时组织维度 handler 失效**，`assignee` / 表单字段 / 发起人语义不受影响

> **设计者实操**：内置 handler 的 7 个 FQCN 已在 `../ToT/guides/07-assignment-handlers.md` 详述；数据源由本 SPI 注入，业务方只实现数据接口，不写 handler。

---

## 可选 SPI

> **本仓实现**：`vendor/jeeflow/spi.py:182` IDGenerator + `:186` ExpressionEvaluator。

| 接口 | 方法 | 说明 | 本仓默认 |
|---|---|---|---|
| `IDGenerator` | `next_id() -> int` | ID 生成 | 雪花 / 数据库自增（按后端）|
| `ExpressionEvaluator` | `eval(expr, vars) -> Any` | 决策表达式求值 | `engine.py` 内联决策分支（默认；`SimpleExprEvaluator` 类不存在，详见 `ToT/docs/diffs.md` §3-6；FIX-T37 支持比较 + 逻辑 + OGNL）|
| `IJsonProvider` | `to_json(obj)` / `from_json(str)` | JSON 序列化 | `json` 标准库（隐式）|
| `ITransactionTemplate` | `execute(action)` | 事务管理 | `main_common.py:with_tx` ContextVar（详见下）|

---

## 事务约定（设计者视角）

> **本仓实现**：`main_common.py:with_tx` async 上下文管理器；`ContextVar` 绑定数据库连接（Python 异步上下文绑定机制）。

**4 条核心原则**：

1. **引擎核心不感知事务**——引擎方法只调仓储接口，不知道事务存在
2. **事务由业务层持有**——业务代码是事务的唯一 owner：开启 → 业务操作 + 引擎调用 → commit / rollback
3. **事务是连接级的**——同事务内所有仓储方法必须使用同一数据库连接
4. **接口契约不变**——仓储接口签名不携带事务参数，事务通过上下文绑定机制传递

**业务层形态**：

```python
async with repo.transaction():
    await order_svc.update_status(order_id, "APPROVED")
    await engine.execute_process_task(task_id, op, args)
```

**约束**：

- 跨数据库 / 分布式事务（2PC/Saga）不在本规范范围——工作流引擎按单库事务设计，跨服务一致性由业务层自管
- 引擎方法**不应**在内部自行开启事务（事务边界由业务层控制，引擎只负责语义）
- 内存仓储 `transaction()` 是 no-op（内存操作天然原子），切换真实仓储时业务代码零改动

---

## IProcessExtRepository（可选）

> **本仓实现**：`vendor/jeeflow/spi.py:190 ProcessExtRepository(ABC)`，12 方法覆盖 3 张表（design / design_his / surrogate）。
>
> **引擎核心不依赖**——设计稿 / 历史 / 委托是"周边管理能力"，通过扩展仓储 SPI 提供统一读写，集成方可选接入。

**方法分类**：

| 类别 | 方法 |
|---|---|
| **流程设计（wf_process_design）** | `find_design_by_id` / `save_design` / `update_design` / `remove_design` / `page_designs` |
| **设计历史（wf_process_design_his）** | `save_design_his` / `list_design_his` |
| **委托代理（wf_process_surrogate）** | `find_surrogate_by_id` / `save_surrogate` / `update_surrogate` / `remove_surrogate` / `page_surrogates` / `get_surrogate(operator, process_name, time)` |

**`get_surrogate` 生效规则**：

- `enabled = 1` 且 `start_time <= time <= end_time`（时间窗为空表示不限）
- 优先匹配 `process_name` 精确命中；`process_name` 为空（全流程委托）作为兜底
- **且 `surrogate <> operator`**（自己委托给自己不生效）
- **`enabled` 取值**：只有整数 `1` 生效；不可解析为整数的脏值**不得当作启用**（曾出现 PHP `(int)'abc'→0` 与 C# `ToInt 回落 1` 的相反默认方向）
- **内存仓与 SQL 仓两条路径都要满足上述全部判据**

---

## SurrogateInterceptor（委托生效，内置实现）

> **v1.9.0 起为引擎内置、默认开启**（issues/116）。本仓实测一致。

任务创建后（`PROCESS_TASK_START` 前），遍历任务参与者：

1. 对每个 actor 调用 `get_surrogate(actor, process_name, now)`（`process_name` = 流程模型 `name`，未带时回落 `wf_process_define.name`）
2. 命中委托 → 把代理人并入**该任务的参与者集合**（随任务一起落库），原授权人保留（**任一可办**）

> ⚠️ **不走"事后 `add_task_actor` 补写"路**——taskId 未分配时补写静默无效。
>
> **未配置 `IProcessExtRepository` 时必须静默跳过**，不得抛错打断建单流程。
>
> **委托在 todoList 的合并展示**属于集成方视图层职责（参考 boot3 `ProcessTaskServiceImpl.todoList`）。

---

## 本仓 Python 实现位置

| SPI | 本仓位置 |
|---|---|
| `ProcessRepository` (ABC) | `vendor/jeeflow/spi.py:16` |
| `UserProvider` (ABC) | `vendor/jeeflow/spi.py:157` |
| `OrgUserProvider` (ABC) | `vendor/jeeflow/spi.py:161` |
| `IDGenerator` (ABC) | `vendor/jeeflow/spi.py:182` |
| `ExpressionEvaluator` (ABC) | `vendor/jeeflow/spi.py:186` |
| `ProcessExtRepository` (ABC) | `vendor/jeeflow/spi.py:190` |
| `MemoryRepository` (内存后端实现) | `vendor/jeeflow/memory.py` |
| `JdbcRepository` (PG 后端实现) | `vendor/jeeflow/repository/jdbc.py` |
| 注册入口（`apply_extensions`）| `main_common.py:301` |
| 事务绑定（`with_tx` ContextVar）| `main_common.py:with_tx` |
| 元数据注册（`register_persist_meta`）| `vendor/jeeflow/persist.py:486` |

> **设计者不直接接触 SPI**——SPI 是**框架集成者 / 业务后端实现**的接口契约。设计者只需知道：
> 1. 流程定义 JSON 中的 `assignmentHandler` 字符串 key 必须先在 `main_common.py:build_*_handlers` 注册对应实例
> 2. 委托 / 抄送 / 设计能力依赖业务方实现 `ProcessExtRepository`
> 3. 多数据库适配（mysql / postgres / sqlite / h2）走 `JdbcRepository` + DB-API 2.0 连接；方言占位符自动探测