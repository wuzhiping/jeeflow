# 规范 03 · 状态机

> **来源**：https://jeeflow-doc.mldong.com/spec/03-state-machine
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**流程实例 / 任务状态码权威参考**——理解状态转换是设计 submitType 路由、调试卡死实例的前提。
>
> **本仓实现版本**：`vendor/jeeflow/model.py:46 InstanceState` IntEnum（7 值）+ `:55 TaskState` IntEnum（6 值）。**命名差异**说明：
> - 终态：上游 `FINISHED` → 本仓 `InstanceState.DONE` / `TaskState.DONE`（**两者**均无 ED 后缀）
> - 废弃态：**不一致**——上游统一 `ABANDON`，本仓 `InstanceState.ABANDON`（无 ED）/ `TaskState.ABANDONED`（**带 ED 后缀**）
> - 数据库列 `state` 数值与上游一致（20 / 99），仅 Python 枚举属性名部分差异；跨语言契约以**数值**为准。
>
> **裁剪记录**：流程实例状态表 + 状态图 + 任务状态表 + 状态图 + 转换规则全部保留 + 加本仓实现验证。

---

## 流程实例状态（`wf_process_instance.state`）

> **本仓实现**：`vendor/jeeflow/model.py:46 InstanceState(IntEnum)`，7 状态码与上游完全一致。

| code | 名称（上游）| 名称（**本仓 enum**）| 说明 |
|---|---|---|---|
| 10 | 进行中 (DOING) | `InstanceState.DOING` | 初始状态 |
| 20 | 已完成 (FINISHED) | `InstanceState.DONE` | 正常走到 end |
| 30 | 已撤回 (WITHDRAW) | `InstanceState.WITHDRAW` | 发起人撤回 |
| 40 | 强行终止 (INTERRUPT) | `InstanceState.INTERRUPT` | 管理员终止 |
| 45 | 已拒绝 (REJECT) | `InstanceState.REJECT` | 驳回/拒绝 |
| 50 | 挂起 (PENDING) | `InstanceState.PENDING` | 暂停 |
| 99 | 已废弃 (ABANDON) | `InstanceState.ABANDON` | 废弃 |

> **命名差异**：上游统一用 `FINISHED` / `ABANDON`，本仓 Python 枚举为 `DONE` / `ABANDON`（**无** `ED` 后缀）—— **数据库 `state` 列数值（20/99）不变**，仅 Python 属性名拼写不同。跨语言契约以数值为准。

```
            start
              │
              ▼
         ┌───────┐    reject    ┌────────┐
         │  10   │─────────────▶│   45   │
         │ 进行中 │              │ 已拒绝  │
         └───┬───┘              └────────┘
             │ complete
             ▼
         ┌───────┐
         │  20   │
         │ 已完成 │
         └───────┘
```

> **状态图说明**（精简版）：
> - `10 DOING` 启动后默认状态
> - `10 → 45 REJECT`：会签 / decision / submitType=2 任一 reject 路径
> - `10 → 20 DONE`：正常走到 end（详见 `../ToT/guides/05-scenarios.md` §场景一）
> - `10 → 30 WITHDRAW`：`processInstance/withdraw` 端点（发起人撤回）
> - `10 → 40 INTERRUPT`：`processInstance/interrupt` 端点（管理员强制终止）
> - `10 → 50 PENDING`：挂起（FIX-T70，`processInstance/suspend` 端点）
> - `50 → 10 DOING`：`processInstance/resume` 恢复

---

## 任务状态（`wf_process_task.task_state`）

> **本仓实现**：`vendor/jeeflow/model.py:55 TaskState(IntEnum)`，6 状态码与上游完全一致。**注意**：任务级**无** `45 REJECT`（REJECT 是流程实例级终结状态）。

| code | 名称（上游）| 名称（**本仓 enum**）| 说明 |
|---|---|---|---|
| 10 | 进行中 (DOING) | `TaskState.DOING` | 初始状态 |
| 20 | 已完成 (FINISHED) | `TaskState.DONE` | 完成 |
| 30 | 已撤回 (WITHDRAW) | `TaskState.WITHDRAW` | 随实例撤回 |
| 40 | 强行终止 (INTERRUPT) | `TaskState.INTERRUPT` | 随实例终止 |
| 50 | 挂起 (PENDING) | `TaskState.PENDING` | 随实例挂起 |
| 99 | 已废弃 (ABANDON) | `TaskState.ABANDONED` | 废弃（驳回/跳转时清理其他进行中任务）|

> **命名差异**：上游 `ABANDON` 对应本仓 `ABANDONED`（带 `ED` 后缀）—— **数据库列数值（99）不变**。代码 `task.state == 99` 等价 `task.taskState == TaskState.ABANDONED`。

```
            create
              │
              ▼
         ┌───────┐   complete   ┌────────┐
         │  10   │─────────────▶│   20   │
         │ 进行中 │              │ 已完成  │
         └───┬───┘              └────────┘
             │ abandon
             ▼
         ┌───────┐
         │  99   │
         │ 已废弃 │
         └───────┘
```

> **状态转换触发点**（`vendor/jeeflow/model.py:182` 等）：
> - `10 → 20 DONE`：`processTask/execute submitType=0`（同意）/ `submitType=1`（推进）
> - `10 → 99 ABANDONED`：会签比例 / ONE_VOTE_VETO / ROLLBACK 时清理其他 DOING 任务（FIX-T111 §112）
> - `10 → 30 WITHDRAW`：随实例撤回
> - `10 → 40 INTERRUPT`：随实例强制终止
> - `10 → 50 PENDING`：随实例挂起

---

## 状态转换规则

> **本仓实现**（`vendor/jeeflow/model.py:112 ProcessInstance.withdraw` + `TaskState` 转换）：
>
> ```python
> # 流程实例撤回
> def withdraw(self):
>     self.state = InstanceState.WITHDRAW       # 实例级 30
>     # 级联 DOING 任务 → 30 WITHDRAW（已完成 20 / 已终止 40 / 已废弃 99 等**不**被改写）
>     # 走 update_instance 同一连接持久化（v1.0.1 契约）
>
> # 任务废弃（FIX-T111 §112）
> def abandon(self, abandoned_by: str):
>     self.taskState = TaskState.ABANDONED      # 任务级 99
>     self.updateUser = abandoned_by           # 触发废弃的人
> ```
>
> **级联落库契约**（v1.0.1，`vendor/jeeflow/repository/ext.py`）：撤回/挂起/终止等聚合命令改完任务状态后，**随 `update_instance` 同一连接持久化**——避免先更新任务再更新实例时中间态被读出。

**关键转换规则**：

- **任务状态转换是聚合根职责**（`ProcessTask.finish/abandon`），引擎只做编排——设计论证见 [设计原理 02 · 领域模型](https://jeeflow-doc.mldong.com/concepts/02-domain-model)
- **任务状态随实例级命令级联落库**：撤回/挂起/终止等聚合命令改完任务状态后，随 `update_instance` 同一连接持久化（v1.0.1 契约，见 [规范 05 · SPI](./05-spi)）

> **本仓设计者实操**：
> - 调试「实例卡 state=10」：查 `processTask/todoList` 看是否有任务的 `taskActorIdList` 为空 —— 这是任务创建但未分配参与者的常见原因
> - 调试「state=50」：`processInstance/resume` 端点（FIX-T70）
> - 调试「state=45」：追溯 `approvalRecord` 最后一条任务的 submitType（应为 2 / 20）
> - 调试「taskState=99 ABANDONED」：查看 `update_user` 字段（FIX-T111 §112，触发废弃的人；缺省 fallback `create_user`）