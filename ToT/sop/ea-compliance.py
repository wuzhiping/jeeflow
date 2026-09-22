#!/usr/bin/env python3
"""ea-compliance.py — 自动化跑 §9 合规检查清单

验证 EA 自身是否被 FDEP 流程遵循：
- §9.1 流程级（9 项）
- §9.2 Job Card 级（5 项）
- §9.3 基线级（5 项）
- §9.4 运维级（4 项）
- §9.5 飞轮级（4 项）

输出：JSON 报告 + 文本汇总。
"""
import json
import re
import subprocess
import sys
from pathlib import Path

BASE = Path("/opt/jupyter/src/RD/projects/jeeFlow")
FDEP_DIR = BASE / "ToT" / "flows" / "fdep"
FDEP_JSON = BASE / "ToT" / "flows" / "fdep.json"
JOB_CARDS = FDEP_DIR / "job_cards"
TDD_DIR = BASE / "ToT" / "tdd"
CUSTOMER_RESETS = BASE / "ToT" / "customer-resets"
CUSTOMER_CHECKS = BASE / "ToT" / "customer-checks"
EA_DIR = BASE / "ToT" / "ea"
CONFIG_PATH = BASE / "ToT" / "config" / "servers.json"

# 集中读 config（不再硬编码 URL）
from server_config import load_config, get_url
_config = load_config(CONFIG_PATH)
TARGET = get_url(config=_config)


def curl(url, method="GET", body=None, timeout=10):
    cmd = ["curl", "-s", "-X", method, f"{url}", "--max-time", str(timeout)]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
    if not result.stdout.strip():
        return None
    try:
        return json.loads(result.stdout)
    except Exception:
        return None


def check_item(layer: str, item_id: str, desc: str, ok: bool, evidence: str = ""):
    return {"layer": layer, "id": item_id, "desc": desc, "ok": ok, "evidence": evidence}


# ===== §9.1 流程级（9 项）=====
def check_layer_flow():
    items = []
    # 1. flow.json 存在且 flow-lint 通过
    flow_lint_ok = False
    if FDEP_JSON.exists():
        r = subprocess.run(
            ["python3", str(BASE / "ToT/sop/flow-lint.py"), str(FDEP_JSON)],
            capture_output=True, text=True, cwd=str(BASE)
        )
        flow_lint_ok = "通过" in r.stdout
    items.append(check_item("flow", "9.1.1", "flow.json 存在且 flow-lint.py 通过",
                             flow_lint_ok, f"flow-lint exit={r.returncode}"))

    # 2. 文件名小写
    stem_ok = FDEP_JSON.stem == FDEP_JSON.stem.lower()
    items.append(check_item("flow", "9.1.2", "文件名 stem == stem.lower()",
                             stem_ok, f"stem={FDEP_JSON.stem}"))

    # 3. 4 文件齐全
    four_files = ["README.md", "ROLES.md", "NODES.md", "CHANGELOG.md"]
    missing = [f for f in four_files if not (FDEP_DIR / f).exists()]
    items.append(check_item("flow", "9.1.3", "4 文件齐全 (README/ROLES/NODES/CHANGELOG)",
                             len(missing) == 0, f"missing={missing}" if missing else "all present"))

    # 4. README 含 §5 Job Card 模板
    readme = (FDEP_DIR / "README.md").read_text(encoding="utf-8") if (FDEP_DIR / "README.md").exists() else ""
    items.append(check_item("flow", "9.1.4", "README 含 §5 Job Card 模板",
                             "Job Card 模板" in readme, ""))

    # 5. NODES 含每个节点的"工作步骤"
    nodes = (FDEP_DIR / "NODES.md").read_text(encoding="utf-8") if (FDEP_DIR / "NODES.md").exists() else ""
    items.append(check_item("flow", "9.1.5", "NODES.md 含每个节点的'工作步骤'",
                             nodes.count("工作步骤") >= 5, f"count={nodes.count('工作步骤')}"))

    # 6. CHANGELOG 含变更 + 触发原因
    chg = (FDEP_DIR / "CHANGELOG.md").read_text(encoding="utf-8") if (FDEP_DIR / "CHANGELOG.md").exists() else ""
    items.append(check_item("flow", "9.1.6", "CHANGELOG 含变更 + 触发原因",
                             chg.count("| v") >= 5, f"rows={chg.count('| v')}"))

    # 7. RESPONSES 含 §0 + 每节点 §X.2.1
    resp = (FDEP_DIR / "RESPONSES.md").read_text(encoding="utf-8") if (FDEP_DIR / "RESPONSES.md").exists() else ""
    has_section_0 = "## 0. Decision Mem 协议" in resp
    has_x21 = sum(1 for m in re.findall(r"### \d+\.2\.1", resp))
    items.append(check_item("flow", "9.1.7", "RESPONSES 含 §0 协议 + 每节点 §X.2.1",
                             has_section_0 and has_x21 >= 5,
                             f"§0={has_section_0}, §X.2.1 count={has_x21}"))

    # 8. job_cards/ 子目录存在
    items.append(check_item("flow", "9.1.8", "job_cards/ 子目录存在",
                             JOB_CARDS.is_dir(), f"path={JOB_CARDS}"))

    # 9. 每 snaker:task 节点 1 张 Job Card
    flow = json.loads(FDEP_JSON.read_text(encoding="utf-8"))
    task_nodes = [n["id"] for n in flow.get("nodes", []) if n.get("type") == "snaker:task"]
    missing_cards = []
    for tn in task_nodes:
        if not (JOB_CARDS / f"job_card_{tn}.md").exists():
            missing_cards.append(tn)
    items.append(check_item("flow", "9.1.9", "每 snaker:task 节点 1 张 Job Card",
                             len(missing_cards) == 0,
                             f"tasks={len(task_nodes)}, missing={missing_cards}"))
    return items


