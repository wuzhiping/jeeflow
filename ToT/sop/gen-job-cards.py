#!/usr/bin/env python3
"""gen-job-cards.py

读 ToT/flows/fdep.json + fdep/NODES.md + fdp/RESPONSES.md → 批量产出 job_card_<node>.md
到 fdep/job_cards/。

输出卡片结构与 README.md §5 Job Card 模板一致（8 节）。

用法：
  python3 ToT/sop/gen-job-cards.py [--force]

选项：
  --force    覆盖已存在的 job_card_*.md（默认跳过，保留手写卡）

关联：
  ToT/flows/fdep/README.md §5 — Job Card 模板
  ToT/flows/fdep/CHANGELOG.md — v0.6.2 + Job Cards 子目录 记录
  ToT/sop/flow-folder.md — 流程定义组织规范
"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent  # ToT/
FDEP_DIR = BASE / "flows" / "fdep"
JSON_PATH = BASE / "flows" / "fdep.json"
NODES_MD = FDEP_DIR / "NODES.md"
RESPONSES_MD = FDEP_DIR / "RESPONSES.md"
CARDS_DIR = FDEP_DIR / "job_cards"
TEMPLATE_MD = FDEP_DIR / "README.md"


# ---------- NODES.md 解析 ----------
def parse_nodes_md(text: str) -> dict:
    """解析 NODES.md，返回 {node_id: {desc, input, output, steps, notes, role, artifact_path}}"""
    result = {}
    # 匹配每个节点段: ## <id>（snaker:task）...\n---\n
    pattern = re.compile(
        r"## (\w+)\uff08snaker:task\uff09\s*\n(.*?)\n---\n",
        re.DOTALL,
    )
    for m in pattern.finditer(text):
        node_id = m.group(1)
        body = m.group(2)
        result[node_id] = {
            "desc": _extract(body, r"-\s*\*\*说明\*\*\uff1a(.*)"),
            "input": _extract(body, r"-\s*\*\*输入\*\*\uff1a(.*)"),
            "output": _extract(body, r"-\s*\*\*输出\*\*\uff1a(.*)"),
            "steps": _extract_list(body, r"-\s*\*\*工作步骤\*\*\uff1a"),
            "notes": _extract_list(body, r"-\s*\*\*注意事项\*\*\uff1a"),
            "role": _extract(body, r"-\s*\*\*关联角色\*\*\uff1a(.*)"),
            "artifact_path": _extract(body, r"-\s*\*\*关联产出物路径\*\*\uff1a(.*)"),
            "tdd": _extract(body, r"-\s*\*\*TDD \*\*\uff1a(.*)"),
        }
    return result


def _extract(body: str, pattern: str) -> str:
    m = re.search(pattern, body)
    return m.group(1).strip() if m else ""


def _extract_list(body: str, header_pattern: str) -> list:
    """提取 '工作步骤' / '注意事项' 这种 header 下的列表项"""
    m = re.search(header_pattern + r"\s*\n(.*?)(?=\n-\s*\*\*|\Z)", body, re.DOTALL)
    if not m:
        return []
    block = m.group(1)
    # 匹配 "1. xxx" 或 "  - xxx"
    items = re.findall(r"(?:^\s*\d+\.\s+|^  -\s+)(.*?)$", block, re.MULTILINE)
    return [i.strip() for i in items if i.strip()]


# ---------- RESPONSES.md 解析（§X.2.1 Decision Mem 模板）----------
def parse_decision_mems(text: str) -> dict:
    """解析 RESPONSES.md 的 §X.2.1 Decision Mem 模板，返回 {node_id: json_str}"""
    result = {}
    # 匹配: ### <X>.2.1 Decision Mem 详情（v1.0 lite）\n\n```json\n{...}\n```
    pattern = re.compile(
        r"### (\d+)\.2\.1 Decision Mem \u8be6\u60c5\uff08v1\.0 lite\uff09\s*\n+```json\n(.*?)\n```",
        re.DOTALL,
    )
    for m in pattern.finditer(text):
        node_num = int(m.group(1))
        json_str = m.group(2)
        node_id = NUM_TO_NODE.get(node_num)
        if node_id:
            result[node_id] = json_str
    return result


# fdep.json 节点序号 → 节点名（按 §1/§2/... 顺序）
NUM_TO_NODE = {
    1: "start",  # 不生成
    2: "stage_intake",
    3: "decision_intake",  # 不生成
    4: "stage_pm",
    5: "stage_design",
    6: "stage_dev",
    7: "stage_review",
    8: "stage_feedback",
    9: "end",  # 不生成
    10: "end_rejected",  # 不生成
}


# ---------- fdep.json 解析 ----------
def parse_flow_edges(text: str) -> dict:
    """解析 fdep.json 的边，返回 {node_id: {in: [...], out: [...]}}"""
    flow = json.loads(text)
    nodes = {n["id"]: n for n in flow["nodes"]}
    edges_map = {nid: {"in": [], "out": []} for nid in nodes}

    for e in flow.get("edges", []):
        s = e.get("sourceNodeId") or e.get("source")
        t = e.get("targetNodeId") or e.get("target")
        if s and t:
            edges_map[s]["out"].append(t)
            edges_map[t]["in"].append(s)

    return nodes, edges_map


# ---------- 卡片渲染 ----------
def render_card(node_id: str, node_def: dict, edges_map: dict,
                nodes_info: dict, mem_template: str) -> str:
    """渲染单张 Job Card"""
    props = node_def.get("properties", {})
    # text.value 仅用于节点名展示，不参与 SPI 角色等元信息输出
    # （避免 future 回归：text.value 啰嗦版也不会再自动生成 SPI 角色信息）
    # SPI 角色 / assignee 等元信息走 NODES.md "关联角色" 行 + properties.assignee

    assignee = props.get("assignee", "?")
    stage = props.get("stage", "?")
    artifact = props.get("artifact", "?")
    storage = props.get("storage", "?")
    exit_criteria = props.get("exitCriteria", "?")
    form = props.get("form", "?")

    # 前节点 / 后节点
    prev_nodes = edges_map.get(node_id, {}).get("in", [])
    next_nodes = edges_map.get(node_id, {}).get("out", [])
    prev_name = prev_nodes[0] if prev_nodes else "start"
    next_name = next_nodes[0] if next_nodes else "end"

    # 哪些节点类型不需要 job card
    NON_TASK_NODES = {"start", "end", "end_rejected", "decision_intake"}

    # 上一节点的 job_card_url（用于 §2 输入）
    prev_card_url = (
        f"ToT/flows/fdep/job_cards/job_card_{prev_name}.md"
        if prev_name not in NON_TASK_NODES else None
    )

    # 下一节点的 job_card_url（用于 §5 next_handoff）
    next_card_url = (
        f"ToT/flows/fdep/job_cards/job_card_{next_name}.md"
        if next_name not in NON_TASK_NODES else None
    )

    # 下一节点的 assignee（用于 §5 next_handoff）
    next_assignee = "?"
    if next_name in edges_map:
        next_node = None
        for nid, n in [("stage_intake", 0), ("stage_pm", 0), ("stage_design", 0),
                       ("stage_dev", 0), ("stage_review", 0), ("stage_feedback", 0),
                       ("end", 0), ("end_rejected", 0)]:
            if nid == next_name:
                pass
        # 简化：从 NODES info 拿
    next_artifact = "?"

    # 拿 NODES.md 信息
    info = nodes_info.get(node_id, {})
    desc = info.get("desc", "")
    input_text = info.get("input", "")
    output_text = info.get("output", "")
    steps = info.get("steps", [])
    notes = info.get("notes", [])
    role = info.get("role", "")

    # 拿下一节点的 artifact 名（用作 handoff.input_files 提示）
    next_info = nodes_info.get(next_name, {}) if next_name in nodes_info else {}
    next_input_text = next_info.get("input", "?")

    # 拿前节点的 artifact 名
    prev_info = nodes_info.get(prev_name, {}) if prev_name in nodes_info else {}

    # ----- 构建 markdown -----
    lines = []
    lines.append(f"# Job Card \u00b7 {node_id}")
    lines.append("")
    lines.append(f"> **\u8282\u70b9\u5b9a\u4e49**\uff1a[../../fdep.json](../../fdep.json) `nodes[id={node_id}]`")
    lines.append(f"> **\u8282\u70b9\u624b\u518c**\uff1a[../NODES.md#{node_id}](../NODES.md#{node_id}snaker-task)")
    lines.append(f"> **Decision Mem \u534f\u8bae**\uff1a[../RESPONSES.md \u00a70](../RESPONSES.md)")
    lines.append(f"> **\u6267\u884c\u8005**\uff1a`{assignee}`")
    lines.append(f"> **\u89d2\u8272**\uff1a{role or '(unknown)'}")
    lines.append(f"> **\u89e6\u53d1**\uff1a{prev_name} \u5b8c\u6210\u540e \u2192 \u5f15\u64ce\u81ea\u52a8\u52a0\u5165 todoList\uff08operator={assignee}\uff09")
    lines.append("")
    lines.append("---")
    lines.append("")

    # §1 身份
    lines.append("## 1. \u4f60\u7684\u8eab\u4efd")
    lines.append("")
    lines.append("```yaml")
    lines.append(f"- node: {node_id}")
    lines.append("- type: snaker:task")
    lines.append(f"- assignee: {assignee}")
    lines.append(f"- stage: {stage}")
    lines.append(f"- form: {form}")
    lines.append("- trigger: \u62fe\u8d77 todoList \u4e2d taskName=\"" + node_id + "\" \u4e14 operator=" + assignee)
    lines.append("```")
    lines.append("")

    # §2 输入
    lines.append("## 2. \u4f60\u7684\u8f93\u5165")
    lines.append("")
    lines.append("\u8bfb\u8fd9\u4e9b\u624d\u80fd\u5e72\u6d3b\uff1a")
    lines.append("")
    lines.append("| \u6765\u6e90 | \u5fc5\u8bfb | \u7528\u9014 |")
    lines.append("|------|------|------|")
    if prev_card_url:
        lines.append(f"| \u524d\u4efb\u52a1\uff1a{prev_name} \u7684 `variable.decision_memo.next_handoff` | \u2705 | \u524d\u8282\u70b9\u7559\u7ed9\u4f60\u7684\u52a8\u6001\u4fe1\u606f |")
    else:
        lines.append(f"| \u524d\u4efb\u52a1\uff1a{prev_name} | \u2705 | \u5207\u5165\u70b9\u4fe1\u606f |")
    lines.append(f"| \u6d41\u7a0b\u5b9a\u4e49\uff1a[../../fdep.json](../../fdep.json) \u672c\u8282\u70b9 props | \u2705 | \u8282\u70b9\u7ed3\u6784 + assignee + artifact\uff1a{artifact} |")
    lines.append(f"| NODES.md \u672c\u8282\u70b9 | \u2705 | \u8bfb\u300a\u5de5\u4f5c\u6b65\u9aa4\u300b\u4e0e\u300a\u6ce8\u610f\u4e8b\u9879\u300b |")
    lines.append("")

    # §3 目标
    lines.append("## 3. \u4f60\u7684\u76ee\u6807")
    lines.append("")
    lines.append("```yaml")
    lines.append(f"- produce: {artifact}")
    lines.append(f"- storage: {storage}")
    lines.append(f"- form: {form}")
    lines.append(f"- exit_criteria: {exit_criteria}")
    lines.append("```")
    lines.append("")
    if desc:
        lines.append(f"> \u8bf4\u660e\uff1a{desc}")
        lines.append("")

    # §4 checklist
    lines.append("## 4. \u4f60\u7684 checklist")
    lines.append("")
    lines.append("\u6309\u987a\u5e8f\u6267\u884c\uff1a")
    lines.append("")
    if steps:
        for i, s in enumerate(steps, 1):
            lines.append(f"- [ ] **Step {i}**\uff1a{s}")
    else:
        lines.append("- [ ] \u8bfb\u524d\u8282\u70b9\u7684 next_handoff")
        lines.append("- [ ] \u8d77\u8349\u672c\u8282\u70b9\u4ea7\u51fa\uff08\u53c2\u8003 [RESPONSES.md \u00a7X.2.1](../RESPONSES.md) \u6a21\u677f\uff09")
        lines.append("- [ ] \u843d\u6863\u5230 " + storage)
        lines.append("- [ ] \u8c03 `processTask/execute` \u63a8\u8fdb\uff08\u4f53\u53c2\u8003 \u00a75\uff09")
    lines.append("")
    if notes:
        lines.append("> \u6ce8\u610f\u4e8b\u9879\uff08\u4ece NODES.md \u62c9\u53d6\uff09\uff1a")
        for n in notes:
            lines.append(f"> - {n}")
        lines.append("")

    # §5 产出（execute body）
    lines.append("## 5. \u4f60\u7684\u4ea7\u51fa\uff08execute body\uff09")
    lines.append("")
    lines.append(f"\u8c03\u7528 `processTask/execute` \u65f6\uff0cbody \u5fc5\u987b\u5305\u542b\uff1a")
    lines.append("")
    if mem_template:
        # RESPONSES.md §X.2.1 模板本身就是顶层 3 字段（decision_reason/decision_memo/context）
        # 把这些字段嵌入 execute body，与 processTaskId/operator/submitType 同级
        # §X.2.1 模板形如 "{ ... }"，需要剥掉外层大括号后逐字段插入
        # 同时把作为 value 的 <X> 占位符加引号（RESPONSES.md 模板可读性 > 严格 JSON）
        lines.append("```json")
        lines.append("{")
        lines.append('  "processTaskId": "<\u4ece todoList \u62ff>",')
        lines.append(f'  "operator": "{assignee}",')
        lines.append('  "submitType": 1,')
        lines.append("")
        # 剥掉外层 { 和 }
        stripped = mem_template.strip()
        if stripped.startswith("{"):
            stripped = stripped[1:]
        if stripped.endswith("}"):
            stripped = stripped[:-1]
        # 把作为 value 的 <X> 占位符加引号（`: <X>` → `: "<X>"`）
        stripped = re.sub(r'(:\s*)(<\w+>)(\s*,?)', r'\1"\2"\3', stripped)
        # 替换字符串内的占位符示例
        stripped = stripped.replace('<date>', '<YYYY-MM-DD>').replace('<id>', '<taskId>')
        # 缩进到第二层
        indented = stripped.strip().replace("\n", "\n  ")
        lines.append("  " + indented + ",")
        lines.append("")
        lines.append('  "next_handoff": {')
        if next_card_url:
            lines.append(f'    "next_node": "{next_name}",')
            lines.append(f'    "job_card_url": "{next_card_url}",')
            lines.append(f'    "input_files": ["{storage}<date>/<taskId>/<\u672c\u8282\u70b9\u4ea7\u51fa>"]')
        else:
            # 终态节点（end/end_rejected）只有 next_node，无 card URL
            lines.append(f'    "next_node": "{next_name}",')
            lines.append('    "is_terminal": true')
        lines.append('  },')
        lines.append("")
        lines.append(f'  "job_card_url": "ToT/flows/fdep/job_cards/job_card_{node_id}.md"')
        lines.append("}")
        lines.append("```")
        lines.append("")
        lines.append(f"> \u4ee5\u4e0a\u662f\u300aRESPONSES.md \u00a7X.2.1 Decision Mem \u6a21\u677f\u300b\u539f\u59cb\u5b57\u6bb5 + \u672c\u8282\u70b9\u7684 `next_handoff` \u5b57\u6bb5\u3002\u8bf7\u66ff\u6362\u4e3a\u5b9e\u9645\u503c\u3002")
    else:
        lines.append("```json")
        lines.append("{")
        lines.append('  "processTaskId": "<\u4ece todoList \u62ff>",')
        lines.append(f'  "operator": "{assignee}",')
        lines.append('  "submitType": 1,')
        lines.append('  "decision_reason": "<\u672c\u8282\u70b9\u51b3\u7b56\u7406\u7531>",')
        lines.append('  "decision_memo": {},')
        lines.append('  "context": {},')
        lines.append("")
        lines.append(f'  "job_card_url": "ToT/flows/fdep/job_cards/job_card_{node_id}.md"')
        lines.append("}")
        lines.append("```")
        lines.append("")

    # §6 handoff
    lines.append("## 6. \u4f60\u7684 handoff")
    lines.append("")
    lines.append(f"\u4e0b\u4e00\u8282\u70b9\uff1a**{next_name}**")
    if next_card_url:
        lines.append("")
        lines.append("\u4ed6\u4eec\u9700\u8981\u7684\u8f93\u5165\uff1a")
        lines.append(f"- \u4f60\u7684\u4ea7\u51fa\uff08{artifact}\uff09\u5728 `{storage}`")
        lines.append(f"- \u4ed6\u4eec\u7684\u6267\u884c\u5361 \u2192 [../job_cards/job_card_{next_name}.md](../job_cards/job_card_{next_name}.md)")
        lines.append("")
        lines.append("\u4f60\u63d0\u4ea4 execute \u540e\uff0c\u5f15\u64ce\u81ea\u52a8\u521b\u5efa\u4e0b\u4e00\u8282\u70b9\u7684 task\u3002\u8be5 next_handoff \u5b57\u6bb5\u5df2\u5728 \u00a75 \u4f8b\u4e2d\u7ed9\u51fa\u3002")
    else:
        lines.append("")
        lines.append(f"\u4ed6\u4eec\u662f\u7ec8\u70b9\u8282\u70b9\uff08{next_name}\uff09\uff0c\u65e0\u9700 handoff \u4f53\u3002")
    lines.append("")

    # §7 关联
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 7. \u5173\u8054\u6587\u6863 + SOP")
    lines.append("")
    lines.append("| \u6587\u6863 | \u7528\u9014 |")
    lines.append("|------|------|")
    lines.append(f"| [../NODES.md#{node_id}](../NODES.md#{node_id}snaker-task) | \u8282\u70b9\u7684\u7eaf\u6587\u672c\u5de5\u4f5c\u624b\u518c |")
    lines.append(f"| [../RESPONSES.md](../RESPONSES.md) | AI \u8d77\u8349\u54cd\u5e94\u65f6\u7684\u6a21\u677f + Decision Mem \u534f\u8bae \u00a70 |")
    lines.append("| [../../../sop/node-execution.md](../../../sop/node-execution.md) | \u4f7f\u7528 Job Card \u7684 6 \u6b65\u901a\u7528 SOP\uff08\u5f85\u5199\uff09 |")
    lines.append("| [../../../mapping.md](../../../mapping.md) | R \u89d2\u8272 \u2194 SPI \u2194 \u7528\u6237 \u4e09\u5c42\u6620\u5c04 |")
    lines.append("| [../README.md \u00a75](../README.md#5-job-card-\u6a21\u677f-v10) | \u5361\u7247\u7ed3\u6784\u4e0e\u547d\u540d\u89c4\u5219 |")
    lines.append("")

    # §8 变更
    lines.append("---")
    lines.append("")
    lines.append("## 8. \u53d8\u66f4\u65e5\u5fd7")
    lines.append("")
    lines.append("| \u7248\u672c | \u65e5\u671f | \u53d8\u66f4 |")
    lines.append("|------|------|------|")
    lines.append("| v0.1 | 2026-09-22 | \u7531 `gen-job-cards.py` \u81ea\u52a8\u751f\u6210\uff08\u57fa\u4e8e fdep.json + NODES.md + RESPONSES.md \u00a7X.2.1\uff09 |")
    lines.append("")

    return "\n".join(lines)


# ---------- 主流程 ----------
def main():
    force = "--force" in sys.argv

    # 1. 准备
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    flow_json = JSON_PATH.read_text(encoding="utf-8")
    nodes_md = NODES_MD.read_text(encoding="utf-8")
    responses_md = RESPONSES_MD.read_text(encoding="utf-8")

    # 2. 解析
    nodes_def, edges_map = parse_flow_edges(flow_json)
    nodes_info = parse_nodes_md(nodes_md)
    mems = parse_decision_mems(responses_md)

    # 3. 过滤只生成 task 节点
    task_ids = [nid for nid, n in nodes_def.items() if n.get("type") == "snaker:task"]

    # 4. 按 fdep.json 中节点顺序遍历
    flow = json.loads(flow_json)
    ordered_task_ids = [n["id"] for n in flow["nodes"] if n.get("type") == "snaker:task"]

    written, skipped = [], []
    for nid in ordered_task_ids:
        out_path = CARDS_DIR / f"job_card_{nid}.md"
        if out_path.exists() and not force:
            skipped.append(out_path.name)
            continue

        card = render_card(
            node_id=nid,
            node_def=nodes_def[nid],
            edges_map=edges_map,
            nodes_info=nodes_info,
            mem_template=mems.get(nid, ""),
        )
        out_path.write_text(card, encoding="utf-8")
        written.append(out_path.name)

    # 5. 报告
    print(f"\u2705 \u751f\u6210 {len(written)} \u5f20\u5361\uff1a")
    for n in written:
        print(f"  + {n}")
    if skipped:
        print(f"\u23ed\ufe0f \u8df3\u8fc7 {len(skipped)} \u5f20\u5df2\u5b58\u5728\u7684\u5361\uff08\u4f7f\u7528 --force \u8986\u76d6\uff09\uff1a")
        for n in skipped:
            print(f"  - {n}")


if __name__ == "__main__":
    main()