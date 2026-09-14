"""jeeflow FastAPI demo（PostgreSQL 版）—— boot2 接口规范对齐。

PG 模式与内存版（main.py）路由契约完全一致；差异：
- pool / repo / ext_repo / facade / 流程定义种子 / 业务数据种子 全部在 FastAPI lifespan 异步上下文创建；
- 重置路径走 TRUNCATE … RESTART IDENTITY CASCADE，不依赖内部字典；
- 所有仓储读取改为 JdbcRepository 的 async API（find_define_by_id / query_*_for_stats / find_task_actors）。
"""
import asyncio
import json
import mimetypes
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

mimetypes.add_type("application/javascript", ".cjs")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

import asyncpg
from jeeflow import EngineImpl, EventType, ProcessEvent, JeeflowFacade, \
    EngineExtensions, HandlerRegistry, register_builtin_assignments, JdbcRepository
from jeeflow.repository.postgres import PostgresAdapter
from jeeflow.repository.ext import JdbcProcessExtRepository
from jeeflow.model import InstanceState, TaskState, ProcessDefine, ProcessInstance, ProcessTask, UserInfo, parse_flow_model
from jeeflow.spi import IDGenerator, ExpressionEvaluator, OrgUserProvider

import flows_resolver
sys.path.insert(0, os.path.dirname(__file__))  # uvicorn demo.main:app 从仓根导入时 demo/ 不在 sys.path
from seed_business import seed_business

# ─── Setup ───────────────────────────────────────────────────────────────────────

# 流程定义：只读本仓 flows/（flows_resolver 已在维护者机器上把 Java 源精确镜像进来）
FLOWS_DIR = flows_resolver.dir()

# 复位时统一清空的 PG 表清单（按 FK 依赖反序）
PG_TABLES = [
    "wf_process_cc_instance",
    "wf_process_task_actor",
    "wf_process_task",
    "wf_process_instance",
    "wf_process_define",
    "wf_process_surrogate",
    "wf_process_design_his",
    "wf_process_design",
]

PG_DSN = os.environ.get(
    "JEEFLOW_PG_DSN",
    "postgresql://uid:pwd@127.0.0.1:5432/jeeflow",
)


class SnowflakeIDGen(IDGenerator):
    """简化雪花 ID"""
    def __init__(self):
        self._epoch = 1700000000000
        self._seq = 0

    def next_id(self) -> int:
        import time
        ts = int(time.time() * 1000) - self._epoch
        self._seq = (self._seq + 1) & 0xFFF
        return (ts << 10) | self._seq


class SimpleExprEvaluator(ExpressionEvaluator):
    """简易 SpEL 表达式：支持 amount >/>=/</<=/== number"""
    async def eval(self, expr: str, vars: dict):
        import re
        m = re.match(r"^\s*(\w+)\s*(>=|<=|!=|==|>|<)\s*(\d+(?:\.\d+)?)\s*$", expr)
        if not m:
            return False
        key, op, val = m.group(1), m.group(2), float(m.group(3))
        actual = vars.get(key)
        if actual is None:
            return False
        actual = float(actual)
        if op == ">": return actual > val
        if op == ">=": return actual >= val
        if op == "<": return actual < val
        if op == "<=": return actual <= val
        if op == "==": return actual == val
        if op == "!=": return actual != val
        return False


from demo import SimpleUserProvider, DemoOrgUserProvider, demo_user_search, DEMO_USERS, DEMO_ROLES, DEMO_DICTS


async def _truncate_all(adapter: PostgresAdapter) -> None:
    """清空 PG 演示表（identity 复位 + 级联）。单事务，保证重置原子性。"""
    conn = await adapter.acquire()
    try:
        await conn.begin()
        sql = "TRUNCATE TABLE " + ", ".join(PG_TABLES) + " RESTART IDENTITY CASCADE"
        await conn.execute(sql, ())
        await conn.commit()
    except BaseException:
        await conn.rollback()
        raise
    finally:
        await adapter.release(conn)


