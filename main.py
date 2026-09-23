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
    _ok, register_routes, build_seed_defines, run_seed_business, run_auto_deploy_fdep,
    install_metrics_endpoint, install_trace_endpoint, metrics_counter, metrics_histogram,
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

engine = RatioCapableEngine(repo, user_prov, idgen, SimpleExprEvaluator(), org_prov)
_registry = HandlerRegistry()
register_builtin_assignments(_registry, user_prov, org_prov)
# BDD #32 FIX-T46 (2026-09-20)：注册示例 decisionHandler
from main_common import build_decision_handlers
apply_extensions(engine, _registry, build_ic_registry(), build_custom_handlers(), build_decision_handlers())
engine.set_ext_repo(ext_repo)
install_resolve_actors_wrapper(engine)

facade = JeeflowFacade(engine, repo, ext_repo, user_search=None, org_prov=org_prov)

# BDD #128 FIX：注册 memory-mode meta_reader（PG 后端在 main_pg.py 用 MetaTableReader）
from main_meta import build_meta_reader
facade.set_meta_reader(build_meta_reader(repo))


# ─── Seed: load_flows (sync) ──────────────────────────────────────────────────
def load_seed_sync():
    """同步版 load_seed：遍历 flows/*.json 写入 repo（memory 同步 API）。"""
    for fname, define in build_seed_defines(FLOWS_DIR):
        repo.add_define(define)


if FLOWS:
    load_seed_sync()

# §7.3.3 FIX-T109 (2026-09-20) 断点续跑 - 启动时扫描 DOING 实例
# MEM 端: load_seed_sync 之后跑 (repo 已有内容)
try:
    doing_res = asyncio.run(facade.flow("processInstance/doingList", {"limit": 100}))
    if doing_res.get("code") == 0:
        data = doing_res["data"]
        print(f"[§7.3.3 startup] DOING 实例数: {data['instance_count']}, DOING 任务数: {data['task_count']}, 节点分布: {data['by_node']}")
except Exception as e:
    print(f"[§7.3.3 startup] DOING 扫描失败: {e}")


# ─── 临时任务：启动后自动部署 ToT/flows/fdep.json ──────────────────────────
# 条件：fdep.json 存在 + 引擎内尚未定义 → 部署
# 已在 main_common.auto_deploy_fdep / run_auto_deploy_fdep
run_auto_deploy_fdep(facade)


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

# v25: 注册 spi/dev API 路由 (CLI 能力远程 API 暴露)
# v26: 改为 dispatcher 层 spi.api (跟随 SPI_FOLDER 自动切换 demo/dev)
# v28: 移到 main_common.register_spi_routes (双端共用)
from main_common import register_spi_routes
register_spi_routes(app)

# BDD #1205 FIX-T83 §4.1.3：安装 Prometheus metrics 端点
app.state.facade = facade
app.state.repo = repo
install_metrics_endpoint(app)
install_trace_endpoint(app)


if __name__ == "__main__":
    import uvicorn
    # 默认端口 8101（memory 端，与 PG 端 8102 区分）；参见 ToT/sop/engine-deploy.md
    uvicorn.run("main:app", host="0.0.0.0",
                port=int(os.environ.get("PORT", "8101")),
                reload=False, log_level="info")
