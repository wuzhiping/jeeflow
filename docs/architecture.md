# jeeFlow 架构文档 (BDD #1208 FIX-T86 §4.3.2)

> **生成时间**: 2026-09-20
> **版本**: v1.9.0+ (Phase 1+2+3 完成)
> **依据**: `roadmap.md §4.3.2` - 引擎分层图 + 扩展点手册

---

## 1. 总体架构

```
┌──────────────────────────────────────────────────────────────────┐
│  HTTP 入口层 (FastAPI)                                            │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ /wf/{action} │ │ /healthz      │ │ /metrics │ │ /api/admin/* │  │
│  └──────┬──────┘ └──────────────┘ └──────────┘ └──────────────┘  │
└─────────┼──────────────────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────────────┐
│  门面层 (vendor/jeeflow/facade.py, 1815 行)                       │
│  - flow(action, args) 路由分发                                      │
│  - 48 个 _processXxx 方法                                          │
│  - 输入参数解析 (_parse_*) + 输出字段序列化 (_stringify_ids)         │
└─────────┬──────────────────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────────────┐
│  引擎核心 (vendor/jeeflow/engine.py, 754 行)                       │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ EngineImpl.start_process_instance_by_id (主流程启动)             │ │
│  │ EngineImpl.execute_process_task (任务推进)                     │ │
│  │ EngineImpl._execute_node (节点类型分发)                        │ │
│  │   ├─ TYPE_TASK → _create_task                                  │ │
│  │   ├─ TYPE_CUSTOM → _execute_custom_node                       │ │
│  │   ├─ TYPE_CALL_ACTIVITY → _execute_call_activity              │ │
│  │   ├─ TYPE_DECISION → _evaluate_decision (含 decisionHandler)   │ │
│  │   ├─ TYPE_FORK/JOIN/CUSTOM/END                                 │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────┬──────────────────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────────────┐
│  扩展层 (vendor/jeeflow/extensions.py)                              │
│  - EngineExtensions 注入点:                                         │
│    ├─ interceptors + interceptor_registry (流程拦截器)              │
│    ├─ assignment_handler (参与者解析)                               │
│    ├─ decision_handler (决策路由)                                    │
│    ├─ event_listener (事件订阅)                                     │
│    ├─ custom_handler_registry (custom 节点)                         │
│    └─ registry (HandlerRegistry: assignment/decision 调度)            │
└─────────┬──────────────────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────────────┐
│  仓储层 (双端并存)                                                    │
│  ┌────────────────────────┐  ┌────────────────────────────────┐     │
│  │ MEM (main.py)            │  │ PG (main_pg.py)                  │     │
│  │ MemoryRepository         │  │ JdbcRepository (PostgresAdapter) │     │
│  │ 进程内 dict, 重启丢失    │  │ asyncpg pool, 持久化              │     │
│  └────────────────────────┘  └────────────────────────────────┘     │
│       +                                                                   │
│  ExtRepo: MemoryExtRepository / JdbcProcessExtRepository                │
│  (设计 / 业务配置 / 委派 / 元数据)                                       │
└──────────────────────────────────────────────────────────────────┘
```

## 2. 引擎核心 (engine.py)

### 2.1 入口方法

| 方法 | 行号 | 职责 |
|------|------|------|
| `start_process_instance_by_id` | 72 | 创建实例 + 启动节点 + 触发第一组 task |
| `execute_process_task` | 138 | 处理 task.execute 请求, 完成 task + 推进 |
| `evaluate_decision` | 540 | 决策路由 (expr / decisionHandler / fallback) |
| `fire_event` | 904 | 事件发布 (PROCESS_START/FINISH/TASK_CREATE/TASK_COMPLETE/CC_CREATE) |

### 2.2 节点类型分发

```
_execute_node(flow, inst, node, operator, vars_)
  │
  ├─ TYPE_TASK      → _create_task → inst.tasks += new_task
  │                   └─ record done (FIX-T55 taskType=2)
  │
  ├─ TYPE_CUSTOM    → _execute_custom_node → EngineExtensions.custom_handler_registry
  │                                                ↓
  │                                          handler(node, inst, vars_, args) → vars_[val]
  │
  ├─ TYPE_CALL_ACTIVITY → _execute_call_activity → start_process_instance_by_id(sub_def)
  │                                                       ↓
  │                                                 vars_[node.id+"_childInstanceId"]
  │                                                       ↓
  │                                                 推进主流程 (不阻塞)
  │
  ├─ TYPE_DECISION  → _evaluate_decision (decisionHandler → expr → fallback)
  │
  ├─ TYPE_FORK      → 推进所有出边 (并行)
  ├─ TYPE_JOIN      → find_doing_tasks==[] 才推进 (汇合)
  ├─ TYPE_END       → inst.finish() / inst.reject()
  │                   └─ parent.parentStatus = "CHILD_DONE/REJECT" (FIX-T72)
  │
  └─ TYPE_CUSTOM    → (类型重复保护) raise
```

