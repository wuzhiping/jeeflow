#!/usr/bin/env python3
"""BDD 任务执行助手 — 流程设计 + 部署 + 跑通 + 校验

使用示例：
    python3 bdd_helpers.py bdd 127  # 执行 bdd/bdd-127-*.json
    python3 bdd_helpers.py reset    # 调 /api/reset
    python3 bdd_helpers.py tdd <flow>  # 直接跑 flows/<flow>.json
"""
import sys
import json
import urllib.request

API = "http://127.0.0.1:8101"


def _call(action, data):
    url = f"{API}/wf/{action}"
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"code": -1, "msg": str(e)}


def reset():
    req = urllib.request.Request(f"{API}/api/reset", data=b'{}', headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def deploy(json_path):
    with open(json_path) as f:
        content = json.load(f)
    name = content.get("name", "test")
    save = _call("processDesign/save", {
        "name": name, "displayName": content.get("displayName", name),
        "type": content.get("type", "approval"),
        "content": json.dumps(content, ensure_ascii=False),
    })
    if save.get("code") != 0:
        return save, None
    design_id = save["data"]["id"]
    deploy_r = _call("processDesign/deploy", {"id": design_id})
    if deploy_r.get("code") != 0:
        return save, deploy_r
    return save, deploy_r


def start(pd_id, operator, variables=None, assignees=None, title="BDD"):
    args = {
        "processDefineId": pd_id,
        "operator": operator,
        "title": title,
        "variables": variables or {},
    }
    if assignees:
        args["assignees"] = assignees
    return _call("processInstance/startAndExecute", args)


def todo(operator):
    return _call("processTask/todoList", {"operator": operator, "pageNum": 1, "pageSize": 50})


def execute(task_id, operator, submitType=0, **extra):
    args = {"processTaskId": task_id, "operator": operator, "submitType": submitType}
    args.update(extra)
    return _call("processTask/execute", args)


def detail(inst_id):
    return _call("processInstance/detail", {"id": inst_id})


def approve_record(inst_id):
    return _call("processInstance/approvalRecord", {"id": inst_id})


def biz_data(inst_id):
    return _call("processInstance/bizData", {"id": inst_id})


def high_light(inst_id):
    return _call("processInstance/highLight", {"id": inst_id})


def todo_for(operator, pageNum=1, pageSize=50):
    return _call("processTask/todoList", {"operator": operator, "pageNum": pageNum, "pageSize": pageSize})


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "reset":
        print(json.dumps(reset(), ensure_ascii=False, indent=2))
    elif cmd == "deploy":
        save, dp = deploy(sys.argv[2])
        print("SAVE:", json.dumps(save, ensure_ascii=False, indent=2))
        print("DEPLOY:", json.dumps(dp, ensure_ascii=False, indent=2))
    elif cmd == "start":
        r = start(*sys.argv[2:])
        print(json.dumps(r, ensure_ascii=False, indent=2))
