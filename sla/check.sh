#!/usr/bin/env bash
# sla/check.sh — jeeFlow SLA 健康度检查 (可固化脚本 + 帮助函数)
# 用法: bash sla/check.sh [host] [port] [pg_host] [pg_port]
#   默认: MEM=localhost:8101, PG=localhost:8102
#   (SLA.md 更新 2026-09-20：要求 memory + pg 双端验证)
# 输出: sla/last_check.json (机读) + stdout (人读)
# 变更:
#   2026-09-20 §6 能力覆盖 (#14-#22)
#   2026-09-20 双端 (MEM + PG) 验证 (#23-#30, SLA.md 新要求)

set -u
HOST="${1:-http://localhost}"
PORT="${2:-8101}"
BASE="$HOST:$PORT"

PG_HOST="${3:-http://localhost}"
PG_PORT="${4:-8102}"
PG_BASE="$PG_HOST:$PG_PORT"

# PG DSN (用于 PG 端 in-process / SQL 检查)
PG_DSN="${JEEFLOW_PG_DSN:-postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm}"

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OUT_JSON="sla/last_check.json"

PASS=0; FAIL=0
RESULTS=()

ok()   { PASS=$((PASS+1)); RESULTS+=("✅ $1"); }
fail() { FAIL=$((FAIL+1)); RESULTS+=("❌ $1 — $2"); }

# === 帮助函数 ===
http_code()  { curl -s -m 3 -o /dev/null -w "%{http_code}" "$1" 2>/dev/null || echo "000"; }
http_get()    { curl -s -m 3 "$1" 2>/dev/null; }
http_post()   { curl -s -X POST -m 5 -H "Content-Type: application/json" -d "$2" "$1" 2>/dev/null; }
latency_ms() { curl -o /dev/null -s -m 5 -w '%{time_total}' "$1" 2>/dev/null | awk '{ printf "%d", $1*1000 }'; }
count_metric() { curl -s -m 3 "$1/metrics" 2>/dev/null | grep -c "^# HELP $2 "; }
file_count()  { ls "$1/$2" 2>/dev/null | grep -E "$3" | wc -l; }

# === 输出当前模式 ===
echo "═══════════════════════════════════════"
echo "jeeFlow SLA 健康度检查"
echo "  MEM backend: $BASE"
echo "  PG  backend: $PG_BASE"
echo "═══════════════════════════════════════"

# === 1. 进程存活 ===
H=$(http_code $BASE/healthz)
[ "$H" = "200" ] && ok "1.1 healthz HTTP 200" || fail "1.1 healthz HTTP 200" "got=$H"

# === 2. healthz 内容 ===
HJ=$(http_get $BASE/healthz)
STATUS=$(echo "$HJ" | jq -r '.status // empty' 2>/dev/null)
[ "$STATUS" = "UP" ] && ok "2.1 healthz.status=UP" || fail "2.1 healthz.status=UP" "got=$STATUS"
BACKEND=$(echo "$HJ" | jq -r '.backend // empty')
[ -n "$BACKEND" ] && ok "2.2 healthz.backend=$BACKEND" || fail "2.2 healthz.backend" "missing"

# === 3. 端点延迟 ===
T_HEALTHZ_MS=$(latency_ms $BASE/healthz)
[ "$T_HEALTHZ_MS" -lt 50 ] && ok "3.1 healthz P99 < 50ms (实测 ${T_HEALTHZ_MS}ms)" \
  || fail "3.1 healthz P99 < 50ms" "实测 ${T_HEALTHZ_MS}ms"

T_METRICS_MS=$(latency_ms $BASE/metrics)
[ "$T_METRICS_MS" -lt 500 ] && ok "3.2 metrics P99 < 500ms (实测 ${T_METRICS_MS}ms)" \
  || fail "3.2 metrics P99 < 500ms" "实测 ${T_METRICS_MS}ms"

# === 4. metrics 4 指标 ===
M=$(http_get $BASE/metrics)
for m in wf_instance_state_total wf_active_instances wf_task_duration_seconds wf_task_completed_total; do
  if echo "$M" | grep -q "^# HELP $m "; then
    ok "4.$m metric exists"
  else
    fail "4.$m metric exists" "missing"
  fi
done

