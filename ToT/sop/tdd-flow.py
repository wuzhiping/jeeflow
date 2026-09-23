#!/usr/bin/env python3
"""tdd-flow.py — 流程 JSON 引擎实跑 TDD 脚本

用途：把 flow JSON 部署到 jeeFlow memory engine，逐 stage 执行并记录完整状态。
依据：ToT/sop/tdd-flow.md

用法：
    # 1. 默认：跑 happy + reject（兼容老用法）
    python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json
    python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json --spi dev --operator u_fdp_pm

    # 2. 加全局 variable（透传到所有 path 的 startAndExecute）
    python3 ToT/sop/tdd-flow.py ToT/flows/invoice-approval.json \
        --variable '{"amount": 500, "purpose": "办公"}'

    # 3. 多 scenario（完全自定义，每个 name + variable，替代 happy/reject）
    python3 ToT/sop/tdd-flow.py ToT/flows/invoice-approval.json \
        --scenarios "small:{\"amount\":500}|big:{\"amount\":8000}"

    # 4. 兼容：仍可用 --no-reject 跳过 reject
    python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json --no-reject

输出（按时间戳，自动写入 ToT/tdd/）：
    test_<flow-name>_<YYYYMMDDHHMMSS>.md   人类可读摘要
    test_<flow-name>_<YYYYMMDDHHMMSS>.json 原始引擎响应（machine-readable）

退出码：
    0 - 所有 path PASSED
    1 - 至少一个 path FAILED
    2 - 部分 PASSED（warning）

历史：
- v0.1 (2026-09-22)：由 v0.6.2 fdep.json 实跑沉淀而来
- v0.2 (2026-09-23 Iter#10)：加 --variable + --scenarios 支持（驱动 invoice-approval 验证）
"""
import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VENDOR = PROJECT_ROOT / "vendor"
sys.path.insert(0, str(VENDOR))
sys.path.insert(0, str(PROJECT_ROOT))


def log(msg: str, fp=None):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line)
    if fp:
        fp.write(line + "\n")


async def setup_engine():
    """初始化 jeeFlow memory engine（与 main.py 一致）"""
    from main_common import (
        SnowflakeIDGen, SimpleExprEvaluator, RatioCapableEngine,
        build_ic_registry, build_custom_handlers, build_decision_handlers,
        apply_extensions, install_resolve_actors_wrapper,
    )
    from jeeflow import MemoryRepository, JeeflowFacade, register_builtin_assignments, HandlerRegistry
    from jeeflow.memory import MemoryExtRepository
    from spi import SimpleUserProvider, SpiOrgUserProvider

    repo = MemoryRepository()
    ext_repo = MemoryExtRepository()
    idgen = SnowflakeIDGen()
    user_prov = SimpleUserProvider()
    org_prov = SpiOrgUserProvider()
    engine = RatioCapableEngine(repo, user_prov, idgen, SimpleExprEvaluator(), org_prov)
    registry = HandlerRegistry()
    register_builtin_assignments(registry, user_prov, org_prov)
    apply_extensions(engine, registry, build_ic_registry(), build_custom_handlers(), build_decision_handlers())
    engine.set_ext_repo(ext_repo)
    install_resolve_actors_wrapper(engine)
    facade = JeeflowFacade(engine, repo, ext_repo, user_search=None, org_prov=org_prov)
    from main_meta import build_meta_reader
    facade.set_meta_reader(build_meta_reader(repo))
    return facade


async def deploy(facade, flow_path: Path, operator: str):
    content = flow_path.read_text(encoding="utf-8")
    resp = await facade.flow("processDefine/deploy", {
        "content": content,
        "operator": operator,
        "name": flow_path.stem,
    })
    if resp.get("code") != 0:
        raise RuntimeError(f"deploy 失败: {resp}")
    return resp["data"]["processDefineId"]


async def inspect(facade, iid):
    detail = await facade.flow("processInstance/detail", {"id": iid})
    data = detail.get("data") or {}
    state = data.get("state")
    state_name = state.name if hasattr(state, "name") else state
    tasks_info = []
    for t in data.get("tasks", []):
        tstate = t.get("taskState")
        tasks_info.append({
            "name": t["taskName"],
            "displayName": t.get("displayName"),
            "state": tstate.name if hasattr(tstate, "name") else tstate,
            "operator": t.get("operator") or None,
            "actors": t.get("taskActorIdList"),
            "id": t.get("id"),
            "finishTime": str(t.get("finishTime")) if t.get("finishTime") else None,
        })
    return {
        "state": state_name,
        "state_code": state,
        "tasks": tasks_info,
        "active_names": [t["taskName"] for t in data.get("activeTaskList", [])],
        "variables": data.get("variables", {}),
    }


async def run_path(facade, define_id, operator, submit_type=1, max_steps=20, label="happy", variable=None, top_vars=None, comment=None):
    """执行一个 instance 直到 DONE / REJECT / 卡住

    参数:
      variable: dict | None  — 透传给 startAndExecute 的 variable（如 {"amount": 500}）
      top_vars: dict | None  — 顶级变量（不进 variable 嵌套），用于 tf_* actor resolver
      comment: str | None    — 驳回时传给 execute（存入 instance.variables.comment + task.variables._comments）
      submit_type: int — 各 task 默认 submitType，submit task 强制用 1
                         驳回场景（submitType=5）只在 approve 第一次执行时用，
                         之后再次到 approve 时改用 1（避免循环）
    """
    start_args = {
        "processDefineId": define_id,
        "operator": operator,
    }
    if variable:
        start_args["variable"] = variable
    if top_vars:
        # 顶级变量（用于 actor resolver 解析 tf_*）
        for k, v in top_vars.items():
            start_args[k] = v
    start = await facade.flow("processDefine/startAndExecute", start_args)
    if start.get("code") != 0:
        return None, f"startAndExecute 失败: {start}"

    iid = start["data"]["processInstanceId"]
    log(f"  [{label}] instance={iid} variable={variable} submitType={submit_type}", None)

    steps = []
    # track 每个 task 已执行次数（防止驳回后 approve 又用 5 造成循环）
    task_exec_count = {}
    # track RE_APPLY 是否已应用（防循环）
    resurrect_attempted = False
    for step_idx in range(max_steps):
        snap = await inspect(facade, iid)
        steps.append({"step": step_idx, "snapshot": snap})

        if snap["state"] in ("DONE", "REJECT"):
            log(f"  [{label}] 终止 state={snap['state']} ({snap['state_code']})", None)
            break

        if snap["state"] not in ("DOING",):
            log(f"  [{label}] 异常 state={snap['state']} ({snap['state_code']}), 停止", None)
            break

        # 找 instance 的 active task
        snap = await inspect(facade, iid)
        active_tasks = [t for t in snap["tasks"] if t["state"] == "DOING"]

        if not active_tasks:
            log(f"  [{label}] 无 active task, 停止", None)
            break

        t = active_tasks[0]
        task_name = t["name"]
        task_exec_count[task_name] = task_exec_count.get(task_name, 0) + 1

        # 决定 submitType：
        # - submit task 永远用 1（提交不能驳回自己）
        # - scenario.submit_type=2 (REJECT)：第一次到任何非 submit task 用 2（流程 REJECT）
        # - scenario.submit_type=5 (RE_APPLY)：第一次到任何非 submit task 用 5（跳回首个 task）
        #   - 但 resurrect_attempted=True 后都改用 1（防循环）
        # - 否则：用 1（默认通过）
        if task_name == "submit":
            exec_submit_type = 1
        elif submit_type == 2 and task_exec_count[task_name] == 1:
            exec_submit_type = 2  # 第一次到非 submit task REJECT 整个流程
        elif submit_type == 5 and task_exec_count[task_name] == 1 and not resurrect_attempted:
            exec_submit_type = 5  # 第一次到非 submit task RE_APPLY（跳回首个 task）
        else:
            exec_submit_type = 1  # 之后默认通过
        # 标记：scenario 提交类型已应用一次（防 RE_APPLY 循环）
        if exec_submit_type in (2, 5) and task_name != "submit":
            resurrect_attempted = True

        log(f"  [{label}] step {step_idx + 1}: execute {task_name} (submitType={exec_submit_type})", None)

        # 用 flow.auto 绕过 actor 校验
        exec_args = {
            "processTaskId": t["id"],
            "operator": "flow.auto",
            "submitType": exec_submit_type,
        }
        # v4 audit：每次 execute 都传 decision_reason / decision_memo / job_card_url
        exec_args["decision_reason"] = f"{task_name} 通过"
        exec_args["decision_memo"] = f"{task_name} 在 {label} scenario 执行"
        exec_args[f"{task_name}_job_card_url"] = (
            f"ToT/flows/<flow>/job_cards/{task_name}.md"
        )
        # 驳回场景额外传 comment
        if exec_submit_type in (2, 5) and comment:
            exec_args["comment"] = comment
        exec_resp = await facade.flow("processTask/execute", exec_args)
        steps.append({"step": step_idx, "execute": {
            "task_name": t.get("taskName") or t.get("name"),
            "submit_type": submit_type,
            "resp_code": exec_resp.get("code"),
            "resp_msg": exec_resp.get("msg", ""),
        }})
        if exec_resp.get("code") != 0:
            log(f"  [{label}] execute 失败: {exec_resp}", None)
            break

    final = await inspect(facade, iid)
    # v4 audit：检查每 task 的 job_card_url（如果 execute 传了）
    audit_summary = []
    for t in final["tasks"]:
        # t 是 inspect 返回的 dict（含 name / actors / state）
        # 看 instance.variables.task_<name>_job_card_url 等字段
        job_card_url = final["variables"].get(f"{t['name']}_job_card_url", "")
        audit_summary.append({
            "task": t["name"],
            "state": t["state"],
            "actors": t.get("actors"),
            "job_card_url": job_card_url,
        })

    return {
        "instance_id": iid,
        "steps": steps,
        "final": final,
        "variable": variable,
        "top_vars": top_vars,
        "comment": comment,
        "audit": audit_summary,  # v4 新增：每 task 审计摘要
    }, None


