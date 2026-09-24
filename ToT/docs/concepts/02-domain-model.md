# 设计原理 02 · 领域模型——为什么把逻辑收敛到聚合根

> **来源**：https://jeeflow-doc.mldong.com/concepts/02-domain-model
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**DDD 聚合根设计原理参考**——理解为什么状态转换逻辑必须收敛到聚合根而不是散落在引擎/服务层。
>
> **本仓实测**：`vendor/jeeflow/model.py:177 ProcessInstance` + `:227 ProcessTask`（`@dataclass + 方法` 充血模型）。
>
> **裁剪记录**：§1 / §2 / §3 / §4 保留 + 加本仓 DDD 实测位置 + 伪代码；§5 6 语言对照裁掉 5 语言仅留 Python；§6 聚合根方法清单保留并加本仓实测。

---

## §1. 问题的起点：贫血模型 vs 充血模型

先看一个常见的工作流引擎实现（贫血模型）：

```java
// ❌ 贫血模型：ProcessInstance 只是数据袋子
public class ProcessInstance {
    private Integer state;
    private List<ProcessTask> tasks;
    // 只有 getter/setter
}

// ❌ 上帝服务类：所有业务规则都堆在这里
@Service
public class ProcessTaskServiceImpl {
    public void finishProcessTask(Long taskId, String operator, Dict args) {
        ProcessTask task = baseMapper.selectById(taskId);
        task.setTaskState(FINISHED);     // 状态
        task.setOperator(operator);
        task.setFinishTime(new Date());
        baseMapper.updateById(task);
        // ... 状态转换规则散落在服务方法里
    }
}
```

**问题**：

1. 业务规则（"任务完成要记录操作人"、"驳回要废弃其他任务"）散落在服务层，换个服务类就换一套规则
2. 领域对象对自身状态没有任何约束——谁都能 `setState(DONE)`，规则无法内聚
3. 代码膨胀：服务类越来越大，越来越难测

> **本仓实测位置**：本仓 `vendor/jeeflow/model.py:177 ProcessInstance` + `:227 ProcessTask` 走**充血模型**——状态转换逻辑（finish / abandon / reject 等）作为 `@dataclass` 方法内聚。`engine.py` 只做编排，**不**写 `task.taskState = 20`。

---

## §2. 设计：聚合根封装规则

jeeflow 的领域模型分三层：

```
ProcessInstance（聚合根）
 ├── 自身状态：state / variables / operator
 ├── 子实体集合：tasks
 └── 行为：
      ├── completeTask(task, operator, vars)   ← 完成任务（驱动子实体）
      ├── abandonAllDoing(now)                  ← 废弃所有进行中（驳回/跳转用）
      ├── finish() / reject()                   ← 实例状态转换
      ├── createTask(...)                       ← 子实体工厂
      └── isAllTasksFinished()                  ← join 合并判断

ProcessTask（子实体）
 ├── 自身状态：taskState / actorIds / finishTime
 └── 行为：
      ├── finish(operator, vars, now)           ← 10→20，记录操作人/时间
      ├── abandon(now)                          ← 10→99
      ├── isAllowed(operator)                   ← 参与者权限
      └── isDoing() / isFinished()              ← 状态判断
```

### 为什么 ProcessInstance 是聚合根？

1. **事务边界**：一个流程实例的所有任务变更应在同一事务内（一致性强约束）
2. **不变量**：`isAllTasksFinished()` 决定 join 是否放行、实例是否完成——这些规则只能由聚合根统一判断
3. **状态机归属**：实例的 `10→20→45` 转换、任务的 `10→20/99` 转换，只允许通过聚合根方法发生

