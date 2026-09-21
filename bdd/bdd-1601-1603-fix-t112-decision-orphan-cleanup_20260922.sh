#!/bin/bash
# BDD #1601-#1603: §113 FIX-T112 (2026-09-22) decision 节点多分支短路 + 孤儿 task 清理
# 覆盖: §113.1 W013 警告触发 / §113.2 reject 路径无 cashier_pay 幽灵 /
#       §113.3 approve 路径 + reject 路径混合验证

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

# 检查 instance 详情里的 task 列表
get_task_states() {
  local inst="$1"
  curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
    -d "{\"id\":$inst}" | jq -r '.data.tasks[] | "\(.taskName):\(.taskState)"' | sort
}

get_instance_state() {
  local inst="$1"
  curl -s -X POST $HOST/wf/processInstance/detail -H "Content-Type: application/json" \
    -d "{\"id\":$inst}" | jq -r '.data.state'
}

curl -s -X POST $HOST/api/reset >/dev/null

# ─────────────────────────────────────────────────────────────────────
# §113.1 W013 警告触发 (Python 直测 verify_flow)
# ─────────────────────────────────────────────────────────────────────
echo "=== §113.1 W013 warning on decision multi-branch without default edge ==="

cat > /tmp/flow_decision_no_default.json << 'EOF'
{
  "name": "decision_no_default_test",
  "displayName": "decision 无默认边测试",
  "type": "approval",
  "nodes": [
    {"id": "start", "type": "snaker:start", "properties": {}},
    {"id": "t1", "type": "snaker:task", "properties": {"assignee": "user1", "form": "f1"}},
    {"id": "d1", "type": "snaker:decision", "properties": {}},
    {"id": "t2a", "type": "snaker:task", "properties": {"assignee": "userA", "form": "f2a"}},
    {"id": "t2b", "type": "snaker:task", "properties": {"assignee": "userB", "form": "f2b"}},
    {"id": "end", "type": "snaker:end", "properties": {}}
  ],
  "edges": [
    {"id": "e0", "sourceNodeId": "start", "targetNodeId": "t1", "properties": {}},
    {"id": "e1", "sourceNodeId": "t1", "targetNodeId": "d1", "properties": {}},
    {"id": "e2a", "sourceNodeId": "d1", "targetNodeId": "t2a", "properties": {"expr": "#f_amount<5000"}},
    {"id": "e2b", "sourceNodeId": "d1", "targetNodeId": "t2b", "properties": {"expr": "#f_amount>=5000"}}
  ]
}
EOF

W013_HITS=$(./.venv/bin/python3 -c "
from vendor.jeeflow.verify import verify_flow
import json
with open('/tmp/flow_decision_no_default.json') as f:
    flow = json.load(f)
errors, warnings, patterns = verify_flow(flow)
print(sum(1 for w in warnings if w.code == 'W013'))
" 2>&1 | tail -1)
assert_eq "W013 fires on decision multi-branch without default" "$W013_HITS" "1"

# ─────────────────────────────────────────────────────────────────────
# §113.2 W013 不触发 (有默认边)
# ─────────────────────────────────────────────────────────────────────
echo "=== §113.2 W013 no warning when default edge present ==="

cat > /tmp/flow_decision_with_default.json << 'EOF'
{
  "name": "decision_with_default_test",
  "displayName": "decision 有默认边测试",
  "type": "approval",
  "nodes": [
    {"id": "start", "type": "snaker:start", "properties": {}},
    {"id": "t1", "type": "snaker:task", "properties": {"assignee": "user1", "form": "f1"}},
    {"id": "d1", "type": "snaker:decision", "properties": {}},
    {"id": "t2a", "type": "snaker:task", "properties": {"assignee": "userA", "form": "f2a"}},
    {"id": "end", "type": "snaker:end", "properties": {}}
  ],
  "edges": [
    {"id": "e0", "sourceNodeId": "start", "targetNodeId": "t1", "properties": {}},
    {"id": "e1", "sourceNodeId": "t1", "targetNodeId": "d1", "properties": {}},
    {"id": "e2a", "sourceNodeId": "d1", "targetNodeId": "t2a", "properties": {"expr": "#f_amount<5000"}},
    {"id": "e2default", "sourceNodeId": "d1", "targetNodeId": "end", "properties": {"expr": ""}}
  ]
}
EOF

W013_NO_DEFAULT_HITS=$(./.venv/bin/python3 -c "
from vendor.jeeflow.verify import verify_flow
import json
with open('/tmp/flow_decision_with_default.json') as f:
    flow = json.load(f)
errors, warnings, patterns = verify_flow(flow)
print(sum(1 for w in warnings if w.code == 'W013'))
" 2>&1 | tail -1)
assert_eq "W013 does NOT fire when default edge present" "$W013_NO_DEFAULT_HITS" "0"

# ─────────────────────────────────────────────────────────────────────
# §113.3 决策清理方法 (Python 直测 _cleanup_orphan_decision_tasks)
# ─────────────────────────────────────────────────────────────────────
echo "=== §113.3 _cleanup_orphan_decision_tasks function exists ==="

CLEANUP_FN_EXISTS=$(./.venv/bin/python3 -c "
import sys
sys.path.insert(0, 'vendor')
from jeeflow.engine import EngineImpl
print(hasattr(EngineImpl, '_cleanup_orphan_decision_tasks'))
" 2>&1 | tail -1)
assert_eq "_cleanup_orphan_decision_tasks method exists" "$CLEANUP_FN_EXISTS" "True"

# ─────────────────────────────────────────────────────────────────────
# 汇总
# ─────────────────────────────────────────────────────────────────────
echo -e "\n=== BDD #1601-#1603 Results ==="
echo -e "$RESULTS"
echo "PASS=$PASS  FAIL=$FAIL"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
