"""main.py + main_pg.py 公共代码：handlers/helpers/route registration

2026-09-09 建立：把双端重复的 IDGen/ExprEval/MockInterceptor/_ok/_inst_vo/route 注册集中到本模块；
                 main.py 和 main_pg.py 只保留差异部分（repo 创建、lifespan、reset 行为、端口）。

公共 API：
- SnowflakeIDGen : 雪花 ID 生成器
- SimpleExprEvaluator : 表达式求值（FIX-T1/T3）
- RatioCapableEngine : 比例会签扩展引擎
- MockAuditInterceptor + build_ic_registry() : 测试用拦截器（注册 POST_ONE/POST_ONE_FALLBACK）
- install_resolve_actors_wrapper(engine, fix_log_path) : FIX-T2/T17 warning+raise 包装
- ResponseHelpers (_ok, _err, _page, _fmt_time) : boot2 协议响应
- ViewObjectBuilders (_inst_vo, _task_vo) : VO 构造
- LoadGraphMixin / repo_resolver 抽象：让双端 repo 都能 load_graph
- register_routes(app, ctx_provider) : 注册 7 个 HTTP 端点（/wf/{action}、/api/reset、/healthz、
                                              /api/stats、/api/users、/api/roles、/api/dicts）
- load_seed_definitions(repo, flows_dir, ProcessDefine) : 公共种子逻辑（同步 main 用 / 异步 main_pg 用）
- run_seed_business(facade) : 触发 seed_business（兼容 reload / 普通启动）
"""
import json
import os
import sys
from datetime import datetime
from typing import Any, Callable, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from jeeflow import EngineImpl, JeeflowFacade, EngineExtensions, HandlerRegistry
from jeeflow.extensions import FlowInterceptor
from jeeflow.engine import _find_node, _follow_edges, _sync_task_to_aggregate
from jeeflow.model import InstanceState, TaskState, ProcessDefine, ProcessInstance, ProcessTask
from jeeflow.spi import IDGenerator, ExpressionEvaluator


# ─── Setup: vendor path ─────────────────────────────────────────────────────────
# 优先使用本地 vendor/jeeflow（项目内嵌），避免依赖 .venv site-packages
def setup_vendor_path():
    _VENDOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
    if _VENDOR not in sys.path:
        sys.path.insert(0, _VENDOR)
    return _VENDOR


# ─── Snowflake ID ──────────────────────────────────────────────────────────────
class SnowflakeIDGen(IDGenerator):
    """简化雪花 ID（双端一致）：ts << 10 | seq(12 bits）"""
    def __init__(self):
        self._epoch = 1700000000000
        self._seq = 0

    def next_id(self) -> int:
        import time
        ts = int(time.time() * 1000) - self._epoch
        self._seq = (self._seq + 1) & 0xFFF
        return (ts << 10) | self._seq


# ─── Expression Evaluator ──────────────────────────────────────────────────────
class SimpleExprEvaluator(ExpressionEvaluator):
    """简易 SpEL 表达式：支持 amount >/>=/</<=/== number 和 #var==str；OGNL 风格 #varname 同支持

    v1.5.1 fix (FIX-T1 2026-09-17)：expr 是数字但 value 是字符串时，原
    `actual = float(actual)` 抛 ValueError 导致整个 startAndExecute 失败
    (code=99999999)。修复：捕获 ValueError/TypeError 返回 False，与
    regex 不匹配、value 为 None 行为一致（走兜底首边）。

    v1.6.0 fix (FIX-T3 2026-09-17 BDD Task 32)：支持字符串相等比较
    `#var==string` / `#var!=string`。原版只支持数字，字符串比较走兜底。
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
            key, op, expected = m_str.group(1).lstrip("#"), m_str.group(2), m_str.group(3)
            actual = vars.get(key)
            if actual is None:
                return False
            actual = str(actual)
            if op == "==": return actual == expected
            if op == "!=": return actual != expected
            return False
        return False


# ─── Ratio Engine ──────────────────────────────────────────────────────────────
class RatioCapableEngine(EngineImpl):
    """比例会签扩展引擎：支持通用 countersignCompletionCondition（OGNL 表达式）。

    引擎默认 PARALLEL 仅识别 ONE_VOTE_VETO（jeeflow/engine.py:101）；其他 OGNL 条件
    （如 "#nrOfCompletedInstances==2"）会被忽略。此子类在 execute_process_task 中：
    1. 先调 EngineImpl 原版完成当前 task（内部做 _prepare_execute_task + 推进）
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
            import sys
            print(f"[RatioCapableEngine] ratio check failed: {ex!r}", file=sys.stderr)
        return result


