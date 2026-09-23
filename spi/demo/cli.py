"""spi/demo CLI 数据接口 (重构 v26)

约定 (参见 SPEC §8): 必须导出以下 _data_* 函数 (返回纯 dict/list):
- _data_verify, _data_status, _data_list_users, _data_show_user,
  _data_list_depts, _data_show_dept

data.py (v6 原始) 不含 verify() 等高级功能, 这里使用基础 SPI_USERS / SPI_ROLE_TO_USERS 派生.

注: demo 数据简单 (无 deptId/level/email 字段), 集成视图字段会简化.
"""


def _data_verify() -> dict:
    """数据完整性基本检查 (简化版)

    demo 数据简单, 只做 C1 跨表引用检查
    """
    from .data import SPI_USERS, SPI_ROLES, SPI_DICTS, SPI_ROLE_TO_USERS
    errors: list[str] = []
    warnings: list[str] = []

    # C1: 跨表引用
    user_ids = set(SPI_USERS.keys())
    role_codes = set(SPI_ROLES.keys())
    for role_code, uids in SPI_ROLE_TO_USERS.items():
        if role_code not in role_codes:
            errors.append(f"ROLE_TO_USERS[{role_code}] 不在 SPI_ROLES")
        for uid in uids:
            if uid not in user_ids:
                errors.append(f"ROLE_TO_USERS[{role_code}] 引用未注册 user={uid}")

    # 计算 (dept, role) 组合数
    users_with_dept = [u for u in SPI_USERS.values() if u.get("deptId")]
    user_to_dept = {uid: u.get("deptId") for uid, u in SPI_USERS.items()}
    dept_role_count = 0
    seen_keys: set[tuple[str, str]] = set()
    for role_code, uids in SPI_ROLE_TO_USERS.items():
        for uid in uids:
            dept_id = user_to_dept.get(uid)
            if dept_id and (dept_id, role_code) not in seen_keys:
                seen_keys.add((dept_id, role_code))
                dept_role_count += 1

    # 简单统计
    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "users": len(SPI_USERS),
            "roles": len(SPI_ROLES),
            "dicts": len(SPI_DICTS),
            "depts": len(set(SPI_USERS[u].get("deptId", "") for u in SPI_USERS if SPI_USERS[u].get("deptId"))),
            "role_to_users_keys": len(SPI_ROLE_TO_USERS),
            "users_by_dept_role_count": dept_role_count,
        },
    }


def _data_status() -> dict:
    """SPI 数据概况 (复用 verify().summary)"""
    return _data_verify()


def _data_list_users() -> list[dict]:
    """列出所有用户 (uid, name, post, dept_id, roles)

    注: demo 用户字段简单 (只有 name + post, 部分有 deptId)
    """
    from .data import SPI_USERS, SPI_ROLE_TO_USERS

    # 反向: uid → roles
    user_roles: dict[str, list[str]] = {}
    for role_code, uids in SPI_ROLE_TO_USERS.items():
        for uid in uids:
            user_roles.setdefault(uid, []).append(role_code)

    result = []
    for uid in sorted(SPI_USERS.keys()):
        user = SPI_USERS[uid]
        result.append({
            "uid": uid,
            "name": user.get("name", ""),
            "post": user.get("post", ""),
            "level": "",  # demo 无 level 字段
            "dept_id": user.get("deptId", ""),
            "roles": user_roles.get(uid, []),
        })
    return result


def _data_show_user(uid: str) -> dict | None:
    """获取用户完整信息 (demo 简化版)

    注: demo 用户字段少, 集成视图字段会简化 (无 leader_chain / colleagues)
    """
    from .data import SPI_USERS, SPI_ROLE_TO_USERS

    if uid not in SPI_USERS:
        return None

    user = SPI_USERS[uid]
    roles = []
    for role_code, uids in SPI_ROLE_TO_USERS.items():
        if uid in uids:
            roles.append(role_code)

    # 从 ROLE_TO_USERS 反查主部门
    dept_id = user.get("deptId", "")

    return {
        "uid": uid,
        "name": user.get("name", ""),
        "post": user.get("post", ""),
        "dept_id": dept_id,
        "dept_name": dept_id,  # demo 无 dept 名映射
        "leader": user.get("leader", ""),
        "roles": roles,
    }


def _data_list_depts() -> list[dict]:
    """列出所有部门 (从 USERS.deptId 推导)

    注: demo 无独立 DEPTS.json, 部门从 USERS.deptId 聚合
    """
    from .data import SPI_USERS, SPI_DEPT_LEADERS, SPI_DEPT_MAIN_LEADERS

    # 部门集合
    dept_ids = set()
    for u in SPI_USERS.values():
        d = u.get("deptId")
        if d:
            dept_ids.add(d)

    result = []
    for dept_id in sorted(dept_ids):
        # 统计成员
        members = [u for u, info in SPI_USERS.items() if info.get("deptId") == dept_id]
        leaders = SPI_DEPT_LEADERS.get(dept_id, [])
        main_leaders = SPI_DEPT_MAIN_LEADERS.get(dept_id, [])
        result.append({
            "dept_id": dept_id,
            "name": dept_id,  # demo 无 name 字段
            "size": len(members),
            "leader": leaders[0] if leaders else "",
            "main_leader": main_leaders[0] if main_leaders else "",
        })
    return result


def _data_show_dept(dept_id: str) -> dict | None:
    """获取部门完整信息 + 成员 (demo 简化版)"""
    from .data import SPI_USERS

    # 部门是否存在
    dept_ids = {u.get("deptId") for u in SPI_USERS.values() if u.get("deptId")}
    if dept_id not in dept_ids:
        return None

    # 成员
    members = [
        {"uid": uid, "name": info.get("name", ""), "post": info.get("post", ""), "dept_id": dept_id}
        for uid, info in SPI_USERS.items()
        if info.get("deptId") == dept_id
    ]

    return {
        "info": {
            "dept_id": dept_id,
            "name": dept_id,  # demo 无 name 字段
            "size": len(members),
        },
        "members": members,
    }