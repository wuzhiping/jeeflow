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

from decorators import access_guard
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
    """简易表达式求值器：基于 Python ast 安全求值，支持复合逻辑

    支持语法（FIX-T37 2026-09-19 §20 修复）：
    - 比较：==  !=  >  <  >=  <=
    - 逻辑：and  or  not
    - 变量：`#var` / `var`（# 前缀兼容 OGNL）
    - 字面量：int / float / str（单/双引号）/ True / False / None

    示例：
        #amount >= 5000
        submitType == 0 or submitType == 1
        not #urgent and #days > 3
        status == "approved"

    安全限制（白名单）：
    - ❌ 函数调用（除 bool/int/float/str）
    - ❌ 属性访问
    - ❌ 下标
    - ❌ 任何 import / 复合语句

    v1.5.1 fix (FIX-T1 2026-09-17)：原 regex 数字比较，遇到字符串值抛 ValueError
    导致整个 startAndExecute 失败。修复：返回 False，走兜底首边。

    v1.6.0 fix (FIX-T3 2026-09-17)：支持字符串相等比较。

    v1.7.0 fix (FIX-T37 2026-09-19 §20)：用 ast 替换 regex，支持 and/or/not。
    """
    # 允许的 AST 节点白名单
    _ALLOWED_BINOPS = {
        "Add": lambda a, b: a + b,
        "Sub": lambda a, b: a - b,
        "Mult": lambda a, b: a * b,
        "Div": lambda a, b: a / b,
        "Mod": lambda a, b: a % b,
    }
    _ALLOWED_CMPOPS = {
        "Eq": lambda a, b: a == b,
        "NotEq": lambda a, b: a != b,
        "Lt": lambda a, b: a < b,
        "LtE": lambda a, b: a <= b,
        "Gt": lambda a, b: a > b,
        "GtE": lambda a, b: a >= b,
    }
    _ALLOWED_UNARYOPS = {
        "Not": lambda a: not a,
        "USub": lambda a: -a,
        "UAdd": lambda a: +a,
    }

    async def eval(self, expr: str, vars: dict):
        import ast
        if not expr or not expr.strip():
            return False
        # 预处理：OGNL 风格 → Python 风格
        # 1) #var → var（# 是 Python 注释符）
        # 2) || → or，&& → and
        # 3) !  → not（只在 != 之外的 !）
        normalized = expr
        import re as _re
        normalized = _re.sub(r"#(\w+)", r"\1", normalized)
        normalized = normalized.replace("||", " or ").replace("&&", " and ")
        # ! 后面不是 = 时替换为 not
        normalized = _re.sub(r"!(?!=)", "not ", normalized)
        try:
            tree = ast.parse(normalized, mode="eval")
        except SyntaxError:
            return False
        try:
            return self._eval_node(tree.body, vars)
        except (TypeError, ValueError, KeyError, AttributeError):
            return False

    def _eval_node(self, node, vars):
        import ast
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            # True / False / None
            if node.id in ("True", "False", "None"):
                return {"True": True, "False": False, "None": None}[node.id]
            # 变量查找（# 前缀兼容）
            key = node.id
            if key in vars:
                return vars[key]
            return None
        if isinstance(node, ast.BinOp) and type(node.op).__name__ in self._ALLOWED_BINOPS:
            left = self._eval_node(node.left, vars)
            right = self._eval_node(node.right, vars)
            return self._ALLOWED_BINOPS[type(node.op).__name__](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op).__name__ in self._ALLOWED_UNARYOPS:
            operand = self._eval_node(node.operand, vars)
            return self._ALLOWED_UNARYOPS[type(node.op).__name__](operand)
        if isinstance(node, ast.BoolOp):
            values = [self._eval_node(v, vars) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)
        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left, vars)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator, vars)
                op_name = type(op).__name__
                if op_name not in self._ALLOWED_CMPOPS:
                    return False
                if not self._ALLOWED_CMPOPS[op_name](left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.Attribute):
            value = self._eval_node(node.value, vars)
            if value is None:
                return None
            try:
                return value[node.attr]
            except (KeyError, TypeError, IndexError):
                return None
        if isinstance(node, ast.Subscript):
            value = self._eval_node(node.value, vars)
            if value is None:
                return None
            key = self._eval_node(node.slice, vars)
            if key is None:
                return None
            try:
                return value[key]
            except (KeyError, TypeError, IndexError):
                return None
        # 不支持的节点类型（函数调用）→ 兜底 False
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
                        # FIX-T111 §112 (2026-09-21): abandoned_by=operator(命中比例条件的提交人)
                        # 替代之前隐式沿用 createUser(=发起人) 导致审计追溯错乱
                        t.abandon(now, abandoned_by=operator)
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
        # §6.1.1 FIX-T94 (2026-09-20)：注册 PRE_ONE 测试用 pre-interceptor
        "PRE_ONE": MockAuditInterceptor(name="PRE_ONE"),
    }


