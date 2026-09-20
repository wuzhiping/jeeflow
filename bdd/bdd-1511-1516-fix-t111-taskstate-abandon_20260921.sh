#!/bin/bash
# BDD #1511-#1516: §112 FIX-T111 (2026-09-21) TaskState.ABANDONED updateUser 语义
# 覆盖:
#   §112.1 比例会签 (RATIO) 完成条件命中 → ABANDON task.updateUser = 命中条件的提交人
#   §112.2 PARALLEL 全部预创建,OAV 完成 (PARALLEL 不带 cs_cond) → ABANDON task.updateUser = 命中条件的人
#   §112.3 ONE_VOTE_VETO REJECT → ABANDON task.updateUser = 否决人
#   §112.4 流程撤回 (withdraw) → ABANDON task.updateUser = 撤回人
#   §112.5 backward compat: 调用方不传 abandoned_by 时 updateUser 不被覆盖
#   §112.6 approvalRecord 包含 state=99 任务 (审计可见)

set -e
HOST=http://localhost:8101
PASS=0
FAIL=0
RESULTS=""

assert_eq() {
  local desc="$1" actual="$2" expected="$3"
  if [ "$actual" = "$expected" ]; then
    PASS=$((PASS + 1))
    RESULTS="$RESULTS\n✅ #$1 [$desc]"
  else
    FAIL=$((FAIL + 1))
    RESULTS="$RESULTS\n❌ #$1 [$desc]  expected=$expected actual=$actual"
  fi
}

# 找指定 instance + taskName + taskState 的 taskId
get_task_for_inst() {
  local operator="$1" inst="$2"
  curl -s -X POST $HOST/wf/processTask/todoList -H "Content-Type: application/json" \
    -d "{\"operator\":\"$operator\",\"pageNum\":1,\"pageSize\":50}" \
    | jq -r --arg inst "$inst" '.data.rows[] | select(.processInstanceId==$inst) | .id' | head -1
}

# 用 taskName + taskState + processInstanceId 找 task id (查 detail 后从 raw 中提取)
get_task_id_by_name_state() {
  local inst="$1" task_name="$2" task_state="$3"
  curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
    -d "{\"id\":\"$inst\"}" \
    | jq -r --arg n "$task_name" --arg s "$task_state" \
      '.data.tasks[] | select(.taskName==$n and (.taskState|tostring)==$s) | .id' | head -1
}

curl -s -X POST $HOST/api/reset >/dev/null

# ─────────────────────────────────────────────────────────────────────
# §112.1 比例会签 (RATIO) 完成条件命中
# ─────────────────────────────────────────────────────────────────────
echo "=== §112.1 比例会签 2/3 完成, userC ABANDON.updateUser=userB ==="
DESIGN1=$(curl -s -X POST $HOST/wf/processDesign/save -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat tdd/bug3_countersign_3of3_abandon_repro.json)" '{name:"bug3_ratio",displayName:"BUG-3比例会签",content:$c}')" | jq -r '.data.id')
DEF1=$(curl -s -X POST $HOST/wf/processDesign/deploy -H "Content-Type: application/json" -d "{\"id\":$DESIGN1}" | jq -r '.data.processDefineId')

INST1=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" \
  -d "{\"processDefineId\":$DEF1,\"operator\":\"user1\",\"assignees\":{\"apply\":\"user1\"},\"variables\":{\"submitType\":0,\"u_userId\":\"user1\",\"u_realName\":\"张三\"}}" | jq -r '.data.processInstanceId')

# userA approve
TASK_A=$(get_task_for_inst userA "$INST1")
curl -s -X POST $HOST/wf/processTask/execute -H "Content-Type: application/json" \
  -d "{\"processTaskId\":\"$TASK_A\",\"submitType\":1,\"operator\":\"userA\"}" >/dev/null

# userB approve → 命中 2/3,userC 应被 ABANDON
TASK_B=$(get_task_for_inst userB "$INST1")
curl -s -X POST $HOST/wf/processTask/execute -H "Content-Type: application/json" \
  -d "{\"processTaskId\":\"$TASK_B\",\"submitType\":1,\"operator\":\"userB\"}" >/dev/null

# 验证 instance.state=20
STATE1=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
  -d "{\"id\":$INST1}" | jq -r '.data.state')
assert_eq "§112.1 instance.state=20 after 2/3 approve" "$STATE1" "20"

# 验证 userC task state=99 + updateUser=userB
USERC_UPDATEUSER=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
  -d "{\"id\":$INST1}" \
  | jq -r '.data.tasks[] | select(.taskState==99) | .updateUser')
assert_eq "§112.1 ABANDON task.updateUser=userB (was user1 before fix)" "$USERC_UPDATEUSER" "userB"

