#!/usr/bin/env python3
"""gen-changelog.py — 从 doc-archive-snapshot 累积生成 CHANGELOG.md

按时间顺序遍历 snapshots 目录，每次 snapshot vs 前一个，输出：
- 新增文件清单
- 修改文件清单（行数 delta）
- drift 变化（OK / NEAR_MATCH / NO_DEF 增减）
- 关键 commit 信息

输出 Markdown CHANGELOG.md，可直接 commit 到 ToT/docs/CHANGELOG.md

用法：
    python3 ToT/sop/gen-changelog.py > ToT/docs/CHANGELOG.md
    python3 ToT/sop/gen-changelog.py --output ToT/docs/CHANGELOG.md
    python3 ToT/sop/gen-changelog.py --limit 10   # 只取最近 10 个

依赖：仅 Python 3.10+ 标准库（json / argparse / pathlib / dataclasses）
"""
import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
DEFAULT_SNAP_DIR = BASE / "ToT" / "sop" / "snapshots"
DEFAULT_OUTPUT = BASE / "ToT" / "CHANGELOG.md"


def load_snapshots(snap_dir: Path):
    """按时间顺序加载所有 snapshot（按 timestamp 排序）。"""
    snaps = []
    for p in sorted(snap_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            data["_path"] = p.name
            snaps.append(data)
        except Exception as e:
            print(f"WARN: {p} 加载失败: {e}", file=sys.stderr)
    return snaps


def diff_two(base, head):
    """返回两个 snapshot 的差异摘要。"""
    bf = base.get("files", {})
    hf = head.get("files", {})
    base_set, head_set = set(bf), set(hf)
    added = sorted(head_set - base_set)
    modified = sorted(
        f for f in (base_set & head_set)
        if bf[f]["sha256"] != hf[f]["sha256"]
    )
    base_lines = base.get("summary", {}).get("total_lines", 0)
    head_lines = head.get("summary", {}).get("total_lines", 0)
    base_drift = base.get("summary", {}).get("drift", {})
    head_drift = head.get("summary", {}).get("drift", {})
    return {
        "added": added,
        "modified": modified,
        "added_count": len(added),
        "modified_count": len(modified),
        "lines_delta": head_lines - base_lines,
        "drift_delta": {
            "ok": head_drift.get("ok", 0) - base_drift.get("ok", 0),
            "near_match": head_drift.get("near_match", 0) - base_drift.get("near_match", 0),
            "drift": head_drift.get("drift", 0) - base_drift.get("drift", 0),
        },
    }


def render_changelog(snaps, limit=None):
    lines = []
    lines.append("# ToT/docs CHANGELOG")
    lines.append("")
    lines.append(
        "> 自动生成（`ToT/sop/gen-changelog.py`）。"
        "基于 `doc-archive-snapshot.py` 累积快照对比。"
    )
    lines.append("")
    lines.append(f"**总快照数**：{len(snaps)}")
    if snaps:
        first = snaps[0]
        last = snaps[-1]
        lines.append(
            f"**时间跨度**：{first['timestamp']} → {last['timestamp']}"
        )
    lines.append("")
    lines.append("---")
    lines.append("")

    if len(snaps) < 1:
        lines.append("（无快照数据）")
        return "\n".join(lines)

    lines.append("## 起始基线")
    lines.append("")
    lines.append(f"- 快照：`{snaps[0]['_path']}`")
    lines.append(f"- Label：`{snaps[0].get('label', '?')}`")
    lines.append(f"- 时间：`{snaps[0]['timestamp']}`")
    lines.append(f"- Git：`{snaps[0].get('git', {}).get('short_sha', '?')}`")
    s = snaps[0].get("summary", {})
    lines.append(
        f"- 文件：{s.get('file_count', 0)} · "
        f"行：{s.get('total_lines', 0)} · "
        f"字节：{s.get('total_bytes', 0)}"
    )
    d = s.get("drift", {})
    lines.append(
        f"- Drift：✅ {d.get('ok', 0)} / ⚠️ NEAR_MATCH {d.get('near_match', 0)} / ❌ {d.get('drift', 0)}"
    )
    lines.append("")

    if len(snaps) < 2:
        lines.append("（无后续 snapshot）")
        return "\n".join(lines)

    seq = snaps[-limit:] if limit else snaps
    for prev, curr in zip(seq, seq[1:]):
        diff = diff_two(prev, curr)
        lines.append("---")
        lines.append("")
        lines.append(f"## `{curr.get('label', '?')}` — {curr['timestamp']}")
        lines.append("")
        lines.append(f"- 快照：`{curr['_path']}`")
        lines.append(f"- Git：`{curr.get('git', {}).get('short_sha', '?')}`")
        lines.append(f"- 上一版：`{prev.get('label', '?')}` ({prev['timestamp']})")
        lines.append("")
        lines.append("### 变更摘要")
        lines.append("")
        lines.append(
            f"- 文件：+{diff['added_count']} added · "
            f"~{diff['modified_count']} modified"
        )
        lines.append(f"- 总行数：Δ {diff['lines_delta']:+d}")
        dd = diff["drift_delta"]
        lines.append(
            f"- Drift："
            f"OK Δ {dd['ok']:+d} · "
            f"NEAR_MATCH Δ {dd['near_match']:+d} · "
            f"DRIFT Δ {dd['drift']:+d}"
        )
        lines.append("")
        if diff["added"]:
            lines.append("**新增文件**：")
            for f in diff["added"]:
                lines.append(f"- `{f}`")
            lines.append("")
        if diff["modified"]:
            lines.append("**修改文件**（按 sha256 变化）：")
            for f in diff["modified"][:20]:
                bf = prev["files"][f]
                hf = curr["files"][f]
                d_lines = hf["lines"] - bf["lines"]
                lines.append(
                    f"- `{f}` ({bf['lines']}L → {hf['lines']}L, Δ {d_lines:+d})"
                )
            if len(diff["modified"]) > 20:
                lines.append(f"- … 还有 {len(diff['modified']) - 20} 个")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 工具链")
    lines.append("")
    lines.append("| 脚本 | 用途 | 状态 |")
    lines.append("|---|---|---|")
    lines.append("| `ToT/sop/doc-link-checker.py` | 扫描所有 .md 中 vendor/jeeflow/*.py 行号引用 | ✅ |")
    lines.append("| `ToT/sop/doc-archive-snapshot.py` | 每发版打 JSON 快照 | ✅ |")
    lines.append("| `ToT/sop/doc-vs-code-drift.py` | 跨 snapshot diff | ✅ |")
    lines.append("| `ToT/sop/gen-changelog.py` | 从 snapshots 生成本文档 | ✅ |")
    lines.append("")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(
        description="从 snapshots 生成 CHANGELOG.md"
    )
    ap.add_argument(
        "--snap-dir", type=Path, default=DEFAULT_SNAP_DIR,
        help=f"snapshot 目录（默认 {DEFAULT_SNAP_DIR.relative_to(BASE)}）"
    )
    ap.add_argument(
        "--output", type=Path, default=None,
        help=f"输出路径（默认 stdout；建议 {DEFAULT_OUTPUT.relative_to(BASE)}）"
    )
    ap.add_argument(
        "--limit", type=int, default=None,
        help="只取最近 N 个 snapshot（默认全部）"
    )
    args = ap.parse_args()

    if not args.snap_dir.exists():
        print(f"ERROR: {args.snap_dir} 不存在", file=sys.stderr)
        return 2

    snaps = load_snapshots(args.snap_dir)
    content = render_changelog(snaps, args.limit)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
        try:
            rel = args.output.relative_to(BASE)
        except ValueError:
            rel = args.output
        print(
            f"✅ CHANGELOG written: {rel} "
            f"({len(content)} chars, {len(snaps)} snapshots)",
            file=sys.stderr,
        )
    else:
        print(content)
    return 0


if __name__ == "__main__":
    sys.exit(main())