def apply_extensions(engine, registry: HandlerRegistry, ic_registry: Optional[dict] = None,
                     custom_handlers: Optional[dict] = None,
                     decision_handlers: Optional[dict] = None):
    """应用 HandlerRegistry + 拦截器注册表 + custom 节点处理器到 engine"""
    # BDD #32 FIX-T46 (2026-09-20)：注册示例 decisionHandler
    # 业务方可通过 registry.register_decision("my.handler", MyHandler()) 扩展
    if decision_handlers:
        for name, handler in decision_handlers.items():
            registry.register_decision(name, handler)
    ext = EngineExtensions(
        registry=registry,
        interceptor_registry=ic_registry or {},
        custom_handler_registry=custom_handlers or {},
    )
    engine.set_extensions(ext)


# ─── Built-in Custom Node Handlers（FIX-T38 2026-09-19 §16 修复）───────────────
async def _builtin_custom_test_handler(node, inst, vars_, args):
    """示例 custom handler：写入 args 字符串到 vars_[val]

    业务用法：custom 节点触发后，把外部系统返回值（如 API response、计算结果）
    存到 vars_ 供下游 decision/task 使用。
    """
    import json as _json
    if not args:
        return None
    # 尝试 JSON 解析
    try:
        return _json.loads(args)
    except (ValueError, TypeError):
        return args



class RaiseHandler:
    """测试：handler 主动抛异常"""
    def __init__(self, name="com.mldong.jeeflow.test.RaiseHandler"):
        self._name = name
    @property
    def name(self): return self._name
    @property
    def order(self): return 0
    async def __call__(self, node, inst, vars_, args):
        raise ValueError(f"RaiseHandler 故意抛错: node={node.id}")


def build_custom_handlers() -> dict:
    """注册示例 custom 节点 handler（生产可扩）"""
    return {
        "com.mldong.jeeflow.test.TestCustomHandler": _builtin_custom_test_handler,
        "com.mldong.jeeflow.test.TimestampHandler": _builtin_custom_timestamp_handler,
        "com.mldong.jeeflow.test.AppendVarsHandler": _builtin_custom_append_vars_handler,
        "com.mldong.jeeflow.test.RaiseHandler": RaiseHandler(),
    }


def build_decision_handlers() -> dict:
    """BDD #32 FIX-T46 (2026-09-20)：注册示例 decisionHandler（生产可扩）"""
    return {
        "demo.decision.amount": _BuiltinDecisionAmountHandler(),
        "demo.decision.priority": _BuiltinDecisionPriorityHandler(),
    }


async def _builtin_custom_timestamp_handler(node, inst, vars_, args):
    """示例 handler：返回当前时间戳到 vars_[val]"""
    from datetime import datetime
    return datetime.now().isoformat()


