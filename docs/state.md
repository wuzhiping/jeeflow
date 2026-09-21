# 实例状态与 SubmitType 对照

本文档集中登记引擎运行时涉及的**状态枚举**与**提交类型枚举**，以及 `processInstance/detail` 接口返回字段与 `InstanceState` 枚举之间的双义关系，避免客户端取值混用。

---

## 1. InstanceState 枚举（来源：jeeflow/model.py）

`InstanceState` 是实例的**生命周期阶段**字段，独立持久化于 `wf_process_instance.state`。该字段取值如下：

| 取值 | 名称 | 含义 |
| --- | --- | --- |
| 10 | `DOING` | 进行中（含被回退重新激活的节点） |
| 20 | `DONE` | 已完成（按 plan 顺序走完到 end） |
| 30 | `WITHDRAW` | 发起人撤回 / 流程回滚 (§7.3.1 FIX-T107: state=WITHDRAW, 废弃所有 DOING 任务) |
| 40 | `INTERRUPT` | 中断（管理员手动干预） |
| 45 | `REJECT` | 驳回（决策路由匹配 submitType==2 等拒绝分支） |
| 50 | `PENDING` | 待激活（如并行汇聚前的等待状态） |
| 99 | `ABANDON` | 废弃（流程作废） |

> ⚠️ 该枚举是 `model.InstanceState` 枚举类，**与 `processInstance/detail` 接口返回的 `state` 字段不是同一字段**。详见 §3。

---

## 2. SubmitType 枚举（来源：jeeflow/model.py）

提交时由前端传入的 `submitType` 字段，影响引擎路由：

| 取值 | 名称 | 行为 |
| --- | --- | --- |
| 0 | `APPLY` | 发起申请（仅 `startAndExecute` 内部自动注入；客户端直接传 0 会被 facade 强制改为 1） |
| 1 | `AGREE` | 同意 |
| 2 | `REJECT` | 驳回（**实例级终止 → state=45**，引擎路径 `execute_and_jump_to_end`） |
| 3 | `RETURN` / `ROLLBACK` | 回退（重新激活上一节点） |
| 4 | `JUMP` | 跳转到指定 taskName |
| 5 | `RE_APPLY` / `FORWARD` | 转交（移交他人） |
| 6 | `ROLLBACK_TO_OPERATOR` / `DELEGATE` | 委派回发起人 |
| 20 | `COUNTERSIGN_DISAGREE` | **会签软拒绝**（不阻断流程，仅记录 countersignDisagreeFlag=1，正常流转到下一节点） |

> ⚠️ **实测（2026-09-17 复测 09-with-reject）**：
> - `submitType=2 (REJECT)` 走 `engine.execute_and_jump_to_end`，**实例级终止**，state=45
> - `submitType=20 (COUNTERSIGN_DISAGREE)` 走 `engine.execute_process_task` 普通路径，**软拒绝**，**不阻断流程**，会创建下一节点 task
> - 两者语义完全不同：REJECT=终止，COUNTERSIGN_DISAGREE=软拒绝继续流转

---

## 3. 状态码双义（重要）

> ✅ **澄清（2026-09-17 实测）**：`processInstance/detail` 接口返回的 `state` 字段**就是 `InstanceState` 枚举值**（10/20/30/40/45/50/99），**不是另一套 `finish_state=7`**。`finish_state` 字段在响应中存在但**整个生命周期恒为 `null`**，不是"已完成"标志。

**实测对照表**（`01-simple.json` 2026-09-17 08:55 验证）：

| 客户端字段 | 取值 | 含义 | 对应 `InstanceState` |
| --- | --- | --- | --- |
| `detail.state` | `10` | 进行中（含回退重新激活） | `DOING=10` |
| `detail.state` | `20` | 已完成（按 plan 走完到 end） | `DONE=20` |
| `detail.state` | `45` | 驳回 | `REJECT=45` |
| `detail.finish_state` | `null` | 永远为 null（**遗留字段，无意义**） | — |

### 客户端取值规则

```text
取 detail.state 作为生命周期阶段判断：
  state==10 → 进行中
  state==20 → 已完成（DONE）
  state==45 → 驳回（REJECT）
  state==30 → 撤回
  ...
不要查 detail.finish_state（永远是 null）。
```

> 💡 完成定义：`state == 20`。详见 `./docs/known-issues.md` §6（已澄清）。

---

## 4. SubmitType 路由矩阵（实测）

实测依据：`./tdd/test_demo-single-approval-reject_20260917075915.md` 5/5 PASS（实际跑了 submitType 0/1/2/3/5/20 六个 case，全部命中预期）。

| submitType | 实际终点 | detail.state | InstanceState | 路由说明 |
| --- | --- | --- | --- | --- |
| 0 | end | 20 | 20 (DONE) | 仅 `startAndExecute` 内部注入，APPLY 自动通过 |
| 1 | end | 20 | 20 (DONE) | 审批人同意 |
| 5 | end | 20 | 20 (DONE) | 转交他人（提交者视角等价同意） |
| 20 | end | 20 | 20 (DONE) | 提交（与 AGREE 等价） |
| 2 | 驳回终点 | 45 | 45 (REJECT) | 审批人拒绝 |
| 3 | apply 重激活 | 10 | 10 (DOING) | 回退到 apply |
| 6 | apply 重激活 | 10 | 10 (DOING) | 委派到 apply（少见用法） |

