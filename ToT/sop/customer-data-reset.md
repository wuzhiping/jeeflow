# SOP: 客户服务器数据 reset (customer-data-reset)

> **所属**：组织 SOP 集（与 engine-deploy 并列）
> **场景**：首次发布 / 重大版本切换前的客户测试服务器数据清理
> **永久规则**：见 `ToT/README.md#11-引擎部署规范` + §1 例外审批留档
> **职责分工**（按用户口头约定 v0.2 更新）：**AI 操作服务器 + 人工部署新引擎**
>   - AI（opencode）通过 HTTPS API 直接操作：reset / healthz / deploy / 测试
>   - 人工仅负责 push 新引擎代码 + 重启服务（触发 auto_deploy_fdep）

---

## 1. 适用场景

| ✅ 适用 | ❌ 不适用 |
|--------|-----------|
| 首次发布 fdep 流程到客户测试服务器 | 生产环境 |
| 引擎大版本升级（如 vendor/jeeflow 重构） | 已有真实用户数据且不可丢失 |
| 流程定义 schema 重大变更 | 仅调试单个 instance |
| 客户反馈"环境脏了"需清空重置 | — |

## 2. 职责分工（重要）

| 操作 | 执行方 | 工具/方式 |
|------|--------|-----------|
| 修改引擎代码（main.py / main_pg.py / main_common.py / main_meta.py / vendor/jeeflow/） | **人工** | git push + 部署 + 重启服务 |
| **reset 客户服务器数据** | **AI**（opencode） | `POST https://abc.feg.cn/jeeflow/api/reset` |
| 部署 / 重部署流程（如 fdep.json） | **AI** | `POST /wf/processDefine/deploy` |
| 健康检查 / smoke test | **AI** | `curl /healthz` + `startAndExecute` 等 |
| 留档 `ToT/customer-resets/` | **AI** | 自动写文件 |
| 通知客户"环境已重置可使用" | **AI** | 通过聊天/邮件（用户决定方式） |
| 服务端 SSH / restart / deploy 新引擎 | **人工** | 需 SSH 权限，AI 无 |

## 3. 前置检查（AI 操作，必做）

```bash
# 3.1 确认服务器可达
curl -sf -o /dev/null -w "HTTP %{http_code}\n" --max-time 5 https://abc.feg.cn/jeeflow/healthz
# 期望: HTTP 200

# 3.2 确认目标环境（healthz 返回体含 backend 信息）
curl -s https://abc.feg.cn/jeeflow/healthz
# 期望: {"status":"UP","backend":"python","pg":"ok"}

# 3.3 确认当前 PG 状态（通过 API，无须 PG DSN）
curl -s -X POST https://abc.feg.cn/jeeflow/wf/processDefine/page \
    -H "Content-Type: application/json" \
    -d '{"pageNum":1,"pageSize":999}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
rows = d.get('data', {}).get('rows', [])
print(f'  total defines: {len(rows)}')
for r in rows[:5]:
    print(f'    id={r[\"id\"]} name={r[\"name\"]} state={r.get(\"state\")}')
"

# 3.4 doing 实例盘点
curl -s -X POST https://abc.feg.cn/jeeflow/wf/processInstance/doingList \
    -H "Content-Type: application/json" \
    -d '{"limit":50}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
data = d.get('data') or {}
print(f'  doing instances: {data.get(\"instance_count\", 0)}')
"
```

## 4. reset 执行（PG 后端，AI 调用引擎 API）

### 4.1 优先方案：调用引擎 `/api/reset` 端点（推荐）

```bash
curl -s -X POST https://abc.feg.cn/jeeflow/api/reset \
    -H "Content-Type: application/json" \
    -d '{}' --max-time 30
# 期望: {"code":0,"msg":"成功","data":{"reloadedDefines":N}}
# N>0: reset 后自动重载了 seed flows
# N=0: reset 后未自动重载（需手动 deploy fdep.json）
```

底层行为（main_pg.py._reset_pg）：TRUNCATE 全部 wf_process_* + RESTART IDENTITY + 按需 reload seeds。

### 4.2 备选方案：直接 SQL TRUNCATE（仅当 /api/reset 不可用且 AI 拿到 PG DSN）

```sql
BEGIN;
TRUNCATE TABLE
    wf_process_cc_instance,
    wf_process_task_actor,
    wf_process_task,
    wf_process_instance,
    wf_process_define,
    wf_process_surrogate,
    wf_process_design_his,
    wf_process_design
RESTART IDENTITY CASCADE;
COMMIT;
```

## 5. 部署 fdep.json（reset 后必须，否则引擎无可用流程）

### 5.1 优先方案：AI 通过 API deploy 本地 fdep.json

