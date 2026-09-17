# 重构 main.py + main_pg.py 公共代码 → main_common.py

## 目标
- 消除 main.py (432行) 和 main_pg.py (672行) 之间的重复代码
- 统一双端行为（之前部分注释 / log 不一致）
- 维护性提升（修改 1 处而非 2 处）

## 重构方案

### 新增 main_common.py (454 行)

| 模块 | 内容 |
|------|------|
| `setup_vendor_path()` | vendor/jeeflow sys.path 优先级 |
| `SnowflakeIDGen` | 雪花 ID 生成器（双端一致） |
| `SimpleExprEvaluator` | SpEL 表达式求值（FIX-T1/T3） |
| `RatioCapableEngine` | 比例会签扩展引擎（execute_process_task override） |
| `MockAuditInterceptor` + `build_ic_registry()` | 测试拦截器 + POST_ONE 注册 |
| `apply_extensions()` | HandlerRegistry + 拦截器注册 |
| `install_resolve_actors_wrapper()` | FIX-T2/T17 warning+raise 包装 |
| `_ok/_err/_page/_fmt_time` | boot2 协议响应 |
| `_inst_vo/_task_vo/_load_graph_*` | VO 构造 + 加载流程图 |
| `APPLY/AGREE/REJECT/...` | submitType 枚举 |
| `build_seed_defines()` | 流程定义种子构造（同步复用） |
| `run_seed_business()` | 兼容 uvicorn reload 触发 seed_business |
| `register_routes()` | **核心**：注册 7 个 HTTP 端点（带 callback） |

### main.py 重写后 (116 行)

```python
# 双端差异点：memory 同步 reset + load_seed_sync
repo = MemoryRepository()
ext_repo = MemoryExtRepository()
engine = RatioCapableEngine(...)
facade = JeeflowFacade(engine, repo, ext_repo, ...)
load_seed_sync()
run_seed_business(facade)

app = FastAPI(...)
register_routes(app,
    get_facade=lambda: facade,
    get_repo=lambda: repo,
    get_pool=lambda: None,
    reset_fn=_reset_memory)  # memory 特定：清字典 + 重 seed
```

### main_pg.py 重写后 (163 行)

```python
# 双端差异点：async lifespan + TRUNCATE 重置
@asynccontextmanager
async def lifespan(app):
    pool = await asyncpg.create_pool(dsn=PG_DSN, ...)
    repo = JdbcRepository(adapter)
    ext_repo = JdbcProcessExtRepository(adapter)
    ...
    yield
    await pool.close()

app = FastAPI(..., lifespan=lifespan)
register_routes(app,
    get_facade=lambda: app.state.facade,
    get_repo=lambda: app.state.repo,
    get_pool=lambda: app.state.pool,
    reset_fn=_reset_pg)  # PG 特定：TRUNCATE + 重 seed
```

## 重构效果

| 文件 | 重构前 | 重构后 | 减少 |
|------|--------|--------|------|
| main.py    | 432 行 | 116 行 | ↓ 316 (73.1%) |
| main_pg.py | 672 行 | 163 行 | ↓ 509 (75.7%) |
| main_common.py (新) | — | 454 行 | — |
| **合计** | 1104 行 | 733 行 | ↓ 371 (33.6%) |

## register_routes 设计要点

7 个端点完全公用，通过 4 个 callback 参数注入双端差异：

```python
register_routes(
    app,
    get_facade=lambda: ...,          # 双端不同的 facade 来源
    get_repo=lambda: ...,            # 双端不同的 repo 来源
    get_pool=lambda: ...,            # 仅 main_pg 需要
    reset_fn=async_func,             # 双端 reset 行为差异
)
```

- `/wf/{action}` → get_facade().flow()
- `/api/reset` → reset_fn()（返回 dict 合并进 _ok.data）
- `/healthz` → 检查 pool 状态（main 返回 "down"）
- `/api/stats` → get_repo().page_todo_tasks() + query_instances_for_stats()
- `/api/users`/`/api/roles`/`/api/dicts` → SPI_* 全局数据

## 回归验证

- **8101 memory**: flows/ 17/17 + bdd/ 67/67 = **84/84 PASS**
- **8102 PG**: flows/ 17/17 + bdd/ 67/67 = **84/84 PASS**
- **合计 168/168 = 100%**（不含 statics.json 统计文件）
- 双端路由契约完全一致

## 后续改进空间

- `_reset_memory` 和 `_reset_pg` 还可以进一步抽象（基类 + override）
- `run_seed_business` 可考虑合并到 `build_seed_defines` 一处
- 增加单元测试覆盖 main_common.py 公共 API
