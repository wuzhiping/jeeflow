#!/bin/bash
# BDD #1331-#1335: §6.5.1 1000 并发 instance 压测 (FIX-T100 2026-09-20)
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

OUT=$(.venv/bin/python /tmp/stress_1000.py 2>&1)
echo "$OUT" > /tmp/stress_1000.log

SUCCESS=$(echo "$OUT" | grep -oE "[0-9]+/1000 成功" | grep -oE "^[0-9]+")
P95=$(echo "$OUT" | grep -oE "实测 [0-9]+ms" | grep -oE "[0-9]+")
THROUGHPUT=$(echo "$OUT" | grep -oE "[0-9]+ instances/s" | grep -oE "^[0-9]+")

echo "SUCCESS=$SUCCESS P95=$P95 THROUGHPUT=$THROUGHPUT"

assert_eq "1331 1000/1000 全部成功" "$SUCCESS" "1000"

if [ -n "$P95" ] && [ "$P95" -lt 5000 ]; then
  assert_eq "1332 P95 < 5000ms (实测 ${P95}ms)" "ok" "ok"
else
  assert_eq "1332 P95 < 5000ms" "fail" "ok"
fi

if [ -n "$THROUGHPUT" ] && [ "$THROUGHPUT" -gt 100 ]; then
  assert_eq "1333 吞吐量 > 100 instances/s (实测 ${THROUGHPUT})" "ok" "ok"
else
  assert_eq "1333 吞吐量 > 100 instances/s" "$THROUGHPUT" "ok"
fi

# 总耗时 < 30s
TOTAL=$(echo "$OUT" | grep -oE "总耗时: [0-9.]+s" | grep -oE "[0-9.]+" | head -1)
if [ -n "$TOTAL" ]; then
  HIGH=$(python3 -c "print(int(float('$TOTAL') < 30))")
  [ "$HIGH" = "1" ] && assert_eq "1334 总耗时 < 30s (实测 ${TOTAL}s)" "ok" "ok" || assert_eq "1334 总耗时 < 30s" "$TOTAL" "ok"
fi

# 无异常
HAS_ERR=$(echo "$OUT" | grep -cE "Traceback|Error")
assert_eq "1335 无异常/traceback" "$HAS_ERR" "0"

echo "=========================================="
echo "BDD §6.5.1 1000 并发压测："
echo "  PASS=$PASS  FAIL=$FAIL"
echo "=========================================="
echo -e "$RESULTS"
[ $FAIL -eq 0 ] && exit 0 || exit 1