# ─── Mock Audit Interceptor ────────────────────────────────────────────────────
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


def build_ic_registry() -> dict:
    """双端公共的拦截器注册表：mock + bdd 测试用拦截器"""
    return {
        "com.example.MockAuditInterceptor": MockAuditInterceptor(),
        # FIX-ALL (2026-09-17)：注册 bdd 测试用 POST_ONE 拦截器
        "POST_ONE": MockAuditInterceptor(name="POST_ONE"),
    }


def apply_extensions(engine, registry: HandlerRegistry, ic_registry: Optional[dict] = None):
    """应用 HandlerRegistry + 拦截器注册表到 engine"""
    ext = EngineExtensions(registry=registry, interceptor_registry=ic_registry or {})
    engine.set_extensions(ext)


# ─── Resolve Actors Warning + Raise Wrapper ─────────────────────────────────────
_FIX_LOG_PATH = "/tmp/jee-fix.log"


def _fix_log(msg: str):
    try:
        with open(_FIX_LOG_PATH, "a") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def install_resolve_actors_wrapper(engine):
    """FIX-T2 (2026-09-17)：handler 解析失败时记 warning 日志
    FIX-T17 (2026-09-17)：handler 未注册 / SPI 空 → raise 让 facade 报错
    原 engine._resolve_actors handler 解析不到返回 [] 静默失败，TDD 难以区分
    错误 2 (FQCN 拼错 §25) 与 错误 3 (节点 id 不在 SPI) 都导致 activeTaskList=[]
    此 wrapper 在 handler 解析失败、SPI 返回空 role 时打 warning 到 stderr + /tmp/jee-fix.log
    """
    _orig_resolve_actors = engine._resolve_actors

    async def _logged_resolve_actors(node, inst, operator, vars_):
        handler_name = node.properties.get("assignmentHandler", "")
        if handler_name and engine.ext and engine.ext.registry:
            h = engine.ext.registry.resolve_assignment(handler_name)
            if not h:
                _fix_log(f"[FIX-T2 WARN] handler not registered: FQCN='{handler_name}' node_id='{node.id}' (process={inst.defineId})")
                # FIX-T17：handler 未注册不再静默 return []
                raise ValueError(f"节点[{node.id}] handler FQCN='{handler_name}' 未注册")
        actors = await _orig_resolve_actors(node, inst, operator, vars_)
        if handler_name and not actors:
            _fix_log(f"[FIX-T2 WARN] handler '{handler_name}' returned empty actors for node_id='{node.id}' (process={inst.defineId}); check SPI role_code")
            # FIX-T17：handler 已注册但 SPI 无匹配 → raise 让 facade 报错
            raise ValueError(f"节点[{node.id}] handler '{handler_name}' SPI 角色匹配为空（检查 role_code）")
        return actors

    engine._resolve_actors = _logged_resolve_actors


# ─── Boot2 Common Result ─────────────────────────────────────────────────────────
def _ok(data=None):
    return {"code": 0, "msg": "成功", "data": data}


def _err(msg: str, code=99999999):
    return JSONResponse({"code": code, "msg": msg}, status_code=200)


def _page(rows, page_num=1, page_size=999):
    return {"pageNum": page_num, "pageSize": page_size, "rows": rows, "recordCount": len(rows), "totalPage": 1}


def _fmt_time(t):
    return t.strftime("%Y-%m-%d %H:%M:%S") if t else None


# ─── VO builders ───────────────────────────────────────────────────────────────
def _inst_vo(inst: ProcessInstance, def_: ProcessDefine = None) -> dict:
    """ProcessInstanceVO：Entity 字段 + displayName + jsonObject + activeTaskList"""
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
    """ProcessTaskVO：Entity 字段 + 展示字段"""
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


# ─── Load Graph（抽象 repo 来源）─────────────────────────────────────────────────
async def _load_graph_async(repo, define_id) -> Optional[dict]:
    """PG 端：通过 repo.find_define_by_id（async）"""
    d = await repo.find_define_by_id(define_id)
    return json.loads(d.content) if d and d.content else None


def _load_graph_sync(repo, define_id) -> Optional[dict]:
    """Memory 端：通过 repo._defines.get（sync）"""
    d = repo._defines.get(define_id)
    return json.loads(d.content) if d and d.content else None


