"""jeeflow FastAPI demo（PostgreSQL 版）—— boot2 接口规范对齐。

PG 模式与内存版（main.py）路由契约完全一致；差异：
- pool / repo / ext_repo / facade / 流程定义种子 / 业务数据种子 全部在 FastAPI lifespan 异步上下文创建；
- 重置路径走 TRUNCATE … RESTART IDENTITY CASCADE，不依赖内部字典；
- 所有仓储读取改为 JdbcRepository 的 async API（find_define_by_id / query_*_for_stats / find_task_actors）。

注意（2026-09-17 §36）：
- 本入口使用 PG 后端（JdbcRepository），拦截器未注册严格抛错
- 与 main.py（内存后端）行为有差异：main.py 拦截器未注册静默通过
- 拦截器相关测试建议用本入口（契约级行为）
- 详见 docs/known-issues.md §36 / docs/flow.md §2
"""
import asyncio
import json
import mimetypes
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

mimetypes.add_type("application/javascript", ".cjs")

# 优先使用本地 vendor/jeeflow（项目内嵌），避免依赖 .venv site-packages
_VENDOR = os.path.join(os.path.dirname(__file__), "vendor")
if _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

import asyncpg
from jeeflow import EngineImpl, EventType, ProcessEvent, JeeflowFacade, \
    EngineExtensions, HandlerRegistry, register_builtin_assignments, JdbcRepository
from jeeflow.extensions import FlowInterceptor
from jeeflow.engine import _find_node, _follow_edges, _sync_task_to_aggregate
from jeeflow.repository.postgres import PostgresAdapter
from jeeflow.repository.ext import JdbcProcessExtRepository
from jeeflow.model import InstanceState, TaskState, ProcessDefine, ProcessInstance, ProcessTask, UserInfo, parse_flow_model
from jeeflow.spi import IDGenerator, ExpressionEvaluator, OrgUserProvider

import flows_resolver
sys.path.insert(0, os.path.dirname(__file__))  # 确保 spi.py / seed_business.py 仓根模块可被 import
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
    """简易 SpEL 表达式：支持 amount >/>=/</<=/== number 和 #var==str；OGNL 风格 #varname 同支持

    v1.5.1-PG fix (FIX-T1 2026-09-17)：与 main.py 同步
    expr 是数字但 value 是字符串时，原 `actual = float(actual)` 抛 ValueError
    导致整个 startAndExecute 失败（code=99999999）。
    修复：捕获 ValueError/TypeError 返回 False，与 regex 不匹配、value 为 None 行为一致
    （走兜底首边）。

    v1.6.0-PG fix (FIX-T3 2026-09-17)：与 main.py 同步
    支持字符串相等比较 `#var==string` / `#var!=string`。
    原版只支持数字，字符串比较走兜底。
    """
    async def eval(self, expr: str, vars: dict):
        import re
        # 数字比较: #var op number
        m_num = re.match(r"^\s*(#?\w+)\s*(>=|<=|!=|==|>|<)\s*(\d+(?:\.\d+)?)\s*$", expr)
        # 字符串比较: #var == "string" 或 #var == string
        m_str = re.match(r'^\s*(#?\w+)\s*(==|!=)\s*"?([A-Za-z0-9_]+)"?\s*$', expr)
        if m_num:
            key, op, val = m_num.group(1).lstrip("#"), m_num.group(2), float(m_num.group(3))
            actual = vars.get(key)
            if actual is None:
                return False
            try:
                actual = float(actual)
            except (ValueError, TypeError):
                return False
            if op == ">": return actual > val
            if op == ">=": return actual >= val
            if op == "<": return actual < val
            if op == "<=": return actual <= val
            if op == "==": return actual == val
            if op == "!=": return actual != val
            return False
        if m_str:
            key, op, val = m_str.group(1).lstrip("#"), m_str.group(2), str(m_str.group(3))
            actual = vars.get(key)
            if actual is None:
                return False
            if op == "==": return str(actual) == val
            if op == "!=": return str(actual) != val
            return False
        return False


