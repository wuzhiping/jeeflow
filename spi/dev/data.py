"""spi/dev/data.py · 动态数据加载 (代理模式 · 重构 v7)

设计动机:
- spi/__init__.py dispatcher 每次调用 SPI() 都 reload(_data_mod) + reload(agt)
- 但直接 `from spi.dev.data import SPI_USERS` 的模块, SPI_USERS 在 import 时就冻结了
- 数据变更后, 这种"直接调用"路径感知不到变更

本实现策略 (代理模式 Proxy Pattern):
- 用 __getattr__ 实现动态属性
- 每次访问 SPI_USERS 等, 检查 JSON mtime, 如变更则重新加载
- .py 函数仍可写 `from .data import SPI_USERS`, SPI_USERS 是模块级 proxy 对象
- 每次访问 SPI_USERS[key] 或 SPI_USERS.items() 等, 触发 __getattr__ 重新加载

对外 API 不变:
- SPI_USERS / SPI_ROLES / SPI_DICTS / SPI_ROLE_TO_USERS / SPI_DEPT_LEADERS / SPI_DEPT_MAIN_LEADERS / SPI_FIND_USER_BY_ROLE_DEPT
- 都仍是 dict 类型, 支持所有 dict 操作 (get / items / keys / __contains__ 等)
- dispatcher + 业务调用方无需修改

性能:
- mtime 未变 → 直接返回内存缓存 (O(1))
- mtime 变更 → 重新加载 JSON (O(file size))
- 首次访问 → 加载 + 缓存 (O(file size))

注意:
- spi/dev/jsons/ 路径通过 _JSON_DIR 计算 (相对 data.py 位置)
- mtime 通过 os.path.getmtime 获取
"""
import json
import os
import time

_BASE = os.path.dirname(os.path.abspath(__file__))
_JSON_DIR = os.path.join(_BASE, "jsons")


def _load_json(name: str) -> dict:
    """读取 JSON 文件 (同步 I/O, 仅在 mtime 变更时调用)"""
    path = os.path.join(_JSON_DIR, name)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# === JSON 文件路径常量 ===
_FILE_TO_PATH = {
    "SPI_USERS": "USERS.json",
    "SPI_ROLES": "ROLES.json",
    "SPI_DICTS": "DICTS.json",
    "SPI_ROLE_TO_USERS": "ROLE_TO_USERS.json",
    "SPI_DEPT_LEADERS": "DEPTS.json",       # 派生 (从 DEPTS 推导)
    "SPI_DEPT_MAIN_LEADERS": "DEPTS.json",  # 派生
    "SPI_FIND_USER_BY_ROLE_DEPT": "DEPTS.json",  # 派生
    "SPI_DEPTS_TREE": "DEPTS.json",         # 派生 (v9 tree, 替换 v8 LEV)
    "SPI_USERS_BY_DEPT": "USERS.json",      # 派生 (v11 部门导航)
    "SPI_DEPT_LEADER_BY_USER": "USERS.json",  # 派生 (v11 部门导航, 跨文件)
    "SPI_DEPT_ANCESTORS": "DEPTS.json",     # 派生 (v12 树遍历·上溯)
    "SPI_DEPT_DESCENDANTS": "DEPTS.json",   # 派生 (v12 树遍历·下钻)
    "SPI_DEPT_MAIN_LEADER_BY_USER": "USERS.json",  # 派生 (v13 用户视角, 跨文件)
    "SPI_USER_DEPT_CHAIN": "USERS.json",    # 派生 (v13 用户视角, 跨文件)
    "SPI_USER_LEADER_CHAIN": "USERS.json",  # 派生 (v14 用户领导链, 跨文件)
    "SPI_USERS_BY_LEVEL": "USERS.json",     # 派生 (v15 职级聚合)
    "SPI_USERS_BY_DEPT_ROLE": "USERS.json",  # 派生 (v27 二维聚合, 跨文件)
    "SPI_USER_DEPT_ROLE": "USERS.json",      # 派生 (v29 v27 反向, 跨文件)
    "SPI_USERS_FULL": "USERS.json",         # 派生 (v16 集成视图)
    "SPI_DEPT_FULL_INFO": "DEPTS.json",     # 派生 (v17 部门集成视图)
    "SPI_DEPT_MEMBERS_FULL": "USERS.json",  # 派生 (v19 部门成员完整视图)
    "SPI_USERS_WITH_ROLES": "ROLE_TO_USERS.json",  # 派生 (v23 用户角色反向)
}

# === JSON 顶层 wrapper key (v6 嵌套化) ===
_WRAPPER_KEYS = {
    "SPI_USERS": "users",
    "SPI_ROLES": "roles",
    "SPI_DICTS": "dicts",
    "SPI_ROLE_TO_USERS": "role_to_users",
    "SPI_DEPT_LEADERS": "departments",
    "SPI_DEPT_MAIN_LEADERS": "departments",
    "SPI_FIND_USER_BY_ROLE_DEPT": "departments",
    "SPI_DEPTS_TREE": "departments",        # v9 tree
    "SPI_USERS_BY_DEPT": "users",           # v11 部门导航
    "SPI_DEPT_LEADER_BY_USER": "users",     # v11 部门导航
    "SPI_DEPT_ANCESTORS": "departments",    # v12 树遍历
    "SPI_DEPT_DESCENDANTS": "departments",  # v12 树遍历
    "SPI_DEPT_MAIN_LEADER_BY_USER": "users",  # v13 用户视角
    "SPI_USER_DEPT_CHAIN": "users",         # v13 用户视角
    "SPI_USER_LEADER_CHAIN": "users",       # v14 用户领导链
    "SPI_USERS_BY_LEVEL": "users",          # v15 职级聚合
    "SPI_USERS_BY_DEPT_ROLE": "users",       # v27 二维聚合
    "SPI_USER_DEPT_ROLE": "users",         # v29 v27 反向
    "SPI_USERS_FULL": "users",              # v16 集成视图
    "SPI_DEPT_FULL_INFO": "departments",     # v17 部门集成视图
    "SPI_DEPT_MEMBERS_FULL": "users",       # v19 部门成员完整视图
    "SPI_USERS_WITH_ROLES": "role_to_users",  # v23 用户角色反向
}


