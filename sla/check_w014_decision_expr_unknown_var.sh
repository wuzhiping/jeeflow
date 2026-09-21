#!/usr/bin/env bash
# sla/check_w014_decision_expr_unknown_var.sh · W014 verify 规则检测
# 来源: omarchy 第 2 次 file-share (取件码 97841) · BDD-1517 + FIX-T113
# 作用: 扫描 flows/*.json, 检测 decision 出边 expr 是否引用了 variables 中未声明的字段

set -u
SKILLS_DIR="${SKILLS_DIR:-skills}"
FLOWS_DIR="${FLOWS_DIR:-flows}"
PASS=0
FAIL=0
RESULTS=""

# 1. 准备: 读取所有 flows
FLOW_FILES=$(find "$FLOWS_DIR" -name "*.json" 2>/dev/null | sort)
if [ -z "$FLOW_FILES" ]; then
  fail "0.1 flows 扫描" "无 flows/*.json"
  echo "{\"check\":\"w014\",\"status\":\"skipped\",\"reason\":\"no flows\"}"
  exit 1
fi

# 2. 用 Python 扫描 + 检测
W014_HITS=$(./.venv/bin/python3 -c "
import json, os, re
from pathlib import Path

PY_KW = {'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is'}
RE_IDENT = re.compile(r'[A-Za-z_][A-Za-z0-9]*')

flows_dir = Path('flows')
unknown_refs = []

for fp in sorted(flows_dir.glob('*.json')):
    if 'w014-test' in fp.name:
        continue
    try:
        with open(fp) as f:
            data = json.load(f)
    except Exception as e:
        continue

    nodes = {n['id']: n for n in data.get('nodes', []) if 'id' in n}
    edges = data.get('edges', [])
    variables = (data.get('properties') or {}).get('variables', {}) or {}

    # 收集决策节点
    decisions = [nid for nid, n in nodes.items() if n.get('type', '').endswith(':decision')]

    for d_id in decisions:
        for e in edges:
            if e.get('sourceNodeId') != d_id:
                continue
            expr = (e.get('properties') or {}).get('expr', '')
            if not expr:
                continue
            ids = set(RE_IDENT.findall(expr))
            ids -= PY_KW
            # 同时剔除 known 字段 (f_xxx, u_xxx)
            for tid in list(ids):
                if tid.startswith('f_') or tid.startswith('u_') or tid.startswith('#'):
                    ids.discard(tid)
            for tid in ids:
                if len(tid) >= 2 and tid not in variables:
                    unknown_refs.append((fp.name, d_id, e.get('id', '?'), tid, expr))

print(len(unknown_refs))
" 2>&1 | tail -1)

# 3. 判定
if [ "$W014_HITS" = "0" ]; then
  PASS=$((PASS + 1))
  RESULTS="$RESULTS\n✅ W014 无触发 (所有 flows 决策正常)"
else
  FAIL=$((FAIL + 1))
  RESULTS="$RESULTS\n❌ W014 触发: $W014_HITS 处未知变量引用"
  # 详细列出
  echo ""
  echo "W014 详细:"
  ./.venv/bin/python3 -c "
import json, re
from pathlib import Path

PY_KW = {'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is'}
RE_IDENT = re.compile(r'[A-Za-z_][A-Za-z0-9]*')

flows_dir = Path('flows')

for fp in sorted(flows_dir.glob('*.json')):
    if 'w014-test' in fp.name:
        continue
    try:
        with open(fp) as f:
            data = json.load(f)
    except Exception as e:
        continue
    nodes = {n['id']: n for n in data.get('nodes', []) if 'id' in n}
    edges = data.get('edges', [])
    variables = (data.get('properties') or {}).get('variables', {}) or {}
    decisions = [nid for nid, n in nodes.items() if n.get('type', '').endswith(':decision')]
    for d_id in decisions:
        for e in edges:
            if e.get('sourceNodeId') != d_id:
                continue
            expr = (e.get('properties') or {}).get('expr', '')
            if not expr:
                continue
            ids = set(RE_IDENT.findall(expr))
            ids -= PY_KW
            for tid in list(ids):
                if tid.startswith('f_') or tid.startswith('u_') or tid.startswith('#'):
                    ids.discard(tid)
            for tid in ids:
                if len(tid) >= 2 and tid not in variables:
                    print(f'  {fp.name}: {d_id} -> {e.get(\"id\")} expr=\"{expr}\" 引用未声明 \'{tid}\"')
" 2>&1 | grep -v "^$"
fi

echo -e "\n=== W014 检查结果 ==="
echo -e "$RESULTS"
echo "PASS=$PASS  FAIL=$FAIL"

# 写结果
mkdir -p sla
cat > sla/last_w014_check.json <<EOF
{
  "check": "w014_decision_expr_unknown_var",
  "status": "$([ "$FAIL" -eq 0 ] && echo "PASS" || echo "WARN")",
  "flows_scanned": $(echo "$FLOW_FILES" | wc -l),
  "unknown_refs": $W014_HITS,
  "source": "omarchy 取件码 97841 · BDD-1517 FIX-T113",
  "timestamp": "$(date -Iseconds)"
}
EOF

[ "$FAIL" -eq 0 ] && exit 0 || exit 1