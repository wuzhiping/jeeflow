#!/usr/bin/env bash
# sla/check_flows_dual.sh — 双端 flows/ 验证 (SLA.md v6 要求)
# 用法: bash sla/check_flows_dual.sh [mem_host:port] [pg_host:port]
#   默认: MEM=localhost:8101, PG=localhost:8102
# 输出: stdout (PASS/FAIL 计数 + 失败列表)

set -u
MEM="${1:-http://localhost:8101}"
PG="${2:-http://localhost:8102}"
EXPECTED="${EXPECTED_MIN_PASS:-17}"  # 至少 17/19 (排除 2 个需 SPI 测试环境的)

# 帮助函数
http_post() { curl -s -X POST -m 5 -H "Content-Type: application/json" -d "$2" "$1" 2>/dev/null; }
http_post_silent() { curl -s -X POST -m 5 "$1" >/dev/null 2>&1; }

run_backend() {
  local HOST=$1
  local LABEL=$2
  local PASS=0
  local FAIL=0
  local FAILED=""
  local TOTAL=0

  for f in flows/*.json; do
    TOTAL=$((TOTAL + 1))
    name=$(basename "$f" .json)
    # reset
    http_post_silent $HOST/api/reset
    # save
    D=$(http_post $HOST/wf/processDesign/save "$(jq -n --arg c "$(cat $f)" '{name:("_'$LABEL'_'$name'"),displayName:"'$name'",content:$c}')" | jq -r '.data.id // empty')
    if [ -z "$D" ]; then
      FAIL=$((FAIL+1)); FAILED="$FAILED $name(save)"; continue
    fi
    # deploy
    DEF=$(http_post $HOST/wf/processDesign/deploy "{\"id\":$D}" | jq -r '.data.processDefineId // empty')
    if [ -z "$DEF" ]; then
      FAIL=$((FAIL+1)); FAILED="$FAILED $name(deploy)"; continue
    fi
    # startAndExecute
    RESP=$(http_post $HOST/wf/processInstance/startAndExecute "{\"processDefineId\":$DEF,\"operator\":\"sla_tester\"}")
    CODE=$(echo "$RESP" | jq -r '.code // "missing"')
    if [ "$CODE" = "0" ]; then
      PASS=$((PASS+1))
    else
      FAIL=$((FAIL+1))
      FAILED="$FAILED $name(start=$CODE)"
    fi
  done
  echo "  $LABEL ($HOST): PASS=$PASS FAIL=$FAIL TOTAL=$TOTAL" 1>&2
  [ -n "$FAILED" ] && echo "    失败: $FAILED" 1>&2
  # 输出到 caller (stdout 只返回数字, 用 NUL 分隔)
  printf '%s\n%s\n' "$PASS" "$FAIL"
}

echo "═══════════════════════════════════════"
echo "jeeFlow SLA 双端 flows/ 验证"
echo "  MEM: $MEM"
echo "  PG:  $PG"
echo "═══════════════════════════════════════"

# MEM 端
echo ""
echo "MEM 端..."
RES=$(run_backend $MEM MEM)
MEM_PASS=$(echo "$RES" | head -1)
MEM_FAIL=$(echo "$RES" | tail -1)

# PG 端
echo ""
echo "PG 端..."
RES=$(run_backend $PG PG)
PG_PASS=$(echo "$RES" | head -1)
PG_FAIL=$(echo "$RES" | tail -1)

echo ""
echo "═══════════════════════════════════════"
echo "汇总: MEM=$MEM_PASS PASS / PG=$PG_PASS PASS"
echo "═══════════════════════════════════════"

# 双端一致性: 失败列表应该一致 (允许 expected pass >= EXPECTED)
[ "$MEM_PASS" -ge "$EXPECTED" ] && [ "$PG_PASS" -ge "$EXPECTED" ] && echo "✅ 双端双达 ≥$EXPECTED pass"
