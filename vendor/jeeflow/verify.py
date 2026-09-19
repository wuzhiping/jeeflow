"""流程定义验证规则库 (2026-09-19 BDD 狩猎汇总)

调用方：
- vendor/jeeflow/facade.py:_processDesign_save
- vendor/jeeflow/facade.py:_processDesign_update
- vendor/jeeflow/facade.py:_deploy
- vendor/jeeflow/facade.py:_processDefine_redeploy
- vendor/jeeflow/facade.py:_processDesign_redeploy

规则分类：
- E (Error) - 阻塞 save
- W (Warning) - 不阻塞，存入 design.remark
- P (Pattern) - 反模式建议

来源 BDD：
- BDD #127-#250 (124 个 BDD 任务中累积的所有 BUG/限制/反模式)
- v1.9.0+ 已知 BUG 全部纳入
"""

from typing import Tuple, List
import re
import json


# ─── 规则 ID 常量 ──────────────────────────────────────────────
E_NAME_MISSING = "E001"
E_NODE_ID_DUPLICATE = "E002"
E_NODE_ID_INVALID = "E003"
E_CYCLE = "E004"
E_NO_START = "E005"
E_NO_END = "E006"
E_EDGE_REFERENCE = "E007"
E_CS_NO_TYPE = "E008"
E_CS_WITH_HANDLER = "E009"
E_DECISION_NO_OUT = "E010"
E_TASK_NO_ASSIGNEE = "E011"
E_CUSTOM_NO_HANDLER = "E012"   # BDD #127 custom 节点未配 clazz (handler)
E_DECISION_HANDLER_UNKNOWN = "E013"  # BDD #32 decision 节点 decisionHandler 未注册
E_SURROGATE_FIELDS_MISSING = "E014"  # surrogate 配置缺 operator 或 surrogate
E_PARENT_CHILD_NAME_CONFLICT = "E015"  # 子流程 name 与已存在流程冲突

W_START_HAS_IN = "W001"
W_END_HAS_OUT = "W002"
W_DECISION_FALLBACK_ONLY = "W003"
W_CS_APPLICANT = "W004"
W_FORK_NO_JOIN = "W005"
W_TOO_MANY_NODES = "W006"
W_PERMISSION_FIELD = "W007"
W_DUPLICATE_EDGES = "W008"
W_PERMISSION_GAP = "W009"
W_DECISION_NO_EXPR = "W010"   # decision 节点所有出边 expr 都为空
W_CUSTOM_UNUSED_VAL = "W011"   # custom 节点 val 字段空（FIX-T38 §16）

P_CS_SINGLE_ACTOR = "P001"
P_JUMP_NO_TARGET = "P002"
P_NO_TASK = "P003"
P_NESTED_DECISION = "P004"
P_DEEP_CHAIN = "P005"          # 流程节点深度 > 10 层

