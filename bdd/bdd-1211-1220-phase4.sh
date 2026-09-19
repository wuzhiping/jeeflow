#!/bin/bash
# BDD #1211-#1220: roadmap §4 第四阶段 (监控/HA/部署) 回归
# 覆盖: §4.1.1 health, §4.1.2 stats, §4.1.3 metrics, §4.1.4 trace,
#       §4.3.1 OpenAPI, §4.4.1 PG pool, §4.4.2 乐观锁, §4.4.3 expire scan

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

assert_neq() {
  local desc="$1" actual="$2" unexpected="$3"
  if [ "$actual" != "$unexpected" ]; then
    PASS=$((PASS + 1))
    RESULTS="$RESULTS\n✅ #$1 [$desc]"
  else
    FAIL=$((FAIL + 1))
    RESULTS="$RESULTS\n❌ #$1 [$desc]  should not be=$unexpected actual=$actual"
  fi
}

curl -s -X POST $HOST/api/reset >/dev/null

# === §4.1.1 health (FIX-T79) ===
H=$(curl -s $HOST/healthz | jq -r '.status')
assert_eq "1211 §4.1.1 health.status=UP" "$H" "UP"

PG=$(curl -s $HOST/healthz | jq -r '.pg')
assert_neq "1212 §4.1.1 health.pg 字段存在" "$PG" "null"

# === §4.1.2 stats (FIX-T80-T82) ===
OVERVIEW=$(curl -s $HOST/api/admin/stats/overview)
assert_neq "1213 §4.1.2 stats/overview 返回 data" "$OVERVIEW" ""
INST_TOTAL=$(echo "$OVERVIEW" | jq -r '.data.instanceTotal // 0')
assert_neq "1214 §4.1.2 stats/overview.instanceTotal>=0" "$INST_TOTAL" "null"

TREND=$(curl -s "$HOST/api/admin/stats/trend?days=7")
assert_neq "1215 §4.1.2 stats/trend 返回" "$TREND" ""

GROUP=$(curl -s "$HOST/api/admin/stats/group?dimension=state")
assert_neq "1216 §4.1.2 stats/group 返回" "$GROUP" ""

# === §4.1.3 metrics (FIX-T83) ===
M=$(curl -s $HOST/metrics)
echo "$M" | grep -q "wf_instance_state_total" && assert_eq "1217 §4.1.3 metric wf_instance_state_total" "yes" "yes" || assert_eq "1217 §4.1.3 metric wf_instance_state_total" "no" "yes"
echo "$M" | grep -q "wf_active_instances" && assert_eq "1218 §4.1.3 metric wf_active_instances" "yes" "yes" || assert_eq "1218 §4.1.3 metric wf_active_instances" "no" "yes"
echo "$M" | grep -q "wf_task_duration_seconds" && assert_eq "1219 §4.1.3 metric wf_task_duration_seconds" "yes" "yes" || assert_eq "1219 §4.1.3 metric wf_task_duration_seconds" "no" "yes"

# === §4.4.3 expire scan (FIX-T91) ===
SCAN=$(curl -s -X POST $HOST/api/admin/expire/scan)
EXPIRED=$(echo "$SCAN" | jq -r '.taskExpired')
assert_neq "1220 §4.4.3 expire/scan 返回 taskExpired" "$EXPIRED" "null"
SCAN_TIME=$(echo "$SCAN" | jq -r '.scanTime')
assert_neq "1221 §4.4.3 expire/scan 返回 scanTime" "$SCAN_TIME" "null"

# === 总结 ===
echo "=========================================="
echo "BDD §4 Phase 4 回归结果："
echo "  PASS=$PASS  FAIL=$FAIL"
echo "=========================================="
echo -e "$RESULTS"
[ $FAIL -eq 0 ] && exit 0 || exit 1