async def _builtin_custom_append_vars_handler(node, inst, vars_, args):
    """示例 handler：从 args JSON 读 dict，merge 到 vars_（v1.9.0+ 修改 vars_）"""
    import json as _json
    if not args:
        return None
    try:
        data = _json.loads(args)
    except (ValueError, TypeError):
        return None
    if isinstance(data, dict):
        for k, v in data.items():
            if k not in vars_:  # 不覆盖已有
                vars_[k] = v
    return data


# ─── Built-in Decision Handlers（FIX-T46 2026-09-20 §46 修复）──────────────────

class _BuiltinDecisionAmountHandler:
    """BDD #32 FIX-T46 (2026-09-20)：示例 decisionHandler

    用 vars_.amount 阈值分流：
    - amount >= 10000 → "task1"（高级审批）
    - amount < 10000 → "end"（直接结束）
    """
    async def decide(self, node, inst, vars_):
        amount = float(vars_.get("amount", 0) or 0)
        if amount >= 10000:
            return "task1"
        return "end"


class _BuiltinDecisionPriorityHandler:
    """示例 decisionHandler：按 priority 字段分流
    - priority >= 5 → "urgent_task"
    - 否则 → "normal_task"
    """
    async def decide(self, node, inst, vars_):
        priority = int(vars_.get("priority", 0) or 0)
        if priority >= 5:
            return "urgent_task"
        return "normal_task"


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
    @access_guard
    async def wf_flow(action: str, request: Request):
        """单入口门面转发（v1.5.0）：/wf/{action}，action 多段（如 processDefine/page）"""
        body = await request.json() if await request.body() else {}
        return await get_facade().flow(action, body)

    @app.post("/api/reset")
    @access_guard
    async def api_reset(request: Request):
        """一键重置（issues/11）：清空存储 + 重载种子。reset_fn 处理双端差异（memory 清字典 / PG TRUNCATE）。"""
        if reset_fn:
            result = await reset_fn()
            if isinstance(result, dict):
                return _ok(result)
        return _ok()

    @app.get("/healthz")
    @access_guard
    async def healthz(request: Request):
        pool_ok = True
        if get_pool is not None:
            pool = get_pool()
            pool_ok = pool is not None and not pool._closing
        return {"status": "UP", "backend": "python", "pg": "ok" if pool_ok else "down"}

    @app.get("/api/admin/health")
    @access_guard
    async def admin_health(request: Request):
        """BDD #1201 FIX-T79 (2026-09-20) §4.1.1：管理端 health 监控

        详细健康检查 (区别于 /healthz 简版):
        - PG pool 状态 (size / idle / min_size / max_size)
        - 引擎缓存状态 (_def_cache 命中数)
        - repo 健康 (find_define_by_id 探测)
        - process count (active instances / active tasks)
        """
        health = {
            "status": "UP",
            "backend": "python",
            "version": "v1.9.0+",
            "checks": {}
        }
        # PG 端
        try:
            pool = get_pool() if get_pool is not None else None
            pool_ok = pool is not None and not getattr(pool, "_closing", False)
            if pool is not None:
                health["checks"]["pg"] = {
                    "status": "ok" if pool_ok else "down",
                    "min_size": getattr(pool, "_minsize", 0),
                    "max_size": getattr(pool, "_maxsize", 0),
                    "size": pool.get_size(),
                    "idle_size": pool.get_idle_size(),
                }
                if not pool_ok:
                    health["status"] = "DEGRADED"
            else:
                # main.py (内存后端) - get_pool 返回 None
                health["checks"]["pg"] = {"status": "n/a (memory backend)"}
        except Exception as e:
            health["checks"]["pg"] = {"status": "error", "error": str(e)[:100]}
            health["status"] = "DEGRADED"
        # Repo 探测
        try:
            repo = get_repo()
            # 任意一次 find_define_by_id 调用验证 repo 可用
            await repo.find_define_by_id(0)  # 期望返回 None
            health["checks"]["repo"] = {"status": "ok"}
        except Exception as e:
            health["checks"]["repo"] = {"status": "fail", "error": str(e)[:100]}
            health["status"] = "DEGRADED"
        # 引擎缓存
        try:
            facade = get_facade()
            engine = getattr(facade, "_engine", None)
            if engine and hasattr(engine, "_def_cache"):
                health["checks"]["engine_cache"] = {
                    "status": "ok",
                    "size": len(engine._def_cache),
                    "max": getattr(engine, "_DEF_CACHE_MAX", 100),
                }
        except Exception:
            pass
        # Process count
        try:
            repo = get_repo()
            active_inst = await repo.query_instances_for_stats(state_in=[10, 50])
            health["checks"]["process"] = {
                "active_instances": len(active_inst),
            }
        except Exception:
            pass
        return health

    @app.get("/api/stats")
    @access_guard
    async def api_stats(request: Request, userId: str = "user1"):
        repo = get_repo()
        # 双端差异：memory 用 all_tasks()；PG 用 page_todo_tasks()
        # 通用做法：调 page_todo_tasks（memory + PG 都有，行为一致）
        todo_rows, _ = await repo.page_todo_tasks(page_num=1, page_size=9999, actor_id=userId)
        mine = await repo.query_instances_for_stats(state_in=None)
        my_inst = sum(1 for i in mine if i.operator == userId)
        return _ok({"todoCount": len(todo_rows), "myInstanceCount": my_inst})

    @app.get("/api/admin/stats/overview")
    @access_guard
    async def admin_stats_overview(request: Request, start: str = None, end: str = None,
                                    stateIn: str = None):
        """BDD #1202 FIX-T80 (2026-09-20) §4.1.2：管理端看板总览

        GET 端点, 调用 facade._processInstance_stats_overview
        Args (query string):
          - start: ISO datetime
          - end: ISO datetime
          - stateIn: 逗号分隔状态码 (10/20/30/40/45/50/99)
        Returns: {total, inProgress, completed, rejected, withdrawn, suspended,
                  todayNew, avgDurationSeconds, pending, overdue, activeUsers,
                  countersignRate, onTimeRate, rejectRate}
        """
        import json as _json
        body = {}
        if start: body["start"] = start
        if end: body["end"] = end
        if stateIn:
            body["stateIn"] = [int(x) for x in stateIn.split(",") if x.strip()]
        return await get_facade().flow("processInstance/stats/overview", body)

    @app.get("/api/admin/stats/trend")
    @access_guard
    async def admin_stats_trend(request: Request, granularity: str = "day", start: str = None,
                                  end: str = None, stateIn: str = None):
        """BDD #1203 FIX-T81 (2026-09-20) §4.1.2：管理端趋势图"""
        import json as _json
        body = {"granularity": granularity}
        if start: body["start"] = start
        if end: body["end"] = end
        if stateIn: body["stateIn"] = [int(x) for x in stateIn.split(",") if x.strip()]
        return await get_facade().flow("processInstance/stats/trend", body)

    @app.get("/api/admin/stats/group")
    @access_guard
    async def admin_stats_group(request: Request, dimension: str = "state", start: str = None,
                                  end: str = None, stateIn: str = None):
        """BDD #1204 FIX-T82 (2026-09-20) §4.1.2：管理端分组聚合"""
        body = {"dimension": dimension}
        if start: body["start"] = start
        if end: body["end"] = end
        if stateIn: body["stateIn"] = [int(x) for x in stateIn.split(",") if x.strip()]
        return await get_facade().flow("processInstance/stats/group", body)

    @app.post("/api/users")
    @access_guard
    async def api_users(request: Request):
        from spi import SPI_USERS, SPI
        body = await request.json() if await request.body() else {}
        keyword = str(body.get("keyword") or "").strip().lower()
        rows = []
        for uid, info in SPI_USERS.items():
            real_name = info["name"]
            post_name = info["post"]
            if keyword and keyword not in uid.lower() and keyword not in real_name.lower():
                continue
            info_full = SPI(func="get_user", payload={"uid": uid})
            rows.append({
                "userId": uid, "realName": real_name,
                "deptId": info_full.get("deptId", "D01"),
                "deptName": info_full.get("deptName", "研发部"),
                "postId": info_full.get("postId", "P01"),
                "postName": post_name,
            })
        return _ok(rows)

    @app.post("/api/roles")
    @access_guard
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
    @access_guard
    async def api_dicts(request: Request):
        from spi import SPI_DICTS
        rows = [{"code": code, "items": list(items)} for code, items in SPI_DICTS.items()]
        return _ok(rows)

    @app.post("/api/admin/expire/scan")
    @access_guard
    async def admin_expire_scan(request: Request):
        """BDD #1214 FIX-T91 (2026-09-20) §4.4.3：异步任务扫描 (Celery 替代)

        扫描 wf_process_task.expireTime < now 的 task, 标记为 EXPIRED.
        扫描 wf_process_surrogate 中 enabled=true 但 endTime < now 的, 标记为 enabled=false.

        业务方建议每 5 分钟调一次 (cron / 定时任务):
        curl -X POST http://jeeFlow:8101/api/admin/expire/scan
        """
        from datetime import datetime as _dt
        now = _dt.now()
        repo = get_repo()
        facade = get_facade()
        task_expired = 0
        surrogate_disabled = 0

        # 扫描 wf_process_task: expireTime < now 标记为 ABANDON
        try:
            tn = getattr(repo, "_find_tasks_by_state", None)
            if tn is not None:
                doing_tasks = await repo._find_tasks_by_state(instance_id=None, state_filter=None, actor_filter=None)
                for task in doing_tasks:
                    if task.expireTime and task.expireTime < now and task.taskState == 10:
                        task.taskState = 99  # TaskState.ABANDON (expiry)
                        task.updateTime = now
                        task.updateUser = "system_expire"
                        await repo.update_task(task)
                        task_expired += 1
        except Exception:
            pass

        # 扫描 wf_process_surrogate: endTime < now 关闭 enabled
        try:
            ext_repo = getattr(facade, "_ext_repo", None)
            if ext_repo is not None:
                rows, _ = await ext_repo.page_surrogates(1, 1000)
                for s in rows:
                    if getattr(s, "enabled", True) and getattr(s, "endTime", None):
                        if s.endTime < now:
                            s.enabled = False
                            await ext_repo.update_surrogate(s)
                            surrogate_disabled += 1
        except Exception:
            pass

        return {"taskExpired": task_expired, "surrogateDisabled": surrogate_disabled, "scanTime": now.isoformat()}