# === mtime 缓存 + 数据缓存 ===
_mtime_cache: dict = {}     # {name: (mtime, data)}
_data_cache: dict = {}


def _get_fresh(name: str, wrapper_key: str = None) -> dict:
    """获取最新数据, mtime 变化时自动重新加载"""
    path = os.path.join(_JSON_DIR, _FILE_TO_PATH[name])
    mtime = os.path.getmtime(path)

    if name in _mtime_cache:
        cached_mtime, cached_data = _mtime_cache[name]
        if cached_mtime == mtime:
            return cached_data  # mtime 未变, 缓存命中

    # mtime 变更或首次访问, 重新加载
    raw = _load_json(_FILE_TO_PATH[name])
    if wrapper_key:
        data = raw.get(wrapper_key, raw)
    else:
        data = raw

    _mtime_cache[name] = (mtime, data)
    _data_cache[name] = data
    return data


def _build_dept_leaders(depts: dict) -> dict:
    """派生 SPI_DEPT_LEADERS (扁平结构保持兼容)"""
    return {
        dept_id: [dept["leader"]]
        for dept_id, dept in depts.items()
        if dept.get("leader")
    }


def _build_dept_main_leaders(depts: dict) -> dict:
    """派生 SPI_DEPT_MAIN_LEADERS"""
    return {
        dept_id: [dept["main_leader"]]
        for dept_id, dept in depts.items()
        if dept.get("main_leader")
    }


def _build_find_user_by_role_dept(depts: dict) -> dict:
    """派生 SPI_FIND_USER_BY_ROLE_DEPT (旧嵌套结构兼容)"""
    return {
        "functions": {
            "find_user_by_role_dept": {
                f"{dept_id}:{role_code}": uids
                for dept_id, dept in depts.items()
                for role_code, uids in dept.get("role_combinations", {}).items()
            }
        }
    }


def _build_dept_tree(depts: dict) -> dict:
    """派生 SPI_DEPTS_TREE (重构 v9 · 替换 v8 LEV)

    扁平存储 + 递归构建嵌套 tree:
    - 顶层节点 (parent_id=None) 作为 SPI_DEPTS_TREE 的 key
    - 每个节点包含 children: {child_dept_id: {...递归...}}

    返回: {root_dept_id: {name, leader, main_leader, children: {...递归...}}}
    """
    # 1. 先创建每个部门的"骨架" (不含 children)
    nodes = {
        dept_id: {
            "name": dept.get("name"),
            "leader": dept.get("leader"),
            "main_leader": dept.get("main_leader"),
            "children": {},
        }
        for dept_id, dept in depts.items()
    }
    # 2. 递归: 找到每个部门的 parent, 把节点挂到 parent.children
    tree = {}
    for dept_id, dept in depts.items():
        parent_id = dept.get("parent_id")
        if parent_id is None:
            tree[dept_id] = nodes[dept_id]
        else:
            nodes[parent_id]["children"][dept_id] = nodes[dept_id]
    return tree


def _build_users_by_dept(users: dict) -> dict:
    """派生 SPI_USERS_BY_DEPT (重构 v11 · 部门导航)

    按 USERS.deptId 聚合, 返回 {dept_id: [uids]}

    注: USERS.deptId 为空的 uid 不会出现在结果中 (无部门归属)
    """
    result: dict[str, list[str]] = {}
    for uid, user in users.items():
        dept_id = user.get("deptId")
        if not dept_id:
            continue
        result.setdefault(dept_id, []).append(uid)
    return result


def _build_users_by_level(users: dict) -> dict:
    """派生 SPI_USERS_BY_LEVEL (重构 v15 · 职级聚合)

    按 USERS.level 聚合, 返回 {level: [uids]}

    - level 通常为 P5-P10 (职级代码)
    - 注: USERS.level 为空的 uid 不会出现在结果中

    用途:
    - 找所有 P5 工程师 (校招/转正)
    - 找所有 P8+ 领导 (决策权范围)
    - 与 SPI_USERS_BY_DEPT 复合查询 (如: D02 的 P5)
    """
    result: dict[str, list[str]] = {}
    for uid, user in users.items():
        level = user.get("level")
        if not level:
            continue
        result.setdefault(level, []).append(uid)
    return result


def _build_users_by_dept_role(users: dict) -> dict[tuple[str, str], list[str]]:
    """派生 SPI_USERS_BY_DEPT_ROLE (重构 v27 · 二维聚合)

    按 (dept_id, role_code) 聚合, 返回 {(dept_id, role_code): [uids]}

    算法:
    - 从 ROLE_TO_USERS 遍历每个 (role, uid) 对
    - 用 USERS[uid].deptId 获取 uid 的 dept_id (跳过空值)
    - 仅包含 ROLE_TO_USERS 中出现的 (dept, role) 组合

    用途:
    - "D02 所有 tech_lead": SPI_USERS_BY_DEPT_ROLE[("D02", "tech_lead")]
    - "所有 senior_engineer": 遍历 keys 找 role="senior_engineer"
    - dept × role 矩阵 (1 次 lookup)

    局限:
    - 仅 ROLE_TO_USERS 出现的 (dept, role)
    - DEPTS.role_combinations 字段未参与 (与 v18 C4 一致)
    """
    role_to_users = _get_fresh("SPI_ROLE_TO_USERS", "role_to_users")

    result: dict[tuple[str, str], list[str]] = {}
    for role_code, uids in role_to_users.items():
        for uid in uids:
            dept_id = users.get(uid, {}).get("deptId")
            if not dept_id:
                continue
            key = (dept_id, role_code)
            result.setdefault(key, []).append(uid)
    return result


