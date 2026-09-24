# 用户指南 07 · 参与者解析（内置 handler 清单）

> **来源**：https://jeeflow-doc.mldong.com/guides/07-assignment-handlers
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**内置参与者解析器速查手册**。
> **裁剪记录**：§1 / §2 / §3.1-§3.7 / §5.5 / §5.5.1 / §6 保留 + 加本仓注册实现注解；§4 / §5 自定义 handler 整段裁 Java/Go/Node 仅保留 Python + 重写本仓注册方式。

---

## 1. 参与者是怎么算出来的（解析优先级）

```
创建任务时 resolveActors:
  ① tf_nextNodeOperator 变量      → 动态指定下一节点处理人（最高优先）
  ② assignee 非空                → 固定参与者（逗号分隔多人；"applicant" = 发起人）
  ③ assignmentHandler 注册名      → 内置或自定义处理器（推荐）
  ④ 都没有                        → 不创建任务
```

> **静态优先于动态**：`assignee` 配置了就按静态走，`assignmentHandler` 不生效——避免"两个都配了，结果不确定"。
>
> **本仓实现**（`vendor/jeeflow/engine.py:761 _resolve_actors`）：
>
> | 优先级 | 字段 | 来源 |
> |---|---|---|
> | ① | `tf_nextNodeOperator`（运行时变量）| 任务 `execute` 时 args 透传；`startAndExecute` 时 `f_nextNodeOperator` 自动转换为 `tf_`（KEY_PROCESS_START_NEXT_NODE_OPERATOR / KEY_NEXT_NODE_OPERATOR）|
> | ② | `assignee` 字面量或变量引用 | `"applicant"` → `inst.operator`；`"leader"` → 字面量 userId；变量名 → 查 `vars_` 解析（list/tuple 展开）|
> | ③ | `assignmentHandler` 注册 key | 从 `EngineExtensions.registry`（HandlerRegistry）查 `IAssignmentHandler` 实例；未注册抛 `ValueError(handler 未注册: ...)` |
> | ④ | 都没有 | 不创建任务 → 引擎兜底 warning |

---

## 2. 内置 handler 速查表

> **本仓实际注册 12 个 key**（`vendor/jeeflow/builtin.py:170-183`）：**7 个简化版主用 + 5 个完整版别名**（兼容历史 FQCN）。

| 注册名（`assignmentHandler` 值，**简化版主用**）| 参与者是谁 | 典型场景 | 依赖 |
|---|---|---|---|
| `com.mldong.jeeflow.interceptor.impl.OperatorAssignmentHandler` | 流程发起人 | 发起人确认/自审节点 | 无（纯引擎）|
| `com.mldong.jeeflow.interceptor.impl.FormFieldAssigneeHandler` | 表单字段里选的人 | 申请人在表单里指定审批人 | 无（纯引擎）|
| `com.mldong.jeeflow.interceptor.impl.DeptLeaderAssignmentHandler` | **当前任务操作人**的部门领导 | 谁处理了上一节点，就由他领导审批 | `UserProvider` + `OrgUserProvider` |
| `com.mldong.jeeflow.interceptor.impl.DeptMainLeaderAssignmentHandler` | 当前任务操作人的部门分管领导 | 同上，但要分管领导（第一副职）| 同上 |
| `com.mldong.jeeflow.interceptor.impl.ApplicantDeptLeaderAssignmentHandler` | **流程发起人**的部门领导 | 无论流程走到哪，都由发起人的领导审批 | 同上 |
| `com.mldong.jeeflow.interceptor.impl.ApplicantDeptMainLeaderAssignmentHandler` | 流程发起人的部门分管领导 | 同上，分管领导 | 同上 |
| `com.mldong.jeeflow.interceptor.impl.TaskRoleAssigneeHandler` | 节点编码关联的角色成员 | 按角色审批（如"财务角色"）| `OrgUserProvider` |

> **完整版别名（`OrgUserAssignmentHandlers$XXX` 形式）同时注册**（`builtin.py:179-183`），兼容历史流程 JSON。本仓推荐**简化版**作为新流程主用。
>
> 组织维度 handler 的数据来自 `OrgUserProvider` SPI——**业务方只实现数据接口，不写 handler**（见 [SPI 设计 05](./../concepts/05-spi-design)）。

---

## 3. 逐个详解

### 3.1 流程发起人 —— `OperatorAssignmentHandler`

**场景**：发起人自己再确认一次（如提交后"确认申请信息"）；或节点必须由发起人本人处理。

