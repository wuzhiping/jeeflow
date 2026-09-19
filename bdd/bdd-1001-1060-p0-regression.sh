#!/bin/bash
# BDD #1001-#1060：roadmap 2.1 P0 任务回归 (2026-09-20)
# 覆盖：§56 §70 §40 §69 §46 §16 + 7 个新端点

set -e
HOST=http://localhost:8101
PASS=0
FAIL=0
RESULTS=""

assert_eq() {
  local desc="$1"
  local actual="$2"
  local expected="$3"
  if [ "$actual" = "$expected" ]; then
    PASS=$((PASS + 1))
    RESULTS="$RESULTS\n✅ #$1 [$desc]"
  else
    FAIL=$((FAIL + 1))
    RESULTS="$RESULTS\n❌ #$1 [$desc]  expected=$expected actual=$actual"
  fi
}

assert_neq() {
  local desc="$1"
  local actual="$2"
  local unexpected="$3"
  if [ "$actual" != "$unexpected" ]; then
    PASS=$((PASS + 1))
    RESULTS="$RESULTS\n✅ #$1 [$desc]"
  else
    FAIL=$((FAIL + 1))
    RESULTS="$RESULTS\n❌ #$1 [$desc]  unexpected=$unexpected"
  fi
}

# 部署 simple 流程
DESIGN_ID=$(curl -s -X POST $HOST/wf/processDesign/save \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat flows/01-simple.json)" '{name: "simple", displayName: "简单审批", content: $c}')" | jq -r '.data.id')
DEF_ID=$(curl -s -X POST $HOST/wf/processDesign/deploy \
  -H "Content-Type: application/json" -d "{\"id\": $DESIGN_ID}" | jq -r '.data.processDefineId')
echo "DEF_ID=$DEF_ID"

start_inst() {
  local op="$1" extra="$2"
  curl -s -X POST $HOST/wf/processInstance/startAndExecute \
    -H "Content-Type: application/json" \
    -d "{\"processDefineId\": $DEF_ID, \"operator\": \"$op\" $extra}"
}
get_task() {
  local inst="$1"
  curl -s -X POST $HOST/wf/processInstance/detail \
    -H "Content-Type: application/json" -d "{\"id\": \"$inst\"}" \
    | jq -r '.data.tasks[] | select(.taskState==10) | .id' | head -1
}

# ============= §56 P0 - parentId =============
echo "=== BDD #1001: §56 parentId 写入 ==="
PARENT=$(start_inst user1 | jq -r '.data.processInstanceId')
PARENT2=$(start_inst user2 | jq -r '.data.processInstanceId')
CHILD=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute \
  -H "Content-Type: application/json" \
  -d "{\"processDefineId\": $DEF_ID, \"operator\": \"user2\", \"parentId\": \"$PARENT\"}" | jq -r '.data.processInstanceId')
PARENT_ID=$(curl -s -X POST $HOST/wf/processInstance/detail \
  -H "Content-Type: application/json" -d "{\"id\": \"$CHILD\"}" | jq -r '.data.parentId')
assert_eq "1001 §56 parentId" "$PARENT_ID" "$PARENT"

# ============= §70 P0 - suspend/resume/transfer/comment/extra =============
echo "=== BDD #1011-#1050: §70 操作端点 ==="
INST=$(start_inst user1 | jq -r '.data.processInstanceId')
TASK=$(get_task "$INST")

# 1011 suspend
STATE=$(curl -s -X POST $HOST/wf/processInstance/suspend \
  -H "Content-Type: application/json" -d "{\"id\": \"$INST\"}" | jq -r '.data.state')
assert_eq "1011 §70 suspend state" "$STATE" "50"

# 1012 resume
STATE=$(curl -s -X POST $HOST/wf/processInstance/resume \
  -H "Content-Type: application/json" -d "{\"id\": \"$INST\"}" | jq -r '.data.state')
assert_eq "1012 §70 resume state" "$STATE" "10"

# 1013 transfer
NEW=$(curl -s -X POST $HOST/wf/processTask/transfer \
  -H "Content-Type: application/json" \
  -d "{\"processTaskId\": \"$TASK\", \"operator\": \"leader\", \"targetUserId\": \"leader2\"}" | jq -r '.data.newActors[0]')
assert_eq "1013 §70 transfer target" "$NEW" "leader2"

