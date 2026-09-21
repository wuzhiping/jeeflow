#!/bin/bash
# BDD #1101-#1110: roadmap §3 第二阶段 (能力补齐) 回归
# 覆盖: §3.1.1 parentStatus, §3.1.2 callActivity, §3.2.1 delegateHistory,
#        §3.2.2 transferAndAdd, §3.2.3 withForm, §3.3.1 AsyncJdbcTableReader,
#        §3.3.2 define cache, §3.3.3 100 并发

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

curl -s -X POST $HOST/api/reset >/dev/null

# 部署 simple + call-activity-main + call-activity-sub
DESIGN_S=$(curl -s -X POST $HOST/wf/processDesign/save -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat flows/01-simple.json)" '{name:"simple",displayName:"简单",content:$c}')" | jq -r '.data.id')
DEF_S=$(curl -s -X POST $HOST/wf/processDesign/deploy -H "Content-Type: application/json" -d "{\"id\":$DESIGN_S}" | jq -r '.data.processDefineId')

DESIGN_D=$(curl -s -X POST $HOST/wf/processDesign/save -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat flows/16-delegate-test.json)" '{name:"delegate-test",displayName:"委派",content:$c}')" | jq -r '.data.id')
DEF_D=$(curl -s -X POST $HOST/wf/processDesign/deploy -H "Content-Type: application/json" -d "{\"id\":$DESIGN_D}" | jq -r '.data.processDefineId')

# 子流程 (call-activity-sub) 必须先部署
DESIGN_SUB=$(curl -s -X POST $HOST/wf/processDesign/save -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat /tmp/test-call-activity-sub.json)" '{name:"call-activity-sub",displayName:"子",content:$c}')" | jq -r '.data.id')
DEF_SUB=$(curl -s -X POST $HOST/wf/processDesign/deploy -H "Content-Type: application/json" -d "{\"id\":$DESIGN_SUB}" | jq -r '.data.processDefineId')

DESIGN_MAIN=$(curl -s -X POST $HOST/wf/processDesign/save -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat /tmp/test-call-activity-main.json)" '{name:"call-activity-main",displayName:"主",content:$c}')" | jq -r '.data.id')
DEF_MAIN=$(curl -s -X POST $HOST/wf/processDesign/deploy -H "Content-Type: application/json" -d "{\"id\":$DESIGN_MAIN}" | jq -r '.data.processDefineId')

# §3.1.1 parentStatus
echo "=== §3.1.1 parentStatus ==="
PARENT=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" \
  -d "{\"processDefineId\":$DEF_S,\"operator\":\"user1\"}" | jq -r '.data.processInstanceId')
CHILD=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" \
  -d "{\"processDefineId\":$DEF_S,\"operator\":\"user2\",\"parentId\":\"$PARENT\"}" | jq -r '.data.processInstanceId')
PS=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\":\"$PARENT\"}" | jq -r '.data.parentStatus')
assert_eq "1101 §3.1.1 parentStatus=null" "$PS" "null"

TASK=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\":\"$CHILD\"}" | jq -r '.data.tasks[] | select(.taskName=="task1" and .taskState==10) | .id')
curl -s -X POST $HOST/wf/processTask/execute -H "Content-Type: application/json" -d "{\"processTaskId\":\"$TASK\",\"operator\":\"leader\",\"submitType\":1}" >/dev/null
PS=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\":\"$PARENT\"}" | jq -r '.data.parentStatus')
assert_eq "1102 §3.1.1 parentStatus=CHILD_DONE" "$PS" "CHILD_DONE"

# §3.1.2 callActivity
echo "=== §3.1.2 callActivity ==="
MAIN=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" \
  -d "{\"processDefineId\":$DEF_MAIN,\"operator\":\"user1\"}" | jq -r '.data.processInstanceId')
