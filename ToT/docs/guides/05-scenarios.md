# 用户指南 05 · 业务闭环场景

> **来源**：https://jeeflow-doc.mldong.com/guides/05-scenarios
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的端到端业务场景参考。每个场景包含：业务背景 → 流程定义要点 → API 调用序列。
> **裁剪记录**：场景一/二/三/四保留 + 加本仓示例路径与语义注解；场景五保留 + 重写为本仓实现状态；场景选择速查表保留 + 增本仓 flows/ 路径列。

---

## 场景一：请假审批（标准闭环）

### 业务规则

- 员工发起请假 → 组长审批 → 经理审批
- 组长/经理不同意 → **退回发起人**，可修改重提
- 重新提交后重新走审批

### 流程定义要点

```
start → apply(applicant) → 组长审批(leader) → 经理审批(manager) → end
```

> **本仓对应示例**：`../flows/09-with-reject.json`（含驳回流程）+ `../flows/02-multi-task.json`（多级审批）。

### 调用序列

```
① 发起（自动完成申请节点）
   POST /wf/processInstance/startAndExecute
   { "processDefineId": <本轮 deploy 返回的 processDefineId>, "operator": "user1" }

② 组长审批通过
   POST /wf/processTask/execute
   { "processTaskId": <taskId>, "operator": "leader", "submitType": 1 }

③ 经理不同意 → 退回发起人（submitType=6，实例保持进行中）
   POST /wf/processTask/execute
   { "processTaskId": <taskId>, "operator": "manager", "submitType": 6 }
   # 效果：第一个任务节点重执行（参与者=发起人），user1 收到新待办"发起申请"

④ 发起人重新提交
   POST /wf/processTask/execute
   { "processTaskId": <taskId>, "operator": "user1", "submitType": 0 }

⑤ 组长/经理依次审批 → 流程完成
```

> ⚠️ **本仓 submitType 三选一硬约束**（FIX-T114 §118）：
> | submitType | 语义 | 实例状态 | 备注 |
> |---|---|---|---|
> | `0` | 同意 / 通过 | 推进至下游节点 | 默认行为 |
> | `2` | 拒绝 / 驳回 | 终止 → state=45 REJECT | 走 facade 不走 decision，实例立即结束 |
> | `6` | 退回发起人 | 保持 state=10 DOING | 强制指派给 `inst.operator`，实例继续 |
>
> - 上游示例 processDefineId=2 / 100 / 101 / 102 为占位 id，**本仓禁止硬编码**——必须从 `processDesign/deploy` 响应取 `data.processDefineId`、从 `processTask/todoList` 响应取 `data.rows[].id`。
> - `submitType=2/3/4` 是 ROLLBACK 变种（FIX-T36 §52），`submitType=3/4` 显式传 `taskName`/`targetTaskName` 可指定回退节点；不传时按 ROLLBACK 默认行为覆写 `assignee`。
> - 详细 facade 行为见 `../docs/actions.md`。

### 审批记录（完整闭环）

```
发起申请   user1    已完成
组长审批   leader   已完成
经理审批   manager  已完成（退回操作）
发起申请   user1    已完成（重新提交）
组长审批   leader   已完成
经理审批   manager  已完成
```

> 退回发起人（submitType=6）不改变实例状态——保持进行中直到最终完成；若用 `submitType=2`（拒绝）则实例直接进入 45 已拒绝。行为表见[设计原理 06 §3-4](./../concepts/06-contracts)。

---

## 场景二：报销审批（决策分支）

### 业务规则

- 填写报销单 → 金额 ≤1000 总监审批即可；金额 >1000 需经理审批

### 流程定义要点

```
start → apply(applicant) → 填写报销单(leader)
      → decision1 ──amount > 1000──▶ 经理审批(manager) ──▶ end
                  └─amount <= 1000─▶ 总监审批(director) ──▶ end
```

> **本仓对应示例**：`../flows/03-decision-expr.json`（决策表达式流程）+ `../flows/15-decision-amount.json`（金额分支）。

决策边：

```json
{ "id":"e3", "sourceNodeId":"decision1", "targetNodeId":"task2",
  "properties":{"expr":"amount > 1000"}, "text":{"value":"金额>1000"} }
```

> **本仓 expr 写法**（FIX-T37 §20）：上游示例 `amount > 1000`（无前缀）合法，但本仓推荐**显式 OGNL 风格 `#var` 前缀**便于复杂条件扩展：
> - 简单：`amount > 1000` / `#amount > 1000`
> - 复合：`#amount >= 5000 && #urgent == 1`（FIX-T37 v1.9.0+ 支持 `&&`/`||`/`!`）
> - 业务变量：`#f_amount`（带 `f_` 前缀的持久化实例变量）
>
> ⚠️ **决策节点默认边兜底语义**（FIX-T112 §113）：**所有 expr 评估失败**时引擎兜底走**第一条**出边（可能创建孤儿 DOING task）。**必须**加显式默认边 `properties.expr=""` —— 上游示例的 `amount <= 1000` 即为该默认值。