def _build_user_dept_role() -> dict[str, list[tuple[str, str]]]:
    """派生 SPI_USER_DEPT_ROLE (重构 v29 · v27 反向)

    返回: {uid: [(dept_id, role_code), ...]}

    同一用户可有多个 (dept, role) (来自 ROLE_TO_USERS 多个角色)

    用途:
    - "周磊的所有 (dept, role)": SPI_USER_DEPT_ROLE["u_fe_eng"]
    - "周磊是 tech_lead 吗? 在哪个部门?": 检查 ("D02", "tech_lead") in list
    - 与 v27 SPI_USERS_BY_DEPT_ROLE 互逆 (uid ∈ keys 中所有 (dept, role) 的 value)

    局限:
    - 仅 ROLE_TO_USERS 出现的 (dept, role)
    - 跳过 deptId 为空的 uid
    """
    role_to_users = _get_fresh("SPI_ROLE_TO_USERS", "role_to_users")
    users = _get_fresh("SPI_USERS", "users")

    result: dict[str, list[tuple[str, str]]] = {}
    for role_code, uids in role_to_users.items():
        for uid in uids:
            dept_id = users.get(uid, {}).get("deptId")
            if not dept_id:
                continue
            result.setdefault(uid, []).append((dept_id, role_code))
    return result


def _build_users_full() -> dict:
    """派生 SPI_USERS_FULL (重构 v16 · 集成视图)

    组合 v11-v15 + USERS 基础, 返回 {uid: rich_dict}

    rich_dict 字段:
    - SPI_USERS 全部字段 (userId, name, post, deptId, level, email)
    - dept_name: 部门名 (v9 SPI_DEPTS_TREE)
    - leader: 组长 uid (v11 SPI_DEPT_LEADER_BY_USER)
    - main_leader: 主管 uid (v13 SPI_DEPT_MAIN_LEADER_BY_USER)
    - dept_chain: 部门链路 [self, ..., root] (v13 SPI_USER_DEPT_CHAIN)
    - leader_chain: 领导链路 [leader, ..., root_leader] (v14 SPI_USER_LEADER_CHAIN)
    - colleagues: 同部门其他人 (除自己) (派生)

    注:
    - USERS.deptId 为空 → uid 不出现
    - 部分字段可能为 None (dept 缺 leader 等)
    - 一次性组装, 后续访问无需多跳查询
    """
    depts = _get_fresh("SPI_DEPT_LEADERS", "departments")
    name_of: dict[str, str] = {
        dept_id: dept["name"]
        for dept_id, dept in depts.items()
    }
    users = _get_fresh("SPI_USERS", "users")
    by_dept = _build_users_by_dept(users)
    leaders = _build_dept_leader_by_user()
    main_leaders = _build_dept_main_leader_by_user()
    dept_chains = _build_user_dept_chain()
    leader_chains = _build_user_leader_chain()

    result: dict[str, dict] = {}
    for uid, user in users.items():
        dept_id = user.get("deptId")
        if not dept_id:
            continue
        # 同部门其他人 (除自己)
        colleagues = [u for u in by_dept.get(dept_id, []) if u != uid]
        result[uid] = {
            **user,
            "dept_name": name_of.get(dept_id),
            "leader": leaders.get(uid),
            "main_leader": main_leaders.get(uid),
            "dept_chain": dept_chains.get(uid, []),
            "leader_chain": leader_chains.get(uid, []),
            "colleagues": colleagues,
        }
    return result


def _build_dept_full_info() -> dict:
    """派生 SPI_DEPT_FULL_INFO (重构 v17 · 部门集成视图)

    组合 v9, v11-v16, 返回 {dept_id: rich_dict}

    rich_dict 字段:
    - name / parent_id / leader / main_leader: 部门基础
    - members: 部门所有 uid (v11 SPI_USERS_BY_DEPT)
    - size: 成员数
    - level_distribution: {level: count} (v15 SPI_USERS_BY_LEVEL 聚合)
    - ancestors: 上溯链路 [self, ..., root] (v12 SPI_DEPT_ANCESTORS)
    - descendants: 下钻链 [self, ..., leaf] (v12 SPI_DEPT_DESCENDANTS)
    - is_leaf: 是否叶子节点 (无 descendants)
    - depth: 在树中的深度 (root=1)

    注:
    - 所有部门都出现 (即使空 members)
    - members 空时 size=0
    """
    depts = _get_fresh("SPI_DEPT_LEADERS", "departments")
    users = _get_fresh("SPI_USERS", "users")
    by_dept = _build_users_by_dept(users)
    by_level = _build_users_by_level(users)
    ancestors_map = _build_dept_ancestors()
    descendants_map = _build_dept_descendants()

    result: dict[str, dict] = {}
    for dept_id, dept in depts.items():
        members = by_dept.get(dept_id, [])
        # 按 level 统计部门成员
        level_dist: dict[str, int] = {}
        for uid in members:
            level = users[uid].get("level")
            if level:
                level_dist[level] = level_dist.get(level, 0) + 1
        ancestors = ancestors_map.get(dept_id, [dept_id])
        descendants = descendants_map.get(dept_id, [dept_id])
        result[dept_id] = {
            "name": dept.get("name"),
            "parent_id": dept.get("parent_id"),
            "leader": dept.get("leader"),
            "main_leader": dept.get("main_leader"),
            "members": members,
            "size": len(members),
            "level_distribution": level_dist,
            "ancestors": ancestors,
            "descendants": descendants,
            "is_leaf": len(descendants) == 1,
            "depth": len(ancestors),
        }
    return result


