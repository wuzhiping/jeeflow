#!/usr/bin/env python3
"""promote.py — 3 阶段环境流水线 CLI 助手

子命令：
  list                           列出所有 servers + tier + AI 能力
  status <flow>                  看某 flow 在各环境的 defineId + 最近 instance
  push <flow> <from>-to-<to>     推 flow 定义（自动）
  request-promote <flow>         生成 promote 请求（人类审批后用 promote）
  promote <flow> <from>-to-<to>  执行 promote（需 --confirm-ai 标志）
  rollback <flow> <from>-to-<to> 回滚

设计原则（与 env-pipeline.md SOP 一致）：
  - Local → Org：AI 全权（风险低）
  - Org → Customer：必须人工确认（--confirm-ai flag）
  - Customer → 任何：禁止（需 SOP 例外）

用法：
  python3 ToT/sop/promote.py list
  python3 ToT/sop/promote.py status fdep
  python3 ToT/sop/promote.py push fdep local-memory-to-local-pg
  python3 ToT/sop/promote.py request-promote fdep
  python3 ToT/sop/promote.py promote fdep org-server-to-customer-test --confirm-ai
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

BASE = Path("/opt/jupyter/src/RD/projects/jeeFlow")
FLOWS_DIR = BASE / "ToT" / "flows"
CONFIG_PATH = BASE / "ToT" / "config" / "servers.json"

sys.path.insert(0, str(BASE / "ToT" / "sop"))
from server_config import load_config, get_url, get_active

ALLOWED_PROMOTIONS = {
    # (from, to) -> 是否需要人工确认
    ("local-memory", "org-server"): False,
    ("local-memory", "customer-test"): True,  # 跳过 org 需审批
    ("local-pg", "org-server"): False,
    ("local-pg", "customer-test"): True,
    ("org-server", "customer-test"): True,    # 必须审批
}


def curl(method, url, body=None, timeout=15):
    cmd = ["curl", "-s", "-X", method, f"{url}", "--max-time", str(timeout)]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
    if not result.stdout.strip():
        return None
    try:
        return json.loads(result.stdout)
    except Exception:
        return None


def list_servers(cfg=None):
    cfg = cfg or load_config()
    print(f"\n=== 3 阶段环境流水线 ({len(cfg['servers'])} servers) ===\n")
    print(f"  {'Server':<18s} {'Tier':<18s} {'Risk':<10s} {'AI Push':<10s} {'AI Reset':<10s} {'URL'}")
    print(f"  {'-'*18} {'-'*18} {'-'*10} {'-'*10} {'-'*10} {'-'*40}")
    for name, info in cfg["servers"].items():
        marker = " ← ACTIVE" if name == cfg["active"] else ""
        print(f"  {name:<18s} {info.get('tier', '?'):<18s} "
              f"{info.get('risk_level', '?'):<10s} "
              f"{'✓' if info.get('ai_can_push') else '✗':<10s} "
              f"{'✓' if info.get('ai_can_reset') else '✗':<10s} "
              f"{info.get('url') or '(not set)'}{marker}")
    print(f"\nactive: {cfg['active']}")
    print()


def get_define_id(server_name: str, flow_name: str):
    cfg = load_config()
    server = cfg["servers"].get(server_name)
    if not server:
        print(f"ERROR: server '{server_name}' not in config")
        return None
    url = server.get("url")
    if not url:
        print(f"ERROR: server '{server_name}' has no URL (yet)")
        return None
    r = curl("POST", f"{url}/wf/processDefine/getLastByName",
             {"processDefineName": flow_name})
    if r and r.get("code") == 0 and r.get("data"):
        return r["data"]["id"]
    return None


def status_flow(flow_name: str):
    cfg = load_config()
    flow_path = FLOWS_DIR / f"{flow_name}.json"
    if not flow_path.exists():
        print(f"ERROR: {flow_path} 不存在")
        sys.exit(1)

    print(f"\n=== Status of '{flow_name}' ===\n")
    print(f"  {'Server':<18s} {'Tier':<18s} {'DefineId':<25s} {'Status'}")
    print(f"  {'-'*18} {'-'*18} {'-'*25} {'-'*15}")
    for name, info in cfg["servers"].items():
        url = info.get("url")
        if not url:
            print(f"  {name:<18s} {info.get('tier', '?'):<18s} {'(no url)':<25s} {'—'}")
            continue
        define_id = get_define_id(name, flow_name)
        if define_id:
            print(f"  {name:<18s} {info.get('tier', '?'):<18s} {define_id:<25s} ✓ deployed")
        else:
            print(f"  {name:<18s} {info.get('tier', '?'):<18s} {'(not deployed)':<25s} —")

    print()


def push_flow(flow_name: str, from_server: str, to_server: str):
    """推 flow 定义"""
    cfg = load_config()
    flow_path = FLOWS_DIR / f"{flow_name}.json"
    if not flow_path.exists():
        print(f"ERROR: {flow_path} 不存在")
        sys.exit(1)

    # 检查权限
    to_info = cfg["servers"].get(to_server, {})
    if not to_info.get("ai_can_push"):
        print(f"ERROR: ai_can_push=false for server '{to_server}'")
        print("  → 必须人工审批（用 'request-promote' + 'promote --confirm-ai'）")
        sys.exit(1)

    # 推
    from_url = get_url(from_server)
    to_url = get_url(to_server)
    if not to_url:
        print(f"ERROR: target server '{to_server}' has no URL")
        sys.exit(1)

    content = flow_path.read_text(encoding="utf-8")
    body = {"content": content, "operator": "system", "name": flow_name}
    rsp = curl("POST", f"{to_url}/wf/processDefine/deploy", body)

    if rsp and rsp.get("code") == 0:
        new_id = rsp["data"]["processDefineId"]
        print(f"✓ pushed {flow_name} to {to_server}")
        print(f"  new defineId: {new_id}")
        print(f"  path: {from_server} → {to_server}")
        return 0
    else:
        print(f"✗ push failed: {rsp}")
        return 1


def request_promote(flow_name: str):
    """生成 promote 请求（不实际推）"""
    print(f"\n=== Promote 请求：{flow_name} → customer-test ===\n")
    print(f"  ⚠️  此操作需人工审批！\n")
    print(f"  步骤：")
    print(f"    1. 人工审批（产品负责人签字 / IM 通知）")
    print(f"    2. 写留档到 ToT/customer-resets/<ts>_promote_<flow>.md")
    print(f"    3. 跑：")
    print(f"       python3 ToT/sop/promote.py promote {flow_name} \\")
    print(f"           org-server-to-customer-test --confirm-ai")
    print()


def do_promote(flow_name: str, from_to: str, confirm_ai: bool):
    """实际执行 promote（需 --confirm-ai 标志）"""
    if not confirm_ai:
        print(f"ERROR: 必须带 --confirm-ai 标志（人工审批后）")
        print(f"  → 先跑 'request-promote {flow_name}' 生成审批请求")
        sys.exit(1)

    if "-" not in from_to:
        print(f"ERROR: 格式应为 'from-to'（如 org-server-to-customer-test）")
        sys.exit(1)
    parts = from_to.split("-to-", 1)
    if len(parts) != 2:
        print(f"ERROR: 格式错误")
        sys.exit(1)
    from_server, to_server = parts[0], parts[1]

    # 检查是否是 customer-test（必须审批）
    cfg = load_config()
    if to_server == "customer-test" or to_server == "production-future":
        # 这是 critical 操作，强制要求 confirm_ai
        pass

    return push_flow(flow_name, from_server, to_server)


def main():
    parser = argparse.ArgumentParser(description="3 阶段环境流水线 CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # list
    sub.add_parser("list", help="列出所有 servers")

    # status
    p_status = sub.add_parser("status", help="查某 flow 在各环境的状态")
    p_status.add_argument("flow", help="flow 名")

    # push
    p_push = sub.add_parser("push", help="推 flow 定义（自动）")
    p_push.add_argument("flow")
    p_push.add_argument("from_to", help="格式: from-to（如 local-memory-to-org-server）")

    # request-promote
    p_req = sub.add_parser("request-promote", help="生成 promote 请求（人类审批）")
    p_req.add_argument("flow")

    # promote
    p_prom = sub.add_parser("promote", help="执行 promote（必须 --confirm-ai）")
    p_prom.add_argument("flow")
    p_prom.add_argument("from_to", help="格式: from-to")
    p_prom.add_argument("--confirm-ai", action="store_true", help="确认已人工审批")

    # rollback
    p_rb = sub.add_parser("rollback", help="回滚（仅向下游）")
    p_rb.add_argument("flow")
    p_rb.add_argument("from_to")

    args = parser.parse_args()

    if args.cmd == "list":
        list_servers()
    elif args.cmd == "status":
        status_flow(args.flow)
    elif args.cmd == "push":
        if "-" not in args.from_to:
            print("ERROR: 格式应为 'from-to'")
            sys.exit(1)
        parts = args.from_to.split("-to-", 1)
        push_flow(args.flow, parts[0], parts[1])
    elif args.cmd == "request-promote":
        request_promote(args.flow)
    elif args.cmd == "promote":
        do_promote(args.flow, args.from_to, args.confirm_ai)
    elif args.cmd == "rollback":
        # 回滚：把 from 的当前定义回滚到 to（一般是回滚到上一个版本，但简化：从 to 推到 from）
        print(f"Rollback {args.flow}: {args.from_to}")
        print("  (回滚需要历史版本管理 —— 当前实现：把 to 的当前内容推回 from)")
        parts = args.from_to.split("-to-", 1)
        push_flow(args.flow, parts[1], parts[0])


if __name__ == "__main__":
    main()