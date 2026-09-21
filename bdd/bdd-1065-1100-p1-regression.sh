#!/bin/bash
# BDD #1065-#1100: roadmap 2.1 P1 + TDD 16/17 端到端 (2026-09-20)
# 覆盖：§36 §61 + TDD 16/17 + transfer/comment/extra + surrogate + decisionHandler

# set -e (allow continue on error)
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

# 部署 simple (用于 §61/ccList + §36/interceptor + transfer/comment/extra)
DESIGN_S=$(curl -s -X POST $HOST/wf/processDesign/save \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat flows/01-simple.json)" '{name: "simple", displayName: "简单审批", content: $c}')" | jq -r '.data.id')
DEF_S=$(curl -s -X POST $HOST/wf/processDesign/deploy \
  -H "Content-Type: application/json" -d "{\"id\": $DESIGN_S}" | jq -r '.data.processDefineId')
echo "DEF_S=$DEF_S"

# 部署 delegate-test
DESIGN_D=$(curl -s -X POST $HOST/wf/processDesign/save \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat flows/16-delegate-test.json)" '{name: "delegate-test", displayName: "委派测试", content: $c}')" | jq -r '.data.id')
DEF_D=$(curl -s -X POST $HOST/wf/processDesign/deploy \
  -H "Content-Type: application/json" -d "{\"id\": $DESIGN_D}" | jq -r '.data.processDefineId')
echo "DEF_D=$DEF_D"

# 部署 suspend-resume-test
DESIGN_R=$(curl -s -X POST $HOST/wf/processDesign/save \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat flows/17-suspend-resume-test.json)" '{name: "suspend-resume-test", displayName: "挂起恢复", content: $c}')" | jq -r '.data.id')
DEF_R=$(curl -s -X POST $HOST/wf/processDesign/deploy \
  -H "Content-Type: application/json" -d "{\"id\": $DESIGN_R}" | jq -r '.data.processDefineId')
echo "DEF_R=$DEF_R"

# 部署 decisionHandler 测试
DESIGN_DH=$(curl -s -X POST $HOST/wf/processDesign/save \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat /tmp/test-decision-handler.json)" '{name: "test-dh", displayName: "DH", content: $c}')" | jq -r '.data.id')
DEF_DH=$(curl -s -X POST $HOST/wf/processDesign/deploy \
  -H "Content-Type: application/json" -d "{\"id\": $DESIGN_DH}" | jq -r '.data.processDefineId')
echo "DEF_DH=$DEF_DH"

