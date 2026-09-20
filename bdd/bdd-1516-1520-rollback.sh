#!/bin/bash
# BDD #1516-#1520: §7.3.1 流程回滚 (FIX-T107 2026-09-20)
# 覆盖: rollback 端点 + 状态变更 + task 废弃 + rollback_info
set +e
HOST=http://localhost:8101
PASS=0
FAIL=0
RESULTS=""

assert_eq() {
  local desc="$1" actual="$2" expected="$3"
  if [ "$actual" = "$expected" ]; then
    PASS=$((PASS + 1)); RESULTS="$RESULTS\n✅ #$1 [$desc]"
  else
    FAIL=$((FAIL + 1)); RESULTS="$RESULTS\n❌ #$1 [$desc]  expected=$expected actual=$actual"
  fi
}

curl -s -X POST $HOST/api/reset >/dev/null
D=$(curl -s -X POST $HOST/wf/processDesign/save -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat flows/01-simple.json)" '{name:"rollback-test",displayName:"r",content:$c}')" | jq -r '.data.id')
DEF=$(curl -s -X POST $HOST/wf/processDesign/deploy -H "Content-Type: application/json" -d "{\"id\":$D}" | jq -r '.data.processDefineId')
INST=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" -d "{\"processDefineId\":$DEF,\"operator\":\"user1\"}" | jq -r '.data.processInstanceId')
echo "INST=$INST"

# === #1516: rollback 端点 code=0 ===
RESP=$(curl -s -X POST $HOST/wf/processInstance/rollback -H "Content-Type: application/json" -d "{\"id\":$INST,\"toNodeName\":\"task1\",\"operator\":\"admin\"}")
CODE=$(echo "$RESP" | jq -r '.code // "missing"')
assert_eq "1516 rollback 端点 code=0" "$CODE" "0"

# === #1517: state=WITHDRAW (30) ===
STATE=$(echo "$RESP" | jq -r '.data.state')
assert_eq "1517 rollback 后 state=30 (WITHDRAW)" "$STATE" "30"

# === #1518: rollback_info 包含 toNodeName ===
TO_NODE=$(echo "$RESP" | jq -r '.data.rollback.toNodeName')
assert_eq "1518 rollback_info.toNodeName=task1" "$TO_NODE" "task1"

# === #1519: doing 任务被废弃 (state=99 ABANDONED) ===
sleep 0.5
TASK_STATE=$(curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" -d "{\"id\":$INST}" | jq '.data.tasks[] | select(.taskName=="task1") | .taskState')
assert_eq "1519 task1 状态=99 (ABANDONED)" "$TASK_STATE" "99"

# === #1520: 二次 rollback 应失败 (state != DOING) ===
RESP2=$(curl -s -X POST $HOST/wf/processInstance/rollback -H "Content-Type: application/json" -d "{\"id\":$INST,\"toNodeName\":\"task1\"}")
CODE2=$(echo "$RESP2" | jq -r '.code // "missing"')
assert_eq "1520 二次 rollback 失败 (state=WITHDRAW)" "$CODE2" "99999999"

echo "=========================================="
echo "BDD §7.3.1 流程回滚："
echo "  PASS=$PASS  FAIL=$FAIL"
echo "=========================================="
echo -e "$RESULTS"
[ $FAIL -eq 0 ] && exit 0 || exit 1
