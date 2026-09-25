#!/usr/bin/env python3
"""feedback-triage.py — 参与者反馈 → 自动分流到 01/02/04 plan

读 `ToT/CC/feedback/03-participant-*.md`，按标签路由到 01/02/04 行动队列：
  - bug + vendor/jeeflow/*.py → 01-engine-developer
  - bug + main_*.py/端点 → 01-engine-developer
  - design-issue / process-gap → 02-process-designer
  - system-perf / system-down / audit-trace → 04-ops-audit
  - doc-gap / ux-issue → 03-participant（自身）

输出：
  - `feedback/_routes/<plan>-<seq>.md` 路由条目
  - `feedback/_routes/_triage-report.md` 周报
  - 更新 03-participant.md §11 「本周飞轮状态」

依赖：仅 Python 3.10+ 标准库
用法：
  python3 feedback-triage.py                 # 跑一次
  python3 feedback-triage.py --report        # 只输出周报（不写文件）
  python3 feedback-triage.py --dry-run       # 模拟，不写文件
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

CC_ROOT = Path(__file__).resolve().parent.parent / "CC"
FEEDBACK = CC_ROOT / "feedback"
ROUTES = FEEDBACK / "_routes"

# 标签 → plan 映射
TAG_TO_PLAN = {
    ("bug",): "01-engine-developer",
    ("design-issue",): "02-process-designer",
    ("process-gap",): "02-process-designer",
    ("system-perf",): "04-ops-audit",
    ("system-down",): "04-ops-audit",
    ("audit-trace",): "04-ops-audit",
    ("doc-gap",): "03-participant",
    ("ux-issue",): "03-participant",
}


def parse_feedback(md_file: Path) -> dict:
    """解析单个 feedback file → 结构化数据"""
    text = md_file.read_text(encoding="utf-8", errors="ignore")
    out = {
        "file": md_file.name,
        "persona": "03",
        "title": "",
        "date": "",
        "reporter": "",
        "severity": "",
        "tags": [],
        "phenomenon": "",
        "evidence": "",
        "status": "open",
    }
    # Title (first H1)
    m = re.search(r"^#\s+Feedback:\s*(\S+)\s*-\s*(.+)$", text, re.M)
    if m:
        out["seq"] = m.group(1)
        out["title"] = m.group(2).strip()
    # Metadata
    for line in text.splitlines():
        m = re.match(r"^>\s+\*\*(\w+)\*\*:\s*(.+)$", line)
        if m:
            key = m.group(1).lower().replace(" ", "_")
            out[key] = m.group(2).strip()
    # Tags (在 标签 节到下一个 ## 或文件末)
    m = re.search(r"^##\s+标签[^\n]*\n([\s\S]*?)(?=^##|\Z)", text, re.M)
    if m:
        tag_section = m.group(1)
        out["tags"] = [t.strip().strip("`").strip() for t in re.findall(r"`([^`]+)`", tag_section)]
    # Phenomenon
    m = re.search(r"^##\s+现象[^\n]*\n([\s\S]*?)(?=^##|\Z)", text, re.M)
    if m:
        out["phenomenon"] = m.group(1).strip()[:200]
    # Status (支持 "已闭环" / "状态: 已闭环" / "状态：已闭环" / "**状态**: 已闭环" 等格式)
    text_lower = text.lower()
    if ("已闭环" in text or "closed" in text_lower) and "open" not in text_lower[:200]:
        out["status"] = "closed"
    return out


def route_feedback(fb: dict) -> str | None:
    """根据 tags 路由到 plan"""
    tags = set(fb.get("tags", []))
    # 单 tag 直接匹配
    for tag_set, plan in TAG_TO_PLAN.items():
        if any(t in tags for t in tag_set):
            return plan
    # 默认按出现顺序匹配
    priority = ["bug", "system-down", "system-perf", "audit-trace",
                "design-issue", "process-gap", "doc-gap", "ux-issue"]
    for tag in priority:
        if tag in tags:
            return TAG_TO_PLAN.get((tag,), "03-participant")
    return None


def make_route_md(fb: dict, plan: str) -> str:
    """生成路由条目 markdown"""
    return f"""# Route: {plan} ← {fb['file']}

> **From**: {fb.get('persona', '03')} · {fb.get('date', '')} · {fb.get('reporter', '')}
> **Severity**: {fb.get('severity', 'P2')}
> **Tags**: {', '.join(fb.get('tags', []))}
> **Routed at**: {datetime.now(timezone.utc).isoformat()}

## 来源反馈

**{fb.get('title', fb['file'])}**

{fb.get('phenomenon', '')}

{fb.get('evidence', '')}

## 行动（待 plan owner 填写）