def load_tests_file(tests_file_path: str, flow_path: Path, args):
    """加载 tests.json 集中管理文件，覆盖 args 的对应字段

    tests.json 格式：
    {
      "version": "1.0",
      "flows": {
        "fdep": {
          "scenarios": "happy:{}|reject:{}:2|resurrect:{}:5",
          "operator": "u_fdp_pm",
          "top_vars": {},
          "baseline": "test_fdep_baseline_v0_5_*.json"
        },
        "invoice-approval": {
          "scenarios": "small:{...}|big:{...}|reject:{...}:5",
          "top_vars": {"tf_manager": "u_bob", "tf_treasurer": "u_carol"},
          "operator": "u_fdp_pm",
          "baseline": "test_invoice-approval_baseline_v0_*.json"
        }
      }
    }
    """
    path = Path(tests_file_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    if not path.exists():
        print(f"❌ tests-file 不存在: {path}")
        sys.exit(1)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"❌ tests-file JSON 解析失败: {e}")
        sys.exit(1)

    flow_name = flow_path.stem
    flow_cfg = data.get("flows", {}).get(flow_name)
    if not flow_cfg:
        print(f"❌ tests-file 中无 flow '{flow_name}' 配置")
        print(f"   可用 flows: {list(data.get('flows', {}).keys())}")
        sys.exit(1)

    print(f"📋 加载 tests-file: {path.relative_to(PROJECT_ROOT)}")
    print(f"   flow: {flow_name}")
    print(f"   scenarios: {flow_cfg.get('scenarios', '(none)')}")
    if flow_cfg.get("top_vars"):
        print(f"   top_vars: {flow_cfg['top_vars']}")
    if flow_cfg.get("operator"):
        print(f"   operator: {flow_cfg['operator']}")
    if flow_cfg.get("baseline"):
        print(f"   baseline: {flow_cfg['baseline']}")

    # 覆盖 args（仅当 tests-file 中指定）
    if "scenarios" in flow_cfg:
        args.scenarios = flow_cfg["scenarios"]
    if "operator" in flow_cfg:
        args.operator = flow_cfg["operator"]
    if "top_vars" in flow_cfg:
        # 转成 JSON 字符串，因为 args.top_vars 是字符串
        args.top_vars = json.dumps(flow_cfg["top_vars"])
    if "variable" in flow_cfg:
        args.variable = json.dumps(flow_cfg["variable"])
    if "baseline" in flow_cfg:
        # 支持 glob 模式（如 test_*_v0_5_*.json）
        baseline_pattern = flow_cfg["baseline"]
        if "*" in baseline_pattern:
            import glob as _glob
            candidates = sorted(_glob.glob(str(PROJECT_ROOT / "ToT/tdd" / baseline_pattern)))
            if candidates:
                # 优先选有 _baseline_meta 的（自动生成的）
                auto_candidates = []
                for c in candidates:
                    try:
                        d = json.loads(Path(c).read_text(encoding="utf-8"))
                        if "_baseline_meta" in d:
                            auto_candidates.append(c)
                    except Exception:
                        pass
                # 如果有自动 baseline，用最新的；否则用任意最新
                if auto_candidates:
                    chosen = auto_candidates[-1]  # 最新自动
                else:
                    chosen = candidates[-1]
                baseline_path = Path(chosen)
                args.compare_baseline = str(baseline_path.relative_to(PROJECT_ROOT))
                print(f"   baseline (glob 解析): {baseline_path.relative_to(PROJECT_ROOT)}")
            else:
                print(f"   ⚠️ baseline glob 模式 '{baseline_pattern}' 未匹配任何文件")
        else:
            args.compare_baseline = baseline_pattern
            print(f"   （将自动对比 baseline: {baseline_pattern}）")


def parse_scenarios(spec: str) -> list:
    """解析 --scenarios 参数：'name1:json1|name2:json2[:submitType][:comment]'

    智能处理 JSON 中的 `:`：
    - 第一个 `:` 是 name 与 json 的分隔符
    - json 部分必须完整 `{...}`，闭合 `}` 后可能有 `:submitType[:comment]`

    返回: [{"name", "variable", "submit_type", "comment"}, ...]
    """
    scenarios = []
    for entry in spec.split("|"):
        entry = entry.strip()
        if not entry:
            continue
        if ":" not in entry:
            raise ValueError(f"scenario 格式错误 '{entry}'，期望 'name:json[:submitType][:comment]'")

        # 第一个 : 分隔 name 和后续
        name, rest = entry.split(":", 1)
        name = name.strip()
        rest = rest.strip()

        # 找 JSON 结束位置（匹配 `}`）
        submit_type = 1
        comment = None
        if rest.endswith("}"):
            json_str = rest
        else:
            # 找最后一个 `}:...` 模式
            depth = 0
            json_end = -1
            in_string = False
            escape = False
            for i, ch in enumerate(rest):
                if escape:
                    escape = False
                    continue
                if ch == "\\":
                    escape = True
                    continue
                if ch == '"':
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        json_end = i
                        break
            if json_end < 0:
                raise ValueError(f"无法解析 JSON 边界 '{rest}'")
            json_str = rest[:json_end + 1]
            after = rest[json_end + 1:].strip()
            if after.startswith(":"):
                # 解析 submitType[:comment]
                parts = after[1:].split(":", 1)
                try:
                    submit_type = int(parts[0].strip())
                except ValueError:
                    raise ValueError(f"submitType 必须是整数 '{parts[0]}'")
                if len(parts) > 1:
                    comment = parts[1].strip()

        var = json.loads(json_str)
        scenarios.append({"name": name, "variable": var, "submit_type": submit_type, "comment": comment})
    return scenarios