start_simple() { curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" -d "{\"processDefineId\": $DEF_S, \"operator\": \"$1\"$2}" | jq -r '.data.processInstanceId'; }
start_delegate() { curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" -d "{\"processDefineId\": $DEF_D, \"operator\": \"$1\"$2}" | jq -r '.data.processInstanceId'; }
start_resume() { curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" -d "{\"processDefineId\": $DEF_R, \"operator\": \"$1\"$2}" | jq -r '.data.processInstanceId'; }
start_dh() { curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" -d "{\"processDefineId\": $DEF_DH, \"operator\": \"$1\", \"amount\": $2}" | jq -r '.data.processInstanceId'; }

# ========== BDD #1065-#1067: §61 ccList ==========
echo "=== BDD #1065-#1067: §61 ccList ==="
INST1=$(start_simple user1 ',"f_ccActors":"observer1"')
INST2=$(start_simple user2 ',"f_ccActors":"observer1"')
TOTAL=$(curl -s -X POST $HOST/wf/processInstance/ccList -H "Content-Type: application/json" -d '{"operator": "observer1", "pageSize": 100}' | jq -r '.data.recordCount')
assert_eq "1065 ccList no filter recordCount" "$TOTAL" "2"
TOTAL=$(curl -s -X POST $HOST/wf/processInstance/ccList -H "Content-Type: application/json" -d "{\"operator\": \"observer1\", \"processInstanceId\": \"$INST1\", \"pageSize\": 100}" | jq -r '.data.recordCount')
assert_eq "1066 ccList INST1 recordCount" "$TOTAL" "1"
ROW_ID=$(curl -s -X POST $HOST/wf/processInstance/ccList -H "Content-Type: application/json" -d "{\"operator\": \"observer1\", \"processInstanceId\": \"$INST2\", \"pageSize\": 100}" | jq -r '.data.rows[0].id')
assert_eq "1067 ccList INST2 id" "$ROW_ID" "$INST2"

# ========== BDD #1070-#1072: §36 interceptor ==========
echo "=== BDD #1070-#1072: §36 interceptor ==="
DESIGN_IC=$(curl -s -X POST $HOST/wf/processDesign/save \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat /tmp/test-ic-flow.json)" '{name: "test-ic-missing", displayName: "拦截器测试", content: $c}')" | jq -r '.data.id')
DEF_IC=$(curl -s -X POST $HOST/wf/processDesign/deploy \
  -H "Content-Type: application/json" -d "{\"id\": $DESIGN_IC}" | jq -r '.data.processDefineId')
CODE=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" -d "{\"processDefineId\": $DEF_IC, \"operator\": \"user1\"}" | jq -r '.code')
assert_eq "1070 §36 unknown interceptor code" "$CODE" "99999999"
MSG=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" -d "{\"processDefineId\": $DEF_IC, \"operator\": \"user1\"}" | jq -r '.msg')
if [[ "$MSG" == *"NON_EXIST_ONE"* ]]; then assert_eq "1071 §36 msg contains name" "match" "match"; else assert_eq "1071 §36 msg contains name" "$MSG" "should contain NON_EXIST_ONE"; fi
DESIGN_IC2=$(curl -s -X POST $HOST/wf/processDesign/save -H "Content-Type: application/json" -d "$(jq -n --arg c "$(jq '. + {postInterceptors:"POST_ONE"}' /tmp/test-ic-flow.json)" '{name: "test-ic-ok", displayName: "OK", content: $c}')" | jq -r '.data.id')
DEF_IC2=$(curl -s -X POST $HOST/wf/processDesign/deploy -H "Content-Type: application/json" -d "{\"id\": $DESIGN_IC2}" | jq -r '.data.processDefineId')
CODE=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" -d "{\"processDefineId\": $DEF_IC2, \"operator\": \"user1\"}" | jq -r '.code')
assert_eq "1072 §36 registered interceptor code" "$CODE" "0"

# ========== BDD #1075-#1079: TDD 16 delegate ==========
echo "=== BDD #1075-#1079: TDD 16 delegate ==="
INST=$(start_delegate user1)
TASK=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\": \"$INST\"}" | jq -r '.data.tasks[] | select(.taskName=="leader_approve") | .id')
TARGET=$(curl -s -X POST $HOST/wf/processTask/delegate -H "Content-Type: application/json" -d "{\"processTaskId\": \"$TASK\", \"operator\": \"leader\", \"targetUserId\": \"boss\"}" | jq -r '.data.to')
assert_eq "1075 delegate to" "$TARGET" "boss"
ACTORS=$(curl -s -X POST $HOST/wf/processTask/delegate -H "Content-Type: application/json" -d "{\"processTaskId\": \"$TASK\", \"operator\": \"leader\", \"targetUserId\": \"boss2\"}" | jq -r '.data.actors | sort | join(",")')
assert_eq "1076 delegate actors sorted" "$ACTORS" "boss,boss2,leader"

INST2=$(start_delegate user1)
TASK2=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\": \"$INST2\"}" | jq -r '.data.tasks[] | select(.taskName=="leader_approve") | .id')
curl -s -X POST $HOST/wf/processTask/delegate -H "Content-Type: application/json" -d "{\"processTaskId\": \"$TASK2\", \"operator\": \"leader\", \"targetUserId\": \"boss\"}" >/dev/null
CODE=$(curl -s -X POST $HOST/wf/processTask/execute -H "Content-Type: application/json" -d "{\"processTaskId\": \"$TASK2\", \"operator\": \"boss\", \"submitType\": 1}" | jq -r '.code')
assert_eq "1077 delegate execute code" "$CODE" "0"

INST3=$(start_delegate user1)
TASK3=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\": \"$INST3\"}" | jq -r '.data.tasks[] | select(.taskName=="leader_approve") | .id')
CODE=$(curl -s -X POST $HOST/wf/processTask/delegate -H "Content-Type: application/json" -d "{\"processTaskId\": \"$TASK3\", \"operator\": \"randomUser\", \"targetUserId\": \"x\"}" | jq -r '.code')
assert_eq "1078 delegate invalid operator code" "$CODE" "99999999"

