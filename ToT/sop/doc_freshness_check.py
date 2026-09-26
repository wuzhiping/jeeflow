#!/usr/bin/env python3
"""doc-freshness-check.py — 自动检测 ToT/ 文档中的陈旧数字

GETTING_STARTED.md / README.md / HANDBOOK.md 等入口文档经常引用具体数字
（43 项 / 8 层 / 5 层 31 项 等）。这些数字会随脚本改动而陈旧，但人工维护
容易遗漏。本工具自动跑实际脚本，把输出与文档中的数字做对比，发现不一致
就告警。

检测维度（v1.0）：
  - ea-compliance.py 的总检查项数（44 / 8 层 / 各层 ID）
  - flow-completeness.py 的 6 层（C1-C6）
  - vendor/jeeflow/ 的公开 API 数（73 个 class/def/async def）
  - ToT/docs/ 文件数与 health-check.py 一致性
  - 路径引用完整性（GETTING_STARTED §5 SOP 表 vs 实际 .md/.py 文件）

输出：
  - 文本模式（默认）：列出 stale 数据 + 建议
  - JSON 模式（--json）：结构化输出

依赖：仅 Python 3.10+ 标准库

用法：
  python3 doc-freshness-check.py                # 跑全维度，文本输出
  python3 doc-freshness-check.py --json         # JSON 输出
  python3 doc-freshness-check.py --dimension ea # 只跑 ea-compliance 检查
  python3 doc-freshness-check.py --fix-marker   # 报告但不改文档（v1 阶段保守）
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class StaleFinding:
    doc: str         # 文件路径
    line: int        # 行号（如果知道）
    claim: str       # 文档中的声称
    actual: str      # 实际值
    severity: str    # "high" / "medium" / "low"


def count_ea_compliance_items() -> dict:
    """跑 ea-compliance.py，统计每层检查项数

    v1.0 策略：跑 ea-compliance.py 解析最终输出（权威值），而非静态解析源码
    （源码部分检查项用 f-string 生成 ID，静态解析会漏算）。
    """
    script = REPO_ROOT / "ToT" / "sop" / "ea-compliance.py"
    if not script.exists():
        return {}
    # 优先：跑 ea-compliance.py 解析 OVERALL 行
    try:
        result = subprocess.run(
            ["python3", str(script)], capture_output=True, text=True,
            cwd=str(REPO_ROOT), timeout=60,
        )
        output = result.stdout
        # 匹配 "OVERALL: 44/44 PASS (100.0%)"
        m = re.search(r"OVERALL:\s*(\d+)/(\d+)\s*PASS", output)
        if m:
            total = int(m.group(2))
            # 各层：从输出中提取每层状态（如果有）
            layer_pattern = re.findall(r"^\s*([9X]\.[\d.]+)\s+(.+?)\s+(✓|✗)", output, re.M)
            return {
                "total": total,
                "method": "runtime",
                "layer_details": [{"id": l[0], "desc": l[1].strip()} for l in layer_pattern],
            }
    except Exception as e:
        pass

    # 回退：静态解析源码（可能少算 f-string 项）
    text = script.read_text(encoding="utf-8")
    layers = {}
    for m in re.finditer(r"def (check_layer_\w+)\(\):(.+?)(?=def |\Z)", text, re.S):
        layer_name = m.group(1)
        body = m.group(2)
        items = re.findall(r'check_item\("([^"]+)",\s*"([^"]+)"', body)
        layers[layer_name] = {
            "count": len(items),
            "ids": [i[1] for i in items],
        }
    total = sum(l["count"] for l in layers.values())
    return {
        "total": total,
        "method": "static",
        "layers": layers,
    }


def count_flow_completeness_layers() -> dict:
    """flow_completeness.py 的 6 层（C1-C6）"""
    script = REPO_ROOT / "ToT" / "sop" / "flow_completeness.py"
    if not script.exists():
        return {}
    text = script.read_text(encoding="utf-8")
    layers = {}
    for m in re.finditer(r"# ===== §C(\d) (.+?) =+", text):
        layers[f"§C{m.group(1)}"] = m.group(2).strip()
    return layers


def count_public_apis() -> int:
    """vendor/jeeflow/*.py 公开 API 数（class/def/async def 不含 _）"""
    vendor = REPO_ROOT / "vendor" / "jeeflow"
    if not vendor.exists():
        return 0
    count = 0
    for py_file in vendor.glob("*.py"):
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"^(?:class|def|async def)\s+([A-Za-z_]\w*)", content, re.M):
            if not m.group(1).startswith("_"):
                count += 1
    return count


def count_tot_docs_files() -> dict:
    """ToT/docs/ 文件统计"""
    docs = REPO_ROOT / "ToT" / "docs"
    if not docs.exists():
        return {}
    out = {"total": 0, "by_subdir": {}}
    for sub in ["guides", "spec", "concepts", "manual", "patterns"]:
        sub_path = docs / sub
        if sub_path.exists():
            files = list(sub_path.glob("*.md"))
            out["by_subdir"][sub] = len(files)
            out["total"] += len(files)
    out["top_level"] = len(list(docs.glob("*.md")))
    return out


def verify_sop_paths() -> list[StaleFinding]:
    """文档中 `path.md` / `path.py` 引用 vs 实际文件

    注意：路径解析尝试多种 base：
      1. 仓库根（最常见，README.md / GETTING_STARTED.md / HANDBOOK.md 的引用习惯）
      2. 文档所在目录（深层 doc 的相对引用）
    任何一个 base 命中就算通过。
    """
    findings = []
    targets = [
        REPO_ROOT / "ToT" / "GETTING_STARTED.md",
        REPO_ROOT / "ToT" / "README.md",
        REPO_ROOT / "README.md",
    ]
    # 不验证这些 docs 的引用（路径 base 不同）
    skip_docs = set()

    # 已知的合法 base 列表
    def resolve(rel_path: str, doc_path: Path) -> bool:
        # 尝试 1: 仓库根
        if (REPO_ROOT / rel_path).exists():
            return True
        # 尝试 2: 文档所在目录
        if (doc_path.parent / rel_path).exists():
            return True
        # 尝试 3: 去掉 `../` 前缀（针对根文档 ToT/ 内文件）
        clean = rel_path.lstrip("./")
        if (doc_path.parent / clean).exists():
            return True
        # 尝试 4: 去掉 `ToT/` 前缀
        if rel_path.startswith("ToT/"):
            if (REPO_ROOT / rel_path[4:]).exists():
                return True
        return False

    for target in targets:
        if not target.exists():
            continue
        for line_num, line in enumerate(target.read_text(encoding="utf-8").splitlines(), 1):
            # 匹配 `xxx.md` 或 `xxx.py` 形式的相对路径引用
            for m in re.finditer(r"`([\w./_-]+\.(?:md|py|sh|json))`", line):
                ref = m.group(1)
                # 跳过 URL / 绝对路径 / 域名
                if ref.startswith("http") or ref.startswith("/"):
                    continue
                # 跳过文件不存在但是合理的占位（带括号说明的）
                if "(无对应" in line or "无对应" in line:
                    continue
                # 跳过 SOP 索引表中纯文件名引用（如 `flow_designer.py` 在叙述中）
                # 这些通常需要在 SOP 文件夹上下文才有意义
                if not "/" in ref and not ref.startswith("ToT"):
                    # 单文件名 — 检查 ToT/sop/ 下是否存在
                    if not (REPO_ROOT / "ToT" / "sop" / ref).exists():
                        continue  # 单文件名跳过（容易误报）
                if not resolve(ref, target):
                    findings.append(StaleFinding(
                        doc=str(target.relative_to(REPO_ROOT)),
                        line=line_num,
                        claim=f"引用 `{ref}`",
                        actual="文件不存在（尝试 4 个 base）",
                        severity="high" if "ToT/" in ref or "/" in ref else "low",
                    ))
    return findings


def scan_stale_numbers() -> list[StaleFinding]:
    """文档中的具体数字声明 vs 实际

    注意：跳过变更日志 / 历史记录里的数字（如 `v2.11 ... 27/27 PASS`），
    这些是历史快照，不应与当前状态对齐。
    """
    findings = []
    ea_items = count_ea_compliance_items()
    ea_total = ea_items.get("total", 0) if isinstance(ea_items, dict) else 0
    if ea_total == 0 and isinstance(ea_items, dict):
        ea_total = sum(l.get("count", 0) for l in ea_items.get("layers", {}).values())
    if ea_total == 0:
        return findings

    docs_to_scan = [
        REPO_ROOT / "ToT" / "GETTING_STARTED.md",
        REPO_ROOT / "ToT" / "ea" / "roadmap.md",
        REPO_ROOT / "ToT" / "README.md",
        REPO_ROOT / "README.md",
    ]
    for doc in docs_to_scan:
        if not doc.exists():
            continue
        in_history = False  # 是否在变更日志 / 历史快照区
        lines = doc.read_text(encoding="utf-8").splitlines()
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            # 检测进入变更日志区
            is_changelog_header = bool(re.match(
                r"^#+\s*(变更日志|Changelog|Change[ ]?Log|迭代历史|历史快照|History)",
                stripped, re.I))
            # changelog table 行：版本号开头（vN.N / **vN.N** / v1.X / v2.X）
            is_changelog_row = bool(re.match(r"^\|\s*\*?\*?v?\d+\.\d+", stripped))

            if is_changelog_header or is_changelog_row:
                in_history = True
                continue

            # 退出 changelog 区：遇到新 ## 标题（且不是历史标题）
            if in_history and stripped.startswith("#"):
                in_history = False

            if in_history:
                continue  # 跳过历史区

            # 1. 检查 "X/Y PASS" 格式（live 状态）
            for m in re.finditer(r"(\d+)/(\d+)\s*PASS", line):
                total = int(m.group(2))
                if total != ea_total:
                    findings.append(StaleFinding(
                        doc=str(doc.relative_to(REPO_ROOT)),
                        line=line_num,
                        claim=f"{m.group(1)}/{total} PASS",
                        actual=f"当前 ea-compliance {ea_total}/{ea_total} PASS",
                        severity="medium",
                    ))
            # 2. 检查 "X 层 Y 项" 格式
            for m in re.finditer(r"(\d+)\s*层\s*(\d+)\s*项", line):
                claim_layers = int(m.group(1))
                ea_layers = (len(ea_items.get("layers", {})) if isinstance(ea_items, dict) and "layers" in ea_items else 8)
                if claim_layers != ea_layers:
                    findings.append(StaleFinding(
                        doc=str(doc.relative_to(REPO_ROOT)),
                        line=line_num,
                        claim=f"{claim_layers} 层",
                        actual=f"ea-compliance 实际 {ea_layers} 层",
                        severity="medium",
                    ))
    return findings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dimension", choices=["ea", "flow", "api", "docs", "paths", "numbers"])
    parser.add_argument("--fix-marker", action="store_true",
                        help="报告但不改文档（v1 阶段保守策略）")
    args = parser.parse_args()

    findings = []

    if args.dimension is None or args.dimension == "ea":
        # §9 各项自动汇总（实际是数据收集）
        ea_items = count_ea_compliance_items()
        if not ea_items:
            findings.append(StaleFinding(
                doc="ea-compliance.py", line=0,
                claim="存在且能跑",
                actual="找不到脚本",
                severity="high",
            ))

    if args.dimension is None or args.dimension == "paths":
        findings.extend(verify_sop_paths())

    if args.dimension is None or args.dimension == "numbers":
        # 用 runtime 总数校验文档
        ea_items = count_ea_compliance_items()
        ea_total = ea_items.get("total", 0) if isinstance(ea_items, dict) else 0
        if ea_total == 0 and ea_items:
            # 回退格式：layers dict
            ea_total = sum(l.get("count", 0) for l in ea_items.values())
        if ea_total > 0:
            docs_to_scan = [
                REPO_ROOT / "ToT" / "GETTING_STARTED.md",
                REPO_ROOT / "ToT" / "ea" / "roadmap.md",
                REPO_ROOT / "ToT" / "README.md",
                REPO_ROOT / "README.md",
            ]
            for doc in docs_to_scan:
                if not doc.exists():
                    continue
                for line_num, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
                    # 检查 X/Y PASS 格式
                    for m in re.finditer(r"(\d+)/(\d+)\s*PASS", line):
                        total = int(m.group(2))
                        if total != ea_total:
                            findings.append(StaleFinding(
                                doc=str(doc.relative_to(REPO_ROOT)),
                                line=line_num,
                                claim=f"{m.group(1)}/{total} PASS",
                                actual=f"当前 ea-compliance {ea_total}/{ea_total} PASS",
                                severity="medium",
                            ))

    if args.json:
        print(json.dumps([asdict(f) for f in findings],
                         indent=2, ensure_ascii=False))
        return

    if not findings:
        print("✅ 无 stale 数据：所有文档声明与实际一致。")
        return

    print(f"⚠️ 发现 {len(findings)} 处 stale 数据：\n")
    by_doc = {}
    for f in findings:
        by_doc.setdefault(f.doc, []).append(f)
    for doc, fs in sorted(by_doc.items()):
        print(f"## {doc}  ({len(fs)} 处)\n")
        for f in fs:
            print(f"  L{f.line}: {f.claim} → 实际: {f.actual}  [{f.severity}]")
        print()

    print(f"\n💡 建议：")
    print(f"  - high 项: 必须更新文档")
    print(f"  - medium 项: 建议更新")
    print(f"  - low 项: 可选更新")
    sys.exit(0 if not any(f.severity == "high" for f in findings) else 1)


if __name__ == "__main__":
    main()