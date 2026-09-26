#!/usr/bin/env python3
"""doc-vs-code-drift.py — 跨 snapshot 对比

对比两个 doc-archive-snapshot.json（base / head），输出 4 类变更：
- 文件级：added / removed / modified / unchanged
- 数量级：总行数 / 字节数 delta
- drift 级：OK / NEAR_MATCH / NO_DEF / FILE_NOT_FOUND / LINE_OUT_OF_RANGE 增减
- 关键告警：head 中新增的 drift 项（base 中没有的） + 已修复项（base 中已修）

用法：
    python3 ToT/sop/doc-vs-code-drift.py base.json head.json
    python3 ToT/sop/doc-vs-code-drift.py --latest          # 最近 2 个 snapshot
    python3 ToT/sop/doc-vs-code-drift.py --label-prefix v1.9.0

依赖：仅 Python 3.10+ 标准库（json / argparse / pathlib / dataclasses）
"""
import argparse
import dataclasses
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
DEFAULT_SNAP_DIR = BASE / "ToT" / "sop" / "snapshots"


@dataclasses.dataclass
class DriftItem:
    md_file: str
    md_line: int
    code_file: str
    code_line: int
    context: str

    def key(self):
        return (self.md_file, self.md_line, self.code_file, self.code_line)

    def logical_key(self):
        return (self.md_file, self.code_file, self.code_line)

    @classmethod
    def from_dict(cls, d):
        return cls(
            md_file=d.get("md_file", ""),
            md_line=d.get("md_line", 0),
            code_file=d.get("code_file", ""),
            code_line=d.get("code_line", 0),
            context=d.get("context", "")[:60],
        )


