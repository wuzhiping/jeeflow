# 规范 07 · 元数据能力

> **来源**：https://jeeflow-doc.mldong.com/spec/07-metadata
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**引擎元数据字典参考**——前端设计器 / 表单下拉 / 状态徽标的值漂移问题源头在此。
>
> **本仓实现版本**：`vendor/jeeflow/metadata.py:55 enum_dict_keys()` + `:60 enum_dict(key)` + `:68 HandlerMeta` + `:102 HandlerRegistry`。
>
> **裁剪记录**：枚举字典表重写为本仓实测（`_DICTS` 7 项 + 字典项）；SPI 实现清单重写为本仓实测（`HandlerRegistry` 6 API + `BUILTIN_ASSIGNMENT_METAS` 7 项）；裁掉上游"4 语言跨栈 API 对照表"仅留 Python 实现位置；保留跨语言注册 key 兼容契约。

---

## 枚举字典

> **本仓实测**（`vendor/jeeflow/metadata.py:25 _DICTS`）：**7 个字典**，key 约定 `wf_` + 枚举名转下划线，**与 boot3 / mldong 框架字典 key 完全一致**，存量前端零改动。
>
> 字典项结构（`metadata.py:19 DictItem`）：
>
> ```python
> @dataclass
> class DictItem:
>     value: str   # code（字符串，与引擎枚举值一致）
>     label: str   # 显示名（中文）
> ```

### 7 个字典实测表

> **本仓实测与上游 7 字典 key 名称一致**，但**字典项内容有差异**——已实测验证：

| 字典 key | 字典项（value/label）| 本仓实测 |
|---|---|---|
| `wf_process_define_state` | 0 禁用 / 1 启用 | ✅ 完整（2 项）|
| `wf_process_instance_state` | 10 进行中 / 20 已完成 / 30 已撤回 / 40 强行终止 / 45 已拒绝 / 50 挂起 / 99 已废弃 | ✅ 完整（7 项）|
| `wf_process_submit_type` | **本仓缺项 + 重复** | ⚠️ 详见下表 |
| `wf_process_task_state` | 10 进行中 / 20 已完成 / 30 已撤回 / 40 强行终止 / 50 挂起 / 99 已废弃 | ✅ 完整（6 项）|
| `wf_process_task_type` | 0 主办 / 1 协办 / 2 记录 | ✅ 完整（3 项）|
| `wf_process_task_perform_type` | 0 普通参与 / 1 会签参与 | ✅ 完整（2 项）|
| `wf_countersign_type` | 0 并行会签 / 1 串行会签 | ✅ 完整（2 项）|

**`wf_process_submit_type` 本仓实测字典**（`metadata.py:34`）：

| value | label |
|---|---|
| 0 | 发起申请 |
| 1 | 同意申请 |
| 2 | 拒绝申请 |
| 3 | 退回上一步 |
| 4 | 跳转 |
| 5 | 重新提交 |
| 6 | 退回发起人 |
| 20 | **拒绝申请** ← **与 `2` 重复** |

> ⚠️ **本仓实测 2 处不一致**（与 `vendor/jeeflow/model.py:70 SubmitType` 枚举对比）—— 详见 `../README.md §3 #1/#2` 决策记录 + `diffs.md` §3.1：
>
> 1. **缺失 `7 转办`（TRANSFER）**——`SubmitType` 枚举含 `7`，但字典无该项。前端"转办"提交类型显示需绕开字典或自定义补充
> 2. **`20 拒绝申请` 与 `2 拒绝申请` 重复**——`20` 在枚举是 `COUNTERSIGN_DISAGREE`（会签拒绝），与 `2 REJECT` 语义不同，但字典 label 重复易混淆
>
> 设计者实操：调 `enum_dict("wf_process_submit_type")` 取字典做表单下拉时，**按 `value` 区分**，避免依赖 label 判别。

### API 速查

```python
from jeeflow import enum_dict_keys, enum_dict

# 1. 取字典 key 清单
keys = enum_dict_keys()
# → ["wf_process_define_state", "wf_process_instance_state", ...]  (7 项)

# 2. 按 key 取字典
items = enum_dict("wf_process_instance_state")
# → [DictItem("10", "进行中"), DictItem("20", "已完成"), ...]  (7 项)

# 3. 未知 key 返回空列表
items = enum_dict("unknown_key")
# → []
```

> **本仓实现**：`vendor/jeeflow/metadata.py:55 enum_dict_keys()` 返回 `list(_DICTS.keys())`；`:60 enum_dict(key)` 返回 `list(_DICTS.get(key, []))` —— 拷贝返回防止外部修改污染源。
>
> **跨语言契约**：key 名称对齐 boot3 / mldong 框架（存量前端零改动）；新增 / 变更自动反映到字典，集成方无需同步。

---

## SPI 实现清单（HandlerRegistry）

> **本仓实现**：`vendor/jeeflow/metadata.py:68 HandlerMeta` + `:102 HandlerRegistry` + `:77 BUILTIN_ASSIGNMENT_METAS`（构造时自动注册 7 个通用 AssignmentHandler 元数据）。

### HandlerMeta 4 字段

```python
@dataclass
class HandlerMeta:
    type: str                                      # 处理器类型名（AssignmentHandler / CandidateHandler / FlowInterceptor）
    className: str                                 # 节点配置的 handlerName（与字典 value 一致）
    displayName: str = ""                          # 显示名（字典 label）
    order: int = 0                                 # 排序（小在前）
    group: Optional[str] = None                    # 拦截器 pre/post 分组，可为空
```

