#!/bin/bash
# BDD #1306-#1310: §6.1.2 bizData PG 异步 meta_reader (FIX-T95 2026-09-20)
# 覆盖: PG 端 bizData 不再 raise "未注册", 返回原始 row (无 meta_defs fallback)

set -e
HOST_PG=http://localhost:8102
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

# 准备 test_biz 表 + relTableName 流程
PG_DSN="postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm"
.venv/bin/python -c "
import asyncio, asyncpg
async def go():
    pool = await asyncpg.create_pool(dsn='$PG_DSN', min_size=1, max_size=1)
    async with pool.acquire() as c:
        await c.execute('DROP TABLE IF EXISTS test_biz_bdd')
        await c.execute('CREATE TABLE test_biz_bdd (id SERIAL PRIMARY KEY, process_instance_id BIGINT, biz_name TEXT, biz_amount INT)')
    await pool.close()
asyncio.run(go())
print('table ok')
"

# 准备流程 JSON
cat > /tmp/test-biz-bdd.json << 'JEOF'
{
  "name": "biz-bdd",
  "displayName": "bizBdd",
  "relTableName": "test_biz_bdd",
  "nodes": [
    {"id": "start", "type": "snaker:start", "properties": {}},
    {"id": "apply", "type": "snaker:task", "properties": {"assignee": "user1"}},
    {"id": "end", "type": "snaker:end", "properties": {}}
  ],
  "edges": [
    {"id": "e0", "sourceNodeId": "start", "targetNodeId": "apply"},
    {"id": "e1", "sourceNodeId": "apply", "targetNodeId": "end"}
  ]
}
JEOF

curl -s -X POST $HOST_PG/api/reset >/dev/null
DESIGN=$(curl -s -X POST $HOST_PG/wf/processDesign/save -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat /tmp/test-biz-bdd.json)" '{name:"biz-bdd",displayName:"bizBdd",content:$c}')" | jq -r '.data.id')
DEF=$(curl -s -X POST $HOST_PG/wf/processDesign/deploy -H "Content-Type: application/json" -d "{\"id\":$DESIGN}" | jq -r '.data.processDefineId')
INST=$(curl -s -X POST $HOST_PG/wf/processInstance/startAndExecute -H "Content-Type: application/json" -d "{\"processDefineId\":$DEF,\"operator\":\"user1\"}" | jq -r '.data.processInstanceId')

# 插入一条匹配 inst_id 的 biz 数据
.venv/bin/python -c "
import asyncio, asyncpg
async def go():
    pool = await asyncpg.create_pool(dsn='$PG_DSN', min_size=1, max_size=1)
    async with pool.acquire() as c:
        await c.execute('INSERT INTO test_biz_bdd (process_instance_id, biz_name, biz_amount) VALUES (\$1, \$2, \$3)', $INST, 'hello-bdd', 12345)
    await pool.close()
asyncio.run(go())
"

# === #1306: bizData 不再 raise "未注册" ===
RESP=$(curl -s "$HOST_PG/wf/processInstance/bizData" -H "Content-Type: application/json" -d "{\"id\":$INST}")
CODE=$(echo "$RESP" | jq -r '.code')
assert_eq "1306 bizData PG code=0 (不再 raise 未注册)" "$CODE" "0"

# === #1307-1309: 返回字段正确 ===
BIZ_NAME=$(echo "$RESP" | jq -r '.data.biz_name')
BIZ_AMT=$(echo "$RESP" | jq -r '.data.biz_amount')
PID=$(echo "$RESP" | jq -r '.data.process_instance_id')
assert_eq "1307 bizData.data.biz_name=hello-bdd" "$BIZ_NAME" "hello-bdd"
assert_eq "1308 bizData.data.biz_amount=12345" "$BIZ_AMT" "12345"
assert_eq "1309 bizData.data.process_instance_id=$INST" "$PID" "$INST"

# === #1310: 不存在的数据返回 null ===
INST_NEW=$(curl -s -X POST $HOST_PG/wf/processInstance/startAndExecute -H "Content-Type: application/json" -d "{\"processDefineId\":$DEF,\"operator\":\"user2\"}" | jq -r '.data.processInstanceId')
RESP2=$(curl -s "$HOST_PG/wf/processInstance/bizData" -H "Content-Type: application/json" -d "{\"id\":$INST_NEW}")
DATA=$(echo "$RESP2" | jq -r '.data')
assert_eq "1310 bizData 无业务数据时 data=null" "$DATA" "null"

echo "=========================================="
echo "BDD §6.1.2 bizData PG 端："
echo "  PASS=$PASS  FAIL=$FAIL"
echo "=========================================="
echo -e "$RESULTS"
[ $FAIL -eq 0 ] && exit 0 || exit 1
