#!/usr/bin/env python3
"""config.py · flow-operator skill 配置加载与设置工具

用法：
    python3 config.py                 # 打印当前配置 + 上下文
    python3 config.py --load           # 仅加载并打印 YAML
    python3 config.py --context       # 打印 get_context() 输出（AI agent 用）
    python3 config.py --setup         # 交互式 setup（首次或修改）
    python3 config.py --set k=v       # 命令行设置单个字段）
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

try:
    import yaml
except ImportError:
    print("❌ 需要 PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

SKILL_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SKILL_DIR / "config.yaml"

# 默认配置 schema（首次 setup 时提示）
DEFAULT_CONFIG = {
    "active_server": "http://127.0.0.1:8101",  # API base URL（完整 URL，不依赖 servers.json）
    "operator": {
        "user_id": "u_fdp_pm",        # 当前 AI 代表的人类用户 uid
        "role_lenses": [              # 限定 list（只能 init 看到的视图）
            "initiator",              # 我创建的
            "assignee",               # 我被指派的
        ],
    },
    "notes": "由 setup() 交互式填写，或手动编辑此 YAML",
}


def load_config():
    """加载 config.yaml；不存在返回 None"""
    if not CONFIG_PATH.exists():
        return None
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(cfg):
    """保存 config 到 YAML"""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f"✅ 已写入: {CONFIG_PATH}")


def get_context():
    """给 AI agent 的上下文摘要（每次触发 SKILL 应展示）

    返回 markdown 字符串，AI agent 加载 SKILL 后先调用此函数得到上下文。
    """
    cfg = load_config()
    if not cfg:
        return (
            "⚠️ flow-operator config 未配置\n"
            f"   运行 `python3 {Path(__file__).name} --setup` 初始化"
        )

    active = cfg.get("active_server", "?")
    op = cfg.get("operator", {})
    user_id = op.get("user_id", "?")
    lenses = op.get("role_lenses", [])

    lens_desc = {
        "initiator": "我创建的（initiator）",
        "assignee": "我被指派的（assignee）",
    }
    lens_lines = "\n".join(f"  - {lens_desc.get(l, l)}" for l in lenses)

    return (
        "## flow-operator 上下文\n\n"
        f"- **server**: `{active}`（API base URL）\n"
        f"- **operator**:\n"
        f"  - **user_id**: `{user_id}`\n"
        f"  - **role_lenses**:\n{lens_lines}\n"
        f"{_fdep_line(cfg)}\n"
        "\n"
        "→ 行动准则：\n"
        f"  - 所有 API 调用 base = `{active}`\n"
        f"  - 我代表 `{user_id}` 操作\n"
        f"  - 我能看到以上 role_lenses 范围内的实例和任务\n"
        f"  - 反馈走 fdep（参见 ## FeedBack 节）\n"
    )


def _fdep_line(cfg):
    """get_context() 辅助：生成 fdep 信息行"""
    fdep = cfg.get("fdep")
    if not fdep:
        return ""
    if "error" in fdep:
        return f"\n- **fdep**: ⚠️ {fdep.get('error', 'unknown error')}"
    return (
        f"\n- **fdep**: define_id=`{fdep.get('define_id', '?')}` "
        f"v{fdep.get('version', '?')} "
        f"({fdep.get('display_name', '?')}) "
        f"[verified {fdep.get('verified_at', '?')}]"
    )


def validate_url(url: str) -> tuple:
    """验证 URL 可达（curl /healthz）。返回 (ok, msg)"""
    try:
        r = subprocess.run(
            ["curl", "-sS", "-L", "--max-time", "10", f"{url.rstrip('/')}/healthz"],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode != 0:
            return False, f"curl exit {r.returncode}: {r.stderr[:100]}"
        try:
            data = json.loads(r.stdout)
            if data.get("status") == "UP":
                return True, f"UP (pg={data.get('pg', '?')})"
            return False, f"非 UP 状态: {data}"
        except Exception:
            return False, f"非 JSON 响应: {r.stdout[:100]}"
    except Exception as e:
        return False, f"异常: {e}"


def validate_user_id(url: str, user_id: str) -> tuple:
    """调 /api/spi/users 验证 user_id 存在。返回 (ok, msg)"""
    try:
        r = subprocess.run(
            ["curl", "-sS", "--max-time", "10", f"{url.rstrip('/')}/api/spi/users?pageSize=200"],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode != 0:
            return False, f"SPI 不可达: {r.stderr[:100]}"
        try:
            data = json.loads(r.stdout)
        except Exception:
            return False, f"SPI 返回非 JSON: {r.stdout[:100]}"
        users = data.get("users", [])
        match = next((u for u in users if u.get("uid") == user_id), None)
        if match:
            name = match.get("name", "?")
            return True, f"已找到: {name} ({match.get('dept_id', '?')})"
        return False, f"未找到 uid={user_id}（SPI 共 {len(users)} 个用户）"
    except Exception as e:
        return False, f"异常: {e}"


def validate_fdep(url: str) -> tuple:
    """调 /wf/processDefine/getLastByName 验证 fdep 部署。返回 (ok, info_dict, msg)"""
    try:
        r = subprocess.run(
            [
                "curl", "-sS", "--max-time", "10",
                "-X", "POST",
                f"{url.rstrip('/')}/wf/processDefine/getLastByName",
                "-H", "Content-Type: application/json",
                "-d", '{"processDefineName":"fdep"}',
            ],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode != 0:
            return False, {}, f"curl exit {r.returncode}"
        try:
            data = json.loads(r.stdout)
        except Exception:
            return False, {}, f"非 JSON: {r.stdout[:100]}"
        if data.get("code") != 0:
            return False, {}, f"engine 报错: {data.get('msg')}"
        d = data.get("data") or data.get("detail")
        if not d:
            return False, {}, f"无 detail: {data}"
        info = {
            "define_id": str(d.get("id", "")),
            "name": d.get("name", ""),
            "display_name": d.get("displayName", ""),
            "version": d.get("version", ""),
            "state": d.get("state", ""),
            "type": d.get("type", ""),
            "verified_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        return True, info, f"v{info['version']} ({info['display_name']})"
    except Exception as e:
        return False, {}, f"异常: {e}"


def setup_interactive():
    """交互式 setup（含数据验证）

    流程：
      1. active_server URL（验证 /healthz 可达）
      2. operator.user_id（用 active_server 调 SPI /users 验证存在）
      3. operator.role_lenses：永远默认 [initiator, assignee]，不询问
      4. 全部验证通过 → 写文件
    """
    cfg = load_config() or DEFAULT_CONFIG.copy()
    print("=" * 60)
    print("flow-operator config setup")
    print("=" * 60)
    print()
    print(f"当前路径: {CONFIG_PATH}")
    print(f"现有内容: {'已有' if CONFIG_PATH.exists() else '空（首次）'}")
    print()

    # 1. active_server URL（验证可达，循环直到成功）
    while True:
        default_server = cfg.get("active_server", DEFAULT_CONFIG["active_server"])
        raw = input(f"active_server URL [{default_server}]: ").strip()
        active_server = raw or default_server
        print(f"  验证 {active_server}/healthz ...", end=" ")
        ok, msg = validate_url(active_server)
        print(f"{'✅' if ok else '❌'} {msg}")
        if ok:
            break
        print("  请重新输入（Ctrl+C 退出）")

    # 2. user_id（用 active_server 调 SPI 验证存在，循环直到成功）
    while True:
        default_uid = cfg.get("operator", {}).get("user_id", DEFAULT_CONFIG["operator"]["user_id"])
        raw = input(f"operator.user_id [{default_uid}]: ").strip()
        user_id = raw or default_uid
        print(f"  验证 {active_server}/api/spi/users ...", end=" ")
        ok, msg = validate_user_id(active_server, user_id)
        print(f"{'✅' if ok else '❌'} {msg}")
        if ok:
            break
        print("  请重新输入（Ctrl+C 退出）")

    # 3. role_lenses：永远默认 [initiator, assignee]，不询问
    lenses = DEFAULT_CONFIG["operator"]["role_lenses"]
    print(f"\nrole_lenses: {lenses}（默认，不询问）")

    # 4. fdep 部署验证（非阻塞：失败也允许，warning + 记录 error）
    print(f"\n  验证 {active_server} 上 fdep 部署 ...", end=" ")
    fdep_ok, fdep_info, fdep_msg = validate_fdep(active_server)
    print(f"{'✅' if fdep_ok else '⚠️'} {fdep_msg}")
    if not fdep_ok:
        fdep_info = {"error": fdep_msg}

    # 写文件
    new_cfg = {
        "active_server": active_server,
        "operator": {
            "user_id": user_id,
            "role_lenses": lenses,
        },
        "fdep": fdep_info,
        "notes": "由 setup() 交互式填写，或手动编辑此 YAML",
    }
    save_config(new_cfg)

    # 显示 get_context() 输出
    print()
    print(get_context())


def set_field(key_path, value):
    """命令行设置单个字段，写入前自动验证

    验证规则：
      - active_server：curl /healthz 验证可达
      - operator.user_id：用 active_server 调 SPI 验证存在
      - operator.role_lenses：强制 [initiator, assignee]，忽略任何其他值
    验证失败 → 不写入，返回 False
    """
    # role_lenses 永远默认
    if key_path == "operator.role_lenses":
        print(f"⚠️  role_lenses 永远默认 {DEFAULT_CONFIG['operator']['role_lenses']}，忽略输入")
        return False

    cfg = load_config() or DEFAULT_CONFIG.copy()
    parts = key_path.split(".")
    cur = cfg
    for p in parts[:-1]:
        if p not in cur:
            cur[p] = {}
        cur = cur[p]

    # 验证
    if key_path == "active_server":
        print(f"  验证 {value}/healthz ...", end=" ")
        ok, msg = validate_url(value)
        print(f"{'✅' if ok else '❌'} {msg}")
        if not ok:
            return False
        # 顺手验证 fdep（非阻塞：失败也写入 active_server，fdep 标 error）
        print(f"  + 验证 {value} 上 fdep 部署 ...", end=" ")
        fdep_ok, fdep_info, fdep_msg = validate_fdep(value)
        print(f"{'✅' if fdep_ok else '⚠️'} {fdep_msg}")
        cur[parts[-1]] = value
        cfg["fdep"] = fdep_info if fdep_ok else {"error": fdep_msg}
        save_config(cfg)
        return True
    elif key_path == "operator.user_id":
        # 需要 active_server（当前 cfg 中的或默认值）
        server = cfg.get("active_server", DEFAULT_CONFIG["active_server"])
        print(f"  验证 {server}/api/spi/users ...", end=" ")
        ok, msg = validate_user_id(server, value)
        print(f"{'✅' if ok else '❌'} {msg}")
        if not ok:
            return False

    cur[parts[-1]] = value
    save_config(cfg)
    return True


def main():
    parser = argparse.ArgumentParser(description="flow-operator config 工具")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--load", action="store_true", help="仅加载并打印 YAML")
    group.add_argument("--context", action="store_true", help="打印 get_context() 输出")
    group.add_argument("--setup", action="store_true", help="交互式 setup")
    group.add_argument("--set", help="设置单个字段（如 operator.user_id=19283746）")
    args = parser.parse_args()

    if args.load:
        cfg = load_config()
        if cfg is None:
            print(f"⚠️ {CONFIG_PATH} 不存在")
            return 1
        print(yaml.dump(cfg, default_flow_style=False, allow_unicode=True, sort_keys=False))
        return 0

    if args.context:
        print(get_context())
        return 0

    if args.setup:
        setup_interactive()
        return 0

    if args.set:
        if "=" not in args.set:
            print("❌ --set 格式: key.path=value", file=sys.stderr)
            return 1
        k, v = args.set.split("=", 1)
        # 尝试 YAML 解析 value（支持 list）
        try:
            v_parsed = yaml.safe_load(v)
        except Exception:
            v_parsed = v
        ok = set_field(k, v_parsed)
        return 0 if ok else 1

    # 默认：print config + 上下文
    print(get_context())
    return 0


if __name__ == "__main__":
    sys.exit(main())