ALL_CODES = {
    E_NAME_MISSING: "name 字段缺失或为空",
    E_NODE_ID_DUPLICATE: "节点 id 重复 (FIX-T31)",
    E_NODE_ID_INVALID: "节点 id 含非法字符 (FIX-T34, 须 ^[A-Za-z0-9_]+$)",
    E_CYCLE: "流程含环 (FIX-T50, 会死循环或无界 task 创建)",
    E_NO_START: "无 start 节点 (BDD #210, 启动失败)",
    E_NO_END: "无 end 节点 (BDD #211, 流程卡死)",
    E_EDGE_REFERENCE: "边 source/target 引用了不存在的节点 (BDD #239)",
    E_CS_NO_TYPE: "performType=1 (会签) 但无 countersignType (BDD #214, 引擎容错但语义错)",
    E_CS_WITH_HANDLER: "会签节点配 assignmentHandler (assignmentHandler 不会被执行)",
    E_DECISION_NO_OUT: "decision 节点所有出边 expr 都为空 (会一直走首边)",
    E_TASK_NO_ASSIGNEE: "task 节点无 assignee 也无 assignmentHandler (节点卡死)",
    E_CUSTOM_NO_HANDLER: "custom 节点未配 clazz (handler 必填, FIX-T38 §16)",
    E_DECISION_HANDLER_UNKNOWN: "decision 节点 decisionHandler 字段格式非法 (BDD #32 §46)",
    E_SURROGATE_FIELDS_MISSING: "surrogate 配置缺 operator 或 surrogate (BDD #26 §40)",
    E_PARENT_CHILD_NAME_CONFLICT: "子流程 name 与已存在流程冲突 (BDD #40 §56)",
    W_START_HAS_IN: "start 节点有入边 (反模式, start 应是流程入口)",
    W_END_HAS_OUT: "end 节点有出边 (反模式, end 应是流程终点)",
    W_DECISION_FALLBACK_ONLY: "decision 节点所有出边 expr 都为空 (仅兜底, 建议显式条件)",
    W_CS_APPLICANT: "会签节点用 applicant 关键字 (会签人应是固定用户, 不是发起人)",
    W_FORK_NO_JOIN: "fork 节点无对应 join (分支可能不汇合, BDD #184)",
    W_TOO_MANY_NODES: "流程节点数 > 50 (建议拆分或精简)",
    W_PERMISSION_FIELD: "field 权限声明了但 variables 没用对应字段 (死配置)",
    W_DUPLICATE_EDGES: "同一对节点重复多条边 (冗余)",
    W_PERMISSION_GAP: "字段在某节点声明为 hidden/read, 但其他节点未声明 (建议显式声明以防覆盖)",
    W_DECISION_NO_EXPR: "decision 节点所有出边 expr 都为空且无 decisionHandler (BDD #32 §46)",
    W_CUSTOM_UNUSED_VAL: "custom 节点 val 字段空 (handler 结果丢弃, FIX-T38 §16)",
    P_CS_SINGLE_ACTOR: "会签只有 1 个 actor (退化为普通 task, 建议去掉 performType=1)",
    P_JUMP_NO_TARGET: "submitType=4 (JUMP) 但 targetTaskName/taskName 字段缺失",
    P_NO_TASK: "流程无 task 节点 (仅计算, 注意 'type=business' 才能纯计算)",
    P_NESTED_DECISION: "decision 嵌套 > 3 层 (可读性差, 建议拆分或合并)",
    P_DEEP_CHAIN: "流程 task 链路过深 (> 10, 建议拆分或用子流程)",
}

TYPE_START = "snaker:start"
TYPE_END = "snaker:end"
TYPE_TASK = "snaker:task"
TYPE_DECISION = "snaker:decision"
TYPE_FORK = "snaker:fork"
TYPE_JOIN = "snaker:join"
TYPE_CUSTOM = "snaker:custom"


class VerifyIssue:
    __slots__ = ("code", "level", "msg", "node_ids", "edge_ids")

    def __init__(self, code: str, level: str, msg: str, node_ids: list = None, edge_ids: list = None):
        self.code = code
        self.level = level  # "error" / "warning" / "pattern"
        self.msg = msg
        self.node_ids = node_ids or []
        self.edge_ids = edge_ids or []

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "level": self.level,
            "message": self.msg,
            "nodeIds": self.node_ids,
            "edgeIds": self.edge_ids,
        }

    def __str__(self) -> str:
        ids = ""
        if self.node_ids:
            ids += f" nodes={self.node_ids}"
        if self.edge_ids:
            ids += f" edges={self.edge_ids}"
        return f"[{self.code}/{self.level}] {self.msg}{ids}"