class RatioCapableEngine(EngineImpl):
    """比例会签扩展引擎：支持通用 countersignCompletionCondition（OGNL 表达式）。

    引擎默认 PARALLEL 仅识别 ONE_VOTE_VETO（jeeflow/engine.py:101）；其他 OGNL 条件
    （如 "#nrOfCompletedInstances==2"）会被忽略。此子类在 execute_process_task 中：
    1. 先调 EngineImpl.execute_process_task 原版完成当前 task（内部做 _prepare_execute_task + 推进）
    2. 重新查实例，统计 cur_node 的 nrOfCompletedInstances/nrOfInstances
    3. 若 cs_cond 非 ONE_VOTE_VETO + 求值通过 → 废弃剩余 DOING + 调用 _execute_node 推进下游

    注意：必须先 super 再判断比例条件，因为 super 内部已经把当前 task 从 DOING 推到 DONE，
    重复 _prepare_execute_task 会导致 "task not doing" 错误。

    cs_cond 同时支持 properties.countersignCompletionCondition（引擎实际读）和
    properties.field.countersignCompletionCondition（设计器输出），向后兼容。
    """

    async def execute_process_task(self, task_id: int, operator: str, args: dict = None):
        result = await EngineImpl.execute_process_task(self, task_id, operator, args)
        try:
            from jeeflow.model import parse_flow_model as _parse
            import json as _json
            def_ = await self.repo.find_define_by_id(result.defineId)
            if not def_: return result
            flow = _parse(_json.loads(def_.content))
            cur_task = await self.repo.find_task_by_id(task_id)
            if not cur_task: return result
            cur_node = _find_node(flow, cur_task.taskName)
            if not cur_node: return result
            ct = str(cur_node.properties.get("countersignType", "") or "").strip()
            cs_cond = ""
            p = cur_node.properties or {}
            cs_cond = str(p.get("countersignCompletionCondition", "") or "").strip()
            if not cs_cond:
                field = p.get("field", {}) or {}
                cs_cond = str(field.get("countersignCompletionCondition", "") or "").strip()
            is_ratio = ct in ("PARALLEL", "RATIO") and cs_cond and cs_cond.upper() != "ONE_VOTE_VETO"
            if not is_ratio:
                return result
            inst_after = result
            node_tasks = [t for t in (inst_after.tasks or []) if t.taskName == cur_node.id]
            completed = sum(1 for t in node_tasks if t.taskState == 20)
            total = len(node_tasks)
            eval_vars = dict(result.variables or {})
            eval_vars["nrOfCompletedInstances"] = completed
            eval_vars["nrOfInstances"] = total
            try:
                satisfied = bool(await self.expr_eval.eval(cs_cond, eval_vars))
            except Exception:
                satisfied = False
            if satisfied:
                now = datetime.now()
                still_doing = [t for t in node_tasks if t.taskState == 10]
                if still_doing:
                    for t in still_doing:
                        t.abandon(now)
                        await self.repo.update_task(t)
                        _sync_task_to_aggregate(inst_after, t)
                    for node in _follow_edges(flow, cur_node.id):
                        await self._execute_node(flow, inst_after, node, operator, eval_vars)
                    return await self.repo.find_instance_by_id(inst_after.id)
        except Exception as ex:
            print(f"[RatioCapableEngine] ratio check failed: {ex!r}", file=sys.stderr)
        return result


from spi import SimpleUserProvider, SpiOrgUserProvider, spi_user_search, SPI_USERS, SPI_ROLES, SPI_DICTS


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
# seed_business.py / spi.py / docs/pg_schema.sql 不可改动；本模块在 lifespan 内对
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
            # FIX-T10 (2026-09-17)：Issue D 业务 variables 嵌套解包已上移到 vendor/jeeflow/facade.py
            # vendor/jeeflow/facade.py:_startAndExecute 内自动 setdefault 展开 nested variables
            # 此处不再需要 monkey patch
        return await _orig_flow(action, args)

    facade.flow = _safe_flow


def _coerce_task_str_fields(task: ProcessTask) -> None:
    """FIX-T16 (2026-09-17) Issue C 步骤 1 VARCHAR 兜底已上移到 vendor。

    vendor/jeeflow/repository/base.py:save_task 内已 str(task.taskType/performType) 兜底
    vendor/jeeflow/repository/base.py:save_instance 内已 str(...) 兜底
    此处不再需要 monkey patch（vendor 是项目内嵌，优先级高于 site-packages）
    """


def _coerce_instance_str_fields(inst: ProcessInstance) -> None:
    """FIX-T16 (2026-09-17) Issue C 步骤 1 扩展 VARCHAR 兜底已上移到 vendor。

    vendor/jeeflow/repository/base.py:save_instance 内 str(parentNodeName/businessNo/...) 兜底
    """


def _coerce_surrogate_enabled(s) -> None:
    """FIX-T13 (2026-09-17) Issue A 防御深度已上移到 vendor。

    vendor/jeeflow/repository/ext.py:save_surrogate + update_surrogate 内已 bool() 兜底
    vendor/jeeflow/facade.py:_apply_surrogate_fields 内已 s.enabled = bool(s.enabled)
    此处不再需要 monkey patch（vendor 是项目内嵌，优先级高于 site-packages）
    """