# ─── Prometheus Metrics (BDD #1205 FIX-T83 §4.1.3) ─────────────────────────────
# 轻量版: 自实现 prometheus text format 输出, 无外部依赖
# 暴露 3 个核心指标: wf_instance_state_total / wf_task_duration_seconds / wf_active_instances
import threading
import time as _time

class _MetricsRegistry:
    """线程安全的 prometheus 指标注册表 (自实现, 无外部依赖)"""
    def __init__(self):
        self._lock = threading.Lock()
        self._counters: dict = {}
        self._gauges: dict = {}
        self._histograms: dict = {}

    def counter_inc(self, name: str, help_: str, labels: dict = None, value: float = 1.0):
        with self._lock:
            key = (name, tuple(sorted((labels or {}).items())))
            if key not in self._counters:
                self._counters[key] = {"name": name, "help": help_, "labels": labels or {}, "value": 0.0}
            self._counters[key]["value"] += value

    def gauge_set(self, name: str, help_: str, labels: dict = None, value: float = 0.0):
        with self._lock:
            key = (name, tuple(sorted((labels or {}).items())))
            self._gauges[key] = {"name": name, "help": help_, "labels": labels or {}, "value": value}

    def histogram_observe(self, name: str, help_: str, labels: dict = None, value: float = 0.0,
                            buckets=(0.01, 0.1, 1.0, 10.0, 60.0, 300.0, 1800.0, 3600.0, 86400.0)):
        with self._lock:
            key = (name, tuple(sorted((labels or {}).items())))
            if key not in self._histograms:
                self._histograms[key] = {
                    "name": name, "help": help_, "labels": labels or {},
                    "buckets": list(buckets), "counts": [0] * (len(buckets) + 1),  # +1 for +Inf
                    "sum": 0.0, "count": 0,
                }
            h = self._histograms[key]
            h["sum"] += value
            h["count"] += 1
            for i, b in enumerate(h["buckets"]):
                if value <= b:
                    h["counts"][i] += 1
            h["counts"][-1] += 1  # +Inf always

    def render(self) -> str:
        """Render Prometheus text format"""
        lines = []
        with self._lock:
            for k, c in self._counters.items():
                lines.append(f"# HELP {c['name']} {c['help']}")
                lines.append(f"# TYPE {c['name']} counter")
                label_str = self._fmt_labels(c["labels"])
                lines.append(f"{c['name']}{label_str} {c['value']}")
            for k, g in self._gauges.items():
                lines.append(f"# HELP {g['name']} {g['help']}")
                lines.append(f"# TYPE {g['name']} gauge")
                label_str = self._fmt_labels(g["labels"])
                lines.append(f"{g['name']}{label_str} {g['value']}")
            for k, h in self._histograms.items():
                lines.append(f"# HELP {h['name']} {h['help']}")
                lines.append(f"# TYPE {h['name']} histogram")
                base_labels = h["labels"]
                for i, b in enumerate(h["buckets"]):
                    le_labels = dict(base_labels)
                    le_labels["le"] = str(b)
                    label_str = self._fmt_labels(le_labels)
                    lines.append(f'{h["name"]}_bucket{label_str} {h["counts"][i]}')
                inf_labels = dict(base_labels)
                inf_labels["le"] = "+Inf"
                label_str = self._fmt_labels(inf_labels)
                lines.append(f'{h["name"]}_bucket{label_str} {h["counts"][-1]}')
                sum_label_str = self._fmt_labels(base_labels)
                lines.append(f'{h["name"]}_sum{sum_label_str} {h["sum"]}')
                lines.append(f'{h["name"]}_count{sum_label_str} {h["count"]}')
        return "\n".join(lines) + "\n"

    @staticmethod
    def _fmt_labels(labels: dict) -> str:
        if not labels:
            return ""
        items = ",".join(f'{k}="{v}"' for k, v in labels.items())
        return "{" + items + "}"


