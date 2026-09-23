# Job Card · approve（主管复核）

> **节点 ID**：`approve`
> **类型**：task
> **角色**：主管（Manager）
> **所属流程**：[invoice-approval](../README.md)

---

## 1. 入口条件
- 仅大金额（amount >= 5000）路径才到此节点
- task.taskState = DOING

## 2. 表单字段
- 表单 Key：`approve-form`
- 字段：
  - `approver`（str，必填，主管 user_id）
  - `comment`（str，必填，审批意见，≥ 10 字符）
  - `result`（int，必填，1=通过 / 2=驳回）

## 3. 操作步骤
1. 检查 actor 权限：当前操作人是否在 `task.actorIds` 中（含 manager role）
2. 校验表单：
   - `len(comment) >= 10`
   - `result in (1, 2)`
3. 构造 decision memo：
   ```json
   {
     "decision_reason": "主管<approver>审批<result>（通过/驳回）",
     "decision_memo": "审批意见=<comment>",
     "context": {"approver": ..., "result": 1|2, "comment": ...},
     "job_card_url": "ToT/flows/invoice-approval/job_cards/approve.md",
     "next_handoff": "treasurer (通过) / applicant (驳回)"
   }
   ```
4. 调用 `POST /wf/processTask/execute`：
   ```json
   {
     "processTaskId": <approve_task_id>,
     "operator": "<manager_user_id>",
     "result": 1,
     "submitType": 1,
     "comment": "业务真实，金额合理",
     "decision_reason": "approve 通过",
     "decision_memo": "金额合理，材料齐全"
   }
   ```

   驳回时改 `submitType` 为 5 (RE_APPLY)：
   ```json
   {
     "processTaskId": <approve_task_id>,
     "operator": "<manager_user_id>",
     "result": 2,
     "submitType": 5,
     "comment": "金额异常，需补充材料",
     "decision_reason": "approve 驳回后回到首个 task 节点",
     "decision_memo": "金额异常，需补充材料"
   }
   ```

## 4. 边界情况
- **result=2 + submitType=5（驳回）**：跳回 submit，员工可修改后重新提交（v0.4）
- **result=2 + submitType=2（REJECT）**：instance.state = REJECT(45)，流程终止（不推荐，应改用 RE_APPLY）
- **comment 太短**：拒绝执行
- **金额 < 5000 但到了此节点**：异常（决策分支 bug），需排查 decision_amount

## 5. 决策 Mem 字段（v0.7 新增 — W17）

驳回时强烈推荐传 3 个字段，让 audit 链完整：

| 字段 | 类型 | 用途 |
|------|------|------|
| `comment` | str | 简短驳回原因（显示在 UI） |
| `decision_reason` | str | 一句话原因（用于统计） |
| `decision_memo` | str | 详细 memo（≥ 20 字，含复审要求） |

**示例**：
```json
{
  "comment": "金额异常",
  "decision_reason": "approve 驳回：金额异常",
  "decision_memo": "发票金额 8000 CNY 已超出 5000 阈值，但缺少采购合同附件。请补充附件后重新提交。"
}
```

**自动保存位置**：`wf_process_instance.variable.{comment, decision_reason, decision_memo}`（由 engine `_merge_exec_into_instance` 自动处理）

## 5. 决策 Mem（透传到 instance.variables）
```json
{
  "decision_reason": "主管<approver>审批<result>（通过/驳回）",
  "decision_memo": "审批意见=<comment>",
  "context": {
    "approver": "u_manager",
    "result": 1,
    "comment": "业务真实，金额合理"
  },
  "job_card_url": "ToT/flows/invoice-approval/job_cards/job_card_approve.md",
  "next_handoff": "treasurer (通过) / applicant (驳回)"
}
```

## 6. 出口
- 通过 → `pay` 节点
- 驳回 → instance.state = REJECT，回到员工（待加 resurrect 边）

## 6. 关联文档
- [NODES.md §N4](../NODES.md) — approve 节点定义
- [RESPONSES.md §N4](../RESPONSES.md) — approve 决策模板
- [ROLES.md §R2](../ROLES.md) — 主管角色

## 7. 测试用例
- **正常**：result=1, comment="业务真实" → 通过，到 pay
- **驳回**：result=2, comment="金额异常" → REJECT
- **异常**：comment="" → 拒绝
