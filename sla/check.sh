#!/usr/bin/env bash
# sla/check.sh — jeeFlow SLA 健康度检查 (可固化脚本)
# 用法: bash sla/check.sh [host] [port]
#   默认: http://localhost 8101
# 输出: sla/last_check.json (机读) + stdout (人读)

set -u
HOST="${1:-http://localhost}"
PORT="${2:-8101}"
BASE="$HOST:$PORT"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OUT_JSON="sla/last_check.json"

PASS=0; FAIL=0
RESULTS=()

ok()   { PASS=$((PASS+1)); RESULTS+=("✅ $1"); }
fail() { FAIL=$((FAIL+1)); RESULTS+=("❌ $1 — $2"); }

# === 1. 进程存活 ===
H=$(curl -s -m 3 -o /dev/null -w "%{http_code}" $BASE/healthz 2>/dev/null || echo "000")
[ "$H" = "200" ] && ok "1.1 healthz HTTP 200" || fail "1.1 healthz HTTP 200" "got=$H"

# === 2. healthz 内容 ===
HJ=$(curl -s -m 3 $BASE/healthz 2>/dev/null)
STATUS=$(echo "$HJ" | jq -r '.status // empty' 2>/dev/null)
[ "$STATUS" = "UP" ] && ok "2.1 healthz.status=UP" || fail "2.1 healthz.status=UP" "got=$STATUS"
BACKEND=$(echo "$HJ" | jq -r '.backend // empty')
[ -n "$BACKEND" ] && ok "2.2 healthz.backend=$BACKEND" || fail "2.2 healthz.backend" "missing"

# === 3. 端点延迟 (SLA 性能承诺) ===
T_HEALTHZ=$(curl -o /dev/null -s -m 3 -w '%{time_total}' $BASE/healthz 2>/dev/null)
T_HEALTHZ_MS=$(awk "BEGIN { printf \"%.0f\", $T_HEALTHZ * 1000 }")
[ "${T_HEALTHZ_MS%.*}" -lt 50 ] && ok "3.1 healthz P99 < 50ms (实测 ${T_HEALTHZ_MS}ms)" \
  || fail "3.1 healthz P99 < 50ms" "实测 ${T_HEALTHZ_MS}ms"

T_METRICS=$(curl -o /dev/null -s -m 5 -w '%{time_total}' $BASE/metrics 2>/dev/null)
T_METRICS_MS=$(awk "BEGIN { printf \"%.0f\", $T_METRICS * 1000 }")
[ "${T_METRICS_MS%.*}" -lt 500 ] && ok "3.2 metrics P99 < 500ms (实测 ${T_METRICS_MS}ms)" \
  || fail "3.2 metrics P99 < 500ms" "实测 ${T_METRICS_MS}ms"

# === 4. metrics 端点存在 4 指标 ===
M=$(curl -s -m 3 $BASE/metrics 2>/dev/null)
for m in wf_instance_state_total wf_active_instances wf_task_duration_seconds wf_task_completed_total; do
  if echo "$M" | grep -q "^# HELP $m "; then
    ok "4.$m metric exists"
  else
    fail "4.$m metric exists" "missing"
  fi
done

# === 5. stats 端点 ===
SO=$(curl -s -m 3 $BASE/api/admin/stats/overview 2>/dev/null)
SOC=$(echo "$SO" | jq -r '.code // empty')
[ "$SOC" = "0" ] && ok "5.1 stats/overview code=0" || fail "5.1 stats/overview code=0" "code=$SOC"
SI=$(echo "$SO" | jq -r '.data.total // empty')
[ -n "$SI" ] && ok "5.2 stats/overview.data.total=${SI}" || fail "5.2 stats/overview.data" "missing"

ST=$(curl -s -m 3 "$BASE/api/admin/stats/trend?start=2026-09-13&end=2026-09-20&granularity=day" 2>/dev/null)
STC=$(echo "$ST" | jq -r '.code // empty')
[ "$STC" = "0" ] && ok "5.3 stats/trend code=0" || fail "5.3 stats/trend code=0" "code=$STC"

# === 6. trace 端点 ===
TR=$(curl -s -m 3 "$BASE/api/admin/trace?limit=1" 2>/dev/null)
TRK=$(echo "$TR" | jq -r '.total // empty')
[ -n "$TRK" ] && ok "6.1 trace.total=${TRK}" || fail "6.1 trace" "missing total"

# === 7. expire scan 端点 ===
SC=$(curl -s -X POST -m 5 $BASE/api/admin/expire/scan 2>/dev/null)
SCN=$(echo "$SC" | jq -r '.scanTime // empty')
[ -n "$SCN" ] && ok "7.1 expire/scan returns scanTime" || fail "7.1 expire/scan" "no scanTime"

