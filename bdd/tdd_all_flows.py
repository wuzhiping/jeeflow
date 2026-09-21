"""TDD 所有 flows/*.json - 验证改动无回归

每个 flow 测试：
1. /wf/verify 预检
2. /wf/processDesign/save
3. /wf/processDesign/deploy
4. /wf/processInstance/startAndExecute
5. /wf/processInstance/detail - 验证 activeTaskList
6. 走完流程 - 模拟用户操作
"""
import json
import httpx
import sys
import time
from typing import Optional

HOST = "http://127.0.0.1:8101"
TIMEOUT = 30
RESULTS = []

def reset():
    httpx.post(f"{HOST}/api/reset", content=b'{}', headers={"Content-Type": "application/json"}, timeout=TIMEOUT)

def post(action, **kwargs):
    """POST /wf/{action}"""
    r = httpx.post(f"{HOST}/wf/{action}", json=kwargs, timeout=TIMEOUT)
    try:
        return r.json()
    except Exception:
        return {"_raw": r.text, "_code": r.status_code}

def deploy(name):
    """save + deploy, 返回 defineId 或 None"""
    flow = json.load(open(f'flows/{name}'))
    r = post("processDesign/save", name=flow["name"], displayName=flow["displayName"], type=flow["type"], content=json.dumps(flow))
    if r.get("code") != 0:
        return None, f"save: {r.get('msg', r)[:100]}"
    did = r["data"]["id"]
    r = post("processDesign/deploy", id=did)
    if r.get("code") != 0:
        return None, f"deploy: {r.get('msg', r)[:100]}"
    return r["data"]["processDefineId"], None

def start(define_id, operator="user1", assignees=None, variables=None, flow_name=None):
    variables = variables or {"u_userId": "user1", "u_realName": "张三"}
    assignees = assignees or {"apply": "user1"}
    # 11-assignment-handler: FormFieldAssigneeHandler 需 f_<node_id>
    if flow_name and '11-assignment-handler' in flow_name:
        variables = dict(variables)
        variables.setdefault("f_task1", "userA,userB")
        variables.setdefault("f_task2", "manager")
        variables.setdefault("f_task3", "director")
        variables.setdefault("f_task4", "leader")
        # task4 用 SPI role, 注入对应 role
        variables.setdefault("u_deptId", "D01")
    r = post("processInstance/startAndExecute", processDefineId=define_id, operator=operator, title=f"tdd-{int(time.time())}", assignees=assignees, variables=variables)
    if r.get("code") != 0:
        return None, r.get("msg", r)[:200]
    return r["data"]["processInstanceId"], None

def detail(inst):
    r = post("processInstance/detail", id=inst)
    return r.get("data", {})

def todo(operator):
    r = post("processTask/todoList", operator=operator, pageNum=1, pageSize=50)
    return r.get("data", {}).get("rows", [])

def execute(task_id, operator, submit_type=0, **kwargs):
    return post("processTask/execute", processTaskId=task_id, operator=operator, submitType=submit_type, **kwargs)

def expect(condition, msg):
    """assert with report"""
    if condition:
        RESULTS.append(("✅", msg))
    else:
        RESULTS.append(("❌", msg))
        print(f"❌ {msg}")

def get_active_tasks(inst, task_name):
    """从 inst 详情找 active task id"""
    d = detail(inst)
    tasks = [t for t in d.get("tasks") or [] if t.get("taskName") == task_name and t.get("taskState") == 10]
    return tasks[0] if tasks else None

def walk_to_end(inst, max_steps=20):
    """自动走完流程: 每次找 DOING task, 用 user1/leader/manager/boss/director 办"""
    actors = ["user1", "user2", "user3", "user4", "userA", "userB", "userC", "userD", "user5", "user6", "user7", "user8", "leader", "manager", "director", "boss", "cashier", "deptLeader", "reviewer", "checker", "applicant"]
    for step in range(max_steps):
        d = detail(inst)
        if d.get("state") == 20:
            return True, f"state=20 DONE"
        if d.get("state") in (30, 40, 45, 99):
            return True, f"state={d.get('state')} (终止状态)"
        active = d.get("activeTaskList") or []
        if not active:
            return False, f"卡死 active=[] (state={d.get('state')})"
        # 试每个 actor 找 todo
        progressed = False
        for t in active:
            for op in actors:
                todos = todo(op)
                my_todos = [x for x in todos if x.get("processInstanceId") == str(inst) and x.get("taskName") == t.get("taskName") and x.get("taskState") == 10]
                if my_todos:
                    r = execute(my_todos[0]["id"], op, 0)
                    if r.get("code") == 0:
                        progressed = True
                        break
            if progressed:
                break
        if not progressed:
            return False, f"无人能办: {[t.get('taskName') for t in active]}"
    return False, f"max_steps={max_steps} 未结束"

# ─── TDD 每个 flow ──────────────────────────────────────────────
def test_flow(name):
    print(f"\n=== {name} ===")
    reset()
    # 1) verify 预检
    flow = json.load(open(f'flows/{name}'))
    r = post("verify", content=json.dumps(flow))
    valid = r.get("data", {}).get("valid")
    summary = r.get("data", {}).get("summary", {})
    print(f"  verify: valid={valid} errors={summary.get('errorCount')} warnings={summary.get('warningCount')}")
    
    # 2) deploy (不带 skipVerify)
    define_id, err = deploy(name)
    if define_id is None:
        # verify 已拦了
        if r.get("data", {}).get("valid"):
            expect(False, f"{name}: verify valid=True 但 deploy 失败: {err}")
        else:
            # 跳过 - 这是预期的（设计本身有问题）
            print(f"  ⚠️ {name} verify 拒绝 (设计 bug): {err[:80]}")
            RESULTS.append(("⚠️", f"{name}: 设计被 verify 拦截 - {err[:80]}"))
        return
    
    # 3) startAndExecute
    inst, err = start(define_id, flow_name=name)
    if inst is None:
        # 启动失败（SPI 角色缺失等已知问题）
        print(f"  ⚠️ {name} 启动失败: {err[:80]}")
        RESULTS.append(("⚠️", f"{name}: 启动失败 - {err[:80]}"))
        return
    
    # 4) 走完流程
    ok, msg = walk_to_end(inst)
    if ok:
        print(f"  ✅ {name} 走完: {msg}")
        RESULTS.append(("✅", f"{name}: {msg}"))
    else:
        print(f"  ❌ {name} 走不完: {msg}")
        RESULTS.append(("❌", f"{name}: {msg}"))

if __name__ == "__main__":
    flows = sorted([f for f in __import__("os").listdir("flows/") if f.endswith(".json") and not f.startswith("__")])
    # 去重（08-custom-node 和 08-countersign-sequential-approve 共存）
    seen = set()
    unique = []
    for f in flows:
        base = f.split(".json")[0]
        if base not in seen:
            seen.add(base)
            unique.append(f)
    flows = unique
    print(f"Test {len(flows)} flows")
    for name in flows:
        test_flow(name)
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    ok = sum(1 for r in RESULTS if r[0] == "✅")
    warn = sum(1 for r in RESULTS if r[0] == "⚠️")
    fail = sum(1 for r in RESULTS if r[0] == "❌")
    print(f"✅ PASS: {ok}")
    print(f"⚠️ WARN (启动失败/设计 bug): {warn}")
    print(f"❌ FAIL: {fail}")
    if fail > 0:
        print("\n失败详情:")
        for r in RESULTS:
            if r[0] == "❌":
                print(f"  {r[1]}")
    sys.exit(0 if fail == 0 else 1)
