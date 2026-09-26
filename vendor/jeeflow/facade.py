"""统一门面（v1.1.0）——"接口即 POST + JSON body"风格的单入口

集成方只实现一个转发端点：把 body JSON 转成 dict 传入 flow()，
所有流程能力按 action（boot2/boot3 端点短名）路由。返回统一结构
{code, msg, data}（code=0 成功 / 99999999 失败）。

操作人约定：门面不感知登录态，args["operator"] 显式传入。
"""
from __future__ import annotations

import dataclasses
import inspect
import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Optional

from .engine import Engine, KEY_NEXT_NODE_OPERATOR, KEY_PROCESS_START_NEXT_NODE_OPERATOR
from .extensions import EventType, ProcessEvent
from .model import ProcessDefine, ProcessDesign, ProcessDesignHis, ProcessSurrogate, TaskState, InstanceState
from .spi import ProcessExtRepository, ProcessRepository, QueryCondition
from .verify import verify_flow, format_issues, VerifyIssue

# submitType 枚举（对齐 boot3）
SUBMIT_APPLY = 0
SUBMIT_AGREE = 1
SUBMIT_REJECT = 2
SUBMIT_ROLLBACK = 3
SUBMIT_JUMP = 4
SUBMIT_ROLLBACK_TO_OPERATOR = 6
SUBMIT_COUNTERSIGN_DISAGREE = 20