async def load_seed(repo: JdbcRepository) -> int:
    """预加载流程定义（种子）——/api/reset 重置后复用。返回写入条数。"""
    written = 0
    for fname in sorted(os.listdir(FLOWS_DIR)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(FLOWS_DIR, fname), "r", encoding="utf-8") as f:
            raw = json.loads(f.read())
        d = ProcessDefine(
            name=raw.get("name", fname),
            displayName=raw.get("displayName", fname),
            type=raw.get("type", ""),
            state=1,
            content=json.dumps(raw, ensure_ascii=False),
        )
        await repo.save_define(d)
        written += 1
    return written


# ─── 启动期补丁 ─────────────────────────────────────────────────────────────────
# seed_business.py / demo.py / docs/pg_schema.sql 不可改动；本模块在 lifespan 内对
# facade.flow 与 repo 的写方法做轻量 wrap，把入参规整成 PG 能接受的形态，再透传给原
# 实现。三个 known issue：
#   A. processSurrogate/save|update 调用方不一定传 enabled；facade._apply_surrogate_fields
#      兜底写入 int 1；PG wf_process_surrogate.enabled 列是 BOOLEAN，asyncpg 拒收 → 在
#      facade.flow 入口强转 args["enabled"]=bool(...)（无值则默认 True），并在 ext_repo 的
#      save/update_surrogate 处再做一次 s.enabled 兜底（防御深度，覆盖 _apply_surrogate_fields
#      在 _orig_flow 内部补默认值的情况）。
#   B. seed_business.py 用 1..15 的 ordinal（= load_seed 按文件名字典序写入的次序）
#      指代 processDefineId；PG 真实 id 是雪花 ID（远大于 10^13），按 ordinal 索引
#      page_defines DESC 列表并翻序，写成真实的雪花 id。
#   C. seed_business.py 触发的 startAndExecute 一路执行到 repo.save_task；
#      ProcessTask.taskType / performType 默认 int 0，但 PG wf_process_task.task_type /
#      perform_type 列是 VARCHAR(64)，asyncpg 会报 `$5/$6: 0 (expected str, got int)`。
#      在 save_task 写入前强转 str 即可（base.py / model.py 均不可改）。
#   D. processDesign/save|update|updateDefine|deploy 一律把 ProcessDesign.isDeployed
#      写成 int 0/1（facade:382/400/462/501），PG wf_process_design.is_deployed 列是
#      BOOLEAN，asyncpg 拒收 → 在 ext_repo.save_design / update_design 落 SQL 前把
#      d.isDeployed 强转 bool（model.ProcessDesign.isDeployed 声明为 int: 0，不可改）。
_DEFINE_ORDINAL_CACHE: dict[int, int] = {}


async def _populate_define_ordinal_cache(repo: JdbcRepository) -> int:
    """拉全表 page_defines，按 DESC 顺序翻序后映射 ordinal → 雪花 id。

    page_defines 默认 ORDER BY id DESC；雪花 id 单调递增（ts 单调），所以 DESC 顺序
    = 倒序插入序 = 倒序字典序；reversed 后第 0 行 = 字典序第 1 个 = seed 里的 ordinal 1。
    """
    _DEFINE_ORDINAL_CACHE.clear()
    rows, _ = await repo.page_defines(page_num=1, page_size=999)
    for ord_, row in enumerate(reversed(rows), start=1):
        _DEFINE_ORDINAL_CACHE[ord_] = row.id
    return len(_DEFINE_ORDINAL_CACHE)


