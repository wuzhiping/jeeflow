#!/usr/bin/env python3
"""tdd-flow.py — 流程 JSON 引擎实跑 TDD 脚本

用途：把 flow JSON 部署到 jeeFlow memory engine，逐 stage 执行并记录完整状态。
依据：ToT/sop/tdd-flow.md

用法：
    python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json
    python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json --spi dev --operator u_fdp_pm
    python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json --no-reject

输出（按时间戳，自动写入 ToT/tdd/）：
    test_<flow-name>_<YYYYMMDDHHMMSS>.md   人类可读摘要
    test_<flow-name>_<YYYYMMDDHHMMSS>.json 原始引擎响应（machine-readable）

退出码：
    0 - happy path PASSED
    1 - happy path FAILED
    2 - 部分 PASSED（warning）

历史：本脚本由 v0.6.2 fdep.json 实跑沉淀而来，2026-09-22 首次落地。
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


async def run_path(facade, define_id, operator, submit_type=1, max_steps=20, label="happy"):
    """执行一个 instance 直到 DONE / REJECT / 卡住"""
    start = await facade.flow("processDefine/startAndExecute", {
        "processDefineId": define_id,
        "operator": operator,
    })
    if start.get("code") != 0:
        return None, f"startAndExecute 失败: {start}"

    iid = start["data"]["processInstanceId"]
    log(f"  [{label}] instance={iid}", None)

    steps = []
    for step_idx in range(max_steps):
        snap = await inspect(facade, iid)
        steps.append({"step": step_idx, "snapshot": snap})

        if snap["state"] in ("DONE", "REJECT"):
            log(f"  [{label}] 终止 state={snap['state']} ({snap['state_code']})", None)
            break

        if snap["state"] not in ("DOING",):
            log(f"  [{label}] 异常 state={snap['state']} ({snap['state_code']}), 停止", None)
            break

        # 找 operator 的 todo
        todo_resp = await facade.flow("processTask/todoList", {"operator": operator, "limit": 50})
        my_tasks = [t for t in (todo_resp.get("data") or {}).get("rows", []) if t.get("processInstanceId") == iid]
        if not my_tasks:
            log(f"  [{label}] 无 todo, 停止", None)
            break

        t = my_tasks[0]
        log(f"  [{label}] step {step_idx + 1}: execute {t['taskName']} (submitType={submit_type})", None)
        exec_resp = await facade.flow("processTask/execute", {
            "processTaskId": t["id"],
            "operator": operator,
            "submitType": submit_type,
        })
        steps.append({"step": step_idx, "execute": {
            "task_name": t["taskName"],
            "submit_type": submit_type,
            "resp_code": exec_resp.get("code"),
            "resp_msg": exec_resp.get("msg", ""),
        }})
        if exec_resp.get("code") != 0:
            log(f"  [{label}] execute 失败: {exec_resp}", None)
            break

    final = await inspect(facade, iid)
    return {"instance_id": iid, "steps": steps, "final": final}, None


async def main():
    parser = argparse.ArgumentParser(description="TDD 流程 JSON 引擎实跑")
    parser.add_argument("flow_json", help="流程 JSON 文件路径")
    parser.add_argument("--spi", default="dev", help="SPI_FOLDER 环境（默认 dev）")
    parser.add_argument("--operator", default="u_fdp_pm", help="流程发起人/执行人（默认 u_fdp_pm）")
    parser.add_argument("--no-reject", action="store_true", help="只跑 happy path，不跑 reject")
    parser.add_argument("--max-steps", type=int, default=20, help="单 path 最大步数")
    args = parser.parse_args()

    os.environ["SPI_FOLDER"] = args.spi

    flow_path = Path(args.flow_json).resolve()
    if not flow_path.exists():
        print(f"❌ 文件不存在: {flow_path}")
        return 1

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
        "flow_json": str(flow_path),
        "results": {},
    }

    log(f"=== TDD 实跑: {flow_path.name} ===")
    log(f"SPI_FOLDER={args.spi}, operator={args.operator}")

    # 1. 静态校验
    log("--- 1. 静态校验 ---")
    from tdd.validate_flow import _validate, _load
    data, err = _load(flow_path)
    if err:
        log(f"❌ JSON 解析失败: {err}")
        raw_data["static_validation"] = {"error": err}
        json_path.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return 1
    errs, warns = _validate(data)
    raw_data["static_validation"] = {
        "node_count": len(data.get("nodes", [])),
        "edge_count": len(data.get("edges", [])),
        "errors": errs,
        "warnings": warns,
    }
    log(f"  validate_flow: {len(data['nodes'])} nodes, {len(data['edges'])} edges, {len(errs)} errors, {len(warns)} warnings")
    if errs:
        log(f"  ❌ errors: {errs}")
        json_path.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return 1

    # 2. 引擎 verify
    log("--- 2. 引擎 verify_flow ---")
    sys.path.insert(0, str(VENDOR))
    from jeeflow.verify import verify_flow
    verrs, vwarns, vpatterns = verify_flow(data)
    raw_data["engine_validation"] = {
        "errors": [{"code": e.code, "msg": e.msg} for e in verrs],
        "warnings": [{"code": w.code, "msg": w.msg} for w in vwarns],
        "patterns": [{"code": p.code, "msg": p.msg} for p in vpatterns],
    }
    log(f"  errors={len(verrs)}, warnings={len(vwarns)}, patterns={len(vpatterns)}")
    for w in vwarns:
        log(f"  ⚠️  [{w.code}] {w.msg[:100]}")
    if verrs:
        log(f"  ❌ errors: {[e.msg for e in verrs]}")
        json_path.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return 1

    # 3. 引擎实跑
    log("--- 3. 引擎实跑 ---")
    facade = await setup_engine()
    define_id = await deploy(facade, flow_path, args.operator)
    log(f"  ✓ define_id={define_id}")
    raw_data["define_id"] = define_id

    # happy path
    happy_result, happy_err = await run_path(facade, define_id, args.operator, submit_type=1, max_steps=args.max_steps, label="happy")
    raw_data["results"]["happy"] = happy_result
    if happy_err:
        log(f"  ❌ happy: {happy_err}")
    else:
        final_state = happy_result["final"]["state"]
        log(f"  ✓ happy final state = {final_state}")

    # reject path（如果流程含 snaker:decision）
    has_decision = any(n.get("type") == "snaker:decision" for n in data["nodes"])
    if has_decision and not args.no_reject:
        reject_result, reject_err = await run_path(facade, define_id, args.operator, submit_type=2, max_steps=args.max_steps, label="reject")
        raw_data["results"]["reject"] = reject_result
        if reject_err:
            log(f"  ❌ reject: {reject_err}")
        else:
            log(f"  ✓ reject final state = {reject_result['final']['state']}")
    else:
        log(f"  -- reject path 跳过 (无 decision 节点 或 --no-reject)")

    # 4. 保存 JSON 原始数据
    json_path.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    log(f"  原始数据: {json_path.relative_to(PROJECT_ROOT)}")

    # 5. 生成人类可读 .md
    generate_md(md_path, flow_path, raw_data)

    # 退出码
    happy_ok = raw_data["results"]["happy"]["final"]["state"] == "DONE"
    if happy_ok and not raw_data["static_validation"]["errors"] and not raw_data["engine_validation"]["errors"]:
        log(f"\n✅ PASSED — happy state=DONE")
        return 0
    else:
        log(f"\n❌ FAILED — happy state={raw_data['results']['happy']['final']['state'] if raw_data['results']['happy'] else 'N/A'}")
        return 1


def generate_md(md_path: Path, flow_path: Path, raw_data: dict):
    """生成人类可读 .md 摘要"""
    flow_name = flow_path.stem
    happy = raw_data["results"]["happy"]
    reject = raw_data["results"].get("reject")
    sv = raw_data["static_validation"]
    ev = raw_data["engine_validation"]

    lines = [
        f"# TDD Test Log · {flow_name} · {raw_data['timestamp']}",
        "",
        f"**SPI_FOLDER**: `{raw_data['spi_folder']}`  |  **operator**: `{raw_data['operator']}`",
        "",
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

    if happy:
        lines.append(f"### Happy path (instance={happy['instance_id']})")
        lines.append("")
        lines.append(f"**最终 state**: `{happy['final']['state']} ({happy['final']['state_code']})`")
        lines.append("")
        lines.append("| # | task | state | operator | actors |")
        lines.append("|---|------|-------|----------|--------|")
        for t in happy["final"]["tasks"]:
            lines.append(f"| {t['name']:18s} | {t['state']:6s} | {str(t['operator'] or '∅'):10s} | {t['actors']} |")
        lines.append("")

    if reject:
        lines.append(f"### Reject path (instance={reject['instance_id']})")
        lines.append("")
        lines.append(f"**最终 state**: `{reject['final']['state']} ({reject['final']['state_code']})`")
        lines.append("")
        lines.append("| # | task | state | operator | actors |")
        lines.append("|---|------|-------|----------|--------|")
        for t in reject["final"]["tasks"]:
            lines.append(f"| {t['name']:18s} | {t['state']:6s} | {str(t['operator'] or '∅'):10s} | {t['actors']} |")
        lines.append("")

    lines += [
        "## 4. 总结",
        "",
        f"- static errors: **{len(sv['errors'])}**",
        f"- engine errors: **{len(ev['errors'])}**",
        f"- happy final: **{happy['final']['state'] if happy else 'N/A'}**",
        f"- reject final: **{reject['final']['state'] if reject else 'skipped'}**",
        "",
        "## 5. 原始数据",
        "",
        f"机器可读原始响应：与本文件同目录的 `.json` 文件（含 deploy / start / execute / detail 全量响应）",
        "",
    ]

    md_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