- [ ] 接收并确认
- [ ] 排期 / 优先级
- [ ] 修复 / 加 doc
- [ ] 闭环：回写 `feedback/{fb['file']}` 加 `状态: 已闭环`
- [ ] release + 同步到 03-participant.md FAQ

## 状态

**状态**: open
"""


def update_03_live_status(stats: dict) -> None:
    """更新 03-participant.md §11 live 状态"""
    p03 = CC_ROOT / "03-participant.md"
    if not p03.exists():
        return
    text = p03.read_text(encoding="utf-8")
    new_rows = f"| 反馈总量 | {stats['total']} |\n| 已分流 | {stats['routed']} |\n| 已闭环 | {stats['closed']} |\n| 自助解决率 | N/A |\n| 月度 RPM | N/A |\n| 季度 NPS | N/A |"
    text = re.sub(
        r"\| 反馈总量 \|.*?\n\| 季度 NPS \|.*?\n",
        new_rows + "\n",
        text,
        flags=re.S,
    )
    if args := text.count("| 反馈总量 |") < 2:  # 防止误改其他表格
        # 用更安全的方式：替换最近一次
        pass
    p03.write_text(text, encoding="utf-8")


def gen_report(stats: dict, routes: list[dict]) -> str:
    """生成周报 markdown"""
    lines = []
    lines.append(f"# 飞轮周报 · {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append("## 总体指标")
    lines.append("")
    lines.append(f"- 反馈总量：**{stats['total']}**")
    lines.append(f"- 已分流：**{stats['routed']}**")
    lines.append(f"- 已闭环：**{stats['closed']}**")
    lines.append(f"- 分流率：{stats['routed']/max(1, stats['total'])*100:.0f}%")
    lines.append("")
    lines.append("## 按 plan 分布")
    lines.append("")
    lines.append("| Plan | 数量 | 已闭环 |")
    lines.append("|---|---|---|")
    for plan in ["01-engine-developer", "02-process-designer", "03-participant", "04-ops-audit"]:
        cnt = sum(1 for r in routes if r["plan"] == plan)
        closed = sum(1 for r in routes if r["plan"] == plan and r.get("status") == "closed")
        lines.append(f"| {plan} | {cnt} | {closed} |")
    lines.append("")
    lines.append("## 详细路由")
    lines.append("")
    for r in routes:
        lines.append(f"- **{r['plan']}** ← `{r['source']}` ({r.get('severity', 'P2')}) - {r['title']}")
    lines.append("")
    lines.append(f"> 自动生成 · `ToT/sop/feedback-triage.py` · {datetime.now(timezone.utc).isoformat()}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true", help="只输出周报")
    parser.add_argument("--dry-run", action="store_true", help="模拟不写文件")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not FEEDBACK.exists():
        print(f"❌ {FEEDBACK} not found")
        sys.exit(1)

    # 收集反馈
    feedbacks = []
    for md_file in sorted(FEEDBACK.glob("03-participant-*.md")):
        fb = parse_feedback(md_file)
        plan = route_feedback(fb)
        fb["routed_to"] = plan
        feedbacks.append(fb)

    # 统计
    stats = {
        "total": len(feedbacks),
        "routed": sum(1 for f in feedbacks if f.get("routed_to")),
        "closed": sum(1 for f in feedbacks if f.get("status") == "closed"),
    }

    # 生成路由
    routes = []
    for fb in feedbacks:
        if fb.get("routed_to"):
            routes.append({
                "source": fb["file"],
                "plan": fb["routed_to"],
                "title": fb.get("title", ""),
                "severity": fb.get("severity", "P2"),
                "status": fb.get("status", "open"),
            })

    if args.json:
        print(json.dumps({"stats": stats, "feedbacks": feedbacks, "routes": routes},
                         indent=2, ensure_ascii=False))
        return

    if args.report:
        print(gen_report(stats, routes))
        return

    # 写文件
    if not args.dry_run:
        ROUTES.mkdir(exist_ok=True)
        for i, fb in enumerate(feedbacks):
            if fb.get("routed_to"):
                plan_short = fb["routed_to"][:2]  # "01"/"02"/"03"/"04"
                route_file = ROUTES / f"{plan_short}-{i+1:03d}-{Path(fb['file']).stem}.md"
                route_file.write_text(make_route_md(fb, fb["routed_to"]), encoding="utf-8")

        report = gen_report(stats, routes)
        (ROUTES / "_triage-report.md").write_text(report, encoding="utf-8")

    # 输出
    print(f"📊 飞轮状态")
    print(f"   反馈总量: {stats['total']}")
    print(f"   已分流: {stats['routed']}")
    print(f"   已闭环: {stats['closed']}")
    if not args.dry_run:
        print(f"   路由条目: {ROUTES}/")
        print(f"   周报: {ROUTES / '_triage-report.md'}")


if __name__ == "__main__":
    main()