def _coerce_design_bool_fields(d) -> None:
    """FIX-T14 (2026-09-17) Issue D 兜底已上移到 vendor。

    vendor/jeeflow/model.py:ProcessDesign.isDeployed 改为 Any 默认 False
    vendor/jeeflow/facade.py:_processDesign_* 改为 True/False
    vendor/jeeflow/repository/ext.py:save/update_design 内 bool() 兜底
    vendor/jeeflow/repository/ext.py:_map_design 读回 bool 统一
    此处不再需要 monkey patch（vendor 是项目内嵌，优先级高于 site-packages）
    """


def _wrap_repo_methods(repo: JdbcRepository, ext_repo: JdbcProcessExtRepository) -> None:
    """Issue C 步骤 2 + Issue A/D 防御深度：monkey-patch 关键写方法。

    - repo.save_task / repo.save_instance：调用前做 VARCHAR 兜底（_coerce_*_str_fields）。
    - ext_repo.save_surrogate / ext_repo.update_surrogate：调用前把 s.enabled 强转 bool。
    - ext_repo.save_design / ext_repo.update_design：调用前把 d.isDeployed 强转 bool。
    全部原地修改 dataclass 字段（mutable），不会破坏其他已绑定同名对象的引用。
    """

    # FIX-T16 (2026-09-17)：taskType/performType VARCHAR 兜底已上移到 vendor
    # vendor/jeeflow/repository/base.py:save_task 内 str(taskType/performType) 兜底
    # vendor/jeeflow/repository/base.py:save_instance 内 str(parentNodeName/businessNo/...) 兜底
    # 此处不再需要 monkey patch（vendor 是项目内嵌，优先级高于 site-packages）

    # FIX-T13 (2026-09-17)：surrogate enabled bool 兜底已上移到 vendor/jeeflow
    # vendor/jeeflow/facade.py:_apply_surrogate_fields 内 s.enabled = bool(s.enabled)
    # vendor/jeeflow/repository/ext.py:save/update_surrogate 内 bool() 兜底
    # 此处不再需要 monkey patch（vendor 是项目内嵌，优先级高于 site-packages）

    # FIX-T14 (2026-09-17)：design.isDeployed bool 兜底已上移到 vendor/jeeflow
    # vendor/jeeflow/model.py:ProcessDesign.isDeployed = Any 默认 False
    # vendor/jeeflow/facade.py:_processDesign_* 改 True/False
    # vendor/jeeflow/repository/ext.py:save/update_design 内 bool() 兜底 + _map_design 读回 bool
    # 此处不再需要 monkey patch

    # FIX-T15 (2026-09-17)：_build_ext_where BOOLEAN 列读路径兼容已上移到 vendor
    # vendor/jeeflow/repository/ext.py:_build_ext_where 内自动 bool() 兜底
    # 此处不再需要 monkey patch（vendor 是项目内嵌，优先级高于 site-packages）

    # FIX-T11 (2026-09-17)：Issue E stats_avg_completed_duration_seconds timedelta 兜底
    # 已上移到 vendor/jeeflow/repository/base.py:stats_avg_completed_duration_seconds
    # vendor 自动检测 timedelta（PG INTERVAL）→ total_seconds；其他后端（SQLite/MySQL）原样 int
    # 此处不再需要 monkey patch（vendor 是项目内嵌，优先级高于 site-packages）

    # FIX-T12 (2026-09-17)：Issue F stats_completed_task_aggregate 字面量兼容 PG
    # 已上移到 vendor/jeeflow/repository/base.py:stats_completed_task_aggregate
    # perform_type 字面量改 '1'（PG VARCHAR 列要求字符串字面量，SQLite 兼容两种）
    # 此处不再需要 monkey patch（vendor 是项目内嵌，优先级高于 site-packages）


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
    org_prov = SpiOrgUserProvider()
    engine = RatioCapableEngine(repo, user_prov, idgen, SimpleExprEvaluator())
    _registry = HandlerRegistry()
    register_builtin_assignments(_registry, user_prov, org_prov)

    # 与 main.py 同步（BDD Task 24 2026-09-17）：注册 mock 拦截器，验证 _fire_post 调用链
    class MockAuditInterceptor(FlowInterceptor):
        """定义级拦截器：每次 pre/post_handle 写一条到 /tmp/jee-mock-audit.log"""
        _audit_log = "/tmp/jee-mock-audit.log"
        def __init__(self, name: str = "com.example.MockAuditInterceptor"):
            self._name = name
            try:
                with open(self._audit_log, "a") as f:
                    f.write(f"# init {self._name} pid={os.getpid()}\n")
            except Exception:
                pass
        @property
        def order(self) -> int:
            return 0
        async def pre_handle(self, node, instance) -> bool:
            with open(self._audit_log, "a") as f:
                f.write(f"PRE  {self._name} node={node.id} inst={instance.id}\n")
            return True
        async def post_handle(self, node, instance) -> None:
            with open(self._audit_log, "a") as f:
                f.write(f"POST {self._name} node={node.id} inst={instance.id} state={instance.state}\n")

    _ic_registry = {
        "com.example.MockAuditInterceptor": MockAuditInterceptor(),
        # FIX-ALL (2026-09-17)：注册 bdd 测试用 POST_ONE 拦截器
        "POST_ONE": MockAuditInterceptor(name="POST_ONE"),
    }
    engine.set_extensions(EngineExtensions(registry=_registry, interceptor_registry=_ic_registry))
    facade = JeeflowFacade(engine, repo, ext_repo, user_search=spi_user_search, org_prov=org_prov)

    state["pool"] = pool
    state["adapter"] = adapter
    state["repo"] = repo
    state["ext_repo"] = ext_repo
    state["facade"] = facade

    # Issue C：先 wrap repo 写方法（save_task / save_instance 类型兜底），
    # 再 wrap facade.flow（入参规整）；顺序无所谓，互不依赖。
    _wrap_repo_methods(repo, ext_repo)
    _wrap_facade_flow(facade, repo)

    # v1.5.2-PG fix (FIX-T2 2026-09-17)：与 main.py 同步
    # handler 解析失败时记 warning 日志（stderr + /tmp/jee-fix.log）
    # 原 engine._resolve_actors handler 解析不到返回 [] 静默失败，TDD 难以区分
    # 错误 2 (FQCN 拼错 §25) 与 错误 3 (节点 id 不在 SPI) 都导致 activeTaskList=[]
    _FIX_LOG = "/tmp/jee-fix.log"
    def _fix_log(msg: str):
        line = f"{msg}"
        print(line, file=sys.stderr, flush=True)
        try:
            with open(_FIX_LOG, "a") as f:
                f.write(line + "\n")
        except Exception:
            pass
    _orig_resolve_actors = engine._resolve_actors
    async def _logged_resolve_actors(node, inst, operator, vars_):
        handler_name = node.properties.get("assignmentHandler", "")
        if handler_name and engine.ext and engine.ext.registry:
            h = engine.ext.registry.resolve_assignment(handler_name)
            if not h:
                _fix_log(f"[FIX-T2 WARN] handler not registered: FQCN='{handler_name}' node_id='{node.id}' (process={inst.defineId})")
                # FIX-T17 (2026-09-17)：handler 未注册不再静默 return []
                # 改为 raise 让上游 facade 报清晰错误（实例转 ABANDON）
                raise ValueError(f"节点[{node.id}] handler FQCN='{handler_name}' 未注册")
        actors = await _orig_resolve_actors(node, inst, operator, vars_)
        if handler_name and not actors:
            _fix_log(f"[FIX-T2 WARN] handler '{handler_name}' returned empty actors for node_id='{node.id}' (process={inst.defineId}); check SPI role_code")
            # FIX-T17：handler 已注册但 SPI 无匹配 → raise 让 facade 报错
            raise ValueError(f"节点[{node.id}] handler '{handler_name}' SPI 角色匹配为空（检查 role_code）")
        return actors
    engine._resolve_actors = _logged_resolve_actors

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