# 1014 comment
COUNT=$(curl -s -X POST $HOST/wf/processTask/comment \
  -H "Content-Type: application/json" \
  -d "{\"processTaskId\": \"$TASK\", \"operator\": \"leader2\", \"comment\": \"BDD#1014\"}" | jq -r '.data.count')
assert_eq "1014 §70 comment count" "$COUNT" "1"

# 1015 extra
URG=$(curl -s -X POST $HOST/wf/processTask/extra \
  -H "Content-Type: application/json" \
  -d "{\"processTaskId\": \"$TASK\", \"operator\": \"leader2\", \"urgency\": \"high\"}" | jq -r '.data.extra.urgency')
assert_eq "1015 §70 extra urgency" "$URG" "high"

# ============= §69 P0 - delegate =============
echo "=== BDD #1021-#1023: §69 delegate ==="
INST=$(start_inst user1 | jq -r '.data.processInstanceId')
TASK=$(get_task "$INST")

# 1021 delegate
DEL=$(curl -s -X POST $HOST/wf/processTask/delegate \
  -H "Content-Type: application/json" \
  -d "{\"processTaskId\": \"$TASK\", \"operator\": \"leader\", \"targetUserId\": \"boss\"}" | jq -r '.data.to')
assert_eq "1021 §69 delegate to" "$DEL" "boss"

# 1022 boss 通过 delegate execute
STATE=$(curl -s -X POST $HOST/wf/processTask/execute \
  -H "Content-Type: application/json" \
  -d "{\"processTaskId\": \"$TASK\", \"operator\": \"boss\", \"submitType\": 1}" | jq -r '.code')
assert_eq "1022 §69 boss execute" "$STATE" "0"

# 1023 delegate 错误用法: operator 不在 actorIds
INST2=$(start_inst user1 | jq -r '.data.processInstanceId')
TASK2=$(get_task "$INST2")
CODE=$(curl -s -X POST $HOST/wf/processTask/delegate \
  -H "Content-Type: application/json" \
  -d "{\"processTaskId\": \"$TASK2\", \"operator\": \"random\", \"targetUserId\": \"boss\"}" | jq -r '.code')
assert_eq "1023 §69 invalid operator" "$CODE" "99999999"

# ============= §40 P0 - surrogate 真实生效 =============
echo "=== BDD #1031: §40 surrogate 生效 ==="
INST=$(start_inst user1 | jq -r '.data.processInstanceId')
TASK=$(get_task "$INST")
# 创建 surrogate
SUR=$(curl -s -X POST $HOST/wf/processSurrogate/save \
  -H "Content-Type: application/json" \
  -d '{"operator": "leader", "surrogate": "manager"}' | jq -r '.data.id')
# manager 代办
CODE=$(curl -s -X POST $HOST/wf/processTask/execute \
  -H "Content-Type: application/json" \
  -d "{\"processTaskId\": \"$TASK\", \"operator\": \"manager\", \"submitType\": 1}" | jq -r '.code')
assert_eq "1031 §40 surrogate execute" "$CODE" "0"

# ============= §46 P0 - decisionHandler =============
echo "=== BDD #1041-#1042: §46 decisionHandler ==="
DESIGN=$(curl -s -X POST $HOST/wf/processDesign/save \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat /tmp/test-decision-handler.json)" '{name: "test-decision-handler", displayName: "decisionHandler 测试", content: $c}')" | jq -r '.data.id')
DEF2=$(curl -s -X POST $HOST/wf/processDesign/deploy \
  -H "Content-Type: application/json" -d "{\"id\": $DESIGN}" | jq -r '.data.processDefineId')

# 1041 低额 → end
INST_LOW=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute \
  -H "Content-Type: application/json" \
  -d "{\"processDefineId\": $DEF2, \"operator\": \"user1\", \"amount\": 5000}" | jq -r '.data.processInstanceId')
STATE=$(curl -s -X POST $HOST/wf/processInstance/detail \
  -H "Content-Type: application/json" -d "{\"id\": \"$INST_LOW\"}" | jq -r '.data.state')
assert_eq "1041 §46 low amount → end state=20" "$STATE" "20"

# 1042 高额 → task1
INST_HIGH=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute \
  -H "Content-Type: application/json" \
  -d "{\"processDefineId\": $DEF2, \"operator\": \"user1\", \"amount\": 20000}" | jq -r '.data.processInstanceId')
STATE=$(curl -s -X POST $HOST/wf/processInstance/detail \
  -H "Content-Type: application/json" -d "{\"id\": \"$INST_HIGH\"}" | jq -r '.data.state')