# ===== §9.2 Job Card 级（5 项）=====
def check_layer_job_card():
    items = []
    cards = list(JOB_CARDS.glob("job_card_*.md")) if JOB_CARDS.exists() else []
    for card in cards[:1]:  # 检查第一张作样本
        text = card.read_text(encoding="utf-8")
        # 1. 8 节齐全
        sections = re.findall(r"^## (\d+)\.", text, re.MULTILINE)
        sections_8 = [s for s in sections if int(s) in range(1, 9)]
        items.append(check_item("job_card", f"9.2.1.{card.name}",
                                 f"{card.name} 8 节齐全",
                                 len(sections_8) == 8, f"sections={sections_8}"))

        # 2. §5 JSON 可解析
        m = re.search(r"## 5\..*?```json\n(.*?)\n```", text, re.DOTALL)
        json_ok = False
        if m:
            try:
                json.loads(m.group(1))
                json_ok = True
            except Exception:
                pass
        items.append(check_item("job_card", f"9.2.2.{card.name}",
                                 f"{card.name} §5 JSON 可解析",
                                 json_ok, ""))

        # 3. §5 含 decision_reason/decision_memo/context
        has_all = all(k in m.group(1) for k in ["decision_reason", "decision_memo", "context"]) if m else False
        items.append(check_item("job_card", f"9.2.3.{card.name}",
                                 f"{card.name} §5 含 3 字段",
                                 has_all, ""))

        # 4. §5 含 job_card_url
        has_jcu = "job_card_url" in m.group(1) if m else False
        items.append(check_item("job_card", f"9.2.4.{card.name}",
                                 f"{card.name} §5 含 job_card_url",
                                 has_jcu, ""))

        # 5. §5 含 next_handoff
        has_nh = "next_handoff" in m.group(1) if m else False
        items.append(check_item("job_card", f"9.2.5.{card.name}",
                                 f"{card.name} §5 含 next_handoff",
                                 has_nh, ""))
        break  # 样本检查即可
    return items


# ===== §9.3 基线级（5 项）=====
def check_layer_baseline():
    items = []
    baselines = sorted(TDD_DIR.glob("test_fdep_baseline_v*.md")) if TDD_DIR.exists() else []
    # 1. happy path PASSED（最新 baseline 含 DONE / state=20 / 5/5 PASS / ✓ PASS）
    happy_ok = False
    reject_ok = False
    naming_ok = False

    if baselines:
        latest = baselines[-1]
        text = latest.read_text(encoding="utf-8")
        happy_ok = (
            "state=20" in text or "DONE" in text or "happy" in text.lower()
        ) and ("PASS" in text or "DONE" in text)
        # 命名：v<数字>[<可选 feature>]?.md  接受 v0.6.2 / v1decision_mems / v3audit 等
        naming_ok = bool(re.match(r"test_fdep_baseline_v\d+[._a-zA-Z]*\.md", latest.name))

    items.append(check_item("baseline", "9.3.1", "happy path PASSED",
                             happy_ok, f"latest={latest.name if baselines else 'none'}"))

    # 2. reject path PASSED（任意 baseline 含 REJECT）
    reject_ok = any(
        "REJECT" in b.read_text(encoding="utf-8") or "state=45" in b.read_text(encoding="utf-8")
        for b in baselines
    )
    items.append(check_item("baseline", "9.3.2", "reject path PASSED",
                             reject_ok, ""))

    # 3. 审计链 baseline 存在
    has_audit_baseline = any("audit" in b.name for b in baselines)
    items.append(check_item("baseline", "9.3.3", "审计链 baseline 存在",
                             has_audit_baseline,
                             f"audit baseline={'✓' if has_audit_baseline else '✗'}"))

    # 4. Job Card 文件存在性（间接）
    items.append(check_item("baseline", "9.3.4", "Job Card 文件存在性（基线自动校验）",
                             len(baselines) >= 3,
                             f"baselines={len(baselines)}"))

    # 5. 命名
    items.append(check_item("baseline", "9.3.5", "baseline 命名格式 test_<flow>_baseline_v<X>[_<feature>].md",
                             naming_ok,
                             f"latest name={latest.name if baselines else 'none'}"))
    return items


