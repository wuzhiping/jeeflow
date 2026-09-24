# 用户指南 04 · 扩展开发

> **来源**：https://jeeflow-doc.mldong.com/guides/04-extensions
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的扩展点开发参考。
> **裁剪记录**：§1 保留 + 加本仓 SPI 注册入口注解；§2 保留 Python 示例 + 裁 Java/Go/Node + 加本仓 API 差异注解；§3 保留 + 裁 Java + 加 Python 入口注解；§4 保留 + 裁 Java + 重写 Python 注册方式；§5 保留 + 重写 Python 示例 + 加 6 事件类型清单；§6 裁掉，仅留本仓 Python 路径。

---

## 1. 扩展点总览

| 扩展点 | 时机 | 场景 |
|---|---|---|
| `FlowInterceptor` | 节点执行前后 | 日志、统计、条件拦截 |
| `ProcessEventListener` | 流程生命周期 | 通知（钉钉/企微/短信）、同步业务状态 |
| `IAssignmentHandler`（Registry）| 创建任务时 | 参与者按业务规则计算 |
| `IDecisionHandler`（Registry）| 决策节点 | 表达式表达不了的复杂路由 |

> **本仓 SPI 注册入口**（`main_common.py:apply_extensions()`）：
> - 拦截器 → `EngineExtensions.interceptor_registry={name: FlowInterceptor实例}`（流程定义 `postInterceptors` 按名解析）
> - 决策 handler（Registry 形式）→ `HandlerRegistry.register_decision(name, IDecisionHandler实例)` + `EngineExtensions.registry=registry`
> - 决策 handler（顶层单 callable）→ `EngineExtensions.decision_handler=callable`
> - 事件监听器 → `EngineExtensions.event_listener=async_callable`
> - Custom 节点 handler → `EngineExtensions.custom_handler_registry={key: async_callable}`（`properties.clazz` 按名解析）
> - Assignment handler（顶层单 callable）→ `EngineExtensions.assignment_handler=callable`
> - Assignment handler（Registry 形式）→ `HandlerRegistry.register_assignment(name, IAssignmentHandler实例)` + `EngineExtensions.registry=registry`
>
> 详见 `../main_common.py:301 apply_extensions` + `../vendor/jeeflow/extensions.py:89 EngineExtensions`。

---

## 2. 动态参与者（最常见的扩展）

**场景**：审批人不是固定的，而是"按部门经理"算出来的。

> **先看有没有内置的**：`按部门领导/分管领导/角色/发起人/表单字段` 等常见场景 jeeflow 已内置 7 个通用 handler，注册即用——完整清单见 [07 · 参与者解析（内置 handler 清单）](./07-assignment-handlers)。 下面的自定义示例只在内置不满足时使用。

### 2.1 实现处理器（接口签名 v1.6.0：带 `operator`）

```python
# Python（仅保留本仓相关）
from jeeflow import IAssignmentHandler

class DeptLeaderHandler(IAssignmentHandler):
    """按当前任务操作人所在部门找部门领导"""
    async def assign(self, node, instance, operator: str) -> list[str]:
        dept_id = instance.variables.get("u_deptId")
        return [dept_service.find_leader(dept_id).user_id]
```

> **本仓接口签名**（`vendor/jeeflow/extensions.py:50 IAssignmentHandler`）：`async def assign(self, node, instance, operator: str) -> list[str]`。
>
> - `operator`：当前任务操作人（对齐 Java `Execution.getOperator()`）；
> - 取**流程发起人**用 `instance.operator`；
> - 返回值：list[str]，可多人。
> - **不能**写同步 `def` —— 引擎统一按 awaitable 调用（即便 handler 不做 IO 也需 `async`）。

### 2.2 注册

```python
# 本仓注册方式（main_common.py:build_*_handlers）
from jeeflow import HandlerRegistry

registry = HandlerRegistry()
registry.register_assignment("deptLeaderHandler", DeptLeaderHandler())

# 应用到 engine
from main_common import apply_extensions
apply_extensions(engine, registry=registry)
```