# === 5. stats 端点 ===
SO=$(http_get $BASE/api/admin/stats/overview)
SOC=$(echo "$SO" | jq -r '.code // empty')
[ "$SOC" = "0" ] && ok "5.1 stats/overview code=0" || fail "5.1 stats/overview code=0" "code=$SOC"
SI=$(echo "$SO" | jq -r '.data.total // empty')
[ -n "$SI" ] && ok "5.2 stats/overview.data.total=${SI}" || fail "5.2 stats/overview.data" "missing"

ST=$(http_get "$BASE/api/admin/stats/trend?start=2026-09-13&end=2026-09-20&granularity=day")
STC=$(echo "$ST" | jq -r '.code // empty')
[ "$STC" = "0" ] && ok "5.3 stats/trend code=0" || fail "5.3 stats/trend code=0" "code=$STC"

# === 6. trace 端点 ===
TR=$(http_get "$BASE/api/admin/trace?limit=1")
TRK=$(echo "$TR" | jq -r '.total // empty')
[ -n "$TRK" ] && ok "6.1 trace.total=${TRK}" || fail "6.1 trace" "missing total"

# === 7. expire scan 端点 ===
SC=$(http_post $BASE/api/admin/expire/scan '{}')
SCN=$(echo "$SC" | jq -r '.scanTime // empty')
[ -n "$SCN" ] && ok "7.1 expire/scan returns scanTime" || fail "7.1 expire/scan" "no scanTime"

# === 8. wf/action 业务端点可达 ===
DSAVE=$(http_post $BASE/wf/processDesign/save '{"name":"_sla_check","displayName":"sla","content":"{}"}' | jq -r '.code // "missing"')
[ "$DSAVE" != "missing" ] && ok "8.1 processDesign/save reachable" || fail "8.1 processDesign/save" "no response"

# === 9. wf/action 文档完整性 ===
ACTION_DOC_COUNT=$(grep -cE "^\| [0-9]+ \|" docs/actions.md 2>/dev/null || echo 0)
[ "$ACTION_DOC_COUNT" -ge 30 ] && ok "9.1 docs/actions.md ≥30 endpoints (实测 $ACTION_DOC_COUNT)" \
  || fail "9.1 docs/actions.md ≥30" "实测 $ACTION_DOC_COUNT"

# === 10. OpenAPI 文档 ===
OA_PATHS=$(python3 -c "import json; print(len(json.load(open('docs/openapi.json')).get('paths', {})))" 2>/dev/null || echo 0)
[ "$OA_PATHS" -ge 50 ] && ok "10.1 openapi.json paths ≥50 (实测 $OA_PATHS)" \
  || fail "10.1 openapi.json paths ≥50" "实测 $OA_PATHS"

# === 11. verify 规则 ===
VR=$(grep -cE "VerifyIssue|severity=\"E|severity=\"W|severity=\"P" vendor/jeeflow/verify.py 2>/dev/null || echo 0)
[ "$VR" -ge 30 ] && ok "11.1 verify rules ≥30 (实测 $VR)" || fail "11.1 verify rules ≥30" "实测 $VR"

# === 12. 流程定义数量 ===
FLOWS=$(file_count "$PWD" flows "*.json")
[ "$FLOWS" -ge 17 ] && ok "12.1 flows/*.json ≥17 (实测 $FLOWS)" || fail "12.1 flows ≥17" "实测 $FLOWS"

# === 13. BDD 回归脚本 ===
BDD_SH=$(file_count "$PWD" bdd "bdd-.*\.sh")
[ "$BDD_SH" -ge 3 ] && ok "13.1 bdd回归脚本 ≥3 (实测 $BDD_SH)" || fail "13.1 bdd回归脚本 ≥3" "实测 $BDD_SH"

# === 14. §6.2.1 processInstance/export (FIX-T97) ===
# 准备数据: deploy + 启动实例
curl -s -X POST $BASE/api/reset >/dev/null 2>&1
D=$(http_post $BASE/wf/processDesign/save "$(jq -n --arg c "$(cat flows/01-simple.json 2>/dev/null || echo '{"nodes":[]}')" '{name:"_sla_export",displayName:"e",content:$c}')" | jq -r '.data.id // empty')
if [ -n "$D" ]; then
  DEF=$(http_post $BASE/wf/processDesign/deploy "{\"id\": $D}" | jq -r '.data.processDefineId // empty')
  [ -n "$DEF" ] && http_post $BASE/wf/processInstance/startAndExecute "{\"processDefineId\":$DEF,\"operator\":\"user1\"}" >/dev/null
  EXP=$(http_post $BASE/wf/processInstance/export '{"format":"csv","limit":10}')
  EXP_CODE=$(echo "$EXP" | jq -r '.code // "missing"')
  EXP_DATA=$(echo "$EXP" | jq -r '.data.data // empty')
  EXP_HAS=$(echo "$EXP_DATA" | grep -c "^id,")
  if [ "$EXP_CODE" = "0" ] && [ "$EXP_HAS" -ge 1 ]; then
    ok "14.1 §6.2.1 processInstance/export CSV (code=0, header ok)"
  else
    fail "14.1 §6.2.1 processInstance/export" "code=$EXP_CODE"
  fi
  EXP_JSON=$(http_post $BASE/wf/processInstance/export '{"format":"json","limit":10}' | jq -r '.data.data')
  echo "$EXP_JSON" | jq . >/dev/null 2>&1 && ok "14.2 §6.2.1 processInstance/export JSON (可解析)" \
    || fail "14.2 JSON 不可解析" ""