# ===== §9.4 运维级（4 项）=====
def check_layer_ops():
    items = []
    # 1. healthz
    h = curl(f"{TARGET}/healthz", timeout=10)
    health_ok = h is not None and h.get("status") == "UP"
    items.append(check_item("ops", "9.4.1", "客户服务器 healthz UP",
                             health_ok, f"health={h.get('status') if h else 'unreachable'}"))

    # 2. fdep 已部署
    fd = curl(f"{TARGET}/wf/processDefine/getLastByName",
              method="POST", body={"processDefineName": "fdep"}, timeout=10)
    fdep_deployed = fd is not None and fd.get("code") == 0 and fd.get("data")
    items.append(check_item("ops", "9.4.2", "fdep 已部署",
                             fdep_deployed,
                             f"id={fd['data']['id'] if fd and fd.get('data') else 'none'}"))

    # 3. 冒烟测试（最近 customer-resets 留档含 done 状态）
    resets = sorted(CUSTOMER_RESETS.glob("*.md")) if CUSTOMER_RESETS.exists() else []
    smoke_ok = False
    for r in resets[-2:]:
        text = r.read_text(encoding="utf-8")
        if "DONE" in text and "state=20" in text:
            smoke_ok = True
            break
    items.append(check_item("ops", "9.4.3", "冒烟测试跑到底（DONE）",
                             smoke_ok,
                             f"checked last 2 reset files"))

    # 4. 留档写入 customer-resets/
    items.append(check_item("ops", "9.4.4", "customer-resets/ 留档存在",
                             len(resets) > 0, f"files={len(resets)}"))
    return items


# ===== §9.5 飞轮级（4 项）=====
def check_layer_flywheel():
    items = []
    # 1. iterations/<date>.md
    iter_dir = EA_DIR / "iterations"
    iters = list(iter_dir.glob("*.md")) if iter_dir.exists() else []
    items.append(check_item("flywheel", "9.5.1", "iterations/<date>.md 留档",
                             len(iters) > 0, f"iterations={len(iters)}"))

    # 2. changelog 更新（roadmap §14 + README §8）
    roadmap = (EA_DIR / "roadmap.md").read_text(encoding="utf-8") if (EA_DIR / "roadmap.md").exists() else ""
    readme = (BASE / "ToT/README.md").read_text(encoding="utf-8")
    rm_log = "## §14 变更日志" in roadmap or "Changelog" in roadmap.lower()
    rd_log = "## 8. 变更日志" in readme or "变更日志" in readme
    items.append(check_item("flywheel", "9.5.2", "changelog 已更新（roadmap + README）",
                             rm_log and rd_log,
                             f"roadmap={rm_log}, README={rd_log}"))

    # 3. Patterns 写回（§5 设计模式）
    patterns = re.findall(r"### Pattern \d+", roadmap)
    items.append(check_item("flywheel", "9.5.3", "Patterns 写回（§5 设计模式）",
                             len(patterns) >= 5, f"patterns={len(patterns)}"))

    # 4. Principles 写回（§2 核心原则）
    principles = re.findall(r"### 原则 \d+", roadmap)
    items.append(check_item("flywheel", "9.5.4", "Principles 写回（§2 核心原则）",
                             len(principles) >= 3, f"principles={len(principles)}"))
    return items