```bash
# 用本地 ToT/flows/fdep.json 作为 body
python3 -c "
import json
content = open('/opt/jupyter/src/RD/projects/jeeFlow/ToT/flows/fdep.json').read()
print(json.dumps({'content': content, 'operator': 'system', 'name': 'fdep'}))
" > /tmp/opencode/fdep_deploy_body.json

curl -s -X POST https://abc.feg.cn/jeeflow/wf/processDefine/deploy \
    -H "Content-Type: application/json" \
    -d @/tmp/opencode/fdep_deploy_body.json --max-time 30
# 期望: {"code":0,"msg":"成功","data":{"processDefineId":"..."}}
```

### 5.2 备选方案：人工重启服务（触发 auto_deploy_fdep）

```bash
ssh <user>@abc.feg.cn "sudo systemctl restart jeeflow"
sleep 10
ssh <user>@abc.feg.cn "sudo journalctl -u jeeflow --since '30 seconds ago' | grep auto-deploy-fdep"
# 期望: [auto-deploy-fdep] ✅ 已部署: {'processDefineId': '...'}
```

## 6. 健康检查（AI 跑）

```bash
# 6.1 healthz
curl -s -o /dev/null -w "healthz: HTTP %{http_code}\n" --max-time 5 https://abc.feg.cn/jeeflow/healthz

# 6.2 fdep 已部署
curl -s -X POST https://abc.feg.cn/jeeflow/wf/processDefine/page \
    -H "Content-Type: application/json" \
    -d '{"pageNum":1,"pageSize":999}' --max-time 5 | python3 -c "
import sys, json
d = json.load(sys.stdin)
rows = d.get('data', {}).get('rows', [])
fdep = [r for r in rows if r.get('name') == 'fdep']
print(f'  total defines : {len(rows)}')
print(f'  fdep exists   : {\"✅\" if fdep else \"❌\"}  (id={fdep[0][\"id\"] if fdep else \"N/A\"})')
"

# 6.3 doingList 应为空
curl -s -X POST https://abc.feg.cn/jeeflow/wf/processInstance/doingList \
    -H "Content-Type: application/json" \
    -d '{"limit":10}' --max-time 5 | python3 -c "
import sys, json
d = json.load(sys.stdin)
data = d.get('data') or {}
print(f'  doing instances: {data.get(\"instance_count\", 0)}')
print(f'  doing tasks    : {data.get(\"task_count\", 0)}')
"

# 6.4 端到端 smoke（创建 + 推到 DONE）

**v0.3 起强制要求**：smoke test 必须**跑到底**（state=DONE），不只停在 stage_pm。

```bash
# Step 1: 创建 instance
START=$(curl -s -X POST https://abc.feg.cn/jeeflow/wf/processDefine/startAndExecute \
    -H "Content-Type: application/json" \
    -d "{\"processDefineId\":\"$FDEP_ID\",\"operator\":\"u_fdp_pm\"}" --max-time 15)
INSTANCE=$(echo "$START" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('processInstanceId',''))")
echo "  instance = $INSTANCE"

