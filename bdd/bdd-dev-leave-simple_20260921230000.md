# BDD-DEV-001 dev-leave-simple (20260921230000)

## 流程设计

```mermaid
flowchart LR
    start([开始]) --> apply[提交请假]
    apply --> leader_approve[组长审批<br/>PERMISSION_f_leaveType=1<br/>PERMISSION_days=2]
    leader_approve --> end([结束])
```

## 场景

请假申请-线性审批 + 字段权限演示。`u_fe_eng` 发起请病假 3 天，`u_fe_lead` (前端组长 D02) 审批。

## 用到的能力

- `snaker:start / task / end` 线性流转
- `assignee="applicant"` + `assignee="u_fe_lead"` 字面量处理人
- `field.PERMISSION_f_leaveType:1` (只读) / `field.PERMISSION_days:2` (编辑)
- 字段权限码语义：1=只读 / 2=编辑 / 3=隐藏 (FIX-DOC-1 §82)

## 执行脚本

```bash
# 1. reset
curl -s -X POST http://127.0.0.1:8101/api/reset

# 2. deploy
DESIGN=$(jq -c . bdd/bdd-dev-leave-simple_20260921230000.json)
curl -s -X POST http://127.0.0.1:8101/wf/processDesign/save \
  -d "$(jq -nc --arg c "$DESIGN" '{name:"dev-leave-simple", displayName:"BDD-DEV-请假申请-线性", type:"approval", content:$c}')"
# → {"code":0,"data":{"id":"1"}}

curl -s -X POST http://127.0.0.1:8101/wf/processDesign/deploy -d '{"id":"1"}'
# → {"code":0,"data":{"processDefineId":"20"}}

# 3. start
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/startAndExecute \
  -d '{"processDefineId":"20","operator":"u_fe_eng","title":"请假-BDD-001",
       "assignees":{"apply":"u_fe_eng"},
       "variables":{"submitType":0,"f_leaveType":"sick","f_days":3,
                    "u_userId":"u_fe_eng","u_realName":"周磊"}}'
# → processInstanceId=92160380497921

# 4. todo + execute (u_fe_lead)
curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList \
  -d '{"operator":"u_fe_lead","pageNum":1,"pageSize":20}'
# taskId=92160380499971

curl -s -X POST http://127.0.0.1:8101/wf/processTask/execute \
  -d '{"processTaskId":"92160380499971","submitType":1,"operator":"u_fe_lead",
       "variables":{"u_userId":"u_fe_lead","u_realName":"刘洋"}}'
```

## 校验

| 项 | 期望 | 实际 | 结果 |
|---|---|---|---|
| `processInstance/detail.state` | 20 (DONE) | 20 | ✅ |
| `approvalRecord` 节点数 | 2 (apply + leader_approve) | 2 | ✅ |
| `bizData.f_leaveType` | "sick" (PERMISSION=1 只读, 不被覆盖) | "sick" | ✅ |
| `bizData.f_days` | 3 (PERMISSION=2 编辑, 保留原值) | 3 | ✅ |
| `bizData.u_*` 不持久化 | null | null | ✅ |
| operator 节点匹配 | u_fe_lead → leader_approve | u_fe_lead | ✅ |

## 结果

- memory (8101): ✅ **PASS**
- pg (8102): skipped (BBD.md 不强制双端)