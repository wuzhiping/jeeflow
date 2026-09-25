#!/usr/bin/env python3
"""health-report.py — 生成 ToT/docs/REPORT.html 可视化健康报告

从 snapshots/_health_*.json 历史 + 当前 health-check.py 结果输出自包含 HTML：
  - 整体评分卡（gauge + 等级）
  - 5 维度明细（progress bar + 详情）
  - 历史趋势 SVG 折线图
  - API 覆盖表格
  - 改进建议清单

依赖：仅 Python 3.10+ 标准库（json / pathlib / datetime / html）
输出：单文件 HTML，零外部依赖（CSS + SVG 内联），可离线打开

用法：
  python3 health-report.py
  python3 health-report.py --output /path/to/REPORT.html
  python3 health-report.py --json     # JSON 中间数据
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOT_DOCS = REPO_ROOT / "ToT" / "docs"
SNAPSHOTS = REPO_ROOT / "ToT" / "sop" / "snapshots"
OUTPUT = TOT_DOCS / "REPORT.html"


def run_health() -> dict:
    """跑 health-check.py --json 拿当前状态"""
    checker = REPO_ROOT / "ToT" / "sop" / "health-check.py"
    r = subprocess.run(
        ["python3", str(checker), "--json"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60,
    )
    if r.returncode != 0:
        print(f"❌ health-check failed: {r.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(r.stdout)


def load_history() -> list[dict]:
    """从 snapshots/_health_*.json 加载历史"""
    history = []
    if not SNAPSHOTS.exists():
        return history
    for f in sorted(SNAPSHOTS.glob("_health_*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["_source_file"] = f.name
            history.append(data)
        except Exception:
            continue
    return history


def score_color(score: int) -> str:
    if score >= 85: return "#22c55e"  # green
    if score >= 60: return "#eab308"  # yellow
    return "#ef4444"                   # red


def grade_emoji(score: int) -> str:
    if score >= 85: return "🟢"
    if score >= 60: return "🟡"
    return "🔴"


def render_gauge(score: int, grade: str) -> str:
    """SVG 半圆 gauge（半径 80）"""
    cx, cy, r = 100, 100, 80
    color = score_color(score)
    pct = score / 100
    # 半圆弧：180° → 360° 表示 0→100
    import math
    angle = math.pi * (1 - pct)  # 180° at 0, 0° at 100
    end_x = cx - r * math.cos(angle)
    end_y = cy - r * math.sin(angle)
    large_arc = 1 if pct > 0.5 else 0
    return f"""
    <svg viewBox="0 0 200 130" class="gauge">
      <path d="M 20 100 A 80 80 0 0 1 180 100" stroke="#e5e7eb" stroke-width="14" fill="none" />
      <path d="M 20 100 A 80 80 0 {large_arc} 1 {end_x:.1f} {end_y:.1f}" stroke="{color}" stroke-width="14" fill="none" stroke-linecap="round" />
      <text x="100" y="95" text-anchor="middle" font-size="40" font-weight="bold" fill="{color}">{score}</text>
      <text x="100" y="120" text-anchor="middle" font-size="14" fill="#6b7280">/ 100 · {grade}</text>
    </svg>
    """


def render_trend_chart(history: list[dict]) -> str:
    """历史趋势折线图（SVG）"""
    if not history:
        return "<p class=\"muted\">尚无历史数据</p>"
    width, height = 600, 200
    margin = 30
    n = len(history)
    if n == 1:
        # 单点画水平线
        score = history[0]["overall_score"]
        return f"""
        <svg viewBox="0 0 {width} {height}" class="chart">
          <line x1="{margin}" y1="{height//2}" x2="{width-margin}" y2="{height//2}" stroke="#3b82f6" stroke-width="2" />
          <text x="{width//2}" y="{height//2 - 10}" text-anchor="middle" fill="#6b7280">{score}/100 (单点)</text>
        </svg>
        """
    xs = [margin + (width - 2*margin) * i / (n - 1) for i in range(n)]
    ys = [height - margin - (height - 2*margin) * h["overall_score"] / 100 for h in history]
    points = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    # Y 轴刻度
    y_labels = ""
    for v in [0, 50, 100]:
        y = height - margin - (height - 2*margin) * v / 100
        y_labels += f'<text x="5" y="{y+4}" font-size="10" fill="#9ca3af">{v}</text>'
        y_labels += f'<line x1="{margin}" y1="{y}" x2="{width-margin}" y2="{y}" stroke="#f3f4f6" stroke-width="1" />'
    # X 轴 labels（首尾 + 中间）
    x_labels = ""
    for i in [0, n//2, n-1]:
        if i < n:
            ts = history[i]["timestamp"][:10]
            x_labels += f'<text x="{xs[i]:.1f}" y="{height-5}" text-anchor="middle" font-size="10" fill="#9ca3af">{ts}</text>'
    return f"""
    <svg viewBox="0 0 {width} {height}" class="chart">
      {y_labels}
      {x_labels}
      <polyline points="{points}" fill="none" stroke="#3b82f6" stroke-width="2" />
      {''.join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{score_color(history[i]["overall_score"])}" />' for i, (x, y) in enumerate(zip(xs, ys)))}
    </svg>
    """


def render_dimension(dim: dict) -> str:
    score = dim["score"]
    color = score_color(score)
    rec = f'<div class="rec">➜ {dim["recommendation"]}</div>' if dim.get("recommendation") else ""
    # 把 details 展平
    details_html = ""
    for k, v in dim["details"].items():
        if isinstance(v, (list, dict)) and not v:
            continue
        if isinstance(v, dict):
            sub = ", ".join(f"{kk}: {vv}" for kk, vv in v.items() if vv)
            details_html += f'<div class="detail"><span>{k}</span>: {sub}</div>'
        elif isinstance(v, list):
            details_html += f'<div class="detail"><span>{k}</span>: {", ".join(str(x) for x in v[:5])}{"..." if len(v)>5 else ""}</div>'
        else:
            details_html += f'<div class="detail"><span>{k}</span>: {v}</div>'
    return f"""
    <div class="dim-card">
      <div class="dim-header">
        <h3>{dim['name']}</h3>
        <span class="badge" style="background:{color}">{dim['grade']} {score}/100</span>
      </div>
      <div class="bar"><div class="bar-fill" style="width:{score}%;background:{color}"></div></div>
      <div class="dim-details">{details_html}{rec}</div>
      <div class="dim-footer">权重 {dim['weight']}%</div>
    </div>
    """


def render_api_table(current: dict) -> str:
    """API 覆盖明细（从 current details 抽取）"""
    api_dim = next((d for d in current["dimensions"] if d["name"] == "API Coverage"), {})
    details = api_dim.get("details", {})
    total = details.get("total", 0)
    covered = details.get("covered", 0)
    missing = details.get("missing_sample", [])
    pct = int(covered / total * 100) if total else 0
    color = score_color(pct)
    rows = ""
    for m in missing:
        rows += f"<tr><td class='api-name'>{m}</td><td><span class='badge' style='background:#ef4444'>missing</span></td></tr>"
    if not rows:
        rows = "<tr><td colspan='2' class='muted'>✅ 全部覆盖</td></tr>"
    return f"""
    <div class="section">
      <h2>API 覆盖明细</h2>
      <p><strong>{covered} / {total}</strong> 公开 API 已记录（<span style="color:{color}">{pct}%</span>）</p>
      <table class="api-table">
        <thead><tr><th>API</th><th>状态</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """


def render_history_table(history: list[dict]) -> str:
    """历史快照表"""
    if not history:
        return "<p class='muted'>尚无历史数据</p>"
    rows = ""
    for h in history[-15:]:  # 最近 15 条
        s = h["overall_score"]
        color = score_color(s)
        ts = h["timestamp"][:19].replace("T", " ")
        rows += f"<tr><td>{ts}</td><td><strong style='color:{color}'>{s}/100</strong></td><td>{h['overall_grade']}</td></tr>"
    return f"""
    <div class="section">
      <h2>历史快照（最近 15 条）</h2>
      <table class="hist-table">
        <thead><tr><th>时间</th><th>综合分</th><th>等级</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>ToT/docs 健康度报告</title>
<style>
* {{ box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f9fafb; color: #111827; margin: 0; padding: 24px; }}
.container {{ max-width: 1100px; margin: 0 auto; }}
h1 {{ font-size: 28px; margin: 0 0 8px 0; }}
.subtitle {{ color: #6b7280; font-size: 14px; margin-bottom: 24px; }}
.section {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
.section h2 {{ font-size: 18px; margin: 0 0 12px 0; }}
.gauge {{ display: block; margin: 0 auto; max-width: 280px; }}
.bar {{ background: #e5e7eb; border-radius: 6px; height: 10px; margin: 10px 0; overflow: hidden; }}
.bar-fill {{ height: 100%; border-radius: 6px; transition: width 0.3s; }}
.dim-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }}
.dim-card {{ background: white; border-radius: 10px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
.dim-header {{ display: flex; justify-content: space-between; align-items: center; }}
.dim-header h3 {{ margin: 0; font-size: 16px; }}
.badge {{ color: white; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }}
.dim-details {{ font-size: 13px; color: #4b5563; margin-top: 10px; }}
.detail {{ margin: 3px 0; }}
.detail span {{ color: #6b7280; }}
.dim-footer {{ color: #9ca3af; font-size: 12px; margin-top: 8px; }}
.rec {{ background: #fef3c7; border-left: 3px solid #f59e0b; padding: 6px 10px; margin-top: 8px; border-radius: 4px; font-size: 13px; }}
.chart {{ width: 100%; max-width: 600px; height: auto; }}
.api-table, .hist-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
.api-table th, .api-table td, .hist-table th, .hist-table td {{ padding: 6px 10px; text-align: left; border-bottom: 1px solid #f3f4f6; }}
.api-table th, .hist-table th {{ background: #f9fafb; color: #6b7280; font-weight: 600; }}
.api-name {{ font-family: monospace; }}
.muted {{ color: #9ca3af; }}
</style>
</head>
<body>
<div class="container">
  <h1>ToT/docs 健康度报告</h1>
  <div class="subtitle">{timestamp} · 仓库 {repo_name}</div>

  <div class="section">
    {gauge}
  </div>

  <div class="section">
    <h2>5 维度明细</h2>
    <div class="dim-grid">
      {dims_html}
    </div>
  </div>

  <div class="section">
    <h2>历史趋势</h2>
    {trend}
  </div>

  {api_table}

  {history_table}

  <div class="section" style="text-align:center;color:#9ca3af;font-size:12px">
    自动生成 · ToT/sop/health-report.py · 仅 Python 3.10+ 标准库 · 零外部依赖
  </div>
</div>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(OUTPUT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    current = run_health()
    history = load_history()

    if args.json:
        print(json.dumps({"current": current, "history_count": len(history)}, indent=2, ensure_ascii=False))
        return

    score = current["overall_score"]
    grade = current["overall_grade"]
    dims_html = "\n".join(render_dimension(d) for d in current["dimensions"])
    api_table = render_api_table(current)
    history_table = render_history_table(history)
    gauge = render_gauge(score, grade)
    trend = render_trend_chart(history)

    html = HTML_TEMPLATE.format(
        timestamp=current["timestamp"],
        repo_name=REPO_ROOT.name,
        gauge=gauge,
        dims_html=dims_html,
        trend=trend,
        api_table=api_table,
        history_table=history_table,
    )

    Path(args.output).write_text(html, encoding="utf-8")
    size = Path(args.output).stat().st_size
    print(f"✅ REPORT.html generated: {args.output} ({size} bytes)")
    print(f"   Overall: {score}/100 {grade}")
    print(f"   History snapshots: {len(history)}")


if __name__ == "__main__":
    main()