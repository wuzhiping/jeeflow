# 设计原理 03 · 执行引擎——一次审批的完整旅程

> **来源**：https://jeeflow-doc.mldong.com/concepts/03-execution-engine
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**执行引擎原理参考**——理解图遍历、任务指针设计、决策优先级、Fork/Join 语义、会签四模式、驳回跳转、6 事件挂载点是把握引擎行为的基础。
>
> **本仓实测**：`vendor/jeeflow/engine.py` + `model.py` + `extensions.py:8 EventType` 枚举 + `persist.py`。
>
> **裁剪记录**：§1-§9 保留 + 加本仓实测伪代码与路径；§10 6 语言源码表裁掉 5 语言仅留 Python。

---

## §1. 核心抽象

执行引擎的本质是一个**图遍历器**：从 start 节点出发，沿着边推进，在任务节点停下生成待办，在决策节点选路，在 fork/join 处分合。

```
FlowModel（流程定义）
 ├── nodes[]：start / task / decision / fork / join / end / custom / callActivity
 └── edges[]：sourceNodeId → targetNodeId（决策边带 expr + text.value）

执行状态 = ProcessInstance + 当前节点指针（通过 task.taskName 反查节点）
```

**关键设计**：任务完成后，引擎通过 `task.taskName` 在 FlowModel 里反查节点，再 `follow_edges` 找到下一个节点——**不需要在实例里维护"当前节点"指针**，任务本身就是指针。这简化了持久化模型（8 张表，无游标表）。

> **本仓实测**（`vendor/jeeflow/engine.py:210 _follow_edges` + `:282 find_node`）：
>
> ```python
> def _follow_edges(self, flow, current_node) -> list[FlowNode]:
>     """从 current_node 的所有出边获取目标节点"""
>     edges = [e for e in flow["edges"] if e["sourceNodeId"] == current_node.id]
>     return [find_node(flow, e["targetNodeId"]) for e in edges]
>
> def find_node(self, flow, node_id) -> Optional[FlowNode]:
>     """按 task.taskName 反查节点"""
>     return next((n for n in flow["nodes"] if n["id"] == node_id), None)
> ```

---

## §2. 启动流程

### 2.1 `start_process_instance_by_id`（引擎职责）

```
1. find_define_by_id → JSON → FlowModel
2. ProcessInstance.create（工厂：state=10，注入用户变量）
3. save_instance
4. 发布 PROCESS_START 事件
5. 找到 start 节点 → follow_edges → 逐个 execute_node
```

启动后生成的第一个任务：发起申请节点（`assignee="applicant"` → 解析为发起人）。

### 2.2 `startAndExecute`（调用方契约，引擎不内置）

```
1. 调 start_process_instance_by_id
2. 取所有进行中任务
3. 逐个 execute_process_task（submitType=0 APPLY）
```

> 为什么引擎不自动做第 2、3 步？因为"第一个任务是否自动完成"是业务决策——有些流程第一个节点就是申请人填单（需要手动），有些是纯审批流（自动跳过）。引擎保持中立，由调用方选择。
>
> **本仓实测**（`vendor/jeeflow/facade.py:155 _startAndExecute`）：契约由 facade 实现，引擎不感知；`facade.py:246 _startAndExecute` 自动调 `execute_process_task` 完成 apply 节点。

---

## §3. 完成任务（核心路径）

```
execute_process_task(task_id, operator, args):
  ┌─ load_and_check
  │    task = find_task_by_id
  │    校验：task.taskState == DOING
  │    校验：task.is_allowed(operator)      # actor_ids 包含 operator
  │    inst = find_instance_by_id
  │
  ├─ 聚合根：inst.complete_task(task, operator, vars)
  │    task.finish(...)                     # 10→20
  │    inst.variables 合并
  │
  ├─ 持久化 + 发布 TASK_COMPLETE 事件
  │
  └─ 推进（关键路径）：
       cur_node = find_node(flow, task.task_name)
       for next in _follow_edges(cur_node):
           case next.type:
             END      → inst.finish() + 发布 PROCESS_FINISH
             TASK     → execute_node → create_task（解析参与者）
             DECISION → evaluate_decision（选一条出边）
             FORK     → 递归 execute_node 每条出边
             JOIN     → 若无进行中任务才放行
```

