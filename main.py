"""jeeflow FastAPI demo —— boot2 接口规范对齐

注意（2026-09-17 §36）：
- 本入口使用内存后端（MemoryRepository）
- 与 main_pg.py（PG 后端）行为有差异：拦截器未注册时 main.py 静默通过，main_pg.py 抛错
- 拦截器相关测试请用 main_pg.py
- 详见 docs/known-issues.md §36 / docs/flow.md §2
"""
import asyncio
import json
import mimetypes
import os
import sys

mimetypes.add_type("application/javascript", ".cjs")

# sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime

from jeeflow import EngineImpl, MemoryRepository, EventType, ProcessEvent, JeeflowFacade, \
    EngineExtensions, HandlerRegistry, register_builtin_assignments
from jeeflow.extensions import FlowInterceptor
from jeeflow.engine import _find_node, _follow_edges, _sync_task_to_aggregate
from jeeflow.memory import MemoryExtRepository
from jeeflow.model import InstanceState, TaskState, ProcessDefine, ProcessInstance, ProcessTask, UserInfo, parse_flow_model
from jeeflow.spi import IDGenerator, ExpressionEvaluator, OrgUserProvider

import flows_resolver
sys.path.insert(0, os.path.dirname(__file__))  # 确保 spi.py / seed_business.py 仓根模块可被 import
from seed_business import seed_business

# ─── Setup ───────────────────────────────────────────────────────────────────────

# 流程定义：只读本仓 flows/（flows_resolver 已在维护者机器上把 Java 源精确镜像进来）
FLOWS_DIR = flows_resolver.dir()

class SnowflakeIDGen(IDGenerator):
    """简化雪花 ID"""
    def __init__(self): self._epoch = 1700000000000; self._seq = 0
    def next_id(self) -> int:
        import time
        ts = int(time.time() * 1000) - self._epoch
        self._seq = (self._seq + 1) & 0xFFF
        return (ts << 10) | self._seq

