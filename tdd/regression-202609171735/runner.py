#!/usr/bin/env python3
"""Regression runner v2 — 只执行本次 start instance 的 task"""
import sys, json, urllib.request, urllib.error, time

BASE_MEM = "http://localhost:8101"
BASE_PG = "http://localhost:8102"


def post(url, body):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read().decode())
        except: return {"code": -1, "msg": str(e)}
    except Exception as e:
        return {"code": -1, "msg": str(e)}


def reset(base_url):
    return post(f"{base_url}/api/reset", {})


def deploy(content, base_url):
    name = content.get("name", "regression")
    save = post(f"{base_url}/wf/processDesign/save", {
        "name": name,
        "displayName": content.get("displayName", name),
        "type": content.get("type", "approval"),
        "content": json.dumps(content, ensure_ascii=False),
    })
    if save.get("code") != 0:
        return None, None, {"save": save}
    did = save.get("data", {}).get("id")
    dep = post(f"{base_url}/wf/processDesign/deploy", {"id": did})
    if dep.get("code") != 0:
        return did, None, {"deploy": dep}
    return did, dep.get("data", {}).get("processDefineId"), {"save": save, "deploy": dep}


def start_instance(define_id, base_url, **kw):
    body = {
        "processDefineId": define_id,
        "operator": kw.get("operator", "user1"),
        "title": kw.get("title", f"regression-{int(time.time())}"),
        "assignees": kw.get("assignees", {}),
        "variables": kw.get("variables", {
            "submitType": 0,
            "u_userId": kw.get("operator", "user1"),
            "u_realName": "用户1"
        }),
    }
    return post(f"{base_url}/wf/processInstance/startAndExecute", body)


def todo(operator, base_url):
    return post(f"{base_url}/wf/processTask/todoList", {
        "operator": operator, "pageNum": 1, "pageSize": 100})


def execute(task_id, operator, submit_type, base_url):
    return post(f"{base_url}/wf/processTask/execute", {
        "processTaskId": task_id, "submitType": submit_type, "operator": operator})


def detail(inst_id, base_url):
    return post(f"{base_url}/wf/processInstance/detail", {"id": inst_id})


def approval_record(inst_id, base_url):
    return post(f"{base_url}/wf/processInstance/approvalRecord", {"id": inst_id})


def _auto_infer_variables(content, base_assignees=None):
    """FIX-ALL (2026-09-17)：从流程定义自动推断 variables
    FormFieldAssigneeHandler 需要 f_<node_id> 字段；如缺失则用 fallback user1
    """
    variables = {"submitType": 0, "u_userId": "user1", "u_realName": "用户1"}
    base_assignees = base_assignees or {}
    # FIX-ALL (2026-09-17)：custom 节点默认 assignee=operator（避免 FIX-T17 raise）
    has_custom = any(n.get("type") == "snaker:custom" for n in content.get("nodes", []))
    if has_custom:
        base_assignees.setdefault("apply", "user1")
    for n in content.get("nodes", []):
        if n.get("type") not in ("snaker:task", "snaker:custom"): continue
        nid = n["id"]
        p = n.get("properties", {})
        h = p.get("assignmentHandler", "")
        # FormFieldAssigneeHandler 需要 f_<node_id>
        if "FormFieldAssigneeHandler" in h:
            f_key = f"f_{nid}"
            if f_key not in variables:
                # fallback: 用 base_assignees 或 'leader'
                variables[f_key] = base_assignees.get(nid, "leader")
        # roleCode 也放进 variables 方便后续解析
        if p.get("roleCode"):
            variables[f"roleCode_{nid}"] = p["roleCode"]
    return variables


def run_flow(content, base_url, base_name, max_steps=10):
    """通用执行：start → 持续 execute 直到 instance 状态为 20/99/30/45"""
    log = []
    did, pdid, dep_log = deploy(content, base_url)
    if not pdid:
        return {"ok": False, "step": "deploy", "log": dep_log}
    variables = _auto_infer_variables(content)
    # FIX-ALL (2026-09-17)：自动给 custom 节点 fallback assignee
    assignees = {"apply": "user1"}
    for n in content.get("nodes", []):
        if n.get("type") == "snaker:custom":
            assignees[n["id"]] = "user1"
    inst = start_instance(pdid, base_url,
                          operator="user1",
                          assignees=assignees,
                          variables=variables)
    if inst.get("code") != 0:
        return {"ok": False, "step": "start", "log": inst, "pdid": pdid}
    inst_id = inst.get("data", {}).get("processInstanceId")
    log.append({"step": "start", "ok": True, "inst_id": inst_id})

    # 不断轮询当前 active operator 并 execute
    seen_operators = set()
    for step in range(max_steps):
        det = detail(inst_id, base_url)
        if det.get("code") != 0:
            return {"ok": False, "step": "detail", "log": det, "inst_id": inst_id}
        state = det.get("data", {}).get("state")
        if state in (20, 99, 30, 45):
            log.append({"step": "end", "state": state, "ok": True})
            break
        active = det.get("data", {}).get("activeTaskList", [])
        if not active:
            log.append({"step": "no-active", "state": state})
            break
        for tk in active:
            actors = tk.get("taskActorIdList") or tk.get("actors") or ([tk.get("assignee")] if tk.get("assignee") else [])
            if isinstance(actors, str):
                actors = [actors]
            for actor in actors:
                if actor in seen_operators and step > 1: continue
                seen_operators.add(actor)
                td = todo(actor, base_url)
                for it in td.get("data", {}).get("rows", []):
                    if it.get("processInstanceId") != inst_id: continue
                    ex = execute(it["id"], actor, 0, base_url)
                    log.append({"step": f"execute-{actor}",
                                "task": it.get("name"), "ok": ex.get("code") == 0,
                                "msg": ex.get("msg", "")[:80]})
    rec = approval_record(inst_id, base_url)
    history = rec.get("data", [])
    if isinstance(history, dict):
        history = history.get("list", [])
    log.append({"step": "approvalRecord", "ok": True,
                "history": [a.get("taskName") if isinstance(a, dict) else "" for a in history]})
    det2 = detail(inst_id, base_url)
    log.append({"step": "final-detail", "state": det2.get("data", {}).get("state")})
    return {"ok": True, "pdid": pdid, "inst_id": inst_id, "log": log}


if __name__ == "__main__":
    flow_path = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else BASE_MEM
    base_name = "memory" if base_url == BASE_MEM else "pg"
    print(f"=== {base_name} {flow_path} ===")
    content = json.load(open(flow_path))
    if base_url == BASE_PG and reset(base_url).get("code") == 0:
        print("[reset] ok")
    out = run_flow(content, base_url, base_name)
    print(json.dumps(out, ensure_ascii=False, indent=2)[:3000])