def load_snapshot(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def diff_drift_items(base_items, head_items):
    """对比两个 drift_items 列表：
    返回 (added, fixed, moved)
    - added: head 中新增（logical_key 不在 base）
    - fixed: head 中已修复（logical_key 不在 head）
    - moved: 同 logical_key 但 md_line 不同（位置漂移）
    """
    base_by_logical = {}
    for d in base_items:
        base_by_logical.setdefault(d.logical_key(), []).append(d)
    head_by_logical = {}
    for d in head_items:
        head_by_logical.setdefault(d.logical_key(), []).append(d)
    base_logicals = set(base_by_logical)
    head_logicals = set(head_by_logical)
    added = [d for d in head_items if d.logical_key() not in base_logicals]
    fixed = [d for d in base_items if d.logical_key() not in head_logicals]
    moved = []
    for k in base_logicals & head_logicals:
        base_lines = {d.md_line for d in base_by_logical[k]}
        head_lines = {d.md_line for d in head_by_logical[k]}
        if base_lines != head_lines:
            for d in head_by_logical[k]:
                moved.append(d)
    return added, fixed, moved


def diff_snapshots(base: dict, head: dict) -> dict:
    base_files = base.get("files", {})
    head_files = head.get("files", {})
    base_set = set(base_files)
    head_set = set(head_files)

    added_files = sorted(head_set - base_set)
    removed_files = sorted(base_set - head_set)
    common = base_set & head_set
    modified = sorted(
        f for f in common
        if base_files[f]["sha256"] != head_files[f]["sha256"]
    )
    unchanged = sorted(
        f for f in common
        if base_files[f]["sha256"] == head_files[f]["sha256"]
    )

    base_lines = base.get("summary", {}).get("total_lines", 0)
    head_lines = head.get("summary", {}).get("total_bytes", 0)
    base_bytes = base.get("summary", {}).get("total_bytes", 0)
    head_bytes = head.get("summary", {}).get("total_bytes", 0)
    base_drift = base.get("summary", {}).get("drift", {})
    head_drift = head.get("summary", {}).get("drift", {})

    drift_status_diff = {}
    for status in ("ok", "near_match", "drift", "total"):
        b = base_drift.get(status, 0)
        h = head_drift.get(status, 0)
        drift_status_diff[status] = {"base": b, "head": h, "delta": h - b}

    added_drift = {}
    fixed_drift = {}
    moved_drift = {}
    base_report = base.get("drift_report", {})
    head_report = head.get("drift_report", {})
    all_statuses = set(base_report) | set(head_report)
    for status in all_statuses:
        base_items = [DriftItem.from_dict(d) for d in base_report.get(status, [])]
        head_items = [DriftItem.from_dict(d) for d in head_report.get(status, [])]
        added, fixed, moved = diff_drift_items(base_items, head_items)
        if added:
            added_drift[status] = [dataclasses.asdict(a) for a in added]
        if fixed:
            fixed_drift[status] = [dataclasses.asdict(f) for f in fixed]
        if moved:
            moved_drift[status] = [dataclasses.asdict(m) for m in moved]

    return {
        "files": {
            "added": added_files,
            "removed": removed_files,
            "modified": modified,
            "unchanged": unchanged,
            "added_count": len(added_files),
            "removed_count": len(removed_files),
            "modified_count": len(modified),
            "unchanged_count": len(unchanged),
        },
        "summary": {
            "lines_delta": head.get("summary", {}).get("total_lines", 0) - base.get("summary", {}).get("total_lines", 0),
            "bytes_delta": head.get("summary", {}).get("total_bytes", 0) - base.get("summary", {}).get("total_bytes", 0),
            "drift_status_delta": drift_status_diff,
        },
        "added_drift": added_drift,
        "fixed_drift": fixed_drift,
        "moved_drift": moved_drift,
        "meta": {
            "base": {
                "label": base.get("label"),
                "timestamp": base.get("timestamp"),
                "git": base.get("git", {}).get("short_sha"),
            },
            "head": {
                "label": head.get("label"),
                "timestamp": head.get("timestamp"),
                "git": head.get("git", {}).get("short_sha"),
            },
        },
    }


def find_latest_snapshots(snap_dir: Path):
    snaps = sorted(snap_dir.glob("*.json"))
    if len(snaps) < 2:
        return None, None
    return snaps[-2], snaps[-1]


def format_text_report(diff):
    lines = []
    meta = diff["meta"]
    f = diff["files"]
    s = diff["summary"]
    lines.append(
        f"Snapshot 对比：{meta['base']['label']} ({meta['base']['git']})"
        f" → {meta['head']['label']} ({meta['head']['git']})"
    )
    lines.append(
        f"时间：{meta['base']['timestamp']} → {meta['head']['timestamp']}"
    )
    lines.append("")
    lines.append("文件变更：")
    lines.append(
        f"  + {f['added_count']} added · "
        f"- {f['removed_count']} removed · "
        f"~ {f['modified_count']} modified · "
        f"= {f['unchanged_count']} unchanged"
    )
    if f["added"]:
        lines.append(f"  + Added: {', '.join(f['added'][:5])}")
    if f["removed"]:
        lines.append(f"  - Removed: {', '.join(f['removed'][:5])}")
    if f["modified"]:
        lines.append(f"  ~ Modified: {', '.join(f['modified'][:5])}")
    lines.append("")
    lines.append(
        f"数量：lines Δ {s['lines_delta']:+d} · "
        f"bytes Δ {s['bytes_delta']:+d}"
    )
    lines.append("")
    lines.append("Drift 状态变化：")
    for status, d in s["drift_status_delta"].items():
        lines.append(
            f"  {status}: {d['base']} → {d['head']} (Δ {d['delta']:+d})"
        )
    lines.append("")
    if diff["added_drift"]:
        lines.append("⚠️ 新增 drift（head 中出现，base 中没有）：")
        for status, items in diff["added_drift"].items():
            lines.append(f"  [{status}] {len(items)} 条")
            for it in items[:5]:
                lines.append(
                    f"    {it['md_file']}:{it['md_line']} → "
                    f"vendor/jeeflow/{it['code_file']}:{it['code_line']}"
                )
    if diff["fixed_drift"]:
        lines.append("✅ 已修复 drift（base 中有，head 中没有）：")
        for status, items in diff["fixed_drift"].items():
            lines.append(f"  [{status}] {len(items)} 条")
    if diff["moved_drift"]:
        total_moved = sum(len(v) for v in diff["moved_drift"].values())
        lines.append(
            f"↔️ 位置漂移（md_line 变化但 logical_key 不变）：{total_moved} 条"
        )
        for status, items in diff["moved_drift"].items():
            lines.append(f"  [{status}] {len(items)} 条（informational）")
    if not diff["added_drift"] and not diff["fixed_drift"] and not diff["moved_drift"]:
        lines.append("✅ 无新增 / 已修复 / 漂移 drift。")
    return lines


def main():
    ap = argparse.ArgumentParser(description="跨 snapshot 对比")
    ap.add_argument("base", nargs="?", type=Path, help="base snapshot JSON")
    ap.add_argument("head", nargs="?", type=Path, help="head snapshot JSON")
    ap.add_argument(
        "--snap-dir", type=Path, default=DEFAULT_SNAP_DIR,
        help=f"snapshot 目录（默认 {DEFAULT_SNAP_DIR.relative_to(BASE)}）"
    )
    ap.add_argument(
        "--latest", action="store_true",
        help="自动取最近 2 个 snapshot（无需参数）"
    )
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    args = ap.parse_args()

    if args.latest:
        b, h = find_latest_snapshots(args.snap_dir)
        if not b:
            print(
                f"ERROR: {args.snap_dir} 至少需要 2 个 snapshot 才能 --latest",
                file=sys.stderr,
            )
            return 2
    else:
        if not (args.base and args.head):
            ap.error("必须提供 base / head，或用 --latest")
        b, h = args.base, args.head
        if not b.exists():
            print(f"ERROR: {b} 不存在", file=sys.stderr)
            return 2
        if not h.exists():
            print(f"ERROR: {h} 不存在", file=sys.stderr)
            return 2

    base = load_snapshot(b)
    head = load_snapshot(h)
    diff = diff_snapshots(base, head)

    if args.json:
        print(json.dumps(diff, ensure_ascii=False, indent=2))
    else:
        print("\n".join(format_text_report(diff)))
    return 0


if __name__ == "__main__":
    sys.exit(main())