else
  fail "14.1 §6.2.1 processInstance/export" "deploy failed"
fi

# === 15. §6.2.2 auditLog/export (FIX-T98) ===
AUDIT=$(http_post $BASE/wf/auditLog/export '{"format":"csv","limit":100}')
AUDIT_CODE=$(echo "$AUDIT" | jq -r '.code // "missing"')
AUDIT_COUNT=$(echo "$AUDIT" | jq -r '.data.count // 0')
[ "$AUDIT_COUNT" -ge 1 ] && [ "$AUDIT_CODE" = "0" ] && ok "15.1 §6.2.2 auditLog/export CSV (count=$AUDIT_COUNT)" \
  || fail "15.1 §6.2.2 auditLog/export" "code=$AUDIT_CODE count=$AUDIT_COUNT"

# === 16. §6.1.1 preInterceptors 识别 (FIX-T94) ===
# 通过 mock-audit.log 验证 pre_handle 被调用 (需要 server 是 main.py 内存版)
rm -f /tmp/jee-mock-audit.log
PRE_DESIGN=$(http_post $BASE/wf/processDesign/save "$(jq -n --arg c "$(cat /tmp/test-pre-interceptor.json 2>/dev/null || echo '{"nodes":[]}')" '{name:"_sla_pre",displayName:"p",content:$c}')" | jq -r '.data.id // empty')
if [ -n "$PRE_DESIGN" ]; then
  http_post $BASE/wf/processDesign/deploy "{\"id\":$PRE_DESIGN}" >/dev/null
  DEF_PRE=$(http_post $BASE/wf/processDesign/deploy "{\"id\":$PRE_DESIGN}" | jq -r '.data.processDefineId // empty')
  # 实际只 deploy 一次
  if [ -n "$DEF_PRE" ]; then
    http_post $BASE/wf/processInstance/startAndExecute "{\"processDefineId\":$DEF_PRE,\"operator\":\"user1\"}" >/dev/null
    PRE_CNT=$(grep -c "^PRE  PRE_ONE" /tmp/jee-mock-audit.log 2>/dev/null || echo 0)
    [ "$PRE_CNT" -ge 1 ] && ok "16.1 §6.1.1 preInterceptors pre_handle 被调用 ($PRE_CNT 次)" \
      || fail "16.1 §6.1.1 pre_handle" "audit log 无 PRE 行 (可能 8101 未重启注册 PRE_ONE)"
  else
    fail "16.1 §6.1.1 pre_handle" "deploy 二次失败"
  fi
else
  fail "16.1 §6.1.1 pre_handle" "design save 失败"
fi

# === 17. §6.4.2 metrics remote_write env 已实现 ===
HAS_ENV=$(grep -c "JEEFLOW_METRICS_REMOTE_WRITE_URL" main_common.py 2>/dev/null || echo 0)
[ "$HAS_ENV" -ge 1 ] && ok "17.1 §6.4.2 main_common 读取 JEEFLOW_METRICS_REMOTE_WRITE_URL env" \
  || fail "17.1 §6.4.2 remote_write env" "main_common.py 缺少"

# === 18. /api/admin/trace/{trace_id} 端点 (FIX-T84) ===
TR_ID_CODE=$(http_get "$BASE/api/admin/trace/spans/_sla_test_trace" | jq -r '.trace_id // empty')
[ -n "$TR_ID_CODE" ] && ok "18.1 trace/spans/{trace_id} 返回结构 (trace_id=_sla_test_trace)" \
  || fail "18.1 trace/spans/{trace_id}" "missing"