```json
{
  "id": "confirm",
  "type": "snaker:task",
  "properties": {
    "assignmentHandler": "com.mldong.jeeflow.interceptor.impl.OperatorAssignmentHandler"
  }
}
```

**行为**：参与者 = 流程发起人（`inst.operator`）；发起人为空时兜底 `"apply.operator"`（与 demo 契约一致）。

> **本仓实测**（`vendor/jeeflow/engine.py:793`）：若 `inst.operator` 为空 → 引擎 warning `节点[id] OperatorAssignmentHandler 返回空：操作人为空。`

### 3.2 表单里选人 —— `FormFieldAssigneeHandler`

**场景**：申请表单里有"审批人/会签人"字段，由申请人填写。节点名与字段名**精确匹配**；字段值支持逗号分隔字符串（`"userA,userB"`）或数组（`["userA","userB"]`）。

```json
{
  "id": "task1",
  "type": "snaker:task",
  "properties": {
    "assignmentHandler": "com.mldong.jeeflow.interceptor.impl.FormFieldAssigneeHandler"
  }
}
```

**发起参数**：变量里要有同名字段：

```json
{ "task1": "userA,userB" }        // → 参与者 userA,userB
{ "task1": ["userA", "userB"] }   // → 同上
```

**编号后缀规则**：节点 id 以 `_数字` 结尾时自动去掉后缀再匹配——设计器里 `task_01`/`task_02` 多个节点可以共用一个 `task` 字段（会签拆分场景常用）：

```
节点 id: "task_01" → 匹配变量 "task"（找不到 task_01 时）
```

> **本仓实测**（`vendor/jeeflow/builtin.py:47 FormFieldAssigneeHandler` + `engine.py:773`）：**优先级查找 `f_<node.id>` → 回落 `<node.id>` → 回落 `_数字` 去后缀匹配**（`f_task_01` 找不到时匹配 `f_task`）。上游示例「变量 task1」在本仓**推荐传 `f_task1`**——直接传 `task1` 也能匹配但易混。

### 3.3 当前操作人部门领导 —— `DeptLeaderAssignmentHandler`

**场景**：**谁处理了上一节点，就由他的部门领导审批**。多级流程中不同部门的人提交后，各自的领导审批，无需为每个部门配流程。

```json
{
  "id": "leader_approve",
  "type": "snaker:task",
  "properties": {
    "assignmentHandler": "com.mldong.jeeflow.interceptor.impl.DeptLeaderAssignmentHandler"
  }
}
```

**数据链路**：`operator`（当前任务操作人）→ `UserProvider.get_user` 取 `deptId` → `OrgUserProvider.find_dept_leaders(deptId)` 取领导列表。

**注意**：区分"当前操作人"与"发起人"——上一节点被谁处理（转交/代理后可能是别人），就取谁的领导。要**始终按发起人**算，用 §3.5。

> **本仓 FQCN 修正**（`vendor/jeeflow/builtin.py:19`）：**主用名是简化版** `…DeptLeaderAssignmentHandler`（**无** `OrgUserAssignmentHandlers$` 嵌套类前缀）；完整版 `…OrgUserAssignmentHandlers$DeptLeaderAssignmentHandler` 是**别名**（兼容历史 JSON）。上游文档写嵌套类形式，本仓建议设计者统一用简化版。

### 3.4 当前操作人部门分管领导 —— `DeptMainLeaderAssignmentHandler`

与 §3.3 完全一样，只把 `find_dept_leaders` 换成 `find_dept_main_leaders`（部门第一副职/分管领导）。适用"领导请假时由分管领导审批"等场景。

```json
{
  "assignmentHandler": "com.mldong.jeeflow.interceptor.impl.DeptMainLeaderAssignmentHandler"
}
```

### 3.5 发起人部门领导 —— `ApplicantDeptLeaderAssignmentHandler`

**场景**：**无论流程流转到哪，都由发起人的部门领导审批**（跨部门会签时保持"谁发起谁负责"）。

```json
{
  "id": "final_approve",
  "type": "snaker:task",
  "properties": {
    "assignmentHandler": "com.mldong.jeeflow.interceptor.impl.ApplicantDeptLeaderAssignmentHandler"
  }
}
```

**数据链路**：`inst.operator`（发起人）→ `UserProvider.get_user` 取 `deptId` → `OrgUserProvider.find_dept_leaders(deptId)`。

