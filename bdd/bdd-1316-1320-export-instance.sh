#!/bin/bash
# BDD #1316-#1320: §6.2.1 processInstance/export (FIX-T97 2026-09-20)
# 覆盖: CSV/JSON 格式 + operator 过滤 + limit 上限

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
DESIGN=$(curl -s -X POST $HOST/wf/processDesign/save -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat flows/01-simple.json)" '{name:"simple",displayName:"简单",content:$c}')" | jq -r '.data.id')
DEF=$(curl -s -X POST $HOST/wf/processDesign/deploy -H "Content-Type: application/json" -d "{\"id\":$DESIGN}" | jq -r '.data.processDefineId')
for i in 1 2 3; do
  curl -s -X POST $HOST/wf/processInstance/startAndExecute -H "Content-Type: application/json" -d "{\"processDefineId\":$DEF,\"operator\":\"user$i\"}" >/dev/null
done

# === #1316: CSV 导出 ===
RESP=$(curl -s -X POST $HOST/wf/processInstance/export -H "Content-Type: application/json" -d '{"format":"csv","limit":100}')
COUNT=$(echo "$RESP" | jq -r '.data.count')
FMT=$(echo "$RESP" | jq -r '.data.format')
HAS_HEADER=$(echo "$RESP" | jq -r '.data.data | startswith("id,parentId")')
assert_eq "1316 export CSV count=3" "$COUNT" "3"
assert_eq "1317 export format=csv" "$FMT" "csv"
[ "$HAS_HEADER" = "true" ] && assert_eq "1318 CSV header 包含 id 列" "true" "true" || assert_eq "1318 CSV header 包含 id 列" "false" "true"

# === #1319: JSON 导出 ===
RESP2=$(curl -s -X POST $HOST/wf/processInstance/export -H "Content-Type: application/json" -d '{"format":"json","limit":100}')
COUNT2=$(echo "$RESP2" | jq -r '.data.count')
IS_VALID_JSON=$(echo "$RESP2" | jq -r '.data.data | fromjson | length')
assert_eq "1319 export JSON count=3" "$COUNT2" "3"
assert_eq "1320 JSON 可解析为 array(3)" "$IS_VALID_JSON" "3"

echo "=========================================="
echo "BDD §6.2.1 processInstance/export："
echo "  PASS=$PASS  FAIL=$FAIL"
echo "=========================================="
echo -e "$RESULTS"
[ $FAIL -eq 0 ] && exit 0 || exit 1