### 调用序列

```
① 发起时带金额变量
   POST /wf/processInstance/startAndExecute
   { "processDefineId": <id>, "operator": "user1", "amount": 5000 }

② 填写报销单 → 自动路由到经理审批（amount=5000 > 1000）
   { "processTaskId": <id>, "operator": "leader", "submitType": 1 }
   # 经理收到待办
```

> **本仓变量作用域铁律**（FB-0011 / FIX-DOC-4 §115）：`amount` 在决策表达式里**只能读 `f_amount`（持久化实例变量）或 `tf_amount`（任务流变量）**。`startAndExecute` 时直接传 `amount` 会被引擎解析为**顶级变量**写入 `vars_`，决策 expr 能读到；但若用 `tf_*` 仅当前 task + 后置拦截器可见，**decision expr 读不到**——会触发孤儿 DOING 现象。

---

## 场景三：并行会签

### 业务规则

- 三个部门主管**同时**会签，全部同意才通过

### 流程定义要点

```json
{
  "id": "countersign",
  "type": "snaker:task",
  "properties": {
    "assignee": "userA,userB,userC",
    "performType": 1,
    "countersignType": "PARALLEL"
  }
}
```

> **本仓对应示例**：`../flows/05-countersign-parallel.json`（并行会签）+ `../flows/06-countersign-sequential.json`（串行会签）+ `../flows/07-countersign-ratio.json`（比例会签，RATIO 模式）+ `../flows/13-countersign-one-vote-veto.json`（一票否决）。

### 调用序列

```
① 启动 → 自动完成 apply → 同时生成 3 个会签任务（同一 taskName）

② userA / userB / userC 各自处理（顺序无关）
   { "processTaskId": <id>, "operator": "userA", "submitType": 1 }
   # 完成 1 个后：还有 2 个进行中 → 等待

③ 全部完成 → 流程推进到 end → 完成
```

### 串行会签（SEQUENTIAL）

同样配置但 `countersignType: "SEQUENTIAL"`：只生成 userA 的任务，A 完成 → 生成 userB 的任务 → B 完成 → 推进。

> **本仓会签四模式实际行为**（与上游文字略不同，详见 `../ToT/guides/02-flow-definition.md` §2.5）：
>
> | 模式 | 本仓实现 | 关键差异 |
> |---|---|---|
> | `PARALLEL`（默认）| `performType=1 + countersignType=PARALLEL`，**无** `countersignCompletionCondition` | 全部 `submitType=0` 通过才流转；剩余 taskState 仍 10，**不自动废弃** |
> | `SEQUENTIAL`（按顺序）| `performType=1 + countersignType=SEQUENTIAL` | 仅最后一个通过即流转；上游示例的「只生成 userA 任务 → A 完成 → 生成 userB」是真实行为 |
> | `RATIO`（比例完成）| `performType=1 + countersignType=PARALLEL` + `countersignCompletionCondition` 表达式 | OGNL 表达式，引擎注入 `nrOfCompletedInstances` / `nrOfInstances` 变量；命中即流转，余者 ABANDON |
> | 一票否决 | `performType=1 + countersignType=PARALLEL` + `countersignCompletionCondition="ONE_VOTE_VETO"` | 任一 reject 立即流转 state=45 + 余者 ABANDON |
>
> ⚠️ **RATIO 与 ONE_VOTE_VETO 互斥**（FB-0008 §113）：字段值 = **表达式** → 比例模式（放弃一票否决）；字段值 = **字符串 "ONE_VOTE_VETO"** → 一票否决（放弃比例）。两种语义不可复合。
>
> ⚠️ **submitType=20 拓扑约束**（FB-0012 §116）：会签 task → end **直连**时 submitType=20（一票否决 REJECT）才生效；若会签后接 decision 节点，decision 会截断 cs_veto 路径，一票否决失效。详见 `../docs/flow.md §3.3` + `../docs/known-issues.md §116`。

---

## 场景四：并行分支合并（fork/join）

### 业务规则

- 发起后**财务审核**与**法务审核**并行，都通过才进入终审

### 流程定义要点

```
start → apply → fork1 ─┬→ 财务审核(checker) ─┐
                       └→ 法务审核(reviewer) ─┴→ join1 → 老板终审(boss) → end
```

> **本仓对应示例**：`../flows/04-fork-join.json`（并行分支合并）+ `../flows/10-mixed-mode.json`（混合模式：fork+join+decision+会签组合）。