### 3.6 发起人部门分管领导 —— `ApplicantDeptMainLeaderAssignmentHandler`

同 §3.5，走 `find_dept_main_leaders`。

```json
{
  "assignmentHandler": "com.mldong.jeeflow.interceptor.impl.ApplicantDeptMainLeaderAssignmentHandler"
}
```

### 3.7 按角色 —— `TaskRoleAssigneeHandler`

**场景**：节点绑定一个角色编码，该角色的所有成员都是候选人（任一可办）。**roleCode = 节点 id**——设计器里节点编码即角色编码，无需额外配置。

```json
{
  "id": "finance",
  "type": "snaker:task",
  "properties": {
    "assignmentHandler": "com.mldong.jeeflow.interceptor.impl.TaskRoleAssigneeHandler"
  }
}
```

**数据链路**：`OrgUserProvider.find_by_role("finance")` → 角色成员列表。

> **本仓 roleCode 双轨制**（FIX-T8 §68，`vendor/jeeflow/builtin.py:143 TaskRoleAssigneeHandler`）：
>
> | 优先级 | 取值 | 何时用 |
> |---|---|---|
> | ① | `properties.roleCode`（节点 properties 内显式字段）| Java 设计器规范字段；显式覆盖 |
> | ② | `node.id` | 回落（向后兼容）；节点 id 必须等于 SPI `DEMO_ROLE_TO_USERS.json` 的 key |
>
> 实测提示（`engine.py:781`）：roleCode 在 SPI 角色表中无用户 → warning `TaskRoleAssigneeHandler 返回空：roleCode='<rc>' 在 SPI 角色表中无用户。`

---

## 4. 怎么注册（本仓 Python）

> **上游原文 4 语言（Java/Go/Python/Node）注册方式整段裁剪，保留 Python 实现**。

```python
# main_common.py:build_assignment_handlers()
from jeeflow import register_builtin_assignments, HandlerRegistry

def build_assignment_handlers(user_prov, org_prov):
    """注册 12 个内置 handler key（7 简化版 + 5 完整版别名）"""
    registry = HandlerRegistry()
    register_builtin_assignments(
        registry,
        user_prov=user_prov,
        org_prov=org_prov,
    )
    return registry
```

```python
# 应用到 engine
from main_common import build_assignment_handlers, apply_extensions

registry = build_assignment_handlers(user_prov, org_prov)
apply_extensions(engine, registry=registry)
```

> **本仓 SPI 依赖**：
> - `UserProvider.get_user(user_id) -> UserInfo`（含 `deptId`）
> - `OrgUserProvider.find_dept_leaders(dept_id) -> list[str]`
> - `OrgUserProvider.find_dept_main_leaders(dept_id) -> list[str]`
> - `OrgUserProvider.find_by_role(role_code) -> list[str]`
>
> 业务方实现 SPI 后**无需写 handler**——直接传 `user_prov` / `org_prov` 给 `register_builtin_assignments` 即可。

---

## 5. 自定义 handler（还不够用时）

> **上游 4 语言示例整段裁剪，仅保留 Python 实现**。

接口签名（v1.6.0 起带 `operator`，可区分"当前操作人"与"发起人"）：

```python
# Python（vendor/jeeflow/extensions.py:50 IAssignmentHandler）
from jeeflow import IAssignmentHandler

class MyHandler(IAssignmentHandler):
    async def assign(self, node, instance, operator: str) -> list[str]:
        # operator = 当前任务操作人（上一节点谁处理的）
        # instance.operator = 流程发起人
        return ["userA", "userB"]  # list[str]；空列表 = 不处理（引擎继续走下一优先级）
```

```python
# 注册（main_common.py:build_assignment_handlers）
registry.register_assignment("my.handler", MyHandler())
apply_extensions(engine, registry=registry)
```

```json
// 流程定义引用
{
  "id": "task1",
  "type": "snaker:task",
  "properties": { "assignmentHandler": "my.handler" }
}
```

> **本仓实现注意**：
> - 注册名（`"my.handler"`）是**字符串 key**，引擎按 key 从 HandlerRegistry 取实例
> - 未注册抛 `ValueError(handler 未注册: my.handler)`（**不静默跳过**）
> - **handler 必须 `async def`** —— 引擎统一按 awaitable 调用
> - 完整示例参见 `../flows/11-assignment-handler.json`

---

## 5.5 候选人（candidatePage）—— 执行时指定下个节点处理人

**场景**：当前节点审核时，经办人可以**指定下一个节点的处理人**（转交/预指派人）。`processTask/candidatePage` 端点返回可选项：

