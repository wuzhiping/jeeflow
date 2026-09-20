#!/bin/bash
# §7.3.3 FIX-T109 (2026-09-20) 断点续跑 - doingList API + startup hook
set -e
source /opt/jupyter/src/RD/projects/jeeFlow/.venv/bin/activate
cd /opt/jupyter/src/RD/projects/jeeFlow
export JEEFLOW_PG_DSN="postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm"

PASS=0; FAIL=0
ok() { echo "  ✅ $*"; PASS=$((PASS+1)); }
err() { echo "  ❌ $*"; FAIL=$((FAIL+1)); }

echo "[#1526-1532] §7.3.3 断点续跑 (FIX-T109)"
.venv/bin/python /tmp/test_resume.py > /tmp/_resume_result.txt 2>&1
RES=$(cat /tmp/_resume_result.txt)
if echo "$RES" | grep -q "#1526"; then ok "doingList API"; else err "doingList API 失败"; fi
if echo "$RES" | grep -q "#1527"; then ok "task_count"; else err "task_count 失败"; fi
if echo "$RES" | grep -q "#1528"; then ok "by_node 统计"; else err "by_node 失败"; fi
if echo "$RES" | grep -q "#1529"; then ok "defineId 过滤"; else err "defineId 过滤失败"; fi
if echo "$RES" | grep -q "#1530"; then ok "limit 生效"; else err "limit 失败"; fi
if echo "$RES" | grep -q "#1531"; then ok "DONE 排除"; else err "DONE 排除失败"; fi
if echo "$RES" | grep -q "#1532"; then ok "全 DONE 时 count=0"; else err "全 DONE 失败"; fi

# [#1533] 双端 doingList API 可用
MEM_RES=$(curl -s -X POST http://localhost:8101/wf/processInstance/doingList -H "Content-Type: application/json" -d '{"limit":10}')
PG_RES=$(curl -s -X POST http://localhost:8102/wf/processInstance/doingList -H "Content-Type: application/json" -d '{"limit":10}')
MEM_CODE=$(echo "$MEM_RES" | python3 -c "import sys,json; print(json.load(sys.stdin).get('code'))")
PG_CODE=$(echo "$PG_RES" | python3 -c "import sys,json; print(json.load(sys.stdin).get('code'))")
if [ "$MEM_CODE" = "0" ] && [ "$PG_CODE" = "0" ]; then
    ok "双端 doingList API 双端 code=0"
else
    err "双端 doingList API 失败 MEM=$MEM_CODE PG=$PG_CODE"
fi

echo "===== TOTAL: PASS=$PASS FAIL=$FAIL ====="
exit $FAIL