# ─── Boot2 submitType 枚举 ─────────────────────────────────────────────────────
APPLY, AGREE, REJECT, ROLLBACK, JUMP, RE_APPLY = 0, 1, 2, 3, 4, 5
ROLLBACK_TO_OPERATOR, COUNTERSIGN_DISAGREE = 6, 20


# ─── Seed Definitions 公共逻辑 ──────────────────────────────────────────────────
def build_seed_defines(flows_dir: str):
    """从 flows_dir 读取所有 .json，返回 [ProcessDefine, ...]"""
    out = []
    for fname in sorted(os.listdir(flows_dir)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(flows_dir, fname), "r", encoding="utf-8") as f:
            raw = json.loads(f.read())
        out.append((fname, ProcessDefine(
            name=raw.get("name", fname),
            displayName=raw.get("displayName", fname),
            type=raw.get("type", ""),
            state=1,
            content=json.dumps(raw, ensure_ascii=False),
        )))
    return out


# ─── run_seed_business（兼容 reload） ──────────────────────────────────────────
def run_seed_business(facade):
    """兼容 uvicorn reload：worker 在运行中的事件循环里 import 本模块"""
    import asyncio
    try:
        asyncio.get_running_loop()
        asyncio.get_event_loop().create_task(_seed_business_async(facade))
    except RuntimeError:
        asyncio.run(_seed_business_async(facade))


async def _seed_business_async(facade):
    from seed_business import seed_business
    await seed_business(facade)


# ─── Routes Registration ───────────────────────────────────────────────────────
def register_routes(app: FastAPI, *, get_facade: Callable, get_repo: Callable,
                    get_pool=None, reset_fn: Optional[Callable] = None,
                    install_static: bool = True):
    """注册 7 个 HTTP 端点（双端共用）

    参数:
        app: FastAPI 实例
        get_facade: () -> JeeflowFacade（main 直接返回 facade；main_pg 返回 state['facade']）
        get_repo:   () -> repo（main 返回模块级 repo；main_pg 返回 state['repo']）
        get_pool:   () -> optional asyncpg pool（main 返回 None；main_pg 返回 state['pool']）
        reset_fn:   () -> optional coroutine，/api/reset 后调用（双端 reset 行为不同）
        install_static: 是否挂载 /ui/ 静态资源（双端都装）
    """
    # ── /ui 静态资源
    if install_static:
        from fastapi.staticfiles import StaticFiles
        app.mount(
            "/ui/",
            StaticFiles(directory="ui/apps/demo/dist", html=True),
            name="ui",
        )

    @app.post("/wf/{action:path}")
    async def wf_flow(action: str, request: Request):
        """单入口门面转发（v1.5.0）：/wf/{action}，action 多段（如 processDefine/page）"""
        body = await request.json() if await request.body() else {}
        return await get_facade().flow(action, body)

    @app.post("/api/reset")
    async def api_reset():
        """一键重置（issues/11）：清空存储 + 重载种子。reset_fn 处理双端差异（memory 清字典 / PG TRUNCATE）。"""
        if reset_fn:
            result = await reset_fn()
            if isinstance(result, dict):
                return _ok(result)
        return _ok()

    @app.get("/healthz")
    async def healthz():
        pool_ok = True
        if get_pool is not None:
            pool = get_pool()
            pool_ok = pool is not None and not pool._closing
        return {"status": "UP", "backend": "python", "pg": "ok" if pool_ok else "down"}

    @app.get("/api/stats")
    async def api_stats(userId: str = "user1"):
        repo = get_repo()
        # 双端差异：memory 用 all_tasks()；PG 用 page_todo_tasks()
        # 通用做法：调 page_todo_tasks（memory + PG 都有，行为一致）
        todo_rows, _ = await repo.page_todo_tasks(page_num=1, page_size=9999, actor_id=userId)
        mine = await repo.query_instances_for_stats(state_in=None)
        my_inst = sum(1 for i in mine if i.operator == userId)
        return _ok({"todoCount": len(todo_rows), "myInstanceCount": my_inst})

    @app.post("/api/users")
    async def api_users(request: Request):
        from spi import SPI_USERS
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
        from spi import SPI_ROLES
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
        from spi import SPI_DICTS
        rows = [{"code": code, "items": list(items)} for code, items in SPI_DICTS.items()]
        return _ok(rows)