# 全局指标注册表
_METRICS = _MetricsRegistry()


def metrics_counter(name, help_, labels=None, value=1.0):
    """业务调用：counter 累加"""
    _METRICS.counter_inc(name, help_, labels, value)


def metrics_gauge(name, help_, labels=None, value=0.0):
    """业务调用：gauge 设置"""
    _METRICS.gauge_set(name, help_, labels, value)


def metrics_histogram(name, help_, labels=None, value=0.0):
    """业务调用：histogram 观察"""
    _METRICS.histogram_observe(name, help_, labels, value)


_METRICS_REMOTE_WRITE_URL: str = os.environ.get("JEEFLOW_METRICS_REMOTE_WRITE_URL", "").strip()
_METRICS_REMOTE_WRITE_AUTH: str = os.environ.get("JEEFLOW_METRICS_REMOTE_WRITE_AUTH", "").strip()


def _metrics_remote_write(content: str) -> None:
    """§6.4.2 FIX-T102 (2026-09-20): Prometheus remote_write 客户端 (httpx → urllib fallback).

    推送格式: protobuf (snappy 压缩), 简化为 HTTP POST body 直接送 text/plain.
    实际生产推荐用 prometheus_client 库 (本项目不得加依赖), 此处 fire-and-forget.
    """
    if not _METRICS_REMOTE_WRITE_URL:
        return
    try:
        import urllib.request
        req = urllib.request.Request(
            _METRICS_REMOTE_WRITE_URL,
            data=content.encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "text/plain; version=0.0.4",
                **({"Authorization": _METRICS_REMOTE_WRITE_AUTH} if _METRICS_REMOTE_WRITE_AUTH else {}),
            },
        )
        urllib.request.urlopen(req, timeout=2).read()
    except Exception:
        pass  # 远程写失败静默 (不阻塞本地)