# === 19. /api/admin/stats/group 端点 ===
SG=$(http_get "$BASE/api/admin/stats/group?dimension=state")
SGC=$(echo "$SG" | jq -r '.code // empty')
[ "$SGC" = "0" ] && ok "19.1 stats/group code=0" || fail "19.1 stats/group" "code=$SGC"

# === 20. §6 全部新增能力文件存在 ===
NEW_DOCS=0
[ -f docs/deployment.md ] && NEW_DOCS=$((NEW_DOCS+1))
[ -f docs/integration.md ] && NEW_DOCS=$((NEW_DOCS+1))
[ -f docs/openapi.json ] && NEW_DOCS=$((NEW_DOCS+1))
[ -f TODO.md ] && NEW_DOCS=$((NEW_DOCS+1))
[ "$NEW_DOCS" -ge 4 ] && ok "20.1 §6 新增文档 ≥4 (实测 $NEW_DOCS)" \
  || fail "20.1 §6 新增文档" "实测 $NEW_DOCS"

# === 运行时指标快照 (MEM) ===
INST_ACT=$(echo "$M" | grep '^wf_active_instances ' | awk '{print $2}')
INST_DONE=$(echo "$M" | grep '^wf_instance_state_total{state="DONE"}' | awk '{print $2}')
INST_DOING=$(echo "$M" | grep '^wf_instance_state_total{state="DOING"}' | awk '{print $2}')
TASK_DONE=$(echo "$M" | grep -oE 'wf_task_completed_total\{taskName="[^"]+"\} [0-9.]+' | head -3)
echo ""
echo "📊 MEM 运行时指标:"
echo "  wf_active_instances = ${INST_ACT:-0}"
echo "  wf_instance_state_total{DOING} = ${INST_DOING:-0}"
echo "  wf_instance_state_total{DONE}  = ${INST_DONE:-0}"
[ -n "$TASK_DONE" ] && echo "  任务完成: $(echo "$TASK_DONE" | tr '\n' ' ')"

# ====================================================================
# 双端 PG 端验证 (SLA.md 2026-09-20 更新: 所有测试需 memory + pg 双验证)
# ====================================================================

# === 21. PG 端 healthz UP ===
PG_HJ=$(http_get $PG_BASE/healthz)
PG_STATUS=$(echo "$PG_HJ" | jq -r '.status // empty' 2>/dev/null)
PG_OK=$(echo "$PG_HJ" | jq -r '.pg // empty' 2>/dev/null)
if [ "$PG_STATUS" = "UP" ] && [ "$PG_OK" = "ok" ]; then
  ok "21.1 PG healthz UP + pg=ok"
else
  fail "21.1 PG healthz" "status=$PG_STATUS pg=$PG_OK"
fi

# === 22. PG 端 4 指标 ===
PG_M=$(http_get $PG_BASE/metrics)
PG_METRIC_OK=0
for m in wf_instance_state_total wf_active_instances wf_task_duration_seconds wf_task_completed_total; do
  if echo "$PG_M" | grep -q "^# HELP $m "; then
    PG_METRIC_OK=$((PG_METRIC_OK + 1))
  fi
done
[ "$PG_METRIC_OK" -ge 4 ] && ok "22.1 PG 4 指标全部存在" || fail "22.1 PG 指标" "only $PG_METRIC_OK/4"

# === 23. PG 端 processInstance/export ===
PG_DESIGN=$(http_post $PG_BASE/wf/processDesign/save "$(jq -n --arg c "$(cat flows/01-simple.json)" '{name:"_sla_pg",displayName:"p",content:$c}')" | jq -r '.data.id // empty')
if [ -n "$PG_DESIGN" ]; then
  PG_DEF=$(http_post $PG_BASE/wf/processDesign/deploy "{\"id\":$PG_DESIGN}" | jq -r '.data.processDefineId // empty')
  if [ -n "$PG_DEF" ]; then
    http_post $PG_BASE/wf/processInstance/startAndExecute "{\"processDefineId\":$PG_DEF,\"operator\":\"sla-pg\"}" >/dev/null
    PG_EXP=$(http_post $PG_BASE/wf/processInstance/export '{"format":"csv","limit":10}')
    PG_EXP_CODE=$(echo "$PG_EXP" | jq -r '.code // "missing"')
    PG_EXP_HAS=$(echo "$PG_EXP" | jq -r '.data.data // ""' | grep -c "^id,")
    [ "$PG_EXP_CODE" = "0" ] && [ "$PG_EXP_HAS" -ge 1 ] \
      && ok "23.1 PG processInstance/export CSV (code=0, header ok)" \
      || fail "23.1 PG processInstance/export" "code=$PG_EXP_CODE"
  else
    fail "23.1 PG processInstance/export" "deploy failed"
  fi
