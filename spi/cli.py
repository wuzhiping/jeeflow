"""spi CLI 入口 (dispatcher 层, 重构 v26)

统一的 CLI 入口, 通过 SPI_FOLDER 动态选择实现包:
- SPI_FOLDER=demo → spi/demo/cli.py
- SPI_FOLDER=dev  → spi/dev/cli.py

Usage:
    python -m spi.cli verify
    python -m spi.cli list-users
    python -m spi.cli show-user u_fe_eng

每个实现包必须提供 cli.py, 导出以下 _data_* 函数 (参见 SPEC §8):
- _data_verify, _data_status, _data_list_users, _data_show_user,
  _data_list_depts, _data_show_dept

如果 SPI_FOLDER=<impl> 但 <impl>/cli.py 不存在, raise NotImplementedError.
"""
import sys


def _load_impl_module(name: str):
    """按 SPI_FOLDER 动态加载实现模块

    Raises:
        NotImplementedError: 当前实现包不支持 CLI (缺少 cli.py)
    """
    from spi import get_spi_folder
    folder = get_spi_folder()
    full_name = f"spi.{folder}.{name}"
    try:
        from importlib import import_module
        return import_module(full_name)
    except ImportError as e:
        raise NotImplementedError(
            f"spi.{folder} 不支持 CLI (缺少 {name} 模块): {e}"
        )


# === 数据获取函数 (delegate 给实现包) ===

def _data_verify() -> dict:
    """获取 verify() 结果"""
    return _load_impl_module("cli")._data_verify()


def _data_status() -> dict:
    """获取 status 概况"""
    return _load_impl_module("cli")._data_status()


def _data_list_users() -> list[dict]:
    """获取用户列表"""
    return _load_impl_module("cli")._data_list_users()


def _data_show_user(uid: str) -> dict | None:
    """获取用户完整信息 (None 表示不存在)"""
    return _load_impl_module("cli")._data_show_user(uid)


def _data_list_depts() -> list[dict]:
    """获取部门列表"""
    return _load_impl_module("cli")._data_list_depts()


def _data_show_dept(dept_id: str) -> dict | None:
    """获取部门完整信息 (None 表示不存在)"""
    return _load_impl_module("cli")._data_show_dept(dept_id)


# === CLI 命令 (使用 _data_* 函数) ===

def _cmd_verify() -> int:
    """执行 verify() 并打印结果

    返回: 0=PASS, 1=FAIL (有 errors)
    """
    result = _data_verify()
    from spi import get_spi_folder
    print(f"=== spi/{get_spi_folder()} verify ===")
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


def _cmd_status() -> int:
    """打印 SPI 数据概况"""
    result = _data_status()
    from spi import get_spi_folder
    print(f"=== spi/{get_spi_folder()} status ===")
    print()
    s = result["summary"]
    print(f"summary:")
    for k, v in s.items():
        print(f"  {k}: {v}")
    status = "✓ ok" if result["ok"] else f"✗ {len(result['errors'])} errors"
    print(f"\nverify: {status}")
    return 0


def _cmd_list_users() -> int:
    """列出所有用户 (uid, name, post, dept, role)"""
    users = _data_list_users()
    print(f"=== Users ({len(users)}) ===")
    print(f"{'uid':18s} {'name':10s} {'post':12s} {'dept':8s} {'role':20s}")
    print("-" * 75)
    for u in users:
        role_str = ",".join(u.get("roles", [])) if u.get("roles") else "(无)"
        print(f"{u.get('uid', ''):18s} {u.get('name', ''):10s} {u.get('post', ''):12s} "
              f"{u.get('dept_id', ''):8s} {role_str:20s}")
    return 0


def _cmd_show_user(uid: str) -> int:
    """显示用户完整信息"""
    info = _data_show_user(uid)
    if info is None:
        print(f"❌ User not found: {uid}", file=sys.stderr)
        return 1
    print(f"=== User: {uid} ===")
    for k, v in info.items():
        if isinstance(v, list):
            v_str = " → ".join(v) if k.endswith("_chain") else ", ".join(v)
            print(f"  {k}: {v_str}")
        elif isinstance(v, dict):
            print(f"  {k}: {v}")
        else:
            print(f"  {k}: {v}")
    return 0


def _cmd_list_depts() -> int:
    """列出所有部门"""
    depts = _data_list_depts()
    print(f"=== Departments ({len(depts)}) ===")
    print(f"{'dept_id':10s} {'name':10s} {'size':5s} {'leader':18s} {'main_leader':18s}")
    print("-" * 65)
    for d in depts:
        print(f"{d.get('dept_id', ''):10s} {d.get('name', ''):10s} {d.get('size', 0):<5d} "
              f"{d.get('leader', '') or '(空)':18s} {d.get('main_leader', '') or '(空)':18s}")
    return 0


def _cmd_show_dept(dept_id: str) -> int:
    """显示部门完整信息"""
    data = _data_show_dept(dept_id)
    if data is None:
        print(f"❌ Department not found: {dept_id}", file=sys.stderr)
        return 1
    info = data.get("info", {})
    members = data.get("members", [])
    print(f"=== Department: {dept_id} ===")
    for k, v in info.items():
        if isinstance(v, list):
            print(f"  {k}: {', '.join(v)}")
        elif isinstance(v, dict):
            print(f"  {k}: {v}")
        else:
            print(f"  {k}: {v}")
    print()
    print(f"Members ({len(members)}):")
    for m in members:
        print(f"  - {m.get('name', '?')} ({m.get('userId', 'N/A')}) - {m.get('post', '?')}")
    return 0


def _print_help() -> None:
    print("Usage: python -m spi.cli [command] [args]")
    print()
    print("Commands:")
    print("  verify                          验证数据完整性 (4 类检查)")
    print("  status                          打印 SPI 数据概况")
    print("  list-users                      列出所有用户")
    print("  show-user <uid>                 显示用户完整信息")
    print("  list-depts                      列出所有部门")
    print("  show-dept <dept_id>             显示部门完整信息")
    print("  help                            显示帮助")


def main(argv: list[str] | None = None) -> int:
    """CLI 入口 (dispatcher 层)

    根据 SPI_FOLDER 自动路由到 spi.<folder>.cli

    Usage:
        python -m spi.cli verify
        python -m spi.cli status
        python -m spi.cli list-users
        python -m spi.cli show-user <uid>
        python -m spi.cli list-depts
        python -m spi.cli show-dept <dept_id>
        python -m spi.cli help

    返回: 0=PASS, 1=FAIL, 2=USAGE ERROR
    """
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] == "help" or argv[0] == "-h" or argv[0] == "--help":
        _print_help()
        return 0

    cmd = argv[0]
    args = argv[1:]

    try:
        if cmd == "verify":
            return _cmd_verify()
        elif cmd == "status":
            return _cmd_status()
        elif cmd == "list-users":
            if args:
                print(f"Unexpected args for list-users: {args}", file=sys.stderr)
                return 2
            return _cmd_list_users()
        elif cmd == "show-user":
            if not args:
                print("Usage: python -m spi.cli show-user <uid>", file=sys.stderr)
                return 2
            return _cmd_show_user(args[0])
        elif cmd == "list-depts":
            if args:
                print(f"Unexpected args for list-depts: {args}", file=sys.stderr)
                return 2
            return _cmd_list_depts()
        elif cmd == "show-dept":
            if not args:
                print("Usage: python -m spi.cli show-dept <dept_id>", file=sys.stderr)
                return 2
            return _cmd_show_dept(args[0])
        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            print("Run 'python -m spi.cli help' for usage.", file=sys.stderr)
            return 2
    except NotImplementedError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())