# 验证 userC task updateTime + createUser (sanity)
USERC_CREATER=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
  -d "{\"id\":$INST1}" \
  | jq -r '.data.tasks[] | select(.taskState==99) | .createUser')
assert_eq "§112.1 ABANDON task.createUser=user1 (unchanged)" "$USERC_CREATER" "user1"

# 验证 ABANDON task.finishTime 仍为 null (本设计要求)
USERC_FINISHTIME=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
  -d "{\"id\":$INST1}" \
  | jq -r '.data.tasks[] | select(.taskState==99) | .finishTime')
assert_eq "§112.1 ABANDON task.finishTime=null (永久 NULL)" "$USERC_FINISHTIME" "null"

# ─────────────────────────────────────────────────────────────────────
# §112.2 ONE_VOTE_VETO REJECT → ABANDON.task.updateUser = 否决人
# ─────────────────────────────────────────────────────────────────────
echo "=== §112.2 ONE_VOTE_VETO REJECT, ABANDON.updateUser=rejecter ==="
curl -s -X POST $HOST/api/reset >/dev/null
cat > /tmp/bug3_one_vote_veto.json <<'EOF'
{
  "name": "bug3_one_vote_veto",
  "displayName": "BUG-3 ONE_VOTE_VETO 测试",
  "nodes": [
    {"id":"start","type":"snaker:start","properties":{}},
    {"id":"apply","type":"snaker:task","properties":{"assignee":"user1","taskType":0,"performType":0}},
    {"id":"review_veto","type":"snaker:task","properties":{"assignee":"userA,userB,userC","taskType":0,"performType":1,"countersignType":"PARALLEL","countersignCompletionCondition":"ONE_VOTE_VETO"}},
    {"id":"end_rejected","type":"snaker:end","properties":{}},
    {"id":"end_approved","type":"snaker:end","properties":{}}
  ],
  "edges": [
    {"id":"e0","sourceNodeId":"start","targetNodeId":"apply","properties":{}},
    {"id":"e1","sourceNodeId":"apply","targetNodeId":"review_veto","properties":{}},
    {"id":"e2","sourceNodeId":"review_veto","targetNodeId":"end_approved","properties":{}},
    {"id":"e3","sourceNodeId":"review_veto","targetNodeId":"end_rejected","properties":{}}
  ]
}
EOF
DESIGN2=$(curl -s -X POST $HOST/wf/processDesign/save -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat /tmp/bug3_one_vote_veto.json)" '{name:"bug3_veto",displayName:"veto",content:$c}')" | jq -r '.data.id')
DEF2=$(curl -s -X POST $HOST/wf/processDesign/deploy -H "Content-Type: application/json" -d "{\"id\":$DESIGN2}" | jq -r '.data.processDefineId')

INST2=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" \
  -d "{\"processDefineId\":$DEF2,\"operator\":\"user1\",\"assignees\":{\"apply\":\"user1\"},\"variables\":{\"submitType\":0,\"u_userId\":\"user1\",\"u_realName\":\"张三\"}}" | jq -r '.data.processInstanceId')

# userA 用 submitType=20 否决
TASK_A=$(get_task_for_inst userA "$INST2")
curl -s -X POST $HOST/wf/processTask/execute -H "Content-Type: application/json" \
  -d "{\"processTaskId\":\"$TASK_A\",\"submitType\":20,\"operator\":\"userA\"}" >/dev/null

STATE2=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
  -d "{\"id\":$INST2}" | jq -r '.data.state')
assert_eq "§112.2 ONE_VOTE_VETO REJECT instance.state=45" "$STATE2" "45"

# userB 和 userC 应该是 ABANDONED,updateUser=userA (rejecter)
ABANDON2_USERS=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
  -d "{\"id\":$INST2}" \
  | jq -r '[.data.tasks[] | select(.taskState==99) | .updateUser] | sort | join(",")')
assert_eq "§112.2 all ABANDON tasks.updateUser=userA" "$ABANDON2_USERS" "userA,userA"