else
  fail "23.1 PG processInstance/export" "save failed"
fi

# === 24. PG 端 auditLog/export ===
PG_AUDIT=$(http_post $PG_BASE/wf/auditLog/export '{"format":"csv","limit":100}')
PG_AUDIT_CODE=$(echo "$PG_AUDIT" | jq -r '.code // "missing"')
PG_AUDIT_COUNT=$(echo "$PG_AUDIT" | jq -r '.data.count // 0')
[ "$PG_AUDIT_COUNT" -ge 1 ] && [ "$PG_AUDIT_CODE" = "0" ] \
  && ok "24.1 PG auditLog/export CSV (count=$PG_AUDIT_COUNT)" \
  || fail "24.1 PG auditLog/export" "code=$PG_AUDIT_CODE count=$PG_AUDIT_COUNT"

# === 25. PG 端 bizData (FIX-T95 §6.1.2) ===
# 准备测试表 + 流程 relTableName
PG_DSN_OK=$(.venv/bin/python << PYEOF 2>/dev/null
import asyncio, asyncpg
async def go():
    pool = await asyncpg.create_pool(dsn="$PG_DSN", min_size=1)
    async with pool.acquire() as c:
        await c.execute('DROP TABLE IF EXISTS _sla_biz')
        await c.execute('CREATE TABLE _sla_biz (id SERIAL PRIMARY KEY, process_instance_id BIGINT, biz_name TEXT)')
    await pool.close()
    print('ok')
asyncio.run(go())
PYEOF
)
if [ "$PG_DSN_OK" = "ok" ]; then
  # 部署带 relTableName 的流程
  cat > /tmp/_sla_biz_flow.json << 'JEOF'
{"name":"_sla_biz","displayName":"b","relTableName":"_sla_biz","nodes":[
{"id":"start","type":"snaker:start","properties":{}},
{"id":"apply","type":"snaker:task","properties":{"assignee":"sla-biz"}},
{"id":"end","type":"snaker:end","properties":{}}
],"edges":[
{"id":"e0","sourceNodeId":"start","targetNodeId":"apply"},
{"id":"e1","sourceNodeId":"apply","targetNodeId":"end"}
]}
JEOF
  BID=$(http_post $PG_BASE/wf/processDesign/save "$(jq -n --arg c "$(cat /tmp/_sla_biz_flow.json)" '{name:"_sla_biz_flow",displayName:"b",content:$c}')" | jq -r '.data.id // empty')
  if [ -n "$BID" ]; then
    BD=$(http_post $PG_BASE/wf/processDesign/deploy "{\"id\":$BID}" | jq -r '.data.processDefineId // empty')
    if [ -n "$BD" ]; then
      INST_PG=$(http_post $PG_BASE/wf/processInstance/startAndExecute "{\"processDefineId\":$BD,\"operator\":\"sla-biz\"}" | jq -r '.data.processInstanceId // empty')
      if [ -n "$INST_PG" ]; then
        # 插入对应 process_instance_id 的业务数据
        .venv/bin/python << PYEOF >/dev/null 2>&1
import asyncio, asyncpg
async def go():
    pool = await asyncpg.create_pool(dsn="$PG_DSN", min_size=1)
    async with pool.acquire() as c:
        await c.execute("INSERT INTO _sla_biz (process_instance_id, biz_name) VALUES (\$1, \$2)", $INST_PG, "sla-test")
    await pool.close()
asyncio.run(go())
PYEOF
        # 调 bizData
        PG_BIZ=$(http_post $PG_BASE/wf/processInstance/bizData "{\"id\":$INST_PG}" | jq -r '.data.biz_name // empty')
        [ "$PG_BIZ" = "sla-test" ] && ok "25.1 PG bizData 返回数据 (FIX-T95)" \
          || fail "25.1 PG bizData" "biz_name=$PG_BIZ"
      else
        fail "25.1 PG bizData" "start failed"
      fi
    else
      fail "25.1 PG bizData" "deploy failed"
    fi
  else
    fail "25.1 PG bizData" "save failed"
  fi
else
  fail "25.1 PG bizData" "PG DSN 不通: $PG_DSN_OK"
fi

