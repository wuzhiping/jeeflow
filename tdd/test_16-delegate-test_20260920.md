# TDD 16: 任务委派测试 (2026-09-20)

## 流程定义

`flows/16-delegate-test.json` (`name: delegate-test`)

```
start → apply → leader_approve → end
```

## 节点配置

| 节点 | type | assignee | 备注 |
|---|---|---|---|
| start | snaker:start | — | — |
| apply | snaker:task | applicant | 发起人（auto） |
| leader_approve | snaker:task | leader | 测试委派目标 |
| end | snaker:end | — | — |

## 测试场景

### 1. delegate leader → boss

```bash
POST /wf/processTask/delegate
{"processTaskId": "91975961176073", "operator": "leader", "targetUserId": "boss"}

→ {
  "code": 0,
  "data": {
    "taskId": "91975961176073",
    "delegated": "leader",
    "to": "boss",
    "actors": ["leader", "boss"]
  }
}
```

### 2. boss 通过 delegate 代办

```bash
POST /wf/processTask/execute
{"processTaskId": "91975961176073", "operator": "boss", "submitType": 1}

→ {"code": 0, "msg": "成功"}
```

### 3. 错误用法：operator 不在 actorIds

```bash
POST /wf/processTask/delegate
{"processTaskId": "...", "operator": "randomUser", "targetUserId": "boss"}

→ {"code": 99999999, "msg": "[ValueError] operator randomUser 不在 task actorIds 中"}
```

## 断言

| # | 断言 | 结果 |
|---|------|------|
| 1 | delegate 端点接受 operator + targetUserId | ✅ |
| 2 | actorIds 扩展为 [leader, boss] | ✅ |
| 3 | boss 通过 delegate execute 成功 | ✅ |
| 4 | 校验：operator 必须在 actorIds | ✅ |
| 5 | instance state=20 DONE | ✅ |

## 修复关联

- **FIX-T69 §69** (vendor/jeeflow/facade.py:1597-1635 + engine.py:711-720)

## 状态

✅ PASS - 5/5