> **本仓实测**（`vendor/jeeflow/engine.py:707 execute_process_task`）：
> - 12 步核心路径：load → check → complete_task 聚合根 → save_task + fire TASK_COMPLETE → find_node → switch by node type
> - task.is_allowed(`operator`) 系统代执行：`flow.auto` / `flow.admin` 恒放行
> - 推进核心 4 节点类型分支：END / TASK / DECISION / FORK / JOIN / CUSTOM

---

## §4. 决策节点：三种求值优先级

```
evaluate_decision(node):
  1. Registry 按名解析（decisionHandler/assignmentHandler）
       → 返回目标边 ID → 直接跳转
  2. 扩展注入的 DecisionHandler
  3. 出边 expr 表达式求值（ExpressionEvaluator SPI）
       → 遍历出边，第一个 expr 为真的边获胜
       → 若出边无 expr，作为默认分支
```

**优先级设计理由**：Registry（注册的处理器）是编译期可确定的强约定；表达式是运行期自由求值。有处理器走处理器，没有才回退表达式——业务方按需选择。

> **本仓实测**（`vendor/jeeflow/engine.py:1381 _eval_decision_expr` + `SimpleExprEvaluator`）：
>
> - 第 1 优先级：`HandlerRegistry.resolve_decision(name)` → `IDecisionHandler.decide(node, instance, vars)`
> - 第 2 优先级：`EngineExtensions.decision_handler`（单 callable）→ `async def decide(flow, inst, vars) -> str`
> - 第 3 优先级：出边 `expr` 表达式求值（OGNL 风格 `#var` / 直接变量名）
> - **兜底**（FIX-T112 §113）：所有 expr 评估失败且无默认边 → 走第一条边（可能创建孤儿 DOING task）→ `verify W013` 警告
>
> 详见 `../ToT/guides/02-flow-definition.md` §5。

---

## §5. Fork / Join 语义

```
FORK：无条件并行——递归执行每条出边（生成多个任务）
JOIN：等待所有分支完成——只有 find_doing_tasks 为空时才放行
```

**Join 的实现**不统计分支数，而是问聚合根"还有没有进行中任务"：

```
JOIN 放行条件 = inst 无任何 DOING 任务
```

**为什么可以这么简化**：因为 fork 之后只可能产生任务节点（决策/嵌套 fork 最终都落到任务），任务完成顺序不定，但**只要还有任务在做，join 就等着**；全部完成则放行。这是 snaker 风格引擎的经典做法，牺牲了"分支数精确计数"，换来了模型简单（不需要在实例上记录分支计数）。

> **本仓实测**（`vendor/jeeflow/engine.py`）：
> - FORK：`execute_node(fork)` → 遍历出边 → 每条出边递归 `execute_node(target)`
> - JOIN：`is_all_tasks_finished()` 调聚合根（`model.py:280`）—— 实例 `tasks` 列表中**所有**任务 `taskState != DOING` 才放行
> - 设计建议（FIX-T35 §30）：即便 FIX-T35 后已支持隐式 join，**推荐显式加 join 节点**——流程图可视化清晰 + 防 task 节点多条无条件出边陷阱（F-110）+ verify W012 警告
>
> 详见 `../ToT/guides/02-flow-definition.md` §3 + `../docs/known-issues.md §30`。

---

## §6. 会签：三种模式

会签节点的判定：`performType=1` 且有 `countersignType`。

### 6.1 并行会签（PARALLEL）

```
create_task: 为每个 actor 创建一个独立任务（同 task_name）
完成一个：检查是否还有同节点 DOING 任务 → 有则等待
全部完成：走下一节点
```

> **本仓实测**（`engine.py:468 _create_countersign_tasks`）：逐 actor 调 `ProcessTask.create(...)` 落库；剩余 DOING 检测在 `engine.py:121 _check_doing_tasks`。

### 6.2 串行会签（SEQUENTIAL）

```
create_task: 只创建第一个 actor 的任务
            任务变量写入 operatorList / loopCounter / nr_of_instances
完成任务：loop_counter+1 < nr_of_instances → 创建下一个 actor 的任务
          否则 → 走下一节点
```

