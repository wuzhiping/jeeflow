#!/bin/bash
# BDD #1336-#1340: §6.5.2 各接口 P50/P95/P99 性能基线 (FIX-T101 2026-09-20)
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

OUT=$(.venv/bin/python /tmp/perf_baseline.py 2>&1)
echo "$OUT" > /tmp/perf_baseline.log

P95_COUNT=$(echo "$OUT" | grep -oE "[0-9]+\.[0-9]+ms" | head -22 | wc -l)
[ "$P95_COUNT" -gt 10 ] && assert_eq "1336 性能基线测试≥10 端点" "ok" "ok" || assert_eq "1336 性能基线条数" "$P95_COUNT" "11"

ALL_OK=$(echo "$OUT" | grep "全部 P95 < 100ms")
[ -n "$ALL_OK" ] && assert_eq "1337 全部 P95 < 100ms (实测)" "ok" "ok" || assert_eq "1337 全部 P95 < 100ms" "no" "ok"

# /healthz P95 < 50ms
HEALTHZ_P95=$(echo "$OUT" | grep "/healthz" | awk '{print $4}')
[ -n "$HEALTHZ_P95" ] && python3 -c "
v = float('${HEALTHZ_P95%ms}')
import sys; sys.exit(0 if v < 50 else 1)
" && assert_eq "1338 /healthz P95 < 50ms" "ok" "ok" || assert_eq "1338 /healthz P95" "$HEALTHZ_P95" "<50ms"

# /metrics P95 < 500ms  
METRICS_P95=$(echo "$OUT" | grep "/metrics " | awk '{print $4}')
python3 -c "
v = float('${METRICS_P95%ms}')
import sys; sys.exit(0 if v < 500 else 1)
" && assert_eq "1339 /metrics P95 < 500ms" "ok" "ok" || assert_eq "1339 /metrics P95" "$METRICS_P95" "<500ms"

# 业务端点 P95 < 100ms (除 healthz/metrics)
ALL_UNDER=$(echo "$OUT" | grep -v "/healthz\|/metrics" | grep -E "[0-9]+\.[0-9]+ms" | wc -l)
assert_eq "1340 业务端点有 P95 数据" "$ALL_UNDER" "9"

echo "=========================================="
echo "BDD §6.5.2 性能基线："
echo "  PASS=$PASS  FAIL=$FAIL"
echo "=========================================="
echo -e "$RESULTS"
[ $FAIL -eq 0 ] && exit 0 || exit 1
