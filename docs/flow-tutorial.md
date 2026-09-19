
## 9. 教程: 10 分钟上手 (BDD #1211 FIX-T89 §4.3.5)

私用项目 API 视角, 不涉及 UI 设计.

### 9.1 最简单的流程 (3 节点)

最简单的流程: 申请 → 结束.

**步骤 A**: 写流程定义文件 (`/tmp/my_flow.json`):
```json
{
  "name": "my-first-flow",
  "displayName": "我的第一个流程",
  "type": "approval",
  "nodes": [
    {"id": "start", "type": "snaker:start", "properties": {}},
    {"id": "apply", "type": "snaker:task", "properties": {"assignee": "user1"}},
    {"id": "end", "type": "snaker:end", "properties": {}}
  ],
  "edges": [
    {"sourceNodeId": "start", "targetNodeId": "apply"},
    {"sourceNodeId": "apply", "targetNodeId": "end"}
  ]
}
```

**步骤 B**: 部署 (save + deploy):
```bash
DESIGN_ID=$(curl -s -X POST http://localhost:8101/wf/processDesign/save \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat /tmp/my_flow.json)" '{name:"my-first-flow",displayName:"我的",content:$c}')" \
  | jq -r '.data.id')

DEF_ID=$(curl -s -X POST http://localhost:8101/wf/processDesign/deploy \
  -H "Content-Type: application/json" -d "{\"id\": $DESIGN_ID}" \
  | jq -r '.data.processDefineId')
```

**步骤 C**: 启动实例 (startAndExecute):
```bash
curl -s -X POST http://localhost:8101/wf/processInstance/startAndExecute \
  -H "Content-Type: application/json" \
  -d "{\"processDefineId\": $DEF_ID, \"operator\": \"user1\"}"
# → {"code":0,"data":{"processInstanceId":"..."}}
```

### 9.2 多人审批流程

三级审批: user1 → leader → manager → end.

节点定义:
```json
{
  "name": "multi-approve",
  "nodes": [
    {"id": "start", "type": "snaker:start"},
    {"id": "apply", "type": "snaker:task", "properties": {"assignee": "user1"}},
    {"id": "leader_review", "type": "snaker:task", "properties": {"assignee": "leader"}},
    {"id": "manager_review", "type": "snaker:task", "properties": {"assignee": "manager"}},
    {"id": "end", "type": "snaker:end"}
  ],
  "edges": [
    {"id": "e0", "sourceNodeId": "start", "targetNodeId": "apply"},
    {"id": "e1", "sourceNodeId": "apply", "targetNodeId": "leader_review"},
    {"id": "e2", "sourceNodeId": "leader_review", "targetNodeId": "manager_review"},
    {"id": "e3", "sourceNodeId": "manager_review", "targetNodeId": "end"}
  ]
}
```

执行链: user1 申请 → leader 查 todoList → leader.execute → manager 查 todoList → manager.execute → end.

### 9.3 决策分支流程

按金额分流: amount < 10000 直接结束, >= 10000 进 CEO 审批.

```json
{
  "name": "amount-decision",
  "nodes": [
    {"id": "start", "type": "snaker:start"},
    {"id": "apply", "type": "snaker:task", "properties": {"assignee": "user1"}},
    {"id": "amount_check", "type": "snaker:decision"},
    {"id": "big_amount", "type": "snaker:task", "properties": {"assignee": "ceo"}},
    {"id": "end", "type": "snaker:end"}
  ],
  "edges": [
    {"id": "e0", "sourceNodeId": "start", "targetNodeId": "apply"},
    {"id": "e1", "sourceNodeId": "apply", "targetNodeId": "amount_check"},
    {"id": "e_high", "sourceNodeId": "amount_check", "targetNodeId": "big_amount",
     "properties": {"expr": "#amount>=10000"}},
    {"id": "e_low", "sourceNodeId": "amount_check", "targetNodeId": "end"}
  ]
}
```

启动时传 `amount` 变量:
```bash
# amount=5000 → 跳过 big_amount, 走 end (state=20 DONE)
# amount=20000 → 走 big_amount, 等 ceo 审批 (state=10 DOING)
curl -X POST /wf/processInstance/startAndExecute \
  -d '{"processDefineId": ..., "operator": "user1", "amount": 20000}'
```