串行会签的关键：**进度存在任务变量里**（`operatorList_${nodeId}` 等），不落表——因为串行是"同一节点的多次实例化"，复用同一 `task_name`。

### 6.3 按比例会签（RATIO）

```
按并行方式创建任务，放行条件由 countersignCompletionCondition 表达式决定
（如 #nrOfCompletedInstances>=2，已支持，见 flows/07-countersign-ratio.json）
```

> 按比例的阈值判断（如"2/4 同意即通过"）通过会签节点 `countersignCompletionCondition` 表达式实现（如 `#nrOfCompletedInstances>=2`），**已支持**。

### 6.4 会签拒绝：软拒绝（默认）与一票否决（ONE_VOTE_VETO）

```
submitType=20（COUNTERSIGN_DISAGREE）：门面自动置 countersignDisagreeFlag=1
节点 countersignCompletionCondition == "ONE_VOTE_VETO"（忽略大小写）：
    一票否决 → 节点立即 merged 推进，flag 落实例/任务变量
否则（默认，含条件为空 / 比例表达式）：
    软拒绝 → 否决者任务正常完成，flag 仅作流程变量记录（供下游参考），
             流程不阻断：并行等其余成员 / 串行推进下一人 / 按表达式判定
```

- **默认策略 = 软拒绝**：会签意见一般只作下一节点的参考，不阻断流程（对齐 mldong 内置引擎）
- **阻断式否决 = 定义级可选开关**：在设计器把节点 `countersignCompletionCondition` 填 `ONE_VOTE_VETO` 即开启
- 节点 merged 推进时，该节点剩余 DOING 会签任务一律废弃（`taskState=99`，FIX-T111 §112），不留孤儿待办（如并行会签 3 人，第 2 人否决整单 → 第 3 人待办被清空）

> **本仓实测铁律**（FB-0008 §113）：
> - 字段值 = **表达式** → 比例模式（放弃一票否决）
> - 字段值 = **字符串 "ONE_VOTE_VETO"** → 一票否决模式（放弃比例）
> - 两种语义**互斥**，不可复合
>
> 详见 `../ToT/guides/02-flow-definition.md` §2.5 + `../docs/known-issues.md §113`。

---

## §7. 驳回与跳转

```
execute_and_jump_to_end(task_id, operator, args):              # 拒绝（REJECT=2）→ 跳结束
  聚合根 abandon_all_doing → 完成任务 → inst.reject()（10→45）

execute_and_jump_task(task_id, operator, args, target):         # 跳转（JUMP=4）/ 退回上一步（ROLLBACK=3）
  聚合根 abandon_all_doing → 完成任务
  target 节点 → execute_node（重新生成目标任务）

execute_and_jump_to_first_task_node(task_id, operator, args):   # 退回发起人（ROLLBACK_TO_OPERATOR=6）
  聚合根 abandon_all_doing → 完成任务
  第一个任务节点重执行，参与者强制为发起人 → 发起人收到新待办（实例保持 10）
```

> **本仓实测**（`vendor/jeeflow/engine.py`）：
>
> | 方法 | 实测位置 | 行号 |
> |---|---|---|
> | `execute_and_jump_to_end` | `_handle_end_jump` | `:239` |
> | `execute_and_jump_task`（ROLLBACK / JUMP）| `_handle_rollback_jump` | `:245` |
> | `execute_and_jump_to_first_task_node`（ROLLBACK_TO_OPERATOR=6）| `_handle_jump_to_first_task` | `:272` |
> | `_resolve_actors` ROLLBACK 场景 | 行 `:356` |
>
> **submitType 行为**：`submitType=2(REJECT)` 调 `execute_and_jump_to_end`（实例→45，无新待办）；退回发起人用 `submitType=6` 调 `execute_and_jump_to_first_task_node`。详见 `../spec/04-engine-ops.md` + `../ToT/guides/05-scenarios.md` 场景一。

---

## §8. 拦截器与事件挂载点