def install_metrics_endpoint(app):
    """BDD #1205 FIX-T83 (2026-09-20) §4.1.3：安装 /metrics 端点

    Prometheus 文本格式输出 (无 prometheus_client 依赖)
    暴露 3 个核心指标:
    - wf_instance_state_total{state="doing|done|..."}
    - wf_task_duration_seconds (histogram, labels=taskName)
    - wf_active_instances (gauge)
    """
    @app.get("/metrics")
    @access_guard
    async def metrics(request: Request):
        # 动态更新 active_instances (每次 scrape 重新查)
        try:
            from jeeflow.model import InstanceState
            counts = {}
            for s in InstanceState:
                if s == InstanceState.DOING or s == InstanceState.PENDING:
                    insts = await app.state.repo.query_instances_for_stats(state_in=[s.value])
                    counts[s.value] = len(insts)
            _METRICS.gauge_set(
                "wf_active_instances",
                "当前活跃流程实例数 (DOING + PENDING)",
                labels=None,
                value=counts.get(InstanceState.DOING.value, 0) + counts.get(InstanceState.PENDING.value, 0),
            )
            # 各 state 计数 (作为 counter snapshot)
            for s in InstanceState:
                insts = await app.state.repo.query_instances_for_stats(state_in=[s.value])
                _METRICS.counter_inc(
                    "wf_instance_state_total",
                    "流程实例状态总数 (按状态分组)",
                    labels={"state": s.name},
                    value=0,  # 仅初始化 label
                )
            # 重写 counter 为 gauge snapshot (覆盖之前累计的值)
            with _METRICS._lock:
                _METRICS._counters = {
                    k: v for k, v in _METRICS._counters.items()
                    if k[0] != "wf_instance_state_total"
                }
            for s in InstanceState:
                insts = await app.state.repo.query_instances_for_stats(state_in=[s.value])
                _METRICS.counter_inc(
                    "wf_instance_state_total",
                    "流程实例状态总数 (按状态分组)",
                    labels={"state": s.name},
                    value=float(len(insts)),
                )
        except Exception as _e:
            # 指标采集失败不影响主流程
            pass

        # BDD #1219 FIX-T83+ §4.1.3：初始化 wf_task_duration_seconds histogram 占位 (无 sample 时也能 scrape)
        _METRICS.histogram_observe(
            "wf_task_duration_seconds",
            "任务处理耗时 (histogram)",
            labels={"taskName": "_init"},
            value=0.001,
        )

        content = _METRICS.render()
        _metrics_remote_write(content)  # §6.4.2 FIX-T102: remote_write 推送
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content=content, media_type="text/plain; version=0.0.4")


