#!/usr/bin/env python3
"""BDD runner helper — 简化 detail 输出"""
import sys
import json
import urllib.request

def detail(inst_id):
    req = urllib.request.Request(
        "http://localhost:8101/wf/processInstance/detail",
        data=json.dumps({"id": inst_id}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read()).get("data", {})

def highlight(inst_id):
    req = urllib.request.Request(
        "http://localhost:8101/wf/processInstance/highLight",
        data=json.dumps({"id": inst_id}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read()).get("data", {})

def print_state(inst_id, label=""):
    d = detail(inst_id)
    state = d.get("state")
    active = d.get("activeTaskList", [])
    tasks = d.get("tasks", [])
    print(f"  state={state} active={len(active)}")
    for t in active:
        print(f"    ACTIVE: {t.get('taskName')} actors={t.get('taskActorIdList')}")
    for t in tasks:
        if t.get("taskName") not in [a.get("taskName") for a in active]:
            print(f"    DONE:   {t.get('taskName')} state={t.get('taskState')} actors={t.get('taskActorIdList')}")
    if label and "history" in label:
        h = highlight(inst_id)
        print(f"  history: {h.get('historyNodeNames')}")
        print(f"  current: {h.get('current')}")
    return d

if __name__ == "__main__":
    inst_id = sys.argv[1] if len(sys.argv) > 1 else input("inst_id: ")
    label = sys.argv[2] if len(sys.argv) > 2 else "history"
    print_state(inst_id, label)