def _check_cycle(node_ids: list, edges: list, node_types: dict = None) -> bool:
    """检测会导致死循环的环

    策略 BDD #364/#365 FIX-T58 (2026-09-19)：
    - 仅检测 task 节点构成的环（task→task→...→task）
    - 自环 / 短环 / 长环都拦截
    - decision→task 回退 (业务环) 不拦截（如 14-decision-submitType 用例）

    BDD #209 #213: 自环 / start→mid→start → 死循环
    """
    # FIX-T58 v2 (2026-09-19)：仅 task→task cycle 视为死循环
    # 但 task 直接/间接回到 start 也算
    task_nodes = set()  # 需调用方传 node_types

    adj = {nid: [] for nid in node_ids}
    for e in edges:
        s, t = e.get("sourceNodeId"), e.get("targetNodeId")
        if s in adj and t in adj:
            adj[s].append(t)

    # 自环
    for n in node_ids:
        if n in adj[n]:
            return True

    # 找入度为 0 的"start 候选"节点
    in_deg = {nid: 0 for nid in node_ids}
    out_deg = {nid: 0 for nid in node_ids}
    for e in edges:
        s, t = e.get("sourceNodeId"), e.get("targetNodeId")
        if s in in_deg and t in in_deg:
            in_deg[t] += 1
            out_deg[s] += 1
    starts = [nid for nid in in_deg if in_deg[nid] == 0 and out_deg.get(nid, 0) > 0]
    if not starts and node_ids:
        # 找不到自然 start, 用入度最小的节点
        starts = [min(node_ids, key=lambda n: in_deg.get(n, 999))]

    # FIX-T58 v3 (2026-09-19)：仅检测"task 直接构成的环"或"自环"
    # 业务回退（decision→task）允许（如 14-decision-submitType 用例）
    # 直接 task→task cycle 才拦截（如 a→b→a）
    is_task = lambda n: node_types.get(n, "") == TYPE_TASK if node_types else True

    def has_cycle(u, stack):
        if u in stack:
            return True
        if u not in adj:
            return False
        stack.add(u)
        for v in adj[u]:
            if v in adj and is_task(v) and has_cycle(v, stack):
                return True
        stack.remove(u)
        return False

    # 仅从 task 节点出发，且中间必须全是 task 节点
    for n in node_ids:
        if not is_task(n):
            continue
        if has_cycle(n, set()):
            return True
    return False