# Step 2: 循环推进每个 task 直到 DONE
for i in 1 2 3 4 5 6 7; do
    TODO=$(curl -s -X POST https://abc.feg.cn/jeeflow/wf/processTask/todoList \
        -H "Content-Type: application/json" \
        -d "{\"operator\":\"u_fdp_pm\",\"limit\":50}" --max-time 5 \
        | python3 -c "
import sys, json
rows = json.load(sys.stdin).get('data', {}).get('rows', [])
my = [t for t in rows if t.get('processInstanceId') == '$INSTANCE']
if my: print(f\"{my[0]['id']}|{my[0].get('taskName','')}\")
")
    TASK_ID=$(echo "$TODO" | cut -d'|' -f1)
    TASK_NAME=$(echo "$TODO" | cut -d'|' -f2)
    if [ -z "$TASK_ID" ]; then
        echo "  step $i: 无 todo，停止（可能已完成）"
        break
    fi
    EXEC_CODE=$(curl -s -X POST https://abc.feg.cn/jeeflow/wf/processTask/execute \
        -H "Content-Type: application/json" \
        -d "{\"processTaskId\":\"$TASK_ID\",\"operator\":\"u_fdp_pm\",\"submitType\":1}" \
        --max-time 15 \
        | python3 -c "import sys,json; print(json.load(sys.stdin).get('code',-1))")
    echo "  step $i: execute $TASK_NAME → code=$EXEC_CODE"
    [ "$EXEC_CODE" != "0" ] && break
    sleep 0.5
done

# Step 3: 验证终态
FINAL=$(curl -s -X POST https://abc.feg.cn/jeeflow/wf/processInstance/detail \
    -H "Content-Type: application/json" -d "{\"id\":\"$INSTANCE\"}" --max-time 5 \
    | python3 -c "
import sys, json
d = json.load(sys.stdin).get('data') or {}
state = d.get('state')
state_name = state.name if hasattr(state, 'name') else state
all_done = all(t.get('taskState').name == 'DONE' if hasattr(t.get('taskState'), 'name') else t.get('taskState') == 20 for t in d.get('tasks', []))
print(f'  state = {state_name}, all_done = {all_done}')
")
echo "  $FINAL"
```

期望输出：`state = DONE, all_done = True`

## 7. 留档（AI 自动写）

按 ToT/README.md §1 第 3 条例外审批规则，在 `ToT/customer-resets/` 目录创建：

```
ToT/customer-resets/YYYY-MM-DD_<domain>.md
```

模板见同目录 `2026-09-22_abc.feg.cn.md`（首次 reset 留档，AI 自动生成 + 回填实际结果）。

## 8. 完整命令清单（一键复制，AI 执行版）

```bash
# === 一键 reset + 部署 fdep + 健康检查（AI 全自动） ===

set -e
TARGET="https://abc.feg.cn/jeeflow"

# Step 1: 前置盘点
echo "[1/4] 测可达性"
curl -sf -o /dev/null -w "  healthz: HTTP %{http_code}\n" --max-time 5 "$TARGET/healthz"

echo "[2/4] 当前 define 盘点"
curl -s -X POST "$TARGET/wf/processDefine/page" \
    -H "Content-Type: application/json" \
    -d '{"pageNum":1,"pageSize":999}' \
    | python3 -c "import sys,json; print(f'  total defines: {len(json.load(sys.stdin)[\"data\"][\"rows\"])}')"

# Step 3: reset
echo "[3/4] /api/reset"
curl -s -X POST "$TARGET/api/reset" \
    -H "Content-Type: application/json" \
    -d '{}' --max-time 30
echo ""

# Step 4: deploy fdep.json
echo "[4/4] /wf/processDefine/deploy (fdep.json)"
python3 -c "
import json
content = open('/opt/jupyter/src/RD/projects/jeeFlow/ToT/flows/fdep.json').read()
print(json.dumps({'content': content, 'operator': 'system', 'name': 'fdep'}))
" | curl -s -X POST "$TARGET/wf/processDefine/deploy" \
    -H "Content-Type: application/json" \
    -d @- --max-time 30
echo ""

# Step 5: 验证
echo "[verify] fdep 部署 + healthz"
curl -sf -o /dev/null -w "  healthz: HTTP %{http_code}\n" "$TARGET/healthz"
curl -s -X POST "$TARGET/wf/processDefine/page" \
    -H "Content-Type: application/json" \
    -d '{"pageNum":1,"pageSize":999}' \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
rows = d['data']['rows']
fdep = [r for r in rows if r.get('name') == 'fdep']
print(f'  defines: {len(rows)}, fdep: {\"✅\" if fdep else \"❌\"}')
"
```

## 9. 风险与回滚

| 风险 | 缓解 |
|------|------|
| 误操作（清错环境） | 执行前确认 URL = `https://abc.feg.cn/jeeflow/`（非生产）；健康检查确认 backend |
| 客户真实数据丢失 | 仅在用户授权下执行；本 SOP §7 留档 |
| reset 后 fdep 缺失 | §5.1 AI 自动 deploy；§5.2 人工 restart 触发 auto_deploy_fdep |
| 引擎未重启导致下次 reset 又清掉 fdep | 通知人工重启一次服务（一次性） |
| fdep 部署但状态错 | `tdd-flow.py` 实测 happy/reject 路径 |

**回滚**：本场景默认无备份。如需恢复，只能从其他渠道（如 daily backup）拉回。**建议**：下次 SOP 改进为 "backup-then-reset" 模式。

## 10. 关联文档

- `ToT/sop/engine-deploy.md` — 引擎部署 5 步（人工负责的部分）
- `ToT/README.md#11-引擎部署规范` — 拓扑 + 职责分工
- `ToT/sop/auto-deploy-fdep.md` — 服务启动后自动部署机制
- `ToT/customer-resets/2026-09-22_abc.feg.cn.md` — 首次 reset 实际留档

## 11. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 初稿：首次发布 fdep 到 abc.feg.cn 前的客户服务器数据 reset 流程 |
| v0.2 | 2026-09-22 | **职责分工重写**（用户口头约定）：AI 操作服务器（reset / deploy / healthz / 留档），人工仅部署新引擎。补 §2 职责分工表 + §3/§5 API 调用 + §6 AI 跑健康检查 + §7 AI 留档 + §8 AI 一键命令清单。首次 reset 实际执行成功留档在 `ToT/customer-resets/2026-09-22_abc.feg.cn.md`。 |
| v0.3 | 2026-09-22 | **冒烟测试必须跑到底**（用户口头指令："the moke test should run to the end after doing the reset job"）：§6.4 smoke test 升级为"创建 + 循环推进到 DONE"，不再停在 stage_pm。循环 7 步兜底，期望终态 `state=DONE, all_done=True`。`doingList` 验证必须为 0。 |
