# 附录 B · 下拉选项与状态值对照

> **来源**：https://jeeflow-doc.mldong.com/manual/appendix-b-values
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**附录 B**——界面上看到的中文选项，对应的引擎取值。排查问题、直接调接口、手写流程 JSON 时对照用。完整配置项字典见 [规范 02 · 流程定义格式](../spec/02-flow-definition.md)。
>
> **本仓实测**：基于 `vendor/jeeflow/model.py:46 InstanceState(IntEnum)` + `:55 TaskState(IntEnum)` + `:70 SubmitType(IntEnum)` + `metadata.py:25 _DICTS` 7 字典 + `builtin.py:15-30` 12 handler FQCN。
>
> **裁剪记录**：流程分类 + 节点基础信息 + 设计器模式**原文保留**；参与人处理类 + 拦截器 + 字段权限 + 持久化 + 提交类型 + 实例状态 6 节**全部保留并重写为本仓实测对照表**。

---

## 流程分类（原文保留）

| 值 | 界面 |
|---|---|
| 1 | 假勤管理 |
| 2 | 人事管理 |
| 3 | 智能财务 |
| 4 | 法务管理 |
| 5 | 行政管理 |
| 6 | 业务管理 |
| 99 | 其他 |

---

## 节点基础信息（原文保留）

| 界面字段 | 界面选项 | 引擎取值 |
|---|---|---|
| 任务类型 | 主办 | `taskType` 0 |
| 任务类型 | 协办 | `taskType` 1 |
| 参与类型 | 普通参与 | `performType` 0（任一人办理即通过）|
| 参与类型 | 会签参与 | `performType` 1（多人，按会签类型与完成条件）|
| 会签类型 | 并行会签 | `countersignType` 0 |
| 会签类型 | 顺序会签 | `countersignType` 1 |

> **本仓实测补充**（`docs/flow.md §3.3`）：
>
> - `performType=1` 字符串兼容：`'1'` / `'ALL'` / `'COUNTERSIGN'` 引擎自动容错
> - `performType=2` RECORD 模式（实测任务创建后自动完成）—— **不在上游对照表**，是本仓额外发现（FIX-T30 §3.3）
>
> 详见 `../ToT/guides/02-flow-definition.md` §4。

---

## 参与人处理类（重写为本仓实测）

> **本仓实测**（`vendor/jeeflow/builtin.py:15-30`）：7 个简化版主用 + 5 个完整版别名 = 12 个 key。下表列出设计者实际写流程 JSON 时填入 `assignmentHandler` 字段的 FQCN：

| 界面显示名 | 写入 `assignmentHandler` 的值 | 本仓 enum / FQCN |
|---|---|---|
| 流程发起人 | `com.mldong.jeeflow.interceptor.impl.OperatorAssignmentHandler` | `builtin.py:38 OperatorAssignmentHandler` |
| 发起人所属部门经理 | `com.mldong.jeeflow.interceptor.impl.ApplicantDeptLeaderAssignmentHandler` | `builtin.py:125`（**简化版主用**）|
| 发起人所属部门分管领导 | `com.mldong.jeeflow.interceptor.impl.ApplicantDeptMainLeaderAssignmentHandler` | `builtin.py:134`（**简化版主用**）|
| 当前用户所属部门经理 | `com.mldong.jeeflow.interceptor.impl.DeptLeaderAssignmentHandler` | `builtin.py:111`（**简化版主用**）|
| 当前用户所属部门分管领导 | `com.mldong.jeeflow.interceptor.impl.DeptMainLeaderAssignmentHandler` | `builtin.py:118`（**简化版主用**）|
| 根据表单字段值分配参与者 | `com.mldong.jeeflow.interceptor.impl.FormFieldAssigneeHandler` | `builtin.py:47` |
| 根据任务节点唯一编码关联角色分配参与者 | `com.mldong.jeeflow.interceptor.impl.TaskRoleAssigneeHandler` | `builtin.py:143` |

> **本仓实测警示**（FIX-T67 §67）：
>
> - 上游文档写完整版 FQCN（`OrgUserAssignmentHandlers$...`）——本仓**同时**注册 12 个 key（7 简化版主用 + 5 完整版别名）
> - 历史流程用完整版仍能跑；**新流程建议用简化版主用**（无 `OrgUserAssignmentHandlers$` 嵌套前缀）
> - 详见 `../ToT/guides/07-assignment-handlers.md` §2 + `../spec/05-spi.md` §IOrgUserProvider

