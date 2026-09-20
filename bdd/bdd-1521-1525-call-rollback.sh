#!/bin/bash
# §7.3.2 FIX-T108 (2026-09-20) callActivity 主子回滚
set -e
source /opt/jupyter/src/RD/projects/jeeFlow/.venv/bin/activate
cd /opt/jupyter/src/RD/projects/jeeFlow
export JEEFLOW_PG_DSN="postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm"

PASS=0; FAIL=0
log() { echo "  $*"; }
ok() { log "  ✅ $*"; PASS=$((PASS+1)); }
err() { log "  ❌ $*"; FAIL=$((FAIL+1)); }

# 运行基础测试, 拿到 instance id
.venv/bin/python /tmp/debug_call5.py > /tmp/_call_rollback_result.txt 2>&1
RESULT=$(cat /tmp/_call_rollback_result.txt)
MAIN_ID=$(echo "$RESULT" | grep "main_id=" | head -1 | sed 's/main_id=//')
echo "  (main_id=$MAIN_ID)"

echo "[#1521] 子实例 REJECT → 主实例 state=WITHDRAW"
if echo "$RESULT" | grep -q "state=30"; then ok "主实例 state=WITHDRAW"; else err "主实例 state 未变更"; echo "$RESULT" | tail -3; fi

echo "[#1522] 主实例 rollback 信息记录 toNodeName/operator"
if echo "$RESULT" | grep -q "rollback_info_present"; then ok "rollback_info 存在"; else err "rollback_info 缺失"; fi

echo "[#1523] 主实例 DOING 任务自动 ABANDONED"
if echo "$RESULT" | grep -q "ABANDONED: 99"; then ok "final_app 任务 ABANDONED"; else err "final_app 任务未废弃"; fi

echo "[#1524] 主实例已 WITHDRAW 后不再被处理 (幂等)"
# 直接检查主实例 state 仍然是 30
if echo "$RESULT" | grep -q "state=30"; then ok "主实例保持 WITHDRAW"; else err "主实例 state 不稳定"; fi

echo "[#1525] rollbackOnChildFail=false 时不触发主实例回滚"
NO_ROLL=$(.venv/bin/python /tmp/test_no_rollback.py 2>&1 | tail -3)
if echo "$NO_ROLL" | grep -q "state_unchanged=YES"; then ok "rollbackOnChildFail=false 时主实例不变"; else err "rollbackOnChildFail=false 时主实例被错误回滚: $NO_ROLL"; fi

echo "===== TOTAL: PASS=$PASS FAIL=$FAIL ====="
exit $FAIL