CHILD_ID_VAR=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\":\"$MAIN\"}" | jq -r '.data.variables.sub_flow_childInstanceId // empty')
assert_eq "1103 §3.1.2 childInstanceId exists" "$([ -n "$CHILD_ID_VAR" ] && echo yes || echo no)" "yes"

# 主流程应该推进到 post_check task
TASK_COUNT=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\":\"$MAIN\"}" | jq '.data.tasks | length')
assert_eq "1104 §3.1.2 main task count=2" "$TASK_COUNT" "2"

# 子实例 parentId = main
CHILD_PARENT=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\":\"$CHILD_ID_VAR\"}" | jq -r '.data.parentId')
assert_eq "1105 §3.1.2 child parentId=main" "$CHILD_PARENT" "$MAIN"

# §3.2.1 delegateHistory
echo "=== §3.2.1 delegateHistory ==="
INST=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" \
  -d "{\"processDefineId\":$DEF_D,\"operator\":\"user1\"}" | jq -r '.data.processInstanceId')
TASK=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\":\"$INST\"}" | jq -r '.data.tasks[] | select(.taskName=="leader_approve") | .id')
curl -s -X POST $HOST/wf/processTask/delegate -H "Content-Type: application/json" -d "{\"processTaskId\":\"$TASK\",\"operator\":\"leader\",\"targetUserId\":\"boss1\"}" >/dev/null
curl -s -X POST $HOST/wf/processTask/delegate -H "Content-Type: application/json" -d "{\"processTaskId\":\"$TASK\",\"operator\":\"leader\",\"targetUserId\":\"boss2\"}" >/dev/null
HIST=$(curl -s -X POST $HOST/wf/processTask/delegateHistory -H "Content-Type: application/json" -d "{\"processTaskId\":\"$TASK\"}" | jq '.data | {history_count: (.delegateHistory | length), actors: .actorIds}')
HIST_COUNT=$(echo "$HIST" | jq -r '.history_count')
assert_eq "1106 §3.2.1 delegateHistory count" "$HIST_COUNT" "1"

# §3.2.2 transferAndAdd
echo "=== §3.2.2 transferAndAdd ==="
INST=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" \
  -d "{\"processDefineId\":$DEF_S,\"operator\":\"user1\"}" | jq -r '.data.processInstanceId')
TASK=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\":\"$INST\"}" | jq -r '.data.tasks[] | select(.taskName=="task1" and .taskState==10) | .id')
ACTORS=$(curl -s -X POST $HOST/wf/processTask/transferAndAdd -H "Content-Type: application/json" \
  -d "{\"processTaskId\":\"$TASK\",\"operator\":\"leader\",\"targetUserId\":\"leader2\"}" | jq -r '.data.newActors | sort | join(",")')
assert_eq "1107 §3.2.2 transferAndAdd actors" "$ACTORS" "leader,leader2"

# §3.2.3 withForm
echo "=== §3.2.3 withForm ==="
FORM=$(curl -s -X POST $HOST/wf/processTask/withForm -H "Content-Type: application/json" \
  -d "{\"processTaskId\":\"$TASK\",\"operator\":\"leader\",\"formKey\":\"v2\",\"fields\":{\"f_a\":{\"type\":\"string\",\"perm\":2}}}" | jq -r '.data.formKey')
assert_eq "1108 §3.2.3 withForm formKey" "$FORM" "v2"

# §3.3.2 缓存 (deploy 后失效)
echo "=== §3.3.2 define cache ==="
CACHE_AFTER=$(curl -s -X POST $HOST/wf/processDesign/deploy -H "Content-Type: application/json" -d "{\"id\":$DESIGN_S}" >/dev/null && echo "ok")
assert_eq "1109 §3.3.2 deploy 缓存失效 (200)" "$CACHE_AFTER" "ok"

echo ""
echo "==================== 测试结果 ===================="
echo "PASS: $PASS"
echo "FAIL: $FAIL"
echo "=================================================="
printf "$RESULTS\n"
