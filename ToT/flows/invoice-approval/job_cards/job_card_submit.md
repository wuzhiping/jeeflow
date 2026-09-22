# Job Card · submit（提交发票）

> **节点 ID**：`submit`
> **类型**：task
> **角色**：员工（Employee）
> **所属流程**：[invoice-approval](../README.md)

---

## 1. 入口条件
- 流程已发起（instance.state = DOING）
- submit task 在 actor list 中（task.taskState = DOING）

## 2. 表单字段
- 表单 Key：`invoice-submit-form`
- 字段：
  - `amount`（int，必填，发票金额 CNY）
  - `purpose`（str，必填，用途说明，≥ 5 字符）
  - `attach_url`（str，可选，发票图片 URL）
  - `applicant`（str，必填，员工 user_id，应等于当前操作人）

## 3. 操作步骤
1. 检查 actor 权限：当前操作人是否在 `task.actorIds` 中（含 employee role）
2. 校验表单字段：
   - `amount >= 0`
   - `len(purpose) >= 5`
   - `applicant == operator`
3. 构造 decision memo：
   ```json
   {
     "decision_reason": "员工提交发票，金额=<amount>",
     "decision_memo": "用途=<purpose>",
     "context": {"amount": ..., "purpose": ..., "applicant": ...},
     "job_card_url": "ToT/flows/invoice-approval/job_cards/submit.md",
     "next_handoff": "system (decision_amount)"
   }
   ```
4. 调用 `POST /wf/processTask/execute`：
   ```json
   {
     "processTaskId": <submit_task_id>,
     "operator": "<user_id>",
     "result": 1,
     "comment": "提交发票",
     "variable": {...decision_memo...}
   }
   ```

## 4. 边界情况
- **金额 < 0**：拒绝执行，提示"金额必须 ≥ 0"
- **applicant != operator**：拒绝，提示"申请人必须等于操作人"
- **purpose 太短**：拒绝，提示"用途说明至少 5 字符"

## 5. 决策 Mem（透传到 instance.variables）
```json
{
  "decision_reason": "员工提交发票，金额=<amount>，用途=<purpose>",
  "decision_memo": "附件=<attach_url>，申请人=<applicant>",
  "context": {
    "amount": 6000,
    "purpose": "服务器采购",
    "applicant": "u_alice"
  },
  "job_card_url": "ToT/flows/invoice-approval/job_cards/job_card_submit.md",
  "next_handoff": "system (decision_amount)"
}
```

## 6. 出口
- taskState → DONE
- instance 推进到 `decision_amount`
- `variable` 写入 instance.variables（key: variable, 含 amount/purpose/applicant）

## 6. 关联文档
- [NODES.md §N2](../NODES.md) — submit 节点定义
- [RESPONSES.md §N2](../RESPONSES.md) — submit 决策模板
- [ROLES.md §R1](../ROLES.md) — 员工角色

## 7. 测试用例
- **正常**：amount=500 → 成功提交，进入决策
- **异常**：amount=-1 → 拒绝
- **异常**：purpose="x" → 拒绝