### BUILTIN_ASSIGNMENT_METAS 7 项实测（本仓字典源）

> ⚠️ **实测差异警示**：本仓 `BUILTIN_ASSIGNMENT_METAS` 与 `vendor/jeeflow/builtin.py` 注册的 7 简化版主用 key **部分不一致**——

| order | className（本仓 metadata 注册）| displayName |
|---|---|---|
| -9999 | `com.mldong.jeeflow.interceptor.impl.OperatorAssignmentHandler` | 流程发起人 |
| 10 | `com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$ApplicantDeptLeaderAssignmentHandler` | 发起人所属部门经理 |
| 20 | `com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$ApplicantDeptMainLeaderAssignmentHandler` | 发起人所属部门分管领导 |
| 30 | `com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$DeptLeaderAssignmentHandler` | 当前用户所属部门经理 |
| 40 | `com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$DeptMainLeaderAssignmentHandler` | 当前用户所属部门分管领导 |
| 50 | `com.mldong.jeeflow.interceptor.impl.FormFieldAssigneeHandler` | 根据表单字段值分配参与者 |
| 60 | `com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$TaskRoleAssigneeHandler` | 根据任务节点唯一编码关联角色分配参与者 |

> **关键差异**：
> - `OperatorAssignmentHandler` / `FormFieldAssigneeHandler`：metadata 注册**简化版**（无 `OrgUserAssignmentHandlers$` 嵌套）
> - 5 个组织维度 / 角色 handler：metadata 注册**完整版**（带 `OrgUserAssignmentHandlers$` 嵌套）
>
> 而 `vendor/jeeflow/builtin.py:170-183 register_builtin_assignments` **同时**注册简化版主用 + 完整版别名（12 个 key）。
>
> ⇒ 前端设计器从 `HandlerRegistry.list_handlers("AssignmentHandler")` 拿到的字典与引擎运行时实际加载的 handler 集合**部分不一致**——若设计器按 metadata 字典生成的 candidateUsers 默认值，运行时会抛 `ValueError(handler 未注册: ...)`。**建议**集成方在字典返回前显式过滤 / 替换为简化版主用 key。

### HandlerRegistry API 速查（本仓 Python 实测）

```python
from jeeflow import HandlerRegistry, HandlerMeta

registry = HandlerRegistry()      # 自动注册 BUILTIN_ASSIGNMENT_METAS 7 项

# 1. 注册单个 / 批量
registry.register(HandlerMeta(
    type="AssignmentHandler",
    className="my.handler",
    displayName="我的处理器",
    order=100,
))
registry.register_all([
    HandlerMeta(type="FlowInterceptor", className="audit", displayName="审计", order=0, group="post"),
    # ...
])

# 2. 按类型列出（按 order 升序）
items = registry.list_handlers("AssignmentHandler")
# → [HandlerMeta(...), ...] (7 项默认 + 自定义)

# 3. 按类型 + 分组列出（拦截器 pre/post）
post = registry.list_handlers_group("FlowInterceptor", "post")
# → [HandlerMeta(...)]

# 4. 列出已注册类型
types = registry.list_handler_types()
# → ["AssignmentHandler", "FlowInterceptor", ...]
```

> **可选能力**：不注册不影响引擎加载行为（Java 走 `Class.forName`，本仓 Python 走 `builtin.py:register_builtin_assignments` 显式注册）。**注册表的真正价值**是为前端设计器提供字典源，与运行时加载的 handlerName 天然一致。

### 元注册助手（本仓专属）

> **本仓实测**（`vendor/jeeflow/persist.py:486 register_persist_meta`）：

```python
from jeeflow.persist import register_persist_meta
from jeeflow import HandlerRegistry

registry = HandlerRegistry()
register_persist_meta(registry)
# → 自动注册 PersistPostInterceptor（type=FlowInterceptor, className=com.mldong.jeeflow.persist.interceptor.PersistPostInterceptor, displayName="业务数据自动入库", order=0, group="post"）
```

> 设计者实操：在 `main_common.py:build_decision_handlers()` 后调 `register_persist_meta(registry)`，让设计器自动知道 persist 拦截器存在（不用手填）。

---

## 设计者实操速查

| 场景 | 用什么 API |
|---|---|
| 表单下拉"实例状态" | `enum_dict("wf_process_instance_state")` |
| 表单下拉"提交类型" | `enum_dict("wf_process_submit_type")` + **按 value 区分**（避免 `2` 与 `20` 混淆）|
| 设计器"assignmentHandler 下拉" | `registry.list_handlers("AssignmentHandler")` + 替换为简化版主用 key |
| 设计器"interceptor 选 post" | `registry.list_handlers_group("FlowInterceptor", "post")` |
| 自动加 persist 拦截器 | `register_persist_meta(registry)` |
| 字典 key 漂移检查 | `enum_dict_keys()` 返回与 boot3 字典 key 一致时，前端零改动 |

> **跨语言契约保证**：key 名称（`wf_*`）+ value 数值（10/20/30/...）+ label 文案**所有栈统一**——本仓 `metadata.py:25 _DICTS` 与 Java `ProcessInstanceStateEnum.getCode()/getMessage()` 对齐，**杜绝集成方重复定义**。