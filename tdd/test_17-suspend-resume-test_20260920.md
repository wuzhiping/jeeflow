# TDD 17: 挂起恢复测试 (2026-09-20)

## 流程定义

`flows/17-suspend-resume-test.json` (`name: suspend-resume-test`)

```
start → apply → leader_approve → manager_approve → end
```

## 测试场景

### 1. 启动 + 第一次 suspend

```bash
POST /wf/processInstance/startAndExecute {"processDefineId": 29, "operator": "user1"}
→ processInstanceId=91975972366346 (state=10 DOING)

POST /wf/processInstance/suspend {"id": "91975972366346"}
→ {"code": 0, "data": {"state": 50}}  # PENDING
```

### 2. 第一次 resume

```bash
POST /wf/processInstance/resume {"id": "91975972366346"}
→ {"code": 0, "data": {"state": 10}}  # DOING
```

### 3. 第二次 suspend + execute 校验（FIX-T56）

```bash
POST /wf/processInstance/suspend {"id": "91975972366346"}
→ {"code": 0, "data": {"state": 50}}

POST /wf/processTask/execute {"processTaskId": "91975972367372", "operator": "leader", "submitType": 1}
→ {
  "code": 99999999,
  "msg": "[ValueError] 实例 state=50 不可执行任务（仅 DOING=10 可执行）"
}
```

### 4. resume + 成功 execute

```bash
POST /wf/processInstance/resume {"id": "91975972366346"}
→ {"code": 0, "data": {"state": 10}}

POST /wf/processTask/execute {"processTaskId": "91975972367372", "operator": "leader", "submitType": 1}
→ {"code": 0, "msg": "成功"}
```

### 5. 最终状态

```bash
POST /wf/processInstance/detail {"id": "91975972366346"}
→ {
  "state": 10,
  "tasks": [
    {"taskName": "apply", "taskState": 20},
    {"taskName": "leader_approve", "taskState": 20},
    {"taskName": "manager_approve", "taskState": 10}
  ]
}
```

## 断言

| # | 断言 | 结果 |
|---|------|------|
| 1 | suspend: DOING → PENDING | ✅ |
| 2 | resume: PENDING → DOING | ✅ |
| 3 | suspended 时 execute 拒绝 | ✅ |
| 4 | resume 后 execute 成功 | ✅ |
| 5 | 流程继续推进到 manager_approve | ✅ |

## 修复关联

- **FIX-T70 §70** (vendor/jeeflow/facade.py:1486-1501 suspend + 1503-1518 resume)
- **FIX-T56 §56** (PENDING 禁止 execute)

## 状态

✅ PASS - 5/5