def _wrap_facade_flow(facade: JeeflowFacade, repo: JdbcRepository) -> None:
    """monkey-patch facade.flow：按 action 在分发前规整入参，再透传给原 flow。"""
    _orig_flow = facade.flow

    async def _safe_flow(action, args=None):
        args = dict(args or {})
        # Issue A：委托 enabled → bool（PG BOOLEAN 列不接受 int）。即使调用方未传 enabled，
        # facade._apply_surrogate_fields 会兜底写 int 1；此处先按 True 占位确保走 default 时
        # 也是 bool。真正下 SQL 时 ext_repo.save/update_surrogate 的二次兜底也会再校一次。
        if action in ("processSurrogate/save", "processSurrogate/update"):
            args["enabled"] = bool(args.get("enabled", 1))
        # Issue B：startAndExecute ordinal → 真实雪花 id
        if action in ("processDefine/startAndExecute", "processInstance/startAndExecute"):
            v = args.get("processDefineId")
            if isinstance(v, int) and 0 < v < 10**13:
                real = _DEFINE_ORDINAL_CACHE.get(v)
                if real is None:
                    # 缓存未命中（reset 后 ordinal 表变化）→ 实时刷新一次
                    await _populate_define_ordinal_cache(repo)
                    real = _DEFINE_ORDINAL_CACHE.get(v)
                if real is not None:
                    args["processDefineId"] = real
        return await _orig_flow(action, args)

    facade.flow = _safe_flow


def _coerce_task_str_fields(task: ProcessTask) -> None:
    """Issue C 步骤 1：把 ProcessTask 中该是 VARCHAR 的列从 int 兜底成 str。

    ProcessTask.taskType / performType 默认值是 int 0；PG wf_process_task.task_type /
    perform_type 列是 VARCHAR(64)，asyncpg 严格类型校验会拒收。seed_business.py 启动期
    触发的 startAndExecute 必然走这条路径。
    """
    if getattr(task, "taskType", None) is not None and not isinstance(task.taskType, str):
        task.taskType = str(task.taskType)
    if getattr(task, "performType", None) is not None and not isinstance(task.performType, str):
        task.performType = str(task.performType)


def _coerce_instance_str_fields(inst: ProcessInstance) -> None:
    """Issue C 步骤 1 扩展：把 ProcessInstance 中 VARCHAR 列做同样兜底。

    dataclass 默认值已是 str（parentNodeName="" 等），但 seed_business.py 路径中如
    果给这些字段赋了 int，asyncpg 同样会拒收。属于 Issue C 同源的轻量兜底。
    """
    for fld in ("parentNodeName", "businessNo", "createUser", "updateUser"):
        v = getattr(inst, fld, None)
        if v is not None and not isinstance(v, str):
            setattr(inst, fld, str(v))


def _coerce_surrogate_enabled(s) -> None:
    """Issue A 防御深度：ext_repo 写入前把 ProcessSurrogate.enabled 兜底成 bool。

    facade._apply_surrogate_fields 在 _orig_flow 内部把 args["enabled"] 缺省补成 int 1
    然后再写到 s.enabled；此处 ext_repo.save/update_surrogate 落 SQL 前再校一次，确保
    PG BOOLEAN 列永远收到 bool 而非 int（避免双 wrap 之间的窗口期仍出错）。
    """
    v = getattr(s, "enabled", None)
    if v is not None and not isinstance(v, bool):
        s.enabled = bool(v)


def _coerce_design_bool_fields(d) -> None:
    """Issue D 防御深度：ext_repo 写入前把 ProcessDesign.isDeployed 兜底成 bool。

    facade._processDesign_save/update/updateDefine/deploy 内部统一把 design.isDeployed
    写成 int 0/1（facade.py:382/400/462/501），ProcessDesign dataclass 声明 isDeployed: int
    = 0 也不可变；此处 ext_repo.save_design/update_design 落 SQL 前再校一次，确保 PG
    wf_process_design.is_deployed（BOOLEAN）永远收到 bool 而非 int。
    """
    v = getattr(d, "isDeployed", None)
    if v is not None and not isinstance(v, bool):
        d.isDeployed = bool(v)


