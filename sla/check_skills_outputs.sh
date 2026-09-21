#!/usr/bin/env bash
# sla/check_skills_outputs.sh — skills/ 制度体系健康度检查 (Phase 8 新增)
# 用法: bash sla/check_skills_outputs.sh
# 输出: sla/last_skills_check.json + stdout
#
# 检查项:
#   1. 核心制度文档存在 (README, FEEDBACK, FREEZE, CUSTOMER, ROADMAP, etc.)
#   2. 反馈闭环目录结构
#   3. 客户档案存在
#   4. weekly/backlog 节奏机制
#   5. 累计产出文件数

set -u

SKILLS_DIR="${SKILLS_DIR:-skills}"

PASS=0; FAIL=0
RESULTS=()

ok()   { PASS=$((PASS+1)); RESULTS+=("✅ $1"); }
fail() { FAIL=$((FAIL+1)); RESULTS+=("❌ $1 — $2"); }

# === 1. 核心文档 ===
REQUIRED_DOCS=(
  "README.md"
  "SKILLS.md"
  "FREEZE.md"
  "FEEDBACK.md"
  "CUSTOMER.md"
  "ROADMAP.md"
  "SKILL-TREE.md"
  "RACI.md"
  "RML.md"
  "users.md"
)

for doc in "${REQUIRED_DOCS[@]}"; do
  if [ -f "$SKILLS_DIR/$doc" ]; then
    ok "1.1 文档存在 $doc"
  else
    fail "1.1 文档缺失" "$doc"
  fi
done

# === 2. 反馈闭环目录 ===
[ -d "$SKILLS_DIR/feedback" ]      && ok "2.1 feedback/ 存在" || fail "2.1 feedback/" "missing"
[ -d "$SKILLS_DIR/feedback/archive" ] && ok "2.2 feedback/archive/ 存在" || fail "2.2 feedback/archive/" "missing"
[ -d "$SKILLS_DIR/feedback/metrics" ] && ok "2.3 feedback/metrics/ 存在" || fail "2.3 feedback/metrics/" "missing"
[ -d "$SKILLS_DIR/feedback/templates" ] && ok "2.4 feedback/templates/ 存在" || fail "2.4 feedback/templates/" "missing"
[ -d "$SKILLS_DIR/feedback/retrospectives" ] && ok "2.5 feedback/retrospectives/ 存在" || fail "2.5 feedback/retrospectives/" "missing"

# === 3. 客户档案 ===
[ -d "$SKILLS_DIR/customers" ] && ok "3.1 customers/ 存在" || fail "3.1 customers/" "missing"
CUSTOMER_COUNT=$(ls "$SKILLS_DIR/customers/"C-*.yaml 2>/dev/null | wc -l)
[ "$CUSTOMER_COUNT" -ge 1 ] && ok "3.2 客户档案 $CUSTOMER_COUNT 个" || fail "3.2 客户档案" "无 C-*.yaml"

# === 4. 节奏机制 ===
[ -d "$SKILLS_DIR/weekly" ] && ok "4.1 weekly/ 存在" || fail "4.1 weekly/" "missing"
[ -d "$SKILLS_DIR/backlog" ] && ok "4.2 backlog/ 存在" || fail "4.2 backlog/" "missing"
[ -d "$SKILLS_DIR/proposals" ] && ok "4.3 proposals/ 存在" || fail "4.3 proposals/" "missing (Phase 8 新增)"

# === 5. 累计产出 ===
TOTAL_FILES=$(find "$SKILLS_DIR" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" \) 2>/dev/null | wc -l)
ok "5.1 skills/ 总文件数 $TOTAL_FILES"

# === 输出汇总 ===
echo ""
echo "═══════════════════════════════════════"
echo "skills/ 制度体系 SLA 健康度"
echo "═══════════════════════════════════════"
echo "  total_files: $TOTAL_FILES"
echo "  customer_files: $CUSTOMER_COUNT"
echo ""
for r in "${RESULTS[@]}"; do
  echo "$r"
done
echo ""
echo "PASS=$PASS  FAIL=$FAIL"

# 写机器可读
cat > sla/last_skills_check.json <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "total_files": $TOTAL_FILES,
  "customer_files": $CUSTOMER_COUNT,
  "pass": $PASS,
  "fail": $FAIL
}
EOF

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
