#!/bin/bash
# BDD #1511-#1515: §7.2.2 双端 perf diff 报告 (FIX-T106 2026-09-20)
set +e
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

OUT=$(.venv/bin/python /tmp/perf_dual.py 2>&1)
echo "$OUT" > /tmp/perf_dual.log

# === #1511: 报告生成 ===
HAS_REPORT=$(echo "$OUT" | grep -c "平均 diff")
[ "$HAS_REPORT" -ge 1 ] && assert_eq "1511 双端 perf diff 报告生成" "yes" "yes" \
  || assert_eq "1511 报告生成" "no" "yes"

# === #1512-#1515: 端点覆盖 ===
for ep in "/healthz" "/metrics" "/api/admin/stats/overview" "/wf/processInstance/page"; do
  HAS=$(echo "$OUT" | grep -c "$ep")
  [ "$HAS" -ge 1 ] && assert_eq "1512 报告含 $ep" "yes" "yes" \
    || assert_eq "1512 报告含 $ep" "no" "yes"
done

echo "=========================================="
echo "BDD §7.2.2 双端 perf diff："
echo "  PASS=$PASS  FAIL=$FAIL"
echo "=========================================="
echo -e "$RESULTS"
[ $FAIL -eq 0 ] && exit 0 || exit 1
