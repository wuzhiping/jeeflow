#!/usr/bin/env python3
"""flow_designer.py — 流程设计助手

5 问引导用户从"模糊需求"到"可跑通的最小 flow.json"。

用法：
  python3 ToT/sop/flow_designer.py              # 交互模式
  python3 ToT/sop/flow_designer.py --name my-flow   # 指定 flow 名
  python3 ToT/sop/flow_designer.py --demo         # 演示（自动回答）
"""
import argparse
import json
import sys
from pathlib import Path

BASE = Path("/opt/jupyter/src/RD/projects/jeeFlow")
FLOWS_DIR = BASE / "ToT" / "flows"


def ask(question: str, default: str = "", required: bool = True) -> str:
    """交互式问问题"""
    if default:
        prompt = f"\n{question} [{default}]: "
    else:
        prompt = f"\n{question}: "
    while True:
        try:
            answer = input(prompt).strip()
        except EOFError:
            return default
        if answer:
            return answer
        if default:
            return default
        if not required:
            return ""
        print("  (必填)")


def design(name: str, demo: bool = False) -> dict:
    """5 问 → 生成 flow.json 草稿"""
    print("=" * 60)
    print(f" 流程设计助手（flow_designer）")
    print(f"  目标: 生成 {name}.json 草稿")
    print("=" * 60)
    print("\n我会问 5 个问题。回答即可。Ctrl+C 退出。\n")

    # Q1: 业务目标
    purpose = ("用于团队内部采购流程自动化：员工提交 → 主管审批 → 财务归档"
               if demo else ask("Q1: 这个流程做什么？（一句话，例如'员工报销审批'）"))

    # Q2: 发起者
    initiator = ("任意员工（占位用 u_test）"
                 if demo else ask("Q2: 谁可以发起？例如'任意员工' / '主管' / '客户'"))

    # Q3: 阶段（简单默认 3 阶段）
    print("\nQ3: 流程有几个阶段？（最少 1 个）")
    print("   例如：3 阶段：提交 → 审批 → 完成")
    print("   每阶段用一句话描述，例如：'提交：员工填写申请'")
    n_stages = int(ask("   阶段数", default="3" if demo else "3"))

    stages = []
    for i in range(n_stages):
        print(f"\n   --- 阶段 {i+1} ---")
        if demo and i == 0:
            sname, srole, sartifact = "submit", "员工", "申请单"
        elif demo and i == 1:
            sname, srole, sartifact = "approve", "主管", "审批结果"
        elif demo and i == 2:
            sname, srole, sartifact = "archive", "财务", "归档凭证"
        else:
            sname = ask(f"   阶段 {i+1} 英文名（snake_case）", default=f"stage_{i+1}")
            srole = ask(f"   阶段 {i+1} 执行者（角色或用户名）", default="u_test")
            sartifact = ask(f"   阶段 {i+1} 产出物", default=f"artifact_{i+1}")
        stages.append({"name": sname, "role": srole, "artifact": sartifact})

    # Q4: 决策分支
    has_decision = (ask("Q4: 需要分支决策吗？（y/n，例如'金额 < 5000 自动通过'）",
                       default="n" if demo else "n")).lower() in ("y", "yes")

    decision_expr = ""
    if has_decision and not demo:
        decision_expr = ask("   决策表达式（OGNL/expr）", default="#amount < 5000")

    # Q5: 完成条件
    completion = ("所有阶段执行完成"
                  if demo else ask("Q5: 什么时候算完成？", default="所有阶段执行完成"))

    # === 生成 flow.json ===
    flow = {
        "name": name,
        "displayName": purpose,
        "type": "collaboration",
        "schema": "snaker-1.0",
        "version": "0.1",
        "nodes": [
            {"id": "start", "type": "snaker:start", "x": 50, "y": 200, "text": {"value": initiator}},
            {"id": "decision_intake", "type": "snaker:decision", "x": 250, "y": 200,
             "properties": {"expr": decision_expr or "true"} if has_decision else {"expr": "true"},
             "text": {"value": "路由"}},
        ],
        "edges": [
            {"id": "e0", "sourceNodeId": "start", "targetNodeId": "decision_intake",
             "text": {"value": "发起"}},
        ],
    }

    # 加 stages
    prev_id = "decision_intake"
    for i, s in enumerate(stages):
        nid = s["name"]
        flow["nodes"].append({
            "id": nid, "type": "snaker:task", "x": 400 + i*200, "y": 200,
            "properties": {
                "assignee": s["role"],
                "form": f"{nid}-template",
                "artifact": s["artifact"],
                "storage": f"ToT/{name}/{nid}/",
                "exitCriteria": "完成"
            },
            "text": {"value": f"{i+1}. {s['artifact']}（{s['role']}）"}
        })
        flow["edges"].append({
            "id": f"e{i+1}", "sourceNodeId": prev_id, "targetNodeId": nid,
            "text": {"value": "通过" if i == 0 else ""}
        })
        prev_id = nid

    # decision 默认边（兜底）
    if has_decision:
        flow["edges"].append({
            "id": "e_decision_default",
            "sourceNodeId": "decision_intake",
            "targetNodeId": stages[0]["name"],
            "text": {"value": "默认 → " + stages[0]["name"]}
        })

    # end 节点
    flow["nodes"].append({
        "id": "end", "type": "snaker:end", "x": 400 + len(stages)*200, "y": 200,
        "text": {"value": "完成"}
    })
    flow["edges"].append({
        "id": "e_end", "sourceNodeId": prev_id, "targetNodeId": "end",
        "text": {"value": ""}
    })

    return flow


def save(flow: dict):
    out_path = FLOWS_DIR / f"{flow['name']}.json"
    out_path.write_text(
        json.dumps(flow, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n✓ 已生成：{out_path}")
    print(f"  大小: {out_path.stat().st_size} 字节")
    print(f"  节点数: {len(flow['nodes'])} (含 1 start + 1 decision + {len(flow['nodes']) - 3} task + 1 end)")
    print(f"\n下一步:")
    print(f"  1. 部署: python3 -m uvicorn main:app --port 8101")
    print(f"  2. 检测: python3 ToT/sop/flow_completeness.py {out_path}")
    print(f"  3. 补严谨: 按 completeness 的'下一步建议'逐项做")


def main():
    parser = argparse.ArgumentParser(description="流程设计助手")
    parser.add_argument("--name", default="", help="flow 名（默认问）")
    parser.add_argument("--demo", action="store_true", help="演示模式（跳过提问）")
    args = parser.parse_args()

    name = args.name or ask("flow 名（小写，snake_case）", default="my-flow" if args.demo else "")
    flow = design(name, demo=args.demo)
    save(flow)


if __name__ == "__main__":
    main()