> **本仓注册方式与上游不同**（FIX-T67 §67）：
> - 上游文档：`engine.ext.registry.register_assignment(...)`
> - 本仓：`HandlerRegistry.register_assignment(name, handler)` + 通过 `apply_extensions(engine, registry=...)` 注入
> - `assignmentHandler` 字段值为 `IAssignmentHandler` 实例（**不是**字符串 key）；流程 JSON 中 `"assignmentHandler": "deptLeaderHandler"` 字符串按名解析为 Registry 实例
> - 未注册时引擎抛 `ValueError(handler 未注册: deptLeaderHandler)` —— 不静默跳过

### 2.3 流程定义引用

```json
{
  "id": "task1",
  "type": "snaker:task",
  "properties": { "assignmentHandler": "deptLeaderHandler" }
}
```

> 引擎解析顺序：`assignee` 优先；为空时查 Registry 的 `assignmentHandler`。
>
> **本仓硬约束**：handler FQCN 必须为简化版 `com.mldong.jeeflow.interceptor.impl.*` —— `OrgUserAssignmentHandlers$*` 嵌套类**未注册**，写了立即抛错（详见 `../ToT/guides/02-flow-definition.md` §2.3.1 警示）。

---

## 3. 动态决策

**场景**：分支条件需要查库（如"该客户是否黑名单"），表达式写不了。

```python
# 本仓 Python 实现
from jeeflow import IDecisionHandler

class RiskDecisionHandler(IDecisionHandler):
    """黑名单检查：命中返回走 edge_black，否则 edge_normal"""
    async def decide(self, node, instance, vars_: dict) -> str:
        customer_id = vars_.get("customerId")
        return "edge_black" if risk_service.is_black(customer_id) else "edge_normal"
```

```python
# 注册（main_common.py:build_decision_handlers）
from jeeflow import HandlerRegistry
registry = HandlerRegistry()
registry.register_decision("riskDecisionHandler", RiskDecisionHandler())
apply_extensions(engine, registry=registry)
```

```json
// 流程定义引用
{
  "id": "risk_check",
  "type": "snaker:decision",
  "properties": { "decisionHandler": "riskDecisionHandler" }
}
```

> **本仓接口签名**（`vendor/jeeflow/extensions.py:58 IDecisionHandler`）：`async def decide(self, node, instance, vars: dict) -> str`。
> - 返回值为**目标边的 id**（`edges[].id`），引擎据此跳转；
> - 若返回的边 id 不存在，引擎按顺序找第一条出边（F-112 兜底）；
> - 与 §2 决策表达式（OGNL 风格表达式，内联在 engine.py 决策分支）的关系：handler 用于"查库等表达式干不了的事"；表达式用于纯变量运算。

---

## 4. 拦截器

**场景**：审批节点前置校验——"客户未实名认证则不给组长建任务"。

```python
# 本仓拦截器实现
from jeeflow import FlowInterceptor

class RealnameInterceptor(FlowInterceptor):
    """客户未实名认证则阻断 verify 节点"""
    async def pre_handle(self, node, instance) -> bool:
        if node.id == "verify":
            return instance.variables.get("realnameVerified") == "1"
        return True

    async def post_handle(self, node, instance) -> None:
        # 节点执行后钩子：日志/统计/同步
        audit_log.info(f"node={node.id} done, inst={instance.id}")

    @property
    def order(self) -> int:
        return 10
```

```python
# 注册（main_common.py:build_interceptor_registry）
from jeeflow import EngineExtensions
ext = EngineExtensions(
    interceptor_registry={
        "realname": RealnameInterceptor(),
    },
)
engine.set_extensions(ext)
```

```json
// 流程定义引用（顶层 postInterceptors，按名解析）
{
  "name": "loan",
  "postInterceptors": "realname",
  "nodes": [...]
}
```

**规则**：
- `pre_handle` 返回 `false` → 跳过该节点（不创建任务），流程暂停
- `order` 越小越先执行；post 按倒序（洋葱模型）
- 拦截器在**节点级**生效（可配置到流程级，见流程定义 `postInterceptors`）

