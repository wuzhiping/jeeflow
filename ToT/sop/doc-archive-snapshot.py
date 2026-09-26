#!/usr/bin/env python3
"""doc-archive-snapshot.py — ToT/docs 状态快照归档

每次发版前跑一次，生成 ToT/docs 状态快照：
- 每个 .md 的行数、字符数、sha256、mtime
- doc-link-checker.py drift 报告（NEAR_MATCH / NO_DEF / FILE_NOT_FOUND / LINE_OUT_OF_RANGE）
- 当前 git commit + branch + 是否有未提交修改
- 输出：JSON 文件 + 文本汇总

输出路径：<out-dir>/YYYY-MM-DDTHHMMSSZ-<label>-<short-sha>.json

用法：
    python3 ToT/sop/doc-archive-snapshot.py
    python3 ToT/sop/doc-archive-snapshot.py --label v1.9.0
    python3 ToT/sop/doc-archive-snapshot.py --out-dir ./snapshots
    python3 ToT/sop/doc-archive-snapshot.py --no-checker  # 跳过 drift 检查（更快）

依赖：仅标准库（hashlib / subprocess / json / datetime / pathlib / dataclasses）
可选：调用 ToT/sop/doc-link-checker.py 作为子进程
"""
import argparse
import dataclasses
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = BASE / "ToT" / "docs"
DEFAULT_OUT_DIR = BASE / "ToT" / "sop" / "snapshots"


@dataclasses.dataclass
class FileSnapshot:
    path: str
    size: int
    lines: int
    sha256: str
    mtime: float


def file_snapshot(path: Path) -> FileSnapshot:
    """计算单个文件的快照信息。"""
    content = path.read_bytes()
    return FileSnapshot(
        path=str(path.relative_to(BASE)),
        size=len(content),
        lines=content.count(b"\n") + (0 if content.endswith(b"\n") else 1),
        sha256=hashlib.sha256(content).hexdigest(),
        mtime=path.stat().st_mtime,
    )


def git_info() -> dict:
    """读取当前 git commit / branch / dirty 状态。"""
    info = {"commit": None, "short_sha": None, "branch": None, "dirty": False}
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=BASE, text=True, stderr=subprocess.DEVNULL,
        ).strip()
        info["commit"] = commit
        info["short_sha"] = commit[:8]
        try:
            info["branch"] = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=BASE, text=True, stderr=subprocess.DEVNULL,
            ).strip()
        except subprocess.CalledProcessError:
            info["branch"] = "DETACHED"
        status = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=BASE, text=True, stderr=subprocess.DEVNULL,
        ).strip()
        info["dirty"] = bool(status)
    except subprocess.CalledProcessError:
        pass
    return info


def run_link_checker(docs_dir: Path) -> dict:
    """调用 doc-link-checker.py --json 收集 drift 数。"""
    script = BASE / "ToT" / "sop" / "doc-link-checker.py"
    if not script.exists():
        return {"available": False}
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--json"],
            cwd=BASE, capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0 and not result.stdout.strip().startswith("{"):
            return {"available": False, "error": result.stderr[:200]}
        return json.loads(result.stdout)
    except Exception as e:
        return {"available": False, "error": str(e)}


def main():
    ap = argparse.ArgumentParser(
        description="ToT/docs 状态快照归档"
    )
    ap.add_argument(
        "--out-dir", type=Path, default=DEFAULT_OUT_DIR,
        help=f"快照输出目录（默认 {DEFAULT_OUT_DIR.relative_to(BASE)}）"
    )
    ap.add_argument(
        "--label", type=str, default=None,
        help="快照标签（如 v1.9.0 / 2026-Q4-release）"
    )
    ap.add_argument(
        "--no-checker", action="store_true",
        help="跳过 doc-link-checker.py 调用（更快）"
    )
    args = ap.parse_args()

    if not DOCS_DIR.exists():
        print(f"ERROR: {DOCS_DIR} 不存在", file=sys.stderr)
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    label = args.label or "snapshot"
    git = git_info()
    short_sha = git["short_sha"] or "no-git"

    files = {}
    total_lines = 0
    total_bytes = 0
    for md in sorted(DOCS_DIR.rglob("*.md")):
        snap = file_snapshot(md)
        files[snap.path] = dataclasses.asdict(snap)
        total_lines += snap.lines
        total_bytes += snap.size

    drift_report = (
        run_link_checker(DOCS_DIR) if not args.no_checker else {"available": False}
    )

    snapshot = {
        "schema": "doc-archive-snapshot/v1",
        "timestamp": timestamp,
        "label": label,
        "git": git,
        "docs_root": str(DOCS_DIR.relative_to(BASE)),
        "summary": {
            "file_count": len(files),
            "total_lines": total_lines,
            "total_bytes": total_bytes,
            "drift": drift_report.get("summary", {}),
        },
        "files": files,
        "drift_report": drift_report.get("by_status", {}),
    }

    slug = (
        f"{timestamp}-{label}-{short_sha}"
        .replace("/", "_").replace(" ", "_")
    )
    out_path = args.out_dir / f"{slug}.json"
    out_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"✅ Snapshot saved: {out_path.relative_to(BASE)}")
    print(f"   Label: {label}")
    print(f"   Git: {git['short_sha'] or 'no-git'} ({git['branch']}){' [dirty]' if git['dirty'] else ''}")
    print(f"   Files: {len(files)} · Total lines: {total_lines} · Total bytes: {total_bytes}")
    s = drift_report.get("summary", {})
    if s:
        print(
            f"   Drift: ✅ OK {s.get('ok', 0)} · "
            f"⚠️ NEAR_MATCH {s.get('near_match', 0)} · "
            f"❌ DRIFT {s.get('drift', 0)}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())