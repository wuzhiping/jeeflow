#!/bin/bash
set -e
PG_DSN="postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm"
HOST_PG=http://localhost:8102
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

HAS_TABLE=$(.venv/bin/python << 'PYEOF'
import asyncio, asyncpg
async def go():
    pool = await asyncpg.create_pool(dsn="postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm", min_size=1)
    async with pool.acquire() as c:
        n = await c.fetchval("SELECT count(*) FROM information_schema.tables WHERE table_name='wf_trace_span'")
        print(n)
    await pool.close()
asyncio.run(go())
PYEOF
)
assert_eq "1326 wf_trace_span 表已创建" "$HAS_TABLE" "1"

COUNT_BEFORE=$(.venv/bin/python << 'PYEOF'
import asyncio, asyncpg
async def go():
    pool = await asyncpg.create_pool(dsn="postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm", min_size=1)
    async with pool.acquire() as c:
        n = await c.fetchval("SELECT count(*) FROM wf_trace_span")
        print(n)
    await pool.close()
asyncio.run(go())
PYEOF
)
curl -s -X POST $HOST_PG/wf/processDesign/save -H "Content-Type: application/json" \
  -d '{"name":"trace-test-bdd","displayName":"t","content":"{\"nodes\":[]}"}' >/dev/null
sleep 1
COUNT_AFTER=$(.venv/bin/python << 'PYEOF'
import asyncio, asyncpg
async def go():
    pool = await asyncpg.create_pool(dsn="postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm", min_size=1)
    async with pool.acquire() as c:
        n = await c.fetchval("SELECT count(*) FROM wf_trace_span")
        print(n)
    await pool.close()
asyncio.run(go())
PYEOF
)
DELTA=$((COUNT_AFTER - COUNT_BEFORE))
[ "$DELTA" -ge 1 ] && assert_eq "1327 trace span 写入 PG (delta≥1)" "ok" "ok" || assert_eq "1327 trace span 写入 PG" "$DELTA" "1"

HAS_NAME=$(.venv/bin/python << 'PYEOF'
import asyncio, asyncpg
async def go():
    pool = await asyncpg.create_pool(dsn="postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm", min_size=1)
    async with pool.acquire() as c:
        row = await c.fetchrow("SELECT name FROM wf_trace_span WHERE name LIKE 'facade%' LIMIT 1")
        print(row["name"] if row else "none")
    await pool.close()
asyncio.run(go())
PYEOF
)
echo "$HAS_NAME" | grep -q "facade" && assert_eq "1328 span.name 包含 facade" "ok" "ok" || assert_eq "1328 span.name" "$HAS_NAME" "facade"

TID_LEN=$(.venv/bin/python << 'PYEOF'
import asyncio, asyncpg
async def go():
    pool = await asyncpg.create_pool(dsn="postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm", min_size=1)
    async with pool.acquire() as c:
        row = await c.fetchrow("SELECT trace_id FROM wf_trace_span ORDER BY id DESC LIMIT 1")
        print(len(row["trace_id"]) if row else 0)
    await pool.close()
asyncio.run(go())
PYEOF
)
[ "$TID_LEN" -ge 16 ] && assert_eq "1329 trace_id 长度≥16 (实测 $TID_LEN)" "ok" "ok" || assert_eq "1329 trace_id" "$TID_LEN" "16"

HAS_IDX=$(.venv/bin/python << 'PYEOF'
import asyncio, asyncpg
async def go():
    pool = await asyncpg.create_pool(dsn="postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm", min_size=1)
    async with pool.acquire() as c:
        n = await c.fetchval("SELECT count(*) FROM pg_indexes WHERE tablename='wf_trace_span'")
        print(n)
    await pool.close()
asyncio.run(go())
PYEOF
)
[ "$HAS_IDX" -ge 2 ] && assert_eq "1330 索引≥2 (实测 $HAS_IDX)" "ok" "ok" || assert_eq "1330 索引数" "$HAS_IDX" "2"

echo "=========================================="
echo "BDD §6.4.1 trace 持久化："
echo "  PASS=$PASS  FAIL=$FAIL"
echo "=========================================="
echo -e "$RESULTS"
[ $FAIL -eq 0 ] && exit 0 || exit 1
