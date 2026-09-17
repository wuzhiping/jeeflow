#!/usr/bin/env python3
"""regression_runner.py — parameterised regression for one processDefineId.

仅 stdlib（urllib/json/argparse），无外部依赖。

Usage:
    python ./tdd/regression_runner.py --define <processDefineId> --cases 1,2,3,5,6,20
        [--operator user1] [--assignee user2] [--base http://localhost:8101]

每个 submitType case 跑：
  1. POST /api/reset                         — 重置环境
  2. POST /wf/processInstance/startAndExecute — 起批（submitType=1 + operator=user1 + assignee=user2）
  3. POST /wf/processInstance/execute        — user2 以 submitType=X 提交
  4. POST /wf/processInstance/detail         — 校验终态 state

期望终态依据 ./docs/flow.md §7a 路由矩阵：
  1 / 5 / 20  -> 7   (DONE)
  2           -> 45  (REJECT)
  3 / 6       -> 10  (DOING, 重新激活 apply)
  0           -> 7   (DONE; 仅经 startAndExecute 内部注入，不走 execute)

报告落 ./tdd/regression_<define>_<YYYYMMDDHHMMSS>.json。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

EXPECTED_STATE = {
    0: 20,
    1: 20,
    5: 20,
    20: 20,
    2: 45,
    3: 10,
    6: 10,
}


def _first_active_task_id(detail_body: dict) -> str | None:
    data = detail_body.get("data") if isinstance(detail_body, dict) else None
    if not isinstance(data, dict):
        return None
    tasks = data.get("tasks") or []
    for t in tasks:
        if isinstance(t, dict) and t.get("taskState") in (10, "10"):
            return t.get("id")
    return None


def _http(base: str, action: str, body: dict, timeout: float = 10.0) -> tuple[int, dict]:
    url = f"{base.rstrip('/')}/wf/{action}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8") or "{}")
            return resp.status, payload
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8") or "{}")
        except Exception:
            payload = {"raw": str(exc)}
        return exc.code, payload
    except urllib.error.URLError as exc:
        return 0, {"error": str(exc)}


def _reset(base: str) -> tuple[int, dict]:
    url = f"{base.rstrip('/')}/api/reset"
    req = urllib.request.Request(url, data=b"", method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": str(exc)}


def _run_case(
    base: str,
    process_define_id: int,
    submit_type: int,
    operator: str,
    assignee: str,
    extra_vars: dict | None = None,
) -> dict:
    t0 = time.time()
    reset_status, reset_body = _reset(base)
    variables = {"submitType": 1, "f_apply": operator}
    if extra_vars:
        variables.update(extra_vars)
    start_status, start_body = _http(
        base,
        "processInstance/startAndExecute",
        {
            "processDefineId": process_define_id,
            "operator": operator,
            "businessNo": f"REG-{submit_type}-{int(t0)}",
            "title": f"regression case submitType={submit_type}",
            "assignees": {
                "apply": operator,
                "task1": assignee,
            },
            "variables": variables,
        },
    )
    instance_id = (
        start_body.get("data", {}).get("processInstanceId")
        or start_body.get("processInstanceId")
    )
    task_id = (
        start_body.get("data", {}).get("processTaskId")
        or start_body.get("processTaskId")
    )
    if not instance_id:
        elapsed = int((time.time() - t0) * 1000)
        return {
            "submitType": submit_type,
            "processInstanceId": None,
            "actualState": None,
            "expectedState": EXPECTED_STATE.get(submit_type),
            "pass": False,
            "elapsedMs": elapsed,
            "stage": "start",
            "startStatus": start_status,
            "startBody": start_body,
            "resetStatus": reset_status,
        }

    exec_status = None
    exec_body = None
    detail_status = None
    detail_body = {}

    if not task_id:
        detail_status, detail_body = _http(
            base,
            "processInstance/detail",
            {"id": instance_id},
        )
        task_id = _first_active_task_id(detail_body)

    if task_id:
        exec_status, exec_body = _http(
            base,
            "processTask/execute",
            {
                "processTaskId": task_id,
                "operator": assignee,
                "submitType": submit_type,
                "variables": {},
            },
        )

    detail_status, detail_body = _http(
        base,
        "processInstance/detail",
        {"id": instance_id},
    )
    actual_state = detail_body.get("state")
    if actual_state is None and isinstance(detail_body.get("data"), dict):
        actual_state = detail_body["data"].get("state")

    elapsed = int((time.time() - t0) * 1000)
    expected = EXPECTED_STATE.get(submit_type)
    return {
        "submitType": submit_type,
        "processInstanceId": instance_id,
        "actualState": actual_state,
        "expectedState": expected,
        "pass": actual_state == expected,
        "elapsedMs": elapsed,
        "resetStatus": reset_status,
        "startStatus": start_status,
        "execStatus": exec_status,
        "detailStatus": detail_status,
        "execBody": exec_body,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Parameterised flow regression runner.")
    parser.add_argument("--define", type=int, required=True, help="processDefineId")
    parser.add_argument(
        "--cases",
        default="1,2,3,5,6,20",
        help="comma-separated submitType values (default: 1,2,3,5,6,20)",
    )
    parser.add_argument("--operator", default="user1", help="applicant user id")
    parser.add_argument("--assignee", default="user2", help="approver user id")
    parser.add_argument("--base", default="http://localhost:8101", help="service base URL")
    parser.add_argument(
        "--vars",
        default="{}",
        help="extra variables injected into startAndExecute (JSON object, default: {})",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="report output path (default: ./tdd/regression_<define>_<ts>.json)",
    )
    args = parser.parse_args()

    cases = [int(c.strip()) for c in args.cases.split(",") if c.strip()]
    if not cases:
        print("no cases provided", file=sys.stderr)
        return 2
    try:
        extra_vars = json.loads(args.vars) if args.vars else {}
    except json.JSONDecodeError as e:
        print(f"invalid --vars JSON: {e}", file=sys.stderr)
        return 2

    print(f"base={args.base}  processDefineId={args.define}  cases={cases}  vars={extra_vars}")
    results = []
    for st in cases:
        print(f"  -> submitType={st} ...", end="", flush=True)
        r = _run_case(args.base, args.define, st, args.operator, args.assignee, extra_vars)
        print(
            f" instanceId={r['processInstanceId']} actual={r['actualState']} "
            f"expected={r['expectedState']} {'PASS' if r['pass'] else 'FAIL'} "
            f"({r['elapsedMs']}ms)"
        )
        results.append(r)

    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    out_path = Path(args.out) if args.out else Path(f"./tdd/regression_{args.define}_{ts}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "processDefineId": args.define,
        "base": args.base,
        "operator": args.operator,
        "assignee": args.assignee,
        "vars": extra_vars,
        "cases": results,
        "totals": {
            "run": len(results),
            "passed": sum(1 for r in results if r["pass"]),
            "failed": sum(1 for r in results if not r["pass"]),
        },
        "ranAt": ts,
    }
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report: {out_path}")
    print(
        f"summary: {summary['totals']['passed']}/{summary['totals']['run']} passed"
    )
    return 0 if summary["totals"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
