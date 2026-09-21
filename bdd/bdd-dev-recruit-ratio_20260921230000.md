# BDD-DEV-005 dev-recruit-ratio (20260921230000)

## 流程设计

```mermaid
flowchart LR
    start([开始]) --> apply[提交招聘]
    apply --> panel_vote[评委投票(2/3)<br/>u_cto+u_rd_dir+u_ceo<br/>PARALLEL + #nrOfCompletedInstances>=2]
    panel_vote --> hr_record[HR 备案]
    hr_record --> end([结束])
```

## 场景

招聘审批 - 比例会签。3 个评委（CTO/研发总监/CEO），满足 2 人通过即流转，未投票者 task 自动 ABANDONED。

## 用到的能力

- `performType=1` + `countersignType=PARALLEL` 并行会签
- `countersignCompletionCondition="#nrOfCompletedInstances>=2"` 比例完成条件（OGNL 表达式，`nrOfCompletedInstances`/`nrOfInstances` 自动注入）
- 比例会签完成条件命中后，未投票者 task 自动 `taskState=99 ABANDONED`（FIX-T111 §112）
- `assignee="u_cto,u_rd_dir,u_ceo"` 字面量多 actor
- `field.PERMISSION_f_position:1` + `PERMISSION_f_level:2` 字段权限

## 执行脚本

```bash
# reset + deploy
curl -s -X POST http://127.0.0.1:8101/api/reset
CONTENT=$(jq -c . bdd/bdd-dev-recruit-ratio_20260921230000.json)
curl -s -X POST http://127.0.0.1:8101/wf/processDesign/save \
  -d "$(jq -nc --arg c "$CONTENT" '{name:"dev-recruit-ratio", displayName:"BDD-DEV-招聘审批-比例会签", type:"approval", content:$c}')"
curl -s -X POST http://127.0.0.1:8101/wf/processDesign/deploy -d '{"id":"1"}'
# → processDefineId=20

PID=$(curl -s -X POST http://127.0.0.1:8101/wf/processInstance/startAndExecute \
  -d '{"processDefineId":"20","operator":"u_rd_dir","title":"招聘-BDD-005",
       "assignees":{"apply":"u_rd_dir"},
       "variables":{"submitType":0,"f_position":"高级前端","f_level":"P6",
                    "u_userId":"u_rd_dir","u_realName":"王强"}}' \
  | jq -r .data.processInstanceId)

# 3 个评委 task 并行 active
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/highLight -d "{\"id\":\"$PID\"}"

# 1. u_cto 通过 (1/3)
T1=$(curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList \
  -d '{"operator":"u_cto","pageNum":1,"pageSize":20}' | jq -r '.data.rows[0].id')
curl -s -X POST http://127.0.0.1:8101/wf/processTask/execute \
  -d "{\"processTaskId\":\"$T1\",\"submitType\":1,\"operator\":\"u_cto\",\"variables\":{\"u_userId\":\"u_cto\",\"u_realName\":\"李娜\"}}"

# 此时 u_ceo 仍 DOING (1/3 < 2)
curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList -d '{"operator":"u_ceo","pageNum":1,"pageSize":20}'

# 2. u_rd_dir 通过 (2/3) → 比例条件命中 → u_ceo ABANDONED + 流转到 hr_record
T2=$(curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList \
  -d '{"operator":"u_rd_dir","pageNum":1,"pageSize":20}' | jq -r '.data.rows[0].id')
curl -s -X POST http://127.0.0.1:8101/wf/processTask/execute \
  -d "{\"processTaskId\":\"$T2\",\"submitType\":1,\"operator\":\"u_rd_dir\",\"variables\":{\"u_userId\":\"u_rd_dir\",\"u_realName\":\"王强\"}}"

# 验证 u_ceo task 状态变为 ABANDONED(99)
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/approvalRecord \
  -d "{\"id\":\"$PID\"}" | jq '.data[] | select(.taskName=="panel_vote") | {taskState, operator}'
```

## 校验

| 项 | 期望 | 实际 | 结果 |
|---|---|---|---|
| 3 个评委并行 active | activeNodeNames=[panel_vote], members=3 | ✅ | ✅ |
| 第 1 票后仍未流转 (1/3 < 2) | u_ceo DOING, hr_record 未激活 | ✅ | ✅ |
| 第 2 票后命中比例 (2/3) | u_ceo ABANDONED(99), hr_record 激活 | ✅ | ✅ |
| approvalRecord panel_vote 出现 3 次 | u_cto DONE, u_rd_dir DONE, u_ceo ABANDONED | ✅ | ✅ |
| `state` | 20 (DONE) | 20 | ✅ |
| 比例条件求值表达式 | #nrOfCompletedInstances>=2 | engine 内部 OGNL 评估 | ✅ |

## 引擎行为关键发现

- `TaskState.ABANDONED = 99`（taskState 枚举值，model.py:96 附近定义）
- 比例会签完成条件命中时，未投票者 task 自动置 ABANDONED + updateUser = 触发者 (FIX-T111 §112)
- `hr_record` 用 `taskType=2` (RECORD) → 创建后自动完成（设计自动登记语义）

## 结果

- memory (8101): ✅ **PASS**（比例会签 2/3 触发 ABANDON + 自动流转）
- pg (8102): skipped