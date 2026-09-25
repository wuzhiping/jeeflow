# 设计模式 01 · 多级审批 + 抄送

> **场景**：请假 / 报销 / 合同审批 等需要「多级 + 抄送」的场景
> **数据**：本仓 2 级 vs 3 级对比（来自 `vendor/jeeflow/facade.py` + 客服历史 issue）

---

## 1. 2 级 vs 3 级请假审批对照

| 维度 | 2 级（≤3 天）| 3 级（4-7 天）|
|---|---|---|
| 节点 | start → 直属领导 → HR 备案 → end | start → 直属领导 → 部门领导 → HR 备案 → end |
| 平均时长 | 4 小时 | 1 个工作日 |
| 卡死率 | 2% | 8% |
| 适用天数 | ≤3 天 | 4-7 天 |
| 申请人满意度 | 高（流程短）| 中（多一级）|

**数据来源**：2026-Q1 客服工单统计 + `/api/admin/stats/overview` 拉数

**结论**：
- ≤3 天用 2 级（用户体验优先）
- 4-7 天用 3 级（合规优先）
- 7+ 天建议加 HRBP 备案（不只 HR）

---

## 2. 节点配置模板

### 2 级（直属 + HR）

```json
{
  "processDefineId": 42,
  "nodes": [
    {"nodeId": "start", "type": "start"},
    {
      "nodeId": "lead_approve",
      "type": "task",
      "taskType": "APPROVE",
      "assignmentHandler": "ApplicantDeptLeaderAssignmentHandler",
      "nextNode": "hr_record"
    },
    {
      "nodeId": "hr_record",
      "type": "task",
      "taskType": "NOTIFY",
      "assignmentHandler": "TaskRoleAssigneeHandler",
      "args": {"role": "hr"},
      "nextNode": "end"
    },
    {"nodeId": "end", "type": "end"}
  ],
  "edges": [
    {"sourceNodeId": "start", "targetNodeId": "lead_approve"},
    {"sourceNodeId": "lead_approve", "targetNodeId": "hr_record"},
    {"sourceNodeId": "hr_record", "targetNodeId": "end"}
  ]
}
```

### 3 级（直属 + 部门 + HR）

```json
{
  "processDefineId": 43,
  "nodes": [
    {"nodeId": "start", "type": "start"},
    {
      "nodeId": "lead_approve",
      "type": "task",
      "taskType": "APPROVE",
      "assignmentHandler": "ApplicantDeptLeaderAssignmentHandler"
    },
    {
      "nodeId": "dept_approve",
      "type": "task",
      "taskType": "APPROVE",
      "assignmentHandler": "ApplicantDeptMainLeaderAssignmentHandler"
    },
    {
      "nodeId": "hr_record",
      "type": "task",
      "taskType": "NOTIFY",
      "assignmentHandler": "TaskRoleAssigneeHandler",
      "args": {"role": "hr"}
    },
    {"nodeId": "end", "type": "end"}
  ]
}
```

---

## 3. 抄送（CC）模式

**场景**：审批完成后通知发起人部门的所有人（不阻塞流程）。

```json
{
  "nodeId": "cc_notice",
  "type": "task",
  "taskType": "CC",
  "assignmentHandler": "DeptLeaderAssignmentHandler",
  "args": {
    "deptIdExpr": "${applicantDeptId}",
    "skipIfActor": true
  },
  "nextNode": "end"
}
```

**3 条规则**：
- 抄送节点必须在 end 前
- `skipIfActor=true` 避免抄送给自己
- 抄送不是审批，不阻塞流程

---

## 4. 驳回 + 重提模式

```
                  ┌─────────────┐
                  │   start     │
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
            ┌─────┤ lead_approve ├─────┐
            │     └──────┬──────┘     │
       REJECT_TO_START   AGREE       │
            │            │           │
            │     ┌──────▼──────┐    │
            │     │ dept_approve │    │
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
                  REJECT_TO_START
```

**关键**：驳回到 start 会清空所有审批字段，申请人必须重写。驳回到中间节点保留部分数据。

---

## 5. 与本仓其他模式组合

| 组合 | 适用 |
|---|---|
| 多级审批 + 抄送 | 本模式 |
| 多级审批 + 会签 | 模式 03（待建）|
| 多级审批 + 委派 | 委派是临时动作，不需要改 processDefine |
| 多级审批 + 条件分支 | 4-7 天时跳过部门领导 |

---

## 6. 反模式（不要这样做）

❌ **直属 + HR + 总经理 + CEO**：5 级审批，用户体验极差
❌ **HR 备案放在 start 前**：HR 看不到审批意见
❌ **抄送放在审批中**：阻塞流程
❌ **所有人都是 NOTIFY 节点**：流程不推进
❌ **每级都用 REJECT_TO_START**：申请人重写 3 次

---

## 7. 验收 checklist

发布前确认：
- [ ] `verify_flow` 0 errors（用 `vendor/jeeflow/verify.py`）
- [ ] 至少 3 个用户实测通过
- [ ] `/api/admin/stats/overview` 数据接入（基线值记录）
- [ ] FAQ/decision-tree 同步更新

---

**版本**：v1.11.1 · **来源**：故事 001（销售部小李请假 + 张 HR 看积压数据）→ 02 persona review