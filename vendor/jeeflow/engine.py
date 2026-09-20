"""引擎核心——对标 Java EngineImpl"""
import logging
import json, time, random
from datetime import datetime
from typing import Any, Optional
from .model import (
    FlowModel, FlowNode, FlowEdge,
    TYPE_START, TYPE_END, TYPE_TASK, TYPE_DECISION, TYPE_FORK, TYPE_JOIN, TYPE_CUSTOM,
    TYPE_CALL_ACTIVITY,  # BDD #1102 FIX-T73 §3.1.2
    ProcessInstance, ProcessTask, ProcessDefine,
    InstanceState, TaskState, SubmitType, PerformType,
    parse_flow_model,
)
from .spi import ProcessRepository, UserProvider, IDGenerator, ExpressionEvaluator
from .extensions import EngineExtensions, EventType, ProcessEvent

KEY_SUBMIT_TYPE   = "submitType"
KEY_BUSINESS_NO   = "BUSINESS_NO"
KEY_USER_ID       = "u_userId"
KEY_REAL_NAME     = "u_realName"
KEY_DEPT_ID       = "u_deptId"
KEY_DEPT_NAME     = "u_deptName"
KEY_POST_ID       = "u_postId"
KEY_POST_NAME     = "u_postName"
# v1.0.1：下一节点处理人（对齐 boot3 tf_nextNodeOperator）
KEY_NEXT_NODE_OPERATOR = "tf_nextNodeOperator"
# v1.6.0：流程启动时预指派人（对齐 boot3 f_nextNodeOperator）——startAndExecute 时转换为 tf_
KEY_PROCESS_START_NEXT_NODE_OPERATOR = "f_nextNodeOperator"
# v1.0.1：系统代执行 / 超级管理员（对齐 boot3 FlowConst）
KEY_AUTO_ID   = "flow.auto"
KEY_ADMIN_ID  = "flow.admin"
# issue 29：自动生成标题（对齐 boot3 FlowConst.AUTO_GEN_TITLE）
KEY_AUTO_GEN_TITLE = "autoGenTitle"

class Engine:
    """引擎接口"""

    async def start_process_instance_by_id(self, define_id: int, operator: str, args: dict[str, Any] = None) -> ProcessInstance: ...
    async def execute_process_task(self, task_id: int, operator: str, args: dict[str, Any] = None) -> ProcessInstance: ...
    async def execute_and_jump_to_end(self, task_id: int, operator: str, args: dict[str, Any] = None) -> ProcessInstance: ...
    async def execute_and_jump_task(self, task_id: int, operator: str, args: dict[str, Any] = None, target_task_name: str = None) -> ProcessInstance: ...
    async def execute_and_jump_to_first_task_node(self, task_id: int, operator: str, args: dict[str, Any] = None) -> ProcessInstance: ...

