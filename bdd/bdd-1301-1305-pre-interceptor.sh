#!/bin/bash
# BDD #1301-#1305: §6.1.1 preInterceptors 字段生效 (FIX-T94 2026-09-20)
# 覆盖: preInterceptors 已注册/未注册/空字段

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

rm -f /tmp/jee-mock-audit.log
curl -s -X POST $HOST/api/reset >/dev/null

# === #1301: preInterceptors=PRE_ONE (已注册) 启动成功 ===
DESIGN=$(curl -s -X POST $HOST/wf/processDesign/save -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat /tmp/test-pre-interceptor.json)" '{name:"pre-ok",displayName:"preOk",content:$c}')" | jq -r '.data.id')
DEF=$(curl -s -X POST $HOST/wf/processDesign/deploy -H "Content-Type: application/json" -d "{\"id\": $DESIGN}" | jq -r '.data.processDefineId')
CODE=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" -d "{\"processDefineId\": $DEF, \"operator\": \"user1\"}" | jq -r '.code')
assert_eq "1301 preInterceptors=PRE_ONE 启动 code=0" "$CODE" "0"

# === #1302: pre_handle 被调用 ===
PRE_CNT=$(grep -c "^PRE  PRE_ONE" /tmp/jee-mock-audit.log 2>/dev/null || echo 0)
[ "$PRE_CNT" -gt 0 ] && assert_eq "1302 pre_handle 被调用 (审计 PRE 行数 ≥1, 实测 $PRE_CNT)" "yes" "yes" || assert_eq "1302 pre_handle 被调用" "no" "yes"

# === #1303: preInterceptors=PRE_UNKNOWN (未注册) 启动失败 ===
cat > /tmp/test-pre-unknown.json << 'EOF'
{
  "name": "test-pre-unknown",
  "displayName": "preUnknown",
  "preInterceptors": "PRE_UNKNOWN",
  "nodes": [
    {"id": "start", "type": "snaker:start", "properties": {}},
    {"id": "apply", "type": "snaker:task", "properties": {"assignee": "user1"}},
    {"id": "end", "type": "snaker:end", "properties": {}}
  ],
  "edges": [
    {"id": "e0", "sourceNodeId": "start", "targetNodeId": "apply"},
    {"id": "e1", "sourceNodeId": "apply", "targetNodeId": "end"}
  ]
}
EOF
curl -s -X POST $HOST/api/reset >/dev/null
DESIGN2=$(curl -s -X POST $HOST/wf/processDesign/save -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat /tmp/test-pre-unknown.json)" '{name:"pre-unknown",displayName:"PU",content:$c}')" | jq -r '.data.id')
DEF2=$(curl -s -X POST $HOST/wf/processDesign/deploy -H "Content-Type: application/json" -d "{\"id\": $DESIGN2}" | jq -r '.data.processDefineId')
RESP=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" -d "{\"processDefineId\": $DEF2, \"operator\": \"user1\"}")
CODE=$(echo "$RESP" | jq -r '.code')
MSG=$(echo "$RESP" | jq -r '.msg')
assert_eq "1303 preInterceptors=PRE_UNKNOWN 未注册 code=99999999" "$CODE" "99999999"
echo "$MSG" | grep -q "PRE_UNKNOWN" && assert_eq "1304 错误消息包含 PRE_UNKNOWN" "match" "match" || assert_eq "1304 错误消息包含 PRE_UNKNOWN" "no" "match"

# === #1305: preInterceptors="" (空字符串) 不报错 ===
cat > /tmp/test-pre-empty.json << 'EOF'
{
  "name": "test-pre-empty",
  "displayName": "preEmpty",
  "preInterceptors": "",
  "nodes": [
    {"id": "start", "type": "snaker:start", "properties": {}},
    {"id": "apply", "type": "snaker:task", "properties": {"assignee": "user1"}},
    {"id": "end", "type": "snaker:end", "properties": {}}
  ],
  "edges": [
    {"id": "e0", "sourceNodeId": "start", "targetNodeId": "apply"},
    {"id": "e1", "sourceNodeId": "apply", "targetNodeId": "end"}
  ]
}
EOF
curl -s -X POST $HOST/api/reset >/dev/null
DESIGN3=$(curl -s -X POST $HOST/wf/processDesign/save -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat /tmp/test-pre-empty.json)" '{name:"pre-empty",displayName:"PE",content:$c}')" | jq -r '.data.id')
DEF3=$(curl -s -X POST $HOST/wf/processDesign/deploy -H "Content-Type: application/json" -d "{\"id\": $DESIGN3}" | jq -r '.data.processDefineId')
CODE=$(curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" -d "{\"processDefineId\": $DEF3, \"operator\": \"user1\"}" | jq -r '.code')
assert_eq "1305 preInterceptors='' 启动 code=0" "$CODE" "0"

echo "=========================================="
echo "BDD §6.1.1 preInterceptors 生效："
echo "  PASS=$PASS  FAIL=$FAIL"
echo "=========================================="
echo -e "$RESULTS"
[ $FAIL -eq 0 ] && exit 0 || exit 1