def _wrap_repo_methods(repo: JdbcRepository, ext_repo: JdbcProcessExtRepository) -> None:
    """Issue C 步骤 2 + Issue A/D 防御深度：monkey-patch 关键写方法。

    - repo.save_task / repo.save_instance：调用前做 VARCHAR 兜底（_coerce_*_str_fields）。
    - ext_repo.save_surrogate / ext_repo.update_surrogate：调用前把 s.enabled 强转 bool。
    - ext_repo.save_design / ext_repo.update_design：调用前把 d.isDeployed 强转 bool。
    全部原地修改 dataclass 字段（mutable），不会破坏其他已绑定同名对象的引用。
    """
    _orig_save_task = repo.save_task
    _orig_save_instance = repo.save_instance

    async def _safe_save_task(task):
        _coerce_task_str_fields(task)
        return await _orig_save_task(task)

    async def _safe_save_instance(inst):
        _coerce_instance_str_fields(inst)
        return await _orig_save_instance(inst)

    repo.save_task = _safe_save_task
    repo.save_instance = _safe_save_instance

    _orig_save_surrogate = ext_repo.save_surrogate
    _orig_update_surrogate = ext_repo.update_surrogate

    async def _safe_save_surrogate(s):
        _coerce_surrogate_enabled(s)
        return await _orig_save_surrogate(s)

    async def _safe_update_surrogate(s):
        _coerce_surrogate_enabled(s)
        return await _orig_update_surrogate(s)

    ext_repo.save_surrogate = _safe_save_surrogate
    ext_repo.update_surrogate = _safe_update_surrogate

    _orig_save_design = ext_repo.save_design
    _orig_update_design = ext_repo.update_design

    async def _safe_save_design(d):
        _coerce_design_bool_fields(d)
        return await _orig_save_design(d)

    async def _safe_update_design(d):
        _coerce_design_bool_fields(d)
        return await _orig_update_design(d)

    ext_repo.save_design = _safe_save_design
    ext_repo.update_design = _safe_update_design

    # Issue D 读路径：page_designs / page_surrogates 通过 _build_ext_where 构造
    # "AND t.is_deployed = ?" / "AND t.enabled = ?" 时，前端传来的 0/1 是 int，
    # BOOLEAN 列拒收（同 Issue A 写入路径同根因）。在条件构建层把布尔列的值强转 bool。
    # 注意：原 _build_ext_where 对不在白名单的 condition 跳过但不计入 args，
    # 因此要按"被接受"的子集对齐参数，避免把 LIKE 参数误转 bool。
    _orig_build_ext_where = ext_repo._build_ext_where
    _BOOL_COL_SUFFIXES = ("_deployed",)  # t.enabled 不是后缀匹配，下面单独处理
    _BOOL_COL_EXACT = {"t.enabled"}

    def _safe_build_ext_where(conditions, whitelist):
        sql, args = _orig_build_ext_where(conditions, whitelist)
        if not args:
            return sql, args
        accepted = [c for c in (conditions or []) if c.column in whitelist]
        coerced = []
        for c, v in zip(accepted, args):
            col = getattr(c, "column", "")
            is_bool_col = (col in _BOOL_COL_EXACT
                           or any(col.endswith(suf) for suf in _BOOL_COL_SUFFIXES))
            coerced.append(bool(v) if is_bool_col and not isinstance(v, bool) else v)
        return sql, tuple(coerced)

    ext_repo._build_ext_where = _safe_build_ext_where

    # Issue E：stats_avg_completed_duration_seconds 里 SQL 是
    # "AVG(ts.max_finish - i.create_time)"，PG 的 timestamp-timestamp 返回 INTERVAL，
    # asyncpg 把 INTERVAL 解码为 datetime.timedelta。原代码 line 652 直接
    # "return int(r[0])"，对 timedelta 抛 TypeError（int() 不接受 timedelta）。
    # 原始实现位于 .venv/.../repository/base.py:637，不可改源；用 monkey-patch 覆盖。
    import functools
    _orig_stats_avg_dur = repo.stats_avg_completed_duration_seconds

    @functools.wraps(_orig_stats_avg_dur)
    async def _fixed_stats_avg_dur(start=None, end=None):
        sql = ("SELECT AVG(ts.max_finish - i.create_time) FROM wf_process_instance i "
               "INNER JOIN (SELECT process_instance_id, MAX(finish_time) AS max_finish "
               "FROM wf_process_task WHERE task_state = 20 GROUP BY process_instance_id) ts "
               "ON i.id = ts.process_instance_id WHERE i.state = 20")
        args: list = []
        if start:
            sql += " AND i.create_time >= ?"; args.append(start)
        if end:
            sql += " AND i.create_time < ?"; args.append(end)
        async with repo._conn() as conn:
            r = await conn.fetchone(repo._sql(sql), tuple(args))
        if not r or r[0] is None:
            return 0
        v = r[0]
        if hasattr(v, "total_seconds"):
            return int(v.total_seconds())
        return int(v)

    repo.stats_avg_completed_duration_seconds = _fixed_stats_avg_dur

    # Issue F：stats_completed_task_aggregate SQL 里有 "perform_type = 1" 字面量，
    # 但 wf_process_task.perform_type 在 PG 里是 VARCHAR(64)（对齐 jeeflow model
    # ProcessTask.performType=IntEnum，PG schema 把枚举存为字符串，见
    # docs/pg_schema.sql:42）。原 .venv/.../base.py:629 字面量 = 1 → PG 报
    # "operator does not exist: character varying = integer"。把字面量改字符串。
    _orig_stats_task_agg = repo.stats_completed_task_aggregate

    @functools.wraps(_orig_stats_task_agg)
    async def _fixed_stats_task_agg():
        async with repo._conn() as conn:
            r = await conn.fetchone(
                repo._sql(
                    "SELECT COUNT(*), "
                    "SUM(CASE WHEN perform_type = '1' THEN 1 ELSE 0 END), "
                    "SUM(CASE WHEN expire_time IS NOT NULL AND finish_time <= expire_time THEN 1 ELSE 0 END), "
                    "SUM(CASE WHEN expire_time IS NOT NULL THEN 1 ELSE 0 END) "
                    "FROM wf_process_task WHERE task_state = 20"
                ), ())
        if not r:
            return 0, 0, 0, 0
        return int(r[0] or 0), int(r[1] or 0), int(r[2] or 0), int(r[3] or 0)

    repo.stats_completed_task_aggregate = _fixed_stats_task_agg