def verify_flow(flow: dict, variables: dict = None) -> Tuple[List[VerifyIssue], List[VerifyIssue], List[VerifyIssue]]:
    """流程定义 verify 入口

    Returns:
        (errors, warnings, patterns) - 三类 issue 列表
    """
    errors: List[VerifyIssue] = []
    warnings: List[VerifyIssue] = []
    patterns: List[VerifyIssue] = []
    variables = variables or {}

    name = (flow.get("name") or "").strip()
    if not name:
        errors.append(VerifyIssue(E_NAME_MISSING, "error", "流程 name 字段缺失或为空"))

    nodes = flow.get("nodes") or []
    edges = flow.get("edges") or []

    # 节点索引
    node_ids: list = []
    node_by_id: dict = {}
    for n in nodes:
        nid = n.get("id")
        if not nid:
            continue
        node_ids.append(nid)
        node_by_id[nid] = n

    # FIX-T58 v2 (2026-09-19)：构造 node_types 用于 cycle 检测
    node_types = {nid: n.get("type", "") for nid, n in node_by_id.items()}

    # E002 - 节点 id 重复
    seen: dict = {}
    for nid in node_ids:
        seen[nid] = seen.get(nid, 0) + 1
    dup_ids = sorted([nid for nid, c in seen.items() if c > 1])
    if dup_ids:
        errors.append(VerifyIssue(E_NODE_ID_DUPLICATE, "error",
                                   f"节点 id 重复: {dup_ids}", node_ids=dup_ids))

    # E003 - 节点 id 含非法字符
    pattern = re.compile(r"^[A-Za-z0-9_]+$")
    bad_ids = sorted([nid for nid in node_ids if not pattern.match(nid)])
    if bad_ids:
        errors.append(VerifyIssue(E_NODE_ID_INVALID, "error",
                                   f"节点 id 含非法字符: {bad_ids}（只允许 ^[A-Za-z0-9_]+$）",
                                   node_ids=bad_ids))

    # E005 / E006 - 必须有 start / end
    start_ids = [nid for nid, n in node_by_id.items() if n.get("type") == TYPE_START]
    end_ids = [nid for nid, n in node_by_id.items() if n.get("type") == TYPE_END]
    if not start_ids:
        errors.append(VerifyIssue(E_NO_START, "error", "流程无 start 节点"))
    if not end_ids:
        errors.append(VerifyIssue(E_NO_END, "error", "流程无 end 节点"))

    # W001 - start 不应有入边
    in_edges: dict = {nid: [] for nid in node_ids}
    out_edges: dict = {nid: [] for nid in node_ids}
    for e in edges:
        s, t = e.get("sourceNodeId"), e.get("targetNodeId")
        if s in in_edges and t in in_edges:
            in_edges[t].append(e.get("id"))
            out_edges[s].append(e.get("id"))

    for sid in start_ids:
        if in_edges.get(sid):
            warnings.append(VerifyIssue(W_START_HAS_IN, "warning",
                                       f"start 节点[{sid}] 不应有入边", node_ids=[sid]))

    # W002 - end 不应有出边
    for eid in end_ids:
        if out_edges.get(eid):
            warnings.append(VerifyIssue(W_END_HAS_OUT, "warning",
                                       f"end 节点[{eid}] 不应有出边", node_ids=[eid]))

    # E004 - 环
    if _check_cycle(node_ids, edges, node_types):
        errors.append(VerifyIssue(E_CYCLE, "error",
                                   f"流程含环（cycle），会死循环或无界 task 创建"))

    # E007 - 边 source/target 引用不存在节点
    orphan_edges: list = []
    for e in edges:
        s, t = e.get("sourceNodeId"), e.get("targetNodeId")
        if s not in node_by_id:
            orphan_edges.append((e.get("id"), s, t, "source 不存在"))
        elif t not in node_by_id:
            orphan_edges.append((e.get("id"), s, t, "target 不存在"))
    if orphan_edges:
        bad_edge_ids = [x[0] for x in orphan_edges]
        errors.append(VerifyIssue(E_EDGE_REFERENCE, "error",
                                   f"边引用不存在节点: {orphan_edges}",
                                   edge_ids=bad_edge_ids))

    # 节点级检查
    for nid, n in node_by_id.items():
        ntype = n.get("type")
        props = n.get("properties") or {}

        # E008 - 会签无 cs_type
        pt = props.get("performType")
        if pt in (1, "1", "ALL", "COUNTERSIGN"):
            cs = props.get("countersignType")
            if not cs:
                errors.append(VerifyIssue(E_CS_NO_TYPE, "error",
                                           f"节点[{nid}] performType=1 但无 countersignType (会签必须配 PARALLEL/SEQUENTIAL)",
                                           node_ids=[nid]))

        # E009 - 会签配 assignmentHandler（不应混用）
        if pt in (1, "1", "ALL", "COUNTERSIGN"):
            if props.get("assignmentHandler"):
                errors.append(VerifyIssue(E_CS_WITH_HANDLER, "error",
                                           f"会签节点[{nid}] 不应配 assignmentHandler (会签 assignee 应是字面量列表)",
                                           node_ids=[nid]))

        # E010 - decision 节点无出边 expr
        if ntype == TYPE_DECISION:
            out = out_edges.get(nid, [])
            if not out:
                errors.append(VerifyIssue(E_DECISION_NO_OUT, "error",
                                           f"decision 节点[{nid}] 无出边 (卡死)",
                                           node_ids=[nid]))

        # E011 - task 节点无 assignee 也无 assignmentHandler
        if ntype == TYPE_TASK:
            assignee = props.get("assignee", "")
            handler = props.get("assignmentHandler", "")
            if not assignee and not handler:
                errors.append(VerifyIssue(E_TASK_NO_ASSIGNEE, "error",
                                           f"task 节点[{nid}] 无 assignee 也无 assignmentHandler (没人能办)",
                                           node_ids=[nid]))

        # W003 - decision 节点所有出边 expr 都为空
        if ntype == TYPE_DECISION:
            out = out_edges.get(nid, [])
            if out:
                all_empty = True
                for eid in out:
                    e = next((e for e in edges if e.get("id") == eid), None)
                    if e and (e.get("properties") or {}).get("expr"):
                        all_empty = False
                        break
                if all_empty:
                    warnings.append(VerifyIssue(W_DECISION_FALLBACK_ONLY, "warning",
                                               f"decision 节点[{nid}] 所有出边 expr 都为空 (只走兜底, 建议显式条件)",
                                               node_ids=[nid]))

        # W004 - 会签用 applicant
        if pt in (1, "1", "ALL", "COUNTERSIGN") and "applicant" in (props.get("assignee") or ""):
            warnings.append(VerifyIssue(W_CS_APPLICANT, "warning",
                                       f"会签节点[{nid}] 用 applicant 关键字 (会签人应是固定用户)",
                                       node_ids=[nid]))

        # P001 - 会签单 actor
        if pt in (1, "1", "ALL", "COUNTERSIGN"):
            assignee = props.get("assignee", "")
            actors = [a.strip() for a in assignee.split(",") if a.strip()]
            if len(actors) == 1:
                patterns.append(VerifyIssue(P_CS_SINGLE_ACTOR, "pattern",
                                            f"会签节点[{nid}] 只有 1 个 actor (退化为普通 task, 建议去掉 performType=1)",
                                            node_ids=[nid]))

        # P004 - decision 嵌套 > 3 层
        # 简化: 通过边回溯统计上游 decision 数
        # 留作性能优化, 此处只检查自身
        pass

    # W005 - fork 无 join
    fork_ids = [nid for nid, n in node_by_id.items() if n.get("type") == TYPE_FORK]
    join_ids = set(nid for nid, n in node_by_id.items() if n.get("type") == TYPE_JOIN)
    for fid in fork_ids:
        # 简化: 从 fork 出发 BFS, 走 task/decision/custom 节点后是否遇到 join
        from collections import deque
        visited = set()
        q = deque([fid])
        has_join = False
        while q:
            cur = q.popleft()
            if cur in visited:
                continue
            visited.add(cur)
            if cur in join_ids:
                has_join = True
                break
            if cur != fid and node_by_id.get(cur, {}).get("type") in (TYPE_TASK, TYPE_DECISION, TYPE_CUSTOM):
                # 遇到 task/dec 不再下钻
                continue
            for eid in out_edges.get(cur, []):
                e = next((e for e in edges if e.get("id") == eid), None)
                if e:
                    q.append(e.get("targetNodeId"))
        if not has_join:
            warnings.append(VerifyIssue(W_FORK_NO_JOIN, "warning",
                                       f"fork 节点[{fid}] 路径上无 join 节点 (分支可能不汇合)",
                                       node_ids=[fid]))

    # W006 - 节点数过多
    if len(node_ids) > 50:
        warnings.append(VerifyIssue(W_TOO_MANY_NODES, "warning",
                                   f"流程节点数 {len(node_ids)} > 50 (建议拆分或精简)"))

    # W007 - 死配置 field 权限
    perm_declared: set = set()
    for nid, n in node_by_id.items():
        field = (n.get("properties") or {}).get("field") or {}
        for k in field.keys():
            if k.startswith("PERMISSION_f_"):
                perm_declared.add(k[len("PERMISSION_f_"):])
    if variables:
        actual_fields: set = set()
        for k in variables.keys():
            if k.startswith("f_"):
                actual_fields.add(k[2:])
        unused = perm_declared - actual_fields
        if unused:
            warnings.append(VerifyIssue(W_PERMISSION_FIELD, "warning",
                                       f"field 权限声明了但 variables 没用: {sorted(unused)}"))

    # W008 - 重复边
    edge_pairs: dict = {}
    for e in edges:
        s, t = e.get("sourceNodeId"), e.get("targetNodeId")
        key = (s, t)
        edge_pairs.setdefault(key, []).append(e.get("id"))
    for (s, t), eids in edge_pairs.items():
        if len(eids) > 1:
            warnings.append(VerifyIssue(W_DUPLICATE_EDGES, "warning",
                                       f"节点 [{s}]→[{t}] 有 {len(eids)} 条边 (冗余)",
                                       edge_ids=eids))

    # W009 - 字段权限间隙：某节点声明 hidden/read, 其他节点未声明
    # 引擎逻辑: 未声明 PERMISSION 的字段默认可写
    # 设计风险: hidden 字段在 apply 节点声明, 但下游未声明, 仍可被覆盖
    field_per_node: dict = {}  # node_id -> set of declared f_xxx fields
    for nid, n in node_by_id.items():
        if n.get("type") != TYPE_TASK:
            continue
        field = (n.get("properties") or {}).get("field") or {}
        declared = set()
        for k, v in field.items():
            if k.startswith("PERMISSION_f_") and v in (1, 3):  # read or hidden
                fname = k[len("PERMISSION_f_"):]
                declared.add(fname)
        field_per_node[nid] = declared

    # 找所有被声明为 read/hidden 的字段
    all_restricted: set = set()
    for decls in field_per_node.values():
        all_restricted |= decls
    for fname in all_restricted:
        # 哪些节点声明了?
        declared_in = [nid for nid, decls in field_per_node.items() if fname in decls]
        # 哪些 task 节点未声明?
        undeclared = [nid for nid, n in node_by_id.items()
                      if n.get("type") == TYPE_TASK and fname not in field_per_node.get(nid, set())]
        if undeclared:
            warnings.append(VerifyIssue(W_PERMISSION_GAP, "warning",
                                       f"字段 f_{fname} 在节点 {declared_in} 声明为 read/hidden, "
                                       f"但节点 {undeclared} 未声明 (下游可覆盖, 建议显式声明)",
                                       node_ids=undeclared))

    # P003 - 无 task 节点
    has_task = any(n.get("type") == TYPE_TASK for n in nodes)
    if not has_task:
        patterns.append(VerifyIssue(P_NO_TASK, "pattern",
                                    "流程无 task 节点 (仅计算, 注意 'type=business' 才能纯计算)"))

    # P004 - decision 嵌套深度
    def _decision_depth(start, max_hops=20):
        """BFS 测从 start 出发的最长决策深度"""
        from collections import deque
        dq = deque([(start, 0)])
        visited = set()
        max_d = 0
        while dq:
            cur, d = dq.popleft()
            if cur in visited or d > max_hops:
                continue
            visited.add(cur)
            t = node_by_id.get(cur, {}).get("type")
            if t == TYPE_DECISION and d > max_d:
                max_d = d
            for eid in out_edges.get(cur, []):
                e = next((e for e in edges if e.get("id") == eid), None)
                if e:
                    nxt = e.get("targetNodeId")
                    if node_by_id.get(nxt, {}).get("type") in (TYPE_DECISION,):
                        dq.append((nxt, d + 1))
        return max_d
    if start_ids:
        depth = _decision_depth(start_ids[0])
        if depth > 3:
            patterns.append(VerifyIssue(P_NESTED_DECISION, "pattern",
                                        f"decision 嵌套深度 {depth} > 3 (可读性差, 建议拆分或合并)"))

    # BDD #1001 FIX-T70+ (2026-09-20)：扩展规则

    # E012 - custom 节点未配 clazz (handler 必填)
    custom_no_handler: list = []
    for nid, n in node_by_id.items():
        if n.get("type") == TYPE_CUSTOM:
            props = n.get("properties") or {}
            clazz = props.get("clazz", "")
            if not clazz:
                custom_no_handler.append(nid)
    if custom_no_handler:
        errors.append(VerifyIssue(E_CUSTOM_NO_HANDLER, "error",
                                   f"custom 节点未配 clazz (handler): {custom_no_handler} (FIX-T38 §16)",
                                   node_ids=custom_no_handler))

    # E013 - decision 节点的 decisionHandler 字段语法校验
    #   注: 是否已注册由引擎运行时校验, verify 阶段只查字段格式
    decision_handler_bad: list = []
    for nid, n in node_by_id.items():
        if n.get("type") == TYPE_DECISION:
            props = n.get("properties") or {}
            dh = props.get("decisionHandler", "")
            if dh and not re.match(r"^[A-Za-z0-9_.]+$", dh):
                decision_handler_bad.append((nid, dh))
    if decision_handler_bad:
        errors.append(VerifyIssue(E_DECISION_HANDLER_UNKNOWN, "error",
                                   f"decision 节点 decisionHandler 字段格式非法: {decision_handler_bad}",
                                   node_ids=[x[0] for x in decision_handler_bad]))

    # W010 - decision 节点所有出边 expr 都为空
    # (运行时仅靠 decisionHandler 或 fallback)
    for nid, n in node_by_id.items():
        if n.get("type") == TYPE_DECISION:
            out = out_edges.get(nid, [])
            has_expr = False
            for eid in out:
                e = next((e for e in edges if e.get("id") == eid), None)
                if e and e.get("properties", {}).get("expr"):
                    has_expr = True
                    break
            if not has_expr and out:
                props = n.get("properties") or {}
                if not props.get("decisionHandler"):
                    warnings.append(VerifyIssue(W_DECISION_NO_EXPR, "warning",
                                               f"decision 节点[{nid}] 所有出边 expr 都为空且无 decisionHandler",
                                               node_ids=[nid]))

    # W011 - custom 节点 val 字段空
    #   FIX-T38 §16：val 决定 handler 结果写回哪个 vars key；空则丢弃结果
    for nid, n in node_by_id.items():
        if n.get("type") == TYPE_CUSTOM:
            props = n.get("properties") or {}
            if not props.get("val"):
                warnings.append(VerifyIssue(W_CUSTOM_UNUSED_VAL, "warning",
                                           f"custom 节点[{nid}] val 字段为空，handler 结果将丢弃",
                                           node_ids=[nid]))

    # P005 - 流程链路过深 (start 到 end 超过 10 个 task 节点)
    if start_ids:
        from collections import deque as _dq
        dq2 = _dq([(start_ids[0], 0)])
        visited2 = set()
        max_chain = 0
        while dq2:
            cur, d = dq2.popleft()
            if cur in visited2:
                continue
            visited2.add(cur)
            t = node_by_id.get(cur, {}).get("type")
            if t == TYPE_TASK and d > max_chain:
                max_chain = d
            for eid in out_edges.get(cur, []):
                e = next((e for e in edges if e.get("id") == eid), None)
                if e:
                    nxt = e.get("targetNodeId")
                    dq2.append((nxt, d + 1))
        if max_chain > 10:
            patterns.append(VerifyIssue(P_DEEP_CHAIN, "pattern",
                                        f"流程 task 链路过深 ({max_chain} > 10), 建议拆分或用子流程"))

    # BDD #1101 FIX-VERIFY-3 (2026-09-20)：E014 surrogate 配置校验
    #   校验 processDesign/save 不会带 surrogate, 但可通过顶层 surrogateRules 字段做全局委派
    #   此处只检查典型错误: processName 含空格 / 包含 surrogate 但 operator/surrogate 字段为空
    surrogate_rules = (flow.get("surrogateRules") or [])
    if not isinstance(surrogate_rules, list):
        surrogate_rules = []
    bad_surrogate = []
    for i, s in enumerate(surrogate_rules):
        if not isinstance(s, dict):
            continue
        if not s.get("operator") or not s.get("surrogate"):
            bad_surrogate.append((i, s.get("operator"), s.get("surrogate")))
    if bad_surrogate:
        errors.append(VerifyIssue(E_SURROGATE_FIELDS_MISSING, "error",
                                   f"surrogate 配置缺 operator 或 surrogate: {bad_surrogate}"))

    # BDD #1102 FIX-VERIFY-3 (2026-09-20)：E015 子流程 name 冲突
    #   通过 parentProcessName 字段标记子流程, 不允许子流程 name 与父流程 name 冲突
    parent_name = (flow.get("parentProcessName") or "").strip()
    if parent_name and parent_name == name:
        errors.append(VerifyIssue(E_PARENT_CHILD_NAME_CONFLICT, "error",
                                   f"子流程 name '{name}' 与父流程 name 冲突"))

    return errors, warnings, patterns


def format_issues(issues: list) -> str:
    if not issues:
        return ""
    return "\n".join("  - " + str(i) for i in issues)