# ─────────────────────────────────────────────────────────────────────
# §112.3 流程撤回 (withdraw) → ABANDON.task.updateUser = 撤回人
# ─────────────────────────────────────────────────────────────────────
echo "=== §112.3 withdraw path, ABANDON.updateUser=withdrawer ==="
curl -s -X POST $HOST/api/reset >/dev/null
cat > /tmp/bug3_withdraw.json <<'EOF'
{
  "name":"bug3_withdraw","displayName":"withdraw test",
  "nodes":[
    {"id":"start","type":"snaker:start","properties":{}},
    {"id":"apply","type":"snaker:task","properties":{"assignee":"user1","taskType":0,"performType":0}},
    {"id":"leader","type":"snaker:task","properties":{"assignee":"leader","taskType":0,"performType":0}},
    {"id":"end","type":"snaker:end","properties":{}}
  ],
  "edges":[
    {"id":"e0","sourceNodeId":"start","targetNodeId":"apply","properties":{}},
    {"id":"e1","sourceNodeId":"apply","targetNodeId":"leader","properties":{}},
    {"id":"e2","sourceNodeId":"leader","targetNodeId":"end","properties":{}}
  ]
}
EOF
DESIGN3=$(curl -s -X POST $HOST/wf/processDesign/save -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat /tmp/bug3_withdraw.json)" '{name:"bug3_w",displayName:"w",content:$c}')" | jq -r '.data.id')
DEF3=$(curl -s -X POST $HOST/wf/processDesign/deploy -H "Content-Type: application/json" -d "{\"id\":$DESIGN3}" | jq -r '.data.processDefineId')

INST3=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" \
  -d "{\"processDefineId\":$DEF3,\"operator\":\"user1\",\"assignees\":{\"apply\":\"user1\"},\"variables\":{\"submitType\":0,\"u_userId\":\"user1\",\"u_realName\":\"张三\"}}" | jq -r '.data.processInstanceId')

# 流程撤回 (user1 withdraw)
curl -s -X POST $HOST/wf/processInstance/withdraw -H "Content-Type: application/json" \
  -d "{\"id\":$INST3,\"operator\":\"user1\"}" >/dev/null

STATE3=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
  -d "{\"id\":$INST3}" | jq -r '.data.state')
assert_eq "§112.3 withdraw instance.state=30 WITHDRAW" "$STATE3" "30"

LEADER_ABANDON_USER=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
  -d "{\"id\":$INST3}" \
  | jq -r '.data.tasks[] | select(.taskState==99) | .updateUser')
assert_eq "§112.3 leader task ABANDON.updateUser=user1 (withdrawer)" "$LEADER_ABANDON_USER" "user1"

# ─────────────────────────────────────────────────────────────────────
# §112.4 approvalRecord 包含 state=99 任务 (审计可见)
# ─────────────────────────────────────────────────────────────────────
echo "=== §112.4 approvalRecord 包含 ABANDON tasks ==="
# 用 INST3 (withdraw 实例,最近创建的,还活着) 验证 approvalRecord 包含 ABANDON
AR=$(curl -s -X POST $HOST/wf/processInstance/approvalRecord -H "Content-Type: application/json" \
  -d "{\"id\":$INST3}" | jq '[.data[] | select(.taskName=="leader" and .taskState==99)] | length')
assert_eq "§112.4 approvalRecord 含 1 条 leader state=99 ABANDON record" "$AR" "1"

# ─────────────────────────────────────────────────────────────────────
# §112.5 todoList 不应包含 state=99 (DOING only)
# ─────────────────────────────────────────────────────────────────────
echo "=== §112.5 userC todoList 应为空 (ABANDON 不算待办) ==="
USERC_TODO=$(curl -s -X POST $HOST/wf/processTask/todoList -H "Content-Type: application/json" \
  -d '{"operator":"userC","pageNum":1,"pageSize":50}' \
  | jq --arg inst "$INST1" '[.data.rows[] | select(.processInstanceId==$inst)] | length')
assert_eq "§112.5 userC todoList has 0 active tasks (ABANDON excluded)" "$USERC_TODO" "0"

# ─────────────────────────────────────────────────────────────────────
# §112.6 backward compat (默认参数保持原行为)
# ─────────────────────────────────────────────────────────────────────
echo "=== §112.6 backward compat: t.abandon(now) 不传 abandoned_by 不覆盖 updateUser ==="
cd /opt/jupyter/src/RD/projects/jeeFlow
./.venv/bin/python3 -c "
from vendor.jeeflow.model import ProcessTask, TaskState
from datetime import datetime
t = ProcessTask(id=1, processInstanceId=1, taskName='x', displayName='', taskType=0, performType=0)
t.createUser='user1'
t.updateUser='ORIGINAL_OP'
now = datetime.now()
t.abandon(now)  # backward compat: abandoned_by 默认 ''
assert t.taskState == TaskState.ABANDONED, f'taskState={t.taskState}'
assert t.updateUser == 'ORIGINAL_OP', f'updateUser={t.updateUser!r} (should not be overwritten)'
print('OK')
"

# ─────────────────────────────────────────────────────────────────────
# 输出结果
# ─────────────────────────────────────────────────────────────────────
printf "$RESULTS\n"
echo ""
echo "═══════════════════════════════════════"
echo "  §112 FIX-T111 BDD: $PASS passed, $FAIL failed"
echo "═══════════════════════════════════════"
[ $FAIL -eq 0 ] && exit 0 || exit 1
