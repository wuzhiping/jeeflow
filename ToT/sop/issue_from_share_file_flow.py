#!/usr/bin/env python3
"""issue_from_share_file_flow.py · 从 file-share 取件码建立 issue 跟踪

实现 `ToT/sop/issue-from-share-file-flow.md` SOP 的 6 步流程。

用法：
    ./ToT/bin/jf python3 ToT/sop/issue_from_share_file_flow.py <取件码>
    ./ToT/bin/jf python3 ToT/sop/issue_from_share_file_flow.py <取件码> --requirement "需求说明"

流程：
    1. 输入取件码
    2. 重复检测（核心规则：重复只出报告不动作）
    3. 下载到 tmp
    4. tmp 解压 + 预览
    5. 确认需求（用户需 --requirement 或手动确认）
    6. 建立 issues/<code>_<date>.md + <code>_<date>/ raw 子目录

安全约束（与 SOP §4 一致）：
    ❌ 不修改任何 SOP / 脚本 / 配置 / 流程定义 / 留档
    ✅ 只读 + 只在 ToT/issues/ 下创建
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
ISSUES_DIR = BASE / "ToT" / "issues"
SHARE_CONFIG_PATH = BASE / "ToT" / "config" / "share.json"


def log(msg):
    print(f"[issue_flow] {msg}", flush=True)


def load_share_config(path: Path = SHARE_CONFIG_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"share.json not found at {path}")
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    if "share" not in cfg:
        raise KeyError(f"share.json missing 'share' block")
    return cfg["share"]


def step2_check_duplicate(code: str) -> list:
    """重复检测：返回已存在的 issue 文件列表（空 = 未重复）"""
    return sorted(ISSUES_DIR.glob(f"{code}_*.md"))


def report_duplicate(code: str, existing: list) -> None:
    """取件码重复：只出报告，不动作"""
    log(f"⚠️  取件码 {code} 已存在 issue 记录：")
    for f in existing:
        log(f"    {f.relative_to(BASE)}")
    log("")
    log("=== 已有记录摘要 ===")
    for f in existing:
        log(f"--- {f.relative_to(BASE)} ---")
        try:
            head = f.read_text(encoding="utf-8").split("\n")[:10]
            for line in head:
                log(f"    {line}")
        except Exception as e:
            log(f"    ⚠️ 读取失败: {e}")

        raw_dir = f.parent / f.stem
        if raw_dir.exists():
            file_count = sum(1 for _ in raw_dir.rglob("*") if _.is_file())
            log(f"    raw: {raw_dir.relative_to(BASE)} ({file_count} 文件)")

    log("")
    log("按 SOP §5 规则：只出报告，不动作，等待用户指令。")
    log("用户选项：")
    log("  - 新建：用 --force 强制创建新 issue（用当前日期）")
    log("  - 续接：手动编辑已有 issue")
    log("  - 跳过：直接退出")


def step3_download(code: str, share_config: dict, tmp_dir: Path) -> tuple:
    """下载到 tmp，返回 (download_url, size, file_type)

    失败时返回 (None, 0, "") —— main 据此判定不创建 issue。
    容错规则见 `ToT/sop/issue-from-share-file-flow.md` §3 Step 3：
      - HTTP 4xx/5xx → 报告错误
      - 文件 < 100 bytes → 报告异常（疑似错误页）
      - 响应为 JSON 错误（`{"code":...}`） → 报告错误
    """
    template = share_config["download_url_template"]
    download_url = template.format(code=code)
    log(f"☁️  下载: {download_url}")

    tmp_dir.mkdir(parents=True, exist_ok=True)
    target = tmp_dir / "file.bin"

    try:
        # curl 加 -w 拿 HTTP code（追加到 stdout 末尾）
        result = subprocess.run(
            [
                "curl", "-sS", "-L", "--max-time", "60",
                "-w", "\n%{http_code}",
                "-o", str(target),
                download_url,
            ],
            capture_output=True, text=True, timeout=70,
        )
        if result.returncode != 0:
            log(f"❌ curl 失败: {result.stderr}")
            return None, 0, ""

        # 解析 HTTP code（最后一行）
        http_code = "000"
        if result.stdout:
            lines = result.stdout.strip().split("\n")
            if lines and lines[-1].isdigit() and len(lines[-1]) == 3:
                http_code = lines[-1]

        # 容错 #1: HTTP 4xx/5xx
        if http_code.startswith("4") or http_code.startswith("5"):
            log(f"❌ HTTP {http_code}（取件码无效 / 过期 / 服务端异常）")
            return None, 0, ""
    except Exception as e:
        log(f"❌ 下载异常: {e}")
        return None, 0, ""

    if not target.exists():
        log(f"❌ 下载文件不存在")
        return None, 0, ""

    size = target.stat().st_size

    # 容错 #2: 文件过小（疑似错误页 / JSON 错误响应）
    if size < 100:
        log(f"❌ 文件过小（{size} bytes，疑似错误页）")
        try:
            head = target.read_text(errors="replace")[:200]
            log(f"   内容预览: {head}")
        except Exception:
            pass
        return None, 0, ""

    # 容错 #3: JSON 错误响应（file-share 实际返回 200 + JSON body）
    try:
        with target.open("rb") as f:
            head_bytes = f.read(100)
        if head_bytes.lstrip().startswith(b"{") and b'"code"' in head_bytes:
            head_text = head_bytes.decode("utf-8", errors="replace")
            log(f"❌ 服务端返回 JSON 错误响应：")
            log(f"   {head_text[:200]}")
            return None, 0, ""
    except Exception:
        pass

    # 正常：检测文件类型
    file_result = subprocess.run(["file", "-b", str(target)], capture_output=True, text=True)
    file_type = file_result.stdout.strip()

    log(f"   size: {size} bytes")
    log(f"   type: {file_type}")
    log(f"   HTTP: {http_code}")
    return download_url, size, file_type


def step4_extract_preview(tmp_dir: Path) -> dict:
    """解压 + 预览，返回 {file_listing, key_summaries}"""
    extracted = tmp_dir / "extracted"
    extracted.mkdir(parents=True, exist_ok=True)
    target = tmp_dir / "file.bin"

    file_result = subprocess.run(["file", "-b", str(target)], capture_output=True, text=True)
    file_type = file_result.stdout.strip()

    try:
        if "gzip" in file_type.lower():
            subprocess.run(["tar", "-xzf", str(target), "-C", str(extracted)],
                          check=True, capture_output=True)
        elif "Zip" in file_type:
            subprocess.run(["unzip", "-q", str(target), "-d", str(extracted)],
                          check=True, capture_output=True)
        else:
            # 裸文件
            (extracted / "original").write_bytes(target.read_bytes())
    except Exception as e:
        log(f"❌ 解压失败: {e}")
        return {"file_listing": "", "key_summaries": ""}

    # 文件清单
    files = sorted([p for p in extracted.rglob("*") if p.is_file()])
    file_listing = "\n".join(str(p.relative_to(extracted)) for p in files)

    log(f"   文件清单（{len(files)} 个文件，前 20）:")
    for p in files[:20]:
        log(f"     - {p.relative_to(extracted)}")
    if len(files) > 20:
        log(f"     ... +{len(files)-20} more")

    # 关键文件摘要
    key_summaries = ""
    for fname in ["report.md", "README.md"]:
        matches = list(extracted.rglob(fname))
        if matches:
            m = matches[0]
            try:
                content = m.read_text(encoding="utf-8")
                key_summaries += f"\n**`{m.relative_to(extracted)}` (前 40 行)**:\n"
                key_summaries += "```\n"
                key_summaries += "\n".join(content.split("\n")[:40])
                key_summaries += "\n```\n"
                log(f"   ✓ 关键文件: {m.relative_to(extracted)}")
            except Exception:
                pass
            break  # 只取第一个匹配

    return {"file_listing": file_listing, "key_summaries": key_summaries}


def step6_create_issue(code: str, date: str, date_human: str, requirement: str,
                       download_url: str, orig_filename: str, size: int,
                       file_type: str, file_listing: str, key_summaries: str,
                       tmp_dir: Path) -> Path:
    """建立 issue + 复制 raw"""
    issue_file = ISSUES_DIR / f"{code}_{date}.md"
    raw_dir = ISSUES_DIR / f"{code}_{date}"

    log(f"📝 建立 issue: {issue_file.relative_to(BASE)}")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # 复制 raw
    extracted = tmp_dir / "extracted"
    if extracted.exists():
        for p in extracted.rglob("*"):
            if p.is_file():
                target = raw_dir / p.relative_to(extracted)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(p.read_bytes())
    raw_count = sum(1 for _ in raw_dir.rglob("*") if _.is_file())
    log(f"   raw: {raw_dir.relative_to(BASE)} ({raw_count} 文件)")

    # 推测意图（基础启发式）
    guess_type = "未知"
    guess_purpose = "未知"
    if "report.md" in file_listing and "invoice-approval" in file_listing:
        guess_type = "invoice-approval 流程测试归档"
        guess_purpose = "archive_flow.py 产物 / 跨环境测试快照"
    elif "fdep" in file_listing.lower():
        guess_type = "FDEP 相关产物"
        guess_purpose = "FDEP 元流程产物"

    # 写 issue 文件
    content = f"""# Issue · 取件码 {code} · {date}

