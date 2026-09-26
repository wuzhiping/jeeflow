#!/usr/bin/env python3
"""version-bump-guard.py — 版本更新守卫

原则：vendor/jeeflow/__init__.py:__version__ 反映**运行时行为变化**。
  - 代码变更（*.py）→ 自动 bump（release.sh 正常流程）
  - 纯文档变更（*.md, docs/, ToT/docs/, ToT/CC/, ToT/ea/ 等）→ 需人工确认 + 理由
  - 混合变更 → 自动 bump

用法：
  python3 version-bump-guard.py                  # 检查 git diff（默认）
  python3 version-bump-guard.py --confirm-doc-only "理由"
                                                  # 强制文档变更也 bump
  python3 version-bump-guard.py --dry-run         # 只显示判定结果

退出码：
  0 = 可以自动 bump
  1 = 需要 --confirm-doc-only
  2 = git 错误
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# 文档类路径模式（任何匹配 → 视为纯文档变更）
DOC_PATH_PATTERNS = [
    r".*\.md$",
    r".*\.html$",
    r".*\.txt$",
    r".*\.json$",          # 注意：仅当文件内容是 doc 时才算
    r"^docs/",            # 项目根 docs/
    r"^ToT/docs/",         # ToT 知识库
    r"^ToT/CC/",           # 客户中心（含 _stories/）
    r"^ToT/ea/",           # EA 飞轮（含 README/PPT/roadmap/iterations）
    r"^ToT/GETTING_STARTED\.md$",
    r"^ToT/HANDBOOK\.md$",
    r"^ToT/README\.md$",
    r"^ToT/mapping\.md$",
    r"^ToT/sop/[^/]+\.md$",   # SOP 文档（.md 部分）
    r"^ToT/tdd/",         # 测试基线（输出物，非代码）
    r"^ToT/customer-resets/",
    r"^ToT/customer-checks/",
    r"^ToT/issues/",
    r"^ToT/config/",      # 配置（含 share.json）
    r"^README\.md$",
    r"^AGENTS\.md$",
    r"^PRD\.md$",
    r"^BDD\.md$",
    r"^ToT/sop/[^/]+\.sh$",  # 脚本文件可被代码触发，列入 doc check
    r"^scripts/",
    r"^bin/",
    r"^hooks/",
    r"^archived/",
    r"^\.github/",
    r"^docs/architecture\.md$",
    r"^docs/api\.md$",
    r"^docs/actions\.md$",
    r"^docs/AGENTS\.md$",
    r"^docs/flow\.md$",
    r"^docs/flow-tutorial\.md$",
    r"^docs/state\.md$",
    r"^docs/known-issues\.md$",
    r"^docs/integration\.md$",
    r"^docs/pg_schema\.sql$",   # SQL 是数据契约，不是代码
    r"^docs/openapi\.json$",     # OpenAPI 规范
    r"^docs/BUGS\.md$",
]


def is_doc_path(path: str) -> bool:
    """判断路径是否属于文档类"""
    for pattern in DOC_PATH_PATTERNS:
        if re.match(pattern, path):
            return True
    return False


def get_git_diff_files() -> list[str]:
    """获取 git diff 中的所有变更文件（相对路径）"""
    files = set()

    # 1. 已 staged 的变更
    r = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30,
    )
    if r.returncode == 0:
        for line in r.stdout.strip().splitlines():
            if line:
                files.add(line)

    # 2. 工作区未 staged 的变更
    r = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30,
    )
    if r.returncode == 0:
        for line in r.stdout.strip().splitlines():
            if line:
                files.add(line)

    # 3. 未跟踪文件
    r = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30,
    )
    if r.returncode == 0:
        for line in r.stdout.strip().splitlines():
            if line:
                files.add(line)

    return sorted(files)


def classify_files(files: list[str]) -> tuple[list[str], list[str]]:
    """分类文件为 doc vs non-doc"""
    doc_files = []
    non_doc_files = []
    for f in files:
        if is_doc_path(f):
            doc_files.append(f)
        else:
            non_doc_files.append(f)
    return doc_files, non_doc_files


def main():
    parser = argparse.ArgumentParser(
        description="version-bump-guard — 检查 git diff 是否需要自动 bump 版本",
    )
    parser.add_argument(
        "--confirm-doc-only",
        metavar="REASON",
        help="确认纯文档变更也要 bump 版本（需提供理由）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只显示判定结果，不退出",
    )
    args = parser.parse_args()

    try:
        files = get_git_diff_files()
    except Exception as e:
        print(f"❌ git 错误: {e}", file=sys.stderr)
        sys.exit(2)

    if not files:
        print("ℹ️ 无 git diff，version-bump 无事可做")
        sys.exit(0)

    doc_files, non_doc_files = classify_files(files)

    print("=" * 60)
    print(f"📋 git diff 文件分类")
    print("=" * 60)
    print(f"\n文档类文件 ({len(doc_files)}):")
    for f in doc_files:
        print(f"  📄 {f}")
    print(f"\n非文档类文件 ({len(non_doc_files)}):")
    for f in non_doc_files:
        print(f"  📦 {f}")
    print()

    # 判定
    is_doc_only = len(non_doc_files) == 0

    if not is_doc_only:
        # 有非文档变更 → 自动 bump OK
        print("✅ 检测到非文档变更（代码 / 配置 / 资源），可自动 bump 版本")
        sys.exit(0)

    # 纯文档变更
    if args.confirm_doc_only:
        print(f"⚠️ 纯文档变更，但已通过 --confirm-doc-only 确认")
        print(f"   理由：{args.confirm_doc_only}")
        print(f"✅ 继续 bump 版本")
        sys.exit(0)

    # 需要确认
    print("=" * 60)
    print("❌ 检测到**纯文档变更**（无代码变更）")
    print("=" * 60)
    print()
    print("**原则**：`vendor/jeeflow/__init__.py:__version__` 反映运行时行为变化。")
    print("纯文档变更不应自动 bump 引擎版本号（避免版本语义混乱）。")
    print()
    print("如果确实需要 bump 版本（例如：同步健康度数据到 changelog），请明确原因：")
    print()
    print("  bash ToT/sop/release.sh v1.12.2 --reason \"同步健康度数据 + CC 飞轮中枢\"")
    print()
    print("或在脚本中调用：")
    print("  python3 ToT/sop/version-bump-guard.py --confirm-doc-only \"<理由>\"")
    print()
    print("否则，请只 commit 文档变更，不发布新版本。")

    if args.dry_run:
        sys.exit(0)  # dry-run 不报错
    sys.exit(1)


if __name__ == "__main__":
    main()