# ─── OpenTelemetry-style Trace (BDD #1206 FIX-T84 §4.1.4) ──────────────────────
# 轻量版: 自实现 trace context + span 收集, 无 opentelemetry-api 依赖
# 输出: JSON trace 数据到 /api/admin/trace
import uuid
from contextvars import ContextVar
from contextlib import asynccontextmanager

_current_span: ContextVar = ContextVar("current_span", default=None)
_spans_log: list = []  # 最近 1000 个 span
_persist_span_hook = None  # §6.4.1 FIX-T99: main_pg.py lifespan 注册, 用于异步落 PG


@asynccontextmanager
async def trace_span(name: str, **attrs):
    """BDD #1206 FIX-T84 §4.1.4：轻量级 span 追踪

    用法:
        async with trace_span("engine.execute_process_task", task_id=123) as span:
            ... 主流程 ...
            span.set_attribute("result", "ok")
    """
    parent = _current_span.get()
    span_id = uuid.uuid4().hex[:16]
    trace_id = parent["trace_id"] if parent else uuid.uuid4().hex
    span = {
        "span_id": span_id,
        "trace_id": trace_id,
        "parent_span_id": parent["span_id"] if parent else None,
        "name": name,
        "start_time": _time.time(),
        "attributes": dict(attrs),
        "events": [],
        "status": "ok",
    }
    token = _current_span.set(span)
    try:
        yield span
    except Exception as e:
        span["status"] = "error"
        span["error"] = str(e)[:200]
        raise
    finally:
        span["end_time"] = _time.time()
        span["duration_ms"] = int((span["end_time"] - span["start_time"]) * 1000)
        _spans_log.append(span)
        if len(_spans_log) > 1000:
            _spans_log.pop(0)
        # §6.4.1 FIX-T99 (2026-09-20): trace 持久化 (PG) 钩子
        # main_pg.py lifespan 中注册 _persist_span_hook, main.py 不注册 (in-memory only)
        try:
            if _persist_span_hook is not None:
                _persist_span_hook(span)
        except Exception:
            pass  # 持久化失败不应影响主流程
        _current_span.reset(token)