# ─── 应用状态（lifespan 注入；路由闭包从这里取） ─────────────────────────────────

state: dict = {
    "pool": None,
    "adapter": None,
    "repo": None,
    "ext_repo": None,
    "facade": None,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动：建连接池 + repo/ext_repo + facade + 流程定义种子 + 业务种子；
    关闭：归还连接池。"""
    pool = await asyncpg.create_pool(dsn=PG_DSN, min_size=1, max_size=10)
    adapter = PostgresAdapter(pool)
    repo = JdbcRepository(adapter)
    ext_repo = JdbcProcessExtRepository(adapter)

    idgen = SnowflakeIDGen()
    user_prov = SimpleUserProvider()
    org_prov = DemoOrgUserProvider()
    engine = EngineImpl(repo, user_prov, idgen, SimpleExprEvaluator())
    _registry = HandlerRegistry()
    register_builtin_assignments(_registry, user_prov, org_prov)
    engine.set_extensions(EngineExtensions(registry=_registry))
    facade = JeeflowFacade(engine, repo, ext_repo, user_search=demo_user_search, org_prov=org_prov)

    state["pool"] = pool
    state["adapter"] = adapter
    state["repo"] = repo
    state["ext_repo"] = ext_repo
    state["facade"] = facade

    # Issue C：先 wrap repo 写方法（save_task / save_instance 类型兜底），
    # 再 wrap facade.flow（入参规整）；顺序无所谓，互不依赖。
    _wrap_repo_methods(repo, ext_repo)
    _wrap_facade_flow(facade, repo)

    try:
        pass
        # n = await load_seed(repo)
        # print(f"[main_pg] loaded {n} process definitions from {FLOWS_DIR}")
        # await _populate_define_ordinal_cache(repo)
        # print(f"[main_pg] define ordinal cache: {len(_DEFINE_ORDINAL_CACHE)}")
        # await seed_business(facade)
        # print("[main_pg] seed_business done")
    except Exception as e:
        print(f"[main_pg] startup seed failed: {e!r}（PG 可能未就绪或表未建）", file=sys.stderr)

    try:
        yield
    finally:
        await pool.close()


app = FastAPI(root_path=("/jeeflow"), title="jeeflow api", version="0.1.0", lifespan=lifespan)
# CORS——允许 jeeflow-ui (localhost:5173) 跨域直连
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

from fastapi.staticfiles import StaticFiles
app.mount(
    "/ui/",
    StaticFiles(
        directory="ui/apps/demo/dist",
        html=True,
    ),
    name="ui",
)


# ─── Helpers（boot2 CommonResult：code=0 成功 / 99999999 失败，字段 code/msg/data）──

def _ok(data=None):
    return {"code": 0, "msg": "成功", "data": data}


def _err(msg: str, code=99999999):
    return JSONResponse({"code": code, "msg": msg}, status_code=200)


def _page(rows, page_num=1, page_size=999):
    return {"pageNum": page_num, "pageSize": page_size, "rows": rows, "recordCount": len(rows), "totalPage": 1}


def _fmt_time(t):
    return t.strftime("%Y-%m-%d %H:%M:%S") if t else None


async def _inst_vo(inst: ProcessInstance, def_: ProcessDefine = None) -> dict:
    """ProcessInstanceVO：Entity 字段 + displayName + jsonObject + activeTaskList"""
    repo = state["repo"]
    if def_ is None:
        def_ = await repo.find_define_by_id(inst.defineId)
    vo = {
        "id": inst.id, "parentId": inst.parentId, "processDefineId": inst.defineId,
        "state": inst.state, "parentNodeName": inst.parentNodeName,
        "businessNo": inst.businessNo, "operator": inst.operator,
        "expireTime": _fmt_time(inst.expireTime), "variable": json.dumps(inst.variables, ensure_ascii=False),
        "createTime": _fmt_time(inst.createTime), "createUser": inst.createUser,
        "updateTime": _fmt_time(inst.updateTime), "updateUser": inst.updateUser,
    }
    if def_:
        vo["displayName"] = def_.displayName
        vo["name"] = def_.name
        vo["version"] = def_.version
        if def_.content:
            vo["jsonObject"] = json.loads(def_.content)
    vo["activeTaskList"] = [_task_vo(t) for t in inst.tasks if t.taskState == TaskState.DOING]
    return vo


def _task_vo(t: ProcessTask, inst: ProcessInstance = None, def_: ProcessDefine = None) -> dict:
    """ProcessTaskVO：Entity 字段 + 展示字段。注意 actorIds 在 JdbcRepository 水合时已填充（issues/110）。"""
    vo = {
        "id": t.id, "processInstanceId": t.processInstanceId,
        "taskName": t.taskName, "displayName": t.displayName,
        "taskType": t.taskType, "performType": t.performType,
        "taskState": t.taskState, "operator": t.actorId,
        "finishTime": _fmt_time(t.finishTime), "expireTime": _fmt_time(t.expireTime),
        "formKey": t.formKey, "taskParentId": t.parentTaskId,
        "variable": json.dumps(t.variables, ensure_ascii=False),
        "createTime": _fmt_time(t.createTime), "createUser": t.createUser,
        "updateTime": _fmt_time(t.updateTime), "updateUser": t.updateUser,
    }
    if inst and def_:
        vo["processDefineName"] = def_.name
        vo["processDefineDisplayName"] = def_.displayName
        vo["instanceCreateTime"] = _fmt_time(inst.createTime)
    vo["taskActorIdList"] = list(t.actorIds)
    return vo


async def _load_graph(define_id) -> Optional[dict]:
    repo = state["repo"]
    d = await repo.find_define_by_id(define_id)
    return json.loads(d.content) if d and d.content else None


# boot2 submitType 枚举
APPLY, AGREE, REJECT, ROLLBACK, JUMP, RE_APPLY = 0, 1, 2, 3, 4, 5
ROLLBACK_TO_OPERATOR, COUNTERSIGN_DISAGREE = 6, 20

# ─── 流程定义 ────────────────────────────────────────────────────────────────────


@app.post("/wf/{action:path}")
async def wf_flow(action: str, request: Request):
    """单入口门面转发（v1.5.0）：/wf/{action}，action 多段（如 processDefine/page）"""
    body = await request.json() if await request.body() else {}
    return await state["facade"].flow(action, body)


@app.post("/api/reset")
async def api_reset():
    """一键重置演示数据（issues/11）：清空 PG 表（identity 复位 + 级联）+ 重载流程定义种子 + 重跑业务种子。"""
    adapter = state["adapter"]
    repo = state["repo"]
    facade = state["facade"]
    await _truncate_all(adapter)
    n = await load_seed(repo)
    # await _populate_define_ordinal_cache(repo)
    # await seed_business(facade)
    return _ok({"reloadedDefines": n})


@app.get("/healthz")
async def healthz():
    """健康检查（四端对齐）"""
    pool_ok = state["pool"] is not None and not state["pool"]._closing
    return {"status": "UP", "backend": "python", "pg": "ok" if pool_ok else "down"}


@app.get("/api/stats")
async def api_stats(userId: str = "user1"):
    """统计：用户待办数（DOING 任务且用户为 actor）+ 我发起的实例数。

    注：JdbcRepository.query_tasks_for_stats() 返回的 TaskStatsRow 不含任务 id，
    无法按 actor 二次过滤；直接走 page_todo_tasks(actor_id=userId)，单查询拿 todo 行。
    """
    repo = state["repo"]
    todo_rows, _ = await repo.page_todo_tasks(page_num=1, page_size=9999, actor_id=userId)
    mine = await repo.query_instances_for_stats(state_in=None)
    my_inst = sum(1 for i in mine if i.operator == userId)
    return _ok({"todoCount": len(todo_rows), "myInstanceCount": my_inst})


@app.post("/api/users")
async def api_users(request: Request):
    """演示用户列表（与四后端同一套 8 个具名用户）：body.keyword 可选模糊检索"""
    body = await request.json() if await request.body() else {}
    keyword = str(body.get("keyword") or "").strip().lower()
    rows = []
    for uid, (real_name, post_name) in DEMO_USERS.items():
        if keyword and keyword not in uid.lower() and keyword not in real_name.lower():
            continue
        rows.append({
            "userId": uid, "realName": real_name,
            "deptId": "D01", "deptName": "研发部",
            "postId": "P01", "postName": post_name,
        })
    return _ok(rows)


@app.post("/api/roles")
async def api_roles(request: Request):
    """演示角色列表（与四后端同一套 4 个角色）：body.keyword 可选模糊检索"""
    body = await request.json() if await request.body() else {}
    keyword = str(body.get("keyword") or "").strip().lower()
    rows = []
    for role_id, role_name in DEMO_ROLES.items():
        if keyword and keyword not in role_id.lower() and keyword not in role_name.lower():
            continue
        rows.append({"roleId": role_id, "roleName": role_name})
    return _ok(rows)


@app.post("/api/dicts")
async def api_dicts(request: Request):
    """演示字典全集（与四后端同一套 wf_* 字典）：返回 [{code, items:[{value,label}]}]，前端按 code 索引缓存"""
    rows = [{"code": code, "items": list(items)} for code, items in DEMO_DICTS.items()]
    return _ok(rows)


if __name__ == "__main__":
    import uvicorn
    # 端口可覆盖（PORT 环境变量）：本机 8100 被残留进程占用时可 PORT=8101 起
    uvicorn.run("main_pg:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8101")), reload=True)