class SimpleExprEvaluator(ExpressionEvaluator):
    """简易 SpEL 表达式：支持 amount >/>=/</<=/== number 和 #var==str；OGNL 风格 #varname 同支持

    v1.5.1 fix (FIX-T1 2026-09-17): expr 是数字但 value 是字符串时,原
    `actual = float(actual)` 抛 ValueError 导致整个 startAndExecute 失败
    (code=99999999)。修复:捕获 ValueError/TypeError 返回 False,与
    regex 不匹配、value 为 None 行为一致(走兜底首边)。

    v1.6.0 fix (FIX-T3 2026-09-17 BDD Task 32): 支持字符串相等比较
    `#var==string` / `#var!=string`。原版只支持数字,字符串比较走兜底。
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
    1. 先调 super 原版完成当前 task（super 内部做 _prepare_execute_task + 推进）
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

repo = MemoryRepository()
ext_repo = MemoryExtRepository()  # 扩展仓储（内存实现）：流程设计/历史/委托
idgen = SnowflakeIDGen()

from spi import SimpleUserProvider, SpiOrgUserProvider, spi_user_search, SPI_USERS, SPI_ROLES, SPI_DICTS
user_prov = SimpleUserProvider()
org_prov = SpiOrgUserProvider()

engine = RatioCapableEngine(repo, user_prov, idgen, SimpleExprEvaluator())
# 内置参与者 handler（部门领导/角色取人等，assignment-handler 流程依赖）
_registry = HandlerRegistry()
register_builtin_assignments(_registry, user_prov, org_prov)

# Task 24 (BDD 2026-09-17 14:02): 注册 mock 拦截器，验证 _fire_post 调用链
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
}
engine.set_extensions(EngineExtensions(registry=_registry, interceptor_registry=_ic_registry))

# v1.5.2 fix (FIX-T2 2026-09-17): handler 解析失败时记 warning 日志
# 原 engine._resolve_actors handler 解析不到返回 [] 静默失败，TDD 难以区分
# 错误 2 (FQCN 拼错 §25) 与 错误 3 (节点 id 不在 SPI) 都导致 activeTaskList=[]
# 此 wrapper 在 handler 解析失败、SPI 返回空 role 时打 warning 到 stderr + /tmp/jee-fix.log
# v1.5.3 (FIX-T2b 2026-09-17): 同时写文件 /tmp/jee-fix.log，避免 uv run 模式 stderr 丢失
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
            return []  # 与原行为一致：解析不到返回 []
    actors = await _orig_resolve_actors(node, inst, operator, vars_)
    if handler_name and not actors:
        # handler 已注册但返回 [] — 可能是 SPI role_code 不存在
        _fix_log(f"[FIX-T2 WARN] handler '{handler_name}' returned empty actors for node_id='{node.id}' (process={inst.defineId}); check SPI role_code")
    return actors
engine._resolve_actors = _logged_resolve_actors
facade = JeeflowFacade(engine, repo, ext_repo, user_search=spi_user_search, org_prov=org_prov)

# Issue D：startAndExecute business variables 嵌套解包（与 main_pg.py 同步）
# jeeflow engine.start_process_instance_by_id 把 args 整体塞到 inst.variables，
# 调用方传 {variables: {amount: 5000}} 时 amount 被嵌到 inst.variables.variables.amount，
# decision expr vars_.get("amount") 永远拿不到，expr 永远 False → fallback edges[0]。
# 此处 monkey-patch facade.flow：startAndExecute 前把 nested variables 展开到 args 顶层。
_orig_flow = facade.flow
async def _safe_flow(action, args=None):
    args = dict(args or {})
    if action in ("processDefine/startAndExecute", "processInstance/startAndExecute"):
        nested = args.get("variables")
        if isinstance(nested, dict):
            for k, val in nested.items():
                if k not in args:
                    args[k] = val
    return await _orig_flow(action, args)
facade.flow = _safe_flow

def load_seed():
    """预加载流程定义（种子）——/api/reset 重置后复用"""
    for fname in sorted(os.listdir(FLOWS_DIR)):
        if fname.endswith(".json"):
            with open(os.path.join(FLOWS_DIR, fname), "r", encoding="utf-8") as f:
                raw = json.loads(f.read())
            d = ProcessDefine(
                name=raw.get("name", fname),
                displayName=raw.get("displayName", fname),
                type=raw.get("type", ""),
                state=1,
                content=json.dumps(raw, ensure_ascii=False),
            )
            repo.add_define(d)


load_seed()

# T003：业务数据种子（引擎真实启动 16 进行中 + 9 已完成 + 8 委托），/api/reset 复跑。
# 兼容 uvicorn reload：worker 在运行中的事件循环里 import 本模块，此时挂后台任务而非 asyncio.run。
try:
    asyncio.get_running_loop()
    asyncio.get_event_loop().create_task(seed_business(facade))
except RuntimeError:
    asyncio.run(seed_business(facade))

app = FastAPI(root_path= ("/jeeflow"), title="jeeflow api", version="0.1.0")
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

def _load_graph(define_id) -> Optional[dict]:
    d = repo._defines.get(define_id)
    return json.loads(d.content) if d and d.content else None

# boot2 submitType 枚举
APPLY, AGREE, REJECT, ROLLBACK, JUMP, RE_APPLY = 0, 1, 2, 3, 4, 5
ROLLBACK_TO_OPERATOR, COUNTERSIGN_DISAGREE = 6, 20

# ─── 流程定义 ────────────────────────────────────────────────────────────────────

@app.post("/wf/{action:path}")
async def wf_flow(action: str, request: Request):
    """单入口门面转发（v1.5.0）：/wf/{action}，action 多段（如 processDefine/page）"""
    body = await request.json() if await request.body() else {}
    return await facade.flow(action, body)

@app.post("/api/reset")
async def api_reset():
    """一键重置演示数据（issues/11）：清空内存库（实例/任务/抄送/参与者 + 扩展仓储）+ 重载种子流程定义"""
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
    load_seed()
    await seed_business(facade)  # T003：reset 后复跑业务种子
    return _ok()


@app.get("/healthz")
async def healthz():
    """健康检查（四端对齐）"""
    return {"status": "UP", "backend": "python"}


@app.get("/api/stats")
async def api_stats(userId: str = "user1"):
    tasks = [t for t in repo.all_tasks() if t.taskState == TaskState.DOING and userId in repo._actors.get(t.id, [])]
    insts = [i for i in repo.all_instances() if i.operator == userId]
    return _ok({"todoCount": len(tasks), "myInstanceCount": len(insts)})


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
    # 端口可覆盖（PORT 环境变量）：本机 8100 被残留进程占用时可 PORT=8101 起
    uvicorn.run("main:app", host="0.0.0.0", port=8101, reload=True)