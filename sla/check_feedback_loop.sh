#!/usr/bin/env bash
# sla/check_feedback_loop.sh — 反馈闭环健康度检查 (Phase 8 新增)
# 用法: bash sla/check_feedback_loop.sh
# 输出: sla/last_feedback_check.json + stdout
#
# 检查项:
#   1. skills/feedback/ 目录结构完整性
#   2. archive/ 与 inbox/ 文件数量
#   3. FB 编号连续性 (1 起递增, 不跳号)
#   4. 每条 FB 含 lessons_learned 字段
#   5. metrics/monthly-*.json 与 archive 数量一致
#   6. 客户档案存在 (C-NNN.yaml)
#   7. README.md v1.x 反映闭环率
#
# 输出字段 (用于 Phase 9 趋势监控):
#   - closed_count
#   - inbox_count
#   - closure_rate
#   - continuity_ok (True / False)
#   - lessons_learned_coverage (%)
#   - metrics_consistency (True / False)

set -u

SKILLS_DIR="${SKILLS_DIR:-skills}"
FEEDBACK_DIR="$SKILLS_DIR/feedback"
CUSTOMERS_DIR="$SKILLS_DIR/customers"

PASS=0; FAIL=0
RESULTS=()

ok()   { PASS=$((PASS+1)); RESULTS+=("✅ $1"); }
fail() { FAIL=$((FAIL+1)); RESULTS+=("❌ $1 — $2"); }

CLOSED=0
INBOX=0
CONTINUITY=true
LESSONS_COVERAGE=0
METRICS_CONSISTENT=true

# === 1. 目录结构 ===
[ -d "$FEEDBACK_DIR/archive" ] && ok "1.1 archive/ 存在" || fail "1.1 archive/" "missing"
[ -d "$FEEDBACK_DIR/inbox" ]   && ok "1.2 inbox/ 存在"   || fail "1.2 inbox/" "missing"
[ -d "$FEEDBACK_DIR/metrics" ] && ok "1.3 metrics/ 存在" || fail "1.3 metrics/" "missing"

# === 2. 数量统计 ===
CLOSED=$(ls "$FEEDBACK_DIR/archive/"*.json 2>/dev/null | wc -l)
INBOX=$(ls "$FEEDBACK_DIR/inbox/"*.json 2>/dev/null | wc -l)
TOTAL=$((CLOSED + INBOX))

ok "2.1 archive/ 数量 = $CLOSED"
ok "2.2 inbox/ 数量 = $INBOX"

# === 3. 编号连续性 ===
# 提取所有 FB 编号, 检查是否从 1 递增
ALL_IDS=$(ls "$FEEDBACK_DIR/archive/"*.json "$FEEDBACK_DIR/inbox/"*.json 2>/dev/null \
  | xargs -I {} basename {} .json 2>/dev/null \
  | grep -E "^FB-[0-9]+$" \
  | sed 's/^FB-//' \
  | sort -n)

EXPECTED=1
for ID in $ALL_IDS; do
  if [ "$ID" -ne "$EXPECTED" ]; then
    fail "3.1 FB 编号连续性" "expect=$EXPECTED got=$ID"
    CONTINUITY=false
    break
  fi
  EXPECTED=$((EXPECTED + 1))
done
[ "$CONTINUITY" = "true" ] && ok "3.1 FB 编号连续 (1 ~ $((EXPECTED - 1)))"

# === 4. lessons_learned 字段覆盖 ===
LESSONS_COUNT=0
for f in "$FEEDBACK_DIR/archive/"*.json; do
  [ -f "$f" ] || continue
  if grep -q '"lessons_learned"' "$f" 2>/dev/null; then
    LESSONS_COUNT=$((LESSONS_COUNT + 1))
  fi
done

if [ "$CLOSED" -gt 0 ]; then
  COVERAGE=$((LESSONS_COUNT * 100 / CLOSED))
  if [ "$COVERAGE" -ge 80 ]; then
    ok "4.1 lessons_learned 覆盖率 ${COVERAGE}% ($LESSONS_COUNT/$CLOSED)"
  else
    fail "4.1 lessons_learned 覆盖率低" "${COVERAGE}% < 80%"
  fi
else
  fail "4.1 lessons_learned 检查" "无 closed FB"
fi

# === 5. metrics 一致性 ===
LATEST_METRICS=$(ls -t "$FEEDBACK_DIR/metrics/"monthly-*.json 2>/dev/null | head -1)
if [ -n "$LATEST_METRICS" ]; then
  METRICS_CLOSED=$(jq -r '.summary.closed // 0' "$LATEST_METRICS" 2>/dev/null)
  if [ "$METRICS_CLOSED" = "$CLOSED" ]; then
    ok "5.1 metrics closed_count 与 archive 一致 ($CLOSED)"
  else
    fail "5.1 metrics closed_count 不一致" "metrics=$METRICS_CLOSED actual=$CLOSED"
    METRICS_CONSISTENT=false
  fi
else
  fail "5.1 metrics 检查" "无 metrics/monthly-*.json"
fi

# === 6. 客户档案 ===
CUSTOMER_COUNT=$(ls "$CUSTOMERS_DIR"/C-*.yaml 2>/dev/null | wc -l)
if [ "$CUSTOMER_COUNT" -ge 1 ]; then
  ok "6.1 客户档案 $CUSTOMER_COUNT 个"
else
  fail "6.1 客户档案" "无 C-*.yaml"
fi

# === 7. README.md 版本检查 ===
README_PATH="$SKILLS_DIR/README.md"
if [ -f "$README_PATH" ]; then
  # 取最大版本号 (从 versions 段: 行首 "- **vX.Y**")
  VERSION=$(grep -E "^- \*\*v[0-9]+\.[0-9]+\*\*" "$README_PATH" | tail -1 | grep -oE "v[0-9]+\.[0-9]+" | head -1)
  ok "7.1 README.md 最新版本 $VERSION"
else
  fail "7.1 README.md" "missing"
fi

# === 输出汇总 ===
if [ "$CLOSED" -gt 0 ]; then
  CLOSURE_RATE=$((CLOSED * 100 / TOTAL))
else
  CLOSURE_RATE="N/A"
fi

echo ""
echo "═══════════════════════════════════════"
echo "反馈闭环 SLA 健康度"
echo "═══════════════════════════════════════"
echo "  closed: $CLOSED"
echo "  inbox:  $INBOX"
echo "  total:  $TOTAL"
echo "  closure_rate: ${CLOSURE_RATE}%"
echo "  continuity_ok: $CONTINUITY"
echo "  lessons_coverage: ${LESSONS_COVERAGE}%"
echo "  metrics_consistent: $METRICS_CONSISTENT"
echo "  customer_files: $CUSTOMER_COUNT"

echo ""
for r in "${RESULTS[@]}"; do
  echo "$r"
done
echo ""
echo "PASS=$PASS  FAIL=$FAIL"

# 写机器可读
cat > sla/last_feedback_check.json <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "closed_count": $CLOSED,
  "inbox_count": $INBOX,
  "total": $TOTAL,
  "closure_rate": "${CLOSURE_RATE}",
  "continuity_ok": $CONTINUITY,
  "lessons_learned_coverage_pct": $LESSONS_COVERAGE,
  "metrics_consistency_ok": $METRICS_CONSISTENT,
  "customer_files": $CUSTOMER_COUNT,
  "pass": $PASS,
  "fail": $FAIL
}
EOF

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