> **本仓注册方式与上游差异**（FIX-T34 / FIX-T72 §34/§72）：
> - 上游文档：`engine.getRegistry().register(...)` 反射加载类全限定名
> - 本仓：`EngineExtensions.interceptor_registry={name: FlowInterceptor实例}` + 通过 `apply_extensions(engine, ic_registry=...)` 注入
> - 流程 JSON 中**顶层 `preInterceptors` v1.9.0+ 已修复**（F-34）；老版本静默不生效，建议**优先使用 `postInterceptors`**
> - **未注册拦截器**立即抛 `ValueError(拦截器未注册: realname)`（`vendor/jeeflow/engine.py:1071`）—— 不静默跳过
> - 拦截器未注册的行为（main.py 内存后端 vs main_pg.py PG 后端）差异：内存后端静默通过 code=0；PG 后端严格抛错 code=99999999（FIX-T34 后已统一）。详见 `../docs/known-issues.md §34` + `../docs/flow.md §2`。

---

## 5. 事件监听

**场景**：任务完成发钉钉通知。

```python
# 本仓 Python 实现
from jeeflow import EventType, ProcessEvent

async def on_event(evt: ProcessEvent):
    if evt.type == EventType.TASK_COMPLETE:
        await dingtalk.send(f"任务完成：{evt.taskName}（实例 {evt.instanceId}）")
    elif evt.type == EventType.PROCESS_FINISH:
        await dingtalk.send(f"流程完成：{evt.instanceId}")

# 注册
from jeeflow import EngineExtensions
ext = EngineExtensions(
    event_listener=on_event,
)
engine.set_extensions(ext)
```

**事件清单**（本仓实际枚举，`vendor/jeeflow/extensions.py:8 EventType`，6 种）：

| 事件 | 触发时机 | 关键字段 |
|---|---|---|
| `PROCESS_START` | 流程实例启动 | `instanceId`, `operator` |
| `PROCESS_FINISH` | 流程实例 DONE | `instanceId`, `operator` |
| `PROCESS_REJECT` | 流程实例 REJECT | `instanceId`, `operator` |
| `TASK_CREATE` | 任务被创建 | `instanceId`, `taskId`, `taskName`, `operator` |
| `TASK_COMPLETE` | 任务执行完成 | `instanceId`, `taskId`, `taskName`, `operator` |
| `CC_CREATE` | 抄送人创建（issues/102）| `instanceId`, `ccActorId` |

> **本仓与上游差异**（`vendor/jeeflow/extensions.py:19 ProcessEvent`）：
> - 上游文档列 4 事件（`PROCESS_START` / `PROCESS_FINISH` / `PROCESS_REJECT` / `TASK_COMPLETE`）
> - 本仓实际 6 事件：多 `TASK_CREATE` 与 `CC_CREATE`
> - 事件体字段：`type` / `instanceId` / `taskId` / `taskName` / `operator` / `ccActorId`
> - **注意**：事件只带 id，需要业务数据时**自己查仓储**（刻意设计，见 [设计原理 04](./../concepts/04-extensions)）

---

## 6. 本仓扩展源码位置

> **上游原文给出 4 语言路径表，本节仅保留本仓 Python 相关路径**。

| 扩展 | 本仓位置 |
|---|---|
| 扩展抽象基类 | `vendor/jeeflow/extensions.py`（`FlowInterceptor` / `IAssignmentHandler` / `IDecisionHandler` / `EventType` / `ProcessEvent`）|
| 引擎注入入口 | `main_common.py:apply_extensions()`（`main.py` / `main_pg.py` 均调用）|
| 自定义处理器注册 | `main_common.py:build_custom_handlers()` / `build_decision_handlers()` / `build_interceptor_registry()` |
| 引擎消费入口 | `vendor/jeeflow/engine.py:_resolve_interceptors()` / `_fire_event()` / `resolve_assignment()` / `resolve_decision()` |
| 流程 JSON → 引擎 | `vendor/jeeflow/facade.py`（解析 `postInterceptors` / `assignmentHandler` / `decisionHandler` 字段）|

> 上游 4 语言对照表（Java/Go/Node 路径）见 [上游 04-扩展开发 §6](https://jeeflow-doc.mldong.com/guides/04-extensions)。本项目不引入其他语言后端（PRD 私用项目定位），故仅保留本仓 Python 路径。