# FIX-T6 (2026-09-17): submitType=5 RE_APPLY 路由已上移到 vendor/jeeflow/facade.py
# vendor/jeeflow/facade.py:312 新增 elif submit_type == 5 分支 → execute_and_jump_to_first_task_node
# 此处不再需要 monkey patch（vendor 是项目内嵌，优先级高于 site-packages）

# FIX-T7 (2026-09-17): processDesignHis/page 路由已上移到 vendor/jeeflow/facade.py
# vendor/jeeflow/facade.py 新增 _processDesignHis_page 方法（兼容 memory + jdbc 后端）
# 此处不再需要 monkey patch（vendor 是项目内嵌，优先级高于 site-packages）

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
    for uid, info in SPI_USERS.items():
        real_name = info["name"]
        post_name = info["post"]
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
    for role_id, role_name in SPI_ROLES.items():
        if keyword and keyword not in role_id.lower() and keyword not in role_name.lower():
            continue
        rows.append({"roleId": role_id, "roleName": role_name})
    return _ok(rows)


@app.post("/api/dicts")
async def api_dicts(request: Request):
    """演示字典全集（与四后端同一套 wf_* 字典）：返回 [{code, items:[{value,label}]}]，前端按 code 索引缓存"""
    rows = [{"code": code, "items": list(items)} for code, items in SPI_DICTS.items()]
    return _ok(rows)


if __name__ == "__main__":
    import uvicorn
    # main_pg.py 用 8102 端口（与 main.py 内存后端 8101 区分），避免冲突
    # 端口可覆盖（PORT 环境变量）：本机 8100 被残留进程占用时可 PORT=8103 起
    uvicorn.run("main_pg:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8102")), reload=True)