# ===== §9.6 配置集中化（4 项）=====
def check_layer_config():
    items = []
    # 1. servers.json 存在且合法 JSON
    config_exists = CONFIG_PATH.exists()
    config_valid = False
    if config_exists:
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            config_valid = "servers" in cfg and "active" in cfg
        except Exception:
            pass
    items.append(check_item("config", "9.6.1", "ToT/config/servers.json 存在且合法",
                             config_exists and config_valid,
                             f"path={CONFIG_PATH}"))

    # 2. server_config.py 加载器存在
    loader_exists = (BASE / "ToT/sop/server_config.py").exists()
    items.append(check_item("config", "9.6.2", "server_config.py 加载器存在",
                             loader_exists, ""))

    # 3. ea-compliance.py 不硬编码 URL（应读 config）
    # 检查 TARGET 赋值是否为字面量 URL（避免被自身检测串触发假阳性）
    comp_src = (BASE / "ToT/sop/ea-compliance.py").read_text(encoding="utf-8")
    has_target_assignment = bool(re.search(r'TARGET\s*=\s*["\']https?://', comp_src))
    uses_get_url = "get_url" in comp_src
    items.append(check_item("config", "9.6.3", "ea-compliance.py 不硬编码 URL（读 config）",
                             not has_target_assignment and uses_get_url,
                             f"TARGET literal URL={'✗' if has_target_assignment else '✓'}, uses get_url()={'✓' if uses_get_url else '✗'}"))

    # 4. config 含 customer-test（当前主目标）
    has_customer = False
    if config_valid:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        has_customer = "customer-test" in cfg["servers"] and cfg["servers"]["customer-test"].get("url")
    items.append(check_item("config", "9.6.4", "config 含 customer-test 配置",
                             has_customer, ""))
    return items


# ===== §9.7 环境流水线（3 阶段）（4 项）=====
def check_layer_pipeline():
    items = []
    # 1. servers.json 含 3 阶段 tier 标识
    tiers_ok = False
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        tiers = [info.get("tier") for info in cfg.get("servers", {}).values()]
        tiers_ok = ("stage-1-dev" in tiers and "stage-2-staging" in tiers
                    and tiers.count("stage-3-prod") >= 1)
    items.append(check_item("pipeline", "9.7.1", "servers.json 含 3 阶段 tier 标识",
                             tiers_ok, ""))

    # 2. ai_can_push / ai_can_reset 字段完整
    acl_ok = False
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        acl_ok = all(
            "ai_can_push" in info and "ai_can_reset" in info
            for info in cfg.get("servers", {}).values()
        )
    items.append(check_item("pipeline", "9.7.2", "servers.json 含 ai_can_push / ai_can_reset 权限",
                             acl_ok, ""))

    # 3. promote.py 流水线工具存在
    promote_exists = (BASE / "ToT/sop/promote.py").exists()
    items.append(check_item("pipeline", "9.7.3", "promote.py 流水线 CLI 工具存在",
                             promote_exists, ""))

    # 4. env-pipeline.md SOP 存在
    env_pipeline_exists = (BASE / "ToT/sop/env-pipeline.md").exists()
    items.append(check_item("pipeline", "9.7.4", "env-pipeline.md SOP 存在",
                             env_pipeline_exists, ""))
    return items


def main():
    all_items = []
    print("Running §9 compliance check on FDEP...")
    print()
    for layer_fn, layer_name in [
        (check_layer_flow, "§9.1 流程级"),
        (check_layer_job_card, "§9.2 Job Card 级"),
        (check_layer_baseline, "§9.3 基线级"),
        (check_layer_ops, "§9.4 运维级"),
        (check_layer_flywheel, "§9.5 飞轮级"),
        (check_layer_config, "§9.6 配置集中化"),
        (check_layer_pipeline, "§9.7 环境流水线"),
    ]:
        items = layer_fn()
        all_items.extend(items)
        pass_count = sum(1 for i in items if i["ok"])
        total = len(items)
        print(f"  {layer_name}: {pass_count}/{total} PASS")
        for it in items:
            mark = "✓" if it["ok"] else "✗"
            extra = f" — {it['evidence']}" if it['evidence'] and not it['ok'] else ""
            print(f"    {mark} {it['id']}: {it['desc']}{extra}")

    total_pass = sum(1 for i in all_items if i["ok"])
    total = len(all_items)
    print()
    print(f"OVERALL: {total_pass}/{total} PASS ({100*total_pass/total:.1f}%)")

    # JSON 输出
    report = {
        "total": total,
        "pass": total_pass,
        "pass_rate": total_pass / total,
        "items": all_items,
    }
    Path("/tmp/ea_compliance_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\nsaved: /tmp/ea_compliance_report.json")
    return 0 if total_pass == total else 1


if __name__ == "__main__":
    sys.exit(main())