def _build_dept_members_full() -> dict:
    """派生 SPI_DEPT_MEMBERS_FULL (重构 v19 · 部门成员完整视图)

    组合 v16 + v17: 每个部门成员用 SPI_USERS_FULL 展开

    返回: {dept_id: [user_full_dict, ...]}

    用途:
    - 部门详情页: 显示所有成员完整档案
    - 部门通知: 一键获取所有成员邮箱
    - 部门统计: 自动汇总 (level, leader_chain 等)

    注:
    - 包含所有部门 (空部门为 [])
    - members 顺序来自 SPI_USERS_BY_DEPT
    - 复用 SPI_USERS_FULL (DRY)
    """
    users_full = _build_users_full()
    by_dept = _build_users_by_dept(_get_fresh("SPI_USERS", "users"))
    dept_info = _build_dept_full_info()

    result: dict[str, list[dict]] = {}
    for dept_id in dept_info:
        member_uids = by_dept.get(dept_id, [])
        result[dept_id] = [
            users_full[uid] for uid in member_uids if uid in users_full
        ]
    return result


def _build_users_with_roles() -> dict:
    """派生 SPI_USERS_WITH_ROLES (重构 v23 · 用户角色反向)

    反向映射 ROLE_TO_USERS: {uid: [role_codes, ...]}

    返回: {uid: [role_code1, role_code2, ...]}

    用途:
    - 查 "周磊的所有角色"
    - 多角色用户审计
    - 与 SPI_USERS_FULL 组合显示完整身份

    注:
    - 仅在 ROLE_TO_USERS 中出现的 uid 被包含
    - 角色列表按 ROLE_TO_USERS 的 key 顺序 (JSON dict order)
    """
    role_to_users = _get_fresh("SPI_ROLE_TO_USERS", "role_to_users")
    result: dict[str, list[str]] = {}
    for role_code, uids in role_to_users.items():
        for uid in uids:
            result.setdefault(uid, []).append(role_code)
    return result


def _build_dept_leader_by_user() -> dict:
    """派生 SPI_DEPT_LEADER_BY_USER (重构 v11 · 部门导航)

    3 跳查找: uid → USERS.deptId → SPI_DEPT_LEADERS[dept_id][0]

    返回: {uid: leader_uid}

    注:
    - USERS.deptId 为空 → uid 不出现在结果中
    - dept 缺 leader → uid 不出现在结果中 (SPI_DEPT_LEADERS 派生过滤)
    - 跳过字符串空值 (与 verify 一致)
    """
    depts = _get_fresh("SPI_DEPT_LEADERS", "departments")
    # 用原始 depts 构建 leader 映射 (覆盖所有部门, 包括 leader 为空的)
    leader_of: dict[str, str] = {
        dept_id: dept["leader"]
        for dept_id, dept in depts.items()
        if dept.get("leader")
    }
    users = _get_fresh("SPI_USERS", "users")
    return {
        uid: leader_of[user["deptId"]]
        for uid, user in users.items()
        if user.get("deptId") and user["deptId"] in leader_of
    }


def _build_dept_ancestors() -> dict:
    """派生 SPI_DEPT_ANCESTORS (重构 v12 · 树遍历 · 上溯)

    返回: {dept_id: [self, parent, ..., root]}

    - 含自身 (索引 0)
    - root 部门: [root_dept_id] (单元素)
    - 孤立部门 (parent_id 指向不存在的 dept): 截断到当前, 不再向上
    - 防环 (parent_id 形成回路时截断)
    """
    depts = _get_fresh("SPI_DEPT_LEADERS", "departments")
    parent_of = {dept_id: dept.get("parent_id") for dept_id, dept in depts.items()}

    result: dict[str, list[str]] = {}
    for dept_id in depts:
        chain: list[str] = []
        current = dept_id
        seen: set[str] = set()
        while current is not None and current not in seen:
            chain.append(current)
            seen.add(current)
            parent = parent_of.get(current)
            if parent is None or parent not in depts:
                break  # 孤立或 root, 停止
            current = parent
        result[dept_id] = chain
    return result


def _build_dept_descendants() -> dict:
    """派生 SPI_DEPT_DESCENDANTS (重构 v12 · 树遍历 · 下钻)

    返回: {dept_id: [self, child1, child2, ..., leaf_dept_ids]}

    - 含自身 (索引 0)
    - 叶子部门: [dept_id] (单元素)
    - 深度优先遍历 (与 v9 SPI_DEPTS_TREE 的 children 顺序一致)
    - 防环 (出现 parent_id 环时仍可正常下钻, 上溯已截断)
    """
    depts = _get_fresh("SPI_DEPT_LEADERS", "departments")
    # 1. 构建 parent_id → [child_dept_ids] 反向索引
    children_of: dict[str, list[str]] = {dept_id: [] for dept_id in depts}
    for dept_id, dept in depts.items():
        parent_id = dept.get("parent_id")
        if parent_id and parent_id in children_of:
            children_of[parent_id].append(dept_id)

    # 2. 深度优先收集 (parent_id 环时, visited 切断递归, 避免 stack overflow)
    def collect(start: str, visited: set[str] | None = None) -> list[str]:
        if visited is None:
            visited = set()
        visited = visited | {start}  # 不可变, 防共享污染
        result: list[str] = [start]
        for child in children_of.get(start, []):
            if child in visited:
                continue  # 跳过已访问, 防止环递归
            result.extend(collect(child, visited))
        return result

    return {dept_id: collect(dept_id) for dept_id in depts}


