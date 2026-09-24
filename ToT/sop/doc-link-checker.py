#!/usr/bin/env python3
"""doc-link-checker.py — ToT/docs ↔ vendor/jeeflow/*.py 行号引用校准

扫描所有 ToT/docs/*.md 中的 `vendor/jeeflow/<file>.py:<line>` 模式，
与实际代码核对，输出 drift 报告。

校验逻辑：
1. 提取 .md 中所有 `vendor/jeeflow/<file>.py:<line>` 引用
2. 对每条引用：
   - 验证文件存在
   - 验证行号有效（≤ 代码总行数）
   - 检查目标行内容是否像定义（def / class / 常量赋值）
   - 若不像，查找附近 ±5 行内的匹配（粗粒度 "near match"）
3. 输出 JSON 报告 + 文本汇总
4. exit 0 = 无 drift；exit 1 = 有 drift；exit 2 = 脚本错误

依赖：仅标准库（re / json / sys / pathlib）

用法：
    python3 ToT/sop/doc-link-checker.py
    python3 ToT/sop/doc-link-checker.py --tolerance 3
    python3 ToT/sop/doc-link-checker.py --json
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = BASE / "ToT" / "docs"
VENDOR_DIR = BASE / "vendor" / "jeeflow"

# 匹配 `vendor/jeeflow/<filename>.py:<line>` 后可跟随字符
LINE_PATTERN = re.compile(
    r"vendor/jeeflow/(\w+\.py):(\d+)(?:-(\d+))?"
)

# 匹配类/函数/常量定义
DEF_PATTERN = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(")
CLASS_PATTERN = re.compile(r"^class\s+(\w+)\s*[\(:]")
# 大写常量（如 PERM_EDIT）
CONST_PATTERN = re.compile(
    r"^[A-Z_][A-Z0-9_]*\s*[:=]"
)
# dataclass 字段定义（小写 + 类型注解 + =），如 event_listener: Optional[...] = None
FIELD_PATTERN = re.compile(
    r"^\s+([a-z_]\w*)\s*:\s*[^=]+=\s*"
)
# 模块级常量赋值（如 KEY_NEXT_NODE_OPERATOR = "..."）
MODCONST_PATTERN = re.compile(
    r"^[A-Z][A-Z0-9_]*\s*=\s*[^=]"
)
# 缩进行（函数/类/方法体内任意位置）— 用于接受「调用站点」「赋值语句」「字符串」等
INDENTED_PATTERN = re.compile(r"^\s+\S")

DEFAULT_TOLERANCE = 5


def extract_references(md_path: Path):
    """提取 markdown 中所有 vendor/jeeflow/<file>.py:<line> 引用。"""
    refs = []
    content = md_path.read_text(encoding="utf-8")
    for m in LINE_PATTERN.finditer(content):
        filename = m.group(1)
        line_num = int(m.group(2))
        end_line = int(m.group(3)) if m.group(3) else line_num
        ctx_start = max(0, m.start() - 40)
        ctx_end = min(len(content), m.end() + 40)
        ctx = content[ctx_start:ctx_end].replace("\n", " ")
        refs.append(
            {
                "md_file": str(md_path.relative_to(BASE)),
                "md_line": content[: m.start()].count("\n") + 1,
                "code_file": filename,
                "code_line": line_num,
                "code_end_line": end_line,
                "context": ctx,
            }
        )
    return refs


def verify_reference(ref, tolerance):
    """验证一条引用：实际行号处是否有定义 / 类 / 常量。"""
    code_path = VENDOR_DIR / ref["code_file"]
    if not code_path.exists():
        return {
            "status": "FILE_NOT_FOUND",
            "actual": f"vendor/jeeflow/{ref['code_file']} 不存在",
        }
    lines = code_path.read_text(encoding="utf-8").splitlines()
    total = len(lines)
    target = ref["code_line"]
    if target < 1 or target > total:
        return {
            "status": "LINE_OUT_OF_RANGE",
            "actual": f"代码共 {total} 行，引用 {target}",
        }
    actual = lines[target - 1]
    if (
        DEF_PATTERN.match(actual)
        or CLASS_PATTERN.match(actual)
        or CONST_PATTERN.match(actual)
        or FIELD_PATTERN.match(actual)
        or MODCONST_PATTERN.match(actual)
        or (INDENTED_PATTERN.match(actual) and not actual.strip().startswith("#"))
    ):
        return {
            "status": "OK",
            "actual": actual.strip()[:80],
        }
    near = []
    for offset in range(1, tolerance + 1):
        for delta in (-offset, offset):
            ln = target + delta
            if 1 <= ln <= total:
                content = lines[ln - 1]
                if (
                    DEF_PATTERN.match(content)
                    or CLASS_PATTERN.match(content)
                    or CONST_PATTERN.match(content)
                    or FIELD_PATTERN.match(content)
                    or MODCONST_PATTERN.match(content)
                    or (
                        INDENTED_PATTERN.match(content)
                        and not content.strip().startswith("#")
                    )
                ):
                    near.append((delta, content.strip()[:80]))
    if near:
        nearest_delta, nearest_content = min(near, key=lambda x: abs(x[0]))
        return {
            "status": "NEAR_MATCH",
            "actual": f"行 {target + nearest_delta}: {nearest_content} (offset {nearest_delta:+d})",
            "near_content": nearest_content,
            "near_offset": nearest_delta,
        }
    return {
        "status": "NO_DEF",
        "actual": actual.strip()[:80],
    }


def format_text_report(results, by_file):
    lines = []
    drift_count = sum(1 for r in results if r["status"] != "OK")
    ok_count = sum(1 for r in results if r["status"] == "OK")
    near_match_count = sum(1 for r in results if r["status"] == "NEAR_MATCH")
    lines.append(
        f"扫描 {len(results)} 条引用 → "
        f"✅ OK {ok_count} · "
        f"⚠️ NEAR_MATCH {near_match_count} · "
        f"❌ DRIFT {drift_count - near_match_count}"
    )
    lines.append("")
    if drift_count == 0:
        lines.append("✅ 无 drift：所有行号引用与代码一致。")
        return lines
    lines.append(f"发现 {drift_count} 条 drift：")
    lines.append("")
    for status, items in by_file.items():
        if status == "OK":
            continue
        lines.append(f"## {status} ({len(items)} 条)")
        for r in items[:20]:
            lines.append(
                f"  {r['md_file']}:{r['md_line']} → "
                f"vendor/jeeflow/{r['code_file']}:{r['code_line']}"
            )
            lines.append(f"    ctx: …{r['context']}…")
            lines.append(f"    actual: {r['actual']}")
        if len(items) > 20:
            lines.append(f"  … 还有 {len(items) - 20} 条")
        lines.append("")
    return lines


def main():
    ap = argparse.ArgumentParser(
        description="扫描 ToT/docs 中 vendor/jeeflow 行号引用"
    )
    ap.add_argument(
        "--tolerance", type=int, default=DEFAULT_TOLERANCE,
        help=f"near_match 容忍行数（默认 {DEFAULT_TOLERANCE}）"
    )
    ap.add_argument(
        "--json", action="store_true", help="输出 JSON 报告"
    )
    ap.add_argument(
        "--md-file", type=str, help="只扫描指定 .md 文件"
    )
    args = ap.parse_args()

    if not DOCS_DIR.exists():
        print(f"ERROR: {DOCS_DIR} 不存在", file=sys.stderr)
        return 2
    if not VENDOR_DIR.exists():
        print(f"ERROR: {VENDOR_DIR} 不存在", file=sys.stderr)
        return 2

    if args.md_file:
        md_paths = [BASE / args.md_file]
        if not md_paths[0].exists():
            print(f"ERROR: {md_paths[0]} 不存在", file=sys.stderr)
            return 2
    else:
        md_paths = sorted(
            p for p in DOCS_DIR.rglob("*.md")
            if p.name != "diffs.md"
        )

    all_refs = []
    for md in md_paths:
        all_refs.extend(extract_references(md))

    results = []
    for ref in all_refs:
        v = verify_reference(ref, args.tolerance)
        results.append({**ref, **v})

    by_status = defaultdict(list)
    for r in results:
        by_status[r["status"]].append(r)

    drift_count = sum(1 for r in results if r["status"] != "OK")
    by_file = by_status

    if args.json:
        report = {
            "summary": {
                "total": len(results),
                "ok": len(by_status.get("OK", [])),
                "near_match": len(by_status.get("NEAR_MATCH", [])),
                "drift": drift_count - len(by_status.get("NEAR_MATCH", [])),
                "tolerance": args.tolerance,
            },
            "by_status": {
                k: [{"md_file": r["md_file"], "md_line": r["md_line"],
                     "code_file": r["code_file"], "code_line": r["code_line"],
                     "context": r["context"], "actual": r["actual"]}
                    for r in v]
                for k, v in by_status.items()
            },
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        text = format_text_report(results, by_file)
        print("\n".join(text))

    return 1 if drift_count > len(by_status.get("NEAR_MATCH", [])) else 0


if __name__ == "__main__":
    sys.exit(main())