完整矩阵见 `./docs/flow.md` §7a。

## 5. TaskState 枚举（实测补）

`processInstance/detail.tasks[].taskState` 字段是 `TaskState` 枚举：

| 取值 | 名称 | 含义 |
| --- | --- | --- |
| 10 | `DOING` | 任务待执行 |
| 20 | `DONE` | 任务已完成（submitType=0/1/5/20 等"通过"类） |
| 99 | `ABANDON` | 任务废弃（如比例会签完成条件满足后，未完成的会签子任务被设为 ABANDON） |

> 💡 与 `InstanceState` 编号体系**部分重叠**（DOING=10, DONE=20），但语义不同：前者是任务粒度，后者是实例粒度。
> 
> ⚠️ **2026-09-17 实测补（07-countersign-ratio）**：比例会签满足 `countersignCompletionCondition` 后，未完成的子任务 `taskState=99 ABANDON`。`approvalRecord` 中这些 task 仍记录但 `operator` 为空字符串。详见 `./tdd/test_07-countersign-ratio_20260917120200.md`。

### 5.1 TaskState.ABANDON 字段语义（FIX-T111 §112 2026-09-21 实测补）

| 字段 | DONE (state=20) | ABANDON (state=99) |
|---|---|---|
| `finishTime` | ✅ 有值（执行时间） | ❌ 永久 NULL（ABANDON 不算 finish） |
| `updateTime` | 执行完成时刻 | ABANDON 触发时刻 |
| `updateUser` | 实际执行人 (operator) | **触发废弃的人**（FIX-T111 之前误为 createUser=发起人） |
| `createUser` | task 创建时的人 | task 创建时的人（不变） |
| `operator` | 执行人 | 空字符串（未执行） |
| `actorIds` | 执行人的 actor | 原应执行的人列表（未投的人） |
| 是否进 `activeTaskList` | ❌ 不进（DONE） | ❌ 不进（ABANDON 已结束） |
| 是否进 `todoList` | ❌ 不进 | ❌ 不进（不作为待办） |
| 是否进 `approvalRecord` | ✅ 进 | ✅ 进（审计可见，operator="" + updateUser=触发者） |
| 是否进 `bizData` | ✅ 进 | ✅ 进（actorIds 仍可见，原应执行者） |

### 5.2 ABANDON 触发场景（FIX-T111 §112）

| 场景 | updateUser 期望值（修复后） |
|---|---|
| 比例/PARALLEL 会签完成条件命中 | 命中条件的最后提交人 (e.g. 2/3 → 第 2 个同意的人) |
| ONE_VOTE_VETO REJECT (submitType=20) | 否决人 (engine.py:202 显式赋值,一直正确) |
| 流程撤回 (withdraw) | 撤回人 (facade.py:586 已修复) |
| `start_process_instance_by_id` 异常回滚 | 发起人 (engine.py:123) |

> **修复背景**：FIX-T111 之前，所有比例/PARALLEL 废弃路径的 `updateUser` 都隐式沿用 `createUser`（=发起人 `user1`），导致审计追溯错乱——看上去是「发起人废弃了未投的会签子任务」，实际是「另一个会签人的提交触发了完成条件」。详见 `./docs/known-issues.md §112` + `./bdd/bdd-1511-1516-fix-t111-taskstate-abandon_20260921.sh`。

### 5.3 `abandon()` API 约定

```python
# vendor/jeeflow/model.py
def abandon(self, now, abandoned_by: str = "") -> None:
    self.taskState = TaskState.ABANDONED
    self.updateTime = now
    if abandoned_by:
        self.updateUser = abandoned_by
```

- `abandoned_by` **非空时**：写 `updateUser = abandoned_by`（审计追溯）
- `abandoned_by` **为空时**：保持 backward compat（不覆盖 `updateUser`）
- **调用约定**：所有 ABANDON 路径必须显式传 `abandoned_by`（engine.py:187 / engine.py:202 / facade.py:586 / main_common.py:248）

---

## 6. 字段读取顺序

`/wf/processInstance/detail` 响应**直接是** `data` 对象，`data.state` 即 `InstanceState` 枚举值：

```json
{
  "code": 0,
  "data": {
    "id": "<processInstanceId>",
    "state": 20,            ← InstanceState.DONE
    "tasks": [
      {"id":"...", "taskName":"apply", "taskState":20, "operator":"applicant", ...},
      ...
    ],
    "finish_state": null,   ← 永远为 null，忽略
    ...
  }
}
```

`/wf/processDesign/detail` 返回 `id` 作为 `processDefineId`；`/wf/processInstance/startAndExecute` 响应返回 `processInstanceId` 与 `processTaskId`（**field name 不可缩写**）。

`/wf/processInstance/highLight` 响应结构：

```json
{
  "activeNodeNames": [],        ← [] = 已结束
  "historyNodeNames": [...],    ← 已走过节点（含 end）
  "historyEdgeNames": [...],    ← 已走过边
  "nodeProgress": {             ← 节点参与人进度
    "<nodeName>": {
      "members": [{"id":"userId","name":"displayName","done":true|false}]
    }
  }
}
```

> 字段命名约定汇总见 `./docs/api.md` §4。