assert_eq "1042 §46 high amount → task1 state=10" "$STATE" "10"

# ============= §16 P0 - custom node =============
echo "=== BDD #1051: §16 custom 节点 ==="
DESIGN=$(curl -s -X POST $HOST/wf/processDesign/save \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat flows/08-custom-node.json)" '{name: "08-custom-node", displayName: "自定义节点", content: $c}')" | jq -r '.data.id')
DEF3=$(curl -s -X POST $HOST/wf/processDesign/deploy \
  -H "Content-Type: application/json" -d "{\"id\": $DESIGN}" | jq -r '.data.processDefineId')
INST=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute \
  -H "Content-Type: application/json" \
  -d "{\"processDefineId\": $DEF3, \"operator\": \"user1\"}" | jq -r '.data.processInstanceId')
RESULT=$(curl -s -X POST $HOST/wf/processInstance/detail \
  -H "Content-Type: application/json" -d "{\"id\": \"$INST\"}" | jq -r '.data.variables.customResult')
assert_eq "1051 §16 customResult" "$RESULT" "param1"

# ============= verify 规则 =============
echo "=== BDD #1061-#1064: verify 新规则 (单元测试) ==="
VERIFY_OUT=$(.venv/bin/python -c "
import sys; sys.path.insert(0, 'vendor')
from jeeflow.verify import verify_flow
# E012: custom 无 clazz
f = {'name':'t1','nodes':[{'id':'start','type':'snaker:start','properties':{}},{'id':'c','type':'snaker:custom','properties':{}},{'id':'end','type':'snaker:end','properties':{}}],'edges':[{'id':'e0','sourceNodeId':'start','targetNodeId':'c'},{'id':'e1','sourceNodeId':'c','targetNodeId':'end'}]}
e,w,p = verify_flow(f)
print('E012' in [x.code for x in e])
")
assert_eq "1061 verify E012" "$VERIFY_OUT" "True"

VERIFY_OUT=$(.venv/bin/python -c "
import sys; sys.path.insert(0, 'vendor')
from jeeflow.verify import verify_flow
# W011: custom val 空
f = {'name':'t2','nodes':[{'id':'start','type':'snaker:start','properties':{}},{'id':'c','type':'snaker:custom','properties':{'clazz':'X'}},{'id':'end','type':'snaker:end','properties':{}}],'edges':[{'id':'e0','sourceNodeId':'start','targetNodeId':'c'},{'id':'e1','sourceNodeId':'c','targetNodeId':'end'}]}
e,w,p = verify_flow(f)
print('W011' in [x.code for x in w])
")
assert_eq "1062 verify W011" "$VERIFY_OUT" "True"

VERIFY_OUT=$(.venv/bin/python -c "
import sys; sys.path.insert(0, 'vendor')
from jeeflow.verify import verify_flow
# E013: decisionHandler 格式非法
f = {'name':'t3','nodes':[{'id':'start','type':'snaker:start','properties':{}},{'id':'d','type':'snaker:decision','properties':{'decisionHandler':'bad name'}},{'id':'end','type':'snaker:end','properties':{}}],'edges':[{'id':'e0','sourceNodeId':'start','targetNodeId':'d'},{'id':'e1','sourceNodeId':'d','targetNodeId':'end'}]}
e,w,p = verify_flow(f)
print('E013' in [x.code for x in e])
")
assert_eq "1063 verify E013" "$VERIFY_OUT" "True"

VERIFY_OUT=$(.venv/bin/python -c "
import sys; sys.path.insert(0, 'vendor')
from jeeflow.verify import verify_flow
# W010: decision 无 expr 且无 decisionHandler
f = {'name':'t4','nodes':[{'id':'start','type':'snaker:start','properties':{}},{'id':'d','type':'snaker:decision','properties':{}},{'id':'end','type':'snaker:end','properties':{}}],'edges':[{'id':'e0','sourceNodeId':'start','targetNodeId':'d'},{'id':'e1','sourceNodeId':'d','targetNodeId':'end','properties':{}}]}
e,w,p = verify_flow(f)
print('W010' in [x.code for x in w])
")
assert_eq "1064 verify W010" "$VERIFY_OUT" "True"

# 输出
echo ""
echo "==================== 测试结果 ===================="
echo "PASS: $PASS"
echo "FAIL: $FAIL"
echo "=================================================="
printf "$RESULTS\n"