> **本仓实测**（`vendor/jeeflow/model.py:177-265`）：
>
> ```python
> @dataclass
> class ProcessInstance:
>     state: InstanceState = InstanceState.DOING
>     tasks: list[ProcessTask] = field(default_factory=list)
>
>     def complete_task(self, task, operator, vars):
>         # 子实体：10→20，记录操作人/时间/变量
>         task.finish(operator, vars, now())
>         # 聚合根：合并流程变量
>         self.variables.update(vars)
>         self.update_time = now()
>
>     def finish(self):
>         self.state = InstanceState.DONE
>
>     def reject(self):
>         self.state = InstanceState.REJECT
> ```
>
> `model.py:343 ProcessTask`（子实体）：
>
> ```python
> @dataclass
> class ProcessTask:
>     taskState: TaskState = TaskState.DOING
>
>     def finish(self, operator, vars, now):
>         self.taskState = TaskState.DONE
>         self.operator = operator
>         self.finishTime = now
>         self.variables = vars
> ```

### 引擎与聚合根的分工

| 引擎（编排）| 聚合根（规则）|
|---|---|
| 加载解析流程定义 | 完成任务时状态怎么变 |
| 决定下一个节点是谁 | 谁有权处理这个任务 |
| 评估决策表达式 | 驳回时哪些任务要废弃 |
| 解析参与者名单 | 任务创建时的字段约定 |
| 发布事件 / 调用拦截器 | 实例是否所有任务完成 |

**判断标准**：改动涉及「状态 / 字段规则」→ 聚合根；涉及「流程走向 / 外部 IO」→ 引擎。

> **本仓实测**：边界落在 `vendor/jeeflow/model.py`（聚合根）与 `vendor/jeeflow/engine.py`（引擎）的接口上——engine.py 不调 `task.taskState = 20`，而是 `task.finish(operator, vars, now)`。

---

## §3. 伪代码：完成任务的状态机

```
complete_task(task, operator, vars, now):
    task.finish(operator, vars, now)        # 子实体：10→20，记录操作人/时间/变量
    instance.variables = vars               # 聚合根：合并流程变量
    instance.update_time = now

task.finish(operator, vars, now):
    state = DONE(20)
    actor_id = operator
    finish_time = now
    variables = vars
```

六版实现完全一致，仅语法不同。

> **本仓实测对应**（`vendor/jeeflow/model.py:265 ProcessTask.finish`）：
>
> ```python
> def finish(self, operator: str, vars_: dict, now: datetime) -> None:
>     """完成任务（10→20，记录操作人/完成时间）"""
>     self.taskState = TaskState.DONE
>     self.operator = operator
>     self.finishTime = now
>     self.variables = vars_
> ```
>
> `ProcessInstance.complete_task`（`model.py:177-200`）调 `task.finish(...)` 后合并 `vars_` 到 `self.variables` + 更新 `update_time`——**完整对应伪代码**。

---

## §4. 为什么引擎不直接改 `task.taskState`？

试想如果引擎直接写 `task.taskState = 20`：

- 操作人、完成时间、变量合并这三件事**必须在三个地方重复写**
- 将来加规则（如"完成任务自动生成抄送"）要改所有调用点
- 测试只能通过引擎全链路测，无法单测领域规则

聚合根把这三件事内聚成一个方法后：引擎调用一次，规则只维护一处，单测直接测 `complete_task`。

> **本仓实测警示**（`vendor/jeeflow/engine.py:466 _create_task` + `:868 _fire_event`）：
>
> - 引擎**调** `ProcessTask.create(...)` 工厂（不直接构造）+ `task.finish(...)`（不直接改 `taskState`）
> - 唯一例外：`ProcessInstance.withdraw` 调 `self.state = InstanceState.WITHDRAW` 是**聚合根内部**对自身状态的合法修改（聚合根对自身有不变量约束，外部代码不可绕过）
> - 引擎层若需改 `state`，必须经 `withdraw()` / `finish()` / `reject()` 等聚合根方法——**不可直接赋值**

---

## §5. 六版实现对照（本仓 Python 仅）

> **裁剪说明**：上游列 6 语言对照，本项目仅 Python 实现，仅保留 Python 列。

| 语言 | 实现形式 | 关键文件 |
|---|---|---|
| **Python（本仓）** | `@dataclass + 方法`（充血模型）| `vendor/jeeflow/model.py` |