- **节点配置了候选**（`candidateUsers` / `candidateGroups`）→ 只能从候选人里选
- **未配置** → 开放全部用户（走 `IUserSearchProvider.page` 用户分页搜索）

候选双源（v1.6.0，对齐 boot4 GlobalCandidateHandler）：

| 节点属性 | 语义 | 示例 |
|---|---|---|
| `candidateUsers` | 逗号分隔的指定 userId，直接作为候选人 | `"userA,userB"` |
| `candidateGroups` | 逗号分隔的角色标识，`OrgUserProvider.find_by_role` 取人 | `"finance"` → 财务角色成员 |

```json
{
  "id": "review",
  "type": "snaker:task",
  "properties": {
    "assignee": "leader",
    "candidateUsers": "userA,userB",
    "candidateGroups": "finance"
  }
}
```

**语义**：candidatePage 传**当前任务** id（如 apply 任务），引擎沿流程找**后继任务节点**（穿透 fork/join/decision），收集其候选配置并去重。候选命中返回候选列表；无候选回退用户搜索（依赖用户搜索钩子注入）。

> 与 `assignmentHandler` 的区别：候选只影响"当前节点可选的下一处理人名单"，**不决定任务创建时的参与者**——任务创建参与者仍由 `assignee` / `assignmentHandler` 决定。
>
> **本仓实测**（`docs/flow.md §3.3 candidatePage`）：必传参数 `processTaskId`（当前任务 ID）；**不是**按 operator 查候选任务；行为：查当前任务**后继节点**的 candidateUsers / candidateGroups。

### 5.5.1 发起时预指派人 —— `f_nextNodeOperator`（v1.6.0）

**场景**：发起流程时就指定第一个业务节点的处理人（"发起并预指派"，如发起报销时直接指定财务审批人）。`startAndExecute` 发起时 args 带 `f_nextNodeOperator`：

```bash
startAndExecute({ processDefineId, operator, f_nextNodeOperator: "finA" })
  # → 自动完成申请节点（apply）时转换为 tf_nextNodeOperator
  # → 第一个业务节点参与者 = finA（覆盖其 assignee / assignmentHandler）
```

**与 `tf_nextNodeOperator` 的关系**（对齐 boot3 两个预留 key）：

| key | 时机 | 语义 |
|---|---|---|
| `f_nextNodeOperator` | **发起时**（`startAndExecute` args）| 指定第一个业务节点处理人；内部转换为 `tf_` |
| `tf_nextNodeOperator` | **任务执行时**（`execute` args）| 指定下一节点处理人（最高优先，v1.0.1 已有）|

两者最终都走引擎同一读取链（`resolveActors` 第一优先），`f_` 只是发起场景的便捷入口。

> **本仓实现**（`vendor/jeeflow/engine.py:26-28 KEY_NEXT_NODE_OPERATOR / KEY_PROCESS_START_NEXT_NODE_OPERATOR`）：
>
> ```python
> KEY_NEXT_NODE_OPERATOR = "tf_nextNodeOperator"           # v1.0.1
> KEY_PROCESS_START_NEXT_NODE_OPERATOR = "f_nextNodeOperator"  # v1.6.0
> ```
>
> 详见 `../docs/known-issues.md`。

---

## 6. 常见问题

- **组织 handler 没效果？** 检查是否注入了 `OrgUserProvider`（部门领导/角色查不到人 → 不创建任务）
- **字段配了但参与者为空？** 确认发起参数里**变量名与节点 id 完全一致**（含大小写）；`_数字` 后缀只支持去掉**尾部数字**，`t1_approve` 这类中间数字不处理
- **`assignee` 和 `assignmentHandler` 都配了？** `assignee` 生效，handler 被忽略

> **本仓补充 3 条**：
> - **FormFieldAssigneeHandler 变量名带 `f_` 前缀**：本仓优先查 `f_<node.id>`，回落 `<node.id>`（`engine.py:773`）；上游文档示例「`task1`」在本仓推荐传 `f_task1`，直接传 `task1` 也能匹配
> - **TaskRoleAssigneeHandler roleCode 双轨**：`properties.roleCode` 优先，回落 `node.id`（FIX-T8 §68）
> - **完整版 FQCN 别名兼容**：历史流程写 `…OrgUserAssignmentHandlers$XXX` 仍能跑（`builtin.py:179-183` 别名注册），但新流程建议用简化版 `…XXX`