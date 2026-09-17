#!/usr/bin/env python3
"""BDD runner helper — 简化 detail 输出

提供 3 个 helper 用于 BDD 报告生成：

- detail(inst_id): 查询实例完整信息（state/activeTaskList/tasks/variable/formData）
- highlight(inst_id): 查询实例高亮（historyNodeNames/current）
- print_state(inst_id, label): 打印实例状态 + 任务列表 + 历史

**使用示例**：

```python
import sys
sys.path.insert(0, '/opt/jupyter/src/RD/projects/jeeFlow/bdd')
from runner import print_state

# 默认模式（仅 state + active + done tasks）
print_state('91775430336808')

# history 模式（额外打印 historyNodeNames）
print_state('91775430336808', 'history')
```

**CLI 模式**：

```bash
./venv/bin/python3 ./bdd/runner.py 91775430336808 history
```

**输出格式**：

```
  state=10 active=1
    ACTIVE: tech_review actors=['leader']
    DONE:   apply state=20 actors=['user1']
    DONE:   biz_review state=20 actors=['manager']
  history: ['apply', 'tech_review', 'biz_review', 'merge_point', 'end']
  current: None
```

**已知约束**：
- 服务必须在 8101 端口运行
- 假设内存后端（main.py）；PG 后端（main_pg.py）行为一致
- highLight 接口可能返回未访问节点（§31）

**新增 helper 提案**（如需）：
- `done_list(operator, pageNum)` — 调 `/wf/processTask/doneList`（§55 actorIdList=None）
- `todo_list(operator, pageNum)` — 调 `/wf/processTask/todoList`
- `cc_list(operator, pageNum)` — 调 `/wf/processInstance/ccList`
"""
import sys
import json
import urllib.request


def detail(inst_id):
    """查询实例 detail（state/activeTaskList/tasks/variable/formData）"""
    req = urllib.request.Request(
        "http://localhost:8101/wf/processInstance/detail",
        data=json.dumps({"id": inst_id}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read()).get("data", {})


def highlight(inst_id):
    """查询实例高亮（historyNodeNames/current）"""
    req = urllib.request.Request(
        "http://localhost:8101/wf/processInstance/highLight",
        data=json.dumps({"id": inst_id}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read()).get("data", {})


def print_state(inst_id, label=""):
    """打印实例状态 + 任务列表（label 含 'history' 时额外打印 historyNodeNames）"""
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