def _build_dept_main_leader_by_user() -> dict:
    """派生 SPI_DEPT_MAIN_LEADER_BY_USER (重构 v13 · 用户视角)

    3 跳查找: uid → USERS.deptId → SPI_DEPT_MAIN_LEADERS[dept_id][0]

    返回: {uid: main_leader_uid}

    注:
    - USERS.deptId 为空 → uid 不出现
    - dept 缺 main_leader → uid 不出现
    - 跳过字符串空值 (与 verify 一致)
    """
    depts = _get_fresh("SPI_DEPT_LEADERS", "departments")
    # 用原始 depts 构建 main_leader 映射 (覆盖所有部门)
    main_leader_of: dict[str, str] = {
        dept_id: dept["main_leader"]
        for dept_id, dept in depts.items()
        if dept.get("main_leader")
    }
    users = _get_fresh("SPI_USERS", "users")
    return {
        uid: main_leader_of[user["deptId"]]
        for uid, user in users.items()
        if user.get("deptId") and user["deptId"] in main_leader_of
    }


def _build_user_dept_chain() -> dict:
    """派生 SPI_USER_DEPT_CHAIN (重构 v13 · 用户视角)

    2 跳组合: uid → USERS.deptId → SPI_DEPT_ANCESTORS[deptId]

    返回: {uid: [dept_id, parent_dept_id, ..., root_dept_id]}

    注:
    - USERS.deptId 为空 → uid 不出现
    - 复用 v12 SPI_DEPT_ANCESTORS (自动继承环/悬空截断)
    """
    users = _get_fresh("SPI_USERS", "users")
    ancestors = _build_dept_ancestors()
    return {
        uid: ancestors[user["deptId"]]
        for uid, user in users.items()
        if user.get("deptId") and user["deptId"] in ancestors
    }


def _build_user_leader_chain() -> dict:
    """派生 SPI_USER_LEADER_CHAIN (重构 v14 · 用户完整领导链)

    组合 v13 SPI_USER_DEPT_CHAIN + 每 dept 的 leader:
    - 用户部门链路 → 每个 dept 的 leader → 去重后保留顺序

    返回: {uid: [leader_at_dept1, leader_at_dept2, ..., leader_at_root]}

    注:
    - 跳过 dept 空 leader (verify 独立报错)
    - 去重 (顶层 dept leader 可能 == 用户本人 leader)
    - 用户视角的"完整升级路径"
    """
    depts = _get_fresh("SPI_DEPT_LEADERS", "departments")
    # 用原始 depts 构建完整 leader 映射 (覆盖所有 dept, 包括空 leader 的)
    leader_of: dict[str, str] = {
        dept_id: dept["leader"]
        for dept_id, dept in depts.items()
        if dept.get("leader")
    }
    user_chain = _build_user_dept_chain()
    result: dict[str, list[str]] = {}
    for uid, dept_chain in user_chain.items():
        leaders: list[str] = []
        for dept_id in dept_chain:
            leader = leader_of.get(dept_id)
            if leader and leader not in leaders:
                leaders.append(leader)
        if leaders:
            result[uid] = leaders
    return result


# === 代理对象 (DictProxy) ===
class _DictProxy:
    """dict 代理: 每次访问触发 mtime 检查 + 可能的 reload

    公开 API:
    - dict 所有方法 (get, items, keys, values, __getitem__, __contains__, __iter__, __len__)
    - 比较操作 (==, !=)

    注意:
    - 直接 dict() 转换 (e.g., dict(proxy)) 返回新 dict, 不会触发 reload
    - 此时代理持有的 dict 是当前快照, 修改 JSON 后需要重新访问才会 reload
    """

    __slots__ = ("_name",)

    def __init__(self, name: str):
        # 直接绕过 __setattr__, 避免递归
        object.__setattr__(self, "_name", name)

    def _data(self) -> dict:
        """获取当前最新数据"""
        if self._name in ("SPI_DEPT_LEADERS", "SPI_DEPT_MAIN_LEADERS", "SPI_FIND_USER_BY_ROLE_DEPT", "SPI_DEPTS_TREE"):
            depts = _get_fresh("SPI_DEPT_LEADERS", "departments")
            if self._name == "SPI_DEPT_LEADERS":
                return _build_dept_leaders(depts)
            elif self._name == "SPI_DEPT_MAIN_LEADERS":
                return _build_dept_main_leaders(depts)
            elif self._name == "SPI_FIND_USER_BY_ROLE_DEPT":
                return _build_find_user_by_role_dept(depts)
            else:  # SPI_DEPTS_TREE
                return _build_dept_tree(depts)
        if self._name in ("SPI_DEPT_ANCESTORS", "SPI_DEPT_DESCENDANTS"):
            if self._name == "SPI_DEPT_ANCESTORS":
                return _build_dept_ancestors()
            return _build_dept_descendants()
        if self._name == "SPI_USERS_BY_DEPT":
            return _build_users_by_dept(_get_fresh("SPI_USERS", "users"))
        if self._name == "SPI_USERS_BY_LEVEL":
            return _build_users_by_level(_get_fresh("SPI_USERS", "users"))
        if self._name == "SPI_USERS_BY_DEPT_ROLE":
            return _build_users_by_dept_role(_get_fresh("SPI_USERS", "users"))
        if self._name == "SPI_USER_DEPT_ROLE":
            return _build_user_dept_role()
        if self._name == "SPI_USERS_FULL":
            return _build_users_full()
        if self._name == "SPI_DEPT_FULL_INFO":
            return _build_dept_full_info()
        if self._name == "SPI_DEPT_MEMBERS_FULL":
            return _build_dept_members_full()
        if self._name == "SPI_USERS_WITH_ROLES":
            return _build_users_with_roles()
        if self._name == "SPI_DEPT_LEADER_BY_USER":
            return _build_dept_leader_by_user()
        if self._name == "SPI_DEPT_MAIN_LEADER_BY_USER":
            return _build_dept_main_leader_by_user()
        if self._name == "SPI_USER_DEPT_CHAIN":
            return _build_user_dept_chain()
        if self._name == "SPI_USER_LEADER_CHAIN":
            return _build_user_leader_chain()
        return _get_fresh(self._name, _WRAPPER_KEYS.get(self._name))

    # dict-like 接口
    def __getitem__(self, key):
        return self._data()[key]

    def __contains__(self, key):
        return key in self._data()

    def __iter__(self):
        return iter(self._data())

    def __len__(self):
        return len(self._data())

    def __eq__(self, other):
        return self._data() == other

    def __ne__(self, other):
        return self._data() != other

    def __repr__(self):
        return repr(self._data())

    def get(self, key, default=None):
        return self._data().get(key, default)

    def items(self):
        return self._data().items()

    def keys(self):
        return self._data().keys()

    def values(self):
        return self._data().values()