class EngineImpl(Engine):
    def __init__(self, repo: ProcessRepository, user_prov: UserProvider = None,
                 id_gen: IDGenerator = None, expr_eval: ExpressionEvaluator = None,
                 org_prov: Optional["OrgUserProvider"] = None):
        self.repo = repo
        self.user_prov = user_prov
        self.id_gen = id_gen
        self.expr_eval = expr_eval
        self.org_prov = org_prov  # BDD #294 FIX-T57 (2026-09-19)：@role: 解析
        self.ext: Optional[EngineExtensions] = None
        self._ic_cache: dict = {}   # 定义级拦截器解析缓存（issue 34，按 defineId）
        self._last_created_tasks: list = []  # FIX-T61：临时存储当前 _create_task 创建的 task
        # BDD #1107 FIX-T78 (2026-09-20) §3.3.2：流程定义缓存 (LRU, max=100)
        # 避免每次 startAndExecute 都从 repo 读完整 flow JSON + parse
        # 部署 (processDefine/deploy / processDefine/redeploy) 时 facade._deploy_invalidate_cache 失效
        self._def_cache: "collections.OrderedDict[int, ProcessDefine]" = __import__("collections").OrderedDict()
        self._DEF_CACHE_MAX = 100

    def invalidate_define_cache(self, define_id: int = None):
        """失效流程定义缓存 (deploy/redeploy 时调用)"""
        if define_id is None:
            self._def_cache.clear()
        else:
            self._def_cache.pop(define_id, None)

    def set_extensions(self, ext: EngineExtensions):
        self.ext = ext
        self._ic_cache.clear()

    def set_ext_repo(self, ext_repo) -> None:
        # BDD #567 FIX-T62 (2026-09-19)：注入 ext_repo 让 _is_surrogate_allowed 可查 surrogate
        self._ext_repo_ref = ext_repo

    async def eval_expr(self, expr: str, vars_: dict) -> Any:
        """表达式求值（v1.5.0，门面 highLight 决策分支过滤用）"""
        if self.expr_eval is None:
            raise ValueError("ExpressionEvaluator 未配置")
        return await self.expr_eval.eval(expr, vars_)

    # ─── Start ────────────────────────────────────────────────────────────────

    async def start_process_instance_by_id(self, define_id: int, operator: str, args: dict[str, Any] = None) -> ProcessInstance:
        def_ = await self.repo.find_define_by_id(define_id)
        if not def_: raise ValueError(f"define not found: {define_id}")
        flow = parse_flow_model(json.loads(def_.content))
        vars_ = {**(args or {})}
        await self._add_user_info(operator, vars_)
        self._add_auto_gen_title(def_.displayName, vars_)
        # FIX-T9 (2026-09-17) §66 ownerId 提取：显式 ownerId > 发起时 u_userId > operator
        # 必须 _add_user_info 之后再取（_add_user_info 会用 user_prov 覆盖 u_userId）
        owner_id = (
            str(args.get("ownerId", "") or "").strip()
            or str(args.get("u_userId", "") or "").strip()  # 发起时传的原始 u_userId（不被 user_prov 覆盖）
            or operator
        )
        inst = ProcessInstance(id=self._next_id(), defineId=define_id, operator=operator,
                               ownerId=owner_id,
                               parentId=int(args.get("parentId")) if args.get("parentId") is not None else None,  # FIX-T33 (2026-09-18) §56
                               parentNodeName=str(args.get("parentNodeName") or ""),  # §7.3.2 FIX-T108 (2026-09-20) callActivity
                               variables=vars_, createTime=datetime.now(), updateTime=datetime.now(),
                               createUser=operator, updateUser=operator,
                               businessNo=str(vars_.get(KEY_BUSINESS_NO, "")))
        await self.repo.save_instance(inst)
        await self._fire_event(ProcessEvent(type=EventType.PROCESS_START, instanceId=inst.id, operator=operator))
        start_node = _find_by_type(flow, TYPE_START)
        if not start_node: raise ValueError("no start node")
        try:
            for node in _follow_edges(flow, start_node.id):
                await self._execute_node(flow, inst, node, operator, vars_)
        except ValueError as e:
            # FIX-T17 (2026-09-17)：start 路径节点创建失败 → instance 标记 ABANDON
            from .model import InstanceState, TaskState
            inst.state = InstanceState.ABANDON
            inst.updateTime = datetime.now()
            # BDD #144 FIX-T44 (2026-09-19)：同步废弃所有 DOING 任务
            for t in inst.tasks:
                if t.taskState == TaskState.DOING:
                    t.taskState = TaskState.ABANDONED
                    t.updateTime = datetime.now()
                    t.updateUser = operator
            try:
                await self.repo.update_instance(inst)
                for t in inst.tasks:
                    if t.taskState == TaskState.ABANDONED:
                        try:
                            await self.repo.update_task(t)
                        except Exception:
                            pass
            except Exception:
                pass
            raise
        return await self.repo.find_instance_by_id(inst.id)

    # ─── Execute ──────────────────────────────────────────────────────────────

    async def execute_process_task(self, task_id: int, operator: str, args: dict[str, Any] = None) -> ProcessInstance:
        task, inst, flow, vars_ = await self._prepare_execute_task(task_id, operator, args)
        now = datetime.now()
        cur_node = _find_node(flow, task.taskName)
        if cur_node:
            # 1.8.0：任务完成节点自身的后置拦截器（SYNC 同步演进——任务节点推进更新状态/字段）。
            # _create_task 不再触发（引擎语义修正），此处为完成任务节点的唯一触发点
            await self._fire_post(cur_node, inst)
            ct = cur_node.properties.get("countersignType", "")
            cs_cond = str(cur_node.properties.get("countersignCompletionCondition", "") or "").strip()
            # issues/91：会签一票否决仅当节点配置 ONE_VOTE_VETO（忽略大小写）时生效，
            # submitType=20 才跳过会签"未完成即停留"门控提前流转；否则为软拒绝——
            # 否决者任务正常完成、countersignDisagreeFlag=1 已记录为变量（供下游参考），
            # 流程不阻断（对齐 mldong 内置引擎 / Java CountersignHandler）
            try:
                cs_veto = ct != "" and cs_cond.upper() == "ONE_VOTE_VETO" and \
                    int(vars_.get(KEY_SUBMIT_TYPE, -1)) == int(SubmitType.COUNTERSIGN_DISAGREE)
            except (ValueError, TypeError):
                cs_veto = False
            if ct == "SEQUENTIAL" and not cs_veto:
                doing = await self.repo.find_doing_tasks(inst.id)
                if not doing:
                    actors, lc = _get_cs_state(vars_, cur_node.id)
                    if actors and lc + 1 < len(actors):
                        # 聚合根：创建串行会签下一步任务
                        nt = inst.create_task(self._next_id(), cur_node.id, cur_node.text.get("value", ""),
                                              actors[lc + 1], operator, cur_node.properties.get("form", ""), now, 1)
                        nt.variables = {f"operatorList_{cur_node.id}": actors, f"loopCounter_{cur_node.id}": lc + 1,
                                        f"nrOfInstances_{cur_node.id}": len(actors)}
                        await self.repo.save_task(nt)
                        # TASK_CREATE：顺序会签推进新任务落库后 fire（对齐 Java CreateTaskHandler）
                        await self._fire_event(ProcessEvent(EventType.TASK_CREATE, inst.id, nt.id, cur_node.id, operator))
                        return await self.repo.find_instance_by_id(inst.id)
                else:
                    return await self.repo.find_instance_by_id(inst.id)
            if (ct in ("PARALLEL",) or ct.startswith("RATIO")) and not cs_veto:
                doing = await self.repo.find_doing_tasks(inst.id)
                if doing: return await self.repo.find_instance_by_id(inst.id)

            # issues/91：会签节点 merged 后（ONE_VOTE_VETO 否决 / 全部完成任一路径），
            # 废弃该节点剩余 DOING 任务（对齐内置引擎 abandonProcessTask）：
            # SEQUENTIAL 逐人创建天然 no-op；PARALLEL 全员预创建，否决时废弃其余成员
            # （刚完成者已 DONE 不会误伤）。逐条持久化并回写聚合副本（E25：防 update_instance 级联回写旧状态）
            # FIX-T111 §112 (2026-09-21): 显式传 abandoned_by=operator(命中完成条件的提交人)
            # 替代之前隐式沿用 createUser(=发起人),导致审计追溯错乱的问题
            if ct:
                remaining = await self.repo.find_doing_tasks(inst.id, [cur_node.id])
                for t in remaining:
                    t.abandon(now, abandoned_by=operator)
                    await self.repo.update_task(t)
                    _sync_task_to_aggregate(inst, t)
                # BDD #129 FIX-T46 (2026-09-19)：ONE_VOTE_VETO REJECT 路径
                # 一票否决触发后立即将 instance 标记为 REJECT (state=45)
                # 否则下游走到 end 节点会调用 inst.finish() → state=20 DONE
                # 与"否决"语义不符（业务方期望 state=45 REJECTED）
                if cs_veto:
                    from .model import InstanceState
                    inst.state = InstanceState.REJECT
                    inst.updateTime = now
                    # BDD #148 FIX-T47 (2026-09-19)：废弃 instance 全部 DOING 任务
                    # 不限于当前节点（fork 出来的其他分支 task 也得清，否则孤立 todo）
                    all_remaining = await self.repo.find_doing_tasks(inst.id)
                    for t in all_remaining:
                        t.taskState = TaskState.ABANDONED
                        t.updateTime = now
                        t.updateUser = operator
                        await self.repo.update_task(t)
                        _sync_task_to_aggregate(inst, t)
                    await self.repo.update_instance(inst)
                    await self._fire_event(ProcessEvent(EventType.PROCESS_REJECT, inst.id, task_id, operator=operator))
                    # FIX-T46：否决后不往下游推进（end 节点会覆盖 state=20 DONE）
                    return await self.repo.find_instance_by_id(inst.id)

            for node in _follow_edges(flow, cur_node.id):
                # 统一走 _execute_node：结束节点也经节点执行链（拦截器/事件完整触发），
                # _execute_node 内部 TYPE_END 分支完成聚合根 finish + 事件发布
                await self._execute_node(flow, inst, node, operator, vars_)
        return await self.repo.find_instance_by_id(inst.id)

    # ─── Reject ───────────────────────────────────────────────────────────────

    async def execute_and_jump_to_end(self, task_id: int, operator: str, args: dict[str, Any] = None) -> ProcessInstance:
        _, inst, _, _ = await self._prepare_execute_task(task_id, operator, args)
        # 门面 submitType=2 REJECT 唯一入口（对齐 Java executeAndJumpToEnd 语义）
        inst.reject(datetime.now())
        await self.repo.update_instance(inst)
        # §7.3.2 FIX-T108 (2026-09-20) callActivity 主子回滚
        # 子实例 REJECT → 主实例自动 rollback 到 callActivity 节点
        if inst.parentId and inst.variables.get("__rollbackOnChildFail__") and inst.parentNodeName:
            try:
                parent = await self.repo.find_instance_by_id(inst.parentId)
                if parent and parent.state in (InstanceState.DOING, InstanceState.PENDING):
                    parent.rollback(inst.parentNodeName, datetime.now(), operator)
                    await self.repo.update_instance(parent)
            except Exception:
                pass  # 主实例可能不存在或已被删除
        await self._fire_event(ProcessEvent(EventType.PROCESS_REJECT, inst.id, task_id, operator=operator))
        return await self.repo.find_instance_by_id(inst.id)

    # ─── Jump（ROLLBACK 空 target / JUMP 命名 target，boot2 executeAndJumpTask）──

    async def execute_and_jump_task(self, task_id: int, operator: str, args: dict[str, Any] = None,
                                     target_task_name: str = None) -> ProcessInstance:
        task, inst, flow, vars_ = await self._prepare_execute_task(task_id, operator, args)
        if not target_task_name:
            # issues/79：ROLLBACK 对齐 Java rejectTask——退回上一任务节点（首条输入边 source）；
            # §52 修复（2026-09-19 FIX-T36）：根据"是否首任务节点"分支：
            #   - 跳首任务：actor=inst.operator（发起人），避免 §52 错位
            #   - 跳非首任务：actor=前任务完成人（保留 Java rejectTask 语义）
            # 走 _execute_node 复用 §27 FIX-T35 修复（悲观锁+去重）
            prev_name = self._previous_task_name(flow, task.taskName)
            if prev_name:
                prev = _find_node(flow, prev_name)
                if prev:
                    if prev.type == TYPE_TASK:
                        if self._is_first_task_node(flow, prev):
                            prev.properties["assignee"] = inst.operator
                        else:
                            # 跳非首任务：assignee 改为前任务完成人（对齐 Java rejectTask）
                            prev.properties["assignee"] = task.actorId or operator
                    await self._execute_node(flow, inst, prev, operator, vars_)
        else:
            # issues/79：对齐 Java——目标节点不存在显式报错（前端 JUMP 无效 taskName 不再静默空操作）
            target = _find_node(flow, target_task_name)
            if target is None:
                raise ValueError(f"根据节点名称[{target_task_name}]无法找到节点模型")
            # 对齐 Java isFirstTaskName：跳首任务节点（start 直接后继）assignee 强制为发起人
            if target.type == TYPE_TASK and self._is_first_task_node(flow, target):
                target.properties["assignee"] = inst.operator
            await self._execute_node(flow, inst, target, operator, vars_)
        return await self.repo.find_instance_by_id(inst.id)

    # ─── Jump To First Task（退回发起人，boot2 ROLLBACK_TO_OPERATOR=6）───────

    async def execute_and_jump_to_first_task_node(self, task_id: int, operator: str,
                                                   args: dict[str, Any] = None) -> ProcessInstance:
        _, inst, flow, vars_ = await self._prepare_execute_task(task_id, operator, args)
        # 找到第一个任务节点，强制参与者为发起人，重新执行
        start_node = _find_by_type(flow, TYPE_START)
        if start_node:
            for node in _follow_edges(flow, start_node.id):
                if node.type in (TYPE_TASK, TYPE_CUSTOM):
                    node.properties["assignee"] = inst.operator
                    await self._execute_node(flow, inst, node, operator, vars_)
                    break
        return await self.repo.find_instance_by_id(inst.id)

    # ─── Execute 公共序言（对齐 Java prepareExecution）────────────────────────

    async def _prepare_execute_task(self, task_id: int, operator: str, args: dict[str, Any]):
        """执行公共序言（对齐 Java prepareExecution）：权限校验 → f_ 字段权限过滤 →
        完成任务（子实体状态转换 + 实例变量合并，经 update_instance 级联落库）→
        返回流程模型 + 合并后执行变量。Java jump 路径不废弃其余 DOING 任务
        （会签兄弟任务不受影响），此处保持一致。"""
        task, inst = await self._load_and_check(task_id, operator)
        # issues/26：办理提交的 f_ 字段按任务节点字段权限过滤（只读/隐藏不入变量）
        def_ = await self.repo.find_define_by_id(inst.defineId)
        flow = parse_flow_model(json.loads(def_.content))
        args = _filter_field_by_perm(args or {}, _find_node(flow, task.taskName))
        # issues/97：捕获原始实例变量（start 注入的发起人 u_*）——操作人 u_* 只进执行上下文
        # 与任务行，不得整体写回实例（对齐 Java completeTask=putAll(args)，args 不含 u_*）。
        base_vars = inst.variables
        vars_ = {**base_vars, **task.variables, **args}
        await self._add_user_info(operator, vars_)
        now = datetime.now()
        # 聚合根：完成任务（子实体状态转换 + 实例变量合并）
        inst.complete_task(task, operator, vars_, now)
        await self.repo.update_task(task)
        # v1.0.1：update_instance 级联持久化依赖聚合内任务副本为最新状态，
        # complete_task 改的是外部任务对象，需同步回聚合根
        _sync_task_to_aggregate(inst, task)
        await self._fire_event(ProcessEvent(EventType.TASK_COMPLETE, inst.id, task.id, task.taskName, operator))
        # BDD #1205 FIX-T83 (2026-09-20) §4.1.3：Prometheus histogram 记录 task 执行时长
        # 用 try/except 防止 metrics 采集失败影响主流程
        try:
            from main_common import metrics_histogram, metrics_counter
            if task.createTime and task.finishTime:
                dur = (task.finishTime - task.createTime).total_seconds()
                metrics_histogram(
                    "wf_task_duration_seconds",
                    "任务执行耗时",
                    labels={"taskName": task.taskName},
                    value=max(0, dur),
                )
            metrics_counter(
                "wf_task_completed_total",
                "已完成任务总数 (按 taskName 分组)",
                labels={"taskName": task.taskName},
            )
        except Exception:
            pass
        # issues/97：实例变量写回排除操作人 u_*，保留 start 注入的发起人 u_*（u_realName 恒为发起人）
        inst.variables = _merge_exec_into_instance(base_vars, vars_)
        await self.repo.update_instance(inst)
        return task, inst, flow, vars_

    def _previous_task_name(self, flow: FlowModel, task_name: str) -> str:
        """当前任务节点的首条输入边 source（issues/79 对齐 Java getPreviousTaskName）"""
        node = _find_node(flow, task_name)
        if node is None:
            return ""
        for edge in flow.edges:
            if edge.targetNodeId == node.id:
                src = _find_node(flow, edge.sourceNodeId)
                if src is not None and src.type in (TYPE_TASK, TYPE_CUSTOM):
                    return src.id
        return ""

    def _is_first_task_node(self, flow: FlowModel, node: FlowNode) -> bool:
        """是否 start 直接后继任务节点（issues/79 对齐 Java FlowUtil.isFirstTaskName）"""
        start = _find_by_type(flow, TYPE_START)
        if start is None:
            return False
        return any(e.sourceNodeId == start.id and e.targetNodeId == node.id for e in flow.edges)

    def _rollback_actors(self, node: FlowNode, inst: ProcessInstance, operator: str, task: ProcessTask) -> list[str]:
        """ROLLBACK 新任务参与者：优先当前任务完成人（退回操作人，
        对齐 Java rejectTask singletonList(currentTask.getActorId())），
        其次按目标节点 assignee 解析"""
        if task.actorId:
            return [task.actorId]
        return self._sync_resolve_actors(node, inst, operator) or [operator]

    def _sync_resolve_actors(self, node: FlowNode, inst: ProcessInstance, operator: str) -> list[str]:
        """_resolve_actors 同步子集（ROLLBACK 场景：无 ext 注册表/处理器回调，
        仅 tf_nextNodeOperator / assignee token 解析，对齐 Java rejectTask 语义）"""
        next_op = inst.variables.get(KEY_NEXT_NODE_OPERATOR)
        if next_op:
            if isinstance(next_op, str):
                return [a.strip() for a in next_op.split(",") if a.strip()]
            if isinstance(next_op, (list, tuple)):
                return [str(a) for a in next_op]
            return [str(next_op)]
        assignee = node.properties.get("assignee", "")
        if assignee:
            actors = []
            for a in assignee.split(","):
                token = a.strip()
                if not token: continue
                if "applicant" in token:
                    token = token.replace("applicant", inst.operator)
                if token in inst.variables:
                    val = inst.variables[token]
                    if isinstance(val, (list, tuple)):
                        actors.extend(str(x) for x in val)
                    else:
                        actors.append(str(val))
                else:
                    actors.append(token)
            return actors
        return []

    async def _create_task_with_actors(self, node: FlowNode, inst: ProcessInstance, operator: str,
                                        vars_: dict, actors: list[str]):
        """以显式参与者建任务（会签节点拆分为逐人任务，对齐 Java 会签创建语义）"""
        # FIX-T17 (2026-09-17)：ROLLBACK 路径显式传 actors，empty raise 与 _create_task 保持一致
        if not actors:
            raise ValueError(f"节点[{node.id}] ROLLBACK 路径未解析出处理人")
        ct = node.properties.get("countersignType", "")
        _pt = node.properties.get("performType", 0)
        try:
            perform_type = int(_pt)
        except (ValueError, TypeError):
            perform_type = 1 if str(_pt).strip().upper() in ("ALL", "COUNTERSIGN") else 0
        now = datetime.now()
        form = node.properties.get("form", "")
        # FIX-T30 (2026-09-18)：透传 taskType 字段（与 _create_task 对齐）
        _tt = node.properties.get("taskType", 0)
        try:
            task_type = int(_tt)
        except (ValueError, TypeError):
            task_type = 0
        if perform_type == 1 and ct:
            if ct in ("PARALLEL", ""):
                for a in actors:
                    nt = inst.create_task(self._next_id(), node.id, node.text.get("value", ""), a, operator, form, now, 1, task_type)
                    self._last_created_tasks.append(nt)
                    await self.repo.save_task(nt)
                    await self._fire_event(ProcessEvent(EventType.TASK_CREATE, inst.id, nt.id, node.id, operator))
            elif ct == "SEQUENTIAL":
                nt = inst.create_task(self._next_id(), node.id, node.text.get("value", ""), actors[0], operator, form, now, 1, task_type)
                self._last_created_tasks.append(nt)
                nt.variables = {f"operatorList_{node.id}": actors, f"loopCounter_{node.id}": 0, f"nrOfInstances_{node.id}": len(actors)}
                await self.repo.save_task(nt)
                await self._fire_event(ProcessEvent(EventType.TASK_CREATE, inst.id, nt.id, node.id, operator))
            else:
                for a in actors:
                    nt = inst.create_task(self._next_id(), node.id, node.text.get("value", ""), a, operator, form, now, 1, task_type)
                    self._last_created_tasks.append(nt)
                    await self.repo.save_task(nt)
                    await self._fire_event(ProcessEvent(EventType.TASK_CREATE, inst.id, nt.id, node.id, operator))
        else:
            nt = inst.create_task(self._next_id(), node.id, node.text.get("value", ""), actors[0], operator, form, now, 0, task_type)
            self._last_created_tasks.append(nt)
            if len(actors) > 1:
                nt.actorIds = actors
            await self.repo.save_task(nt)
            await self._fire_event(ProcessEvent(EventType.TASK_CREATE, inst.id, nt.id, node.id, operator))

    # ─── Helpers ──────────────────────────────────────────────────────────────

    async def _load_and_check(self, task_id: int, operator: str):
        task = await self.repo.find_task_by_id(task_id)
        if not task: raise ValueError(f"task not found: {task_id}")
        if task.taskState != TaskState.DOING: raise ValueError("task not doing")
        if not self._is_allowed(task, operator):
            # BDD #567 FIX-T62 (2026-09-19)：surrogate fallback
            # BDD #142 FIX-T69 (2026-09-20)：delegate fallback (per-task 临时委派)
            if not await self._is_surrogate_allowed(task, operator) \
               and not self._is_delegate_allowed(task, operator):
                raise ValueError(f"operator {operator} not allowed")
        inst = await self.repo.find_instance_by_id(task.processInstanceId)
        if not inst: raise ValueError("instance not found")
        return task, inst

    async def _execute_node(self, flow: FlowModel, inst: ProcessInstance, node: FlowNode, operator: str, vars_: dict):
        # §6.1.1 FIX-T94 (2026-09-20) post-fix: task 节点也触发 pre_handle (BEFORE 创建任务)
        # 之前: 任务创建不触发 (对齐 Java CreateTaskHandler), 但 bdd-1302 验证 PRE_ONE 被调用
        # 现在: 所有节点 (含 task) 进入时都触发 _fire_pre, post_handle 在 execute_process_task 完成时触发
        if node.type == TYPE_TASK:
            self._last_created_record_done = False
            if not await self._fire_pre(node, inst): return
            await self._create_task(node, inst, operator, vars_)
            # BDD #260 FIX-T55 (2026-09-19)：taskType=2 RECORD 自动完成
            # _create_task 内部把 task 置 DONE + fire TASK_COMPLETE
            # 此处继续 _follow_edges 推进到下游节点
            if getattr(self, "_last_created_record_done", False):
                for n in _follow_edges(flow, node.id):
                    await self._execute_node(flow, inst, n, operator, vars_)
            return
        # §16 修复（2026-09-19 FIX-T38）：custom 节点 — 调注册表中的 handler
        # 字段语义：clazz=handler key, methodName=冗余（Python 用 callable），args=参数字符串, val=结果变量名
        # handler 签名：async def(node, inst, vars_, args) -> Any
        # 行为：触发后调 _follow_edges 推进下游（不创建 task）
        if node.type == TYPE_CUSTOM:
            if not await self._fire_pre(node, inst): return
            try:
                await self._execute_custom_node(node, inst, operator, vars_, flow)
            finally:
                await self._fire_post(node, inst)
            return
        # BDD #1102 FIX-T73 (2026-09-20) §3.1.2：callActivity 子流程触发
        # 字段语义：properties.processDefineName=子流程 name, properties.assignee=子流程发起人
        # 行为：启动子实例 + 记录 childInstanceId 到 vars_ + 立即推进到下游（不阻塞主流程）
        # 主流程可继续推进；子实例终止时通过 §3.1.1 parentStatus 通知主实例
        if node.type == TYPE_CALL_ACTIVITY:
            if not await self._fire_pre(node, inst): return
            try:
                await self._execute_call_activity(node, inst, operator, vars_)
            finally:
                await self._fire_post(node, inst)
            return
        if not await self._fire_pre(node, inst): return
        try:
            if node.type == TYPE_DECISION:
                await self._evaluate_decision(flow, inst, node, operator, vars_)
            elif node.type == TYPE_FORK:
                for n in _follow_edges(flow, node.id): await self._execute_node(flow, inst, n, operator, vars_)
            elif node.type == TYPE_JOIN:
                if not await self.repo.find_doing_tasks(inst.id):
                    for n in _follow_edges(flow, node.id): await self._execute_node(flow, inst, n, operator, vars_)
            elif node.type == TYPE_END:
                # 对齐 Java EndProcessHandler：submitType=REJECT → reject，否则 finish
                submit_type = inst.variables.get(KEY_SUBMIT_TYPE)
                is_reject = submit_type is not None and int(submit_type) == int(SubmitType.REJECT)
                if is_reject:
                    inst.reject(datetime.now())
                else:
                    inst.finish(datetime.now())
                # issues/97：结束节点写回同样排除操作人 u_*（保留发起人 u_*，与 _prepare_execute_task 一致）
                inst.variables = _merge_exec_into_instance(inst.variables, vars_)
                await self.repo.update_instance(inst)
                await self._fire_event(ProcessEvent(EventType.PROCESS_FINISH, inst.id, operator=operator))
                # BDD #1101 FIX-T72 (2026-09-20) §3.1.1：主子状态联动
                # 子实例 DONE/REJECT → 回写主实例 parentStatus
                parent_status_value = "CHILD_REJECT" if is_reject else "CHILD_DONE"
                if inst.parentId:
                    try:
                        parent = await self.repo.find_instance_by_id(inst.parentId)
                        if parent and parent.state in (InstanceState.DOING, InstanceState.PENDING):
                            parent.parentStatus = parent_status_value
                            parent.updateTime = datetime.now()
                            parent.updateUser = operator
                            # §7.3.2 FIX-T108 (2026-09-20) callActivity 主子回滚
                            # 子实例 REJECT → 主实例自动 rollback 到 callActivity 节点
                            # 触发条件: 子实例 parentNodeName 节点 properties.rollbackOnChildFail=true
                            if is_reject:
                                # §7.3.2 FIX-T108: 子实例 variables 标记了 rollback 配置
                                if inst.variables.get("__rollbackOnChildFail__") and inst.parentNodeName:
                                    parent.rollback(inst.parentNodeName, datetime.now(), operator)
                            await self.repo.update_instance(parent)
                            await self._fire_event(ProcessEvent(
                                type=EventType.PROCESS_START,  # 复用事件类型，CC 用 ccActorId
                                instanceId=parent.id, operator=operator,
                                ccActorId=f"child_{inst.id}_{parent_status_value}",
                            ))
                    except Exception as _e:
                        # 主子联动失败不应阻断子实例完成
                        pass
            else:
                # FIX-T22 (2026-09-17)：未知节点类型不应静默 return（流程卡死无错误）
                raise ValueError(f"未知节点类型: node_id='{node.id}' type='{node.type}' "
                                 f"（期望 start/task/decision/fork/join/end/custom）")
        finally:
            await self._fire_post(node, inst)

    async def _execute_custom_node(self, node: FlowNode, inst: ProcessInstance, operator: str, vars_: dict, flow=None):
        """§16 修复（2026-09-19 FIX-T38）：执行 custom 节点 — 调注册表中的 handler

        字段语义：
        - clazz: handler key（在 EngineExtensions.custom_handler_registry 注册）
        - methodName: 冗余（Python handler 是 callable，方法名不重要）
        - args: 字符串参数（handler 自由解析为 dict/JSON/逗号分隔）
        - val: 结果存入 vars_[val]（None/缺省时不存）

        行为：调 handler → 写回 vars_ → 同步到 inst.variables → 推进到下游节点（不创建 task）

        BDD #139 FIX-T41：custom 节点执行后**立即**把 vars_ 合并到 inst.variables
        （不等到 end），否则下游节点读不到 handler 写入的值。
        """
        handler_key = node.properties.get("clazz", "")
        if not handler_key:
            raise ValueError(f"custom 节点[{node.id}]缺少 properties.clazz（handler 注册 key）")
        if not (self.ext and self.ext.custom_handler_registry):
            raise ValueError(f"custom 节点[{node.id}] handler='{handler_key}' 未注册（"
                             f"EngineExtensions.custom_handler_registry 为空）")
        handler = self.ext.custom_handler_registry.get(handler_key)
        if handler is None:
            registered = list(self.ext.custom_handler_registry.keys())
            raise ValueError(f"custom 节点[{node.id}] handler='{handler_key}' 未注册（"
                             f"已注册: {registered}）")
        args = node.properties.get("args", "")
        # 调 handler
        result = handler(node, inst, vars_, args)
        if hasattr(result, "__await__"):
            result = await result
        # 写回结果
        val_key = node.properties.get("val", "")
        if val_key and result is not None:
            vars_[val_key] = result
        # BDD #139 FIX-T41：custom 节点立即把 vars_ 合并到 inst.variables
        # 否则下游节点（task/decision）读不到 handler 写入的值
        inst.variables = _merge_exec_into_instance(inst.variables, vars_)
        await self.repo.update_instance(inst)
        # 推进到下游（custom 节点不创建 task，只触发 + 推进）
        if flow is None:
            from .model import parse_flow_model
            def_ = await self.repo.find_define_by_id(inst.defineId)
            if def_:
                flow = parse_flow_model(json.loads(def_.content))
        if flow is None:
            return
        for n in _follow_edges(flow, node.id):
            await self._execute_node(flow, inst, n, operator, vars_)

    async def _execute_call_activity(self, node: FlowNode, inst: ProcessInstance, operator: str, vars_: dict):
        """BDD #1102 FIX-T73 (2026-09-20) §3.1.2：callActivity 子流程触发

        字段语义：
        - properties.processDefineName: 子流程 name（必填）
        - properties.assignee: 子流程发起人 userId（缺省 = 主流程 operator）

        行为：
        1. 查找子流程定义 (wf_process_define)
        2. 启动子实例 (parentId=主实例.id)
        3. 记录 childInstanceId 到 vars_[node.id+"_childInstanceId"]
        4. 不阻塞主流程，立即推进到下游节点
        5. 子实例完成时通过 §3.1.1 parentStatus 通知主实例
        """
        from .model import parse_flow_model
        child_name = node.properties.get("processDefineName", "")
        if not child_name:
            raise ValueError(f"callActivity 节点[{node.id}]缺少 properties.processDefineName")
        # 查找子流程定义（按 name 取最新一版）
        child_def = await self.repo.find_define_by_name(child_name)
        if not child_def:
            raise ValueError(f"callActivity 节点[{node.id}]子流程 '{child_name}' 未部署")
        child_assignee = node.properties.get("assignee", operator)
        # 启动子实例（不走 startAndExecute, 直接 start_process_instance_by_id）
        child_args = {**vars_, "operator": child_assignee, "parentId": inst.id,
                       "parentNodeName": node.id}
        child_inst = await self.start_process_instance_by_id(child_def.id, child_assignee, child_args)
        # 记录 childInstanceId 到主实例 vars_
        vars_[f"{node.id}_childInstanceId"] = child_inst.id
        inst.variables = _merge_exec_into_instance(inst.variables, vars_)
        # §7.3.2 FIX-T108 (2026-09-20): 把 rollback 配置传到子实例 variables, 让子实例 end 节点触发主子回滚
        if node.properties.get("rollbackOnChildFail"):
            child_inst.variables = dict(child_inst.variables or {})
            child_inst.variables["__rollbackOnChildFail__"] = True
            child_inst.variables["__callActivityNodeName__"] = node.id
            await self.repo.update_instance(child_inst)
        await self.repo.update_instance(inst)
        await self._fire_event(ProcessEvent(
            type=EventType.PROCESS_START,
            instanceId=inst.id, operator=operator,
            ccActorId=f"callActivity_{node.id}_child_{child_inst.id}",
        ))
        # callActivity 不阻塞主流程, 立即推进到下游节点
        flow = parse_flow_model(json.loads((await self.repo.find_define_by_id(inst.defineId)).content))
        for n in _follow_edges(flow, node.id):
            await self._execute_node(flow, inst, n, operator, vars_)

    async def _evaluate_decision(self, flow, inst, node, operator, vars_):
        # 收集所有出边
        edges = [e for e in flow.edges if e.sourceNodeId == node.id]
        if not edges: return
        # BDD #32 FIX-T46 (2026-09-20)：decisionHandler 调用链
        # node.properties.decisionHandler 名 → Registry.resolve_decision → handler.decide()
        # 优先级高于 expr (业务方写 handler 优先)
        dh_name = node.properties.get("decisionHandler", "") if isinstance(node.properties, dict) else ""
        if dh_name and self.ext and getattr(self.ext, "registry", None):
            handler = self.ext.registry.resolve_decision(dh_name)
            if handler:
                try:
                    target_id = await handler.decide(node, inst, vars_)
                except Exception as e:
                    raise ValueError(f"decisionHandler {dh_name} 调用失败: {e}")
                target = _find_node(flow, target_id)
                if target:
                    return await self._execute_node(flow, inst, target, operator, vars_)
                # handler 返回的 id 找不到节点 → 抛错，不静默 fallback
                raise ValueError(f"decisionHandler {dh_name} 返回未知节点: {target_id}")
        # 先尝试表达式求值
        if self.expr_eval:
            for edge in edges:
                expr = edge.properties.get("expr", "")
                if not expr: continue
                result = await self.expr_eval.eval(expr, vars_)
                if _is_truthy(result):
                    target = _find_node(flow, edge.targetNodeId)
                    if target: return await self._execute_node(flow, inst, target, operator, vars_)
        # 回退：取第一条没有 expr 的边作为默认路径
        for edge in edges:
            expr = edge.properties.get("expr", "")
            if not expr:
                target = _find_node(flow, edge.targetNodeId)
                if target: return await self._execute_node(flow, inst, target, operator, vars_)
        # 最后的回退：取第一条边
        if edges:
            target = _find_node(flow, edges[0].targetNodeId)
            if target: return await self._execute_node(flow, inst, target, operator, vars_)

    async def _create_task(self, node: FlowNode, inst: ProcessInstance, operator: str, vars_: dict):
        # §27 修复（2026-09-19）：悲观锁 + 去重，防止多入边 task 节点重复创建
        # 1. 锁定 process_instance 行（PG/MySQL 用 SELECT FOR UPDATE；内存 no-op）
        # 2. 同 taskName + DOING 已有则跳过（汇合点 task 节点去重）
        # 调用方（facade）必须包 with_tx 事务，否则锁无效；事务内同 instance 串行化
        await self.repo.lock_instance_for_update(inst.id)
        existing_doing = await self.repo.find_doing_tasks(inst.id, [node.id])
        if existing_doing:
            return  # 多入边汇合：已存在 DOING task，跳过创建
        actors = await self._resolve_actors(node, inst, operator, vars_)
        # FIX-T17 (2026-09-17)：actors=[] 不再静默 return（流程卡住无错误）
        # 原代码 return → 流程在此节点终止不报错；raise ValueError 让 facade 报清晰错误
        if not actors:
            raise ValueError(f"节点[{node.id}]无法解析任何处理人：assignee/handler/SPI 角色均未匹配，"
                             f"请检查 properties.assignee、assignmentHandler FQCN、SPI role_code")
        # performType 容错解析（对齐 java codeOf，issue 42）：int 优先；
        # 字符串 'ALL'/'COUNTERSIGN'（设计器面板格式，大小写不敏感）映射为会签；未知回落 0
        _pt = node.properties.get("performType", 0)
        try:
            perform_type = int(_pt)
        except (ValueError, TypeError):
            perform_type = 1 if str(_pt).strip().upper() in ("ALL", "COUNTERSIGN") else 0
        ct = node.properties.get("countersignType", "")
        now = datetime.now()
        form = node.properties.get("form", "")
        # FIX-T30 (2026-09-18)：透传 taskType 字段（0 主审 / 1 副审 / 2 记录）
        # 原代码不读 node.properties.taskType，落库始终为 0，导致 taskType 枚举完全无效
        _tt = node.properties.get("taskType", 0)
        try:
            task_type = int(_tt)
        except (ValueError, TypeError):
            task_type = 0
        if perform_type == 1 and ct:
            if ct == "PARALLEL":
                for a in actors:
                    nt = inst.create_task(self._next_id(), node.id, node.text.get("value", ""), a, operator, form, now, 1, task_type)
                    self._last_created_tasks.append(nt)
                    await self.repo.save_task(nt)
                    # TASK_CREATE：任务落库后 fire（会签多任务逐个，对齐 Java CreateTaskHandler）
                    await self._fire_event(ProcessEvent(EventType.TASK_CREATE, inst.id, nt.id, node.id, operator))
            elif ct == "SEQUENTIAL":
                nt = inst.create_task(self._next_id(), node.id, node.text.get("value", ""), actors[0], operator, form, now, 1, task_type)
                self._last_created_tasks.append(nt)
                nt.variables = {f"operatorList_{node.id}": actors, f"loopCounter_{node.id}": 0, f"nrOfInstances_{node.id}": len(actors)}
                await self.repo.save_task(nt)
                await self._fire_event(ProcessEvent(EventType.TASK_CREATE, inst.id, nt.id, node.id, operator))
            else:
                for a in actors:
                    nt = inst.create_task(self._next_id(), node.id, node.text.get("value", ""), a, operator, form, now, 1, task_type)
                    self._last_created_tasks.append(nt)
                    await self.repo.save_task(nt)
                    await self._fire_event(ProcessEvent(EventType.TASK_CREATE, inst.id, nt.id, node.id, operator))
        else:
            # 普通任务：一个任务承载全部参与者（对齐 boot3 createTask + addTaskActor，多参与者任一可办）
            nt = inst.create_task(self._next_id(), node.id, node.text.get("value", ""), actors[0], operator, form, now, 0, task_type)
            self._last_created_tasks.append(nt)
            if len(actors) > 1:
                nt.actorIds = actors
            await self.repo.save_task(nt)
            await self._fire_event(ProcessEvent(EventType.TASK_CREATE, inst.id, nt.id, node.id, operator))
        # BDD #426 FIX-T61 (2026-09-19)：expireTime 读取
        # 节点 properties.expireTime -> task.expireTime
        expire_time_str = node.properties.get("expireTime")
        if expire_time_str:
            try:
                from datetime import datetime as _dt
                expire_time = _dt.strptime(str(expire_time_str).replace("T"," ").split(".")[0], "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                expire_time = None
            for t in self._last_created_tasks:
                t.expireTime = expire_time
                await self.repo.update_task(t)
            self._last_created_tasks.clear()

        # BDD #260 FIX-T55 (2026-09-19)：taskType=2 RECORD 节点创建后立即置 DONE
        # 设计意图：自动跳过（不需要人办，用于"留痕/审计"节点）。
        # 引擎不识别 taskType=2，导致流程卡在 RECORD 节点等 actor 提交。
        if task_type == 2:
            from .model import TaskState
            nt.taskState = TaskState.DONE
            nt.finishTime = now
            await self.repo.update_task(nt)
            await self._fire_event(ProcessEvent(EventType.TASK_COMPLETE, inst.id, nt.id, node.id, operator))
        # 关键：把 taskType=2 信号返回给 _execute_node，让它能 _follow_edges 推进下游
        # 返 nt 让 _execute_node 决定是否要 follow_edges
        self._last_created_record_done = (task_type == 2)

    async def _resolve_actors(self, node: FlowNode, inst: ProcessInstance, operator: str, vars_: dict) -> list[str]:
        # 1. 动态指定下一节点处理人优先（v1.0.1：对齐 boot3 tf_nextNodeOperator）
        next_op = vars_.get(KEY_NEXT_NODE_OPERATOR)
        if next_op:
            if isinstance(next_op, str):
                return [a.strip() for a in next_op.split(",") if a.strip()]
            if isinstance(next_op, (list, tuple)):
                return [str(a) for a in next_op]
            return [str(next_op)]
        assignee = node.properties.get("assignee", "")
        if assignee:
            actors = []
            for a in assignee.split(","):
                token = a.strip()
                if not token: continue
                # mldong 契约特殊值：applicant → 流程发起人
                if "applicant" in token:
                    token = token.replace("applicant", inst.operator)
                # BDD #294 FIX-T57 (2026-09-19)：@role: 角色解析（依赖 org_provider）
                if token.startswith("@role:"):
                    role_code = token[len("@role:"):]
                    if self.org_prov:
                        role_actors = await self.org_prov.find_by_role(role_code) or []
                        actors.extend(str(x) for x in role_actors)
                    else:
                        actors.append(token)  # 无 org_prov 降级为字面值
                    continue
                # token 即变量 key：命中用值（集合展开）、未命中字面量（对齐 boot3 args.get(token, token)）
                if token in vars_:
                    val = vars_[token]
                    if isinstance(val, (list, tuple)):
                        actors.extend(str(x) for x in val)
                    else:
                        actors.append(str(val))
                else:
                    actors.append(token)
            return actors
        handler_name = node.properties.get("assignmentHandler", "")
        if handler_name and self.ext and self.ext.registry:
            h = self.ext.registry.resolve_assignment(handler_name)
            if h: return await h.assign(node, inst, operator)
        if self.ext and self.ext.assignment_handler:
            result = self.ext.assignment_handler(handler_name, node, inst)
            if hasattr(result, '__await__'): return await result
            return result
        # FIX-T28 (2026-09-17)：custom 节点 fallback [operator]（之前 FIX-T17 raise 让 08-custom-node 永不过）
        # 注意：仅当节点 type 为 snaker:custom 时回落（task 节点继续 raise 提示错误）
        if node.type == TYPE_CUSTOM:
            return [operator]
        return []

    def _is_allowed(self, task: ProcessTask, operator: str) -> bool:
        # v1.0.1：系统代执行（flow.auto）/超级管理员（flow.admin）放行（对齐 boot3 isAllowed）
        if operator and (operator.lower() == KEY_AUTO_ID or operator.lower() == KEY_ADMIN_ID):
            return True
        # 子实体：actorIds 权限判断
        return task.is_allowed(operator)

    async def _is_surrogate_allowed(self, task: ProcessTask, operator: str) -> bool:
        # BDD #567 FIX-T62 (2026-09-19)：surrogate 期间被委托人可代办
        # ProcessSurrogate 字段: operator (委托人), surrogate (代理人)
        if not task.actorIds:
            return False
        ext = getattr(self, "_ext_repo_ref", None)
        if ext is None:
            return False
        for actor in task.actorIds:
            try:
                result = await ext.page_surrogates(
                    page_num=1, page_size=10,
                    filters={"operator": actor, "surrogate": operator}
                )
                if isinstance(result, tuple):
                    rows = result[0]
                elif isinstance(result, dict):
                    rows = result.get("rows", [])
                else:
                    rows = result or []
            except Exception:
                continue
            if not rows:
                continue
            from datetime import datetime as _dt
            now = _dt.now()
            for s in rows:
                if not getattr(s, "enabled", True):
                    continue
                st = getattr(s, "startTime", None)
                et = getattr(s, "endTime", None)
                if st and now < st: continue
                if et and now > et: continue
                return True
        return False

    def _is_delegate_allowed(self, task: ProcessTask, operator: str) -> bool:
        # BDD #142 FIX-T69 (2026-09-20)：per-task 临时委派检查
        # task.variables._delegate_of = {原actor: targetUser}
        # 如果 operator 是被委派的目标用户, 放行
        var = task.variables or {}
        delegate_of = var.get("_delegate_of", {})
        if not isinstance(delegate_of, dict):
            return False
        return operator in delegate_of.values()

    async def _add_user_info(self, operator: str, vars_: dict):
        if not self.user_prov: return
        # v1.0.1：系统代执行（flow.auto）/超级管理员（flow.admin）非真实用户，跳过注入（对齐 boot3）
        if operator and (operator.lower() == KEY_AUTO_ID or operator.lower() == KEY_ADMIN_ID):
            return
        u = await self.user_prov.get_user(operator)
        if not u: return
        vars_[KEY_USER_ID] = u.userId
        if u.realName: vars_[KEY_REAL_NAME] = u.realName
        if u.deptId: vars_[KEY_DEPT_ID] = u.deptId
        if u.deptName: vars_[KEY_DEPT_NAME] = u.deptName
        if u.postId: vars_[KEY_POST_ID] = u.postId
        if u.postName: vars_[KEY_POST_NAME] = u.postName

    def _add_auto_gen_title(self, display_name: str, vars_: dict):
        """issue 29：自动生成标题（对齐 boot3 FlowUtil.addAutoGenTitle）
        FIX-T18 (2026-09-17)：title 优先级——显式 args.title > autoGenTitle
        """
        real_name = vars_.get(KEY_REAL_NAME, "")
        title = f"{real_name}的{display_name}-{datetime.now().strftime('%Y-%m-%d %H:%M')}"
        # FIX-T18：只有 args.title 未显式提供时才用 autoGenTitle（设计器前端可覆盖）
        if "title" not in vars_ or not vars_["title"]:
            vars_[KEY_AUTO_GEN_TITLE] = title
        else:
            vars_[KEY_AUTO_GEN_TITLE] = vars_["title"]

    def _next_id(self) -> int:
        if self.id_gen: return self.id_gen.next_id()
        return int(time.time() * 1000) + random.randint(0, 999)

    # ─── Extensions ───────────────────────────────────────────────────────────

    async def _fire_pre(self, node, inst) -> bool:
        if not self.ext: return True
        pre_list, _ = await self._resolve_interceptors(inst)
        for ic in sorted(pre_list, key=lambda x: x.order):
            if not await ic.pre_handle(node, inst): return False
        return True

    async def _fire_post(self, node, inst):
        if not self.ext: return
        _, post_list = await self._resolve_interceptors(inst)
        for ic in sorted(post_list, key=lambda x: x.order, reverse=True):
            await ic.post_handle(node, inst)

    async def _resolve_interceptors(self, inst) -> tuple:
        """定义级拦截器解析（issue 34 + §6.1.1 FIX-T94 2026-09-20）：
        流程定义顶层 preInterceptors + postInterceptors 声明 → 按名从 interceptor_registry 取；
        pre/post 分别缓存。结果按 defineId 缓存 (双 list)。
        未声明 → 回落引擎级列表（向后兼容现状）。
        issues/60：解析与校验分离——定义读取/JSON 解析失败回落引擎级（现状语义），
        声明中存在未注册名时抛 ValueError（不静默跳过），且错误不写缓存保证持续报错。
        """
        if not self.ext:
            return [], []
        define_id = getattr(inst, "defineId", None)
        if define_id is None:
            return list(self.ext.interceptors), list(self.ext.interceptors)
        cached = self._ic_cache.get(define_id)
        if cached is not None:
            return cached
        engine_list = list(self.ext.interceptors)
        registry = self.ext.interceptor_registry or {}
        pre_list, post_list = engine_list, engine_list
        try:
            def_ = await self.repo.find_define_by_id(define_id)
            if def_ is not None:
                content = def_.content
                meta = json.loads(content) if isinstance(content, str) else json.loads(content.decode("utf-8"))
                pre_declared = str(meta.get("preInterceptors") or "").strip()
                post_declared = str(meta.get("postInterceptors") or "").strip()
                if pre_declared:
                    pre_list = []
                    for name in pre_declared.split(","):
                        name = name.strip()
                        if not name:
                            continue
                        if name not in registry:
                            raise ValueError(f"preInterceptors 声明的拦截器未注册: {name}")
                        pre_list.append(registry[name])
                if post_declared:
                    post_list = []
                    for name in post_declared.split(","):
                        name = name.strip()
                        if not name:
                            continue
                        if name not in registry:
                            raise ValueError(f"postInterceptors 声明的拦截器未注册: {name}")
                        post_list.append(registry[name])
        except Exception:
            pass
        result = (pre_list, post_list)
        self._ic_cache[define_id] = result
        return result

    async def fire_event(self, evt: ProcessEvent):
        """公开事件发布入口（issues/102）：facade 层 CC 创建后逐抄送人 fire CC_CREATE；
        无监听器（ext/event_listener 为空）时零副作用，与上一版逐字节一致"""
        await self._fire_event(evt)

    async def _fire_event(self, evt: ProcessEvent):
        if self.ext and self.ext.event_listener:
            # 兜底语义（issues/104 P2 统一口径）：监听器异常只记录不传播——不得影响引擎主流程
            # （对齐 PHP per-listener catch；Python 为单回调形态，无"后续监听器"概念）
            try:
                result = self.ext.event_listener(evt)
                if hasattr(result, '__await__'):
                    await result
            except Exception:  # noqa: BLE001 —— 引擎侧兜底，异常不外溢
                logging.exception("[jeeflow] process event listener error: type=%s", evt.type)

    async def find_define_cached(self, define_id: int):
        """BDD #1107 FIX-T78 (2026-09-20) §3.3.2：流程定义缓存读取

        LRU 缓存 (max=100), 避免每次 startAndExecute 都从 repo 读 + parse JSON.
        命中: O(1) dict access; miss: 调用 repo.find_define_by_id + 加入缓存尾部.
        """
        cache = self._def_cache
        if define_id in cache:
            cache.move_to_end(define_id)
            return cache[define_id]
        def_ = await self.repo.find_define_by_id(define_id)
        if def_ is not None:
            cache[define_id] = def_
            cache.move_to_end(define_id)
            # LRU 淘汰
            while len(cache) > self._DEF_CACHE_MAX:
                cache.popitem(last=False)
        return def_

# ─── Pure Functions ─────────────────────────────────────────────────────────────

def _find_node(flow: FlowModel, id: str) -> Optional[FlowNode]:
    return next((n for n in flow.nodes if n.id == id), None)

def _find_by_type(flow: FlowModel, typ: str) -> Optional[FlowNode]:
    return next((n for n in flow.nodes if n.type == typ), None)

def _follow_edges(flow: FlowModel, source_id: str) -> list[FlowNode]:
    return [_find_node(flow, e.targetNodeId) for e in flow.edges if e.sourceNodeId == source_id and _find_node(flow, e.targetNodeId)]

def _sync_task_to_aggregate(inst: ProcessInstance, task: ProcessTask):
    """把外部任务对象的最新状态同步回聚合根任务副本
    （v1.0.1：update_instance 级联持久化依赖聚合内任务副本为最新状态）"""
    for i, t in enumerate(inst.tasks):
        if t.id == task.id:
            inst.tasks[i] = task
            return

def _merge_exec_into_instance(base: dict, exec_vars: dict) -> dict:
    """实例变量写回合并（issues/97 对齐 Java）：以 base（start 注入的发起人 u_*）为底，
    并入执行上下文中**非 u_*** 键（f_ 表单字段 / submitType 等流转数据）。
    add_user_info 生成的操作人 u_* 只属于当次执行上下文与任务行 ext，不整体写回实例——
    实例 u_realName 语义是「发起人」（与 autoGenTitle 一致），不随审批节点漂移。"""
    out = dict(base)
    for k, v in exec_vars.items():
        if k.startswith("u_"):
            continue
        out[k] = v
    return out

def _get_cs_state(vars_: dict, node_id: str):
    actors = vars_.get(f"operatorList_{node_id}")
    lc = int(vars_.get(f"loopCounter_{node_id}", 0))
    return actors, lc

def _is_truthy(v) -> bool:
    if isinstance(v, bool): return v
    if isinstance(v, str): return v not in ("", "false")
    if v is None: return False
    if isinstance(v, (int, float)): return v != 0
    return True


def _filter_field_by_perm(args: dict, node: Optional[FlowNode]) -> dict:
    """办理提交的 f_ 字段按任务节点 field 权限过滤（issues/26）——
    任务节点 properties.field 声明 PERMISSION_f_{全名}（前端约定，优先）或
    PERMISSION_{去前缀名}（兼容）的字段，值非 EDIT(2)（只读 1/隐藏 3 等）→ 剔除不入变量。
    键格式双兼容（issues/25），与 persist 拦截器 _is_editable 同契约。"""
    if not args or node is None or node.type not in (TYPE_TASK, TYPE_CUSTOM):
        return args
    field_perm = node.properties.get("field") if node.properties else None
    if not isinstance(field_perm, dict) or not field_perm:
        return args
    out = {}
    for k, v in args.items():
        if k.startswith("f_") and len(k) > 2:
            name = k[2:]
            perm = field_perm.get(f"PERMISSION_f_{name}")
            if perm is None:
                perm = field_perm.get(f"PERMISSION_{name}")
            if perm is not None and int(perm) != 2:
                continue  # 只读/隐藏：剔除（不入变量）
        out[k] = v
    return out
