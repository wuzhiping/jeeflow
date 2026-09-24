# 设计原理 05 · SPI 设计——接口的边界在哪里

> **来源**：https://jeeflow-doc.mldong.com/concepts/05-spi-design
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**SPI 设计原理参考**——理解哪些 SPI 是必选 / 可选、为什么 `ProcessRepository` 是唯一必选、为什么 `UserProvider` / `OrgUserProvider` / `ExpressionEvaluator` 都可选，是把握引擎扩展边界的基础。
>
> **本仓实测**：`vendor/jeeflow/spi.py:6 ABC` 定义（`ProcessRepository` / `UserProvider` / `OrgUserProvider` / `IDGenerator` / `ExpressionEvaluator` / `ProcessExtRepository`）。
>
> **裁剪记录**：§1-§6 保留 + 加本仓实测；§7 6 语言实现表裁掉 5 语言仅留 Python。

---

## §1. 设计原则

引擎的 SPI 划分遵循一个原则：

> **引擎只依赖抽象，不依赖实现；只有"换不掉"的才做必选 SPI，其余全部可选。**

| SPI | 必须/可选 | 理由 |
|---|---|---|
| `ProcessRepository` | **必须** | 引擎读写数据的唯一通道，不可绕过 |
| `UserProvider` | 可选 | 不注入则变量里没有用户信息，引擎照跑 |
| `OrgUserProvider` | 可选（v1.6.0）| 组织维度取人（部门领导 / 分管领导 / 角色），内置组织 handler 的数据源 |
| `IDGenerator` | 可选 | 默认时间戳方案，业务方想用雪花可替换 |
| `ExpressionEvaluator` | 可选 | 不用决策表达式就不需要 |
| `TransactionTemplate` | 可选 | 内存测试不需要事务 |
| `IJsonProvider` | 可选（隐式）| JSON 解析内部有默认实现（Python `json` 标准库）|

> **本仓实测**：本仓 Python 引擎实现 6 个 ABC（`spi.py`）：`ProcessRepository` / `UserProvider` / `OrgUserProvider` / `IDGenerator` / `ExpressionEvaluator` / `ProcessExtRepository`（最后一个属于扩展仓储，详见 `../spec/05-spi.md` §扩展仓储）。

---

## §2. `ProcessRepository`——为什么它是唯一的必须 SPI

### 2.1 接口边界

```python
# vendor/jeeflow/spi.py:16
class ProcessRepository(ABC):
    # 流程定义
    @abstractmethod
    async def find_define_by_id(self, id: int) -> Optional[ProcessDefine]: ...
    @abstractmethod
    async def find_define_by_name(self, name: str) -> Optional[ProcessDefine]: ...   # v1.1.0 Facade deploy
    @abstractmethod
    async def save_define(self, define: ProcessDefine) -> None: ...                  # v1.0.1
    @abstractmethod
    async def update_define(self, define: ProcessDefine) -> None: ...
    @abstractmethod
    async def update_define_state(self, define_id: int, state: int) -> None: ...
    @abstractmethod
    async def remove_define(self, define_id: int) -> None: ...

    # 流程实例
    @abstractmethod
    async def find_instance_by_id(self, id: int) -> Optional[ProcessInstance]: ...
    @abstractmethod
    async def save_instance(self, inst: ProcessInstance) -> None: ...
    @abstractmethod
    async def update_instance(self, inst: ProcessInstance) -> None: ...               # 级联

    # 任务
    @abstractmethod
    async def find_task_by_id(self, task_id: int) -> Optional[ProcessTask]: ...
    @abstractmethod
    async def save_task(self, task: ProcessTask) -> None: ...
    @abstractmethod
    async def update_task(self, task: ProcessTask) -> None: ...
    @abstractmethod
    async def find_doing_tasks(self, instance_id: int, task_names: Optional[list[str]] = None) -> list[ProcessTask]: ...
    @abstractmethod
    async def find_done_tasks(self, instance_id: int, task_names: Optional[list[str]] = None) -> list[ProcessTask]: ...
    @abstractmethod
    async def find_history_tasks(self, instance_id: int) -> list[ProcessTask]: ...

    # 参与者
    @abstractmethod
    async def find_task_actors(self, task_id: int) -> list[str]: ...
    @abstractmethod
    async def add_task_actor(self, task_id: int, actors: list[str]) -> None: ...
    @abstractmethod
    async def remove_task_actor(self, task_id: int, actors: list[str]) -> None: ...

    # 抄送
    @abstractmethod
    async def create_cc_instance(self, instance_id: int, creator: str, *actor_ids: str) -> None: ...
    @abstractmethod
    async def update_cc_status(self, instance_id: int, actor_id: str) -> None: ...
    @abstractmethod
    async def page_cc_instances(self, page_num: int = 1, page_size: int = 10,
                                actor_id: Optional[str] = None) -> tuple[list[CcInstanceRow], int]: ...  # v1.3.0

    # 本仓实测额外
    @abstractmethod
    async def lock_instance_for_update(self, instance_id: int) -> None: ...         # §27 悲观锁
    @abstractmethod
    async def page_defines(self, page_num, page_size, conditions) -> ...             # v1.5.0
    @abstractmethod
    async def page_instances(self, page_num, page_size, operator, conditions) -> ...
    @abstractmethod
    async def page_todo_tasks(self, page_num, page_size, actor_id, conditions) -> ...
    @abstractmethod
    async def page_done_tasks(self, page_num, page_size, operator, conditions) -> ...
    @abstractmethod
    async def query_instances_for_stats(self, state_in, order_by, start, end) -> ...
    @abstractmethod
    async def query_tasks_for_stats(self, task_state, start, end) -> ...
    @abstractmethod
    async def stats_pending_and_overdue_count(self) -> tuple[int, int]: ...
    @abstractmethod
    async def stats_avg_completed_duration_seconds(self, start, end) -> int: ...
    @abstractmethod
    async def stats_completed_task_aggregate(self) -> tuple[int, int, int, int]: ...
    # ... 共 30+ abstractmethod
```