```
execute_node(node):
  pre_handle(node, instance)              # 按 order 升序；返回 false 中断该节点执行
      ├── 节点分派（task/decision/fork/join/end）
  post_handle(node, instance)             # 无论成功失败都执行

事件挂载点（引擎 fire）：
  PROCESS_START    启动流程
  PROCESS_FINISH   到达 end（Java/Rust 与 REJECT 合并为 INSTANCE_END）
  PROCESS_REJECT   拒绝（跳结束）
  TASK_CREATE      任务落库后 fire（逐任务；会签各一次）
  TASK_COMPLETE    完成任务
  CC_CREATE        抄送人创建（issues/102）
```

> **本仓实测**（`vendor/jeeflow/extensions.py:8 EventType(Enum)`）：
>
> ```python
> class EventType(Enum):
>     PROCESS_START = "PROCESS_START"     # 启动
>     PROCESS_FINISH = "PROCESS_FINISH"   # 完成
>     PROCESS_REJECT = "PROCESS_REJECT"   # 拒绝
>     TASK_CREATE = "TASK_CREATE"         # 任务创建
>     TASK_COMPLETE = "TASK_COMPLETE"     # 任务完成
>     CC_CREATE = "CC_CREATE"             # 抄送（issues/102）
> ```
>
> - 6 事件，与上游 5 事件 + 本仓实测 CC_CREATE
> - 触发位置：`engine.py:108 _fire_event`（统一 fire） + 节点处理器 + 任务完成路径
> - 监听入口：`EngineExtensions.event_listener = async_callable`（`extensions.py:95`）
> - 「事件 → 消息」的字段组装 + 落库是**集成层职责**（详见 `../ToT/guides/04-extensions.md` §5 + `../concepts/04-extensions.md`）

---

## §9. 一次完整旅程（时序）

```
发起人: startAndExecute
  start → apply(自动完成) → 组长审批
组长:   execute_process_task(同意, submitType=1)
  → 经理审批
经理:   execute_and_jump_to_first_task_node(退回发起人, submitType=6)
  → apply 重执行（参与者=发起人）→ 发起人收到新待办
发起人: execute_process_task(重新提交, submitType=0)
  → 组长审批 → 经理审批 → 组长审批... 直到 end
  → inst.finish() → PROCESS_FINISH
```

> **本仓实测**（同构）：上述流程与本仓 `flows/09-with-reject.json`（含驳回流程） + `flows/10-mixed-mode.json`（混合模式）+ `flows/13-countersign-one-vote-veto.json`（一票否决）+ `flows/17-suspend-resume-test.json`（挂起恢复）4 个 sample 完整对应。详见 `../ToT/guides/05-scenarios.md` 场景一/三/四 + `../ToT/guides/04-extensions.md` §4。

---

## §10. 关键源码位置（本仓 Python 仅）

> **裁剪说明**：仅保留 Python 路径。

| 主题 | 本仓 Python 路径 |
|---|---|
| 启动 / 执行 / 跳转 | `vendor/jeeflow/engine.py`（`EngineImpl` 类） |
| 节点遍历 `execute_node` | `vendor/jeeflow/engine.py:execute_node` |
| 决策求值 | `vendor/jeeflow/engine.py:1381 _eval_decision_expr` + `SimpleExprEvaluator` |
| 会签创建 | `vendor/jeeflow/engine.py:468 _create_countersign_tasks` |
| 聚合根状态转换 | `vendor/jeeflow/model.py:177 ProcessInstance` + `:227 ProcessTask` |
| 事件枚举 | `vendor/jeeflow/extensions.py:8 EventType` |
| 事件 fire | `vendor/jeeflow/engine.py:108 _fire_event` |

---

## 跨文档交叉引用

- 引擎核心操作（start / execute / reject / withdraw / transfer）：`../spec/04-engine-ops.md`
- 状态机（`InstanceState` 7 值 + `TaskState` 6 值）：`../spec/03-state-machine.md`
- 聚合根方法清单：`../concepts/02-domain-model.md` §6
- 拦截器 / 事件扩展点：`../ToT/guides/04-extensions.md` §4-§5
- 会签四模式 + 一票否决 + submitType=20 拓扑约束：`../ToT/guides/02-flow-definition.md` §2.5
- 业务闭环场景（请假 / 报销 / 会签 / fork-join / 抄送）：`../ToT/guides/05-scenarios.md`