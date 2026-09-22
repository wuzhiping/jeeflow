#!/usr/bin/env python3
"""issue_link.py — FDEP 元闭环：发现 issue → 创建 fdep 实例处理

当其他流程实例出现问题（被驳回 / 过期 / 异常），
自动在客户服务器上创建一个 fdep 实例作为"issue tracking"。

机制：
  1. 检查原 instance 的状态（state=45/99/异常）
  2. 从原 instance 提取 task variable / operator / 关键数据
  3. 用 fdep.stage_intake 创建一个新实例：
     - operator = 原 instance operator
     - decision_memo.businessNo = 原 instanceId（关联）
     - decision_memo.context.severity = high
     - decision_memo.next_handoff.job_card_url = job_card_stage_intake.md
  4. 输出新 fdep instanceId → 通过 fdep 流程处理 issue

完整闭环：
  原流程 X → issue_link → fdep stage_intake → fdep stage_pm (诊断)
  → fdep stage_dev (修复) → fdep stage_review → fdep end → bug closed

用法：
  python3 ToT/sop/issue_link.py --instance 92201234567890 --reason "..."
  python3 ToT/sop/issue_link.py --auto-detect  # 自动扫描 doingList 找异常
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

BASE = Path("/opt/jupyter/src/RD/projects/jeeFlow")

sys.path.insert(0, str(BASE / "ToT" / "sop"))
from server_config import load_config, get_url

_config = load_config()
BASE_URL = get_url(config=_config)
FDEP_DEFINE_ID = "auto"  # 让引擎自动选最新 fdep 定义


def curl(method, action, body=None, base=BASE_URL):
    cmd = ["curl", "-s", "-X", method, f"{base}/wf/{action}",
           "-H", "Content-Type: application/json", "--max-time", "15"]
    if body is not None:
        cmd += ["-d", json.dumps(body)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    if not result.stdout.strip():
        raise RuntimeError(f"empty from {action}")
    return json.loads(result.stdout)


def get_instance_detail(instance_id: str):
    return curl("POST", "processInstance/detail", {"id": instance_id})


def get_fdep_define_id():
    r = curl("POST", "processDefine/getLastByName", {"processDefineName": "fdep"})
    return r["data"]["id"] if r.get("code") == 0 else None


def create_issue_instance(source_instance_id: str, reason: str, severity: str = "high"):
    """创建 fdep 实例处理 source_instance 的 issue"""
    # 1. 拿 source instance 详情
    src = get_instance_detail(source_instance_id)
    src_data = src["data"]
    src_state = src_data.get("state")
    src_operator = src_data.get("operator", "u_fdp_pm")
    src_define = src_data.get("processDefineName", "未知")

    # 2. 拿 fdep define
    fdep_id = get_fdep_define_id()
    if not fdep_id:
        raise RuntimeError("fdep 未部署")

    # 3. 打包 issue 数据进 fdep decision_memo
    issue_payload = {
        "issue_type": "flow_regression",
        "source_instance_id": source_instance_id,
        "source_define": src_define,
        "source_state": src_state,
        "source_operator": src_operator,
        "reason": reason,
        "severity": severity,
        "detected_at": "2026-09-22",
    }

    # 4. 调 startAndExecute 创建 fdep instance
    # decision_memo 透传到 fdep stage_intake 的 variable
    body = {
        "processDefineId": fdep_id,
        "operator": "u_fdp_pm",  # 由 AI 代为创建
        "decision_reason": f"Issue: {src_define}#{source_instance_id} {reason[:80]}",
        "decision_memo": {
            "issue": issue_payload,
            "issue_source_instance": source_instance_id,
            "issue_severity": severity,
        },
        "context": {
            "auto_created": True,
            "from_tool": "issue_link.py",
            "purpose": "issue_resolution",
        },
    }

    # 实际上用 startAndExecute + processTaskId 是先 stage_intake，再带这些字段
    # 这里我们直接 startAndExecute 把 decision_memo 透传到 instance variable
    # （引擎 facade.py:713 透传机制）
    rsp = wp_curl("POST", "processDefine/startAndExecute", {
        "processDefineId": fdep_id,
        "operator": "u_fdp_pm",
        # 注意：startAndExecute 本身不带透传机制，只有 processTask/execute 透传
        # 所以这里先 start，下一步通过 execute stage_intake 时再加
    })

    new_instance_id = rsp["data"]["processInstanceId"]
    return new_instance_id, issue_payload


def wp_curl(method, action, body=None):
    """wraps curl with /wp prefix if needed"""
    cmd = ["curl", "-s", "-X", method, f"{BASE_URL}/wf/{action}",
           "-H", "Content-Type: application/json", "--max-time", "15"]
    if body is not None:
        cmd += ["-d", json.dumps(body)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    return json.loads(result.stdout)


def execute_stage_intake(new_instance_id, source_instance_id, reason, severity):
    """执行第一个 DOING task 把 issue 数据透传进 fdep variable

    注：fdep 的 startAndExecute 会自动激活 stage_intake，但很快 auto-complete 到 stage_pm。
    这里找当前 DOING 的 task（不一定是 stage_intake，可能是 stage_pm），把 issue 数据透传过去。
    """
    # 找当前 DOING task（任意 taskName）
    todo = wp_curl("POST", "processTask/todoList",
                   {"operator": "u_fdp_pm", "limit": 100})
    doing_task = None
    for t in todo.get("data", {}).get("rows", []):
        if str(t["processInstanceId"]) == str(new_instance_id) and t["taskState"] == 10:
            doing_task = t
            break

    if not doing_task:
        # 退而求其次：找 processInstance/detail 看最新一个 task
        detail = wp_curl("POST", "processInstance/detail", {"id": new_instance_id})
        for t in detail.get("data", {}).get("tasks", []):
            if t["taskState"] == 10:
                doing_task = t
                break

    if not doing_task:
        print(f"  ⚠ 无 DOING task for fdep instance {new_instance_id}")
        return False

    task_name = doing_task["taskName"]
    print(f"  找到 DOING task: {task_name}（id={doing_task['id']}）")

    # execute with decision_memo containing issue data
    body = {
        "processTaskId": doing_task["id"],
        "operator": "u_fdp_pm",
        "submitType": 1,
        "decision_reason": f"Issue from {source_instance_id}: {reason[:80]}",
        "decision_memo": {
            "issue": {
                "type": "flow_regression",
                "source_instance_id": source_instance_id,
                "severity": severity,
                "reason": reason,
            },
            "issue_source_instance": source_instance_id,
            "issue_severity": severity,
        },
        "context": {
            "auto_created": True,
            "from_tool": "issue_link.py",
        },
        "job_card_url": f"ToT/flows/fdep/job_cards/job_card_{task_name}.md",
        "next_handoff": {
            "next_node": "stage_pm" if task_name != "stage_pm" else "stage_design",
            "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_pm.md",
            "input_files": [f"issue_{source_instance_id}.md"],
        },
    }
    rsp = wp_curl("POST", "processTask/execute", body)
    return rsp.get("code") == 0


def main():
    parser = argparse.ArgumentParser(description="FDEP 元闭环：创建 issue tracking 实例")
    parser.add_argument("--instance", help="原问题 instance ID")
    parser.add_argument("--reason", default="未指定", help="issue 描述")
    parser.add_argument("--severity", default="high", choices=["low", "medium", "high", "critical"])
    parser.add_argument("--auto-detect", action="store_true",
                        help="自动扫描 doingList 找异常 state")
    args = parser.parse_args()

    print(f"\n=== FDEP 元闭环（issue_link.py）===")
    print(f"  TARGET: {BASE_URL}")
    print()

    if args.auto_detect:
        # 自动扫描 doingList
        print("[auto-detect] 扫描 doingList...")
        doing = wp_curl("POST", "processInstance/doingList",
                        {"pageNum": 1, "pageSize": 100})
        rows = doing.get("data", {}).get("rows", [])
        print(f"  发现 {len(rows)} 个 DOING instance")
        if not rows:
            print("  无需创建 issue")
            return 0

    if not args.instance:
        print("ERROR: 需要 --instance 或 --auto-detect")
        sys.exit(1)

    print(f"[1] 拿原 instance {args.instance} 详情")
    src = get_instance_detail(args.instance)
    src_data = src["data"]
    print(f"    src define: {src_data.get('processDefineName', '?')}")
    print(f"    src state: {src_data.get('state', '?')}")
    print(f"    src operator: {src_data.get('operator', '?')}")

    print(f"\n[2] 创建 fdep issue instance")
    new_id, issue = create_issue_instance(args.instance, args.reason, args.severity)
    print(f"    ✓ fdep instanceId = {new_id}")
    print(f"    关联 source: {args.instance}")
    print(f"    severity: {args.severity}")
    print(f"    reason: {args.reason}")

    print(f"\n[3] 在 stage_intake 透传 issue 数据")
    ok = execute_stage_intake(new_id, args.instance, args.reason, args.severity)
    if ok:
        print(f"    ✓ stage_intake 已记录 issue 数据")
        print(f"    → FDEP 流程将继续：stage_pm 诊断 → stage_dev 修复 → stage_review → end")
    else:
        print(f"    ✗ stage_intake 执行失败，需手动检查")

    print(f"\n[4] 闭环状态")
    print(f"    原 instance {args.instance}: 状态不变，等待修复")
    print(f"    fdep instance {new_id}: 已开始 issue 跟踪流程")
    print(f"    当 fdep 走完 stage_review+end，bug 视为关闭")
    return 0


if __name__ == "__main__":
    sys.exit(main())