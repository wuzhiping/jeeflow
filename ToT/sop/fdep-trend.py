#!/usr/bin/env python3
"""fdep-trend.py — 02-process-designer 的 FDEP 趋势扫描（A6）

每周扫 `/api/admin/stats/overview` × N 个流程 → 输出退化榜单
输出 Markdown：流程名 / 7d 趋势 / 是否需要改进

数据源：
  - 实际 API（如果有 ALIVE_URL 环境变量）
  - 否则模拟：从 ToT/docs/spec/kpi-dictionary.md 读取基线阈值

输出位置：
  - ToT/sop/snapshots/fdep-trend-<YYYY-MM-DD>.md（每次运行）
  - ToT/docs/spec/fdep-trend-latest.md（最新一份，覆盖式）

依赖：仅 Python 3.10+ 标准库
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SNAPSHOTS = REPO_ROOT / "ToT" / "sop" / "snapshots"
LATEST = REPO_ROOT / "ToT" / "docs" / "spec" / "fdep-trend-latest.md"

# 监控的流程定义（来自上游/本仓通用场景）
MONITORED_DEFINES = [
    {"id": 1, "name": "请假（≤3 天 2 级）", "category": "leave"},
    {"id": 2, "name": "请假（4-7 天 3 级）", "category": "leave"},
    {"id": 3, "name": "报销（小额）", "category": "expense"},
    {"id": 4, "name": "报销（大额）", "category": "expense"},
    {"id": 5, "name": "合同审批", "category": "contract"},
    {"id": 6, "name": "立项", "category": "project"},
]


def fetch_stats_via_api(alive_url: str) -> dict:
    """从 alive API 拿数据（如配置了 ALIVE_URL）"""
    import urllib.request
    try:
        with urllib.request.urlopen(f"{alive_url}/api/admin/stats/overview", timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"⚠️ 无法访问 {alive_url}：{e}", file=sys.stderr)
        return {}


def simulate_stats() -> dict:
    """模拟数据（无 ALIVE_URL 时）"""
    # 基于 ToT/docs/spec/kpi-dictionary.md 的阈值生成示例数据
    return {
        "total": 1234,
        "running": 50,
        "completedToday": 23,
        "by_define": [
            {"id": 1, "name": "请假（≤3 天 2 级）", "running": 5, "backlog_rate": 0.04, "p95_duration_h": 4.2},
            {"id": 2, "name": "请假（4-7 天 3 级）", "running": 12, "backlog_rate": 0.10, "p95_duration_h": 22.5},  # 超过阈值
            {"id": 3, "name": "报销（小额）", "running": 8, "backlog_rate": 0.06, "p95_duration_h": 18.0},
            {"id": 4, "name": "报销（大额）", "running": 15, "backlog_rate": 0.12, "p95_duration_h": 48.0},  # 接近阈值
            {"id": 5, "name": "合同审批", "running": 6, "backlog_rate": 0.05, "p95_duration_h": 60.0},
            {"id": 6, "name": "立项", "running": 4, "backlog_rate": 0.03, "p95_duration_h": 100.0},
        ],
    }


def analyze(stats: dict) -> list[dict]:
    """分析每个流程，给出是否需要改进"""
    results = []
    for d in stats.get("by_define", []):
        backlog = d.get("backlog_rate", 0)
        p95 = d.get("p95_duration_h", 0)
        # 基于 KPI 字典阈值
        needs_improve = False
        reasons = []
        if backlog >= 0.15:
            needs_improve = True
            reasons.append(f"积压率 {backlog*100:.0f}% 超过 15% 警告线")
        elif backlog >= 0.05:
            reasons.append(f"积压率 {backlog*100:.0f}% 需关注")
        if p95 > 24:
            needs_improve = True
            reasons.append(f"P95 时长 {p95:.0f}h 超过 24h SLA")
        elif p95 > 4:
            reasons.append(f"P95 时长 {p95:.0f}h 需关注")
        results.append({
            "id": d["id"],
            "name": d["name"],
            "running": d.get("running", 0),
            "backlog_rate": backlog,
            "p95_duration_h": p95,
            "needs_improve": needs_improve,
            "reasons": reasons,
        })
    # 按 needs_improve 排序（最需要改进在前）
    results.sort(key=lambda x: (not x["needs_improve"], x["backlog_rate"]), reverse=True)
    return results


def render_table(results: list[dict], date: str) -> str:
    """渲染 Markdown 表格"""
    lines = []
    lines.append(f"# FDEP 趋势报告 · {date}")
    lines.append("")
    lines.append("> 自动生成 · `ToT/sop/fdep-trend.py` · 02-process-designer A6")
    lines.append("> 数据源：`/api/admin/stats/overview` × N 个流程")
    lines.append("> 阈值参考：[`../../docs/spec/kpi-dictionary.md`](../../docs/spec/kpi-dictionary.md)")
    lines.append("")
    lines.append("## 退化榜单")
    lines.append("")
    lines.append("| 排名 | 流程 | running | 积压率 | P95 时长 | 是否需改进 | 原因 |")
    lines.append("|---|---|---|---|---|---|---|")
    rank = 1
    for r in results:
        if not r["needs_improve"]:
            continue
        reasons = "; ".join(r["reasons"]) if r["reasons"] else "-"
        # 转义 markdown 表格里的 |
        reasons = reasons.replace("|", "\\|")
        badge = "🔴 **立即**" if r["backlog_rate"] >= 0.15 or r["p95_duration_h"] > 48 else "🟡 关注"
        lines.append(f"| {rank} | {r['name']} | {r['running']} | {r['backlog_rate']*100:.0f}% | {r['p95_duration_h']:.0f}h | {badge} | {reasons} |")
        rank += 1
    if rank == 1:
        lines.append("| - | - | - | - | - | 🟢 无 | 所有流程健康 |")
    lines.append("")
    lines.append("## 全部流程（健康）")
    lines.append("")
    lines.append("| 流程 | running | 积压率 | P95 时长 |")
    lines.append("|---|---|---|---|")
    for r in results:
        if not r["needs_improve"]:
            lines.append(f"| {r['name']} | {r['running']} | {r['backlog_rate']*100:.0f}% | {r['p95_duration_h']:.0f}h |")
    lines.append("")
    lines.append("## 行动建议")
    lines.append("")
    improving = [r for r in results if r["needs_improve"]]
    if improving:
        for r in improving[:3]:
            lines.append(f"- **{r['name']}**：")
            if r["backlog_rate"] >= 0.15:
                lines.append(f"  - 立即介入（积压率 {r['backlog_rate']*100:.0f}%）")
                lines.append(f"  - 参考 [`../CC/runbook.md §流程积压飙升`](../CC/runbook.md)")
            if r["p95_duration_h"] > 24:
                lines.append(f"  - P95 {r['p95_duration_h']:.0f}h 超 SLA → 考虑：①简化审批级数 ②加跳过规则")
            lines.append(f"  - 通知对应流程管理员（02 张 HR 类角色）")
    else:
        lines.append("- 🟢 全部健康，继续维护")
    lines.append("")
    lines.append(f"> 生成时间：{datetime.now(timezone.utc).isoformat()}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=str(SNAPSHOTS), help="归档目录")
    parser.add_argument("--latest", default=str(LATEST), help="latest 输出路径")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    alive_url = os.environ.get("ALIVE_URL")
    if alive_url:
        print(f"📡 抓取 {alive_url} ...", file=sys.stderr)
        stats = fetch_stats_via_api(alive_url)
    else:
        print("⚠️ 未设置 ALIVE_URL，使用模拟数据", file=sys.stderr)
        stats = simulate_stats()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    results = analyze(stats)
    content = render_table(results, today)

    if args.json:
        print(json.dumps({"date": today, "results": results}, indent=2, ensure_ascii=False))
        return

    # 写归档
    archive = Path(args.output_dir) / f"fdep-trend-{today}.md"
    archive.parent.mkdir(exist_ok=True)
    archive.write_text(content, encoding="utf-8")
    print(f"✅ 归档：{archive}")

    # 写 latest
    latest = Path(args.latest)
    latest.parent.mkdir(exist_ok=True)
    latest.write_text(content, encoding="utf-8")
    print(f"✅ Latest：{latest}")

    # 摘要
    improving = sum(1 for r in results if r["needs_improve"])
    print(f"📊 退化榜单：{improving} 个流程需要改进（共 {len(results)} 个监控）")


if __name__ == "__main__":
    main()