**候选用户处理类** 下拉在净装镜像里没有注册项，为空属正常。

---

## 拦截器（重写为本仓实测）

| 界面字段 | 形态 | 净装镜像里的选项 | 本仓实测位置 |
|---|---|---|---|
| 流程属性 → 前置拦截器 | 下拉 | 无注册项 | `engine.py:1054 _resolve_interceptors`（未注册抛 `ValueError`）|
| **流程属性 → 后置拦截器** | 下拉 | **业务数据自动入库**（`com.mldong.jeeflow.persist.interceptor.PersistPostInterceptor`）| `persist.py:486 register_persist_meta` 自动注册到 `HandlerRegistry` |
| 节点高级配置 → 前置 / 后置拦截器 | 文本框 | 填类全限定名，多个用逗号分隔 | `extensions.py:92 interceptor_registry: dict[str, FlowInterceptor]` |

> **本仓实测 6 事件**（`extensions.py:8 EventType`）：`PROCESS_START` / `PROCESS_FINISH` / `PROCESS_REJECT` / `TASK_CREATE` / `TASK_COMPLETE` / `CC_CREATE`——监听入口 `EngineExtensions.event_listener`（单回调）。详见 `../concepts/04-extensions.md` §4 + `../ToT/guides/04-extensions.md` §5。

---

## 字段权限（重写为本仓实测）

| 值 | 界面 | 效果 | 本仓实现 |
|---|---|---|---|
| `1` | 只读 | 可见不可改 | `persist.py:302 PERM_READ_ONLY` |
| `2` | 可编辑 | 正常填写 | `persist.py:303 PERM_EDIT`（**缺省**）|
| `3` | 不可见 | 该节点不渲染这个字段 | `persist.py:304 PERM_HIDDEN` |

存储形式是节点属性里的 `field.PERMISSION_{字段名}`；发起表单字段带 `f_` 前缀，故实际键名形如 `PERMISSION_f_days`。

> **本仓实测双键格式**（v1.8.1+ issues/25）：
>
> ```json
> {
>   "id": "task1",
>   "properties": {
>     "field": {
>       "PERMISSION_f_title": 1,
>       "PERMISSION_amount": 2
>     }
>   }
> }
> ```
>
> - **优先** `PERMISSION_f_{字段全名}`（前端 vben5-wf 设计器约定）
> - **兼容** `PERMISSION_{去前缀名}`（v1.8.0 首版）
> - 缺省 = 可编辑
>
> 详见 `../spec/09-persist.md` §4.2 + `../docs/known-issues.md §82`。

---

## 持久化（重写为本仓实测）

| 界面字段 | 选项 | 取值 | 本仓 enum |
|---|---|---|---|
| 持久化模式 | 归档 | `ARCHIVE` | `persist.py:298 PERSIST_MODE_ARCHIVE` |
| 持久化模式 | 同步 | `SYNC` | `persist.py:299 PERSIST_MODE_SYNC` |

> **本仓实测差异**：
>
> - ARCHIVE（缺省）：`submitType=AGREE(1)` + end 节点 + `state=DONE(20)` 三条件满足才落库（`persist.py:355-372 _handle_archive`）
> - SYNC：发起 `INSERT` → 任务节点 `UPDATE`（按权限过滤）→ 结束节点 `UPDATE`（定稿状态）
> - **字段权限双保险**：拦截器写侧过滤 + v1.8.2 起引擎办理入口过滤（`filterFieldByPerm`）
> - **非 `SYNC` 值一律回落 `ARCHIVE`**（未知值不报错，保持向后兼容）
>
> 详见 `../spec/09-persist.md` §4.1 / §4.2 + `../ToT/guides/08-persist.md` §3。

---

## 提交类型（重写为本仓实测）

> **本仓实测**（`model.py:70 SubmitType(IntEnum)`）：9 枚举 + 引擎路由方法对照表：

