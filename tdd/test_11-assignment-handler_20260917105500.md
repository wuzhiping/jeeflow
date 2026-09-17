# 11-assignment-handler 测试日志

**日期**：2026-09-17 10:55
**测试文件**：`./flows/11-assignment-handler.json`
**结论**：⚠️ **PARTIAL** — 4 个 handler 机制正确，前 3 个 task 通过；task4 因 SPI 数据缺失（无 "task4" role）卡死

---

## 1. 流程结构（6 节点 / 5 边）

```
start → task1 → task2 → task3 → task4 → end
       ↓       ↓       ↓       ↓
       Form    Operator Dept  TaskRole
       Field   Handler  Leader Assignee
```

| 节点 | assignmentHandler |
|---|---|
| task1 | `com.mldong.jeeflow.interceptor.impl.FormFieldAssigneeHandler` |
| task2 | `com.mldong.jeeflow.interceptor.impl.OperatorAssignmentHandler` |
| task3 | `com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$DeptLeaderAssignmentHandler` |
| task4 | `com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$TaskRoleAssigneeHandler` |

**注意**：无 apply 节点，start 直接接 task1。

## 2. Handler 解析实测

### 2.1 task1 — FormFieldAssigneeHandler

`builtin.py:39-62`：

```python
async def assign(self, node, inst, operator):
    if inst is None or node is None:
        return []
    value = self._find_field_value(inst.variables, node.id)
    if value is None: return []
    return self._collect(value)
```

`_find_field_value(variables, "task1")`:
- `f_task1` 优先 → `variables["f_task1"]`
- 回落 `task1` → `variables["task1"]`
- 数字后缀匹配

**实测**：传 `f_task1="user1"` → actorIds=`['user1']` ✅

### 2.2 task2 — OperatorAssignmentHandler

`builtin.py:30-36`：

```python
async def assign(self, node, inst, operator):
    if inst is not None and inst.operator:
        return [inst.operator]
    return ["apply.operator"]
```

**实测**：inst.operator=user1 → actorIds=`['user1']` ✅

### 2.3 task3 — DeptLeaderAssignmentHandler

`builtin.py:103-107`：

```python
async def assign(self, node, inst, operator):
    return await self.by_dept(await self.dept_id_of(operator), False)
```

`dept_id_of(operator)` 取 u_deptId 或从 SPI 查 user.deptId，传 `u_deptId="D01"` → D01 leader。

**实测**：传 `u_userId="user1", u_deptId="D01"` → actorIds=`['leader']` ✅

### 2.4 task4 — TaskRoleAssigneeHandler

`builtin.py:135-144`：

```python
async def assign(self, node, inst, operator):
    if node is None or self.org_prov is None:
        return []
    return await self.org_prov.find_by_role(node.id) or []
```

`find_by_role(node.id="task4")` → `SPI_ROLE_TO_USERS.get("task4", [])` → `[]`（SPI 数据无 "task4" role）。

**实测**：actorIds=`[]` → **不创建 task** → 流程卡死

## 3. SPI 数据现状（实测）

`./spi/demo/DEMO_ROLE_TO_USERS.json`：

```json
{
  "leader": ["leader"],
  "manager": ["manager"],
  "director": ["director"],
  "boss": ["boss"]
}
```

**没有 "task4" 这个 role**，所以 TaskRoleAssigneeHandler 找不到 actor。

## 4. 测试详情

### 4.1 startAndExecute

```json
{
  "processDefineId": "113",
  "operator": "user1",
  "title": "11-handler",
  "f_task1": "user1",
  "f_task2": "user1",
  "f_task3": "user1",
  "f_task4": "leader",
  "u_userId": "user1",
  "u_deptId": "D01"
}
```

### 4.2 实测任务流转

| 节点 | Handler | actorIds | 实测状态 |
|---|---|---|---|
| task1 | FormFieldAssigneeHandler | `['user1']` | DONE（自动被 startAndExecute 完成） |
| task2 | OperatorAssignmentHandler | `['user1']` | DONE（user1 agree） |
| task3 | DeptLeaderAssignmentHandler | `['leader']` | DONE（leader agree） |
| task4 | TaskRoleAssigneeHandler | `[]` | ❌ **未创建，流程卡死** |

最终：
```
state=10  activeTasks=0
task1/task2/task3 全 state=20
task4 未创建
```

## 5. 根因分析

### 5.1 Handler 机制正确

4 个 handler 都正确注册到 `HandlerRegistry`，FQCN 完全匹配（builtin.py:153-159）：

```
FormFieldAssigneeHandler         → FormFieldAssigneeHandler instance
OperatorAssignmentHandler        → OperatorAssignmentHandler instance
DeptLeaderAssignmentHandler      → DeptLeaderAssignmentHandler(user_prov, org_prov)
TaskRoleAssigneeHandler          → TaskRoleAssigneeHandler(org_prov)
```

### 5.2 task4 卡死是 SPI 数据缺失

`TaskRoleAssigneeHandler.assign(node=task4_node, ...)` 调 `find_by_role("task4")` → SPI_ROLE_TO_USERS 中无 "task4" → 返回 `[]` → `_create_task` 在 actors=[] 时 return。

**这不是引擎 bug**，是 11-assignment-handler.json 设计假设了"SPI 提供以 node.id 为 roleCode 的角色数据"，但 SPI demo 数据没有。

### 5.3 类似问题

与 08-custom-node 同类型：
- 08：custom 节点设计假设引擎有 clazz/methodName 反射（实际没有）
- 11：task4 设计假设 SPI 提供 "task4" 角色（实际没有）

**两者都是"流程设计对外部数据/功能的假设与实际不符"**。

## 6. 文档同步

`./docs/flow.md §3.3` assignmentHandler 字段已说明使用方式。需新增警示：
- TaskRoleAssigneeHandler 用 `node.id` 作为 roleCode，需 SPI_ROLES 提供对应 key
- 现有 SPI demo 数据只有 leader/manager/director/boss/engineer，不含任何以"task*"为名的角色

## 7. 结论

| 项 | 状态 |
|---|---|
| HandlerRegistry 注册 | ✅ 4 个 FQCN 都注册 |
| FormFieldAssigneeHandler | ✅ f_task1=user1 解析正确 |
| OperatorAssignmentHandler | ✅ 取 inst.operator=user1 |
| DeptLeaderAssignmentHandler | ✅ D01 leader |
| TaskRoleAssigneeHandler | ⚠️ 机制正确，但 SPI 无 "task4" role |
| 流程完整跑通 | ❌ task4 卡死，state=10 未到 end |

**整体**：⚠️ PARTIAL（3/4 handler 验证，task4 因 SPI 数据问题卡死）

## 8. 服务

PID 3365271 在 8101 运行中，healthz UP。