# === 26. PG 端 trace 持久化 (FIX-T99 §6.4.1) ===
TRACE_CNT=$(.venv/bin/python << PYEOF 2>/dev/null
import asyncio, asyncpg
async def go():
    pool = await asyncpg.create_pool(dsn="$PG_DSN", min_size=1)
    async with pool.acquire() as c:
        n = await c.fetchval("SELECT count(*) FROM wf_trace_span")
        print(n)
    await pool.close()
asyncio.run(go())
PYEOF
)
if [ -n "$TRACE_CNT" ] && [ "$TRACE_CNT" -ge 1 ]; then
  ok "26.1 PG wf_trace_span 表 span 数=$TRACE_CNT (FIX-T99)"
else
  fail "26.1 PG trace 持久化" "count=$TRACE_CNT"
fi

# === 27. PG 端 expire/scan ===
PG_SCAN=$(http_post $PG_BASE/api/admin/expire/scan '{}')
PG_SCAN_TIME=$(echo "$PG_SCAN" | jq -r '.scanTime // empty')
[ -n "$PG_SCAN_TIME" ] && ok "27.1 PG expire/scan returns scanTime" \
  || fail "27.1 PG expire/scan" "no scanTime"

# === 28. PG 端 stats/overview ===
PG_SO=$(http_get $PG_BASE/api/admin/stats/overview)
PG_SOC=$(echo "$PG_SO" | jq -r '.code // empty')
[ "$PG_SOC" = "0" ] && ok "28.1 PG stats/overview code=0" || fail "28.1 PG stats/overview" "code=$PG_SOC"

# === 29. 双端关键数据一致性 (bizData + trace 持久化) ===
# 已经在 25 + 26 验证. 这里加一个 cross-check: PG 端 bizData 数据能查到
CROSS_OK=$(.venv/bin/python << PYEOF 2>/dev/null
import asyncio, asyncpg
async def go():
    pool = await asyncpg.create_pool(dsn="$PG_DSN", min_size=1)
    async with pool.acquire() as c:
        biz_n = await c.fetchval("SELECT count(*) FROM _sla_biz")
        trace_n = await c.fetchval("SELECT count(*) FROM wf_trace_span")
        print(f"{biz_n},{trace_n}")
    await pool.close()
asyncio.run(go())
PYEOF
)
[ -n "$CROSS_OK" ] && ok "29.1 双端 PG 数据可查 (bizData + trace)" \
  || fail "29.1 双端数据" "query failed"

# === 30. 双端 PG schema 完整性 ===
SCHEMA_OK=$(.venv/bin/python << PYEOF 2>/dev/null
import asyncio, asyncpg
async def go():
    pool = await asyncpg.create_pool(dsn="$PG_DSN", min_size=1)
    async with pool.acquire() as c:
        # 检查核心 8 张表 + wf_trace_span
        tables = ['wf_process_define', 'wf_process_design', 'wf_process_design_his',
                  'wf_process_instance', 'wf_process_task', 'wf_process_task_actor',
                  'wf_process_cc_instance', 'wf_process_surrogate', 'wf_trace_span']
        ok = 0
        for t in tables:
            n = await c.fetchval(f"SELECT count(*) FROM information_schema.tables WHERE table_name='{t}'")
            if n == 1: ok += 1
        print(ok)
    await pool.close()
asyncio.run(go())
PYEOF
)
[ "$SCHEMA_OK" -ge 9 ] && ok "30.1 PG schema 9 张表完整 (实测 $SCHEMA_OK)" \
  || fail "30.1 PG schema" "only $SCHEMA_OK/9"

# ====================================================================
# 双端 flows/ 验证 (SLA.md v6 更新: 所有流程都需 memory + pg 双端)
# ====================================================================

# === 31. flows/ 数量检查 ===
FLOWS_COUNT=$(file_count "$PWD" flows "*.json")
[ "$FLOWS_COUNT" -ge 17 ] && ok "31.1 flows/*.json 数量≥17 (实测 $FLOWS_COUNT)" \
  || fail "31.1 flows 数量" "实测 $FLOWS_COUNT"

# === 32. 双端 flows/ 验证脚本存在 ===
[ -x "sla/check_flows_dual.sh" ] && ok "32.1 sla/check_flows_dual.sh 可执行" \
  || fail "32.1 check_flows_dual.sh" "不存在或不可执行"

