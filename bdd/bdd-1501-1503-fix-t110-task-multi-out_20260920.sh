#!/bin/bash
# BDD #1501-#1503: §110 FIX-T110 (2026-09-20) task 节点多出边隐式 fork 致实例提前 finish
# 覆盖: §110.1 W012 警告触发 / §110.2 v1 (坏设计) 复现 instance state=20 + cashier_pay DOING /
#       §110.3 v2 (decision 节点分隔) instance state=20 + cashier_pay DONE

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

# 找指定 instance 的 taskId（避免 todoList 返回其他实例）
get_task_for_inst() {
  local operator="$1" inst="$2"
  curl -s -X POST $HOST/wf/processTask/todoList -H "Content-Type: application/json" \
    -d "{\"operator\":\"$operator\",\"pageNum\":1,\"pageSize\":50}" \
    | jq -r --arg inst "$inst" '.data.rows[] | select(.processInstanceId==$inst) | .id' | head -1
}

curl -s -X POST $HOST/api/reset >/dev/null

# ─────────────────────────────────────────────────────────────────────
# §110.1 W012 警告触发 (Python 直测 verify_flow)
# ─────────────────────────────────────────────────────────────────────
echo "=== §110.1 W012 warning on multi-out-edge task ==="
W012_HITS=$(./.venv/bin/python3 -c "
from vendor.jeeflow.verify import verify_flow
import json
with open('tdd/expense_report_repro.json') as f:
    flow = json.load(f)
errors, warnings, patterns = verify_flow(flow)
print(sum(1 for w in warnings if w.code == 'W012'))
" 2>&1 | tail -1)
assert_eq "W012 fires on mgr_approve + dir_approve" "$W012_HITS" "2"

# ─────────────────────────────────────────────────────────────────────
# §110.2 v1 (坏设计) 复现
# ─────────────────────────────────────────────────────────────────────
echo "=== §110.2 v1 bad design: cashier execute fails with 99999999 ==="
DESIGN_V1=$(curl -s -X POST $HOST/wf/processDesign/save -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat tdd/expense_report_repro.json)" '{name:"expense_report_v1_bug",displayName:"v1坏设计",content:$c}')" | jq -r '.data.id')
DEF_V1=$(curl -s -X POST $HOST/wf/processDesign/deploy -H "Content-Type: application/json" -d "{\"id\":$DESIGN_V1}" | jq -r '.data.processDefineId')

INST_V1=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" \
  -d "{\"processDefineId\":$DEF_V1,\"operator\":\"user1\",\"assignees\":{\"apply\":\"user1\"},\"variables\":{\"submitType\":0,\"f_amount\":4800,\"u_userId\":\"user1\",\"u_realName\":\"张三\"}}" | jq -r '.data.processInstanceId')

MGR_V1=$(get_task_for_inst manager "$INST_V1")
curl -s -X POST $HOST/wf/processTask/execute -H "Content-Type: application/json" \
  -d "{\"processTaskId\":\"$MGR_V1\",\"submitType\":1,\"operator\":\"manager\"}" >/dev/null

STATE_AFTER_MGR=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
  -d "{\"id\":$INST_V1}" | jq -r '.data.state')
assert_eq "v1 instance state after mgr approve (BUG: 20 instead of 10)" "$STATE_AFTER_MGR" "20"

CASH_V1=$(get_task_for_inst cashier "$INST_V1")
EXEC_CODE_V1=$(curl -s -X POST $HOST/wf/processTask/execute -H "Content-Type: application/json" \
  -d "{\"processTaskId\":\"$CASH_V1\",\"submitType\":1,\"operator\":\"cashier\"}" | jq -r '.code')
assert_eq "v1 cashier execute returns 99999999 (BUG-1 signature)" "$EXEC_CODE_V1" "99999999"

# ─────────────────────────────────────────────────────────────────────
# §110.3 v2 (decision 分隔) 修复验证 — 每次 reset 避免残留
# ─────────────────────────────────────────────────────────────────────
echo "=== §110.3 v2 fix: cashier_pay executes correctly ==="

# §110.3.1 mgr path approve
curl -s -X POST $HOST/api/reset >/dev/null
DESIGN_V2=$(curl -s -X POST $HOST/wf/processDesign/save -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat tdd/expense_report_v2.json)" '{name:"expense_report_v2_fix",displayName:"v2修复",content:$c}')" | jq -r '.data.id')
DEF_V2=$(curl -s -X POST $HOST/wf/processDesign/deploy -H "Content-Type: application/json" -d "{\"id\":$DESIGN_V2}" | jq -r '.data.processDefineId')