# === 公开常量 (代理对象) ===
SPI_USERS: _DictProxy = _DictProxy("SPI_USERS")
SPI_ROLES: _DictProxy = _DictProxy("SPI_ROLES")
SPI_DICTS: _DictProxy = _DictProxy("SPI_DICTS")
SPI_ROLE_TO_USERS: _DictProxy = _DictProxy("SPI_ROLE_TO_USERS")
SPI_DEPT_LEADERS: _DictProxy = _DictProxy("SPI_DEPT_LEADERS")
SPI_DEPT_MAIN_LEADERS: _DictProxy = _DictProxy("SPI_DEPT_MAIN_LEADERS")
SPI_FIND_USER_BY_ROLE_DEPT: _DictProxy = _DictProxy("SPI_FIND_USER_BY_ROLE_DEPT")
SPI_DEPTS_TREE: _DictProxy = _DictProxy("SPI_DEPTS_TREE")  # v9 新增 (替换 v8 SPI_DEPTS_LEV)
SPI_USERS_BY_DEPT: _DictProxy = _DictProxy("SPI_USERS_BY_DEPT")  # v11 新增 (部门导航)
SPI_DEPT_LEADER_BY_USER: _DictProxy = _DictProxy("SPI_DEPT_LEADER_BY_USER")  # v11 新增 (部门导航)
SPI_DEPT_ANCESTORS: _DictProxy = _DictProxy("SPI_DEPT_ANCESTORS")  # v12 新增 (树遍历·上溯)
SPI_DEPT_DESCENDANTS: _DictProxy = _DictProxy("SPI_DEPT_DESCENDANTS")  # v12 新增 (树遍历·下钻)
SPI_DEPT_MAIN_LEADER_BY_USER: _DictProxy = _DictProxy("SPI_DEPT_MAIN_LEADER_BY_USER")  # v13 新增 (用户视角)
SPI_USER_DEPT_CHAIN: _DictProxy = _DictProxy("SPI_USER_DEPT_CHAIN")  # v13 新增 (用户视角)
SPI_USER_LEADER_CHAIN: _DictProxy = _DictProxy("SPI_USER_LEADER_CHAIN")  # v14 新增 (用户完整领导链)
SPI_USERS_BY_LEVEL: _DictProxy = _DictProxy("SPI_USERS_BY_LEVEL")  # v15 新增 (职级聚合)
SPI_USERS_BY_DEPT_ROLE: _DictProxy = _DictProxy("SPI_USERS_BY_DEPT_ROLE")  # v27 新增 (二维聚合)
SPI_USER_DEPT_ROLE: _DictProxy = _DictProxy("SPI_USER_DEPT_ROLE")  # v29 新增 (v27 反向)
SPI_USERS_FULL: _DictProxy = _DictProxy("SPI_USERS_FULL")  # v16 新增 (集成视图)
SPI_DEPT_FULL_INFO: _DictProxy = _DictProxy("SPI_DEPT_FULL_INFO")  # v17 新增 (部门集成视图)
SPI_DEPT_MEMBERS_FULL: _DictProxy = _DictProxy("SPI_DEPT_MEMBERS_FULL")  # v19 新增 (部门成员完整视图)
SPI_USERS_WITH_ROLES: _DictProxy = _DictProxy("SPI_USERS_WITH_ROLES")  # v23 新增 (用户角色反向)


# === 兼容旧调用方式 (直接 reload) ===
def reload_data():
    """手动触发数据重新加载 (用于测试 / 调试)

    使用场景:
    - 测试期间手动修改 JSON 后, 立即生效
    - 调试时强制刷新缓存

    注意:
    - 正常情况下不需要调用, mtime 检查会自动 reload
    """
    _mtime_cache.clear()
    _data_cache.clear()