> **v1.0.1 集成反馈**：`save_define / update_define / update_define_state / remove_define` 让集成方不再需要直写 `wf_process_define` 表做定义增删改/启停（设计器 deploy、启停端点直接走仓储）。
>
> **`update_instance(inst)` 级联契约**（v1.0.1）：会**级联持久化聚合根内任务状态变更**（撤回 / 挂起 / 废弃等随同落库，与实例更新同连接保证一致）——聚合根内任务副本需反映最新状态。

### 2.2 设计要点

**a) 面向"聚合"而非"表"**

接口操作的是 `ProcessInstance` 整体和 `ProcessTask` 整体，不是 `update_state()` 这种字段级方法。仓储实现内部映射到 8 张表，引擎不感知表结构——这正是"同一套表可被不同语言共享"的前提。

**b) 读方法返回"完整聚合"**

`find_instance_by_id` 返回实例 + 全部任务 + 参与者（引擎执行推进时不需要再查任务列表）：

```python
# 内存仓储实现（vendor/jeeflow/memory.py）
async def find_instance_by_id(self, id: int) -> Optional[ProcessInstance]:
    inst = self._instances.get(id)
    if not inst: return None
    # 加载 tasks + actors 完整聚合
    inst.tasks = [t for t in self._tasks.values() if t.process_instance_id == id]
    for task in inst.tasks:
        task.actor_ids = [a.actor_id for a in self._actors.get(task.id, [])]
    return inst
```

**c) 没有分页/统计方法在引擎核心**

分页、统计是"查询视图"，属于业务层（demo 的 page / todoList 端点自己遍历内存仓库实现）。**引擎核心只做执行所需的读写**——接口最小化，实现才简单（一个内存 Map 就能实现，测试零成本）。

> 本仓实测：本仓 `ProcessRepository` ABC 含 **30+ 方法**（上游 19 + 本仓 11 个 `page_*` / `stats_*` / `lock_instance_for_update` / `find_define_by_name`），但**引擎核心执行路径只调用**前 19 个 + `lock_instance_for_update`；分页 / 统计是 facade 层（`facade.py:1276+`）需要，由独立查询方法承接。

### 2.3 内存仓储的价值

内置内存仓储（六版都有）不是玩具，它让：

- 引擎单测零配置（不依赖数据库）
- demo 开箱即用
- 仓储接口的"可实现性"始终被验证（内存实现能跑通，接口就没设计过度）

> **本仓实测**（`vendor/jeeflow/memory.py`）：
>
> - 单进程 dict 存储（`_instances` / `_tasks` / `_actors` / `_defines` / `_ccs`）
> - 适用于：单元测试 / demo / 单机部署 / 学习
> - **生产 / 多节点**：必走 `vendor/jeeflow/repository/jdbc.py`（`JdbcRepository` PG 后端）

---

## §3. `UserProvider`——为什么可选

