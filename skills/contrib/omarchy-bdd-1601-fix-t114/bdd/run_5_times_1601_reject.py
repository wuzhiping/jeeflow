#!/usr/bin/env python3
"""Run BDD-1601 REJECT bug repro 5 times.

Targets: PARALLEL countersign with submitType=2 REJECT (no ONE_VOTE_VETO).
Expected: userA (rejecter) DONE + instance state=45 REJECT
Bug:      userB, userC tasks remain DOING (state=10), orphan tasks
"""
import json, sys, os, subprocess
from urllib import request as urlrequest
from datetime import datetime

API = "http://127.0.0.1:8101"
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
RUNS = 5
FLOW = "bdd/bdd-1601-expense-threshold-countersign_20260921_155448.json"
ASSIGN = "bdd/bdd-1601-assignees.json"
OUT_RESULTS = f"bdd/test-results-1601-reject-{TS}.json"
OUT_AUDIT_DIR = f"bdd/audit-1601-reject-{TS}"


def call(action, data):
    req = urlrequest.Request(f"{API}/wf/{action}",
                             data=json.dumps(data).encode(),
                             headers={"Content-Type": "application/json"})
    try:
        with urlrequest.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"code": -1, "msg": str(e)}


def reset():
    req = urlrequest.Request(f"{API}/api/reset", data=b"{}",
                             headers={"Content-Type": "application/json"})
    with urlrequest.urlopen(req) as r:
        return json.loads(r.read().decode())


def todo(op):
    return call("processTask/todoList", {"operator": op, "pageNum": 1, "pageSize": 50})


def grab_audit():
    r = call("auditLog/export", {"format": "json"})
    if r.get("code") == 0:
        return {"count": r["data"].get("count", 0),
                "entries": json.loads(r["data"].get("data", "[]"))}
    return {"count": 0, "entries": []}


def main():
    os.makedirs(OUT_AUDIT_DIR, exist_ok=True)
    print(f"=== BUG-4 (PARALLEL countersign REJECT) 5-run repro at {TS} ===")

    # Five scenarios: vary rejector (userA, userB, userC) + boundary (amount=5000 boundary goes small branch, use 5500)
    rejecters = ["userA", "userB", "userC", "userA", "userB"]

    results = []

    for i, rejecter in enumerate(rejecters):
        run_n = i + 1
        print(f"\n--- Run {run_n}/{RUNS} [rejector={rejecter}] ---")

        reset()

        # deploy
        content = json.load(open(FLOW, encoding="utf-8"))
        save = call("processDesign/save", {
            "name": content["name"],
            "displayName": content.get("displayName", content["name"]),
            "type": content.get("type", "approval"),
            "content": json.dumps(content, ensure_ascii=False)})
        dp = call("processDesign/deploy", {"id": save["data"]["id"]})
        pdi = dp["data"]["processDefineId"]

        # start with amount=8000 (large branch)
        assignees = json.load(open(ASSIGN, encoding="utf-8"))
        vars_ = {"f_amount": 8000, "f_applicant": "user1", "u_userId": "user1",
                 "u_realName": "张三"}
        st = call("processInstance/startAndExecute", {
            "processDefineId": pdi, "operator": "user1",
            "title": f"BUG-4 R{run_n} reject={rejecter}",
            "assignees": assignees, "variables": vars_})
        inst = st["data"]["processInstanceId"]

        # leader approves
        todos = todo("leader")
        tid_l = next((t["id"] for t in todos.get("data", {}).get("rows", [])
                      if str(t.get("processInstanceId")) == str(inst)), None)
        r1 = call("processTask/execute", {"processTaskId": tid_l, "operator": "leader", "submitType": 1})

        # Verify all 3 countersign tasks created
        task_ids = {}
        for op in ["userA", "userB", "userC"]:
            todos = todo(op)
            for t in todos.get("data", {}).get("rows", []):
                if str(t.get("processInstanceId")) == str(inst):
                    task_ids[op] = t["id"]
                    break

        # rejecter rejects
        r_rej = call("processTask/execute", {
            "processTaskId": task_ids[rejecter],
            "operator": rejecter, "submitType": 2})

        # Check instance state
        det = call("processInstance/detail", {"id": str(inst)})
        hl = call("processInstance/highLight", {"id": str(inst)})
        ar = call("processInstance/approvalRecord", {"id": str(inst)})

        # Check orphan tasks
        orphan_tasks = {}
        for op in ["userA", "userB", "userC"]:
            todos = todo(op)
            for t in todos.get("data", {}).get("rows", []):
                if str(t.get("processInstanceId")) == str(inst):
                    orphan_tasks[op] = {"task_id": t["id"], "state": t.get("taskState"),
                                         "operator": t.get("operator")}

        # audit
        snap = grab_audit()
        snap["after_run"] = run_n
        with open(f"{OUT_AUDIT_DIR}/audit-after-run-{run_n}.json", "w",
                  encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False, indent=1)

        # Summary
        bug_count = sum(1 for op, t in orphan_tasks.items()
                        if op != rejecter and t.get("state") == 10)
        verdict = "❌ BUG" if bug_count > 0 else "✅ OK"

        print(f"  [{verdict}] inst={inst} rejecter={rejecter} "
              f"inst_state={det['data']['state']} orphan_DOING={bug_count}")
        for op, info in orphan_tasks.items():
            print(f"    {op}: task={info['task_id']} state={info['state']} "
                  f"(operator={info['operator']!r})")

        results.append({
            "run": run_n, "rejecter": rejecter,
            "inst": str(inst),
            "instance_state": det["data"]["state"],
            "rejecter_task_state": orphan_tasks.get(rejecter, {}).get("state"),
            "orphan_DOING_count": bug_count,
            "orphan_tasks": {op: t for op, t in orphan_tasks.items()
                             if op != rejecter and t.get("state") == 10},
            "approval_record": [
                {"taskName": r["taskName"],
                 "operator": r.get("operator") or r.get("assignee"),
                 "taskState": r["taskState"]}
                for r in ar.get("data", [])
            ],
            "history_nodes": (hl.get("data") or {}).get("historyNodeNames"),
            "audit_count": snap.get("count"),
            "audit_entries": snap.get("entries"),
        })

    # Summary
    bug_runs = sum(1 for r in results if r["orphan_DOING_count"] > 0)
    clean_runs = RUNS - bug_runs

    summary = {
        "timestamp": TS, "flow": FLOW, "scenario": "BUG-4 PARALLEL REJECT orphan",
        "total_runs": RUNS, "bug_repro": bug_runs, "clean": clean_runs,
        "results": results,
    }

    with open(OUT_RESULTS, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    print(f"\n=== Done. Bug reproduced {bug_runs}/{RUNS} runs ===")
    print(f"Results: {OUT_RESULTS}")
    print(f"Reports: {OUT_AUDIT_DIR}/")
    return summary


if __name__ == "__main__":
    main()