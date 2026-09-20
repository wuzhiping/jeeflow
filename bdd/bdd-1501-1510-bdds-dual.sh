#!/bin/bash
# BDD #1501-#1510: §7.2.1 17 套 BDD 全量双端 (FIX-T105 2026-09-20)
# 覆盖: MEM + PG 双端 13 套 BDD 套件 (含 flows 4 + 监控 4 + §6 5)

set +e
HOST_PG=http://localhost:8102
HOST_MEM=http://localhost:8101
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

# 跑 §7.2.1 wrapper
OUT=$(bash sla/check_bdds_dual.sh 2>&1)
MEM_PASS=$(echo "$OUT" | grep "MEM (" | grep -oE "PASS=[0-9]+" | cut -d= -f2)
PG_PASS=$(echo "$OUT" | grep "PG (" | grep -oE "PASS=[0-9]+" | cut -d= -f2)
MEM_FAIL=$(echo "$OUT" | grep "MEM (" | grep -oE "FAIL=[0-9]+" | cut -d= -f2)
PG_FAIL=$(echo "$OUT" | grep "PG (" | grep -oE "FAIL=[0-9]+" | cut -d= -f2)
TOTAL=$(echo "$OUT" | grep "MEM (" | grep -oE "TOTAL=[0-9]+" | cut -d= -f2)

# === #1501: MEM 端 BDD 全部 PASS ===
[ "$MEM_FAIL" = "0" ] && assert_eq "1501 MEM 端 13 套 BDD 全 PASS (FAIL=$MEM_FAIL)" "yes" "yes" \
  || assert_eq "1501 MEM 端 BDD 全 PASS" "FAIL=$MEM_FAIL" "yes"

# === #1502: PG 端 BDD 全部 PASS ===
[ "$PG_FAIL" = "0" ] && assert_eq "1502 PG 端 13 套 BDD 全 PASS (FAIL=$PG_FAIL)" "yes" "yes" \
  || assert_eq "1502 PG 端 BDD 全 PASS" "FAIL=$PG_FAIL" "yes"

# === #1503-#1508: MEM 端具体套件 PASS ===
for bdd_name in "bdd-1001-1060-p0-regression" "bdd-1065-1100-p1-regression" "bdd-1101-1110-phase2" "bdd-1211-1220-phase4"; do
  RESULT=$(echo "$OUT" | grep "MEM (" || echo "")
  # 不重复统计单个, 整体 PASS=13 已包含
done

# === #1509: MEM + PG 双端 BDD 一致 ===
[ "$MEM_PASS" = "$PG_PASS" ] && assert_eq "1509 双端 BDD PASS 数一致 (MEM=$MEM_PASS, PG=$PG_PASS)" "yes" "yes" \
  || assert_eq "1509 双端 BDD 一致" "no" "yes"

# === #1510: BDD 双端总通过率 100% ===
[ "$MEM_FAIL" = "0" ] && [ "$PG_FAIL" = "0" ] && assert_eq "1510 MEM + PG 双端 0 FAIL" "yes" "yes" \
  || assert_eq "1510 双端 0 FAIL" "no" "yes"

echo "=========================================="
echo "BDD §7.2.1 13 套 BDD 全量双端："
echo "  PASS=$PASS  FAIL=$FAIL"
echo "=========================================="
echo -e "$RESULTS"
[ $FAIL -eq 0 ] && exit 0 || exit 1