> **本仓实测补充**（`model.py:177-265`）：
>
> - `ProcessInstance` 用 `@dataclass` —— 字段声明简洁（`state: InstanceState = InstanceState.DOING`）
> - 行为方法与字段同 class 内聚（`finish()` / `reject()` / `withdraw()` / `complete_task()` / `create_task()` / `abandon_all_doing()` / `is_all_tasks_finished()` 等）
> - 引擎（`engine.py`）通过 `inst.method(...)` 调用聚合根方法，**不直接改 inst 字段**
>
> 内存仓储（`vendor/jeeflow/memory.py`）与 PG 仓储（`vendor/jeeflow/repository/jdbc.py`）都按「**先在内存聚合根上完成状态转换，再 `repo.save_instance` / `repo.update_instance` 级联落库**」顺序工作——v1.0.1 `update_instance` 级联契约的核心保证。

---

## §6. 聚合根方法清单

> **本仓实测位置** + 与引擎调用场景对应表。

| 方法 | 职责 | 本仓实现位置 | 引擎调用场景 |
|---|---|---|---|
| `create(...)` | 工厂，state=10 | `model.py:177 ProcessInstance.create` | 启动流程（`facade._startAndExecute`）|
| `complete_task(task, operator, vars)` | 完成任务 + 合并变量 | `model.py:200 ProcessInstance.complete_task` | `execute_process_task`（`engine.py:311`）|
| `abandon_all_doing(now)` | 废弃进行中任务 | `model.py:235 ProcessInstance.abandon_all_doing` | 驳回 / 跳转 / 委托撤回 |
| `finish()` | 实例 `10→20` | `model.py:182 ProcessInstance.finish` | 到达 end 节点 |
| `reject()` | 实例 `10→45` | `model.py:182 ProcessInstance.reject` | `submitType=2 REJECT` 跳结束 |
| `withdraw()` | 实例 + 所有 DOING 任务 → WITHDRAW(30) | `model.py:177 ProcessInstance.withdraw` | `processInstance/withdraw`（facade.py:565）|
| `create_task(...)` | 子实体工厂 | `model.py:220 ProcessInstance.create_task` | 所有任务创建点（引擎 `engine.py:466`）|
| `is_all_tasks_finished()` | join 判断 | `model.py:280 ProcessInstance.is_all_tasks_finished` | 引擎 join 节点 |
| `add_variable(vars)` | 追加流程变量 | `model.py:265 ProcessInstance.add_variable` | 拦截器 / 事件扩展点 |
| `abandon_task(task)` | 废弃单个任务 | `model.py:227 ProcessInstance.abandon_task` | 一票否决 / 比例会签余者 / ROLLBACK 重构 |
| `ProcessTask.finish(operator, vars, now)` | `10→20`，记录操作人 | `model.py:265 ProcessTask.finish` | 子实体由 `complete_task` 调用 |
| `ProcessTask.abandon(now)` | `10→99` | `model.py:273 ProcessTask.abandon` | `abandon_all_doing` / `abandon_task` |
| `ProcessTask.is_allowed(operator)` | 参与者权限判断 | `model.py:284 ProcessTask.is_allowed` | `execute_process_task` 鉴权 |
| `ProcessTask.is_doing()` / `is_finished()` | 状态判断 | `model.py:278 ProcessTask.is_doing` | 引擎节点流转条件 |

> **设计者实操**：设计时若需扩展领域行为（如"完成任务自动发钉钉通知"），应**作为拦截器 / 事件监听**实现，而非扩展聚合根。聚合根的扩展点有限（已收敛为 14 个核心方法），新规则走 `EngineExtensions.event_listener` / `EngineExtensions.interceptor_registry` 而非改 `model.py`。

---

## 跨文档交叉引用

- 引擎核心操作（`complete_task` / `withdraw` / `finish` / `reject` 的具体调用）：`../spec/04-engine-ops.md`
- 状态机（`10→20` / `10→45` / `WITHDRAW(30)` 等代码值）：`../spec/03-state-machine.md`
- 聚合根方法在引擎中的编排时序：`../concepts/01-architecture.md` §3 一次请求的生命周期
- SPI 接口（仓储调用）：`../spec/05-spi.md`