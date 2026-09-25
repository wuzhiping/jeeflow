# 设计模式 02 · 多级 + 跳转

> **场景**：3 级以上审批需要「跳转到任意节点」（驳回 / 撤回 / 跨级跳转）
> **依据**：`vendor/jeeflow/facade.py:1521 _processTask_jumpAbleTaskNameList`（已实现）+ `:461 rollback`

---

## 1. 节点跳转 vs 实例撤回

| 维度 | 节点跳转 (jump) | 实例撤回 (withdraw) |
|---|---|---|
| 操作人 | 当前 task 审批人 | 流程发起人 |
| 跳转范围 | 当前 task → 任意前置 task | 整个实例 |
| API | `processTask/execute` with `submitType=JUMP` | `processInstance/withdraw` |
| 数据保留 | 保留全部历史 + 字段 | 保留全部历史 + 字段 |
| 限制 | 只能在当前 task 跳转 | 必须 RUNNING + 我是发起人 |

---

## 2. 3 级审批 + 跳转示例

```
                  ┌─────────────┐
                  │   start     │
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
            ┌─────┤  lead_approv├─────┐
            │     └──────┬──────┘     │
       JUMP_TO_LEAD     AGREE       │
            │            │           │
            │     ┌──────▼──────┐    │
            │     │dept_approve │    │
            │     └──────┬──────┘    │
            │            │           │
            │     ┌──────▼──────┐    │
            │     │  hr_record  │    │
            │     └──────┬──────┘    │
            │            │           │
            ▼     ┌──────▼──────┐    │
        [回到 start]    │  end       │    │
                       └────────────┘    │
            ▲                            │
            └────────────────────────────┘
                  JUMP_TO_LEAD
```

**3 级 + 跳转节点配置**：

```json
{
  "nodes": [
    {"nodeId": "start", "type": "start"},
    {
      "nodeId": "lead_approve",
      "type": "task",
      "taskType": "APPROVE",
      "assignmentHandler": "ApplicantDeptLeaderAssignmentHandler",
      "allowJump": true
    },
    {
      "nodeId": "dept_approve",
      "type": "task",
      "taskType": "APPROVE",
      "assignmentHandler": "ApplicantDeptMainLeaderAssignmentHandler",
      "allowJump": true
    },
    {
      "nodeId": "hr_record",
      "type": "task",
      "taskType": "NOTIFY"
    },
    {"nodeId": "end", "type": "end"}
  ]
}
```

---

## 3. 跳转 API 用法

### 3.1 获取可跳转节点列表

```bash
curl -sX POST http://localhost:8101/wf/processTask/jumpAbleTaskNameList \
  -H "Content-Type: application/json" \
  -d '{"processTaskId":12345}' | jq
```

**返回**：
```json
{
  "code": 0,
  "data": [
    {"taskName": "lead_approve", "nodeName": "直属领导审批"},
    {"taskName": "start", "nodeName": "申请人提交"}
  ]
}
```

### 3.2 执行跳转

```bash
curl -sX POST http://localhost:8101/wf/processTask/execute \
  -H "Content-Type: application/json" \
  -d '{
    "processTaskId":12345,
    "operator":"dept_leader",
    "submitType":"JUMP",
    "args":{"targetTaskName":"lead_approve"},
    "comment":"数据有误，请直属领导重审"
  }' | jq
```

---

## 4. 何时用跳转 vs 驳回

| 场景 | 用跳转 | 用驳回 |
|---|---|---|
| 数据错误，需要领导重看 | ✅ JUMP_TO_LEAD | ❌ |
| 流程方向错，要回到中间 | ✅ | ❌ |
| 整个流程作废 | ❌ | ✅ REJECT_TO_START |
| 申请人重写申请 | ❌ | ✅ REJECT_TO_START |

**关键差异**：
- 跳转：保留 task 完成历史
- 驳回：保留驳回意见 + 强制重新审批

---

## 5. 权限校验

`engine.py:_is_jump_allowed`（类似 `_is_delegate_allowed`）：

- 只有当前 task 的 `assignmentHandler` 解析的参与者能跳转
- 跳转目标必须是历史已完成的节点
- 不能跳转到后续节点（避免绕过审批）

---

## 6. 反模式

❌ **所有人都能跳转**：必须限制为当前 task 的参与者
❌ **跳转到 end**：直接结束流程等于终止，应该用 `terminate`
❌ **频繁跳转**：体验差，建议改流程定义
❌ **跳转不带 comment**：审计无法追踪原因

---

## 7. 验收 checklist

- [ ] `processTask/jumpAbleTaskNameList` 返回列表正确
- [ ] 跳转后状态变 `RUNNING`（不是 `REJECTED`）
- [ ] 历史保留（`processInstance/approvalRecord` 完整）
- [ ] `/api/admin/trace` 记录跳转事件
- [ ] FAQ 中加入「跳转」说明

---

**版本**：v1.11.5 · **来源**：02 plan A2 W2 末 · 与 03 decision-tree.md §3 联动