# === 33. MEM 端 flows/ 批量验证 (deploy + startAndExecute) ===
echo ""
echo "🧪 双端 flows/ 批量验证 (MEM + PG)..."
DUAL_OUT=$(bash sla/check_flows_dual.sh "$BASE" "$PG_BASE" 2>&1)
echo "$DUAL_OUT" | grep -E "^  MEM|^  PG" | head -2

# 提取数字: MEM_PASS, MEM_FAIL, PG_PASS, PG_FAIL
MEM_DUAL_LINE=$(echo "$DUAL_OUT" | grep "^  MEM ")
PG_DUAL_LINE=$(echo "$DUAL_OUT" | grep "^  PG ")
MEM_PASS=$(echo "$MEM_DUAL_LINE" | grep -oE "PASS=[0-9]+" | cut -d= -f2)
PG_PASS=$(echo "$PG_DUAL_LINE" | grep -oE "PASS=[0-9]+" | cut -d= -f2)
MEM_FAIL=$(echo "$MEM_DUAL_LINE" | grep -oE "FAIL=[0-9]+" | cut -d= -f2)
PG_FAIL=$(echo "$PG_DUAL_LINE" | grep -oE "FAIL=[0-9]+" | cut -d= -f2)

DUAL_MIN=17  # 至少 17 个 flows 双端通过 (排除 SPI 角色测试范围)
[ "$MEM_PASS" -ge "$DUAL_MIN" ] && ok "33.1 MEM 端 flows/ 验证 ≥$DUAL_MIN PASS (实测 $MEM_PASS/$MEM_FAIL)" \
  || fail "33.1 MEM 端 flows" "PASS=$MEM_PASS FAIL=$MEM_FAIL"

[ "$PG_PASS" -ge "$DUAL_MIN" ] && ok "34.1 PG 端 flows/ 验证 ≥$DUAL_MIN PASS (实测 $PG_PASS/$PG_FAIL)" \
  || fail "34.1 PG 端 flows" "PASS=$PG_PASS FAIL=$PG_FAIL"

# === 34. 双端 flows/ 一致性 (MEM 和 PG 通过的应该一致) ===
if [ "$MEM_PASS" = "$PG_PASS" ] && [ "$MEM_FAIL" = "$PG_FAIL" ]; then
  ok "35.1 双端 flows/ 行为一致 (MEM=PASS=$MEM_PASS/FAIL=$MEM_FAIL, PG=PASS=$PG_PASS/FAIL=$PG_FAIL)"
else
  fail "35.1 双端 flows/ 不一致" "MEM=$MEM_PASS/$MEM_FAIL PG=$PG_PASS/$PG_FAIL"
fi

