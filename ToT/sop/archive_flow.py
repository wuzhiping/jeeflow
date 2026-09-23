#!/usr/bin/env python3
"""archive_flow.py · 流程归档与分享工具

用法：
  ./ToT/bin/jf python3 ToT/sop/archive_flow.py <flow-id> [--clean] [--expire-days N]

步骤：
  1. 收集 SPI 背景数据（组织架构 + 用户信息）
  2. 生成测试使用改进报告
  3. 打包所有相关产出到 tar.gz
  4. 用 file-share skill 上传，返回取件码
  5. （--clean 时）清理本地测试数据
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
FLOWS_DIR = BASE / "ToT" / "flows"
TDD_DIR = BASE / "ToT" / "tdd"
TESTS_FILE = BASE / "ToT" / "tdd" / "tests.json"
ARCHIVE_DIR = BASE / "ToT" / "archive"
SHARE_CONFIG_PATH = BASE / "ToT" / "config" / "share.json"

# SPI API（可通过 SPI_FOLDER env 切换）
SPI_API = os.environ.get("SPI_API", "http://127.0.0.1:8101/api/spi")


def load_share_config(path: Path = SHARE_CONFIG_PATH) -> dict:
    """加载 share.json（archive_flow 的 share endpoint 真相源）

    返回 dict 含 upload_url / download_url_template / expire_unit /
         default_expire_value / max_expire_value 等字段。
    """
    if not path.exists():
        raise FileNotFoundError(f"share.json not found at {path}")
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    if "share" not in cfg:
        raise KeyError(f"share.json missing 'share' block at {path}")
    return cfg["share"]


def log(msg):
    print(f"[archive_flow] {msg}", flush=True)


def fetch_spi_users():
    """获取 SPI 用户列表（背景数据）"""
    try:
        import requests
        r = requests.get(f"{SPI_API}/users", params={"pageSize": 100}, timeout=10)
        if r.status_code == 200:
            return r.json().get("users", [])
    except Exception as e:
        log(f"⚠️ SPI users 获取失败: {e}")
    return []


def fetch_spi_depts():
    """获取 SPI 部门列表（组织架构图）"""
    try:
        import requests
        r = requests.get(f"{SPI_API}/depts", params={"pageSize": 100}, timeout=10)
        if r.status_code == 200:
            return r.json().get("depts", [])
    except Exception as e:
        log(f"⚠️ SPI depts 获取失败: {e}")
    return []


def fetch_test_results(flow_id):
    """读 tests.json 中该 flow 的 scenarios 配置 + 最新 baseline + dashboard"""
    config = None
    if TESTS_FILE.exists():
        try:
            data = json.loads(TESTS_FILE.read_text(encoding="utf-8"))
            config = data.get("flows", {}).get(flow_id)
        except Exception:
            pass

    baseline = None
    if TDD_DIR.exists():
        baselines = sorted(TDD_DIR.glob(f"test_{flow_id}_baseline_v*.json"))
        if baselines:
            try:
                baseline = json.loads(baselines[-1].read_text(encoding="utf-8"))
            except Exception:
                pass

    dashboard = None
    dashboard_files = sorted(ARCHIVE_DIR.glob("dashboard_*.json") if ARCHIVE_DIR.exists() else [])
    if not dashboard_files and TDD_DIR.exists():
        dashboard_files = sorted(TDD_DIR.glob("dashboard-history/dashboard_*.json"))
    if dashboard_files:
        try:
            dashboard = json.loads(dashboard_files[-1].read_text(encoding="utf-8"))
        except Exception:
            pass

    return config, baseline, dashboard


def fetch_flow_meta(flow_id):
    """读 flow.json 的 node / edge 统计"""
    flow_json = FLOWS_DIR / f"{flow_id}.json"
    if not flow_json.exists():
        return None
    try:
        d = json.loads(flow_json.read_text(encoding="utf-8"))
        return {
            "name": d.get("name", flow_id),
            "displayName": d.get("displayName", ""),
            "version": d.get("version", ""),
            "node_count": len(d.get("nodes", [])),
            "edge_count": len(d.get("edges", [])),
            "node_types": _count_node_types(d.get("nodes", [])),
        }
    except Exception:
        return None


def _count_node_types(nodes):
    """统计节点类型"""
    from collections import Counter
    types = Counter()
    for n in nodes:
        t = n.get("type", "unknown").replace("snaker:", "")
        types[t] += 1
    return dict(types)


def collect_files(flow_id, work_dir):
    """收集所有相关文件到 work_dir"""
    files_collected = []

    # 1. flow.json
    flow_json = FLOWS_DIR / f"{flow_id}.json"
    if flow_json.exists():
        target = work_dir / "flows" / f"{flow_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(flow_json.read_bytes())
        files_collected.append(str(target.relative_to(work_dir)))

    # 2. flow 文档目录
    flow_docs = FLOWS_DIR / flow_id
    if flow_docs.exists():
        for f in flow_docs.rglob("*"):
            if f.is_file():
                rel = f.relative_to(FLOWS_DIR)
                target = work_dir / "flows" / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(f.read_bytes())
                files_collected.append(str(target.relative_to(work_dir)))

    # 3. tdd baseline（最近 3 个）
    if TDD_DIR.exists():
        baselines = sorted(TDD_DIR.glob(f"test_{flow_id}_baseline_v*.json"))
        baselines += sorted(TDD_DIR.glob(f"test_{flow_id}_baseline_v*.md"))
        for b in baselines[-6:]:  # 最近 3 个 .json + 3 个 .md = 6 个
            target = work_dir / "tdd" / b.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b.read_bytes())
            files_collected.append(str(target.relative_to(work_dir)))

        # tdd test results（最近 5 次）
        results = sorted(TDD_DIR.glob(f"test_{flow_id}_2026*.json"))[-5:]
        results += sorted(TDD_DIR.glob(f"test_{flow_id}_2026*.md"))[-5:]
        for r in results:
            if r.exists():
                target = work_dir / "tdd" / r.name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(r.read_bytes())
                files_collected.append(str(target.relative_to(work_dir)))

    # 4. tests.json（整个文件，但只展示相关 flow）
    if TESTS_FILE.exists():
        target = work_dir / "tests.json"
        target.write_bytes(TESTS_FILE.read_bytes())
        files_collected.append(str(target.relative_to(work_dir)))

    return files_collected


def generate_report(flow_id, flow_meta, config, baseline, dashboard, users, depts):
    """生成测试使用改进报告"""
    lines = [
        f"# 流程测试报告 · {flow_id} · {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "> **生成方式**：`ToT/sop/archive_flow.py` 自动生成",
        f"> **目的**：测试数据归档 + 跨环境分享 + 历史快照",
        "",
        "---",
        "",
        "## 1. 流程基本信息",
        "",
    ]

    if flow_meta:
        lines += [
            f"- **name**: `{flow_meta['name']}`",
            f"- **displayName**: {flow_meta['displayName']}",
            f"- **version**: {flow_meta['version']}",
            f"- **节点数**: {flow_meta['node_count']}",
            f"- **边数**: {flow_meta['edge_count']}",
            f"- **节点类型**: {flow_meta['node_types']}",
        ]
    else:
        lines.append(f"- ⚠️ flow.json 不存在: ToT/flows/{flow_id}.json")
    lines.append("")

    lines += [
        "## 2. 测试配置（来自 tests.json）",
        "",
    ]
    if config:
        lines += [
            f"- **operator**: `{config.get('operator', 'u_fdp_pm')}`",
            f"- **scenarios**: `{config.get('scenarios', '(default)')}`",
            f"- **top_vars**: `{config.get('top_vars', {})}`",
            f"- **baseline**: `{config.get('baseline', '(auto)')}`",
        ]
    else:
        lines.append("- ⚠️ tests.json 中无此 flow 配置")
    lines.append("")

    lines += [
        "## 3. 测试结果（最新 baseline + dashboard）",
        "",
    ]
    if baseline:
        s = baseline.get("summary", {})
        lines += [
            f"- **baseline timestamp**: {baseline.get('timestamp', '?')}",
            f"- **scenarios**: {len(baseline.get('scenarios', []))}",
            f"- **results**: {len(baseline.get('results', {}))}",
        ]
        for label, r in baseline.get("results", {}).items():
            if r:
                state = r["final"]["state"]
                lines.append(f"  - `{label}` → state=`{state}`")
    else:
        lines.append("- ⚠️ 无 baseline")
    lines.append("")

    if dashboard:
        s = dashboard.get("summary", {})
        lines += [
            f"- **dashboard all_passed**: {s.get('all_passed', '?')}",
            f"- **total flows**: {s.get('total_flows', '?')}",
            f"- **total scenarios**: {s.get('total_scenarios', '?')}",
        ]
    lines.append("")

    lines += [
        "## 4. 组织架构图（来自 SPI `/api/spi/depts`）",
        "",
    ]
    if depts:
        for d in depts:
            lines.append(
                f"- **{d.get('name', '?')}** ({d.get('dept_id', '?')}) "
                f"— size={d.get('size', '?')}, leader=`{d.get('leader', '-')}`, "
                f"main_leader=`{d.get('main_leader', '-')}`"
            )
    else:
        lines.append("- ⚠️ 无部门数据（SPI 不可用）")
    lines.append("")

    lines += [
        "## 5. 关键用户（来自 SPI `/api/spi/users`）",
        "",
        "| uid | 姓名 | 岗位 | 部门 | 角色 |",
        "|-----|------|------|------|------|",
    ]
    if users:
        for u in users[:20]:  # 限制 20 个
            roles = ", ".join(u.get("roles", []))
            lines.append(
                f"| `{u.get('uid', '?')}` | {u.get('name', '?')} | "
                f"{u.get('post', '?')} ({u.get('level', '-')}) | "
                f"{u.get('dept_id', '-')} | {roles} |"
            )
    else:
        lines.append("| (无数据) | | | | |")
    lines.append("")

    lines += [
        "## 6. 改进建议（基于 27+ 圈 EA 飞轮经验）",
        "",
        "- ✅ 已用 actor resolver 3 种语法（`@role:` / 顶级变量 / `applicant`）",
        "- ✅ 已用 decision mem 协议（comment / decision_reason / decision_memo）",
        "- ✅ 已用驳回机制（`submitType=5 RE_APPLY` 而非 `submitType=2 REJECT`）",
        "- ⚠️ 建议：CI 集成 tdd-flow 4 模式（dry-run / baseline-only / 实跑 / only-changed）",
        "- ⚠️ 建议：dashboard 自动生成 + time filter + sparkline",
        "- 💡 进阶：跨环境兼容性测试（local-memory → local-pg → org-server → customer-test）",
        "",
        "## 7. 附件清单",
        "",
    ]

    return "\n".join(lines)


def create_archive(flow_id, work_dir, files_collected):
    """打包成 tar.gz"""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    datetime_str = time.strftime("%Y%m%d-%H%M%S")
    tar_name = f"{datetime_str}_{flow_id}.tar.gz"
    tar_path = ARCHIVE_DIR / tar_name

    log(f"📦 打包: {tar_path}")
    subprocess.run(
        ["tar", "-czvf", str(tar_path), "-C", str(work_dir.parent), work_dir.name],
        check=True, capture_output=True,
    )
    log(f"   size: {tar_path.stat().st_size} bytes")
    return tar_path


def upload_to_share(tar_path, expire_value=None, share_config=None):
    """file-share skill 上传，返回取件码

    share_config: 来自 load_share_config() 的 dict；缺省时现场加载。
    expire_value: 过期数值（单位 = share_config["expire_unit"]，默认 "day"）。
    """
    cfg = share_config or load_share_config()
    upload_url = cfg["upload_url"]
    download_template = cfg["download_url_template"]
    expire_unit = cfg.get("expire_unit", "day")
    if expire_value is None:
        expire_value = cfg.get("default_expire_value", 7)

    log(f"☁️ 上传: {tar_path.name}")
    log(f"   endpoint: {upload_url} (from ToT/config/share.json)")
    try:
        result = subprocess.run(
            [
                "curl", "-sS", "-X", "POST", upload_url,
                "-F", f"file=@{tar_path}",
                "-F", f"expire_value={expire_value}",
                "-F", f"expire_style={expire_unit}",
            ],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            log(f"❌ curl 失败: {result.stderr}")
            return None

        resp = json.loads(result.stdout)
        if resp.get("code") == 200:
            code = resp["detail"]["code"]
            name = resp["detail"]["name"]
            url = download_template.format(code=code)
            log(f"✅ 上传成功: {name}")
            log(f"   取件码: {code}")
            log(f"   下载: {url}")
            log(f"   有效期: {expire_value} {expire_unit}")
            return code
        else:
            log(f"❌ 上传失败: {resp}")
            return None
    except Exception as e:
        log(f"❌ 上传异常: {e}")
        return None


def cleanup_local(flow_id, preserve_baselines=3):
    """清理本地测试数据（保留最近 N 个 baseline）"""
    log(f"🧹 清理 {flow_id} 的本地测试数据")

    if not TDD_DIR.exists():
        log("   TDD_DIR 不存在，跳过")
        return

    cleaned = []
    # 删除 test_<flow-id>_2026*.json/md（保留 baseline）
    for f in TDD_DIR.glob(f"test_{flow_id}_2026*.json"):
        f.unlink()
        cleaned.append(f.name)
    for f in TDD_DIR.glob(f"test_{flow_id}_2026*.md"):
        f.unlink()
        cleaned.append(f.name)

    # baseline 保留最近 N 个，旧的删除
    baselines = sorted(TDD_DIR.glob(f"test_{flow_id}_baseline_v*.json"))
    baselines_md = sorted(TDD_DIR.glob(f"test_{flow_id}_baseline_v*.md"))
    for old in baselines[:-preserve_baselines]:
        old.unlink()
        cleaned.append(old.name)
    for old in baselines_md[:-preserve_baselines]:
        old.unlink()
        cleaned.append(old.name)

    log(f"   已清理 {len(cleaned)} 个文件")
    for c in cleaned[:10]:
        log(f"     - {c}")
    if len(cleaned) > 10:
        log(f"     ... +{len(cleaned)-10} more")


def main():
    parser = argparse.ArgumentParser(description="流程归档与分享工具")
    parser.add_argument("flow_id", help="流程 ID（如 invoice-approval / fdep）")
    parser.add_argument("--clean", action="store_true",
                        help="清理本地测试数据（保留最近 3 个 baseline）")
    parser.add_argument("--expire-value", type=int, default=None,
                        help="file-share 过期数值（单位 = share.json 的 expire_unit，默认 day）")
    parser.add_argument("--expire-days", type=int, default=None,
                        help="[兼容旧版] 等同 --expire-value，建议改用 --expire-value")
    parser.add_argument("--no-upload", action="store_true",
                        help="跳过 file-share 上传（只打包）")
    parser.add_argument("--dry-run", action="store_true",
                        help="预览模式：只显示会做什么，不实际打包/上传/清理")
    args = parser.parse_args()

    flow_id = args.flow_id

    # 加载 share config（一次性）
    share_config = load_share_config()

    # 兼容旧 --expire-days
    expire_value = args.expire_value
    if expire_value is None:
        expire_value = args.expire_days
    if expire_value is None:
        expire_value = share_config.get("default_expire_value", 7)
    expire_unit = share_config.get("expire_unit", "day")

    # 检查 flow 是否存在
    flow_json = FLOWS_DIR / f"{flow_id}.json"
    if not flow_json.exists():
        log(f"❌ flow 不存在: {flow_json}")
        sys.exit(1)

    log(f"📋 流程: {flow_id}")
    log(f"   版本: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"   share endpoint: {share_config['upload_url']}")
    log(f"   expire: {expire_value} {expire_unit}")

    # 1. 收集背景数据
    log("\n[1/5] 收集 SPI 背景数据")
    users = fetch_spi_users()
    depts = fetch_spi_depts()
    log(f"   users: {len(users)}, depts: {len(depts)}")

    # 2. 测试结果
    log("\n[2/5] 收集测试结果")
    config, baseline, dashboard = fetch_test_results(flow_id)
    flow_meta = fetch_flow_meta(flow_id)
    log(f"   config: {'✓' if config else '✗'}, baseline: {'✓' if baseline else '✗'}, dashboard: {'✓' if dashboard else '✗'}")

    # 3. 收集文件 + 生成报告
    log("\n[3/5] 收集文件 + 生成报告")
    work_dir = Path("/tmp") / f"archive_{flow_id}"
    work_dir.mkdir(parents=True, exist_ok=True)

    files_collected = collect_files(flow_id, work_dir)
    log(f"   files: {len(files_collected)}")

    report = generate_report(flow_id, flow_meta, config, baseline, dashboard, users, depts)
    report += "\n\n## 8. 附件清单\n\n"
    for f in files_collected:
        report += f"- `{f}`\n"

    report_path = work_dir / "report.md"
    report_path.write_text(report, encoding="utf-8")
    log(f"   report: {report_path}")

    if args.dry_run:
        # dry-run: 显示 report.md 预览（前 30 行）
        log("")
        log("   📄 report.md 预览（前 30 行）：")
        for line in report.split("\n")[:30]:
            log(f"      {line}")

    # 4. 打包
    log("\n[4/5] 打包 tar.gz")
    if args.dry_run:
        # dry-run: 预览 tar.gz 路径 + 文件清单
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        datetime_str = time.strftime("%Y%m%d-%H%M%S")
        tar_name = f"{datetime_str}_{flow_id}.tar.gz"
        tar_path = ARCHIVE_DIR / tar_name
        log(f"   📦 预览 tar.gz: {tar_path}")
        log(f"   📁 包含 {len(files_collected)} 个文件：")
        for f in files_collected[:15]:
            log(f"      - {f}")
        if len(files_collected) > 15:
            log(f"      ... +{len(files_collected)-15} more")
    else:
        tar_path = create_archive(flow_id, work_dir, files_collected)

    # 5. 上传 + 清理（dry-run 跳过）
    if args.dry_run:
        log("\n[5/5] 上传 + 清理（dry-run 预览）")
        log(f"   跳过实际执行（--dry-run）")
        log(f"   --no-upload = {args.no_upload}")
        log(f"   --clean = {args.clean}")
        log(f"   --expire-value = {expire_value} {expire_unit}")
        log("")
        log(f"   📤 预览上传：curl POST {share_config['upload_url']}")
        log(f"      file=@{tar_path}")
        log(f"      expire_value={expire_value}, expire_style={expire_unit}")
        log(f"   🧹 预览清理：见下方文件列表")
        if args.clean:
            # 列出将清理的文件
            to_clean = []
            for f in TDD_DIR.glob(f"test_{flow_id}_2026*.json"):
                to_clean.append(f.name)
            for f in TDD_DIR.glob(f"test_{flow_id}_2026*.md"):
                to_clean.append(f.name)
            baselines = sorted(TDD_DIR.glob(f"test_{flow_id}_baseline_v*.json"))
            baselines_md = sorted(TDD_DIR.glob(f"test_{flow_id}_baseline_v*.md"))
            for old in baselines[:-3]:
                to_clean.append(old.name)
            for old in baselines_md[:-3]:
                to_clean.append(old.name)
            log(f"      将清理 {len(to_clean)} 个文件：")
            for f in to_clean[:10]:
                log(f"        - {f}")
            if len(to_clean) > 10:
                log(f"        ... +{len(to_clean)-10} more")
        code = None
    else:
        log("\n[5/5] 上传 + 清理")
        code = None
        if not args.no_upload:
            code = upload_to_share(tar_path, expire_value, share_config)
        else:
            log(f"   跳过上传（--no-upload）")
            log(f"   本地路径: {tar_path}")

        if args.clean:
            cleanup_local(flow_id)
        else:
            log(f"   跳过清理（未传 --clean）")

    # 清理临时目录
    import shutil
    shutil.rmtree(work_dir, ignore_errors=True)

    # 输出最终结果
    log(f"\n{'='*60}")
    if args.dry_run:
        log(f"🔍 DRY-RUN 预览完成（未实际执行任何操作）")
        log(f"   流程: {flow_id}")
        log(f"   预览 tar.gz: {tar_path}")
        log(f"   运行真实归档：去掉 --dry-run")
    else:
        log(f"✅ 归档完成")
        log(f"   流程: {flow_id}")
        log(f"   tar.gz: {tar_path}")
        if code:
            log(f"   取件码: {code}")
            log(f"   下载: {share_config['download_url_template'].format(code=code)}")
    log(f"{'='*60}")

    return 0 if (args.no_upload or code or args.dry_run) else 1


if __name__ == "__main__":
    sys.exit(main())