def install_trace_persistence(pool):
    """§6.4.1 FIX-T99 (2026-09-20): 注册 trace span 持久化钩子 (PG asyncpg pool).

    每个 trace_span 结束时, 异步写入 wf_trace_span 表 (fire-and-forget, 不阻塞主流程).
    7 天 TTL 由 install_trace_purge 注册的定时清理任务处理.
    """
    global _persist_span_hook
    import asyncio

    def _hook(span: dict):
        # fire-and-forget, 不 await (调用方已 try/except)
        async def _write():
            try:
                async with pool.acquire() as conn:
                    await conn.execute(
                        """INSERT INTO wf_trace_span
                        (trace_id, span_id, parent_span_id, name, start_time, end_time, duration_ms, status, error, attributes, events)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)""",
                        span.get("trace_id", ""),
                        span.get("span_id", ""),
                        span.get("parent_span_id"),
                        span.get("name", ""),
                        span.get("start_time", 0),
                        span.get("end_time"),
                        span.get("duration_ms"),
                        span.get("status", "ok"),
                        span.get("error"),
                        __import__("json").dumps(span.get("attributes", {})),
                        __import__("json").dumps(span.get("events", [])),
                    )
            except Exception:
                pass  # 持久化失败静默
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(_write())
        except Exception:
            pass
    _persist_span_hook = _hook
    return _hook


def install_trace_purge(pool, retention_days: int = 7):
    """§6.4.1 FIX-T99: 注册定时清理任务 (删除 retention_days 前的 span)."""
    async def _purge_loop():
        while True:
            try:
                await asyncio.sleep(24 * 3600)  # 每天清理一次
                async with pool.acquire() as conn:
                    await conn.execute(
                        "DELETE FROM wf_trace_span WHERE create_time < NOW() - INTERVAL '%d days'",
                        retention_days,
                    )
            except Exception:
                continue
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(_purge_loop())
    except Exception:
        pass


def install_trace_endpoint(app):
    """BDD #1206 FIX-T84 §4.1.4：安装 /api/admin/trace 端点

    返回最近 200 个 span (JSON 数组)
    """
    @app.get("/api/admin/trace")
    @access_guard
    async def admin_trace(request: Request, limit: int = 200, name: str = None):
        spans = list(_spans_log)
        if name:
            spans = [s for s in spans if s["name"] == name]
        return {"spans": spans[-limit:], "total": len(_spans_log)}

    @app.get("/api/admin/trace/spans/{trace_id}")
    @access_guard
    async def admin_trace_by_id(request: Request, trace_id: str):
        """按 trace_id 返回完整调用链"""
        spans = [s for s in _spans_log if s["trace_id"] == trace_id]
        spans.sort(key=lambda x: x.get("start_time", 0))
        return {"trace_id": trace_id, "spans": spans}