class JeeflowFacade:
    """统一门面——flow(action, args) -> dict"""

    def __init__(self, engine: Engine, repo: ProcessRepository,
                 ext_repo: Optional[ProcessExtRepository] = None,
                 user_search: Optional[callable] = None,
                 org_prov: Optional["OrgUserProvider"] = None):
        self._engine = engine
        self._repo = repo
        self._ext = ext_repo
        self._user_search = user_search  # 可空：candidatePage 用户分页搜索依赖
        self._org_prov = org_prov  # 可空：candidatePage candidateGroups 角色取人（v1.6.0）
        self._meta_reader = None  # 可空：bizData 业务数据读取器（issue 30，注入式）

    def set_meta_reader(self, reader) -> "JeeflowFacade":
        """注入业务数据读取器（issue 30）：需有 read_by_process_instance(table_name, process_instance_id)"""
        self._meta_reader = reader
        return self

    def set_user_search(self, fn: callable) -> "JeeflowFacade":
        """注入用户搜索钩子：fn(query: dict) -> (rows: list[dict], total: int)"""
        self._user_search = fn
        return self

    def set_org_provider(self, org_prov: "OrgUserProvider") -> "JeeflowFacade":
        """注入组织用户提供者（candidatePage candidateGroups 角色取人）"""
        self._org_prov = org_prov
        return self

    async def flow(self, action: str, args: Optional[dict] = None) -> dict:
        args = args or {}
        # BDD #1206 FIX-T84 (2026-09-20) §4.1.4：trace_span 包裹每个 facade 方法
        try:
            from main_common import trace_span
            with_trace = True
        except ImportError:
            with_trace = False
        if with_trace:
            return await self._flow_with_trace(action, args)
        # fallback (单元测试时没有 main_common)
        try:
            handler = getattr(self, "_" + action.replace("/", "_"), None)
            if handler is None:
                return self._error(f"未知 action: {action}")
            data = await handler(args)
            return self._ok(_stringify_ids(data))
        except Exception as e:
            msg = str(e) if str(e) else type(e).__name__
            return self._error(f"[{type(e).__name__}] {msg}")

    async def _flow_with_trace(self, action: str, args: dict) -> dict:
        """BDD #1206 FIX-T84 §4.1.4：trace_span 包裹"""
        from main_common import trace_span
        args = args or {}
        async with trace_span(f"facade.{action}") as span:
            span["attributes"]["args_keys"] = ",".join(args.keys()) if isinstance(args, dict) else ""
            try:
                handler = getattr(self, "_" + action.replace("/", "_"), None)
                if handler is None:
                    span["attributes"]["error"] = "unknown_action"
                    return self._error(f"未知 action: {action}")
                data = await handler(args)
                # issues/38 E9 出口统一：id 类字段转 string（对齐 Node 全程 string / Java 全局
                # ToStringSerializer）——前端 JS number 无法承载雪花 id（>2^53）
                result = self._ok(_stringify_ids(data))
                span["attributes"]["code"] = result.get("code", -1)
                return result
            except Exception as e:
                # FIX-T19 (2026-09-17)：错误信息附异常类型，便于调试区分 ValueError/RuntimeError
                msg = str(e) if str(e) else type(e).__name__
                span["attributes"]["error"] = msg[:200]
                return self._error(f"[{type(e).__name__}] {msg}")

    async def _verify(self, args: dict) -> dict:
        """BDD #251 (2026-09-19)：流程 verify 预检接口

        请求: { "content": "<json string>", "variables": {...} (可选) }
        响应: { "valid": bool, "errors": [...], "warnings": [...], "patterns": [...] }

        不会写入设计, 仅预检
        """
        content = self._content(args)
        try:
            flow = json.loads(content)
        except Exception as e:
            raise ValueError(f"content JSON 解析失败: {e}")
        variables = args.get("variables") or {}
        errors, warnings, patterns = verify_flow(flow, variables)
        return {
            "valid": len(errors) == 0,
            "errors": [i.to_dict() for i in errors],
            "warnings": [i.to_dict() for i in warnings],
            "patterns": [i.to_dict() for i in patterns],
            "summary": {
                "errorCount": len(errors),
                "warningCount": len(warnings),
                "patternCount": len(patterns),
            },
        }

    # ── 流程定义 / 实例 ─────────────────────────────────────────────────────

    async def _processDefine_page(self, args: dict) -> dict:
        """流程定义分页（v1.5.0 补齐）"""
        page_num = self._to_int(args.get("pageNum") or args.get("pageNo")) or 1
        page_size = self._to_int(args.get("pageSize")) or 10
        rows, total = await self._repo.page_defines(page_num, page_size, self._parse_m_query(args))
        return self._page_data([self._define_row_to_dict(r) for r in rows], total, page_num, page_size)

    async def _processDefine_detail(self, args: dict) -> dict:
        """流程定义详情（v1.5.0 补齐）"""
        define_id = self._to_int(args.get("id"))
        if not define_id:
            raise ValueError("id 缺失或非法")
        def_ = await self._repo.find_define_by_id(define_id)
        if not def_:
            raise ValueError("流程定义不存在")
        return {"id": def_.id, "name": def_.name, "displayName": def_.displayName,
                "type": def_.type, "state": def_.state, "version": def_.version,
                "jsonObject": self._parse_graph(def_.content)}

    async def _processDefine_startAndExecute(self, args: dict) -> dict:
        return await self._startAndExecute(args)

    async def _processInstance_page(self, args: dict) -> dict:
        """我发起的流程实例分页（operator 过滤，v1.5.0 补齐）"""
        page_num = self._to_int(args.get("pageNum") or args.get("pageNo")) or 1
        page_size = self._to_int(args.get("pageSize")) or 10
        operator = str(args.get("operator", "user1"))
        rows, total = await self._repo.page_instances(page_num, page_size, operator, self._parse_m_query(args))
        return self._page_data([self._instance_row_to_dict(r) for r in rows], total, page_num, page_size)

    async def _processInstance_export(self, args: dict) -> dict:
        """§6.2.1 FIX-T97 (2026-09-20): 流程实例导出 (CSV/JSON).

        支持参数:
          operator: 发起人过滤 (默认空=全部, 业务方可指定看自己范围)
          format: csv | json (默认 csv)
          limit: 单次最多导出 (默认 1000, 上限 5000)
          conditions: 通过 _parse_m_query 支持 (state, businessNo 等)
        返回:
          {format, count, data (CSV 字符串 or JSON list 字符串)}
        """
        operator = str(args.get("operator", "")) or None
        fmt = str(args.get("format", "csv")).lower()
        if fmt not in ("csv", "json"):
            raise ValueError(f"format 必须是 csv 或 json, 当前={fmt}")
        limit = min(self._to_int(args.get("limit")) or 1000, 5000)
        # 用 page_instances 一次取 limit 条 (pageSize = limit)
        rows, _ = await self._repo.page_instances(1, limit, operator, self._parse_m_query(args))
        dicts = [self._instance_row_to_dict(r) for r in rows]
        if fmt == "json":
            import json as _json
            data_str = _json.dumps(dicts, ensure_ascii=False, default=str)
        else:
            # CSV
            if dicts:
                import csv as _csv
                import io
                buf = io.StringIO()
                writer = _csv.DictWriter(buf, fieldnames=list(dicts[0].keys()))
                writer.writeheader()
                for d in dicts:
                    writer.writerow({k: _csv_safe(v) for k, v in d.items()})
                data_str = buf.getvalue()
            else:
                data_str = ""
        return {"format": fmt, "count": len(dicts), "data": data_str}

    async def _processInstance_detail(self, args: dict) -> dict:
        """流程实例详情（含任务列表，v1.5.0 补齐）"""
        instance_id = self._to_int(args.get("id"))
        if not instance_id:
            raise ValueError("id 缺失或非法")
        inst = await self._repo.find_instance_by_id(instance_id)
        if not inst:
            raise ValueError("流程实例不存在")
        graph = await self._instance_json_object(inst)
        first_task_id = self._first_task_node_id(graph)
        tasks, active_task_list = [], []
        for t in inst.tasks:
            vo = self._task_vo(t)
            ext = dict(t.variables or {})
            doing = t.taskState == TaskState.DOING
            ext["isFirstTaskNode"] = doing and t.taskName == first_task_id
            vo["ext"] = ext
            tasks.append(vo)
            if doing:
                active_task_list.append(vo)
        data = {
            "id": inst.id, "parentId": inst.parentId, "processDefineId": inst.defineId,
            "state": inst.state, "parentNodeName": inst.parentNodeName,
            "businessNo": inst.businessNo, "operator": inst.operator,
            "ownerId": getattr(inst, "ownerId", "") or "",  # FIX-T9 (2026-09-17) §66
            "parentStatus": getattr(inst, "parentStatus", None),  # FIX-T72 (2026-09-20) §3.1.1
            "variables": inst.variables,
            "formData": self._form_data_of(inst.variables, "f_"),  # issues/15
            "createTime": inst.createTime, "createUser": inst.createUser,
            "jsonObject": graph,
            "tasks": tasks,
            "activeTaskList": active_task_list,
        }
        defn = await self._repo.find_define_by_id(inst.defineId)
        if defn:
            data["displayName"] = defn.displayName  # issues/15
            data["name"] = defn.name
            data["version"] = defn.version
        return data

    async def _processInstance_startAndExecute(self, args: dict) -> dict:
        return await self._startAndExecute(args)

    async def _startAndExecute(self, args: dict) -> dict:
        define_id = self._to_int(args.get("processDefineId"))
        if not define_id:
            raise ValueError("processDefineId 缺失或非法")

        # BDD #1070 FIX-T93 + §6.1.1 FIX-T94 (2026-09-20) §36 + §34 interceptor 校验
        # 在发起时校验 preInterceptors + postInterceptors, 避免拦截器未注册时 startProcess 通过、运行期才报错
        try:
            def_ = await self._repo.find_define_by_id(define_id)
            if def_ is not None:
                flow_meta = json.loads(def_.content) if isinstance(def_.content, str) else json.loads(def_.content.decode("utf-8"))
                engine_ext = getattr(self._engine, "ext", None)
                registry = getattr(engine_ext, "interceptor_registry", None) or {}
                for field_name in ("preInterceptors", "postInterceptors"):
                    declared = str(flow_meta.get(field_name) or "").strip()
                    if declared:
                        unknown = [n.strip() for n in declared.split(",") if n.strip() and n.strip() not in registry]
                        if unknown:
                            raise ValueError(
                                f"{field_name} 声明的拦截器未注册: {','.join(unknown)}"
                            )
        except ValueError:
            raise
        except Exception:
            pass
        operator = str(args.get("operator", "user1"))
        # FIX-T10 (2026-09-17)：business variables 嵌套解包（§Issue D 上游修复）
        # 兼容调用方传 {variables: {amount: 5000}}（设计器前端规范），
        # 把 nested variables 展开到 args 顶层；顶层已有 key 不覆盖（优先级：顶层 > nested）
        nested = args.get("variables")
        if isinstance(nested, dict):
            for k, val in nested.items():
                args.setdefault(k, val)
        flow_args = {k: v for k, v in args.items() if k not in ("processDefineId", "operator")}
        # §27 修复（2026-09-19）：包 with_tx 事务，保证 lock_instance_for_update 在事务内有效
        # 同 instance 后续 _create_task 串行化，防止多入边 task 节点重复创建
        inst = await self._repo.with_tx(
            lambda: self._engine.start_process_instance_by_id(define_id, operator, flow_args)
        )
        # FIX-T9 (2026-09-17)：ProcessInstance.ownerId 提取（§66 修复，兜底双轨制）
        # engine 已经在 start_process_instance_by_id 内提取；此处兜底（防御 facade 跳过 engine）
        if not getattr(inst, "ownerId", ""):
            inst.ownerId = (
                str(args.get("ownerId", "") or "").strip()
                or str(flow_args.get("u_userId", "") or "").strip()
                or operator
            )
        # issues/56 E28：发起时抄送（f_ccActors）创建 cc 实例（对齐 Java enableCcActors 语义）
        cc = flow_args.get("f_ccActors")
        if cc is not None:
            if isinstance(cc, str):
                cc_list = [x.strip() for x in cc.split(",") if x.strip()]
            elif isinstance(cc, (list, tuple)):
                cc_list = [str(x) for x in cc]
            else:
                cc_list = []
            if cc_list:
                await self._repo.create_cc_instance(inst.id, operator, *cc_list)
                # issues/102：CC 实例落库后逐抄送人 fire CC_CREATE（ccActorId 直传事件体，
                # 在 start 事务内；监听器据此落抄送知会 NOTICE）
                for actor in cc_list:
                    await self._engine.fire_event(
                        ProcessEvent(type=EventType.CC_CREATE, instanceId=inst.id, ccActorId=actor))
        # startAndExecute：自动完成申请节点（assignee="applicant" → 发起人）
        doing = await self._repo.find_doing_tasks(inst.id)
        for task in doing:
            await self._repo.add_task_actor(task.id, [operator])
            flow_args["submitType"] = SUBMIT_APPLY
            # 对齐 boot3：f_nextNodeOperator（发起时预指派人）→ tf_nextNodeOperator（引擎执行参数）
            start_next_op = flow_args.get(KEY_PROCESS_START_NEXT_NODE_OPERATOR)
            if start_next_op:
                flow_args[KEY_NEXT_NODE_OPERATOR] = start_next_op
            try:
                await self._engine.execute_process_task(task.id, operator, flow_args)
            except Exception as e:
                # FIX-T17 (2026-09-17)：下游 task 创建失败时清理半成品实例
                # 原代码 exception 吞掉，instance 留在 state=10 DOING 但 active=[]
                # 现在让上层看到明确错误；实例标记 ABANDON 便于排查
                # BDD #144 FIX-T44 (2026-09-19)：同步废弃所有 DOING 任务
                # 否则 instance.state=99 但 task.state=10 → 孤立 todo 待办
                from .model import InstanceState, TaskState
                inst.state = InstanceState.ABANDON
                inst.updateTime = datetime.now()
                for t in inst.tasks:
                    if t.taskState == TaskState.DOING:
                        t.taskState = TaskState.ABANDONED
                        t.updateTime = datetime.now()
                        t.updateUser = operator
                try:
                    await self._repo.update_instance(inst)
                    for t in inst.tasks:
                        if t.taskState == TaskState.ABANDONED:
                            try:
                                await self._repo.update_task(t)
                            except Exception:
                                pass
                except Exception:
                    pass
                raise
        return {"processInstanceId": inst.id}

    async def _processDefine_deploy(self, args: dict) -> dict:
        return await self._deploy(args)

    async def _processDesign_deploy(self, args: dict) -> dict:
        ext = self._ext_repo()
        design_id = self._to_int(args.get("id"))
        design = await ext.find_design_by_id(design_id)
        if not design:
            raise ValueError("流程设计不存在")
        his_list = await ext.list_design_his(design_id)
        if not his_list:
            raise ValueError("流程设计没有内容，无法发布")
        # BDD #251: 透传 skipVerify 给 _deploy
        define_id = await self._deploy({
            "content": his_list[0].content,
            "operator": args.get("operator", "system"),
            "skipVerify": bool(args.get("skipVerify")),
        })
        design.isDeployed = True
        design.updateUser = str(args.get("operator", "system"))
        await ext.update_design(design)
        return define_id

    def _verify_or_raise(self, content: str, args: dict, variables: dict = None):
        """流程定义 verify 入口（2026-09-19 规则库）

        - 解析 content 为 flow dict
        - 跑 verify_flow 得到 errors / warnings / patterns
        - 错误：raise ValueError（阻塞 save/deploy）
        - 警告/反模式：写入 design.remark（不阻塞, 但可见）
        - 跳过：args.skipVerify=True 时仅打 info 日志, 不 raise
        """
        skip = bool(args.get("skipVerify"))
        try:
            flow = json.loads(content)
        except Exception:
            return  # 内容不合法由 deploy 后续的 JSON 解析承担

        errors, warnings, patterns = verify_flow(flow, variables)

        if errors:
            if skip:
                import logging
                logging.warning(f"[verify SKIP] {len(errors)} errors ignored: {format_issues(errors)}")
            else:
                msg = f"流程 verify 失败 ({len(errors)} 个错误):\n{format_issues(errors)}"
                if warnings:
                    msg += f"\n额外警告 ({len(warnings)} 个):\n{format_issues(warnings)}"
                if patterns:
                     msg += f"\n反模式建议 ({len(patterns)} 个):\n{format_issues(patterns)}"
                raise ValueError(msg)

        # 警告/反模式：可继续, 但记录到 remark 提示
        if (warnings or patterns) and not skip:
            import logging
            logging.info(f"[verify] {len(warnings)} warnings, {len(patterns)} patterns: {format_issues(warnings + patterns)}")

    async def _deploy(self, args: dict) -> dict:
        """deploy 版本管理（对齐 boot3）：按 name 查最新定义，存在 version+1 插新记录，否则从 0 起"""
        content = self._content(args)
        # BDD #251 (2026-09-19)：deploy 也跑 verify（兜底二次校验）
        # 即使 processDesign/save 已校验过, deploy 入口仍要校验
        # 防止 processDesign/save 被 skipVerify=true 跳过而直接 deploy
        self._verify_or_raise(content, args)
        flow = json.loads(content)
        name = flow.get("name", "")
        if not name:
            raise ValueError("流程定义缺少 name")
        # 注：旧的 id 唯一 / 命名规范 / 环 校验已迁移到 verify_flow
        # (_verify_or_raise 内部) ——保留 verify 模块统一管理
        version = 0
        latest = await self._repo.find_define_by_name(name)
        if latest:
            version = (latest.version or 0) + 1
        operator = str(args.get("operator", "system"))
        def_ = ProcessDefine(name=name, displayName=flow.get("displayName", ""),
                             type=flow.get("type", "approval"), state=1,
                             content=content, version=version,
                             createUser=operator, updateUser=operator)
        await self._repo.save_define(def_)
        # BDD #1107 FIX-T78 §3.3.2：deploy 时失效所有缓存（name 变了,旧 defineId 可能复用）
        if hasattr(self._engine, "invalidate_define_cache"):
            self._engine.invalidate_define_cache()
        return {"processDefineId": def_.id}

    async def _processDefine_redeploy(self, args: dict) -> dict:
        define_id = self._to_int(args.get("processDefineId"))
        if not define_id:
            raise ValueError("processDefineId 缺失或非法")
        content = self._content(args)
        flow = json.loads(content)
        def_ = ProcessDefine(id=define_id, name=flow.get("name", ""),
                             displayName=flow.get("displayName", ""),
                             type=flow.get("type", "approval"),
                             content=content,
                             updateUser=str(args.get("operator", "system")))
        await self._repo.update_define(def_)
        return None

    async def _processDefine_remove(self, args: dict) -> dict:
        # issues/95：前端删除统一发 {ids}（此前 Python 唯一没做批量兼容的语言）
        for define_id in self._id_list(args):
            await self._repo.remove_define(define_id)
        return None

    async def _processDefine_upAndDown(self, args: dict) -> dict:
        # issues/54 E26：兼容 {ids, opType} 批量与 {id, state} 单条（对齐 Java issues/28）
        state = self._to_int(args.get("opType") if args.get("opType") is not None else args.get("state"))
        if state is None:
            raise ValueError("opType/state 缺失或非法")
        for define_id in self._id_list(args):
            await self._repo.update_define_state(define_id, state)
        return None

    async def _processInstance_rollback(self, args: dict) -> dict:
        """§7.3.1 FIX-T107 (2026-09-20): 回滚流程到指定节点 (state=WITHDRAW, 废弃 DOING 任务)

        参数:
          id: 实例 ID (必填)
          toNodeName: 回滚目标节点名 (必填, 用于记录; 实际跳回由调用方决定)
          operator: 操作人 (可选, 默认 system)
        行为:
          1. 校验实例存在且状态 DOING/PENDING
          2. 废弃所有 DOING 任务
          3. instance.state = WITHDRAW
          4. variables[__rollback__] = {to_node_name, rollback_time, operator}
        返回: {state, rollback: {to_node_name, rollback_time, operator}}
        API 兼容性: 新增 endpoint (走 /wf/{action:path} 路由)
        """
        instance_id = self._to_int(args.get("id"))
        if not instance_id:
            raise ValueError("id 缺失或非法")
        to_node = str(args.get("toNodeName", "")).strip()
        if not to_node:
            raise ValueError("toNodeName 缺失")
        operator = str(args.get("operator", "system"))
        inst = await self._repo.find_instance_by_id(instance_id)
        if not inst:
            raise ValueError(f"流程实例不存在: {instance_id}")
        if inst.state not in (InstanceState.DOING, InstanceState.PENDING):
            raise ValueError(f"实例 state={inst.state} 不可回滚（仅 DOING=10/PENDING=50 可回滚）")
        from datetime import datetime as _dt
        inst.rollback(to_node, _dt.now(), operator)
        await self._repo.update_instance(inst)
        return {
            "state": inst.state,
            "rollback": {
                "toNodeName": to_node,
                "rollbackTime": str(inst.updateTime),
                "operator": operator,
            }
        }

    async def _processInstance_doingList(self, args: dict) -> dict:
        """§7.3.3 FIX-T109 (2026-09-20): 断点续跑 - 扫描 DOING 状态实例

        用法: 启动 hook 调用, 输出当前 DOING 实例统计 + 列表
        参数:
          limit: 返回数量上限 (默认 100)
          defineId: 可选, 只查某 define 的 DOING 实例
        返回:
          {
            instance_count: int,  # DOING 实例数
            task_count: int,      # 关联 DOING 任务数
            by_node: {node_name: count},  # 按当前节点统计
            instances: [{id, defineId, createTime, updateTime, businessNo, doing_tasks: [...]}, ...]
          }
        用途:
          1. 启动 hook: 检测 server 重启前留下的 DOING 实例, 输出日志
          2. 运维: 列出当前所有 DOING 实例, 检查未完成任务
        """
        from .model import InstanceState, TaskState
        limit = int(args.get("limit") or 100)
        define_id = args.get("defineId")
        try:
            define_id = int(define_id) if define_id else None
        except Exception:
            define_id = None
        result = {
            "instance_count": 0,
            "task_count": 0,
            "by_node": {},
            "instances": [],
        }
        # 拿所有 DOING instance
        if hasattr(self._repo, "list_instances_by_state"):
            instances = await self._repo.list_instances_by_state(InstanceState.DOING, limit=limit)
        else:
            # 退化: 全量扫
            instances = []
            for i in range(1, int(getattr(self._repo, "_seq", 0) or 0) + 1):
                inst = await self._repo.find_instance_by_id(i)
                if inst and inst.state == InstanceState.DOING:
                    if define_id is None or inst.defineId == define_id:
                        instances.append(inst)
                if len(instances) >= limit:
                    break
        # 按 defineId 过滤
        if define_id is not None:
            instances = [i for i in instances if i.defineId == define_id]
        result["instance_count"] = len(instances)
        for inst in instances:
            doing_tasks = [t for t in (inst.tasks or []) if t.taskState == TaskState.DOING]
            result["task_count"] += len(doing_tasks)
            cur_node = doing_tasks[0].taskName if doing_tasks else None
            if cur_node:
                result["by_node"][cur_node] = result["by_node"].get(cur_node, 0) + 1
            result["instances"].append({
                "id": inst.id,
                "defineId": inst.defineId,
                "createTime": str(inst.createTime),
                "updateTime": str(inst.updateTime),
                "businessNo": inst.businessNo,
                "currentNode": cur_node,
                "doing_tasks": [{"id": t.id, "taskName": t.taskName, "taskState": t.taskState.value if hasattr(t.taskState, 'value') else t.taskState} for t in doing_tasks],
            })
        return result

    async def _processInstance_withdraw(self, args: dict) -> dict:
        instance_id = self._to_int(args.get("id"))
        if not instance_id:
            raise ValueError("id 缺失或非法")
        inst = await self._repo.find_instance_by_id(instance_id)
        if not inst:
            raise ValueError("流程实例不存在")
        # BDD #562 FIX-T59 (2026-09-19)：撤回权限校验
        # 仅发起人 (inst.operator) 或 system/admin 可撤回
        operator_in = str(args.get("operator", "user1"))
        if operator_in.lower() not in ("flow.auto", "flow.admin", "admin"):
            if inst.operator != operator_in:
                raise ValueError(f"非发起人不可撤回 (inst.operator={inst.operator}, 当前 operator={operator_in})")
        # 撤回：废弃全部 doing 任务 + 实例状态（v1.0.1：update_instance 级联落库）
        # 注意：find_instance_by_id 现水合 tasks（issues/110），此处仍按实例单独查 doing 任务废弃，
        # 且必须把聚合副本重置为仅被废弃项（见下方 inst.tasks = abandoned），防级联回写多余任务
        # FIX-T111 §112 (2026-09-21): 显式传 abandoned_by=operator(撤回人),audit 追溯清晰
        operator = str(args.get("operator", "user1"))
        now = datetime.now()
        abandoned = []
        for t in await self._repo.find_doing_tasks(instance_id):
            t.abandon(now, abandoned_by=operator)
            abandoned.append(t)
        inst.withdraw(now)  # issues/53 E25：撤回状态 Withdraw(30) 而非 Reject(45)
        inst.updateUser = operator
        # 级联覆盖防护（issues/57 补正）：废弃副本同步回聚合（update_instance 级联覆盖防护）
        inst.tasks = abandoned
        for t in abandoned:
            await self._repo.update_task(t)
        await self._repo.update_instance(inst)
        return None

    # ── 流程任务 ─────────────────────────────────────────────────────────────

    async def _processTask_todoList(self, args: dict) -> dict:
        """§6.1.3 FIX-T96 (2026-09-20): 我的待办分页 (含 surrogate 自动展开).

        自动展开: actor 是 surrogate (代理人) 时, 也显示其委托方 (operator) 的待办.
        实现: 查 wf_process_surrogate 中 surrogate=actor 的有效委托,
              收集所有被代理的 operator, 在 page_todo_tasks 后合并去重.

        向后兼容: 无委托时, 行为与原 page_todo_tasks 一致.
        """
        page_num = self._to_int(args.get("pageNum") or args.get("pageNo")) or 1
        page_size = self._to_int(args.get("pageSize")) or 10
        actor_id = str(args.get("operator", "user1"))
        # §6.1.3: 收集 surrogate 委托的 operator 列表
        surrogate_operators = await self._collect_surrogate_operators(actor_id)
        rows, total = await self._repo.page_todo_tasks(page_num, page_size, actor_id, self._parse_m_query(args))
        # 如果有 surrogate 委托, 额外查这些 operator 的待办并去重合并
        if surrogate_operators:
            extra_rows = []
            seen_ids = {r.id for r in rows}
            for op in surrogate_operators:
                extra, _ = await self._repo.page_todo_tasks(1, 1000, op, [])
                for r in extra:
                    if r.id not in seen_ids:
                        extra_rows.append(r)
                        seen_ids.add(r.id)
            rows = list(rows) + extra_rows
            total = len(rows)
        return self._page_data([self._task_row_to_dict(r) for r in rows], total, page_num, page_size)

    async def _collect_surrogate_operators(self, surrogate_actor: str) -> list[str]:
        """§6.1.3 FIX-T96: 收集 surrogate=surrogate_actor 的有效委托方列表.

        委托关系: surrogate (代理人) 可代办 operator (委托人) 的任务.
        当前 actor 是 surrogate 时, 收集他作为代理的所有 operator.
        """
        ext = getattr(self, "_ext", None)  # __init__ 存的属性是 self._ext
        if ext is None:
            return []
        try:
            from datetime import datetime as _dt
            now = _dt.now()
            rows, _ = await ext.page_surrogates(1, 1000, filters={"surrogate": surrogate_actor, "enabled": True})
            operators = []
            for s in rows:
                # 检查时间窗口 (startTime <= now <= endTime)
                if s.startTime and s.startTime > now:
                    continue
                if s.endTime and s.endTime < now:
                    continue
                if s.operator and s.operator not in operators:
                    operators.append(s.operator)
            return operators
        except Exception:
            return []

    async def _processTask_doneList(self, args: dict) -> dict:
        """我的已办分页（operator 过滤，v1.5.0 补齐 + §6.1.3 surrogate 展开）"""
        page_num = self._to_int(args.get("pageNum") or args.get("pageNo")) or 1
        page_size = self._to_int(args.get("pageSize")) or 10
        operator = str(args.get("operator", "user1"))
        # §6.1.3: surrogate 自动展开 (同 todoList)
        surrogate_operators = await self._collect_surrogate_operators(operator)
        rows, total = await self._repo.page_done_tasks(page_num, page_size, operator, self._parse_m_query(args))
        if surrogate_operators:
            extra_rows = []
            seen_ids = {r.id for r in rows}
            for op in surrogate_operators:
                extra, _ = await self._repo.page_done_tasks(1, 1000, op, [])
                for r in extra:
                    if r.id not in seen_ids:
                        extra_rows.append(r)
                        seen_ids.add(r.id)
            rows = list(rows) + extra_rows
            total = len(rows)
        return self._page_data([self._task_row_to_dict(r) for r in rows], total, page_num, page_size)

    async def _auditLog_export(self, args: dict) -> dict:
        """§6.2.2 FIX-T98 (2026-09-20): 审计日志导出 (CSV/JSON).

        数据源: wf_process_task 全部历史 (含 operator + taskState + 完成时间).
        支持参数:
          format: csv | json (默认 csv)
          limit: 单次最多导出 (默认 1000, 上限 5000)
          conditions: 通过 _parse_m_query 支持 (operator, process_instance_id, task_state, create_time)
        返回: {format, count, data}
        """
        fmt = str(args.get("format", "csv")).lower()
        if fmt not in ("csv", "json"):
            raise ValueError(f"format 必须是 csv 或 json, 当前={fmt}")
        limit = min(self._to_int(args.get("limit")) or 1000, 5000)
        rows, _ = await self._repo.page_audit_log(1, limit, self._parse_m_query(args))
        dicts = [self._task_row_to_dict(r) for r in rows]
        if fmt == "json":
            import json as _json
            data_str = _json.dumps(dicts, ensure_ascii=False, default=str)
        else:
            import csv as _csv, io
            if dicts:
                buf = io.StringIO()
                writer = _csv.DictWriter(buf, fieldnames=list(dicts[0].keys()))
                writer.writeheader()
                for d in dicts:
                    writer.writerow({k: _csv_safe(v) for k, v in d.items()})
                data_str = buf.getvalue()
            else:
                data_str = ""
        return {"format": fmt, "count": len(dicts), "data": data_str}

    async def _processTask_execute(self, args: dict) -> dict:
        task_id = self._to_int(args.get("processTaskId"))
        if not task_id:
            raise ValueError("processTaskId 缺失或非法")
        operator = str(args.get("operator", "user1"))
        submit_type = self._to_int(args.get("submitType")) or SUBMIT_AGREE
        flow_args = {k: v for k, v in args.items() if k not in ("processTaskId", "operator")}
        flow_args["submitType"] = submit_type

        # BDD #276 FIX-T56 (2026-09-19)：instance PENDING/WITHDRAW/ABANDON 状态禁止 execute
        # 之前: state=50 (PENDING) 后 execute 仍 0 成功，应禁止
        task = await self._repo.find_task_by_id(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        inst = await self._repo.find_instance_by_id(task.processInstanceId)
        if not inst:
            raise ValueError(f"实例不存在: {task.processInstanceId}")
        from .model import InstanceState
        if inst.state not in (InstanceState.DOING,):
            raise ValueError(f"实例 state={inst.state} 不可执行任务（仅 DOING=10 可执行）")

        # §27 修复（2026-09-19）：包 with_tx 事务，保证 lock_instance_for_update 在事务内有效
        # 整个 execute 链路在事务内，PG 同 instance 串行化；REJECT/ROLLBACK/JUMP 路径同样
        async def _dispatch():
            if submit_type == SUBMIT_REJECT:
                await self._engine.execute_and_jump_to_end(task_id, operator, flow_args)
            elif submit_type == SUBMIT_ROLLBACK:
                # BDD #259 FIX-T54 (2026-09-19)：ROLLBACK 也支持 targetTaskName
                # - 有 targetTaskName → 跳指定节点（与 JUMP 一致）
                # - 无 targetTaskName → 退回上一任务节点（Snaker/Java 默认）
                # FIX-T114 (2026-09-21 BDD-DEV-013): 兼容 taskName 在 args.variables.taskName 的常见调用姿势
                # 之前只看顶层 taskName/targetTaskName, 用户习惯放 variables 内 → target="" 走"无 target"分支
                # FIX-T36 §52 行为: assignee 被覆写为前任务完成人/operator, 失去原 assignee
                target = str(
                    args.get("taskName")
                    or args.get("targetTaskName")
                    or (args.get("variables") or {}).get("taskName")
                    or (args.get("variables") or {}).get("targetTaskName")
                    or ""
                )
                await self._engine.execute_and_jump_task(task_id, operator, flow_args, target)
            elif submit_type == SUBMIT_JUMP:
                # BDD #173 FIX-T49 (2026-09-19)：兼容 targetTaskName 别名（与 pageNo 类似）
                # FIX-T114 (2026-09-21 BDD-DEV-013): 同样兼容 variables.taskName
                target = str(
                    args.get("taskName")
                    or args.get("targetTaskName")
                    or (args.get("variables") or {}).get("taskName")
                    or (args.get("variables") or {}).get("targetTaskName")
                    or ""
                )
                await self._engine.execute_and_jump_task(task_id, operator, flow_args, target)
            elif submit_type == SUBMIT_ROLLBACK_TO_OPERATOR:
                await self._engine.execute_and_jump_to_first_task_node(task_id, operator, flow_args)
            elif submit_type == 5:  # SUBMIT_RE_APPLY — FIX-T6 2026-09-17：boot3 同义于跳回首个 task 节点
                await self._engine.execute_and_jump_to_first_task_node(task_id, operator, flow_args)
            elif submit_type == SUBMIT_COUNTERSIGN_DISAGREE:
                flow_args["countersignDisagreeFlag"] = 1
                await self._engine.execute_process_task(task_id, operator, flow_args)
            else:  # 0 APPLY / 1 AGREE / 5 重新提交
                await self._engine.execute_process_task(task_id, operator, flow_args)
        await self._repo.with_tx(_dispatch)
        return None

    # ── 流程设计（需扩展仓储） ───────────────────────────────────────────────

    async def _processDesign_page(self, args: dict) -> dict:
        # issues/50 E22：行转 dict（模型对象直接透传则出口 stringify 不生效，id 为数字）
        ext = self._ext_repo()
        page_num = self._to_int(args.get("pageNum") or args.get("pageNo")) or 1
        page_size = self._to_int(args.get("pageSize")) or 10
        rows, total = await ext.page_designs(page_num, page_size,
                                              conditions=self._parse_m_query(args))
        out = []
        for d in rows:
            out.append({"id": d.id, "name": d.name, "displayName": d.displayName, "type": d.type,
                        "icon": d.icon, "isDeployed": d.isDeployed, "remark": d.remark,
                        "createTime": self._fmt_time(d.createTime), "createUser": d.createUser,
                        "updateTime": self._fmt_time(d.updateTime), "updateUser": d.updateUser})
        return self._page_data(out, total, page_num, page_size)

    async def _processDesignHis_page(self, args: dict) -> dict:
        # FIX-T7 (2026-09-17)：设计历史分页（v1.1.0 wf_process_design_his 表）
        # 累积读所有 design 的 list_design_his，支持 m_processDesignId / m_designId 过滤
        ext = self._ext_repo()
        page_num = self._to_int(args.get("pageNum") or args.get("pageNo")) or 1
        page_size = self._to_int(args.get("pageSize")) or 10
        m_design_id = args.get("m_processDesignId") or args.get("m_designId")
        design_id_filter = self._to_int(m_design_id) if m_design_id else None

        rows_out = []
        # MemoryExtRepository._designHis: dict[int, list[ProcessDesignHis]]
        # JdbcProcessExtRepository 用 list_design_his(design_id) 累积
        if hasattr(ext, "_designHis"):
            for did, his_list in ext._designHis.items():
                if design_id_filter and did != design_id_filter:
                    continue
                for h in his_list:
                    rows_out.append({
                        "id": h.id, "processDesignId": h.processDesignId,
                        "content": h.content, "createTime": self._fmt_time(h.createTime),
                        "createUser": h.createUser,
                    })
        elif hasattr(ext, "list_design_his"):
            # PG 后端：扫所有 design_id
            for did in (ext._designs.keys() if hasattr(ext, "_designs") else []):
                if design_id_filter and did != design_id_filter:
                    continue
                for h in await ext.list_design_his(did):
                    rows_out.append({
                        "id": h.id, "processDesignId": h.processDesignId,
                        "content": h.content, "createTime": self._fmt_time(h.createTime),
                        "createUser": h.createUser,
                    })
        rows_out.sort(key=lambda r: -(r["id"] or 0))
        # FIX-T26 (2026-09-17)：设计历史支持 m_EQ_createUser / m_LIKE_createUser 等通用 m_ 条件
        rows_out = self._filter_rows_by_m_query(rows_out, args)
        total = len(rows_out)
        start = (page_num - 1) * page_size
        page_rows = rows_out[start:start + page_size]
        return self._page_data(page_rows, total, page_num, page_size)


    async def _processDesign_detail(self, args: dict) -> dict:
        ext = self._ext_repo()
        design_id = self._to_int(args.get("id"))
        if not design_id:
            raise ValueError("id 缺失或非法")
        design = await ext.find_design_by_id(design_id)
        if not design:
            raise ValueError("流程设计不存在")
        data = {
            "id": design.id, "name": design.name, "displayName": design.displayName,
            "type": design.type, "icon": design.icon, "isDeployed": design.isDeployed,
            "remark": design.remark,
        }
        his_list = await ext.list_design_his(design_id)
        json_object = None
        if his_list:
            try:
                json_object = json.loads(his_list[0].content)
            except Exception:
                pass
        # issues/07：jsonObject 缺失基本信息时从设计表补齐（对齐 boot3 ProcessDesignServiceImpl.findById）
        if not json_object or not isinstance(json_object, dict):
            json_object = {}
        if "name" not in json_object:
            json_object["name"] = design.name
        if "displayName" not in json_object:
            json_object["displayName"] = design.displayName
        if "type" not in json_object:
            json_object["type"] = design.type
        if "processDesignId" not in json_object:
            json_object["processDesignId"] = design.id
        data["jsonObject"] = json_object
        data["his"] = his_list
        return data

    async def _processDesign_save(self, args: dict) -> dict:
        ext = self._ext_repo()
        operator = str(args.get("operator", "user1"))
        # BDD #251 (2026-09-19)：save 入口先跑 verify
        # 错误阻塞 save (除非 skipVerify=True)
        content_for_verify = self._content(args, required=False)
        if content_for_verify:
            self._verify_or_raise(content_for_verify, args)
        design_id = self._to_int(args.get("id"))
        if not design_id:
            # BDD #141 FIX-T42 (2026-09-19)：按 name UPSERT（同一 name 复用同一行 id）
            # 修复前：连续 save 同 name 每次创建新行（designId 累积）
            # 修复后：复用现有行（id 不变），仅更新 displayName/type/content 等字段
            name = str(args.get("name", ""))
            existing = None
            if name and hasattr(ext, "find_design_by_name"):
                existing = await ext.find_design_by_name(name)
            if existing is not None:
                # 命中已有 design：复用 id + 走更新路径
                design = existing
                if args.get("displayName") is not None:
                    design.displayName = str(args["displayName"])
                if args.get("type") is not None:
                    design.type = str(args["type"])
                if args.get("icon") is not None:
                    design.icon = str(args["icon"])
                if args.get("remark") is not None:
                    design.remark = str(args["remark"])
                design.updateUser = operator
                if self._content(args, required=False):
                    design.isDeployed = False
                await ext.update_design(design)
            else:
                design = ProcessDesign(name=name,
                                       displayName=str(args.get("displayName", "")),
                                       type=str(args.get("type", "approval")),
                                       icon=str(args.get("icon", "")),
                                       remark=str(args.get("remark", "")),
                                       isDeployed=False,  # FIX-T14 (2026-09-17) bool 兼容 PG
                                       createUser=operator, updateUser=operator)
                await ext.save_design(design)
        else:
            design = await ext.find_design_by_id(design_id)
            if not design:
                raise ValueError("流程设计不存在")
            if args.get("displayName") is not None:
                design.displayName = str(args["displayName"])
            if args.get("type") is not None:
                design.type = str(args["type"])
            if args.get("icon") is not None:
                design.icon = str(args["icon"])
            if args.get("remark") is not None:
                design.remark = str(args["remark"])
            design.updateUser = operator
            # 内容快照变更 → 置为未部署（对齐 boot3 updateDefine 语义，issues/08）
            if self._content(args, required=False):
                design.isDeployed = False
            await ext.update_design(design)
        # 内容快照（设计稿内容存历史表）
        content = self._content(args, required=False)
        if content:
            await ext.save_design_his(ProcessDesignHis(processDesignId=design.id,
                                                       content=content, createUser=operator))
        return {"id": design.id}

    async def _processDesign_update(self, args: dict) -> dict:
        """修改流程设计基本信息（对齐 boot3 ProcessDesignController.update，不写设计稿快照）"""
        ext = self._ext_repo()
        # BDD #251：update 入口 verify（如提供 content）
        content_for_verify = self._content(args, required=False)
        if content_for_verify:
            self._verify_or_raise(content_for_verify, args)
        design_id = self._to_int(args.get("id"))
        if not design_id:
            raise ValueError("id 缺失或非法")
        design = await ext.find_design_by_id(design_id)
        if not design:
            raise ValueError("流程设计不存在")
        if args.get("name") is not None:
            design.name = str(args["name"])
        if args.get("displayName") is not None:
            design.displayName = str(args["displayName"])
        if args.get("type") is not None:
            design.type = str(args["type"])
        if args.get("icon") is not None:
            design.icon = str(args["icon"])
        if args.get("remark") is not None:
            design.remark = str(args["remark"])
        design.updateUser = str(args.get("operator", "system"))
        await ext.update_design(design)
        return None

    async def _processDesign_updateDefine(self, args: dict) -> dict:
        """更新流程设计定义（设计稿保存，issues/08）：content 快照入库 + 同步基本信息 + 置未部署"""
        ext = self._ext_repo()
        # BDD #251：updateDefine 入口 verify
        content = self._content(args, required=False)
        if content:
            self._verify_or_raise(content, args)
        design_id = self._to_int(args.get("processDesignId"))
        if not design_id:
            raise ValueError("processDesignId 缺失或非法")
        design = await ext.find_design_by_id(design_id)
        if not design:
            raise ValueError("流程设计不存在")
        if not content:
            raise ValueError("content 缺失")
        # 与最新一条相同则不重复入库（对齐 boot3 updateDefine）
        his_list = await ext.list_design_his(design_id)
        if not his_list or his_list[0].content != content:
            await ext.save_design_his(ProcessDesignHis(processDesignId=design_id,
                                                       content=content,
                                                       createUser=str(args.get("operator", "system"))))
        # 同步设计基本信息（jsonObject 里的 name/displayName/type）+ 内容变更 → 未部署
        import json as _json
        try:
            flow = _json.loads(content)
            if flow.get("name"):
                design.name = flow["name"]
            if flow.get("displayName"):
                design.displayName = flow["displayName"]
            if flow.get("type"):
                design.type = flow["type"]
        except Exception:
            pass
        design.isDeployed = False
        design.updateUser = str(args.get("operator", "system"))
        await ext.update_design(design)
        return None

    async def _processDesign_redeploy(self, args: dict) -> dict:
        """重新部署流程定义（issues/08）：替换最新定义内容 + 置已部署（对齐 boot3 redeploy）"""
        ext = self._ext_repo()
        # BDD #251：redeploy 入口 verify
        # 由于 redeploy 用 his[0].content 部署, 先验证再走原逻辑
        # 实际验证在下面 his[0].content 拿到后再做
        design_id = self._to_int(args.get("id"))
        if not design_id:
            raise ValueError("id 缺失或非法")
        design = await ext.find_design_by_id(design_id)
        if not design:
            raise ValueError("流程设计不存在")
        his_list = await ext.list_design_his(design_id)
        if not his_list:
            raise ValueError("流程设计没有内容，无法发布")
        content = his_list[0].content
        # BDD #251：redeploy 内容验证
        self._verify_or_raise(content, args)
        import json as _json
        try:
            flow = _json.loads(content)
        except Exception as e:
            raise ValueError(f"流程定义 JSON 解析失败: {e}")
        name = flow.get("name") or ""
        if not name:
            raise ValueError("流程定义缺少 name")
        # 按 name 取最新定义：有则替换内容（version 不变），无则新建（对齐 boot3 redeploy）
        last = await self._repo.find_define_by_name(name)
        if last is None:
            define_id = await self._deploy({"content": content,
                                            "operator": args.get("operator", "system")})
        else:
            last.name = name
            last.displayName = flow.get("displayName", "")
            last.type = flow.get("type", "")
            last.content = content
            last.updateUser = str(args.get("operator", "system"))
            await self._repo.update_define(last)
            define_id = last.id
        design.isDeployed = True
        design.updateUser = str(args.get("operator", "system"))
        await ext.update_design(design)
        return {"processDefineId": define_id}

    async def _processDesign_remove(self, args: dict) -> dict:
        # issues/28：兼容 {ids} 批量（boot3 前端 IdsParam 惯例）与单 {id}
        ext = self._ext_repo()
        for design_id in self._id_list(args):
            await ext.remove_design(design_id)
        return None

    async def _processDesign_listByType(self, args: dict) -> dict:
        """按类型分组列出流程设计（issue 30，对齐 Java issues/28）——不依赖框架字典：
        设计全量 → 按 type 分组 → 组内每 name 取最新 define 的 {processDefineId, name,
        displayName, icon, remark, jsonObject}。"""
        ext = self._ext_repo()
        page_num = self._to_int(args.get("pageNum") or args.get("pageNo")) or 1
        page_size = self._to_int(args.get("pageSize")) or 10000
        rows, _total = await ext.page_designs(page_num, page_size, self._parse_m_query(args))
        # 每 name 最新 define（version 最大）
        def_rows, _ = await self._repo.page_defines(1, 10000, [])
        latest_by_name: dict = {}
        for r in def_rows:
            prev = latest_by_name.get(r.name)
            if prev is None or r.version > prev.version:
                latest_by_name[r.name] = r
        groups: dict = {}
        for d in rows:
            groups.setdefault(d.type or "", []).append({
                "processDesignId": d.id,
                "name": d.name,
                "displayName": d.displayName,
                "icon": getattr(d, "icon", None),
                "remark": getattr(d, "remark", None),
                "processDefineId": latest_by_name[d.name].id if d.name in latest_by_name else None,
                "processDefineState": latest_by_name[d.name].state if d.name in latest_by_name else None,
                "jsonObject": self._parse_graph((await ext.list_design_his(d.id))[0].content)
                              if await ext.list_design_his(d.id) else None,
            })
        return groups

    async def _processInstance_bizData(self, args: dict) -> dict:
        """按流程实例回显业务数据（issue 30，对齐 Java issues/28）——meta_reader 注入式，未注入清晰报错"""
        instance_id = self._to_int(args.get("processInstanceId") or args.get("id"))
        if not instance_id:
            raise ValueError("processInstanceId 缺失")
        inst = await self._repo.find_instance_by_id(instance_id)
        if not inst:
            raise ValueError("流程实例不存在")
        def_ = await self._repo.find_define_by_id(inst.defineId)
        if not def_:
            raise ValueError("流程定义不存在")
        table_name = self._rel_table_name(def_.content)
        if not table_name:
            raise ValueError("流程定义未配置 relTableName")
        if self._meta_reader is None:
            raise ValueError("业务数据读取器未注册（facade.set_meta_reader(MetaTableReader(...))，需引入 jeeflow.meta）")
        result = self._meta_reader.read_by_process_instance(table_name, instance_id)
        # BDD #128 FIX：支持 async meta_reader（PG/Memory 都需走 await）
        if hasattr(result, "__await__"):
            result = await result
        return result

    @staticmethod
    def _rel_table_name(content) -> Optional[str]:
        """从流程定义 content 顶层解析 relTableName（缺省回落 name）"""
        try:
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            meta = json.loads(str(content))
            table = str(meta.get("relTableName") or "").strip()
            if not table:
                table = str(meta.get("name") or "").strip()
            return table or None
        except Exception:
            return None

    # ── 委托代理（需扩展仓储） ───────────────────────────────────────────────

    async def _processSurrogate_page(self, args: dict) -> dict:
        ext = self._ext_repo()
        page_num = self._to_int(args.get("pageNum") or args.get("pageNo")) or 1
        page_size = self._to_int(args.get("pageSize")) or 10
        rows, total = await ext.page_surrogates(page_num, page_size,
                                                filters={"operator": str(args["operator"])}
                                                if args.get("operator") else None,
                                                conditions=self._parse_m_query(args))
        return self._page_data([self._surrogate_row_to_dict(s) for s in rows],
                               total, page_num, page_size)

    async def _processSurrogate_save(self, args: dict) -> dict:
        ext = self._ext_repo()
        operator = str(args.get("operator", "user1"))
        surrogate_id = self._to_int(args.get("id"))
        if not surrogate_id:
            surrogate = ProcessSurrogate(operator=operator,  # 授权人 = 操作人（新建必有）
                                         createUser=operator, updateUser=operator)
            self._apply_surrogate_fields(surrogate, args, operator)
            await ext.save_surrogate(surrogate)
        else:
            surrogate = await ext.find_surrogate_by_id(surrogate_id)
            if not surrogate:
                raise ValueError("委托记录不存在")
            self._apply_surrogate_fields(surrogate, args, operator)
            await ext.update_surrogate(surrogate)
        return {"id": surrogate.id}

    async def _processSurrogate_update(self, args: dict) -> dict:
        """委托更新（issues/77）：按 id 全字段更新，id 不存在/缺失报错"""
        ext = self._ext_repo()
        surrogate_id = self._to_int(args.get("id"))
        if not surrogate_id:
            raise ValueError("id 缺失或非法")
        surrogate = await ext.find_surrogate_by_id(surrogate_id)
        if not surrogate:
            raise ValueError("委托记录不存在")
        operator = str(args.get("operator", "user1"))
        self._apply_surrogate_fields(surrogate, args, operator)
        await ext.update_surrogate(surrogate)
        return {"id": surrogate.id}

    async def _processSurrogate_detail(self, args: dict) -> dict:
        """委托详情（issues/77）：按 id 查单条，返回行结构（时间格式化）"""
        surrogate_id = self._to_int(args.get("id"))
        if not surrogate_id:
            raise ValueError("id 缺失或非法")
        surrogate = await self._ext_repo().find_surrogate_by_id(surrogate_id)
        if not surrogate:
            raise ValueError("委托记录不存在")
        return self._surrogate_row_to_dict(surrogate)

    @staticmethod
    def _apply_surrogate_fields(s, args: dict, operator: str):
        """委托写入公共字段。授权人（operator）仅在显式传入时覆盖，避免 update
        时清空原授权人（前端编辑表单不带 operator；集成层注入时 operator=授权人，覆盖无害）"""
        s.processName = str(args.get("processName", ""))
        if "operator" in args:
            s.operator = str(args.get("operator"))
        s.surrogate = str(args.get("surrogate", ""))
        s.startTime = JeeflowFacade._parse_surrogate_time(args.get("startTime"))
        s.endTime = JeeflowFacade._parse_surrogate_time(args.get("endTime"))
        enabled = JeeflowFacade._to_int(args.get("enabled"))
        s.enabled = 1 if enabled is None else enabled  # 显式 0 不得被 or 1 吞掉（对齐 Java/Go toIntDef）
        # FIX-T13 (2026-09-17)：委托 enabled 列兼容 PG BOOLEAN（int 0/1 → bool）
        # PG wf_process_surrogate.enabled 是 BOOLEAN；int 0/1 直接 INSERT asyncpg 拒收。
        # 兜底 bool()，下游 ext_repo.save_surrogate 强转即可。
        s.enabled = bool(s.enabled)
        s.updateUser = operator

    @staticmethod
    def _parse_surrogate_time(v):
        """解析委托时间入参：兼容 yyyy-MM-dd HH:mm:ss（前端 RangePicker/SPEC 契约）
        与 ISO T（issues/77）；无法解析返回 None"""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        s = str(v).strip()
        if not s:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None

    def _surrogate_row_to_dict(self, s) -> dict:
        """委托行：时间格式化（issues/77，对齐 Java surrogateRowToMap / SPEC）"""
        return {"id": s.id, "processName": s.processName, "operator": s.operator,
                "surrogate": s.surrogate,
                "startTime": self._fmt_time(s.startTime), "endTime": self._fmt_time(s.endTime),
                "enabled": s.enabled,
                "createTime": self._fmt_time(s.createTime), "createUser": s.createUser,
                "updateTime": self._fmt_time(s.updateTime), "updateUser": s.updateUser}

    async def _processSurrogate_remove(self, args: dict) -> dict:
        # issues/95：前端「我的委托」行内/批量删除统一发 {ids}，与 define/design remove 同惯例
        ext = self._ext_repo()
        for surrogate_id in self._id_list(args):
            await ext.remove_surrogate(surrogate_id)
        return None

    # ── 视图端点（v1.2.0） ──────────────────────────────────────────────────

    async def _processDefine_getLastByName(self, args: dict) -> dict:
        name = str(args.get("processDefineName", ""))
        def_ = await self._repo.find_define_by_name(name)
        if not def_:
            raise ValueError(f"流程定义不存在: {name}")
        return {"id": def_.id, "name": def_.name, "displayName": def_.displayName,
                "type": def_.type, "state": def_.state, "version": def_.version}

    async def _processDefine_getJobCardContent(self, args: dict) -> dict:
        """读 job_card / initiate.md markdown 作为工作指导（v0.2）

        请求: {processDefineName: "<flow-id>", url: "<ToT/flows/<flow-id>/...>"}
        返回: {url, content, length}
        安全: url 必须以 ToT/flows/<flow-id>/ 开头（流程目录下任意 .md 文件）
              不允许 ToT/flows/<flow-id>.json（流程定义文件）
              标准化：自动补 .md 后缀

        适用文件类型：
        - ToT/flows/<flow>/job_cards/job_card_<taskName>.md（task job card）
        - ToT/flows/<flow>/initiate.md（流程发起指南）
        """
        name = str(args.get("processDefineName", ""))
        url = str(args.get("url", ""))
        if not name:
            raise ValueError("processDefineName 必填")
        if not url:
            raise ValueError("url 必填")
        # 流程必须存在
        def_ = await self._repo.find_define_by_name(name)
        if not def_:
            raise ValueError(f"流程定义不存在: {name}")
        # 标准化 url（自动补 .md 后缀）
        normalized_url = url if url.endswith(".md") else url + ".md"
        # 安全：必须在 ToT/flows/<name>/ 子目录下（不能跨级，也不能读 <name>.json）
        expected_dir = f"ToT/flows/{name}/"
        if not normalized_url.startswith(expected_dir):
            raise ValueError(
                f"url 不安全: {url}（应位于 {expected_dir} 下）"
            )
        # 进一步禁止读 .json 等敏感文件（设计层文件）
        if not normalized_url.endswith(".md"):
            raise ValueError(f"url 后缀必须为 .md: {normalized_url}")
        # 读文件
        try:
            with open(normalized_url, encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            raise ValueError(f"文档文件不存在: {normalized_url}")
        except Exception as e:
            raise ValueError(f"读失败: {e}")
        return {
            "url": normalized_url,
            "content": content,
            "length": len(content),
        }

    async def _processInstance_highLight(self, args: dict) -> dict:
        instance_id = self._to_int(args.get("id"))
        if not instance_id:
            raise ValueError("id 缺失或非法")
        inst = await self._repo.find_instance_by_id(instance_id)
        if not inst:
            raise ValueError("流程实例不存在")
        active, history, edges = [], [], []
        doing = await self._repo.find_doing_tasks(instance_id)
        for t in doing:
            if t.taskName not in active:
                active.append(t.taskName)
        his = await self._repo.find_history_tasks(instance_id)
        for t in his:
            if t.taskName not in active and t.taskName not in history:
                history.append(t.taskName)
        # 路径补全：start 沿边递归（遇活跃节点停止）
        node_progress = {}
        def_ = await self._repo.find_define_by_id(inst.defineId)
        if def_:
            try:
                flow = json.loads(def_.content)
                node_progress = await self._build_node_progress(flow, his)
                await self._collect_path(flow, "start", "", active, history, edges, set(),
                                         inst.variables, his)
            except Exception:
                pass
        return {"activeNodeNames": active, "historyNodeNames": history,
                "historyEdgeNames": edges, "nodeProgress": node_progress}

    async def _build_node_progress(self, flow: dict, tasks: list) -> dict:
        """节点成员进度（issue 41，对齐 boot3 highLight）：按任务状态 + 会签变量组装。
        会签节点带 type（PARALLEL/SEQUENTIAL）；done 按任务完成状态逐人标记，
        active = 进行中任务首位；动态参与人无静态成员不返回；name 缺省（前端降级显示 id）"""
        from .model import TaskState
        progress = {}
        for name in dict.fromkeys(t.taskName for t in tasks):
            ts = [t for t in tasks if t.taskName == name]
            vars_ = ts[0].variables or {}
            # 完整办理人列表：会签变量 operatorList_{node} 优先（顺序会签全量），否则任务 actorIds 并集
            members = vars_.get(f"operatorList_{name}")
            if not members:
                members = list(dict.fromkeys(a for t in ts for a in (t.actorIds or [])))
            if not members:
                continue  # 动态参与人：无静态成员，不返回
            done_set = {a for t in ts if t.taskState == TaskState.DONE for a in (t.actorIds or [])}
            active_actor = next((t.actorIds[0] for t in ts
                                 if t.taskState == TaskState.DOING and t.actorIds), None)
            # 会签判定：定义节点属性（引擎创建任务时 performType 未落任务表，取模型为准）
            node = next((n for n in flow.get("nodes", []) if n.get("id") == name), None)
            props = (node or {}).get("properties", {}) or {}
            cs_type = props.get("countersignType")
            is_cs = cs_type is not None or str(props.get("performType", "")).strip().upper() in ("1", "ALL", "COUNTERSIGN")
            # 姓名走 UserProvider SPI 解析（issue 43/E15）：asyncio.gather 并行批量，查不到缺省空串
            name_map = {}
            if self._engine.user_prov is not None:
                us = await asyncio.gather(*[self._engine.user_prov.get_user(uid) for uid in members],
                                          return_exceptions=True)
                for uid, u in zip(members, us):
                    if isinstance(u, Exception):
                        continue  # 单用户失败不影响其余
                    if u and u.realName:
                        name_map[uid] = u.realName
            members_out = []
            for uid in members:
                m = {"id": uid, "name": name_map.get(uid, "")}
                if uid in done_set:
                    m["done"] = True
                elif uid == active_actor:
                    m["active"] = True
                members_out.append(m)
            item = {"members": members_out}
            if is_cs and cs_type:
                item["type"] = cs_type
            progress[name] = item
        return progress

    async def _collect_path(self, flow: dict, node_id: str, edge_name: str,
                            active: list, history: list, edges: list, visited: set,
                            vars_: dict, history_tasks: list):
        if node_id in visited:
            return
        visited.add(node_id)
        if edge_name and edge_name not in edges:
            edges.append(edge_name)
        src = self._find_node(flow, node_id)
        for e in flow.get("edges", []):
            if e.get("sourceNodeId") != node_id:
                continue
            # 决策节点：输出边表达式求值过滤（对齐 boot3 recursionModel，issues/06）
            if src and src.get("type") == "snaker:decision":
                expr = (e.get("properties") or {}).get("expr")
                if expr and not await self._eval_decision_expr(flow, src, expr, vars_, history_tasks):
                    continue
            target = self._find_node(flow, e.get("targetNodeId"))
            if not target:
                continue
            tid = target.get("id")
            if tid not in active and tid not in history:
                history.append(tid)
            if tid in active:
                continue
            await self._collect_path(flow, tid, e.get("id"), active, history, edges, visited,
                                     vars_, history_tasks)

    async def _eval_decision_expr(self, flow: dict, decision: dict, expr: str,
                                  vars_: dict, history_tasks: list) -> bool:
        """决策输出边表达式求值（args = 实例变量 + 决策节点前置任务变量）"""
        import asyncio
        args = dict(vars_ or {})
        for e in flow.get("edges", []):
            if e.get("targetNodeId") == decision.get("id"):
                for t in history_tasks or []:
                    if t.taskName == e.get("sourceNodeId") and t.variables:
                        args.update(t.variables)
                    break
                break
        result = await self._engine.eval_expr(expr, args)
        if asyncio.iscoroutine(result):
            result = await result
        return bool(result)

    @staticmethod
    def _find_node(flow: dict, node_id):
        for n in flow.get("nodes", []):
            if n.get("id") == node_id:
                return n
        return None

    async def _processInstance_approvalRecord(self, args: dict) -> dict:
        instance_id = self._to_int(args.get("id"))
        if not instance_id:
            raise ValueError("id 缺失或非法")
        his = await self._repo.find_history_tasks(instance_id)
        return [{
            "taskName": t.taskName, "displayName": t.displayName,
            "taskType": int(t.taskType) if t.taskType is not None else None,
            "performType": int(t.performType) if t.performType is not None else None,
            "taskState": int(t.taskState) if t.taskState is not None else None,
            "operator": t.actorId, "finishTime": self._fmt_time(t.finishTime),
            "variable": t.variables,
            "ext": t.variables,  # issues/15：前端读 ext.tf_approvalComment
        } for t in his]

    async def _processInstance_getAssigneeTextData(self, args: dict) -> dict:
        instance_id = self._to_int(args.get("id"))
        if not instance_id:
            raise ValueError("id 缺失或非法")
        include_node_name = args.get("includeNodeName") is not False
        rows = []
        doing = await self._repo.find_doing_tasks(instance_id)
        for t in doing:
            actors = await self._repo.find_task_actors(t.id)
            for actor in actors:
                label = actor
                if include_node_name:
                    label = f"{t.displayName}:{actor}"
                rows.append({"label": label, "value": actor})
        return rows

    async def _processInstance_createCCInstance(self, args: dict) -> dict:
        instance_id = self._to_int(args.get("processInstanceId"))
        operator = str(args.get("operator", "user1"))
        actor_ids = self._to_str_list(args.get("actorIds"))
        if not instance_id or not actor_ids:
            raise ValueError("processInstanceId/actorIds 缺失")
        await self._repo.create_cc_instance(instance_id, operator, *actor_ids)
        # issues/102：手动 CC 与发起路径同语义——逐抄送人 fire CC_CREATE
        for actor in actor_ids:
            await self._engine.fire_event(
                ProcessEvent(type=EventType.CC_CREATE, instanceId=instance_id, ccActorId=actor))
        return None

    async def _processInstance_updateCCStatus(self, args: dict) -> dict:
        instance_id = self._to_int(args.get("processInstanceId"))
        operator = str(args.get("operator", "user1"))
        if not instance_id:
            raise ValueError("processInstanceId 缺失或非法")
        await self._repo.update_cc_status(instance_id, operator)
        return None

    async def _processInstance_ccList(self, args: dict) -> dict:
        """我的抄送分页（v1.3.0）：operator 作为抄送人过滤
        BDD #1065 FIX-T61 (2026-09-20)：processInstanceId 直接生效
        之前 §61：processInstanceId 参数被忽略；现在 facade 显式转为 m_EQ_id 条件
        """
        page_num = self._to_int(args.get("pageNum") or args.get("pageNo")) or 1
        page_size = self._to_int(args.get("pageSize")) or 10
        actor_id = str(args.get("operator", "user1"))
        conditions = self._parse_m_query(args)
        # FIX-T61 §61：args.processInstanceId 直接生效 → 等价 m_EQ_id
        pid = self._to_int(args.get("processInstanceId"))
        if pid:
            conditions.append(QueryCondition(column="t.id", operator="EQ", value=pid))
        rows, total = await self._repo.page_cc_instances(page_num, page_size, actor_id, conditions)
        return self._page_data([self._cc_row_to_dict(r) for r in rows], total, page_num, page_size)

    async def _processTask_detail(self, args: dict) -> dict:
        task_id = self._to_int(args.get("id"))
        operator = str(args.get("operator", "user1"))
        if not task_id:
            raise ValueError("id 缺失或非法")
        task = await self._repo.find_task_by_id(task_id)
        if not task:
            raise ValueError("任务不存在")
        actors = await self._repo.find_task_actors(task_id)
        # issues/82-5：任务级 ext.isFirstTaskNode（前端 detail.vue 双兜底 record.ext?.isFirstTaskNode）
        # 首个任务节点且 DOING → true，与 instance detail 的 activeTaskList 行语义一致
        t_ext = dict(task.variables or {})
        doing = task.taskState == TaskState.DOING
        t_ext["isFirstTaskNode"] = False
        vo = {
            "id": task.id, "processInstanceId": task.processInstanceId,
            "taskName": task.taskName, "displayName": task.displayName,
            "taskType": int(task.taskType) if task.taskType is not None else None,
            "performType": int(task.performType) if task.performType is not None else None,
            "taskState": int(task.taskState) if task.taskState is not None else None,
            "operator": task.actorId, "formKey": task.formKey,
            "taskActorIdList": actors, "executable": task.is_allowed(operator),
            "ext": t_ext,
        }
        # taskModel：流程定义中对应节点
        inst = await self._repo.find_instance_by_id(task.processInstanceId)
        if inst:
            def_ = await self._repo.find_define_by_id(inst.defineId)
            if def_:
                vo["jsonObject"] = self._parse_graph(def_.content)  # issues/05
                t_ext["isFirstTaskNode"] = doing and task.taskName == self._first_task_node_id(
                    self._parse_graph(def_.content))
                try:
                    flow = json.loads(def_.content)
                    for n in flow.get("nodes", []):
                        if n.get("id") == task.taskName:
                            props = n.get("properties", {}) or {}
                            # issues/62：taskModel 补 form/ext（节点字段权限，对齐 boot2）
                            vo["taskModel"] = {"name": n.get("id"),
                                               "displayName": (n.get("text") or {}).get("value", ""),
                                               "type": n.get("type"),
                                               "form": props.get("form"),
                                               "ext": props.get("field")}
                            break
                except Exception:
                    pass
        return vo

    async def _processTask_jumpAbleTaskNameList(self, args: dict) -> dict:
        instance_id = self._to_int(args.get("processInstanceId"))
        if not instance_id:
            raise ValueError("processInstanceId 缺失或非法")
        done = await self._repo.find_done_tasks(instance_id)
        rows, seen = [], set()
        for t in done:
            if int(t.performType or 0) == 1:  # COUNTERSIGN
                continue
            if t.taskName not in seen:
                seen.add(t.taskName)
                rows.append({"label": t.displayName, "value": t.taskName})
        return rows

    async def _processTask_candidatePage(self, args: dict) -> dict:
        page_num = self._to_int(args.get("pageNum") or args.get("pageNo")) or 1
        page_size = self._to_int(args.get("pageSize")) or 10
        task_id = self._to_int(args.get("processTaskId")) or self._to_int(args.get("id"))
        if not task_id:
            raise ValueError("processTaskId 缺失")
        task = await self._repo.find_task_by_id(task_id)
        if not task:
            raise ValueError("任务不存在")
        inst = await self._repo.find_instance_by_id(task.processInstanceId)
        if not inst:
            raise ValueError("流程实例不存在")
        # 模型候选解析：后继任务节点的 candidateUsers 配置
        candidates = []
        def_ = await self._repo.find_define_by_id(inst.defineId)
        if def_:
            try:
                flow = json.loads(def_.content)
                candidates = await self._next_task_candidates(flow, task.taskName)
            except Exception:
                pass
        if candidates:
            # issues/80：行键对齐前端 UserSelect（valueField='id'）——补 id 键，保留 userId 兼容旧消费方
            rows = [{"id": c, "userId": c, "realName": c} for c in candidates]
            return self._page_data(rows, len(rows), page_num, page_size)
        # 无模型候选 → 用户分页搜索（依赖 user_search 钩子）
        if self._user_search is None:
            raise ValueError("未配置 user_search（用户搜索钩子）")
        result = self._user_search(args)
        if inspect.isawaitable(result):
            result = await result
        rows, total = result
        return self._page_data(rows, total, page_num, page_size)

    async def _next_task_candidates(self, flow: dict, task_name: str) -> list:
        result = []
        visited = set()

        async def collect(node: dict):
            v = (node.get("properties") or {}).get("candidateUsers", "")
            if v:
                for s in str(v).split(","):
                    s = s.strip()
                    if s and s not in result:
                        result.append(s)
            # candidateGroups：按角色取人（v1.6.0，对齐 boot4 GlobalCandidateHandler）
            g = (node.get("properties") or {}).get("candidateGroups", "")
            if g and self._org_prov is not None:
                for rc in str(g).split(","):
                    rc = rc.strip()
                    if not rc:
                        continue
                    ids = await self._org_prov.find_by_role(rc) or []
                    for uid in ids:
                        if uid and uid not in result:
                            result.append(uid)

        async def walk(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            for e in flow.get("edges", []):
                if e.get("sourceNodeId") != node_id:
                    continue
                target = self._find_node(flow, e.get("targetNodeId"))
                if not target:
                    continue
                if target.get("type") in ("snaker:task", "snaker:custom"):
                    await collect(target)
                    continue
                if target.get("type") in ("snaker:fork", "snaker:join", "snaker:decision"):
                    await walk(target.get("id"))

        await walk(task_name)
        return result

    async def _processTask_surrogate(self, args: dict) -> dict:
        return await self._taskAddActor(args)

    async def _processTask_addCandidate(self, args: dict) -> dict:
        return await self._taskAddActor(args)

    async def _processTask_removeCandidate(self, args: dict) -> dict:
        """BDD #138 FIX-T40：减签（移除 task actor）"""
        task_id = self._to_int(args.get("processTaskId"))
        actor_ids = self._to_str_list(args.get("actorIds"))
        if not task_id or not actor_ids:
            raise ValueError("processTaskId/actorIds 缺失")
        await self._repo.remove_task_actor(task_id, actor_ids)
        return None

    async def _taskAddActor(self, args: dict) -> dict:
        task_id = self._to_int(args.get("processTaskId"))
        actor_ids = self._to_str_list(args.get("actorIds"))
        if not task_id or not actor_ids:
            raise ValueError("processTaskId/actorIds 缺失")
        await self._repo.add_task_actor(task_id, actor_ids)
        return None

    async def _processTask_latest(self, args: dict) -> dict:
        instance_id = self._to_int(args.get("processInstanceId"))
        if not instance_id:
            raise ValueError("processInstanceId 缺失或非法")
        doing = await self._repo.find_doing_tasks(instance_id)
        if not doing:
            return None
        t = doing[0]
        return {"id": t.id, "taskName": t.taskName, "displayName": t.displayName,
                "taskState": int(t.taskState) if t.taskState is not None else None,
                "operator": t.actorId}

    @staticmethod
    def _to_str_list(v) -> list:
        if isinstance(v, (list, tuple)):
            return [str(x) for x in v]
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return []

    # ── 工具 ─────────────────────────────────────────────────────────────────

    def _ext_repo(self) -> ProcessExtRepository:
        if self._ext is None:
            raise ValueError("未配置 ProcessExtRepository（扩展仓储）")
        return self._ext

    @staticmethod
    def _content(args: dict, required: bool = True) -> Optional[str]:
        content = args.get("content")
        if content is None:
            # issues/31：兼容 boot3 顶层 JSON（无 content 字段）——非保留字段序列化为内容快照
            copy = {k: v for k, v in args.items() if k not in ("processDesignId", "operator")}
            if not copy:
                if required:
                    raise ValueError("content 缺失")
                return None
            content = json.dumps(copy, ensure_ascii=False)
        if isinstance(content, (dict, list)):
            # content 为对象（前端直接传 JSON 对象）：序列化为 JSON 字符串
            return json.dumps(content, ensure_ascii=False)
        if isinstance(content, bytes):
            return content.decode("utf-8")
        return str(content)

    @staticmethod
    def _to_int(v) -> Optional[int]:
        if v is None:
            return None
        # issues/82 负向（对齐 Go TestSnowflakeIDPrecision / Node toId / Java toLong / issues/38 E9）：
        # 浮点型 id 超 2^53 说明精度已丢（json 解析 / 调用方 float 产物），必须显性报错，
        # 不能 int() 静默截断成错误 id。Python int 本任意精度不受限，仅 float 会丢精度。
        if isinstance(v, float) and abs(v) > 2 ** 53:
            raise ValueError(f"id {v} 超出 float64 精确范围（2^53），请以字符串传递")
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    def _id_list(self, args: dict) -> list:
        """删除/启停类 action 的批量主键：mldong IdsParam 惯例下 {ids} 数组优先，兼容单
        {id}；两者皆缺失、空数组或含非法值一律报错（issues/95，对齐 Java idListArgs）。"""
        ids = args.get("ids")
        if isinstance(ids, (list, tuple)):
            out = []
            for v in ids:
                i = self._to_int(v)
                if not i:
                    raise ValueError("id 缺失或非法")
                out.append(i)
            if not out:
                raise ValueError("id 缺失或非法")
            return out
        single = self._to_int(args.get("id"))
        if not single:
            raise ValueError("id 缺失或非法")
        return [single]

    def _parse_m_query(self, args: dict) -> list:
        """m_ 前缀查询参数解析（issues/05-5，对齐 Java JeeflowQueryParser）：
        m_EQ_taskName → t.task_name EQ；m_pd_LIKE_displayName → pd.display_name LIKE"""
        out = []
        for key, value in args.items():
            if not key.startswith("m_") or value is None or value == "":
                continue
            parts = key[2:].split("_")
            if len(parts) < 2:
                continue
            if len(parts) == 2:
                # 无别名 → 默认主表别名 t（对齐 Java，白名单列均带表别名）
                operator, column = parts[0], "t." + self._to_underscore(parts[1])
            else:
                operator, column = parts[1], parts[0] + "." + self._to_underscore(parts[2])
            out.append(QueryCondition(column=column, operator=operator.upper(), value=value))
        return out

    def _filter_rows_by_m_query(self, rows: list, args: dict, allowed_columns: set = None) -> list:
        """FIX-T26 (2026-09-17)：对已聚合的 rows 应用 m_ 过滤（设计历史等非 SQL 来源行）
        columns 默认白名单：id, processDesignId, content, createTime, createUser
        """
        conds = self._parse_m_query(args)
        # 过滤掉 processDesignId（已在外面处理）和未允许列
        if allowed_columns is None:
            allowed_columns = {"t.id", "t.process_design_id", "t.content", "t.create_time", "t.create_user"}
        kept = []
        for r in rows:
            fields = {
                "t.id": r.get("id"),
                "t.process_design_id": r.get("processDesignId"),
                "t.content": r.get("content"),
                "t.create_time": r.get("createTime"),
                "t.create_user": r.get("createUser"),
            }
            ok = True
            for c in conds:
                if c.column not in allowed_columns:
                    continue
                v = fields.get(c.column)
                expect = c.value
                op = c.operator.upper()
                if op == "EQ" and not (str(v) == str(expect)):
                    ok = False; break
                elif op == "NE" and not (str(v) != str(expect)):
                    ok = False; break
                elif op == "LIKE" and expect not in str(v or ""):
                    ok = False; break
                elif op == "LLIKE" and not str(v or "").endswith(str(expect)):
                    ok = False; break
                elif op == "RLIKE" and not str(v or "").startswith(str(expect)):
                    ok = False; break
            if ok:
                kept.append(r)
        return kept

    @staticmethod
    def _to_underscore(camel: str) -> str:
        out = []
        for c in camel:
            if c.isupper():
                out.append("_" + c.lower())
            else:
                out.append(c)
        return "".join(out)

    @staticmethod
    def _page_data(rows, total: int, page_num: int = 1, page_size: int = 10) -> dict:
        # issues/64：对齐 mldong 分页五键（Java pageResult / Go pageData）
        page_num = page_num or 1
        page_size = page_size or 10
        total_page = 0
        if total > 0 and page_size > 0:
            total_page = (total + page_size - 1) // page_size
        return {
            "pageNum": page_num,
            "pageSize": page_size,
            "recordCount": total,
            "totalPage": total_page,
            "rows": rows,
        }

    @staticmethod
    def _ok(data) -> dict:
        return {"code": 0, "msg": "成功", "data": data}

    @staticmethod
    def _error(msg: str) -> dict:
        return {"code": 99999999, "msg": msg}

    @staticmethod
    def _task_vo(t) -> dict:
        """任务 VO（instanceDetail 任务列表用，对齐 Java taskVo）"""
        import json as _json
        try:
            variable = _json.dumps(t.variables, ensure_ascii=False) if t.variables else None
        except Exception:
            variable = None
        return {
            "id": t.id, "processInstanceId": t.processInstanceId, "taskName": t.taskName,
            "displayName": t.displayName, "taskType": t.taskType, "performType": t.performType,
            "taskState": t.taskState, "operator": t.actorId, "finishTime": t.finishTime,
            "expireTime": t.expireTime, "formKey": t.formKey, "taskParentId": t.parentTaskId,
            "variable": variable, "createTime": t.createTime, "createUser": t.createUser,
            "updateTime": t.updateTime, "updateUser": t.updateUser, "taskActorIdList": t.actorIds,
            "taskFormData": JeeflowFacade._form_data_of(t.variables, "tf_"),  # issues/15（_task_vo 无 self，走类名调用）
        }

    @staticmethod
    def _parse_graph(content) -> Optional[dict]:
        """定义 content 解析为 LogicFlow JSON（issues/05 jsonObject）"""
        import json as _json
        if not content:
            return None
        try:
            obj = _json.loads(content) if isinstance(content, str) else content
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    async def _instance_json_object(self, inst) -> Optional[dict]:
        """实例关联定义的 jsonObject"""
        def_ = await self._repo.find_define_by_id(inst.defineId)
        return self._parse_graph(def_.content) if def_ else None

    @staticmethod
    def _first_task_node_id(graph: Optional[dict]) -> Optional[str]:
        """流程 JSON 中第一个任务节点 id（issues/05-4 isFirstTaskNode 用）"""
        for n in (graph or {}).get("nodes", []):
            if isinstance(n, dict) and n.get("type") == "snaker:task":
                return n.get("id")
        return None

    # ── 实例/任务扩展操作（BDD #258 FIX-T53 2026-09-19） ───────────────────
    async def _processInstance_suspend(self, args: dict) -> dict:
        """挂起实例 (state=50 PENDING)"""
        inst_id = self._to_int(args.get("id")) or self._to_int(args.get("processInstanceId"))
        if not inst_id:
            raise ValueError("id 缺失")
        operator = str(args.get("operator", "admin"))
        async def _do():
            inst = await self._repo.find_instance_by_id(inst_id)
            if not inst: raise ValueError(f"实例不存在: {inst_id}")
            if inst.state not in (InstanceState.DOING, InstanceState.PENDING):
                raise ValueError(f"实例 state={inst.state} 不可挂起")
            inst.state = InstanceState.PENDING
            inst.updateUser = operator
            await self._repo.update_instance(inst)
        await self._repo.with_tx(_do)
        return {"id": inst_id, "state": InstanceState.PENDING.value}

    async def _processInstance_resume(self, args: dict) -> dict:
        """恢复实例 (state=10 DOING)"""
        inst_id = self._to_int(args.get("id")) or self._to_int(args.get("processInstanceId"))
        if not inst_id:
            raise ValueError("id 缺失")
        operator = str(args.get("operator", "admin"))
        async def _do():
            inst = await self._repo.find_instance_by_id(inst_id)
            if not inst: raise ValueError(f"实例不存在: {inst_id}")
            if inst.state != InstanceState.PENDING:
                raise ValueError(f"实例 state={inst.state} 不可恢复（仅 PENDING 可恢复）")
            inst.state = InstanceState.DOING
            inst.updateUser = operator
            await self._repo.update_instance(inst)
        await self._repo.with_tx(_do)
        return {"id": inst_id, "state": InstanceState.DOING.value}

    async def _processTask_transfer(self, args: dict) -> dict:
        """任务转交：修改 task actorIds + 记录到 task variables"""
        task_id = self._to_int(args.get("processTaskId")) or self._to_int(args.get("id"))
        if not task_id:
            raise ValueError("processTaskId 缺失")
        operator = str(args.get("operator", ""))
        target = str(args.get("targetUserId") or args.get("toUserId") or "")
        if not target:
            raise ValueError("targetUserId 缺失")
        async def _do():
            task = await self._repo.find_task_by_id(task_id)
            if not task: raise ValueError(f"任务不存在: {task_id}")
            if task.taskState != TaskState.DOING:
                raise ValueError(f"任务 state={task.taskState} 不可转交")
            old_actors = list(task.actorIds or [])
            task.actorIds = [a.strip() for a in target.split(",") if a.strip()]
            task.updateUser = operator
            await self._repo.update_task(task)
            return {"oldActors": old_actors, "newActors": list(task.actorIds)}
        result = await self._repo.with_tx(_do)
        return {"taskId": task_id, **result}

    async def _processTask_transferAndAdd(self, args: dict) -> dict:
        """BDD #1104 FIX-T75 (2026-09-20) §3.2.2：transfer + addCandidate 合并端点

        与 transfer 的区别：
        - transfer: 替换 actorIds 为 [target] (单一新处理人)
        - transferAndAdd: actorIds = old + [target] (保留原 actor, 加 target)
        - 适用于: A 转给 B 后, A 仍需看流程后续动态 (审计场景)

        字段:
        - processTaskId: 必填
        - operator: 当前处理人 (校验)
        - targetUserId: 新增处理人
        """
        task_id = self._to_int(args.get("processTaskId")) or self._to_int(args.get("id"))
        if not task_id:
            raise ValueError("processTaskId 缺失")
        operator = str(args.get("operator", ""))
        target = str(args.get("targetUserId") or args.get("toUserId") or "")
        if not target:
            raise ValueError("targetUserId 缺失")
        async def _do():
            task = await self._repo.find_task_by_id(task_id)
            if not task: raise ValueError(f"任务不存在: {task_id}")
            if task.taskState != TaskState.DOING:
                raise ValueError(f"任务 state={task.taskState} 不可转交")
            if operator and operator not in (task.actorIds or []):
                raise ValueError(f"operator {operator} 不在 task actorIds 中")
            old_actors = list(task.actorIds or [])
            # addCandidate (保留原 actors)
            target_clean = target.strip()
            if target_clean and target_clean not in old_actors:
                old_actors.append(target_clean)
            task.actorIds = old_actors
            task.updateUser = operator or target_clean
            await self._repo.update_task(task)
            return {"oldActors": list(task.actorIds), "newActors": list(task.actorIds)}
        result = await self._repo.with_tx(_do)
        return {"taskId": task_id, **result}

    async def _processTask_comment(self, args: dict) -> dict:
        """任务评论：追加到 task variables['_comments'] 列表"""
        task_id = self._to_int(args.get("processTaskId")) or self._to_int(args.get("id"))
        if not task_id:
            raise ValueError("processTaskId 缺失")
        operator = str(args.get("operator", ""))
        comment = str(args.get("comment") or args.get("content") or "")
        if not comment:
            raise ValueError("comment 缺失")
        async def _do():
            task = await self._repo.find_task_by_id(task_id)
            if not task: raise ValueError(f"任务不存在: {task_id}")
            var = dict(task.variables or {})
            comments = list(var.get("_comments", []))
            comments.append({
                "operator": operator,
                "comment": comment,
                "time": datetime.now().isoformat()
            })
            var["_comments"] = comments
            task.variables = var
            task.updateUser = operator
            await self._repo.update_task(task)
            return {"count": len(comments)}
        result = await self._repo.with_tx(_do)
        return {"taskId": task_id, **result}

    async def _processTask_extra(self, args: dict) -> dict:
        """任务额外信息：合并到 task variables (key-value)"""
        task_id = self._to_int(args.get("processTaskId")) or self._to_int(args.get("id"))
        if not task_id:
            raise ValueError("processTaskId 缺失")
        operator = str(args.get("operator", ""))
        kv = {k: v for k, v in args.items()
              if k not in ("processTaskId", "id", "operator")}
        if not kv:
            raise ValueError("至少传一个额外字段")
        async def _do():
            task = await self._repo.find_task_by_id(task_id)
            if not task: raise ValueError(f"任务不存在: {task_id}")
            var = dict(task.variables or {})
            extra = dict(var.get("_extra", {}))
            extra.update(kv)
            var["_extra"] = extra
            task.variables = var
            task.updateUser = operator
            await self._repo.update_task(task)
            return extra
        result = await self._repo.with_tx(_do)
        return {"taskId": task_id, "extra": result}

    async def _processTask_delegate(self, args: dict) -> dict:
        """BDD #142 FIX-T69 (2026-09-20)：任务委派（per-task 临时）

        与 surrogate (全局规则) 区别：
        - delegate 仅对**单条 task** 临时授权，不影响用户其他任务
        - 在 task.variables._delegate_of[原actor] = targetUser
        - 同时 addCandidate(task, [targetUser]) 让 actorIds 校验通过
        - engine._is_allowed 失败时 fallback 检查 _delegate_of
        """
        task_id = self._to_int(args.get("processTaskId")) or self._to_int(args.get("id"))
        if not task_id:
            raise ValueError("processTaskId 缺失")
        operator = str(args.get("operator", ""))
        target = str(args.get("targetUserId") or args.get("toUserId") or "")
        if not target:
            raise ValueError("targetUserId 缺失")
        if not operator:
            raise ValueError("operator 缺失")
        async def _do():
            task = await self._repo.find_task_by_id(task_id)
            if not task:
                raise ValueError(f"任务不存在: {task_id}")
            if task.taskState != TaskState.DOING:
                raise ValueError(f"任务 state={task.taskState} 不可委派")
            # 校验：operator 必须是 task 当前 actor
            actors = list(task.actorIds or [])
            if operator not in actors:
                raise ValueError(f"operator {operator} 不在 task actorIds 中")
            # addCandidate 写入目标用户（保留原 actor，不移除）
            await self._repo.add_task_actor(task_id, [target])
            # 重新读取 task（add_task_actor 可能改 actorIds）
            task = await self._repo.find_task_by_id(task_id)
            var = dict(task.variables or {})
            delegate_of = dict(var.get("_delegate_of", {}))
            delegate_of[operator] = target
            var["_delegate_of"] = delegate_of
            var["_delegate_at"] = datetime.now().isoformat()
            task.variables = var
            task.updateUser = operator
            await self._repo.update_task(task)
            return {"delegated": operator, "to": target, "actors": list(task.actorIds or [])}
        result = await self._repo.with_tx(_do)
        return {"taskId": task_id, **result}

    async def _processTask_delegateHistory(self, args: dict) -> dict:
        """BDD #1103 FIX-T74 (2026-09-20) §3.2.1：delegate 历史查询端点

        返回 task.variables._delegate_of 完整历史
        字段:
          - taskId: int
          - delegateHistory: [{from: actor, to: targetUser, at: datetime}]
          - delegateAt: 最近一次 delegate 时间 (ISO 格式)
        """
        task_id = self._to_int(args.get("processTaskId")) or self._to_int(args.get("id"))
        if not task_id:
            raise ValueError("processTaskId 缺失")
        task = await self._repo.find_task_by_id(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        var = dict(task.variables or {})
        delegate_of = dict(var.get("_delegate_of", {}))
        # 转换 dict → list (历史顺序按 from actor 排序)
        history = [
            {"from": actor, "to": target, "at": var.get("_delegate_at")}
            for actor, target in sorted(delegate_of.items())
        ]
        return {
            "taskId": task_id,
            "delegateHistory": history,
            "delegateAt": var.get("_delegate_at"),
            "actorIds": list(task.actorIds or []),
        }

    async def _processTask_withForm(self, args: dict) -> dict:
        """BDD #1105 FIX-T76 (2026-09-20) §3.2.3：with-form 字段权限联动

        给 task 绑定表单字段 + 字段权限。提交 execute 时按权限过滤字段。
        与节点 field.PERMISSION_* 区别:
        - 节点级 PERMISSION_*: 部署时静态声明, 所有 instance 一致
        - task 级 withForm: 运行时动态绑定, 支持 per-instance 定制

        字段:
        - processTaskId: 必填
        - operator: 当前处理人 (校验)
        - formKey: 表单 schema key (用于前端渲染)
        - fields: dict {field_name: {type, required, perm}} — perm=1 只读 / 2 编辑 / 3 隐藏
        """
        task_id = self._to_int(args.get("processTaskId")) or self._to_int(args.get("id"))
        if not task_id:
            raise ValueError("processTaskId 缺失")
        operator = str(args.get("operator", ""))
        form_key = str(args.get("formKey", ""))
        fields = args.get("fields") or {}
        if not isinstance(fields, dict):
            raise ValueError("fields 必须是 dict")
        async def _do():
            task = await self._repo.find_task_by_id(task_id)
            if not task: raise ValueError(f"任务不存在: {task_id}")
            if task.taskState != TaskState.DOING:
                raise ValueError(f"任务 state={task.taskState} 不可绑定表单")
            var = dict(task.variables or {})
            var["_form_key"] = form_key
            var["_form_fields"] = fields
            task.variables = var
            task.updateUser = operator or "system"
            await self._repo.update_task(task)
            return {"formKey": form_key, "fieldCount": len(fields)}
        result = await self._repo.with_tx(_do)
        return {"taskId": task_id, **result}

    # ── 统计（v1.8.25，issues/103） ──────────────────────────────────────────

    _DEFAULT_STATE_IN = [10, 20, 30, 40, 45, 50]
    _DEFAULT_STATS_LIMIT = 10
    _VALID_GRANULARITY = {"hour", "day", "week", "month"}
    _VALID_DIMENSION = {"state", "define", "category", "approver", "applicant",
                        "node", "stuckNode", "stuckApprover", "durationBucket"}

    async def _processInstance_stats_overview(self, args: dict) -> dict:
        start = self._parse_surrogate_time(args.get("start"))
        end = self._parse_surrogate_time(args.get("end"))
        state_in = args.get("stateIn") or self._DEFAULT_STATE_IN

        insts = await self._repo.query_instances_for_stats(state_in, "create_time", start, end)
        total = len(insts)
        in_progress = sum(1 for r in insts if r.state == 10)
        completed = sum(1 for r in insts if r.state == 20)
        withdrawn = sum(1 for r in insts if r.state == 30)
        rejected = sum(1 for r in insts if r.state == 45)
        suspended = sum(1 for r in insts if r.state == 50)

        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        # E：todayNew 恒按服务器当日、不过滤 state / 不受 stateIn 影响（对齐内置线 countTodayNew）
        today_insts = await self._repo.query_instances_for_stats(
            None, "create_time", today_start, today_end)
        today_new = len(today_insts)

        pending, overdue = await self._repo.stats_pending_and_overdue_count()
        avg_dur = await self._repo.stats_avg_completed_duration_seconds(start, end)
        # FIX-T27 (2026-09-17)：活跃操作人数（窗口内不同 operator 数）
        active_users = await self._repo.stats_active_users_count(start, end)

        cs_total, cs_count, on_time, on_time_denom = await self._repo.stats_completed_task_aggregate()
        countersign_rate = _stats_round4(cs_count / cs_total) if cs_total > 0 else 0.0
        on_time_rate = _stats_round4(on_time / on_time_denom) if on_time_denom > 0 else 0.0
        reject_rate = _stats_round4(rejected / max(1, completed + rejected))

        return {
            "total": total, "inProgress": in_progress, "completed": completed,
            "rejected": rejected, "withdrawn": withdrawn, "suspended": suspended,
            "todayNew": today_new, "avgDurationSeconds": avg_dur,
            "rejectRate": reject_rate, "pendingTaskCount": pending,
            "overdueTaskCount": overdue, "countersignRate": countersign_rate,
            "onTimeRate": on_time_rate,
            "activeUserCount": active_users,
        }

    async def _processInstance_stats_trend(self, args: dict) -> dict:
        granularity = str(args.get("granularity", ""))
        if granularity not in self._VALID_GRANULARITY:
            raise ValueError(f"不支持的 granularity: {granularity}")
        start = self._parse_surrogate_time(args.get("start"))
        end = self._parse_surrogate_time(args.get("end"))
        # C：start/end 必填（对齐内置线 20010012 缺参语义），不静默回退不限时间
        if start is None or end is None:
            raise ValueError("trend 缺少必填参数：start/end/granularity")

        # 实例侧无 state 过滤（对齐内置线 countInstanceStartedByBucket）
        insts = await self._repo.query_instances_for_stats(None, "create_time", start, end)
        done_tasks = await self._repo.query_tasks_for_stats(int(TaskState.DONE), start, end)

        buckets = _stats_enumerate_buckets(start, end, granularity)
        started_map: dict[str, int] = {}
        for r in insts:
            ct = self._parse_surrogate_time(r.createTime)
            if ct:
                bk = _stats_bucket_key(ct, granularity)
                started_map[bk] = started_map.get(bk, 0) + 1
        finished_map: dict[str, int] = {}
        for r in done_tasks:
            ft = self._parse_surrogate_time(r.finishTime)
            if ft:
                bk = _stats_bucket_key(ft, granularity)
                finished_map[bk] = finished_map.get(bk, 0) + 1

        series = []
        for b in buckets:
            series.append({"bucket": b, "started": started_map.get(b, 0),
                           "finished": finished_map.get(b, 0)})
        # A：data 本体为裸数组（去掉 {granularity, series} 包装，对齐契约 spec 06 §4.2 / 内置线）
        return series

    async def _processInstance_stats_group(self, args: dict) -> dict:
        dimension = str(args.get("dimension", ""))
        if dimension not in self._VALID_DIMENSION:
            raise ValueError(f"不支持的 dimension: {dimension}")
        start = self._parse_surrogate_time(args.get("start"))
        end = self._parse_surrogate_time(args.get("end"))
        limit = self._to_int(args.get("limit")) or self._DEFAULT_STATS_LIMIT

        if dimension == "define":
            raw = await self._repo.stats_define_group(start, end, limit)
            rows = [{"key": r["key"], "label": r.get("label"), "count": r["count"],
                     "avgDurationSeconds": r.get("avgDurationSeconds")} for r in raw]

        elif dimension == "state":
            insts = await self._repo.query_instances_for_stats(None, "create_time", start, end)  # 无 state 过滤（对齐内置线：仅 overview 用 stateIn）
            # FIX-T21 (2026-09-17)：state 枚举映射 label（设计器可读）
            _STATE_LABELS = {"10": "进行中", "20": "已完成", "30": "已撤回", "99": "已废弃"}
            grouped: dict[str, int] = {}
            for r in insts:
                k = str(r.state)
                grouped[k] = grouped.get(k, 0) + 1
            entries = sorted(grouped.items(), key=lambda x: x[1], reverse=True)[:limit]
            rows = [{"key": k, "label": _STATE_LABELS.get(k, "未知"), "count": c, "avgDurationSeconds": None} for k, c in entries]

        elif dimension == "category":
            insts = await self._repo.query_instances_for_stats(None, "create_time", start, end)  # 无 state 过滤（对齐内置线：仅 overview 用 stateIn）
            define_types: dict[int, str] = {}
            for r in insts:
                if r.defineId not in define_types:
                    defn = await self._repo.find_define_by_id(r.defineId)
                    define_types[r.defineId] = defn.type if defn else ""
            grouped2: dict[str, int] = {}
            for r in insts:
                tp = define_types.get(r.defineId, "")
                grouped2[tp] = grouped2.get(tp, 0) + 1
            entries2 = sorted(grouped2.items(), key=lambda x: x[1], reverse=True)[:limit]
            rows = [{"key": k, "label": None, "count": c, "avgDurationSeconds": None} for k, c in entries2]

        elif dimension == "approver":
            tasks = await self._repo.query_tasks_for_stats(int(TaskState.DONE), start, end)
            grouped3: dict[str, int] = {}
            for r in tasks:
                if not r.operator:
                    continue
                grouped3[r.operator] = grouped3.get(r.operator, 0) + 1
            entries3 = sorted(grouped3.items(), key=lambda x: x[1], reverse=True)[:limit]
            rows = [{"key": k, "label": None, "count": c, "avgDurationSeconds": None} for k, c in entries3]

        elif dimension == "applicant":
            insts = await self._repo.query_instances_for_stats(None, "create_time", start, end)  # 无 state 过滤（对齐内置线：仅 overview 用 stateIn）
            grouped4: dict[str, int] = {}
            for r in insts:
                if not r.operator:
                    continue
                grouped4[r.operator] = grouped4.get(r.operator, 0) + 1
            entries4 = sorted(grouped4.items(), key=lambda x: x[1], reverse=True)[:limit]
            rows = [{"key": k, "label": None, "count": c, "avgDurationSeconds": None} for k, c in entries4]

        elif dimension == "node":
            tasks = await self._repo.query_tasks_for_stats(int(TaskState.DONE), start, end)
            node_agg: dict[str, dict] = {}
            for r in tasks:
                if not r.displayName:
                    continue
                dur = 0
                ft = self._parse_surrogate_time(r.finishTime)
                ct = self._parse_surrogate_time(r.createTime)
                if ft and ct:
                    dur = int((ft - ct).total_seconds())
                agg = node_agg.get(r.displayName)
                if agg is None:
                    agg = {"count": 0, "totalDur": 0}
                    node_agg[r.displayName] = agg
                agg["count"] += 1
                agg["totalDur"] += dur
            entries5 = sorted(node_agg.items(), key=lambda x: x[1]["count"], reverse=True)[:limit]
            rows = []
            for name, agg in entries5:
                avg = int(round(agg["totalDur"] / agg["count"])) if agg["count"] > 0 else None
                rows.append({"key": name, "label": None, "count": agg["count"],
                             "avgDurationSeconds": avg})

        elif dimension == "stuckNode":
            raw5 = await self._repo.stats_stuck_node_group(limit)
            rows = [{"key": r["key"], "label": r.get("label"), "count": r["count"],
                     "avgDurationSeconds": r.get("avgDurationSeconds")} for r in raw5]

        elif dimension == "stuckApprover":
            raw6 = await self._repo.stats_stuck_approver_group(limit)
            rows = [{"key": r["key"], "label": r.get("label"), "count": r["count"],
                     "avgDurationSeconds": r.get("avgDurationSeconds")} for r in raw6]

        elif dimension == "durationBucket":
            durations = await self._repo.stats_completed_instance_durations(start, end)
            same_day = d1to3 = d3to7 = over7d = 0
            for dur in durations:
                if dur < 86400:
                    same_day += 1
                elif dur < 259200:
                    d1to3 += 1
                elif dur < 604800:
                    d3to7 += 1
                else:
                    over7d += 1
            keys = ["sameDay", "1to3d", "3to7d", "over7d"]
            counts = [same_day, d1to3, d3to7, over7d]
            rows = [{"key": keys[i], "label": None, "count": counts[i],
                     "avgDurationSeconds": None} for i in range(4)]
        else:
            rows = []

        # A：data 本体为裸数组（去掉 {dimension, rows} 包装，对齐契约 spec 06 §4.2 / 内置线）
        return rows

    # ═══ 行输出转换（issues/05-2 字段契约 + 05-3 时间格式）═══

    @staticmethod
    def _form_data_of(vars_: dict, prefix: str) -> dict:
        """issues/15：取 vars 中 prefix 前缀字段，输出「带前缀 + 去前缀副本」（对齐 boot3 getFormData）"""
        out = {}
        for k, v in (vars_ or {}).items():
            if k and k.startswith(prefix):
                out[k] = v
                out[k[len(prefix):]] = v
        return out

    @staticmethod
    def _fmt_time(t) -> Optional[str]:
        """时间格式化 yyyy-MM-dd HH:mm:ss"""
        if t is None:
            return None
        if isinstance(t, str):
            return t.replace("T", " ")[:19]
        return t.strftime("%Y-%m-%d %H:%M:%S")

    def _define_row_to_dict(self, r) -> dict:
        return {"id": r.id, "name": r.name, "displayName": r.displayName, "type": r.type,
                "state": r.state, "version": r.version,
                "createTime": self._fmt_time(r.createTime), "createUser": r.createUser,
                "updateTime": self._fmt_time(r.updateTime), "updateUser": r.updateUser}

    def _instance_row_to_dict(self, r) -> dict:
        return {"id": r.id, "parentId": r.parentId, "processDefineId": r.defineId,
                "state": int(r.state) if r.state is not None else None,
                "parentNodeName": r.parentNodeName, "businessNo": r.businessNo, "operator": r.operator,
                "ownerId": getattr(r, "ownerId", "") or "",  # FIX-T9 (2026-09-17) §66 ownerId 字段
                "expireTime": self._fmt_time(r.expireTime), "variable": r.variables,
                "createTime": self._fmt_time(r.createTime), "createUser": r.createUser,
                "updateTime": self._fmt_time(r.updateTime), "updateUser": r.updateUser,
                "processDefineName": r.defineName, "processDefineDisplayName": r.defineDisplayName,
                "processDefineVersion": r.defineVersion,
                "ext": r.variables, "displayName": r.defineDisplayName, "version": r.defineVersion}

    def _cc_row_to_dict(self, r) -> dict:
        return self._instance_row_to_dict(r) if hasattr(r, "defineName") else {
            "id": r.id, "parentId": r.parentId, "processDefineId": r.defineId,
            "state": int(r.state) if r.state is not None else None,
            "parentNodeName": r.parentNodeName, "businessNo": r.businessNo, "operator": r.operator,
            "expireTime": self._fmt_time(r.expireTime), "variable": r.variables,
            "createTime": self._fmt_time(r.createTime), "createUser": r.createUser,
            "updateTime": self._fmt_time(r.updateTime), "updateUser": r.updateUser,
            "processDefineName": r.defineName, "processDefineDisplayName": r.defineDisplayName,
            "processDefineVersion": r.defineVersion,
            "ext": r.variables, "displayName": r.defineDisplayName, "version": r.defineVersion}

    def _task_row_to_dict(self, r) -> dict:
        instance_ext = r.instanceVariable
        if isinstance(instance_ext, str):
            try:
                instance_ext = json.loads(instance_ext) if instance_ext else {}
            except Exception:
                instance_ext = {}
        ext = r.variables or {}
        if not ext:
            ext = instance_ext
        return {"id": r.id, "processInstanceId": r.processInstanceId, "taskName": r.taskName,
                "displayName": r.displayName, "taskType": r.taskType, "performType": r.performType,
                "taskState": int(r.taskState) if r.taskState is not None else None,
                "operator": r.operator, "finishTime": self._fmt_time(r.finishTime),
                "expireTime": self._fmt_time(r.expireTime), "formKey": r.formKey,
                "taskParentId": r.taskParentId, "variable": r.variables,
                "createTime": self._fmt_time(r.createTime), "createUser": r.createUser,
                "updateTime": self._fmt_time(r.updateTime), "updateUser": r.updateUser,
                "processDefineName": r.processDefineName,
                "processDefineDisplayName": r.processDefineDisplayName,
                "instanceVariable": r.instanceVariable,
                "instanceCreateTime": self._fmt_time(r.instanceCreateTime),
                "ext": ext, "instanceExt": instance_ext, "version": r.defineVersion,
                "taskFormData": self._form_data_of(ext, "tf_"),  # issues/15
                # FIX-T32 (2026-09-18)：§55 doneList 行 taskActorIdList 字段
                "taskActorIdList": list(getattr(r, "taskActorIdList", []) or [])}


def _stats_round4(v: float) -> float:
    return round(v * 10000) / 10000


def _stats_week_key(t: datetime) -> str:
    iso = t.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def _stats_enumerate_buckets(start: Optional[datetime], end: Optional[datetime],
                             granularity: str) -> list[str]:
    now = datetime.now()
    s = start if start else now - timedelta(days=30)
    e = end if end else now

    buckets: list[str] = []
    if granularity == "hour":
        cursor = s.replace(minute=0, second=0, microsecond=0)
        while cursor <= e:
            buckets.append(cursor.strftime("%Y-%m-%d %H:00"))
            cursor += timedelta(hours=1)
    elif granularity == "day":
        cursor = s.replace(hour=0, minute=0, second=0, microsecond=0)
        end_day = e.replace(hour=0, minute=0, second=0, microsecond=0)
        while cursor <= end_day:
            buckets.append(cursor.strftime("%Y-%m-%d"))
            cursor += timedelta(days=1)
    elif granularity == "week":
        cursor = s.replace(hour=0, minute=0, second=0, microsecond=0)
        weekday = cursor.weekday()
        cursor -= timedelta(days=weekday)
        end_day = e.replace(hour=0, minute=0, second=0, microsecond=0)
        while cursor <= end_day:
            buckets.append(_stats_week_key(cursor))
            cursor += timedelta(days=7)
    elif granularity == "month":
        year, month = s.year, s.month
        end_year, end_month = e.year, e.month
        while (year, month) <= (end_year, end_month):
            buckets.append(f"{year}-{month:02d}")
            month += 1
            if month > 12:
                month = 1
                year += 1
    return buckets


def _stats_bucket_key(t: datetime, granularity: str) -> str:
    if granularity == "hour":
        return t.strftime("%Y-%m-%d %H:00")
    elif granularity == "day":
        return t.strftime("%Y-%m-%d")
    elif granularity == "week":
        return _stats_week_key(t)
    elif granularity == "month":
        return t.strftime("%Y-%m")
    return ""


def _is_id_key(k: str) -> bool:
    """id 类字段名判定（对齐 Java 实体 id 命名）：精确 'id' 或以 'Id' 结尾
    （processDefineId/processInstanceId/processTaskId/processDesignId/parentId/...）"""
    return k == "id" or k.endswith("Id")


def _stringify_ids(v):
    """出口 id 统一 string 化（issues/38 E9，对齐 Node 全程 string / Java 全局
    ToStringSerializer）——递归处理 dict/list；id 类字段的 int 值转 str，
    None 保持 None（parentId 无值不出 'None'），字符串直通。

    dataclass 分支（issues/76）：dataclass 实例 asdict 后递归，收口
    "嵌套 dataclass 列表整表外泄 int id" 的泄漏面（his 列表），
    对齐 Go stringifyIDs 处理 reflect.Struct（issues/58）。"""
    if isinstance(v, dict):
        return {k: (_stringify_ids(val) if not _is_id_key(k) else
                    (None if val is None else
                     (str(val) if isinstance(val, int) and not isinstance(val, bool) else val)))
                for k, val in v.items()}
    if isinstance(v, (list, tuple)):
        return [_stringify_ids(x) for x in v]
    if dataclasses.is_dataclass(v) and not isinstance(v, type):
        return _stringify_ids(dataclasses.asdict(v))
    return v

def _csv_safe(v):
    """§6.2.1 FIX-T97: CSV 安全序列化 (dict/list 序列化为字符串)."""
    import json as _json
    if v is None: return ""
    if isinstance(v, (dict, list)): return _json.dumps(v, ensure_ascii=False, default=str)
    if isinstance(v, (int, float, bool, str)): return v
    return str(v)