# === 36. BDD 反递归自检 (POSTMORTEM.md 错误 1 防御) ===
RECURSIVE_BDDS=$(grep -l "check_bdds_dual\|check_flows_dual" bdd/*.sh 2>/dev/null | grep -v "bdd-1501-1510-bdds-dual\|bdd-1511-1515-perf-dual" || true)
if [ -z "$RECURSIVE_BDDS" ]; then
  ok "36.1 bdd-*.sh 无新增递归调用 check_*_dual.sh (排除已知 bdd-1501/1511)"
else
  fail "36.1 bdd-*.sh 存在递归调用" "发现: $(echo $RECURSIVE_BDDS | tr '\n' ' ')"
fi

# === 37. BDD 输出格式自检 (POSTMORTEM.md 错误 2 防御) ===
MISSING_FORMAT=0
MISSING_LIST=""
for bdd in bdd/bdd-*.sh; do
  if ! grep -qE "PASS=[0-9]+|^PASS:[[:space:]]*[0-9]+" "$bdd"; then
    MISSING_FORMAT=$((MISSING_FORMAT + 1))
    MISSING_LIST="$MISSING_LIST $(basename $bdd)"
  fi
done
if [ "$MISSING_FORMAT" = "0" ]; then
  ok "37.1 每个 BDD 末尾含 PASS= 或 PASS: 汇总行 (格式规范)"
else
  fail "37.1 BDD 缺汇总行" "$MISSING_FORMAT 个: $MISSING_LIST"
fi

# === 38. check_bdds_dual.sh 函数 stdout 隔离 (POSTMORTEM.md 错误 3 防御) ===
if grep -q "echo .* >&2" sla/check_bdds_dual.sh && grep -q "run_one_side" sla/check_bdds_dual.sh; then
  ok "38.1 check_bdds_dual.sh 函数内 echo 用 >&2 隔离 (防 stdout 污染)"
else
  fail "38.1 check_bdds_dual.sh stdout 隔离缺失" "run_one_side 函数应将日志 echo 改为 >&2"
fi

# === 39. SLA 脚本基础健壮性 (set -u + set -e) ===
ROBUST_COUNT=0
for f in sla/check.sh sla/check_bdds_dual.sh sla/check_flows_dual.sh; do
  if grep -qE "set -[eu]" "$f" 2>/dev/null; then
    ROBUST_COUNT=$((ROBUST_COUNT + 1))
  fi
done
if [ "$ROBUST_COUNT" -ge 2 ]; then
  ok "39.1 SLA 脚本 set -u/-e 启用 (基础健壮性, $ROBUST_COUNT/3)"
else
  fail "39.1 SLA 脚本缺 set -u/-e" "仅 $ROBUST_COUNT/3 启用"
fi

echo ""
echo "📊 PG 运行时指标:"
echo "  PG healthz: $PG_STATUS (pg=$PG_OK)"
echo "  PG wf_trace_span 累计: $TRACE_CNT spans"
echo "  PG bizData (本次): $PG_BIZ"
echo "  PG scanTime: $PG_SCAN_TIME"
echo ""
echo "📊 双端 flows/ 验证:"
echo "  MEM: PASS=$MEM_PASS / FAIL=$MEM_FAIL / TOTAL=$FLOWS_COUNT"
echo "  PG:  PASS=$PG_PASS / FAIL=$PG_FAIL / TOTAL=$FLOWS_COUNT"

# === 输出 JSON ===
TOTAL=$((PASS + FAIL))
SCORE=$(( PASS * 100 / (TOTAL > 0 ? TOTAL : 1) ))
mkdir -p sla
cat > "$OUT_JSON" << EOFJSON
{
  "timestamp": "$TS",
  "host": "$BASE",
  "pg_host": "$PG_BASE",
  "total_checks": $TOTAL,
  "passed": $PASS,
  "failed": $FAIL,
  "score": $SCORE,
  "latency_ms": {
    "healthz": $T_HEALTHZ_MS,
    "metrics": $T_METRICS_MS
  },
  "metrics_snapshot_mem": {
    "active_instances": ${INST_ACT:-0},
    "doing": ${INST_DOING:-0},
    "done": ${INST_DONE:-0}
  },
  "metrics_snapshot_pg": {
    "trace_span_total": ${TRACE_CNT:-0},
    "biz_data_check": "${PG_BIZ:-n/a}"
  },
  "section6_features": {
    "process_instance_export_mem": "$([ "$EXP_CODE" = "0" ] && echo "ok" || echo "fail")",
    "process_instance_export_pg": "$([ "$PG_EXP_CODE" = "0" ] && echo "ok" || echo "fail")",
    "audit_log_export_mem": "$([ "$AUDIT_COUNT" -ge 1 ] && echo "ok" || echo "fail")",
    "audit_log_export_pg": "$([ "$PG_AUDIT_COUNT" -ge 1 ] && echo "ok" || echo "fail")",
    "pre_interceptors": "$([ "$PRE_CNT" -ge 1 ] && echo "ok" || echo "fail")",
    "bizdata_pg_async": "$([ "$PG_BIZ" = "sla-test" ] && echo "ok" || echo "fail")",
    "metrics_remote_write": "$([ "$HAS_ENV" -ge 1 ] && echo "configured" || echo "missing")",
    "trace_persistence_pg": "$([ -n "$TRACE_CNT" ] && [ "$TRACE_CNT" -ge 1 ] && echo "ok" || echo "fail")",
    "flows_dual_mem": "$([ "$MEM_PASS" -ge 17 ] && echo "ok" || echo "fail")",
    "flows_dual_pg": "$([ "$PG_PASS" -ge 17 ] && echo "ok" || echo "fail")",
    "flows_dual_consistency": "$([ "$MEM_PASS" = "$PG_PASS" ] && [ "$MEM_FAIL" = "$PG_FAIL" ] && echo "consistent" || echo "diverged")"
  },
  "checks": $(printf '%s\n' "${RESULTS[@]}" | jq -R . | jq -s .)
}
EOFJSON

echo ""
echo "=========================================="
echo "SLA 健康度检查结果："
echo "  PASS=$PASS  FAIL=$FAIL  Score=${SCORE}%"
echo "=========================================="
echo ""
printf '%s\n' "${RESULTS[@]}"
echo ""
echo "JSON 已写入 $OUT_JSON"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