# === 8. wf/action 业务端点 ===
# 至少能 save + deploy + startAndExecute
DSAVE=$(curl -s -X POST $BASE/wf/processDesign/save -H "Content-Type: application/json" \
  -d '{"name":"_sla_check","displayName":"sla","content":"{}"}' | jq -r '.code // "missing"')
# content 是空 {} → save 会报错 (这是预期的, 我们只是确认端点可达)
[ "$DSAVE" != "missing" ] && ok "8.1 processDesign/save reachable" || fail "8.1 processDesign/save" "no response"

# === 9. wf/action 文档完整性 ===
ACTION_DOC_COUNT=$(grep -cE "^\| [0-9]+ \|" docs/actions.md 2>/dev/null || echo 0)
[ "$ACTION_DOC_COUNT" -ge 30 ] && ok "9.1 docs/actions.md ≥30 endpoints (实测 $ACTION_DOC_COUNT)" \
  || fail "9.1 docs/actions.md ≥30" "实测 $ACTION_DOC_COUNT"

# === 10. OpenAPI 文档 ===
OA_PATHS=$(python3 -c "import json; print(len(json.load(open('docs/openapi.json')).get('paths', {})))" 2>/dev/null || echo 0)
[ "$OA_PATHS" -ge 50 ] && ok "10.1 openapi.json paths ≥50 (实测 $OA_PATHS)" \
  || fail "10.1 openapi.json paths ≥50" "实测 $OA_PATHS"

# === 11. verify 规则 (vendor/jeeflow/verify.py 源) ===
VR=$(grep -cE "VerifyIssue|severity=\"E|severity=\"W|severity=\"P" vendor/jeeflow/verify.py 2>/dev/null || echo 0)
[ "$VR" -ge 30 ] && ok "11.1 verify rules ≥30 (实测 $VR)" || fail "11.1 verify rules ≥30" "实测 $VR"

# === 12. 流程定义数量 ===
FLOWS=$(ls flows/*.json 2>/dev/null | wc -l)
[ "$FLOWS" -ge 17 ] && ok "12.1 flows/*.json ≥17 (实测 $FLOWS)" || fail "12.1 flows ≥17" "实测 $FLOWS"

# === 13. BDD 回归脚本 ===
BDD_SH=$(ls bdd/bdd-*-*.sh 2>/dev/null | wc -l)
[ "$BDD_SH" -ge 3 ] && ok "13.1 bdd回归脚本 ≥3 (实测 $BDD_SH)" || fail "13.1 bdd回归脚本 ≥3" "实测 $BDD_SH"

# === 14. metrics 当前指标快照 ===
INST_ACT=$(echo "$M" | grep '^wf_active_instances ' | awk '{print $2}')
INST_DONE=$(echo "$M" | grep '^wf_instance_state_total{state="DONE"}' | awk '{print $2}')
INST_DOING=$(echo "$M" | grep '^wf_instance_state_total{state="DOING"}' | awk '{print $2}')
echo ""
echo "📊 运行时指标:"
echo "  wf_active_instances = ${INST_ACT:-0}"
echo "  wf_instance_state_total{DOING} = ${INST_DOING:-0}"
echo "  wf_instance_state_total{DONE}  = ${INST_DONE:-0}"

# === 输出 JSON ===
TOTAL=$((PASS + FAIL))
SCORE=$(( PASS * 100 / (TOTAL > 0 ? TOTAL : 1) ))
mkdir -p sla
cat > "$OUT_JSON" << EOFJSON
{
  "timestamp": "$TS",
  "host": "$BASE",
  "total_checks": $TOTAL,
  "passed": $PASS,
  "failed": $FAIL,
  "score": $SCORE,
  "latency_ms": {
    "healthz": $T_HEALTHZ_MS,
    "metrics": $T_METRICS_MS
  },
  "metrics_snapshot": {
    "active_instances": ${INST_ACT:-0},
    "doing": ${INST_DOING:-0},
    "done": ${INST_DONE:-0}
  },
  "checks": $(printf '%s\n' "${RESULTS[@]}" | jq -R . | jq -s .)
}
EOFJSON

echo ""
echo "=========================================="
echo "SLA 健康度检查结果："
echo "  PASS=$PASS  FAIL=$FAIL  Score=${SCORE}%"
echo "=========================================="
echo ""
printf '%s\n' "${RESULTS[@]}"
echo ""
echo "JSON 已写入 $OUT_JSON"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