### 9.4 并行审批 + 汇合

申请人 → [财务 + 技术] 并行 → 总经理 (汇合).

```json
{
  "name": "parallel-review",
  "nodes": [
    {"id": "start", "type": "snaker:start"},
    {"id": "apply", "type": "snaker:task", "properties": {"assignee": "user1"}},
    {"id": "fork1", "type": "snaker:fork"},
    {"id": "finance", "type": "snaker:task", "properties": {"assignee": "finance"}},
    {"id": "tech", "type": "snaker:task", "properties": {"assignee": "tech"}},
    {"id": "join1", "type": "snaker:join"},
    {"id": "boss", "type": "snaker:task", "properties": {"assignee": "boss"}},
    {"id": "end", "type": "snaker:end"}
  ],
  "edges": [
    {"id": "e0", "sourceNodeId": "start", "targetNodeId": "apply"},
    {"id": "e1", "sourceNodeId": "apply", "targetNodeId": "fork1"},
    {"id": "e_f", "sourceNodeId": "fork1", "targetNodeId": "finance"},
    {"id": "e_t", "sourceNodeId": "fork1", "targetNodeId": "tech"},
    {"id": "e_jf", "sourceNodeId": "finance", "targetNodeId": "join1"},
    {"id": "e_jt", "sourceNodeId": "tech", "targetNodeId": "join1"},
    {"id": "e_b", "sourceNodeId": "join1", "targetNodeId": "boss"},
    {"id": "e_e", "sourceNodeId": "boss", "targetNodeId": "end"}
  ]
}
```

引擎行为: fork1 同时创建 finance 和 tech 两个 task. 两个都完成后 join1 放行, 创建 boss task.

### 9.5 会签 (并签/串签)

**并签**: 3 人同时审, 全员通过才流转:
```json
{
  "id": "review",
  "type": "snaker:task",
  "properties": {
    "performType": 1,
    "countersignType": "PARALLEL",
    "assignee": "user2,user3,user4"
  }
}
```

行为: 3 人同时收到 task. user2.execute → 不流转, taskState 仍 10. user3.execute → 不流转. user4.execute → 全部完成才流转.

**串签**: 3 人按顺序审, 1 人通过即流转:
```json
{
  "id": "review",
  "type": "snaker:task",
  "properties": {
    "performType": 1,
    "countersignType": "SEQUENTIAL",
    "assignee": "user2,user3,user4"
  }
}
```

行为: 先给 user2, 通过后给 user3, 再 user4.

**比例会签**: K/N 通过即流转:
```json
{
  "id": "review",
  "type": "snaker:task",
  "properties": {
    "performType": 1,
    "countersignType": "PARALLEL",
    "assignee": "u1,u2,u3,u4",
    "countersignCompletionCondition": "#nrOfCompletedInstances>=2"
  }
}
```

### 9.6 子流程 (callActivity)

主流程触发子流程 (FIX-T73 §3.1.2).

**前置**: 子流程必须先 deploy.
```json
{
  "name": "sub-flow",
  "nodes": [
    {"id": "start", "type": "snaker:start"},
    {"id": "sub_task", "type": "snaker:task", "properties": {"assignee": "user2"}},
    {"id": "end", "type": "snaker:end"}
  ],
  "edges": [...]
}
```

主流程:
```json
{
  "name": "master-flow",
  "nodes": [
    {"id": "start", "type": "snaker:start"},
    {"id": "apply", "type": "snaker:task", "properties": {"assignee": "user1"}},
    {"id": "sub_call", "type": "snaker:callActivity", "properties": {
      "processDefineName": "sub-flow",
      "assignee": "user2"
    }},
    {"id": "post_check", "type": "snaker:task", "properties": {"assignee": "user3"}},
    {"id": "end", "type": "snaker:end"}
  ],
  "edges": [
    {"id": "e0", "sourceNodeId": "start", "targetNodeId": "apply"},
    {"id": "e1", "sourceNodeId": "apply", "targetNodeId": "sub_call"},
    {"id": "e2", "sourceNodeId": "sub_call", "targetNodeId": "post_check"},
    {"id": "e3", "sourceNodeId": "post_check", "targetNodeId": "end"}
  ]
}
```