INST4=$(start_delegate user1)
TASK4=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\": \"$INST4\"}" | jq -r '.data.tasks[] | select(.taskName=="leader_approve") | .id')
curl -s -X POST $HOST/wf/processTask/delegate -H "Content-Type: application/json" -d "{\"processTaskId\": \"$TASK4\", \"operator\": \"leader\", \"targetUserId\": \"boss\"}" >/dev/null
curl -s -X POST $HOST/wf/processTask/execute -H "Content-Type: application/json" -d "{\"processTaskId\": \"$TASK4\", \"operator\": \"boss\", \"submitType\": 1}" >/dev/null
STATE=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\": \"$INST4\"}" | jq -r '.data.state')
assert_eq "1079 delegate complete state=20" "$STATE" "20"

# ========== BDD #1080-#1084: TDD 17 suspend/resume ==========
echo "=== BDD #1080-#1084: TDD 17 suspend/resume ==="
INST=$(start_resume user1)
S=$(curl -s -X POST $HOST/wf/processInstance/suspend -H "Content-Type: application/json" -d "{\"id\": \"$INST\"}" | jq -r '.data.state')
assert_eq "1080 suspend state=50" "$S" "50"
S=$(curl -s -X POST $HOST/wf/processInstance/resume -H "Content-Type: application/json" -d "{\"id\": \"$INST\"}" | jq -r '.data.state')
assert_eq "1081 resume state=10" "$S" "10"

TASK=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\": \"$INST\"}" | jq -r '.data.tasks[] | select(.taskName=="leader_approve") | .id')
curl -s -X POST $HOST/wf/processInstance/suspend -H "Content-Type: application/json" -d "{\"id\": \"$INST\"}" >/dev/null
CODE=$(curl -s -X POST $HOST/wf/processTask/execute -H "Content-Type: application/json" -d "{\"processTaskId\": \"$TASK\", \"operator\": \"leader\", \"submitType\": 1}" | jq -r '.code')
assert_eq "1082 suspended execute code" "$CODE" "99999999"

curl -s -X POST $HOST/wf/processInstance/resume -H "Content-Type: application/json" -d "{\"id\": \"$INST\"}" >/dev/null
CODE=$(curl -s -X POST $HOST/wf/processTask/execute -H "Content-Type: application/json" -d "{\"processTaskId\": \"$TASK\", \"operator\": \"leader\", \"submitType\": 1}" | jq -r '.code')
assert_eq "1083 resumed execute code" "$CODE" "0"

STATE=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\": \"$INST\"}" | jq -r '.data.tasks[] | select(.taskName=="leader_approve") | .taskState')
assert_eq "1084 leader_approve state=20" "$STATE" "20"

