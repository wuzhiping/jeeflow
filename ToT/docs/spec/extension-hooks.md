# Extension Hooks · 引擎扩展点参考

> **来源**：`vendor/jeeflow/extensions.py` + `engine.py`
> **定位**：扩展 jeeflow 引擎时知道「在哪个点插什么」

---

## 1. EventType · 6 个引擎事件

`vendor/jeeflow/extensions.py:8`

```python
class EventType(Enum):
    PRE_COMMIT          # task 即将提交（可拦截修改 args）
    POST_COMMIT         # task 已提交（已落库）
    TASK_CREATED        # 新 task 创建
    TASK_COMPLETED      # task 完成
    INSTANCE_STARTED    # 实例启动
    INSTANCE_ENDED      # 实例结束
```

**触发时机**：

| 事件 | 触发位置 | 典型用途 |
|---|---|---|
| `PRE_COMMIT` | engine.py execute_process_task 入口 | 参数清洗、权限二次校验 |
| `POST_COMMIT` | engine.py execute_process_task 出口 | 发通知、写审计日志 |
| `TASK_CREATED` | engine.py _create_task_with_actors | 推送待办 |
| `TASK_COMPLETED` | engine.py task 完成分支 | 触发下游任务 |
| `INSTANCE_STARTED` | engine.py start_process_instance_by_id | 启动审计 |
| `INSTANCE_ENDED` | engine.py 实例结束 | 归档通知 |

---

## 2. FlowInterceptor · 拦截点

```python
class FlowInterceptor(ABC):
    async def pre_execute(self, task, operator, args) -> Optional[ProcessInstance]:
        # task 即将执行；返回 None = 继续，返回 ProcessInstance = 替换结果
        ...

    async def post_execute(self, task, operator, args, result) -> None:
        # task 已执行；可记录日志/发通知
        ...
```

**典型实现**：
- 钉钉通知拦截器：`post_execute` 发 IM
- 字段补全拦截器：`pre_execute` 自动补 applicantDeptId
- 权限二次校验：`pre_execute` 拒绝非法 operator

---

## 3. EngineExtensions 注册 API

```python
extensions = EngineExtensions()

# 1. 注册事件监听器
extensions.event_listener(EventType.POST_COMMIT, send_dingtalk)

# 2. 注册拦截器
extensions.interceptor_registry.register(AuditInterceptor())

# 3. 注册自定义决策 handler
extensions.decision_handler(my_decide_func)
```

---

## 4. 委派（delegate）相关事件

**delegate 完整事件链**：

```
TASK_CREATED (原 task)
    ↓
processTask/delegate 调用
    ↓
engine.py:_is_delegate_allowed 校验
    ↓
facade.py:_processTask_delegate 创建 delegate 记录
    ↓
POST_COMMIT (原 task 标记 DELEGATED)
    ↓
TASK_CREATED (新 task 给 targetUser)
    ↓
新 task 完成
    ↓
TASK_COMPLETED → INSTANCE_ENDED (可能)
```

**关键代码**：
- `vendor/jeeflow/facade.py:1992 _processTask_delegate` 入口
- `vendor/jeeflow/facade.py:2036 _processTask_delegateHistory` 历史
- `vendor/jeeflow/engine.py:999 _is_delegate_allowed` 权限

**已知的 delegate 字段问题**（郭开发 14:30 收到的 bug）：
- 委派后 `processTask.delegatedTo` 字段未写
- 应在 `_processTask_delegate` 写库时同步写 `delegatedTo`

---

## 5. 自定义 Assignment Handler

**场景**：业务方需要自定义参与者解析规则。

**继承 `IAssignmentHandler`**：

```python
class MyAssignmentHandler(IAssignmentHandler):
    async def resolve(self, context) -> list[str]:
        # 返回参与者工号列表
        dept_id = context.args.get("deptId")
        return await find_users_by_dept(dept_id)

# 注册
register_builtin_assignments(extensions)
extensions.handler_registry.register("MyAssignment", MyAssignmentHandler())
```

**在 processDefine 里引用**：
```json
{
  "assignmentHandler": "MyAssignment",
  "args": {"deptId": "D001"}
}
```

---

## 6. 决策（Decision）handler

**优先级**：
1. 节点内 `expr` 字段（如 `${amount > 1000}`）
2. `extensions.decision_handler` 注册的全局函数

```python
async def my_decide(flow: FlowModel, instance: ProcessInstance, vars: dict) -> str:
    if vars.get("amount", 0) > 10000:
        return "ceo_approve"
    return "manager_approve"

extensions.decision_handler(my_decide)
```

---

## 7. 反模式（不要这样做）

| 反例 | 后果 |
|---|---|
| 在 `POST_COMMIT` 里同步发 IM | 阻塞 task 完成 |
| 在 `PRE_COMMIT` 改 operator | 审计日志不可信 |
| 注册太多 decision_handler | 优先级混乱 |
| 不写 `processInstance.started` 事件 | 启动审计缺失 |

---

## 8. 调试技巧

```python
# 1. 列出所有注册的 handler
print(extensions.handler_registry.list())

# 2. 列出所有事件监听器
print(extensions.event_listener_registry.list())

# 3. 跟踪 task 全链路
# /api/admin/trace?processTaskId=12345
```

---

## 9. 升级注意

新增 EventType 是兼容的（老代码不订阅 = 无影响）。
删除 EventType 是 breaking change（必须 major version bump）。
修改 decision_handler 签名也是 breaking。

---

**版本**：v1.11.1 · **来源**：故事 001（郭开发加委派有效期规则）→ 01 persona review