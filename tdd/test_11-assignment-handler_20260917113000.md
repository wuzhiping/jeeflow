# 11-assignment-handler 回归测试（SPI 修复后）

- **测试时间**：2026-09-17 11:30:00
- **测试类型**：回归（修复后）
- **关联流程**：`./flows/11-assignment-handler.json`
- **关联已知问题**：`./docs/known-issues.md §18`
- **前置报告**：`./tdd/test_11-assignment-handler_20260917105500.md` ⚠️ PARTIAL

## 目标

复盘 §18：补齐 SPI demo 数据（`task4`/`finance` role）后重测，确认 4 个 handler 全部 PASS。

## 修复

### `./spi/demo/DEMO_ROLES.json`

```diff
  "leader": "组长",
  "manager": "经理",
  "director": "总监",
+ "finance": "财务部",
+ "task4": "任务节点4角色"
```

### `./spi/demo/DEMO_ROLE_TO_USERS.json`

```diff
  "leader": ["leader"],
  "manager": ["manager"],
  "director": ["director"],
  "boss": ["boss"],
+ "finance": ["leader", "manager"],
+ "task4": ["userC"]
```

## 验证步骤

### 1. 重启服务（载入新 JSON）

```bash
kill 3378915 2>/dev/null; sleep 2
cd /opt/jupyter/src/RD/projects/jeeFlow
JEEFLOW_PG_DSN="postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm" \
nohup ./venv/bin/python3 main.py > /tmp/jeeflow.log 2>&1 &
```

健康检查：`/healthz` → `{"status":"UP","backend":"python"}` ✅

### 2. 部署流程

`processDefineId=13`（复用前次 deploy 定义，name=assignment-handler）

### 3. 启动实例

```bash
curl -s -X POST http://localhost:8101/wf/processDefine/startAndExecute \
  -H "Content-Type: application/json" \
  -d '{
    "processDefineId": 13,
    "assignees": "user1",
    "operator": "user1",
    "variables": {"f_task1":"user1","f_task2":"user1","f_task3":"user1","u_userId":"user1","u_deptId":"D01"},
    "title": "11-spi-fixed"
  }'
```

→ `processInstanceId=91763197264992`

### 4. 推进各 task

| 步骤 | task | operator | processTaskId | 响应 |
|---|---|---|---|---|
| 1 | task1 | user1 | 91763197267042 | code=0 ✅ |
| 2 | task2 | user1 | 91763197903971 | code=0 ✅ |
| 3 | task3 | leader | 91763198260324 | code=0 ✅ |
| 4 | task4 | userC | — | code=0 ✅ |

### 5. 终态校验

`processInstance/detail` 终态：

```
state=20 (DONE) active=0
task=task1 state=20 actorIds=['user1']
task=task2 state=20 actorIds=['user1']
task=task3 state=20 actorIds=['leader']
task=task4 state=20 actorIds=['userC']   ← ✅ SPI 修复后 userC 正确解析
```

`processInstance/highLight`：

```
historyNodeNames = [task1, task2, task3, task4, end]
nodeProgress = {
  task1: {members: [{id: user1, name: 张三, done: true}]},
  task2: {members: [{id: user1, name: 张三, done: true}]},
  task3: {members: [{id: leader, name: 李四, done: true}]},
  task4: {members: [{id: userC, name: 吴婷, done: true}]}
}
```

`processInstance/approvalRecord`：4 条记录，operator 顺序 = user1 / user1 / leader / userC ✅

## 4 handler 实测对照

| Handler | 节点 | actorIds | 状态 |
|---|---|---|---|
| FormFieldAssigneeHandler | task1 | `['user1']`（f_task1=user1） | ✅ |
| OperatorAssignmentHandler | task2 | `['user1']`（inst.operator） | ✅ |
| DeptLeaderAssignmentHandler | task3 | `['leader']`（D01 leader） | ✅ |
| TaskRoleAssigneeHandler | task4 | `['userC']`（role=task4 → userC） | ✅ |

## 关键发现

### SPI 数据加载机制澄清

- `data.py` 模块级 dict 在 main.py **启动时一次性 `_load()` JSON** → 启动后内存中已含新数据
- `spi/__init__.py:15 SPI()` 重载 `func` 模块（如 find_by_role）
- func 模块重新执行 `from spi.demo.data import SPI_ROLE_TO_USERS` 时，Python 重新从 data 模块**已加载的命名空间**读取属性 → 拿到启动时已包含 task4 的 dict
- **结论**：JSON 修改后**必须重启服务**才生效；仅 reload func 模块**不足**，因为 data 模块级属性未变

### TaskRoleAssigneeHandler 行为

`builtin.py:135-144` 中 `assign(node)` 直接调 `org_prov.find_by_role(node.id)`，不读 `vars_`。**role_code 绑定 node.id**，因此流程设计时需为每个用此 handler 的 task 节点单独注册 role。

## 结论

✅ **PASS** — 4/4 handler 全部正确解析 actors，流程推进至 state=20 DONE。

## 关联变更

- `./spi/demo/DEMO_ROLES.json` +2
- `./spi/demo/DEMO_ROLE_TO_USERS.json` +2
- `./docs/known-issues.md §18` 标"已修复"
- `./flows/README.md` 11 行状态更新
