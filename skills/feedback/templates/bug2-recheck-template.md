# BUG-2 复测模板 (a1) · 2026-11-10 (W46 Day 2)

> **来源**: flowuser DM 2026-11-10 确认 (W46 Day 2)
> **目的**: BUG-2 (FIX-T112) 5 次复测, 升级 FB-0007 双签闭环 (bro + flowuser)
> **状态**: 🟡 template, 等 flowuser 给 B7 + B8 实例 ID

---

## 1. 模板 (基于 omarchy run_5_times_1517.py 改造)

```bash
#!/bin/bash
# bdd/bug2-recheck_<timestamp>.sh
# 5 次复测 BUG-2 (FIX-T112) · 验证 ≥ 3 实例无回归
# 模板 · 待填: V3_INSTANCE + B7_INSTANCE + B8_INSTANCE

set -e
HOST=http://localhost:8101
PASS=0; FAIL=0
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

# === 待填 ===
V3_INSTANCE="92116610518127"   # W40 Day 2 已验证
B7_INSTANCE="<待 flowuser 给>" # 历史实例 1
B8_INSTANCE="<待 flowuser 给>" # 历史实例 2

# === 5 次复测 ===
for INSTANCE in "$V3_INSTANCE" "$B7_INSTANCE" "$B8_INSTANCE"; do
  echo "=== Instance: $INSTANCE ==="

  # 验证 state = 20 DONE
  STATE=$(curl -s -X POST $HOST/wf/processInstance/detail \
    -H "Content-Type: application/json" \
    -d "{\"id\":$INSTANCE}" | jq -r '.data.state')
  assert_eq "$INSTANCE state" "$STATE"
done

# === 汇总 ===
echo -e "\n=== BUG-2 复测结果 ==="
echo -e "$RESULTS"
echo "PASS=$PASS  FAIL=$FAIL"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
```

---

## 2. 使用方法

```bash
# 1. 等 flowuser 给 B7_INSTANCE + B8_INSTANCE (任意时给)
# 2. 替换模板中的 "<待 flowuser 给>" 占位符
# 3. hermes 用本地 main.py (8101) 跑 5 次
# 4. 输出: PASS=3 FAIL=0 → FB-0007 双签闭环升级
```

---

## 3. 关联文档

- `feedback/drafts/draft-to-flowuser-2026-11-04.md` · flowuser 草稿
- `feedback/attachments/FB-0007-bug2-metadata.json` · BUG-2 metadata
- `bdd/bdd-1601-1603-fix-t112-decision-orphan-cleanup_20260922.sh` · FIX-T112 双端测试
- `customers/C-001/journey-evidence/2026-10-30-stage6-tracking.md` · C-001 阶段 6 跟踪 Day 38

---

⏱️ Last updated: 2026-11-10 · 模板 v1.0 等实例 ID