"""spi/dev CLI 数据接口 (重构 v26 实现层)

约定 (参见 SPEC §8): 必须导出以下 _data_* 函数 (返回纯 dict/list):
- _data_verify, _data_status, _data_list_users, _data_show_user,
  _data_list_depts, _data_show_dept

实现包 cli.py 仅暴露数据获取函数 (不做打印).
打印逻辑在 dispatcher 层 spi/cli.py 完成.

注: 也可通过 `python -m spi.dev.cli._print_verify()` 单独调试 (内部辅助).
"""


# === 数据获取函数 (CLI 与 API 共享) ===

def _data_verify() -> dict:
    """获取 verify() 结果 (CLI 与 API 共享)"""
    from .data import verify
    return verify()


def _data_status() -> dict:
    """获取 status 概况 (CLI 与 API 共享)"""
    from .data import verify
    return verify()


def _data_list_users() -> list[dict]:
    """获取用户列表 (CLI 与 API 共享)

    返回: 每用户 5 字段 (uid, name, post, dept_id, roles)
    """
    from .data import SPI_USERS, SPI_USERS_WITH_ROLES
    result = []
    for uid in sorted(SPI_USERS.keys()):
        user = SPI_USERS[uid]
        roles = SPI_USERS_WITH_ROLES.get(uid, [])
        result.append({
            "uid": uid,
            "name": user.get("name", ""),
            "post": user.get("post", ""),
            "level": user.get("level", ""),
            "dept_id": user.get("deptId", ""),
            "roles": roles,
        })
    return result


def _data_show_user(uid: str) -> dict | None:
    """获取用户完整信息 (CLI 与 API 共享)

    返回: SPI_USERS_FULL[uid] 字典, 或 None (uid 不存在)
    """
    from .data import SPI_USERS_FULL
    return SPI_USERS_FULL.get(uid)


def _data_list_depts() -> list[dict]:
    """获取部门列表 (CLI 与 API 共享)

    返回: 每部门 4 字段 (dept_id, name, size, leader, main_leader)
    """
    from .data import SPI_DEPT_FULL_INFO
    result = []
    for dept_id in sorted(SPI_DEPT_FULL_INFO.keys()):
        info = SPI_DEPT_FULL_INFO[dept_id]
        result.append({
            "dept_id": dept_id,
            "name": info.get("name", ""),
            "size": info.get("size", 0),
            "leader": info.get("leader") or "",
            "main_leader": info.get("main_leader") or "",
        })
    return result


def _data_show_dept(dept_id: str) -> dict | None:
    """获取部门完整信息 + 成员 (CLI 与 API 共享)

    返回: {info, members}, 或 None (dept_id 不存在)
    """
    from .data import SPI_DEPT_FULL_INFO, SPI_DEPT_MEMBERS_FULL
    if dept_id not in SPI_DEPT_FULL_INFO:
        return None
    return {
        "info": SPI_DEPT_FULL_INFO[dept_id],
        "members": SPI_DEPT_MEMBERS_FULL.get(dept_id, []),
    }


# === 向后兼容: 直接 CLI 调用 (python -m spi.dev.cli) ===

def _print_verify() -> int:
    """打印 verify 结果 (向后兼容)"""
    import sys
    result = _data_verify()
    print("=== spi/dev verify ===")
    print(f"ok: {'✓ PASS' if result['ok'] else '✗ FAIL'}")
    print(f"errors: {len(result['errors'])}")
    for e in result["errors"]:
        print(f"  ❌ {e}")
    print(f"warnings: {len(result['warnings'])}")
    for w in result["warnings"]:
        print(f"  ⚠️  {w}")
    print()
    print("summary:")
    for k, v in result["summary"].items():
        print(f"  {k}: {v}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    import sys
    sys.exit(_print_verify())