# === 数据完整性校验 (重构 v10) ===
def _verify_cross_refs() -> tuple[list[str], list[str]]:
    """校验 C1: 跨表引用完整性

    返回 (errors, warnings)
    """
    errors: list[str] = []
    warnings: list[str] = []

    user_ids = set(SPI_USERS.keys())
    role_codes = set(SPI_ROLES.keys())
    # 注: 校验用 DEPTS 原始数据, 不用 SPI_DEPT_LEADERS (后者只含非空 leader 的部门)
    depts = _get_fresh("SPI_DEPT_LEADERS", "departments")
    dept_ids = set(depts.keys())

    # 1. DEPTS.role_combinations.uid ⊆ SPI_USERS
    for dept_id, dept in depts.items():
        for role_code, uids in dept.get("role_combinations", {}).items():
            for uid in uids:
                if uid not in user_ids:
                    errors.append(
                        f"DEPTS[{dept_id}].role_combinations[{role_code}] "
                        f"引用未注册的 user={uid}"
                    )
        if dept.get("leader") and dept["leader"] not in user_ids:
            errors.append(
                f"DEPTS[{dept_id}].leader={dept['leader']} 不在 SPI_USERS"
            )
        if dept.get("main_leader") and dept["main_leader"] not in user_ids:
            errors.append(
                f"DEPTS[{dept_id}].main_leader={dept['main_leader']} 不在 SPI_USERS"
            )

    # 2. USERS.deptId ⊆ DEPTS (None 或空字符串允许)
    for uid, user in _get_fresh("SPI_USERS", "users").items():
        dept_id = user.get("deptId")
        if dept_id and dept_id not in dept_ids:
            errors.append(
                f"USERS[{uid}].deptId={dept_id} 不在 DEPTS"
            )

    # 3. ROLE_TO_USERS.role ⊆ SPI_ROLES
    # 4. ROLE_TO_USERS.uid ⊆ SPI_USERS
    role_to_users = _get_fresh("SPI_ROLE_TO_USERS", "role_to_users")
    for role_code, uids in role_to_users.items():
        if role_code not in role_codes:
            errors.append(
                f"ROLE_TO_USERS[{role_code}] 不在 SPI_ROLES"
            )
            continue
        for uid in uids:
            if uid not in user_ids:
                errors.append(
                    f"ROLE_TO_USERS[{role_code}] 引用未注册的 user={uid}"
                )

    return errors, warnings


def _verify_tree() -> tuple[list[str], list[str]]:
    """校验 C2: tree 结构 (parent_id 无悬空 + 无环 + 全可达)

    返回 (errors, warnings)
    """
    errors: list[str] = []
    warnings: list[str] = []

    depts = _get_fresh("SPI_DEPT_LEADERS", "departments")
    dept_ids = set(depts.keys())

    # 1. parent_id 必须存在于 DEPTS (除 None / 空字符串)
    for dept_id, dept in depts.items():
        parent_id = dept.get("parent_id")
        if parent_id and parent_id not in dept_ids:
            errors.append(
                f"DEPTS[{dept_id}].parent_id={parent_id} 不存在"
            )

    # 2. 无环检测 (沿 parent_id 链追踪, 若回到起点则有环)
    def _has_cycle(start: str) -> bool:
        seen: set[str] = set()
        current = start
        while current is not None:
            if current in seen:
                return True
            seen.add(current)
            parent = depts.get(current, {}).get("parent_id")
            current = parent
        return False

    for dept_id in dept_ids:
        if _has_cycle(dept_id):
            errors.append(f"DEPTS[{dept_id}] 存在 parent_id 循环")

    # 3. 可达性: 所有部门是否可达某个 root (parent_id=None)
    def _root_of(dept_id: str) -> str | None:
        seen: set[str] = set()
        current = dept_id
        while current is not None:
            if current in seen:
                return None  # 有环, 已捕获
            seen.add(current)
            parent = depts.get(current, {}).get("parent_id")
            if parent is None:
                return current
            current = parent
        return None

    reachable: set[str] = set()
    for dept_id in dept_ids:
        root = _root_of(dept_id)
        if root is not None:
            reachable.add(root)

    roots = {d for d, info in depts.items() if info.get("parent_id") is None}
    unreachable_roots = roots - reachable
    for dept_id in unreachable_roots:
        warnings.append(f"DEPTS[{dept_id}] 是顶层部门但 parent_id 链异常")

    return errors, warnings


def _verify_completeness() -> tuple[list[str], list[str]]:
    """校验 C3: 完整性 (部门缺领导 / 角色未被使用)

    返回 (errors, warnings)
    """
    warnings: list[str] = []

    # 1. 部门缺 leader / main_leader
    depts = _get_fresh("SPI_DEPT_LEADERS", "departments")
    for dept_id, dept in depts.items():
        if not dept.get("leader"):
            warnings.append(f"DEPTS[{dept_id}] 缺少 leader")
        if not dept.get("main_leader"):
            warnings.append(f"DEPTS[{dept_id}] 缺少 main_leader")
        if not dept.get("role_combinations"):
            warnings.append(f"DEPTS[{dept_id}] 缺少 role_combinations")

    # 2. USERS.deptId 为空 → 数据残缺警告
    for uid, user in _get_fresh("SPI_USERS", "users").items():
        if not user.get("deptId"):
            warnings.append(f"USERS[{uid}].deptId 为空")

    # 2. 角色未被任何用户使用
    role_to_users = _get_fresh("SPI_ROLE_TO_USERS", "role_to_users")
    used_roles = set(role_to_users.keys())
    all_roles = set(SPI_ROLES.keys())
    unused_roles = all_roles - used_roles
    for role_code in sorted(unused_roles):
        warnings.append(f"ROLE[{role_code}] 未被任何用户使用")

    return [], warnings


