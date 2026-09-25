#!/usr/bin/env python3
"""jffeedback — 03-participant 的低摩擦反馈 CLI（A6）

让参与者 30 秒创建一条反馈文件：
  - 一行标题（必填）
  - 自动捕获最近 curl 的响应（如提供）
  - 自动填日期 + 重定向到 feedback-triage.py

用法：
  jffeedback "找不到我的待办"
  jffeedback "同意后没动" --response '{"code":0,...}'
  jffeedback --from-stdin  < some_error.log

环境变量：
  JFFEEDBACK_TAG    默认 'doc-gap'
  JFFEEDBACK_PERSONA 默认 '03'

依赖：仅 Python 3.10+ 标准库
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FEEDBACK_DIR = REPO_ROOT / "ToT" / "CC" / "feedback"


def next_seq() -> str:
    """下一个可用序号"""
    existing = list(FEEDBACK_DIR.glob("03-participant-*.md"))
    nums = []
    for f in existing:
        parts = f.stem.split("-")
        if len(parts) >= 3 and parts[2].isdigit():
            nums.append(int(parts[2]))
    return f"{max(nums, default=0) + 1:03d}"


def render_template(seq: str, title: str, response: str | None) -> str:
    persona = os.environ.get("JFFEEDBACK_PERSONA", "03")
    tag = os.environ.get("JFFEEDBACK_TAG", "doc-gap")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    reporter = os.environ.get("USER", "anonymous")
    response_block = ""
    if response:
        response_block = f"""

## 证据（Evidence）

```json
{response}
```
"""
    return f"""# Feedback: {seq} - {title}

> **Persona**: {persona}
> **Date**: {today}
> **Reporter**: {reporter}
> **Severity**: P1

## 现象（What happened）

{title}
{response_block}
## 影响（Impact）

请补充

## 期望（What we want）

请补充

## 已尝试（What I tried）

请补充

## 标签（Tags）

`{tag}`

"""


def main():
    parser = argparse.ArgumentParser(description="03-participant 低摩擦反馈 CLI")
    parser.add_argument("title", nargs="?", help="反馈标题（简短描述）")
    parser.add_argument("--response", "-r", help="API 响应 JSON（粘贴或 stdin）")
    parser.add_argument("--from-stdin", action="store_true", help="从 stdin 读 title + response")
    parser.add_argument("--tag", "-t", help="标签（覆盖 env）")
    parser.add_argument("--dry-run", action="store_true", help="只打印不写文件")
    args = parser.parse_args()

    title = args.title
    response = args.response

    if args.from_stdin:
        # 从 stdin 读：第一行 = title，剩下 = response
        data = sys.stdin.read().strip()
        parts = data.split("\n", 1)
        title = title or parts[0]
        if len(parts) > 1:
            response = response or parts[1]

    if not title:
        print("❌ 缺少 title（必填）", file=sys.stderr)
        print('   用法：jffeedback "找不到我的待办"', file=sys.stderr)
        sys.exit(1)

    seq = next_seq()
    safe_title = title.replace("/", "-").replace(" ", "-")[:30]
    filename = f"03-participant-{seq}-{safe_title}.md"
    content = render_template(seq, title, response)

    if args.dry_run:
        print(f"--- 预览：{filename} ---")
        print(content)
        return

    FEEDBACK_DIR.mkdir(exist_ok=True)
    path = FEEDBACK_DIR / filename
    path.write_text(content, encoding="utf-8")
    print(f"✅ 反馈已创建：{path}")
    print(f"   序号：{seq}")
    print(f"   标题：{title}")
    print()
    print("💡 下一步：")
    print(f"   1. 编辑 {path} 补充「现象」「期望」「已尝试」")
    print(f"   2. 跑 feedback-triage.py 自动分流到 01/02/04")

    # 自动触发 triage（如可用）
    triage = REPO_ROOT / "ToT" / "sop" / "feedback-triage.py"
    if triage.exists():
        print()
        print("🔄 自动跑 feedback-triage.py ...")
        try:
            r = subprocess.run(
                ["python3", str(triage), "--dry-run"],
                capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30
            )
            print(r.stdout)
        except Exception as e:
            print(f"⚠️ triage 跳过：{e}")


if __name__ == "__main__":
    main()