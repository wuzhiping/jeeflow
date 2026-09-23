# SOP: auto_deploy_fdep 双端验证 (auto-deploy-fdep)

> **所属**：组织 SOP 集（与 spi-verify / tdd-flow / flow-folder 并列）
> **代码位置**：`main_common.auto_deploy_fdep(facade)` + `main_common.run_auto_deploy_fdep(facade)`
> **入口**：main.py（memory 端）/ main_pg.py（PG 端）
> **触发时机**：引擎启动后，DOING 扫描之后

---

## 1. 目的

引擎启动后自动检查并部署 `ToT/flows/fdep.json`，保证 fdep 流程始终可用，无需人工干预。

## 2. 触发条件（AND）

| # | 条件 | 检查方式 |
|---|------|----------|
| 1 | `ToT/flows/fdep.json` 文件存在 | `Path.exists()` |
| 2 | 引擎内尚未定义 `name == "fdep"` 的流程 | `facade.flow("processDefine/getLastByName", {"processDefineName": "fdep"})` |

满足两条 → 通过 `facade.flow("processDefine/deploy", ...)` 自动部署。

任一不满足 → 跳过并打印日志。

## 3. 双端接入位置

| 端 | 文件 | 调用 | 包装函数 |
|----|------|------|----------|
| **memory** (8101) | `main.py` | `run_auto_deploy_fdep(facade)` | `run_auto_deploy_fdep`（兼容 uvicorn reload 事件循环） |
| **PG** (8102) | `main_pg.py` | `await auto_deploy_fdep(facade)` | 直接 await（FastAPI lifespan 已是 async） |

## 4. 实测验证（2026-09-22 8 次启动）

### 4.1 Memory 端（main.py / 8101）

| 启动次序 | 启动前 fdep | 启动日志 | 启动后 fdep | 状态 |
|----------|-------------|----------|-------------|------|
| 1 | 0（memory 进程重启清空） | `[auto-deploy-fdep] ✅ 已部署: {'processDefineId': '20'}` | 1（id=20） | ✅ |
| 2 | 0（进程再重启清空） | `[auto-deploy-fdep] ✅ 已部署: {'processDefineId': '20'}` | 1（id=20） | ✅ |

**特性**：每次启动都部署（memory 端 repo 每次进程启动都重置，故"已部署"判断恒为 False）。这与 memory 端 seed 加载行为一致（每次都重新加载）。

### 4.2 PG 端（main_pg.py / 8102）

| 启动次序 | 启动前 fdep | 启动日志 | 启动后 fdep | 状态 |
|----------|-------------|----------|-------------|------|
| 1 | 0 | `[auto-deploy-fdep] ✅ 已部署: {'processDefineId': '1790038707301000'}` | 1 | ✅ |
| 2 | 1（首次部署遗留） | `[auto-deploy-fdep] ✅ 已部署: {'processDefineId': '1790038718327000'}` | **2** ⚠️ | ❌ |
| 2 修正后 | 2 | `[auto-deploy-fdep] 跳过: fdep 已部署 (id=1790038718327000)` | 2 | ✅ |

**Bug 发现与修复**：第 2 次 PG 启动未跳过，因为 `getLastByName` 实际参数名是 `processDefineName`（不是 `name`）。修正 `main_common.auto_deploy_fdep` 后行为正确。

**遗留数据**：测试产生了 2 条 fdep 定义（id 不同），是修正前的 bug 产物。修正后重启不会再增。

## 5. 错误处置

| 现象 | 原因 | 修复 |
|------|------|------|
| 启动报 `[auto-deploy-fdep] 跳过: .../fdep.json 不存在` | fdep.json 文件被移走或路径错 | 确认 `ToT/flows/fdep.json` 存在 |
| 启动报 `[auto-deploy-fdep] 跳过: fdep 已部署 (id=N)` | 已部署（PG 端正常） | 无需处理 |
| 启动报 `[auto-deploy-fdep] ❌ 部署失败: {...}` | JSON 解析失败或 deploy 校验失败 | 跑 `tdd-flow.py` 静态校验先定位 |
| 启动报 `[auto-deploy-fdep] ❌ 部署异常: ...` | 异常（DB 断开等） | 不阻塞启动，下次重启再试 |
| Memory 端每次启动都看到 deploy 日志 | 正常（memory 端 repo 每次清空） | 无需处理 |

## 6. 一致性自检命令

```bash
# Memory 端（确认 fdep 部署成功）
curl -s -X POST http://127.0.0.1:8101/wf/processDefine/page \
    -H "Content-Type: application/json" \
    -d '{"pageNum":1,"pageSize":999}' \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print([r for r in d['data']['rows'] if r['name']=='fdep'])"

# PG 端（直接查表）
.venv/bin/python3 -c "
import asyncio, asyncpg, os
async def q():
    conn = await asyncpg.connect(os.environ['JEEFLOW_PG_DSN'])
    rows = await conn.fetch(\"SELECT id, name, state FROM wf_process_define WHERE name='fdep'\")
    print(f'count={len(rows)}', [(r['id'], r['state']) for r in rows])
    await conn.close()
asyncio.run(q())
"
```

## 7. 修改记录（main_common.py）

| 字段 | 值 |
|------|---|
| 函数 | `auto_deploy_fdep(facade)` (async) + `run_auto_deploy_fdep(facade)` (sync wrapper) |
| 入参 | `facade: JeeflowFacade` |
| 路径计算 | `Path(__file__).resolve().parent / "ToT" / "flows" / "fdep.json"` |
| 关键 facade 调用 | `processDefine/getLastByName` + `processDefine/deploy` |
| 异常处理 | 捕获所有异常，print 日志，不抛（不阻塞启动） |

## 8. 临时任务标记

> ⚠️ 本任务为**临时**性质（按用户口头指令落地，未走 §10 流程定义规范）。
> 正式化需：① 把 fdep.json 纳入 `flows_resolver.dir()` 或单独的 deploy 机制；② 写 §10 增量章节；③ flow-lint.py 增量校验 deploy 入口。

## 9. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 初稿：memory (main.py) + PG (main_pg.py) 双端落地；首次双测通过；bug 修复（`getLastByName` 参数名 `processDefineName`）；验证矩阵：memory=2/2 deploy（预期），PG=1 deploy + 1 skip（修正后） |
