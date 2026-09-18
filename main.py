"""jeeflow FastAPI demo (memory backend) —— boot2 接口规范对齐

注意（2026-09-17 §36）：
- 本入口使用内存后端（MemoryRepository）
- 与 main_pg.py（PG 后端）行为有差异：拦截器未注册时 main.py 静默通过，main_pg.py 抛错
- 详见 docs/known-issues.md §36 / docs/flow.md §2

2026-09-09 重构：公共代码上移到 main_common.py
"""
import asyncio
import json
import os
import sys

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

# 优先 vendor（项目内嵌）
from main_common import (
    setup_vendor_path, SnowflakeIDGen, SimpleExprEvaluator, RatioCapableEngine,
    build_ic_registry, build_custom_handlers, apply_extensions, install_resolve_actors_wrapper,
    _ok, register_routes, build_seed_defines, run_seed_business,
)

setup_vendor_path()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jeeflow import MemoryRepository, JeeflowFacade, register_builtin_assignments, HandlerRegistry
from jeeflow.memory import MemoryExtRepository

import flows_resolver
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # 让 spi.py / seed_business.py 可 import

FLOWS_DIR = flows_resolver.dir()

# ─── 启动行为开关 ─────────────────────────────────────────────────────────────
# FLOWS: 是否在启动时加载 flows/*.json 到流程定义表
# SEEDS: 启动时是否跑业务种子（16 进行中 + 9 已完成 + 8 委托）
# 都从同名环境变量读，任意一个为 false 则跳过对应动作。
FLOWS = os.environ.get("FLOWS", "true").lower() in ("1", "true", "yes", "on")
SEEDS = os.environ.get("SEEDS", "false").lower() in ("1", "true", "yes", "on")


# ─── Memory backend setup ──────────────────────────────────────────────────────
repo = MemoryRepository()
ext_repo = MemoryExtRepository()
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


# ─── Seed: load_flows (sync) ──────────────────────────────────────────────────
def load_seed_sync():
    """同步版 load_seed：遍历 flows/*.json 写入 repo（memory 同步 API）。"""
    for fname, define in build_seed_defines(FLOWS_DIR):
        repo.add_define(define)


if FLOWS:
    load_seed_sync()


# ─── run_seed_business (兼容 reload) ──────────────────────────────────────────
# T003：业务数据种子（引擎真实启动 16 进行中 + 9 已完成 + 8 委托），/api/reset 复跑。
if SEEDS:
    run_seed_business(facade)


# ─── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(root_path=("/jeeflow"), title="jeeflow api (memory)", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ─── /api/reset 行为（memory 特定） ────────────────────────────────────────────
async def _reset_memory():
    repo._defines.clear()
    repo._instances.clear()
    repo._tasks.clear()
    repo._actors.clear()
    repo._cc.clear()
    repo._seq = 1
    ext_repo._designs.clear()
    ext_repo._designHis.clear()
    ext_repo._surrogates.clear()
    ext_repo._seq = 1
    if FLOWS:
        load_seed_sync()
    if SEEDS:
        await _seed_business_async(facade)


async def _seed_business_async(facade):
    from seed_business import seed_business
    await seed_business(facade)


# ─── 注册路由 ──────────────────────────────────────────────────────────────────
register_routes(
    app,
    get_facade=lambda: facade,
    get_repo=lambda: repo,
    get_pool=lambda: None,
    reset_fn=_reset_memory,
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0",
                port=int(os.environ.get("PORT", "8101")),
                reload=False, log_level="info")