def _verify_role_to_users_consistency() -> tuple[list[str], list[str]]:
    """校验 C4: ROLE_TO_USERS 一致性 (重构 v18)

    逻辑:
    - 从 DEPTS.role_combinations 推导 expected[role_code] = union of all depts' uids
    - 与实际 ROLE_TO_USERS[role_code] 对比
    - error: expected 有, actual 缺失 (用户应有此角色)
    - warning: expected 无, actual 多余 (角色分配与部门定义不符)

    返回 (errors, warnings)
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. 推导 expected (从 DEPTS.role_combinations)
    depts = _get_fresh("SPI_DEPT_LEADERS", "departments")
    expected: dict[str, set[str]] = {}
    for dept_id, dept in depts.items():
        for role_code, uids in dept.get("role_combinations", {}).items():
            expected.setdefault(role_code, set()).update(uids)

    # 2. 获取 actual
    actual_role_to_users = _get_fresh("SPI_ROLE_TO_USERS", "role_to_users")
    actual: dict[str, set[str]] = {
        role_code: set(uids)
        for role_code, uids in actual_role_to_users.items()
    }

    # 3. 对比
    all_roles = set(expected.keys()) | set(actual.keys())
    for role_code in sorted(all_roles):
        exp = expected.get(role_code, set())
        act = actual.get(role_code, set())

        missing = exp - act  # 应有但缺失
        extra = act - exp    # 多余

        if missing:
            errors.append(
                f"ROLE_TO_USERS[{role_code}] 缺失用户 (按 DEPTS 应有): "
                f"{sorted(missing)}"
            )
        if extra:
            warnings.append(
                f"ROLE_TO_USERS[{role_code}] 多余用户 (DEPTS 未定义): "
                f"{sorted(extra)}"
            )

    return errors, warnings


def search_users(query: str) -> list[str]:
    """用户搜索 (重构 v20 · 首个 helper 函数)

    支持字段: uid, name, post, email
    大小写不敏感, 子串匹配

    优先级 (返回顺序):
    1. uid 匹配
    2. name 匹配
    3. post 匹配
    4. email 匹配

    同一用户只出现一次 (按最早匹配字段计优先级)

    Args:
        query: 搜索字符串 (空返回空列表)

    Returns:
        匹配的 uid 列表

    用途:
    - UI 自动完成
    - 模糊查找用户
    - 后台管理快速定位
    """
    if not query:
        return []
    q = query.lower()
    users = _get_fresh("SPI_USERS", "users")
    results: list[str] = []
    for uid, user in users.items():
        # 1. uid 匹配
        if q in uid.lower():
            results.append(uid)
            continue
        # 2. name 匹配
        if q in user.get("name", "").lower():
            results.append(uid)
            continue
        # 3. post 匹配
        if q in user.get("post", "").lower():
            results.append(uid)
            continue
        # 4. email 匹配
        if q in user.get("email", "").lower():
            results.append(uid)
            continue
    return results


def search_depts(query: str) -> list[str]:
    """部门搜索 (重构 v21 · 对称 v20 search_users)

    支持字段: dept_id, name
    大小写不敏感, 子串匹配

    优先级 (返回顺序):
    1. dept_id 匹配
    2. name 匹配

    同一部门只出现一次 (按最早匹配字段计优先级)

    Args:
        query: 搜索字符串 (空返回空列表)

    Returns:
        匹配的 dept_id 列表

    用途:
    - UI 部门选择下拉框
    - 模糊查找部门
    - 与 SPI_DEPT_FULL_INFO 组合使用
    """
    if not query:
        return []
    q = query.lower()
    depts = _get_fresh("SPI_DEPT_LEADERS", "departments")
    results: list[str] = []
    for dept_id, dept in depts.items():
        # 1. dept_id 匹配
        if q in dept_id.lower():
            results.append(dept_id)
            continue
        # 2. name 匹配
        if q in dept.get("name", "").lower():
            results.append(dept_id)
            continue
    return results


def verify() -> dict:
    """数据完整性基本检查 (重构 v10 · 2026-11-17, v18 扩展)

    检查范围 (5 大类):
    - C1 跨表引用完整性 (DEPTS / USERS / ROLE_TO_USERS 互相引用)
    - C2 tree 结构 (parent_id 悬空 / 循环 / 可达性)
    - C3 完整性 (部门缺领导 / 角色未使用)
    - C4 ROLE_TO_USERS 一致性 (v18 新增)

    返回:
        {
            "ok": bool,           # errors 为空时 True
            "errors": list[str],  # 致命错误 (数据不可用)
            "warnings": list[str],  # 警告 (数据可用, 但有疑点)
            "summary": {
                "users": int,
                "roles": int,
                "depts": int,
                "role_to_users_keys": int,
                ...
            },
        }

    使用示例:
        >>> from spi.dev.data import verify
        >>> result = verify()
        >>> if not result["ok"]:
        ...     for err in result["errors"]:
        ...         print(f"❌ {err}")
    """
    errors: list[str] = []
    warnings: list[str] = []

    for check_fn in (_verify_cross_refs, _verify_tree, _verify_completeness, _verify_role_to_users_consistency):
        e, w = check_fn()
        errors.extend(e)
        warnings.extend(w)

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "users": len(SPI_USERS),
            "roles": len(SPI_ROLES),
            "depts": len(SPI_DEPT_LEADERS),
            "role_to_users_keys": len(SPI_ROLE_TO_USERS),
            "users_by_dept_keys": len(SPI_USERS_BY_DEPT),  # v11
            "dept_leader_by_user_count": len(SPI_DEPT_LEADER_BY_USER),  # v11
            "dept_ancestors_count": len(SPI_DEPT_ANCESTORS),  # v12
            "dept_descendants_count": len(SPI_DEPT_DESCENDANTS),  # v12
            "dept_main_leader_by_user_count": len(SPI_DEPT_MAIN_LEADER_BY_USER),  # v13
            "user_dept_chain_count": len(SPI_USER_DEPT_CHAIN),  # v13
            "user_leader_chain_count": len(SPI_USER_LEADER_CHAIN),  # v14
            "users_by_level_keys": len(SPI_USERS_BY_LEVEL),  # v15
            "users_by_dept_role_count": len(SPI_USERS_BY_DEPT_ROLE),  # v27
            "user_dept_role_count": len(SPI_USER_DEPT_ROLE),  # v29
            "users_full_count": len(SPI_USERS_FULL),  # v16
            "dept_full_info_count": len(SPI_DEPT_FULL_INFO),  # v17
            "dept_members_full_count": len(SPI_DEPT_MEMBERS_FULL),  # v19
            "users_with_roles_count": len(SPI_USERS_WITH_ROLES),  # v23
        },
    }