```python
# vendor/jeeflow/spi.py:157
class UserProvider(ABC):
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[UserInfo]: ...
```

引擎在每次操作（启动 / 完成任务）时调用它，把用户信息注入流程变量（`u_userId` / `u_realName` / `u_deptId` 等）。

**可选的代价**：不注入 `UserProvider`，`u_*` 变量缺失，决策表达式若引用了会取不到值。但**引擎核心路径**（创建任务 / 状态转换）完全不依赖用户信息——所以可选是安全的。

> **本仓实测**（`engine.py:_resolve_actors`）：
>
> - `UserInfo` 含 6 字段（`user_id` / `real_name` / `dept_id` / `dept_name` / `post_id` / `post_name`）
> - `u_*` 注入到 `inst.variables`（**仅执行上下文，不写回实例**，FIX-T9 §66）
> - 注入跳过：`flow.auto` / `flow.admin`（系统代执行）

**注**：变量 key 前缀 `u_` 与 mldong 框架完全一致，保证决策表达式在 jeeflow 与 mldong 框架间可移植。

### §3.1 `OrgUserProvider`——组织维度取人（v1.6.0）

```python
# vendor/jeeflow/spi.py:161
class OrgUserProvider(ABC):
    @abstractmethod
    async def find_dept_leaders(self, dept_id: str) -> list[str]: ...
    @abstractmethod
    async def find_dept_main_leaders(self, dept_id: str) -> list[str]: ...
    @abstractmethod
    async def find_by_role(self, role_code: str) -> list[str]: ...
```

「按部门领导 / 分管领导 / 按角色取人」是**通用业务语义**，每个集成方都要写一遍。jeeflow 把这类取人逻辑内置为通用 handler（详见 `../concepts/04-extensions.md` §5.2.1），但**引擎本身不感知组织数据**——数据从哪来？就是本 SPI。

**为什么单独一个 SPI 而不是塞进 `UserProvider`**：`UserProvider.get_user` 是"按 id 取单个用户"，组织维度是"按条件取一批用户"，语义不同、数据源不同（用户中心 vs 组织架构服务）。分开后业务方各自实现，互不干扰。

**可选的代价**：不注入 `OrgUserProvider`，组织维度 handler（部门领导 / 角色）返回空参与者，该节点任务不会创建。纯 `assignee` / 表单字段 / 发起人语义的流程完全不受影响。

> **集成方简化**：从 boot4 的 **8 个 handler** 收敛为本仓的 **1 个数据 SPI**。业务方只实现数据接口，不写 handler。
>
> 详见 `../ToT/guides/07-assignment-handlers.md` §4 行为约定。

---

## §4. `ExpressionEvaluator`——为什么可选

```python
# vendor/jeeflow/spi.py:186
class ExpressionEvaluator(ABC):
    @abstractmethod
    async def eval(self, expr: str, vars: dict[str, Any]) -> Any: ...
```

决策表达式（`amount > 1000`）的求值：**字符串 → 结果**。

**为什么不做内置实现**？表达式语言是典型的"可以有很多答案"的问题：Java 可用 SpEL / MVEL / Aviator；Python 可用 `simpleeval`；Go 有 govaluate。引擎不做选择，业务方选自己熟悉的。

> **本仓实测**：默认 `SimpleExprEvaluator`（`vendor/jeeflow/engine.py` 内置）——支持**比较 + 逻辑运算 + OGNL 风格变量访问**（FIX-T37 §20）：
>
> | 能力 | 语法 | 示例 |
> |---|---|---|
> | 数值比较 | `>` `<` `>=` `<=` `==` `!=` | `amount > 1000` |
> | 逻辑运算 | `&&` `\|\|` `!` | `#amount >= 5000 && #urgent == 1` |
> | 变量访问 | 直接变量名 或 `#var` | `amount` / `#amount` / `#f_amount` |
> | 字符串字面量 | 单 / 双引号 | `u_deptId == 'D01'` |
> | 算术运算 | `+` `-` `*` `/` `%` | `#f_amount * 0.1` |
>
> 不在能力范围：函数调用 / 对象方法 / 数组下标 / 三元表达式。如需复杂条件，需扩展 `ExpressionEvaluator` SPI 自定义。

**可选的代价**：没有求值器时，决策节点只能走 Registry / 扩展处理器，或第一个无 expr 的出边作为默认分支。

---

## §5. 事务边界（`TransactionTemplate`）

```
interface TransactionTemplate:
    execute(action): void    # 在事务中执行 action
```