# ========== BDD #1085-#1089: transfer/comment/extra ==========
echo "=== BDD #1085-#1089: transfer/comment/extra ==="
INST=$(start_simple user1)
TASK=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\": \"$INST\"}" | jq -r '.data.tasks[] | select(.taskName=="task1" and .taskState==10) | .id')
NA=$(curl -s -X POST $HOST/wf/processTask/transfer -H "Content-Type: application/json" -d "{\"processTaskId\": \"$TASK\", \"operator\": \"leader\", \"targetUserId\": \"leader2\"}" | jq -r '.data.newActors[0]')
assert_eq "1085 transfer new actor" "$NA" "leader2"
COUNT=$(curl -s -X POST $HOST/wf/processTask/comment -H "Content-Type: application/json" -d "{\"processTaskId\": \"$TASK\", \"operator\": \"leader2\", \"comment\": \"BDD1086\"}" | jq -r '.data.count')
assert_eq "1086 comment count" "$COUNT" "1"
COUNT=$(curl -s -X POST $HOST/wf/processTask/comment -H "Content-Type: application/json" -d "{\"processTaskId\": \"$TASK\", \"operator\": \"leader2\", \"comment\": \"BDD1087\"}" | jq -r '.data.count')
assert_eq "1087 comment count 2nd" "$COUNT" "2"
URG=$(curl -s -X POST $HOST/wf/processTask/extra -H "Content-Type: application/json" -d "{\"processTaskId\": \"$TASK\", \"operator\": \"leader2\", \"urgency\": \"low\"}" | jq -r '.data.extra.urgency')
assert_eq "1088 extra urgency" "$URG" "low"
EXTRA=$(curl -s -X POST $HOST/wf/processTask/extra -H "Content-Type: application/json" -d "{\"processTaskId\": \"$TASK\", \"operator\": \"leader2\", \"x\": 1, \"y\": \"v\"}" | jq -r '.data.extra | tostring')
if [[ "$EXTRA" == *"\"x\":1"* && "$EXTRA" == *"\"y\":\"v\""* ]]; then assert_eq "1089 extra multi fields" "match" "match"; else assert_eq "1089 extra multi fields" "$EXTRA" "should contain x:1 y:v"; fi

# ========== BDD #1090-#1093: surrogate ==========
echo "=== BDD #1090-#1093: §40 surrogate ==="
INST=$(start_simple user1)
TASK=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\": \"$INST\"}" | jq -r '.data.tasks[] | select(.taskName=="task1" and .taskState==10) | .id')
curl -s -X POST $HOST/wf/processSurrogate/save -H "Content-Type: application/json" -d '{"operator": "leader", "surrogate": "manager"}' >/dev/null
CODE=$(curl -s -X POST $HOST/wf/processTask/execute -H "Content-Type: application/json" -d "{\"processTaskId\": \"$TASK\", \"operator\": \"manager\", \"submitType\": 1}" | jq -r '.code')
assert_eq "1091 surrogate execute code" "$CODE" "0"

INST2=$(start_simple user1)
TASK2=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\": \"$INST2\"}" | jq -r '.data.tasks[] | select(.taskName=="task1" and .taskState==10) | .id')
CODE=$(curl -s -X POST $HOST/wf/processTask/execute -H "Content-Type: application/json" -d "{\"processTaskId\": \"$TASK2\", \"operator\": \"nobody\", \"submitType\": 1}" | jq -r '.code')
assert_eq "1092 unauthorized execute code" "$CODE" "99999999"

# ========== BDD #1094-#1096: decisionHandler ==========
echo "=== BDD #1094-#1096: §46 decisionHandler ==="
INST_LOW=$(start_dh user1 100)
S=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\": \"$INST_LOW\"}" | jq -r '.data.state')
assert_eq "1094 DH low=20" "$S" "20"
INST_HIGH=$(start_dh user1 99999)
S=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\": \"$INST_HIGH\"}" | jq -r '.data.state')
assert_eq "1095 DH high=10" "$S" "10"
INST_BD=$(start_dh user1 10000)
S=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\": \"$INST_BD\"}" | jq -r '.data.state')
assert_eq "1096 DH boundary=10" "$S" "10"

echo ""
echo "==================== 测试结果 ===================="
echo "PASS: $PASS"
echo "FAIL: $FAIL"
echo "=================================================="
printf "$RESULTS\n"