### 2.3 关键修复

| 编号 | 行号 | 描述 |
|------|------|------|
| FIX-T33 | 88 | parentId 参数 (§56) |
| FIX-T46 | 512 | decisionHandler 调用链 (§46) |
| FIX-T55 | _create_task | taskType=2 RECORD 自动完成 |
| FIX-T56 | 295 | PENDING 实例禁止 execute |
| FIX-T58 | verify.py | cycle 检测加强 |
| FIX-T62 | 676 | surrogate 真实生效 |
| FIX-T69 | 819 | _is_delegate_allowed 委派 |
| FIX-T72 | 478 | parentStatus 联动 (§3.1.1) |
| FIX-T73 | 460 | callActivity 节点 (§3.1.2) |
| FIX-T78 | 78 | _def_cache LRU 100 (§3.3.2) |

## 3. 仓储层 (双端)

### 3.1 Memory (main.py)

```python
class MemoryRepository:
    _defines: dict[int, ProcessDefine]
    _designs: dict[int, ProcessDesign]
    _instances: dict[int, ProcessInstance]
    _tasks: dict[int, ProcessTask]
    _cc: dict[int, CcInstanceRow]
    _surrogates: dict[int, ProcessSurrogate]
```

特点:
- 进程内 dict, 全部 in-memory
- 重启数据丢失 (适合 dev/test)
- 单进程, 无并发控制

### 3.2 Jdbc (main_pg.py + asyncpg)

```sql
CREATE TABLE wf_process_define (
    id BIGINT PRIMARY KEY,
    name VARCHAR(128),
    display_name VARCHAR(255),
    type VARCHAR(64),
    state INT,
    content TEXT,  -- JSON 字符串
    version INT,
    create_time TIMESTAMP,
    update_time TIMESTAMP
);
-- 8 张表 (define/design/design_his/instance/task/task_actor/cc_instance/surrogate)
```

特点:
- asyncpg 连接池 (min=1 max=10)
- TRUNCATE 重置 (RESTART IDENTITY)
- 雪花 ID (19 位)
- 支持多节点部署 (lb 轮询)

### 3.3 Repository 接口

```python
class ProcessRepository:
    async def find_define_by_id(self, id) -> ProcessDefine
    async def find_define_by_name(self, name) -> ProcessDefine
    async def save_define(self, def_)
    async def save_instance(self, inst)
    async def update_instance(self, inst)
    async def find_instance_by_id(self, id) -> ProcessInstance
    async def find_task_by_id(self, id) -> ProcessTask
    async def add_task_actor(self, task_id, actor_ids)
    async def remove_task_actor(self, task_id, actor_ids)
    async def save_task(self, task)
    async def update_task(self, task)
    async def page_todo_tasks(...) -> tuple[list, int]
    async def page_done_tasks(...) -> tuple[list, int]
    async def page_instances(...) -> tuple[list, int]
    async def page_cc_instances(...) -> tuple[list, int]
    async def page_surrogates(...) -> tuple[list, int]
    async def lock_instance_for_update(self, inst_id)
    async def query_instances_for_stats(...)
    async def stats_pending_and_overdue_count(...)
    async def stats_avg_completed_duration_seconds(...)
    async def stats_active_users_count(...)
    async def stats_completed_task_aggregate(...)
```

## 4. 扩展点手册 (EngineExtensions)

### 4.1 已实现的扩展点

| 扩展点 | 类型 | 注册方式 | 触发时机 |
|--------|------|----------|----------|
| `interceptors` | list[FlowInterceptor] | 引擎构造时 | 每个节点 pre/post |
| `interceptor_registry` | dict[str, FlowInterceptor] | apply_extensions | 流程级 postInterceptors 按名解析 |
| `assignment_handler` | Callable | apply_extensions | 节点无 assignee 时 |
| `decision_handler` | Callable | apply_extensions | 决策节点 (decisionHandler) |
| `event_listener` | Callable | apply_extensions | 流程/任务事件 |
| `custom_handler_registry` | dict[str, Callable] | apply_extensions | custom 节点 (FIX-T38) |
| `registry` | HandlerRegistry | apply_extensions | 简化版 handler 注册 (§67 §68) |