**引擎内部不带事务**：引擎方法是"编排"，跨多个仓储调用，事务应该由集成层包一层：

```python
# Python 集成层（main_common.py:with_tx）
async with repo.transaction():
    await order_svc.update_status(order_id, "APPROVED")
    await engine.execute_process_task(task_id, op, args)
```

**为什么这样设计**：

- 内存仓储 / 测试不需要事务（裸执行）
- 不同存储（MySQL / PostgreSQL / NoSQL）事务语义不同，引擎不绑死
- JDBC 版 `JdbcRepository` 提供默认 `TransactionTemplate`（PG 后端走 `asyncpg pool` 异步事务）

> **本仓实测**（`main_common.py:with_tx`）：async 上下文管理器 + `ContextVar` 绑定数据库连接（Python 异步上下文绑定机制）。事务 `commit` / `rollback` 自动管理连接释放。
>
> 详见 `../spec/05-spi.md` §事务约定。

---

## §6. 依赖注入：构造器 + 注册表

引擎的 SPI 全部通过**构造器注入**（显式、可测），扩展点通过 **`setExtensions` / `HandlerRegistry`** 注入：

```python
# 构造器注入（必选 + 可选 SPI）
new EngineImpl(
    repo,                     # ProcessRepository（必须）
    user_provider=user_prov,  # 可选
    id_generator=id_gen,      # 可选
    expr_evaluator=expr_eval, # 可选
)

# 扩展点注入（拦截器 / 事件 / 扩展处理器）
engine.set_extensions(EngineExtensions(
    registry=registry,                         # HandlerRegistry（命名处理器）
    interceptor_registry={"persistPost": ic}, # 拦截器注册表
    event_listener=async_on_event,             # 事件监听器（单回调）
    custom_handler_registry={"myHandler": h}, # 自定义节点
))

# 命名处理器（替代 Service Locator）
registry = HandlerRegistry()
registry.register_assignment("deptLeaderHandler", DeptLeaderHandler())
```

不需要服务定位器（ServiceLocator）——全局单例的隐式依赖是测试地狱。

> **本仓实测补充**（`extensions.py:88 EngineExtensions`）：
>
> - 6 个字段（`interceptors` / `interceptor_registry` / `assignment_handler` / `decision_handler` / `event_listener` / `registry` / `custom_handler_registry`）
> - 详细构造位置：`main_common.py:301 apply_extensions`

---

## §7. 六语言实现对照（本仓 Python 仅）

> **裁剪说明**：仅保留 Python 列。

| SPI | 本仓 Python 实现 |
|---|---|
| 仓储（必选）| `vendor/jeeflow/spi.py:16 ProcessRepository(ABC)` + `memory.py` / `repository/jdbc.py` |
| 用户（可选）| `vendor/jeeflow/spi.py:157 UserProvider(ABC)` |
| 组织用户（可选）| `vendor/jeeflow/spi.py:161 OrgUserProvider(ABC)` |
| 表达式（可选）| `vendor/jeeflow/spi.py:186 ExpressionEvaluator(ABC)` + `engine.py:SimpleExprEvaluator`（默认）|
| ID 生成（可选）| `vendor/jeeflow/spi.py:182 IDGenerator(ABC)` |
| 内存仓储 | `vendor/jeeflow/memory.py:MemoryRepository` |
| PG 仓储 | `vendor/jeeflow/repository/jdbc.py:JdbcRepository` |
| 扩展仓储（可选）| `vendor/jeeflow/spi.py:190 ProcessExtRepository(ABC)`（设计 / 历史 / 委托）|

**命名约定**：Python `snake_case`（`find_define_by_id` / `save_instance`），与上游 Java `camelCase`（`findDefineById`）语义一一对应。完整对照表见 `../spec/05-spi.md`。

---

## 跨文档交叉引用

- SPI 接口契约全集（29+ 方法 + 6 ABC）：`../spec/05-spi.md`
- 扩展仓储（设计 / 历史 / 委托）单独契约：`../spec/05-spi.md` §扩展仓储
- 内置 12 handler key 与 `OrgUserProvider` 数据接口的关系：`../concepts/04-extensions.md` §5.2.1
- 事务约定（含 6 语言上下文绑定机制）：`../spec/05-spi.md` §事务约定
- SurrogateInterceptor 运行期 6 条语义（依赖 `ProcessExtRepository`）：`../concepts/04-extensions.md` + `../ToT/guides/05-scenarios.md` 场景五