> **创建时间**: {date_human}
> **取件码来源**: {requirement if requirement else "（未指定）"}
> **raw 文件**: [`./{code}_{date}/`](./{code}_{date}/)（{raw_count} 个文件）
> **状态**: 🟡 待用户确认需求

---

## 1. 取件码元信息

- **取件码**: `{code}`
- **下载 URL**: `{download_url}`
- **文件名**: `{orig_filename}`
- **文件大小**: {size} bytes
- **MIME/类型**: `{file_type}`

---

## 2. 初步预览（来自 tmp 解压）

### 2.1 文件清单

```
{file_listing}
```

### 2.2 关键文件摘要
{key_summaries}

### 2.3 推测意图

- **文件类型**: {guess_type}
- **可能用途**: {guess_purpose}
- **风险信号**: 无明显异常

---

## 3. 确认需求

| # | 问题 | 用户回复 |
|---|------|----------|
| 1 | Issue 类型？（BUG / 需求 / 咨询 / 迁移） | （待回复） |
| 2 | 需要做什么？（分析 / 修复 / 设计 / 归档） | （待回复） |
| 3 | 涉及哪个流程？ | （待回复） |
| 4 | 是否需写入 customer-checks/？ | （待回复） |

---

## 4. 后续行动

| 日期 | 动作 | 涉及文件 | 结果 |
|------|------|----------|------|
| | | | |