INST_V2A=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" \
  -d "{\"processDefineId\":$DEF_V2,\"operator\":\"user1\",\"assignees\":{\"apply\":\"user1\"},\"variables\":{\"submitType\":0,\"f_amount\":4800,\"u_userId\":\"user1\",\"u_realName\":\"张三\"}}" | jq -r '.data.processInstanceId')

MGR_V2A=$(get_task_for_inst manager "$INST_V2A")
curl -s -X POST $HOST/wf/processTask/execute -H "Content-Type: application/json" \
  -d "{\"processTaskId\":\"$MGR_V2A\",\"submitType\":1,\"operator\":\"manager\",\"tf_mgr_decision\":1}" >/dev/null

STATE_AFTER_MGR_V2=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
  -d "{\"id\":$INST_V2A}" | jq -r '.data.state')
assert_eq "v2 instance state after mgr approve (DOING)" "$STATE_AFTER_MGR_V2" "10"

CASH_V2A=$(get_task_for_inst cashier "$INST_V2A")
EXEC_CODE_V2A=$(curl -s -X POST $HOST/wf/processTask/execute -H "Content-Type: application/json" \
  -d "{\"processTaskId\":\"$CASH_V2A\",\"submitType\":1,\"operator\":\"cashier\"}" | jq -r '.code')
assert_eq "v2 cashier execute returns 0" "$EXEC_CODE_V2A" "0"

STATE_FINAL_V2=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
  -d "{\"id\":$INST_V2A}" | jq -r '.data.state')
assert_eq "v2 final state DONE" "$STATE_FINAL_V2" "20"

# §110.3.2 mgr path reject (tf_mgr_decision=2)
INST_V2B=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" \
  -d "{\"processDefineId\":$DEF_V2,\"operator\":\"user1\",\"assignees\":{\"apply\":\"user1\"},\"variables\":{\"submitType\":0,\"f_amount\":4800,\"u_userId\":\"user1\",\"u_realName\":\"张三\"}}" | jq -r '.data.processInstanceId')

MGR_V2B=$(get_task_for_inst manager "$INST_V2B")
curl -s -X POST $HOST/wf/processTask/execute -H "Content-Type: application/json" \
  -d "{\"processTaskId\":\"$MGR_V2B\",\"submitType\":1,\"operator\":\"manager\",\"tf_mgr_decision\":2}" >/dev/null

STATE_V2B=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
  -d "{\"id\":$INST_V2B}" | jq -r '.data.state')
assert_eq "v2 mgr reject → end_rejected DONE" "$STATE_V2B" "20"

# §110.3.3 dir path approve (f_amount=8000)
INST_V2C=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" \
  -d "{\"processDefineId\":$DEF_V2,\"operator\":\"user1\",\"assignees\":{\"apply\":\"user1\"},\"variables\":{\"submitType\":0,\"f_amount\":8000,\"u_userId\":\"user1\",\"u_realName\":\"张三\"}}" | jq -r '.data.processInstanceId')

DIR_V2C=$(get_task_for_inst director "$INST_V2C")
curl -s -X POST $HOST/wf/processTask/execute -H "Content-Type: application/json" \
  -d "{\"processTaskId\":\"$DIR_V2C\",\"submitType\":1,\"operator\":\"director\",\"tf_dir_decision\":1}" >/dev/null

CASH_V2C=$(get_task_for_inst cashier "$INST_V2C")
EXEC_CODE_V2C=$(curl -s -X POST $HOST/wf/processTask/execute -H "Content-Type: application/json" \
  -d "{\"processTaskId\":\"$CASH_V2C\",\"submitType\":1,\"operator\":\"cashier\"}" | jq -r '.code')
assert_eq "v2 dir path cashier execute returns 0" "$EXEC_CODE_V2C" "0"

STATE_V2C=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
  -d "{\"id\":$INST_V2C}" | jq -r '.data.state')
assert_eq "v2 dir path final state DONE" "$STATE_V2C" "20"

# ─────────────────────────────────────────────────────────────────────
# 输出结果
# ─────────────────────────────────────────────────────────────────────
printf "$RESULTS\n"
echo ""
echo "═══════════════════════════════════════"
echo "  §110 FIX-T110 BDD: $PASS passed, $FAIL failed"
echo "═══════════════════════════════════════"
[ $FAIL -eq 0 ] && exit 0 || exit 1