### 调用序列

```
① 启动 → 自动完成 apply → fork 生成 2 个并行任务

② checker 完成（join 等待中）
③ reviewer 完成（join 放行 → 生成老板终审）

④ boss 完成 → end
```

> **本仓 join 节点语义**（FIX-T35 §30）：
> - `snaker:join` 是**显式汇合点**，无活跃任务时放行至下游；
> - 设计师**推荐**加 join 节点（即便 FIX-T35 后已支持隐式 join），原因：
>   1. 流程图可视化清晰（汇合点明确）
>   2. 防止 task 节点多条无条件出边导致 instance.state 提前 DONE 但下游 task 卡 DOING（F-110）
>   3. verify W012 警告检测
> - join 节点的 `properties` 通常为空 `{}`，仅含 `width/height` 设计器尺寸字段。

---

## 场景五：抄送

> **引擎 SPI 预留 `createCcInstance / updateCcStatus`，demo 未内置接口。接入方式**：

```
① 流程完成/任务完成事件中，业务方调用 createCcInstance(instanceId, creator, actorIds...)
② 被抄送人在"我的抄送"列表查看（业务层查询 wf_process_cc_instance）
③ 已读回执：updateCcStatus(instanceId, actorId)
```

> ⚠️ **本仓当前实现状态**（重写）：
>
> | 能力 | 本仓现状 | 设计者独立可做？ |
> |---|---|---|
> | CC 字段存储 | `engine.py` 任务表已有 `cc_actor_id` 字段 | ✅ 数据落库 |
> | CC_CREATE 事件 | `extensions.py:15 EventType.CC_CREATE` 已注册 | ✅ 业务方可监听 |
> | `createCcInstance` 公开 facade | ❌ **未提供** | ❌ |
> | `updateCcStatus` 公开 facade | ❌ **未提供** | ❌ |
> | 「我的抄送」列表查询 API | ❌ **未提供**（业务层自行实现）| ❌ |
>
> **本仓抄送能力的实际工作流**：
>
> ```json
> // 节点 properties 配置抄送人（不是 actor，是旁观者）
> {
>   "id": "task1",
>   "type": "snaker:task",
>   "properties": {
>     "assignee": "leader",
>     "ccActorId": "boss,director"   // ← 节点执行时自动写 cc_actor_id 字段
>   }
> }
> ```
>
> 业务方需**自行实现**：
> 1. 监听 `CC_CREATE` 事件 → 写入业务库 `wf_process_cc_instance`
> 2. 提供「我的抄送」查询 API
> 3. 提供已读回执 update API
>
> 抄送相关的本仓 facade 端点（`createCcInstance` / `updateCcStatus`）**规划中**，详见 `../docs/api.md` §1 + 待补 Issue。

---

## 场景选择速查

> **本表保留上游 7 行分类 + 增列本仓 flows/ 路径**。

| 想演示 | 用哪个流程（demo 预置）| 本仓对应路径 |
|---|---|---|
| 单级审批 | 简单审批流程 | `../flows/01-simple.json` |
| 多级审批 + 驳回退回 | 多级审批流程 / 含驳回流程 | `../flows/02-multi-task.json` / `../flows/09-with-reject.json` |
| 金额决策路由 | 决策表达式流程 | `../flows/03-decision-expr.json` / `../flows/15-decision-amount.json` |
| 并行分支 | 并行分支合并流程 | `../flows/04-fork-join.json` |
| 并行会签 | 并行会签流程 | `../flows/05-countersign-parallel.json` |
| 串行会签 | 串行会签流程 | `../flows/06-countersign-sequential.json` |
| 全组合 | 混合模式流程（fork+join+decision）| `../flows/10-mixed-mode.json` |

> **本仓额外提供 5 类进阶示例**（上游未涵盖）：
>
> | 模式 | 本仓路径 |
> |---|---|
> | 比例会签（OGNL 表达式）| `../flows/07-countersign-ratio.json` |
> | 串行会签-审批（SEQUENTIAL 变种）| `../flows/08-countersign-sequential-approve.json` |
> | 自定义节点（customClass 处理器）| `../flows/08-custom-node.json` |
> | assignee 变量解析（`applicant`/`@role`/`tf_*`）| `../flows/11-assignee-vars.json` |
> | 内置 assignmentHandler 全部列示 | `../flows/11-assignment-handler.json` |
> | 候选人分页（candidatePage）| `../flows/12-candidate-page.json` |
> | 一票否决会签 | `../flows/13-countersign-one-vote-veto.json` |
> | decision + submitType 复合 | `../flows/14-decision-submitType.json` |
> | 委派测试 | `../flows/16-delegate-test.json` |
> | 挂起/恢复测试 | `../flows/17-suspend-resume-test.json` |