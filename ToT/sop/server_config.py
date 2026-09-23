#!/usr/bin/env python3
"""server_config.py — 流程服务器配置加载器

让所有脚本/SOP 集中读 ToT/config/servers.json，不再硬编码 URL。

示例：
    from server_config import get_url, get_active, list_servers
    
    url = get_url("customer-test")         # → "https://abc.feg.cn/jeeflow"
    url = get_url()                        # → 当前 active 的 URL
    active = get_active()                   # → "customer-test"
    info = get_server_info("customer-test")  # → 完整 dict
    all_servers = list_servers()           # → ["local-memory", "local-pg", "customer-test", "production-future"]

CLI:
        python3 ToT/sop/server_config.py                # 打印 active URL
        python3 ToT/sop/server_config.py --active        # 打印 active server 名
        python3 ToT/sop/server_config.py --list         # 列出所有 servers
        python3 ToT/sop/server_config.py customer-test   # 打印指定 server URL
"""
import argparse
import json
import sys
from pathlib import Path

# 默认 config 路径（ToT/config/servers.json）
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "servers.json"


def load_config(path: Path = CONFIG_PATH) -> dict:
    """加载 servers.json"""
    if not path.exists():
        raise FileNotFoundError(f"servers.json not found at {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_server_info(name: str = None, config: dict = None) -> dict:
    """获取指定 server 的完整信息（默认 active）"""
    cfg = config or load_config()
    if name is None:
        name = cfg["active"]
    if name not in cfg["servers"]:
        raise KeyError(f"server '{name}' not in config. Available: {list(cfg['servers'].keys())}")
    return cfg["servers"][name]


def get_url(name: str = None, config: dict = None) -> str:
    """获取指定 server 的 URL（默认 active）"""
    info = get_server_info(name, config)
    if info.get("url") is None:
        raise ValueError(f"server '{name}' has no URL (status: {info.get('status', 'unknown')})")
    return info["url"]


def get_active(config: dict = None) -> str:
    """获取当前 active server 名"""
    cfg = config or load_config()
    return cfg["active"]


def list_servers(config: dict = None) -> list:
    """列出所有 server 名"""
    cfg = config or load_config()
    return list(cfg["servers"].keys())


def main():
    parser = argparse.ArgumentParser(description="流程服务器配置查询")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--active", action="store_true", help="显示 active server 名")
    group.add_argument("--list", action="store_true", help="列出所有 servers")
    group.add_argument("name", nargs="?", help="指定 server 名（显示 URL）")

    args = parser.parse_args()
    cfg = load_config()

    if args.active:
        print(get_active(cfg))
    elif args.list:
        for name in list_servers(cfg):
            info = cfg["servers"][name]
            url = info.get("url") or "(no url)"
            backend = info.get("backend", "?")
            status = info.get("status", "active")
            print(f"  {name:20s} {url:35s} backend={backend} status={status}")
    elif args.name:
        try:
            print(get_url(args.name, cfg))
        except (KeyError, ValueError) as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # 默认：打印 active URL
        print(get_url(None, cfg))


if __name__ == "__main__":
    main()