def detect_changed_flows(repo_root: Path, since_ref: str = "HEAD") -> set:
    """检测 git 改动过的 flow 文件名集合

    包含 3 类改动：
    1. 工作区改动（git diff HEAD）—— 已 tracked 文件的工作区 vs HEAD
    2. 已 staged 改动（git diff --cached）—— staged vs HEAD
    3. 未追踪文件（git ls-files --others --exclude-standard）—— 新增未 add

    返回改动的 flow 名集合（如 {"fdep", "invoice-approval"}）
    """
    import subprocess
    changed_files = set()
    try:
        # 1. 工作区改动（tracked files modified/deleted）
        r1 = subprocess.run(
            ["git", "diff", "--name-only", since_ref, "--", "ToT/flows/*.json"],
            cwd=repo_root, capture_output=True, text=True, timeout=10,
        )
        if r1.returncode == 0 and r1.stdout.strip():
            changed_files.update(r1.stdout.strip().split("\n"))

        # 2. Staged 改动
        r2 = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--", "ToT/flows/*.json"],
            cwd=repo_root, capture_output=True, text=True, timeout=10,
        )
        if r2.returncode == 0 and r2.stdout.strip():
            changed_files.update(r2.stdout.strip().split("\n"))

        # 3. 未追踪文件（untracked）
        r3 = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", "--", "ToT/flows/"],
            cwd=repo_root, capture_output=True, text=True, timeout=10,
        )
        if r3.returncode == 0 and r3.stdout.strip():
            # 过滤 .json
            for f in r3.stdout.strip().split("\n"):
                if f.endswith(".json"):
                    changed_files.add(f)
    except Exception as e:
        log(f"  ⚠️ git diff 失败: {e}")
        return set()

    # 提取 flow 名（去掉路径和扩展名）
    changed_flows = set()
    for f in changed_files:
        if not f:
            continue
        stem = Path(f).stem
        if stem:
            changed_flows.add(stem)
    return changed_flows


def build_dashboard_entry(flow_name: str, exit_code: int, raw_data: dict, elapsed: float) -> dict:
    """构建单 flow 的 dashboard entry"""
    results = raw_data.get("results", {})
    scenarios_summary = []
    all_ok = True
    passed_scenarios = 0
    for label, r in results.items():
        if not r:
            all_ok = False
            continue
        state = r["final"]["state"]
        task_count = len(r["final"]["tasks"])
        # 找 scenario-level submit_type
        sc = next((s for s in (raw_data.get("scenarios") or []) if s["name"] == label), None)
        scenarios_summary.append({
            "name": label,
            "submit_type": sc.get("submit_type", 1) if sc else 1,
            "state": state,
            "task_count": task_count,
            "actors": list(set(actor for t in r["final"]["tasks"] for actor in (t.get("actors") or []))),
        })
        if state in ("DONE", "REJECT"):
            passed_scenarios += 1
        else:
            all_ok = False

    return {
        "flow_name": flow_name,
        "exit_code": exit_code,
        "elapsed_seconds": round(elapsed, 3),
        "passed": exit_code == 0,
        "scenario_count": len(scenarios_summary),
        "passed_scenarios": passed_scenarios,
        "scenarios": scenarios_summary,
        "static_errors": len(raw_data.get("static_validation", {}).get("errors", [])),
        "engine_errors": len(raw_data.get("engine_validation", {}).get("errors", [])),
        "static_warnings": len(raw_data.get("static_validation", {}).get("warnings", [])),
        "engine_warnings": len(raw_data.get("engine_validation", {}).get("warnings", [])),
    }


def build_dashboard(entries: list, total_elapsed: float) -> dict:
    """构建多 flow 汇总 dashboard"""
    total_flows = len(entries)
    passed_flows = sum(1 for e in entries if e["passed"])
    failed_flows = total_flows - passed_flows
    total_scenarios = sum(e["scenario_count"] for e in entries)
    passed_scenarios = sum(
        1 for e in entries for s in e["scenarios"] if s["state"] in ("DONE", "REJECT")
    )

    return {
        "version": "1.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "summary": {
            "total_flows": total_flows,
            "passed_flows": passed_flows,
            "failed_flows": failed_flows,
            "total_scenarios": total_scenarios,
            "passed_scenarios": passed_scenarios,
            "all_passed": failed_flows == 0,
        },
        "total_elapsed_seconds": round(total_elapsed, 3),
        "flows": entries,
    }


def render_sparkline(history_for_flow: list, width: int = 120, height: int = 24) -> str:
    """为单个 flow 渲染 SVG sparkline（显示最近 N 次跑的趋势）

    每根柱代表一次跑：
    - 绿色 = 全通过（all_passed）
    - 黄色 = 部分通过
    - 红色 = 全失败
    - 高度 = 通过率（passed/total scenarios）

    参数:
      history_for_flow: list of entry dicts（每个含 scenario_count / passed_scenarios / passed 字段）
    """
    if not history_for_flow:
        return ""

    bar_w = max(4, width // max(len(history_for_flow), 1))
    bars_svg = []
    for i, h in enumerate(history_for_flow):
        total = h.get("scenario_count", 0)
        passed = h.get("passed_scenarios", 0)
        all_passed = h.get("passed", False)
        x = i * bar_w
        if total == 0:
            color = "#ccc"
            bar_h = 2
        elif all_passed:
            color = "#28a745"
            bar_h = height - 4
        else:
            ratio = passed / max(total, 1)
            bar_h = max(2, int((height - 4) * ratio))
            color = "#28a745" if ratio >= 0.8 else "#ffc107" if ratio >= 0.5 else "#dc3545"
        bars_svg.append(
            f'<rect x="{x}" y="{height-bar_h}" width="{bar_w-1}" height="{bar_h}" '
            f'fill="{color}" rx="1"><title>run {i+1}: {passed}/{total}</title></rect>'
        )
    svg = (
        f'<svg width="{width}" height="{height}" '
        f'style="vertical-align: middle;">{"".join(bars_svg)}</svg>'
    )
    return svg


def render_html_dashboard(dashboard: dict, history: list = None, flow_histories: dict = None) -> str:
    """将 dashboard JSON 渲染为人类可读 HTML"""
    s = dashboard["summary"]
    all_passed = s["all_passed"]
    badge_color = "#28a745" if all_passed else "#dc3545"
    badge_text = "✅ ALL PASSED" if all_passed else "❌ FAILED"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>TDD Dashboard · {dashboard['generated_at']}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
       margin: 0; padding: 20px; background: #f5f5f5; color: #333; }}
.container {{ max-width: 1100px; margin: 0 auto; background: white;
            padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
h1 {{ margin-top: 0; color: #333; }}
.badge {{ display: inline-block; padding: 6px 14px; border-radius: 4px;
         color: white; font-weight: bold; background: {badge_color}; }}
.summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 15px; margin: 20px 0; }}
.summary-card {{ background: #f8f9fa; padding: 15px; border-radius: 6px;
                border-left: 4px solid #007bff; }}
.summary-card .label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
.summary-card .value {{ font-size: 28px; font-weight: bold; color: #333; margin-top: 5px; }}
.summary-card.passed {{ border-left-color: #28a745; }}
.summary-card.failed {{ border-left-color: #dc3545; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
th {{ background: #343a40; color: white; padding: 10px; text-align: left;
    font-size: 13px; }}
td {{ padding: 10px; border-bottom: 1px solid #e9ecef; font-size: 13px; }}
tr.failed {{ background: #fff5f5; }}
tr.passed {{ background: #f5fff5; }}
.state-DONE {{ color: #28a745; font-weight: bold; }}
.state-REJECT {{ color: #dc3545; font-weight: bold; }}
.state-DOING {{ color: #ffc107; }}
.footer {{ margin-top: 30px; padding-top: 15px; border-top: 1px solid #e9ecef;
          color: #666; font-size: 12px; }}
.toggle {{ cursor: pointer; user-select: none; }}
.toggle:hover {{ background: #f0f0f0; }}
.details {{ display: none; background: #fafafa; padding: 10px 20px;
          border-left: 3px solid #007bff; margin: 5px 0; font-size: 12px; }}
.details.open {{ display: block; }}
.details code {{ background: #e9ecef; padding: 2px 5px; border-radius: 3px;
              font-family: monospace; }}
.filter-bar {{ margin: 15px 0; padding: 12px; background: #e9ecef;
              border-radius: 6px; display: flex; gap: 10px; align-items: center; }}
.filter-bar button {{ padding: 6px 14px; border: 1px solid #007bff;
                   background: white; color: #007bff; border-radius: 4px;
                   cursor: pointer; font-size: 13px; }}
.filter-bar button:hover {{ background: #007bff; color: white; }}
.filter-bar button.active {{ background: #007bff; color: white; }}
.filter-bar .count {{ color: #666; font-size: 13px; margin-left: auto; }}
tr.hidden {{ display: none; }}
</style>
<script>
function toggleDetails(id) {{
  const el = document.getElementById(id);
  if (el) el.classList.toggle('open');
}}
function filterByDays(days) {{
  const rows = document.querySelectorAll('tr[data-ts]');
  const now = new Date();
  let shown = 0;
  rows.forEach(row => {{
    const ts = new Date(row.dataset.ts);
    const diffDays = (now - ts) / (1000 * 60 * 60 * 24);
    if (days === 0 || diffDays <= days) {{
      row.classList.remove('hidden');
      shown++;
    }} else {{
      row.classList.add('hidden');
    }}
  }});
  document.querySelectorAll('.filter-bar button').forEach(b => b.classList.remove('active'));
  document.getElementById('filter-' + (days || 'all')).classList.add('active');
  document.getElementById('visible-count').textContent = shown + ' / ' + rows.length;
}}
</script>
</head>
<body>
<div class="container">
<h1>TDD Regression Dashboard <span class="badge">{badge_text}</span></h1>
<p>Generated at {dashboard['generated_at']} · Total elapsed: {dashboard['total_elapsed_seconds']}s</p>

<div class="summary">
  <div class="summary-card">
    <div class="label">Total Flows</div>
    <div class="value">{s['total_flows']}</div>
  </div>
  <div class="summary-card passed">
    <div class="label">Passed Flows</div>
    <div class="value">{s['passed_flows']}</div>
  </div>
  <div class="summary-card {'failed' if s['failed_flows'] else 'passed'}">
    <div class="label">Failed Flows</div>
    <div class="value">{s['failed_flows']}</div>
  </div>
  <div class="summary-card">
    <div class="label">Total Scenarios</div>
    <div class="value">{s['total_scenarios']}</div>
  </div>
  <div class="summary-card passed">
    <div class="label">Passed Scenarios</div>
    <div class="value">{s['passed_scenarios']}</div>
  </div>
</div>

<table>
  <thead>
    <tr>
      <th>Flow</th>
      <th>Passed</th>
      <th>Elapsed</th>
      <th>Scenarios</th>
      <th>Errors (static/engine)</th>
      <th>Trend</th>
    </tr>
  </thead>
  <tbody>
"""

    for entry in dashboard["flows"]:
        passed_class = "passed" if entry["passed"] else "failed"
        flow_id = entry["flow_name"].replace("-", "_")
        scenarios_html = "<ul style='margin:0;padding-left:18px;'>"
        for sc in entry["scenarios"]:
            state = sc["state"]
            sc_class = "passed" if state in ("DONE", "REJECT") else "failed"
            scenarios_html += (
                f"<li class='{sc_class}'>"
                f"<span class='state-{state}'>{state}</span> "
                f"<code>{sc['name']}</code> "
                f"(submitType={sc['submit_type']}, tasks={sc['task_count']})"
                f"</li>"
            )
        scenarios_html += "</ul>"
        errors_str = f"{entry['static_errors']} / {entry['engine_errors']}"
        details_html = (
            f"<div class='details' id='details-{flow_id}'>"
            f"<strong>Scenarios 详情：</strong><br>"
            f"<ul>"
        )
        for sc in entry["scenarios"]:
            state = sc["state"]
            details_html += (
                f"<li><code>{sc['name']}</code>: "
                f"submitType={sc['submit_type']}, state=<span class='state-{state}'>{state}</span>, "
                f"tasks={sc['task_count']}, actors={', '.join(sc['actors'])}</li>"
            )
        details_html += "</ul></div>"
        html += f"""    <tr class="{passed_class} toggle" onclick="toggleDetails('details-{flow_id}')">
      <td><strong>{entry['flow_name']} ▼</strong></td>
      <td>{'✅' if entry['passed'] else '❌'}</td>
      <td>{entry['elapsed_seconds']}s</td>
      <td>{scenarios_html}</td>
      <td>{errors_str}</td>
      <td>{render_sparkline(flow_histories.get(entry['flow_name'], [])) if flow_histories else ''}</td>
    </tr>
    <tr><td colspan="6" style="padding:0;">{details_html}</td></tr>
"""

    html += """  </tbody>
</table>
"""

    # 时间趋势（最近 N 次跑）
    if history and len(history) > 0:
        html += f"""
<h2 style="margin-top: 30px;">📈 历史趋势（最近 {len(history)} 次）</h2>
<div class="filter-bar">
  <strong>时间过滤：</strong>
  <button id="filter-1" onclick="filterByDays(1)">最近 1 天</button>
  <button id="filter-7" onclick="filterByDays(7)">最近 7 天</button>
  <button id="filter-30" onclick="filterByDays(30)">最近 30 天</button>
  <button id="filter-all" class="active" onclick="filterByDays(0)">全部</button>
  <span class="count">显示 <span id="visible-count">{len(history)}</span> / {len(history)}</span>
</div>
<table>
  <thead>
    <tr>
      <th>时间</th>
      <th>Flows (P/T)</th>
      <th>Scenarios (P/T)</th>
      <th>总耗时</th>
      <th>状态</th>
    </tr>
  </thead>
  <tbody>
"""
        for h in history:
            ts = h.get("generated_at", "?")
            s = h.get("summary", {})
            total_f = s.get("total_flows", 0)
            passed_f = s.get("passed_flows", 0)
            total_s = s.get("total_scenarios", 0)
            passed_s = s.get("passed_scenarios", 0)
            elapsed = h.get("total_elapsed_seconds", 0)
            all_ok = s.get("all_passed", False)
            mark = "✅" if all_ok else "❌"
            html += f"""    <tr class="{'passed' if all_ok else 'failed'}" data-ts="{ts}">
      <td><code>{ts}</code></td>
      <td>{passed_f}/{total_f}</td>
      <td>{passed_s}/{total_s}</td>
      <td>{elapsed}s</td>
      <td>{mark}</td>
    </tr>
"""
        html += """  </tbody>
</table>
"""

    html += """
<div class="footer">
  TDD Flow Regression · jeeflow EA · v2.32+ · Generated by ToT/sop/tdd-flow.py
</div>
</div>
</body>
</html>"""
    return html


async def run_single_flow(args, flow_path: Path) -> tuple:
    """运行单个 flow，返回 (exit_code, raw_data, elapsed)"""
    start_time = time.time()
    try:
        # 重构：原 main 函数逻辑提取到这里
        exit_code, raw_data = await main_inner(args, flow_path)
    except SystemExit as e:
        exit_code = e.code if isinstance(e.code, int) else 1
        raw_data = {}
    elapsed = time.time() - start_time
    return exit_code, raw_data, elapsed


async def main():
    # 早期解析参数（用于 --all-flows 决策）
    parser = argparse.ArgumentParser(description="TDD 流程 JSON 引擎实跑")
    parser.add_argument("flow_json", nargs="?", help="流程 JSON 文件路径")
    parser.add_argument("--spi", default="dev", help="SPI_FOLDER 环境（默认 dev）")
    parser.add_argument("--operator", default="u_fdp_pm", help="流程发起人/执行人（默认 u_fdp_pm）")
    parser.add_argument("--no-reject", action="store_true", help="只跑 happy path，不跑 reject")
    parser.add_argument("--max-steps", type=int, default=20, help="单 path 最大步数")
    parser.add_argument("--variable", help="全局 variable（JSON 字符串，透传给所有 path）")
    parser.add_argument("--top-vars", help="顶级变量（JSON 字符串，透传到 startAndExecute args 顶级而非 variable 嵌套，用于 tf_* actor resolver）")
    parser.add_argument("--scenarios",
                        help="自定义多 scenario，格式：name1:json1|name2:json2（覆盖默认 happy+reject）")
    parser.add_argument("--save-baseline",
                        action="store_true",
                        help="把本次结果保存为 baseline md（test_<flow>_baseline_v<N>.md）")
    parser.add_argument("--compare-baseline",
                        help="对比历史 baseline JSON（<path>.json 或 test_<flow>_baseline_*.json），输出 diff")
    parser.add_argument("--tests-file", help="tests.json 集中管理文件路径（含多个 flow 的 scenarios）")
    parser.add_argument("--baseline-only", action="store_true",
                        help="只对比 baseline，不实跑引擎（快速 regression 检测）")
    parser.add_argument("--all-flows", action="store_true",
                        help="迭代 tests.json 中所有 flow（仅在传 --tests-file 时有效）")
    parser.add_argument("--only-changed", action="store_true",
                        help="只跑 git 改动过的 flow（需要 git + git diff）")
    parser.add_argument("--report-json", help="输出汇总 dashboard JSON 到指定路径（用于 CI 集成）")
    parser.add_argument("--report-html", help="输出汇总 dashboard HTML 到指定路径（人类可读）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只跑静态校验 + verify_flow，不实跑引擎（CI 快速检查）")
    parser.add_argument("--parallel", type=int, default=1,
                        help="scenarios 并发数（默认 1=串行，N>1 用 asyncio.Semaphore 限流）")
    args = parser.parse_args()

    # --all-flows 模式：迭代 tests.json 中所有 flow
    if args.all_flows:
        if not args.tests_file:
            print("❌ --all-flows 必须配合 --tests-file 使用")
            sys.exit(1)
        return await run_all_flows(args)

    # 单 flow 模式（保留原逻辑）
    return await run_single_flow(args, None)


async def run_all_flows(args):
    """迭代 tests.json 中所有 flow，跑每个 flow + 生成汇总 dashboard"""
    tests_file = Path(args.tests_file)
    if not tests_file.is_absolute():
        tests_file = PROJECT_ROOT / tests_file
    if not tests_file.exists():
        print(f"❌ tests-file 不存在: {tests_file}")
        sys.exit(1)

    data = json.loads(tests_file.read_text(encoding="utf-8"))
    flows_cfg = data.get("flows", {})
    if not flows_cfg:
        print(f"❌ tests-file 中无 flows 配置")
        sys.exit(1)

    mode_label = "BASELINE-ONLY 对比" if args.baseline_only else "实跑 + 对比"
    print(f"🚀 --all-flows 模式：{mode_label} {len(flows_cfg)} 个 flow")
    print(f"   tests-file: {tests_file}")
    print()

    # only-changed 模式：检测 git diff
    if args.only_changed:
        changed = detect_changed_flows(PROJECT_ROOT)
        if changed:
            print(f"🔍 --only-changed: 只跑改动的 flow")
            print(f"   changed flows: {sorted(changed)}")
            flows_cfg = {k: v for k, v in flows_cfg.items() if k in changed}
            if not flows_cfg:
                print(f"   ⚠️ 无匹配的 flow 在 tests.json 中")
                return 0
            print()
        else:
            print(f"   ⚠️ 无 git diff 改动，全部跑")
            print()

    entries = []
    overall_start = time.time()

    for flow_name, flow_cfg in flows_cfg.items():
        flow_json = PROJECT_ROOT / "ToT" / "flows" / f"{flow_name}.json"
        if not flow_json.exists():
            print(f"⚠️  {flow_name}: {flow_json} 不存在，跳过")
            entries.append(build_dashboard_entry(flow_name, 1, {
                "results": {}, "static_validation": {"errors": [f"flow file not found"]},
                "engine_validation": {"errors": []}, "scenarios": [],
            }, 0))
            continue

        print(f"{'='*60}")
        print(f"▶ {flow_name}")
        print(f"{'='*60}")

        # baseline-only 模式：只对比 baseline，不实跑
        if args.baseline_only:
            baseline_pattern = flow_cfg.get("baseline", "")
            if not baseline_pattern:
                print(f"  ⚠️ 无 baseline 配置，跳过")
                entries.append(build_dashboard_entry(flow_name, 1, {
                    "results": {}, "static_validation": {"errors": ["no baseline configured"]},
                    "engine_validation": {"errors": []}, "scenarios": [],
                }, 0))
                continue

            # 找 baseline
            import glob as _glob
            candidates = sorted(_glob.glob(str(PROJECT_ROOT / "ToT/tdd" / baseline_pattern)))
            if not candidates:
                print(f"  ⚠️ baseline '{baseline_pattern}' 未找到")
                entries.append(build_dashboard_entry(flow_name, 1, {
                    "results": {}, "static_validation": {"errors": [f"baseline {baseline_pattern} not found"]},
                    "engine_validation": {"errors": []}, "scenarios": [],
                }, 0))
                continue

            # 用最新 baseline 对比"无 scenarios"（baseline-only 模式：检查 baseline 自身是否完整）
            baseline_path = Path(candidates[-1])
            try:
                baseline_raw = json.loads(baseline_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                print(f"  ❌ baseline JSON 解析失败: {e}")
                entries.append(build_dashboard_entry(flow_name, 1, {
                    "results": {}, "static_validation": {"errors": [str(e)]},
                    "engine_validation": {"errors": []}, "scenarios": [],
                }, 0))
                continue

            # baseline-only 通过条件：baseline 存在 + scenarios 完整 + 无 engine error
            baseline_scenarios = baseline_raw.get("scenarios") or []
            baseline_results = baseline_raw.get("results", {})
            all_scenarios_ok = all(
                r and r["final"]["state"] in ("DONE", "REJECT")
                for r in baseline_results.values()
            )

            elapsed = time.time() - overall_start  # 简化
            if all_scenarios_ok and baseline_scenarios:
                print(f"  ✅ baseline 完整：{len(baseline_scenarios)} scenarios, {len(baseline_results)} results")
                entry = build_dashboard_entry(flow_name, 0, baseline_raw, elapsed)
                entries.append(entry)
            else:
                print(f"  ❌ baseline 不完整：scenarios={len(baseline_scenarios)} results={len(baseline_results)}")
                entry = build_dashboard_entry(flow_name, 1, baseline_raw, elapsed)
                entries.append(entry)
            continue

        # 重新构造 args（每个 flow 独立的参数）
        flow_args = argparse.Namespace(
            flow_json=str(flow_json),
            spi=args.spi,
            operator=flow_cfg.get("operator", "u_fdp_pm"),
            no_reject=False,
            max_steps=args.max_steps,
            variable=json.dumps(flow_cfg.get("variable", {})),
            top_vars=json.dumps(flow_cfg.get("top_vars", {})),
            scenarios=flow_cfg.get("scenarios", "happy:{}"),
            save_baseline=args.save_baseline,
            compare_baseline=flow_cfg.get("baseline", ""),
            tests_file=str(args.tests_file),
            all_flows=False,
            baseline_only=False,
            report_json=None,  # 不在子流程写 dashboard
            dry_run=args.dry_run,
            parallel=args.parallel,
        )

        exit_code, raw_data, elapsed = await run_single_flow(flow_args, flow_json)
        entry = build_dashboard_entry(flow_name, exit_code, raw_data, elapsed)
        entries.append(entry)

        mark = "✅" if exit_code == 0 else "❌"
        print(f"\n{mark} {flow_name}: exit={exit_code} scenarios={entry['scenario_count']} elapsed={elapsed:.2f}s")
        print()

    total_elapsed = time.time() - overall_start
    dashboard = build_dashboard(entries, total_elapsed)

    # 输出汇总
    print(f"{'='*60}")
    print(f"📊 DASHBOARD SUMMARY")
    print(f"{'='*60}")
    s = dashboard["summary"]
    print(f"   flows: {s['passed_flows']}/{s['total_flows']} PASSED")
    print(f"   scenarios: {s['passed_scenarios']}/{s['total_scenarios']} OK")
    print(f"   total elapsed: {total_elapsed:.2f}s")
    print(f"   all_passed: {s['all_passed']}")
    if s["all_passed"]:
        print(f"\n✅ ALL FLOWS PASSED")
    else:
        print(f"\n❌ {s['failed_flows']} FLOW(S) FAILED")
        for e in entries:
            if not e["passed"]:
                print(f"   - {e['flow_name']}: exit={e['exit_code']}")

    # 写 dashboard JSON
    if args.report_json:
        report_path = Path(args.report_json)
        if not report_path.is_absolute():
            report_path = PROJECT_ROOT / report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(dashboard, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"\n📄 Dashboard JSON: {report_path}")

    # 写 dashboard HTML
    if args.report_html:
        html_path = Path(args.report_html)
        if not html_path.is_absolute():
            html_path = PROJECT_ROOT / html_path
        html_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存 dashboard 到 history（用于趋势）
        history_dir = PROJECT_ROOT / "ToT/tdd/dashboard-history"
        history_dir.mkdir(exist_ok=True)
        history_file = history_dir / f"dashboard_{dashboard['generated_at'].replace(':', '-').replace('T', '_')}.json"
        history_file.write_text(
            json.dumps(dashboard, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

        # 加载最近 10 次历史
        history_files = sorted(history_dir.glob("dashboard_*.json"))[-10:]
        history = []
        for hf in history_files:
            try:
                history.append(json.loads(hf.read_text(encoding="utf-8")))
            except Exception:
                pass

        # 计算 per-flow 历史（每个 flow 在 history 中的多次跑数据）
        flow_histories = {}
        if history:
            for h in history:
                for entry in h.get("flows", []):
                    fn = entry["flow_name"]
                    flow_histories.setdefault(fn, []).append(entry)

        html_content = render_html_dashboard(dashboard, history=history,
                                              flow_histories=flow_histories)
        html_path.write_text(html_content, encoding="utf-8")
        print(f"🌐 Dashboard HTML: {html_path}")
        print(f"   history: {len(history_files)} runs")

    return 0 if dashboard["summary"]["all_passed"] else 1


async def run_single_flow(args, flow_path_ignored):
    """运行单个 flow 的完整流程，返回 (exit_code, raw_data, elapsed)"""
    start_time = time.time()
    exit_code, raw_data = await main_legacy(args)
    elapsed = time.time() - start_time
    return exit_code, raw_data, elapsed


async def main_legacy(args):
    """原 main 函数逻辑（保留向后兼容）"""
    flow_path = Path(args.flow_json).resolve()
    if not flow_path.exists():
        print(f"❌ 文件不存在: {flow_path}")
        return 1, {}

    # 1. 静态校验
    log("--- 1. 静态校验 ---")
    from tdd.validate_flow import _validate, _load
    data, err = _load(flow_path)
    if err:
        log(f"❌ JSON 解析失败: {err}")
        return 1, {"static_validation": {"error": err}}

    errs, warns = _validate(data)
    static_validation = {
        "node_count": len(data.get("nodes", [])),
        "edge_count": len(data.get("edges", [])),
        "errors": errs,
        "warnings": warns,
    }
    log(f"  validate_flow: {len(data['nodes'])} nodes, {len(data['edges'])} edges, {len(errs)} errors, {len(warns)} warnings")
    if errs:
        log(f"  ❌ errors: {errs}")
        return 1, {"static_validation": static_validation}

    # 2. 引擎 verify
    log("--- 2. 引擎 verify_flow ---")
    sys.path.insert(0, str(VENDOR))
    from jeeflow.verify import verify_flow
    verrs, vwarns, vpatterns = verify_flow(data)
    engine_validation = {
        "errors": [{"code": e.code, "msg": e.msg} for e in verrs],
        "warnings": [{"code": w.code, "msg": w.msg} for w in vwarns],
        "patterns": [{"code": p.code, "msg": p.msg} for p in vpatterns],
    }
    log(f"  errors={len(verrs)}, warnings={len(vwarns)}, patterns={len(vpatterns)}")
    for w in vwarns:
        log(f"  ⚠️  [{w.code}] {w.msg[:100]}")
    if verrs:
        log(f"  ❌ errors: {[e.msg for e in verrs]}")
        return 1, {"static_validation": static_validation, "engine_validation": engine_validation}

    # 2.5. dry-run
    if args.dry_run:
        log("")
        log("🏃 dry-run 模式：跳过实跑引擎")
        ts = time.strftime("%Y%m%d%H%M%S")
        out_dir = PROJECT_ROOT / "ToT/tdd"
        out_dir.mkdir(exist_ok=True)
        md_path = out_dir / f"test_{flow_path.stem}_{ts}.md"
        json_path = out_dir / f"test_{flow_path.stem}_{ts}.json"
        md_content = f"# TDD Dry-Run · {flow_path.stem} · {ts}\n\n"
        md_content += f"**模式**: dry-run\n\n"
        md_content += f"## 1. 静态校验\n\n- nodes={static_validation['node_count']} edges={static_validation['edge_count']} errors={len(static_validation['errors'])} warnings={len(static_validation['warnings'])}\n\n"
        md_content += f"## 2. 引擎 verify_flow\n\n- errors={len(engine_validation['errors'])} warnings={len(engine_validation['warnings'])} patterns={len(engine_validation['patterns'])}\n\n"
        for w in vwarns:
            md_content += f"  - ⚠️ [{w.code}] {w.msg[:120]}\n"
        raw_data = {
            "timestamp": ts,
            "spi_folder": args.spi,
            "operator": args.operator,
            "static_validation": static_validation,
            "engine_validation": engine_validation,
            "results": {},
        }
        md_path.write_text(md_content, encoding="utf-8")
        json_path.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        log(f"  报告: {md_path.relative_to(PROJECT_ROOT)}")
        log(f"\n✅ DRY-RUN PASSED")
        return 0, raw_data

    return await _main_impl(args, flow_path, data, static_validation, engine_validation)


async def _main_impl(args, flow_path, data, static_validation, engine_validation):
    """main_legacy 的剩余部分（实跑逻辑）"""
    # 1. 解析 global variable
    global_var = None
    if args.variable:
        try:
            global_var = json.loads(args.variable)
        except json.JSONDecodeError as e:
            print(f"❌ --variable JSON 解析失败: {e}")
            return 1, {}

    # 1.5. 加载 tests-file（如指定）
    if args.tests_file:
        load_tests_file(args.tests_file, flow_path, args)
        # 重新解析
        global_var = None
        if args.variable:
            try:
                global_var = json.loads(args.variable)
            except json.JSONDecodeError as e:
                print(f"❌ --variable JSON 解析失败: {e}")
                return 1, {}
        global_top_vars = None
        if args.top_vars:
            try:
                global_top_vars = json.loads(args.top_vars)
            except json.JSONDecodeError as e:
                print(f"❌ --top-vars JSON 解析失败: {e}")
                return 1, {}
    else:
        global_top_vars = None
        if args.top_vars:
            try:
                global_top_vars = json.loads(args.top_vars)
            except json.JSONDecodeError as e:
                print(f"❌ --top-vars JSON 解析失败: {e}")
                return 1, {}

    ts = time.strftime("%Y%m%d%H%M%S")
    flow_name = flow_path.stem
    out_dir = PROJECT_ROOT / "ToT/tdd"
    out_dir.mkdir(exist_ok=True)
    md_path = out_dir / f"test_{flow_name}_{ts}.md"
    json_path = out_dir / f"test_{flow_name}_{ts}.json"

    raw_data = {
        "timestamp": ts,
        "spi_folder": args.spi,
        "operator": args.operator,
        "global_variable": global_var,
        "global_top_vars": global_top_vars,
        "scenarios": None,
        "flow_json": str(flow_path),
        "results": {},
        "static_validation": static_validation,
        "engine_validation": engine_validation,
    }

    log(f"=== TDD 实跑: {flow_path.name} ===")
    log(f"SPI_FOLDER={args.spi}, operator={args.operator}")
    if args.scenarios:
        log(f"scenarios={args.scenarios}")
    elif global_var:
        log(f"global_variable={global_var}")
    if global_top_vars:
        log(f"global_top_vars={global_top_vars}")

    # 3. 引擎实跑
    log("--- 3. 引擎实跑 ---")
    facade = await setup_engine()
    define_id = await deploy(facade, flow_path, args.operator)
    log(f"  ✓ define_id={define_id}")
    raw_data["define_id"] = define_id

    # happy / reject / scenarios 执行
    if args.scenarios:
        scenarios = parse_scenarios(args.scenarios)
        raw_data["scenarios"] = scenarios
        log(f"--- 3. 引擎实跑（{len(scenarios)} 个自定义 scenarios，parallel={args.parallel}） ---")
        if args.parallel > 1:
            sem = asyncio.Semaphore(args.parallel)
            async def run_with_sem(sc):
                async with sem:
                    label = sc["name"]
                    var = sc["variable"]
                    submit_type = sc.get("submit_type", 1)
                    comment = sc.get("comment")
                    result, err = await run_path(
                        facade, define_id, args.operator,
                        submit_type=submit_type,
                        max_steps=args.max_steps, label=label,
                        variable=var, top_vars=global_top_vars,
                        comment=comment,
                    )
                    return label, submit_type, result, err

            results_list = await asyncio.gather(*[run_with_sem(sc) for sc in scenarios])
            for label, submit_type, result, err in results_list:
                raw_data["results"][label] = result
                if err:
                    log(f"  ❌ {label}: {err}")
                else:
                    log(f"  ✓ {label} final state = {result['final']['state']} (submitType={submit_type})")
        else:
            for sc in scenarios:
                label = sc["name"]
                var = sc["variable"]
                submit_type = sc.get("submit_type", 1)
                comment = sc.get("comment")
                result, err = await run_path(
                    facade, define_id, args.operator,
                    submit_type=submit_type,
                    max_steps=args.max_steps, label=label,
                    variable=var, top_vars=global_top_vars,
                    comment=comment,
                )
                raw_data["results"][label] = result
                if err:
                    log(f"  ❌ {label}: {err}")
                else:
                    log(f"  ✓ {label} final state = {result['final']['state']} (submitType={submit_type})")
    else:
        happy_result, happy_err = await run_path(
            facade, define_id, args.operator,
            submit_type=1, max_steps=args.max_steps, label="happy",
            variable=global_var, top_vars=global_top_vars,
        )
        raw_data["results"]["happy"] = happy_result
        if happy_err:
            log(f"  ❌ happy: {happy_err}")
        else:
            log(f"  ✓ happy final state = {happy_result['final']['state']}")

        has_decision = any(n.get("type") == "snaker:decision" for n in data["nodes"])
        if has_decision and not args.no_reject:
            reject_result, reject_err = await run_path(
                facade, define_id, args.operator,
                submit_type=2, max_steps=args.max_steps, label="reject",
                variable=global_var, top_vars=global_top_vars,
            )
            raw_data["results"]["reject"] = reject_result
            if reject_err:
                log(f"  ❌ reject: {reject_err}")
            else:
                log(f"  ✓ reject final state = {reject_result['final']['state']}")

    # 4. 保存原始数据
    json_path.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    log(f"  原始数据: {json_path.relative_to(PROJECT_ROOT)}")

    # 5. 生成 md
    generate_md(md_path, flow_path, raw_data)

    # 6. save-baseline
    if args.save_baseline:
        save_as_baseline(md_path, flow_name, raw_data)

    # 7. compare-baseline
    if args.compare_baseline:
        compare_ok = compare_with_baseline(args.compare_baseline, raw_data)
        if not compare_ok:
            return 1, raw_data

    # 退出码
    if args.scenarios:
        scenarios_spec = parse_scenarios(args.scenarios)
        def expected_states(sc):
            st = sc.get("submit_type", 1)
            if st == 2:
                return {"DONE", "REJECT"}
            return {"DONE"}
        all_ok = True
        for sc in scenarios_spec:
            label = sc["name"]
            r = raw_data["results"].get(label)
            if not r:
                all_ok = False
                continue
            if r["final"]["state"] not in expected_states(sc):
                all_ok = False
        if all_ok and not static_validation["errors"] and not engine_validation["errors"]:
            log(f"\n✅ PASSED — {len(raw_data['results'])} scenarios OK")
            return 0, raw_data
        else:
            log(f"\n❌ FAILED")
            return 1, raw_data
    else:
        happy_ok = raw_data["results"]["happy"]["final"]["state"] == "DONE"
        if happy_ok and not static_validation["errors"] and not engine_validation["errors"]:
            log(f"\n✅ PASSED — happy state=DONE")
            return 0, raw_data
        else:
            log(f"\n❌ FAILED")
            return 1, raw_data


def compare_with_baseline(baseline_path: str, current_raw: dict):
    """对比当前结果与历史 baseline JSON"""
    baseline_file = Path(baseline_path)
    if not baseline_file.exists():
        if not baseline_file.is_absolute():
            alt = PROJECT_ROOT / "ToT/tdd" / baseline_path
            if alt.exists():
                baseline_file = alt
            else:
                log(f"\n  ❌ baseline 文件不存在: {baseline_path}")
                return False
    try:
        baseline_raw = json.loads(baseline_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        log(f"\n  ❌ baseline JSON 解析失败: {e}")
        return False

    log(f"\n  📊 对比 baseline: {baseline_file.name}")

    def extract_signature(raw):
        sig = {
            "scenarios": [{"name": s["name"], "variable": s.get("variable", {}), "submit_type": s.get("submit_type", 1)}
                          for s in (raw.get("scenarios") or [])],
            "static_errors": len(raw.get("static_validation", {}).get("errors", [])),
            "engine_errors": len(raw.get("engine_validation", {}).get("errors", [])),
            "results": {},
        }
        for label, r in raw.get("results", {}).items():
            if not r:
                continue
            sig["results"][label] = {
                "state": r["final"]["state"],
                "task_count": len([t["name"] for t in r.get("final", {}).get("tasks", [])]),
                "task_names": [t["name"] for t in r.get("final", {}).get("tasks", [])],
                "actors_per_task": {t["name"]: t["actors"] for t in r.get("final", {}).get("tasks", [])},
            }
        return sig

    cur_sig = extract_signature(current_raw)
    base_sig = extract_signature(baseline_raw)

    diffs = []
    if cur_sig["scenarios"] != base_sig["scenarios"]:
        diffs.append(f"  scenarios:\n    旧: {base_sig['scenarios']}\n    新: {cur_sig['scenarios']}")
    if cur_sig["static_errors"] != base_sig["static_errors"]:
        diffs.append(f"  static_errors: 旧={base_sig['static_errors']} 新={cur_sig['static_errors']}")
    if cur_sig["engine_errors"] != base_sig["engine_errors"]:
        diffs.append(f"  engine_errors: 旧={base_sig['engine_errors']} 新={cur_sig['engine_errors']}")
    base_results = set(base_sig["results"].keys())
    cur_results = set(cur_sig["results"].keys())
    if base_results != cur_results:
        diffs.append(f"  scenario names:\n    旧: {sorted(base_results)}\n    新: {sorted(cur_results)}")
    for label in sorted(base_results | cur_results):
        b = base_sig["results"].get(label, {})
        c = cur_sig["results"].get(label, {})
        if b == c:
            continue
        diffs.append(f"  [{label}]:")
        for key in sorted(set(b.keys()) | set(c.keys())):
            bv = b.get(key)
            cv = c.get(key)
            if bv != cv:
                diffs.append(f"    {key}:\n      旧: {bv}\n      新: {cv}")

    if not diffs:
        log(f"  ✅ 无差异（与 baseline 完全一致）")
        return True
    else:
        log(f"  ❌ 发现 {len(diffs)} 处差异：")
        for d in diffs:
            log(d)
        log("")
        log("  📋 对比摘要：")
        for label in sorted(set(cur_sig["results"]) | set(base_sig["results"])):
            b = base_sig["results"].get(label, {})
            c = cur_sig["results"].get(label, {})
            bs = b.get("state", "—")
            cs = c.get("state", "—")
            bt = b.get("task_count", 0)
            ct = c.get("task_count", 0)
            mark = "✅" if bs == cs and bt == ct else "❌"
            log(f"    {mark} [{label}] state {bs}→{cs}, tasks {bt}→{ct}")
        return False


def save_as_baseline(md_path: Path, flow_name: str, raw_data: dict):
    """把测试结果保存为 baseline md (test_<flow>_baseline_v<N>_<M>.md)

    同时复制原始 raw_data JSON 为同名前缀（供 --compare-baseline 使用）。
    自动选择下一个版本号（如果 v0_1 已存在，写 v0_2 等）。
    """
    baseline_dir = PROJECT_ROOT / "ToT/tdd"
    # 找下一个版本号（解析 v<N>_<M> 格式）
    existing = sorted(baseline_dir.glob(f"test_{flow_name}_baseline_v*.md"))
    next_v = len(existing) + 1
    v_str = f"v0_{next_v}"  # 跟手工命名的 v0_1 风格一致
    ts = raw_data["timestamp"]
    baseline_md = baseline_dir / f"test_{flow_name}_baseline_{v_str}_{ts}.md"
    baseline_json = baseline_dir / f"test_{flow_name}_baseline_{v_str}_{ts}.json"

    # 读原 md，加 baseline 头部
    md_content = md_path.read_text(encoding="utf-8")
    baseline_header = (
        f"# Baseline · {flow_name} · v0.{next_v} · {ts}\n\n"
        f"> **目的**：流程自动化生成的 baseline（用 `tdd-flow.py --save-baseline`）\n"
        f"> **原始测试**：`ToT/tdd/{md_path.name}`\n"
        f"> **原始数据**：`ToT/tdd/{baseline_json.name}`\n\n"
        f"---\n\n"
    )
    baseline_md.write_text(baseline_header + md_content, encoding="utf-8")

    # 复制 raw_data 为 baseline JSON（机器可读，compare-baseline 用）
    import copy
    baseline_raw = copy.deepcopy(raw_data)
    # 标记是 baseline
    baseline_raw["_baseline_meta"] = {
        "flow_name": flow_name,
        "version": f"v0.{next_v}",
        "created_at": ts,
        "source_tool": "tdd-flow.py --save-baseline",
    }
    baseline_json.write_text(
        json.dumps(baseline_raw, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    log(f"\n  📋 已保存 baseline:")
    log(f"      md:   {baseline_md.relative_to(PROJECT_ROOT)}")
    log(f"      json: {baseline_json.relative_to(PROJECT_ROOT)}")


def generate_md(md_path: Path, flow_path: Path, raw_data: dict):
    """生成人类可读 .md 摘要（支持多 scenario）"""
    flow_name = flow_path.stem
    results = raw_data["results"]
    sv = raw_data["static_validation"]
    ev = raw_data["engine_validation"]
    is_scenarios = raw_data.get("scenarios") is not None

    lines = [
        f"# TDD Test Log · {flow_name} · {raw_data['timestamp']}",
        "",
        f"**SPI_FOLDER**: `{raw_data['spi_folder']}`  |  **operator**: `{raw_data['operator']}`",
    ]
    if raw_data.get("global_variable"):
        lines.append(f"**global_variable**: `{json.dumps(raw_data['global_variable'], ensure_ascii=False)}`")
    if raw_data.get("global_top_vars"):
        lines.append(f"**global_top_vars**: `{json.dumps(raw_data['global_top_vars'], ensure_ascii=False)}`")
    if is_scenarios:
        lines.append(f"**mode**: 自定义 scenarios ({len(results)} 个)")
    lines.append("")

    lines += [
        "## 1. 静态校验",
        "",
        f"- validate_flow: **{sv['node_count']} nodes, {sv['edge_count']} edges**, {len(sv['errors'])} errors, {len(sv['warnings'])} warnings",
    ]
    if sv["errors"]:
        lines.append(f"- ❌ errors:")
        for e in sv["errors"]:
            lines.append(f"  - {e}")
    if sv["warnings"]:
        lines.append(f"- warnings:")
        for w in sv["warnings"]:
            lines.append(f"  - {w}")

    lines += [
        "",
        "## 2. 引擎 verify_flow",
        "",
        f"- errors: **{len(ev['errors'])}**, warnings: **{len(ev['warnings'])}**, patterns: **{len(ev['patterns'])}**",
    ]
    for e in ev["errors"]:
        lines.append(f"  - ❌ [{e['code']}] {e['msg']}")
    for w in ev["warnings"]:
        lines.append(f"  - ⚠️  [{w['code']}] {w['msg'][:120]}")

    lines += [
        "",
        "## 3. 引擎实跑",
        "",
    ]

    # 每个 scenario/path 一节
    for label, r in results.items():
        if not r:
            continue
        var = r.get("variable", {})
        var_str = f" — variable=`{json.dumps(var, ensure_ascii=False)}`" if var else ""
        top_str = f" — top_vars=`{json.dumps(r.get('top_vars', {}), ensure_ascii=False)}`" if r.get('top_vars') else ""
        lines.append(f"### {label} path (instance={r['instance_id']}){var_str}{top_str}")
        lines.append("")
        lines.append(f"**最终 state**: `{r['final']['state']} ({r['final']['state_code']})`")
        lines.append("")
        lines.append("| task | state | operator | actors |")
        lines.append("|------|-------|----------|--------|")
        for t in r["final"]["tasks"]:
            lines.append(f"| {t['name']:18s} | {t['state']:6s} | {str(t['operator'] or '∅'):10s} | {t['actors']} |")
        lines.append("")

    lines += [
        "## 4. 总结",
        "",
        f"- static errors: **{len(sv['errors'])}**",
        f"- engine errors: **{len(ev['errors'])}**",
    ]
    for label, r in results.items():
        if r:
            lines.append(f"- {label} final: **{r['final']['state']}**")

    lines += [
        "",
        "## 5. 原始数据",
        "",
        f"机器可读原始响应：与本文件同目录的 `.json` 文件（含 deploy / start / execute / detail 全量响应）",
        "",
    ]

    md_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