---

## 5. 关联文档

- [`../sop/issue-from-share-file-flow.md`](../sop/issue-from-share-file-flow.md) — 创建 SOP
- [`../sop/archive-flow.md`](../sop/archive-flow.md) — 若取件码来自 archive_flow

---

## 6. raw 文件说明

子目录 `./{code}_{date}/` 包含从 file-share 下载的原始内容。
**禁止**修改 raw 内容（只读）；如需修改请派生新文件。
"""

    issue_file.write_text(content, encoding="utf-8")
    log(f"   ✓ {issue_file.relative_to(BASE)} 已创建")
    return issue_file


def main():
    parser = argparse.ArgumentParser(
        description="从 file-share 取件码建立 issue 跟踪",
        epilog="详见 ToT/sop/issue-from-share-file-flow.md",
    )
    parser.add_argument("code", help="file-share 取件码")
    parser.add_argument("--requirement", "-r", default="",
                        help="需求说明（来源 / 用途）")
    parser.add_argument("--force", action="store_true",
                        help="强制创建新 issue（即便取件码已存在）")
    parser.add_argument("--keep-tmp", action="store_true",
                        help="保留 /tmp 工作目录（默认清理）")
    args = parser.parse_args()

    code = args.code
    date = time.strftime("%Y%m%d")
    date_human = time.strftime("%Y-%m-%d %H:%M:%S")

    log(f"📋 取件码: {code}, 日期: {date}")

    # Step 2: 重复检测
    log("\n[Step 2] 重复检测")
    existing = step2_check_duplicate(code)
    if existing and not args.force:
        report_duplicate(code, existing)
        return 0

    if existing and args.force:
        log(f"⚠️  --force 启用，将创建新 issue（覆盖已有）")

    # Step 3: 下载
    log("\n[Step 3] 下载")
    share_config = load_share_config()
    tmp_dir = Path(f"/tmp/issue_{code}_{date}")
    download_url, size, file_type = step3_download(code, share_config, tmp_dir)
    if not download_url:
        return 1

    # Step 4: 解压 + 预览
    log("\n[Step 4] tmp 解压 + 预览")
    preview = step4_extract_preview(tmp_dir)
    if not preview["file_listing"]:
        log("❌ 解压失败，无法继续")
        return 1

    # Step 5: 确认需求（--requirement 跳过交互）
    log("\n[Step 5] 确认需求")
    if args.requirement:
        log(f"   需求来源: {args.requirement}")
    else:
        log("   ⚠️ 未指定需求（issue 文件中标记为「待回复」）")

    # Step 6: 建立 issue
    log("\n[Step 6] 建立 issue + raw 存档")
    orig_filename = preview["file_listing"].split("\n")[0] if preview["file_listing"] else "unknown"
    issue_file = step6_create_issue(
        code, date, date_human, args.requirement,
        download_url, orig_filename, size, file_type,
        preview["file_listing"], preview["key_summaries"],
        tmp_dir,
    )

    # 清理 tmp
    if not args.keep_tmp:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        log(f"\n🧹 清理 tmp: {tmp_dir}")
    else:
        log(f"\n⚠️  保留 tmp: {tmp_dir}")

    log(f"\n{'='*60}")
    log(f"✅ Issue 建立完成")
    log(f"   {issue_file.relative_to(BASE)}")
    log(f"\n下一步: 编辑 issue 文件填写 §3 确认需求（与用户对话）")
    log(f"{'='*60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())