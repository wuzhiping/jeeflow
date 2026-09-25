#!/usr/bin/env python3
"""health-check.py — ToT/docs 综合健康度评分

5 维度评分（0-100）+ 加权综合分：
  1. Drift       (30%) — doc-link-checker 结果
  2. Snapshot    (15%) — snapshot 数量 + 增长率
  3. API Coverage(25%) — vendor/jeeflow 公开 API 在 ToT/docs 覆盖度
  4. Freshness   (20%) — git log: doc mtime vs code mtime（stale >30/90 天）
  5. Consistency (10%) — 跨 doc 一致性（核心概念引用频次）

输出：
  - 文本模式（默认）：进度条 + 评级 + 改进建议
  - JSON 模式（--json）：结构化数据，可接入 CI/趋势跟踪

依赖：仅 Python 3.10+ 标准库（re / json / pathlib / subprocess / dataclasses）

用法：
  python3 health-check.py                    # 跑全维度，文本输出
  python3 health-check.py --json             # JSON 输出
  python3 health-check.py --dimension drift  # 只跑单个维度
  python3 health-check.py --save latest.json # 保存当前评分
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOT_DOCS = REPO_ROOT / "ToT" / "docs"
VENDOR = REPO_ROOT / "vendor" / "jeeflow"
SNAPSHOTS = REPO_ROOT / "ToT" / "sop" / "snapshots"


@dataclass
class Dimension:
    name: str
    score: int
    weight: int
    grade: str  # ✅ 良好 / ⚠️ 警告 / ❌ 严重
    details: dict
    recommendation: str = ""


@dataclass
class HealthReport:
    timestamp: str
    overall_score: int
    overall_grade: str
    dimensions: list = field(default_factory=list)


# === 维度 1：Drift ===
def check_drift() -> Dimension:
    """调 doc-link-checker.py，返回 OK/NEAR/DRIFT 计数"""
    checker = REPO_ROOT / "ToT" / "sop" / "doc-link-checker.py"
    try:
        result = subprocess.run(
            ["python3", str(checker), "--json"],
            capture_output=True, text=True, timeout=30, cwd=str(REPO_ROOT)
        )
        if result.returncode == 0 and result.stdout.strip():
            raw = json.loads(result.stdout)
            # 支持两种格式：{summary: {...}} 或扁平 {total, ok, drift, near_match}
            data = raw.get("summary", raw)
        else:
            data = {"ok": 0, "near_match": 0, "drift": 0, "total": 0}
    except Exception:
        data = {"ok": 0, "near_match": 0, "drift": 0, "total": 0}

    total = data.get("total", 0)
    drift = data.get("drift", 0)
    near = data.get("near_match", 0)

    if total == 0:
        score = 100  # 没引用 = 没 drift = 满分（边缘情况）
    else:
        score = max(0, int(100 - (drift / total * 100) - (near / total * 50)))

    grade = "✅" if drift == 0 else ("⚠️" if drift < total * 0.05 else "❌")
    rec = "" if drift == 0 else f"修复 {drift} 条 drift 引用（{near} 条 near_match）"

    return Dimension(
        name="Drift",
        score=score, weight=30, grade=grade,
        details={"total": total, "ok": data.get("ok", 0), "near_match": near, "drift": drift},
        recommendation=rec,
    )


# === 维度 2：Snapshot 累积 ===
def check_snapshots() -> Dimension:
    """统计 snapshot 数量 + 最近增长率"""
    snaps = sorted(SNAPSHOTS.glob("*.json")) if SNAPSHOTS.exists() else []
    count = len(snaps)

    # 评分：≥10 = 100，每少 1 个 -10，下限 50
    score = min(100, max(50, 50 + count * 5))

    # 增长率：最近 3 天 vs 之前
    # snapshot 文件名格式：2026-09-24T235123Z-v1.9.0-final.json（无冒号在时间部分）
    def parse_snap_time(stem: str) -> datetime | None:
        # 提取前 18 字符：YYYY-MM-DDTHHMMSS
        ts = stem[:18] if len(stem) >= 18 else ""
        # 转 ISO：插入冒号 T23:51:23
        if len(ts) == 18 and ts[8] == "T":
            iso = ts[:9] + ts[9:11] + ":" + ts[11:13] + ":" + ts[13:15] + "+00:00"
        else:
            return None
        try:
            return datetime.fromisoformat(iso)
        except ValueError:
            return None

    now = datetime.now(timezone.utc)
    recent = sum(1 for s in snaps
                 if (parse_snap_time(s.stem) and
                     (now - parse_snap_time(s.stem)).days <= 3))
    growth = recent if count > 0 else 0

    grade = "✅" if count >= 5 else ("⚠️" if count >= 2 else "❌")
    rec = "" if count >= 5 else f"已积累 {count} 个 snapshot，≥5 个才算健康"

    return Dimension(
        name="Snapshot",
        score=score, weight=15, grade=grade,
        details={"total": count, "recent_3d": recent},
        recommendation=rec,
    )


# === 维度 3：API 覆盖率 ===
def check_api_coverage() -> Dimension:
    """vendor/jeeflow 公开 API vs ToT/docs 引用"""
    if not VENDOR.exists():
        return Dimension(name="API Coverage", score=0, weight=25, grade="❌",
                        details={"error": "vendor/jeeflow not found"})

    # 1. 提取 vendor/jeeflow 公开 API（class/def/async def，不含 _ 开头）
    public_apis = set()
    for py_file in VENDOR.glob("*.py"):
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"^(?:class|def|async def)\s+([A-Za-z_]\w*)", content, re.M):
            name = m.group(1)
            if not name.startswith("_"):
                public_apis.add(name)

    # 2. 提取 ToT/docs/*.md 实际引用的标识符
    referenced = set()
    if TOT_DOCS.exists():
        for md_file in TOT_DOCS.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            for api in public_apis:
                if re.search(rf"\b{re.escape(api)}\b", content):
                    referenced.add(api)

    total = len(public_apis)
    covered = len(referenced)
    pct = int(covered / total * 100) if total > 0 else 0

    score = pct
    grade = "✅" if pct >= 50 else ("⚠️" if pct >= 25 else "❌")
    missing = sorted(public_apis - referenced)[:10]  # 列前 10 个未覆盖
    rec = ""
    if missing:
        rec = f"补齐 {total - covered} 个公开 API（含 {', '.join(missing[:5])} ...）"

    return Dimension(
        name="API Coverage",
        score=score, weight=25, grade=grade,
        details={"total": total, "covered": covered, "missing_sample": missing},
        recommendation=rec,
    )


# === 维度 4：Doc 新鲜度 ===
def check_freshness() -> Dimension:
    """git log: doc mtime vs vendor/jeeflow mtime"""
    def git_log_date(path: Path) -> datetime | None:
        try:
            r = subprocess.run(
                ["git", "log", "-1", "--format=%cI", "--", str(path.relative_to(REPO_ROOT))],
                capture_output=True, text=True, timeout=10, cwd=str(REPO_ROOT)
            )
            if r.returncode == 0 and r.stdout.strip():
                return datetime.fromisoformat(r.stdout.strip())
        except Exception:
            pass
        return None

    # 取最近 vendor/jeeflow 变更时间
    vendor_modified = max(
        (git_log_date(p) for p in VENDOR.glob("*.py") if p.exists()),
        default=None,
    )
    if vendor_modified is None:
        return Dimension(name="Freshness", score=50, weight=20, grade="⚠️",
                        details={"error": "no vendor git history"})

    now = datetime.now(timezone.utc)
    total_docs = 0
    fresh_count = 0
    stale_30 = 0
    stale_90 = 0
    max_staleness = 0

    for md_file in TOT_DOCS.rglob("*.md"):
        if md_file.name.startswith("_"):
            continue
        md_date = git_log_date(md_file)
        if md_date is None:
            continue
        total_docs += 1
        staleness = (vendor_modified - md_date).days
        max_staleness = max(max_staleness, staleness)
        if staleness > 90:
            stale_90 += 1
        elif staleness > 30:
            stale_30 += 1
        else:
            fresh_count += 1

    if total_docs == 0:
        return Dimension(name="Freshness", score=50, weight=20, grade="⚠️",
                        details={"error": "no docs found"})

    # 评分：90 天以上 = -50，30 天以上 = -20，新鲜 = +1
    penalty = stale_90 * 50 + stale_30 * 20
    score = max(0, 100 - penalty // max(1, total_docs // 10))

    grade = "✅" if stale_90 == 0 else ("⚠️" if stale_90 <= 2 else "❌")
    rec = ""
    if stale_90 > 0:
        rec = f"复查 {stale_90} 个 doc（stale >90 天）"
    elif stale_30 > 0:
        rec = f"关注 {stale_30} 个 doc（stale 30-90 天）"

    return Dimension(
        name="Freshness",
        score=score, weight=20, grade=grade,
        details={"total_docs": total_docs, "fresh": fresh_count,
                "stale_30_90": stale_30, "stale_90_plus": stale_90,
                "max_staleness_days": max_staleness},
        recommendation=rec,
    )


# === 维度 5：跨 doc 一致性 ===
def check_consistency() -> Dimension:
    """核心概念在多 doc 中的引用一致性"""
    if not TOT_DOCS.exists():
        return Dimension(name="Consistency", score=0, weight=10, grade="❌",
                        details={"error": "ToT/docs not found"})

    # 核心概念：高频技术名词
    concepts = [
        "Engine", "JeeflowFacade", "FlowInterceptor", "HandlerRegistry",
        "EventType", "ProcessEvent", "JdbcRepository", "MemoryRepository",
        "IAssignmentHandler", "ExpressionEvaluator",
    ]

    doc_concept_count: dict[str, int] = {}
    for concept in concepts:
        count = 0
        for md_file in TOT_DOCS.rglob("*.md"):
            if re.search(rf"\b{re.escape(concept)}\b", md_file.read_text(encoding="utf-8", errors="ignore")):
                count += 1
        doc_concept_count[concept] = count

    # 评分：引用 ≥3 个 doc 的概念比例
    well_distributed = sum(1 for c in concepts if doc_concept_count[c] >= 3)
    score = int(well_distributed / len(concepts) * 100) if concepts else 0

    grade = "✅" if score >= 60 else ("⚠️" if score >= 30 else "❌")
    rec = ""
    if score < 60:
        orphans = [c for c, n in doc_concept_count.items() if n < 3]
        rec = f"补齐 {len(orphans)} 个孤立概念（{', '.join(orphans[:3])} ...）"

    return Dimension(
        name="Consistency",
        score=score, weight=10, grade=grade,
        details={"concepts": doc_concept_count, "well_distributed": well_distributed},
        recommendation=rec,
    )


# === 综合 ===
def compute_report() -> HealthReport:
    dims = [
        check_drift(),
        check_snapshots(),
        check_api_coverage(),
        check_freshness(),
        check_consistency(),
    ]
    overall = sum(d.score * d.weight for d in dims) // sum(d.weight for d in dims)
    overall_grade = "🟢 健康" if overall >= 85 else ("🟡 亚健康" if overall >= 60 else "🔴 异常")
    return HealthReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        overall_score=overall,
        overall_grade=overall_grade,
        dimensions=[asdict(d) for d in dims],
    )


def render_text(report: HealthReport) -> str:
    lines = []
    lines.append("═" * 60)
    lines.append(f"  ToT/docs Health Report")
    lines.append(f"  {report.timestamp}")
    lines.append("═" * 60)
    lines.append("")
    bar = lambda s: "█" * (s // 5) + "░" * (20 - s // 5)
    for d in report.dimensions:
        lines.append(f"  {d['name']:<18} {bar(d['score'])} {d['score']:>3}/100  {d['grade']}  ({d['weight']}%)")
        for k, v in d["details"].items():
            if isinstance(v, (list, dict)) and not v:
                continue
            lines.append(f"    {k}: {v}")
        if d["recommendation"]:
            lines.append(f"    ➜ {d['recommendation']}")
        lines.append("")
    lines.append("─" * 60)
    lines.append(f"  Overall Score: {bar(report.overall_score)} {report.overall_score}/100  {report.overall_grade}")
    lines.append("═" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="ToT/docs 综合健康度评分")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--dimension", choices=["drift", "snapshots", "api", "freshness", "consistency"])
    parser.add_argument("--save", metavar="FILE", help="保存到 JSON 文件")
    args = parser.parse_args()

    if args.dimension:
        # 单维度
        fn = {
            "drift": check_drift, "snapshots": check_snapshots,
            "api": check_api_coverage, "freshness": check_freshness,
            "consistency": check_consistency,
        }[args.dimension]
        d = asdict(fn())
        if args.json:
            print(json.dumps(d, indent=2, ensure_ascii=False))
        else:
            print(f"{d['name']}: {d['score']}/100 {d['grade']}")
            print(json.dumps(d['details'], indent=2, ensure_ascii=False))
    else:
        report = compute_report()
        if args.json:
            print(json.dumps(asdict(report), indent=2, ensure_ascii=False))
        else:
            print(render_text(report))
        if args.save:
            Path(args.save).write_text(
                json.dumps(asdict(report), indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            print(f"\n✅ Saved to {args.save}")


if __name__ == "__main__":
    main()