行为: 主流程到 sub_call 时启动子实例 (parentId=主实例). 立即推进主流程到 post_check (不阻塞). 子实例完成后通过 `parent.parentStatus = "CHILD_DONE"` 通知主实例.

### 9.7 字段权限

节点 properties.field 控制字段权限:
```json
{
  "id": "leader_review",
  "type": "snaker:task",
  "properties": {
    "assignee": "leader",
    "field": {
      "PERMISSION_f_leaveType": 2,
      "PERMISSION_f_days": 2,
      "PERMISSION_f_secret": 3,
      "PERMISSION_f_old_amount": 1
    }
  }
}
```

权限码: **1=只读 / 2=编辑 / 3=隐藏**.

引擎过滤: 执行 task.execute 时只保留 `perm == 2` 的 `f_*` 字段进入 inst.variables.

### 9.8 业务变量持久化

```bash
# 启动时传 f_ 变量 (持久化到 inst.variables)
curl -X POST /wf/processInstance/startAndExecute \
  -d '{
    "processDefineId": ...,
    "operator": "user1",
    "f_amount": 5000,
    "f_leaveType": "事假",
    "u_userId": "user1",
    "submitType": 0
  }'

# 执行时传 tf_ (运行时透传, 不持久化)
curl -X POST /wf/processTask/execute \
  -d '{
    "processTaskId": ...,
    "tf_comment": "同意",
    "operator": "leader",
    "submitType": 1
  }'
```

变量前缀语义:
- `f_*` (instance variables): 持久化到 inst.variables, 跨 task 可见
- `tf_*` (task flow variables): 运行时透传, 不持久化
- `u_*` (user info): 操作人信息, 仅 exec context, 不写回实例

### 9.9 监控与运维

```bash
# 健康检查
curl http://localhost:8101/healthz

# 看板总览
curl http://localhost:8101/api/admin/stats/overview

# Prometheus 指标
curl http://localhost:8101/metrics

# 链路追踪
curl "http://localhost:8101/api/admin/trace?limit=20"

# 看具体流程的状态
curl -X POST /wf/processInstance/detail \
  -d '{"id": "91975865463809"}'

# 看 leader 的待办
curl -X POST /wf/processTask/todoList \
  -d '{"operator": "leader"}'

# 委派 leader → boss
curl -X POST /wf/processTask/delegate \
  -d '{"processTaskId": "...", "operator": "leader", "targetUserId": "boss"}'

# 挂起 / 恢复
curl -X POST /wf/processInstance/suspend \
  -d '{"id": "91975865463809"}'
curl -X POST /wf/processInstance/resume \
  -d '{"id": "91975865463809"}'
```

### 9.10 错误排查速查

| 现象 | 排查 |
|------|------|
| `code=99999999 + ValueError` | `docs/known-issues.md` 搜关键词 (§X) |
| 流程卡死 state=10 | `processInstance/detail` 看 `tasks[].taskActorIdList` |
| 100 实例慢 | `/metrics` 看 wf_task_duration + 调大 PG pool |
| 双端行为不一致 | `docs/flow.md §2` 后端选择矩阵 |
| 找不到 action | `docs/actions.md` 38 个 action 速查表 |
| `state=50` 不可 execute | `processInstance/resume` |
| 详情含 `_comments` / `_extra` / `_delegate_of` | `data.tasks[].variable` JSON parse |

### 9.11 进阶功能

- **Custom 节点** (§16 FIX-T38): 调用外部处理器, 见 `docs/flow.md §3.5`
- **surrogate 全局委派**: `processSurrogate/save {operator, surrogate}`
- **delegate 任务级委派**: `processTask/delegate {processTaskId, operator, targetUserId}`
- **transferAndAdd** (§3.2.2): `processTask/transferAndAdd` 保留原 actor
- **withForm** (§3.2.3): `processTask/withForm` 运行时表单绑定
- **delegateHistory** (§3.2.1): `processTask/delegateHistory` 查询历史
