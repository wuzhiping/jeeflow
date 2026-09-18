"""jeeflow FastAPI demo (PostgreSQL backend) —— boot2 接口规范对齐

PG 模式与内存版（main.py）路由契约完全一致；差异：
- pool / repo / ext_repo / facade / 流程定义种子 / 业务数据种子 全部在 FastAPI lifespan 异步上下文创建；
- 重置路径走 TRUNCATE … RESTART IDENTITY CASCADE，不依赖内部字典；
- 所有仓储读取改为 JdbcRepository 的 async API（find_define_by_id / query_*_for_stats / find_task_actors）。

注意（2026-09-17 §36）：
- 本入口使用 PG 后端（JdbcRepository），拦截器未注册严格抛错
- 与 main.py（内存后端）行为差异：main.py 拦截器未注册静默通过
- 详见 docs/known-issues.md §36 / docs/flow.md §2

2026-09-09 重构：公共代码上移到 main_common.py
"""
import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager

mimetypes_added = False
try:
    import mimetypes
    mimetypes.add_type("application/javascript", ".cjs")
except Exception:
    pass

# 优先 vendor（项目内嵌）— 必须在 main_common import 之前调，否则 main_common 内部
# 的 `from jeeflow import ...` 会先命中 .venv site-packages 而非 vendor
def _setup_vendor_path():
    _VENDOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
    if _VENDOR not in sys.path:
        sys.path.insert(0, _VENDOR)
    return _VENDOR
_setup_vendor_path()

# 优先 vendor
from main_common import (
    setup_vendor_path, SnowflakeIDGen, SimpleExprEvaluator, RatioCapableEngine,
    build_ic_registry, build_custom_handlers, apply_extensions, install_resolve_actors_wrapper,
    register_routes,
)

setup_vendor_path()

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jeeflow import JeeflowFacade, HandlerRegistry, register_builtin_assignments, JdbcRepository
from jeeflow.repository.postgres import PostgresAdapter
from jeeflow.repository.ext import JdbcProcessExtRepository

import flows_resolver
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FLOWS_DIR = flows_resolver.dir()

PG_DSN = os.environ.get(
    "JEEFLOW_PG_DSN",
    "postgresql://uid:pwd@127.0.0.1:5432/jeeflow",
)

# ─── 启动行为开关（与 main.py 对齐）────────────────────────────────────────────
# FLOWS: 是否在 lifespan 启动时加载 flows/*.json
# SEEDS: 是否在 lifespan 启动时跑业务种子
# 都从同名环境变量读；任意一个为 false 则跳过。
FLOWS = os.environ.get("FLOWS", "true").lower() in ("1", "true", "yes", "on")
SEEDS = os.environ.get("SEEDS", "false").lower() in ("1", "true", "yes", "on")

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


# ─── async helpers ─────────────────────────────────────────────────────────────
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


async def load_seed_pg(repo: JdbcRepository) -> int:
    """PG 异步版 load_seed：写入 wf_process_define 表。返回写入条数。"""
    from main_common import build_seed_defines
    written = 0
    for _, define in build_seed_defines(FLOWS_DIR):
        await repo.save_define(define)
        written += 1
    return written


async def seed_business_pg(facade):
    from seed_business import seed_business
    await seed_business(facade)


# ─── lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动：建连接池 + repo/ext_repo + facade + 流程定义种子；
    关闭：归还连接池。"""
    pool = await asyncpg.create_pool(dsn=PG_DSN, min_size=1, max_size=10)
    adapter = PostgresAdapter(pool)
    repo = JdbcRepository(adapter)
    ext_repo = JdbcProcessExtRepository(adapter)

    idgen = SnowflakeIDGen()
    from spi import SimpleUserProvider, SpiOrgUserProvider
    user_prov = SimpleUserProvider()
    org_prov = SpiOrgUserProvider()
    engine = RatioCapableEngine(repo, user_prov, idgen, SimpleExprEvaluator())
    _registry = HandlerRegistry()
    register_builtin_assignments(_registry, user_prov, org_prov)
    apply_extensions(engine, _registry, build_ic_registry(), build_custom_handlers())
    install_resolve_actors_wrapper(engine)

    facade = JeeflowFacade(engine, repo, ext_repo, user_search=None, org_prov=org_prov)

    # BDD #128 FIX：注册 PG-mode meta_reader（v1.9.0+ 业务数据回显）
    # PG asyncpg 与 JdbcTableReader (sqlite 风格) 接口不兼容，
    # 用 AsyncJdbcTableReader 包装（meta 库提供），目录 meta_defs/<table>.json
    from jeeflow.meta import MetaTableReader
    try:
        from jeeflow.meta import AsyncJdbcTableReader
        from jeeflow.meta import JsonMetaProvider
        meta_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meta_defs")
        if os.path.isdir(meta_dir):
            provider = JsonMetaProvider(meta_dir)
            reader = AsyncJdbcTableReader(pool)
            facade.set_meta_reader(MetaTableReader(reader, provider))
    except ImportError:
        # AsyncJdbcTableReader 尚未提供，PG bizData 暂不可用（raise 提示）
        pass

    # BDD #128 FIX：注册 PG-mode meta_reader（v1.9.0+ 业务数据回显）
    from jeeflow.meta import MetaTableReader, JsonMetaProvider
    from jeeflow.persist import JdbcTableReader
    meta_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meta_defs")
    if os.path.isdir(meta_dir):
        provider = JsonMetaProvider(meta_dir)
        reader = JdbcTableReader(adapter)
        facade.set_meta_reader(MetaTableReader(reader, provider))

    if FLOWS:
        await load_seed_pg(repo)
    if SEEDS:
        await seed_business_pg(facade)

    app.state.pool = pool
    app.state.adapter = adapter
    app.state.repo = repo
    app.state.ext_repo = ext_repo
    app.state.engine = engine
    app.state.facade = facade
    yield

    await pool.close()


# ─── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(root_path=("/jeeflow"), title="jeeflow api (PG)", version="0.1.0",
              lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


async def _reset_pg():
    """PG 端 reset：TRUNCATE + 按 FLOWS/SEEDS 重置种子。返回 {reloadedDefines: N}"""
    await _truncate_all(app.state.adapter)
    n = 0
    if FLOWS:
        n = await load_seed_pg(app.state.repo)
    if SEEDS:
        await seed_business_pg(app.state.facade)
    return {"reloadedDefines": n}


# ─── 注册路由 ──────────────────────────────────────────────────────────────────
register_routes(
    app,
    get_facade=lambda: app.state.facade,
    get_repo=lambda: app.state.repo,
    get_pool=lambda: getattr(app.state, "pool", None),
    reset_fn=_reset_pg,
)


if __name__ == "__main__":
    import uvicorn
    # main_pg.py 用 8102 端口（与 main.py 内存后端 8101 区分）
    uvicorn.run("main_pg:app", host="0.0.0.0",
                port=int(os.environ.get("PORT", "8102")),
                reload=False, log_level="info")