### 4.2 业务方扩展示例

```python
# main_common.py:build_decision_handlers (FIX-T46)
def _BuiltinDecisionAmountHandler:
    async def decide(self, node, inst, vars):
        amount = float(vars.get("amount", 0) or 0)
        return "task1" if amount >= 10000 else "end"

# main_common.py:build_custom_handlers (FIX-T38)
def _builtin_custom_test_handler(node, inst, vars_, args):
    return json.loads(args)  # 解析 args 字符串, 写回 vars_[val]
```

注册:
```python
_registry = HandlerRegistry()
register_builtin_assignments(_registry, user_prov, org_prov)
apply_extensions(engine, _registry, build_ic_registry(),
                 build_custom_handlers(), build_decision_handlers())
```

### 4.3 SPI 注入 (users / roles / depts)

`spi/` 目录:
- `SimpleUserProvider` - 用户查找
- `SpiOrgUserProvider` - 部门/角色查找
- `DEMO_ROLE_TO_USERS.json` - 角色→用户映射
- `SPI(func=..., payload=...)` - 调用方

### 4.4 SPI dispatcher 架构 (v26, 三层分离)

> **演进**: v8-v21 数据层重构 (22 DictProxy + 9 SPI 函数 + 2 helpers + verify()) · v22-v24 CLI 入口 · v25 FastAPI 路由 · **v26 dispatcher 统一** · v28 main_common 双端 · v29 互逆不变.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 1: Dispatcher (spi/cli.py + spi/api.py + spi/__main__.py)    │
│  · 入口层, 跟随 SPI_FOLDER 环境变量                                    │
│  · 解析命令行参数 (cli) 或 HTTP 路由 (api)                              │
│  · 加载 spi/<SPI_FOLDER>/cli.py 或 spi/<SPI_FOLDER>/api.py            │
│  · 调用下层 _data_* 函数, 不含业务逻辑                                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 2: Implementation (spi/{demo,dev,fdep}/cli.py + api.py)      │
│  · 实现层, 每个 SPI_FOLDER 一个子包                                    │
│  · 暴露 6 个 _data_* 函数 (CLI/API 共享):                               │
│    _data_verify() / _data_status() / _data_list_users()               │
│    _data_show_user(uid) / _data_list_depts() / _data_show_dept(dept_id)│
│  · demo 实现简单 dev 实现丰富 (22 DictProxy + 2 helpers + 9 SPI 函数)   │
│  · cli.py + api.py 是薄包装, 几乎全部 re-export                         │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 3: Data (spi/{demo,dev}/data.py + *.json)                      │
│  · 数据层, DictProxy + helpers + verify()                              │
│  · spi/dev/data.py: 22 DictProxy (v8-v29) + 2 helpers + verify()       │
│  · spi/demo/data.py: 基础 + verify() (99 errors 是已知问题)             │
│  · spi/fdep/: 数据层, 无 cli/api → 走 dispatcher 返回 404               │
└─────────────────────────────────────────────────────────────────────┘
```

**调用流程**:

```
HTTP: client → main_common.register_spi_routes(app) → spi/api.py → SPI_FOLDER 加载 → spi/<folder>/api.py → _data_* → spi/<folder>/data.py
CLI:  user   → python -m spi.cli → spi/cli.py → SPI_FOLDER 加载 → spi/<folder>/cli.py → _data_* → spi/<folder>/data.py
```

**SPI_FOLDER 路由**:
- `os.environ["SPI_FOLDER"] = "dev" | "demo" | "fdep" | ...`
- **默认 SPI_FOLDER = dev** (本地开发/测试推荐, 22 DictProxy + helpers + verify() 完整)
- **代码层默认 `"demo"`** (spi/__init__.py:14, FREEZE.md 冻结, 本地请显式设置)
- 缺失 cli/api 时 dispatcher 返回 404 (`{"detail": "SPI_FOLDER=xxx 不支持 API/CLI"}`)

## 5. HTTP 路由分层

| 路由前缀 | 数量 | 用途 |
|----------|------|------|
| `/wf/{action:path}` | 48 | 业务门面 (BDD #1207) |
| `/healthz` | 1 | 简版健康检查 |
| `/api/admin/health` | 1 | 详细健康检查 (FIX-T79) |
| `/api/admin/stats/{overview,trend,group}` | 3 | 看板统计 (FIX-T80/T81/T82) |
| `/metrics` | 1 | Prometheus 指标 (FIX-T83) |
| `/api/admin/trace` | 1 | 链路追踪 (FIX-T84) |
| `/api/reset` | 1 | 一键重置 |
| `/api/stats` | 1 | 用户统计 |
| `/api/users` | 1 | 用户列表 |
| `/api/roles` | 1 | 角色列表 |
| `/api/dicts` | 2 | 字典查询 |
| `/openapi.json` | 1 | OpenAPI 3.0 spec (自动生成) |

## 6. 监控与可观测性 (§4.1)

### 6.1 Prometheus 指标 (3 个核心)

| 指标 | 类型 | Labels | 用途 |
|------|------|--------|------|
| `wf_instance_state_total` | Counter | state | 各状态实例总数 |
| `wf_active_instances` | Gauge | (无) | DOING+PENDING 实时活跃数 |
| `wf_task_duration_seconds` | Histogram | taskName | 任务执行耗时分布 |
| `wf_task_completed_total` | Counter | taskName | 已完成任务数 |

### 6.2 Trace 链路

`trace_span(name, **attrs)` 上下文管理器:
- 自动记录 span_id / trace_id / parent_span_id
- 记录 start_time / end_time / duration_ms
- 暴露 `/api/admin/trace?limit=200` 查看
- 暴露 `/api/admin/trace/spans/{trace_id}` 按 ID 查询完整调用链

## 7. 数据一致性保证

### 7.1 悲观锁 (§27 FIX-T35)

```python
await self.repo.lock_instance_for_update(inst.id)
existing = await self.repo.find_doing_tasks(inst.id, [node.id])
```

### 7.2 乐观锁 (§4.4.2 FIX-T87)

```sql
UPDATE wf_process_instance SET state=?, ..., version=version+1
WHERE id=? AND version=?
```

冲突重试策略: 3 次重试, 指数退避.

### 7.3 Surrogate Fallback (§40 FIX-T62)

`_load_and_check`:
1. operator in task.actorIds → 放行
2. operator in surrogate 表 (operator=X, surrogate=operator) → 放行
3. operator in _delegate_of → 放行
4. 否则 99999999

## 8. 部署架构

### 8.1 MEM 单进程 (dev/test)

```
main.py → MemoryRepository → 进程内 dict
端口: 8101
启动: nohup python main.py &
```

### 8.2 PG 单节点 (生产推荐)

```
main_pg.py + asyncpg pool → JdbcRepository → PG 8 张表
端口: 8102
启动: JEEFLOW_PG_DSN=... nohup python main_pg.py &
```

### 8.3 PG 多节点 (HA)

```
main_pg.py #1 ┐
main_pg.py #2 ├→ 同一 PG 后端 → lb (nginx) → client
main_pg.py #3 ┘
```

约束:
- 同一 PG 同一时间只有 1 个 main_pg 写 (其他读)
- 用乐观锁防止并发冲突 (§4.4.2)
- recommend 监控: Prometheus `/metrics` + `/api/admin/health`

## 9. 扩展业务方

详见 `./docs/integration.md`:
- 部署流程 (§3)
- 调用 action (§4)
- 集成 SPI (§5)
- 自定义 handler (§6)
- 监控告警 (§7)
- 多节点 HA (§8)

## 10. 变更日志

| 日期 | 阶段 | 主要变更 |
|------|------|----------|
| 2026-09-17 | v1.5.x | 基础引擎 + facade |
| 2026-09-18 | v1.6.x | verify 系统 + decision expr 增强 |
| 2026-09-19 | v1.7.x | 16 个 TDD flow 全 PASS |
| 2026-09-19 | v1.8.x | handler registry + SPI 重构 |
| 2026-09-19 | v1.9.0 | 27 个 FIX, custom 节点 (FIX-T38), decision 复合条件 (FIX-T37) |
| 2026-09-20 | v1.9.0+ Phase 1 | 11 已知限制 → 0, 71 FIX, 1100 BDD + 19 TDD |
| 2026-09-20 | v1.9.0+ Phase 2 | parentStatus + callActivity + delegateHistory + transferAndAdd + withForm + AsyncJdbcTableReader + define cache |
| 2026-09-20 | v1.9.0+ Phase 3 | /api/admin/* + Prometheus + Trace + OpenAPI |