| 值 | 枚举 | 含义 | 界面按钮 | 引擎方法 |
|---|---|---|---|---|
| `0` | `APPLY` | 发起申请 | 发起（自动办结申请节点） | `execute_process_task` |
| `1` | `AGREE` | 同意申请 | 同意 | `execute_process_task` |
| `2` | `REJECT` | 拒绝申请 | 不同意（普通节点） | `execute_and_jump_to_end` |
| `3` | `ROLLBACK` | 退回上一步 | 退回上一步 | `execute_and_jump_task`（血缘版） |
| `4` | `JUMP` | 跳转 | 跳转 | `execute_and_jump_task(target=task_name)` |
| `5` | `RE_APPLY` | 重新提交 | 被退回后重新提交 | `execute_process_task` |
| `6` | `ROLLBACK_TO_OPERATOR` | 退回发起人 | 退回发起人 | `execute_and_jump_to_first_task_node` |
| `7` | `TRANSFER` | 转办 | `processTask/transfer`（不走 `execute`） | `remove_task_actor` + `add_task_actor` |
| `20` | `COUNTERSIGN_DISAGREE` | 会签拒绝 | 不同意（会签节点） | `execute_process_task` + `countersignDisagreeFlag=1` |

> ✅ **字典已修复**（2026-09-24，详见 `diffs.md §3.1 #1/#2`）：
> - `metadata.py:34 wf_process_submit_type` 现含完整 **9 项**（含 `7 转办`）
> - `20` label 已改为「会签拒绝」，与 `2 拒绝申请` 区分
>
> 设计者实操：可放心按 `value` 或 `label` 调用 `enum_dict("wf_process_submit_type")`。

---

## 实例状态（重写为本仓实测）

> **本仓实测**（`model.py:46 InstanceState(IntEnum)`）：7 值枚举。命名差异：上游 `FINISHED` 对应本仓 `DONE`，上游 `ABANDON` 对应本仓 `ABANDON`。

| 值 | 界面 | 本仓 enum | 触发场景 |
|---|---|---|---|
| `10` | 进行中 | `InstanceState.DOING` | 初始状态 |
| `20` | 已完成 | `InstanceState.DONE`（上游 `FINISHED`）| 正常走到 end 节点 |
| `30` | 已撤回 | `InstanceState.WITHDRAW` | `processInstance/withdraw`（发起人撤回）|
| `40` | 强行终止 | `InstanceState.INTERRUPT` | `processInstance/interrupt`（管理员终止）|
| `45` | 已拒绝 | `InstanceState.REJECT` | `submitType=2` 跳结束 |
| `50` | 挂起 | `InstanceState.PENDING` | `processInstance/suspend`（FIX-T70）|
| `99` | 已废弃 | `InstanceState.ABANDON` | 流程作废（任务级 99 触发）|

任务级状态与迁移图见 [规范 03 · 状态机](../spec/03-state-machine.md)。

> **本仓实测任务级 6 状态**（`model.py:55 TaskState(IntEnum)`）：10 DOING / 20 DONE / 30 WITHDRAW / 40 INTERRUPT / 50 PENDING / **99 ABANDONED**（带 ED 后缀）—— 任务级**无** 45 REJECT（拒绝是实例级终结状态）。

---

## 设计器模式（原文保留）

`mldong-flow-designer-plus` 支持 `canvas` 与 `dingtalk` 双模式；一键部署包的前端固定用 **dingtalk**（钉钉风格竖排树），所以手册里的截图都是这一种形态。

---

## 跨文档交叉引用

- 完整配置项参考（21 任务节点 properties + 5 未实现）：`../spec/02-flow-definition.md` + `../ToT/guides/02-flow-definition.md` §4
- 状态机全集（InstanceState 7 + TaskState 6 + 迁移图）：`../spec/03-state-machine.md`
- 7 个内置 handler FQCN + 解析优先级：`../ToT/guides/07-assignment-handlers.md`
- 持久化 ARCHIVE/SYNC 双模式 + 字段权限：`../spec/09-persist.md` + `../ToT/guides/08-persist.md`
- 拦截器 / 事件 6 类型 + 注册方式：`../concepts/04-extensions.md` + `../ToT/guides/04-extensions.md`
- submitType 9 枚举 + 引擎方法路由：`../spec/04-engine-ops.md` + `../ToT/guides/05-scenarios.md`
- 字典差异警示（缺 `7 TRANSFER` / `20` 与 `2` 重复）：`ToT/docs/README.md` §3-1