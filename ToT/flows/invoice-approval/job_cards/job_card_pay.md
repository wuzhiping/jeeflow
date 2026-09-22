# Job Card · pay（出纳付款）

> **节点 ID**：`pay`
> **类型**：task
> **角色**：出纳（Treasurer）
> **所属流程**：[invoice-approval](../README.md)

---

## 1. 入口条件
- 小金额（直接到此）或大金额（approve 通过后到此）
- task.taskState = DOING

## 2. 表单字段
- 表单 Key：`pay-form`
- 字段：
  - `treasurer`（str，必填，出纳 user_id）
  - `account`（str，必填，收款账户号）
  - `paid_amount`（num，必填，实际付款金额）
  - `voucher`（str，必填，付款凭证号）
  - `paid_at`（datetime，可选，付款时间）

## 3. 操作步骤
1. 检查 actor 权限：当前操作人是否在 `task.actorIds` 中（含 treasurer role）
2. 校验表单：
   - `paid_amount == variable.amount`
   - `len(voucher) >= 5`
   - `account` 格式合法（银行卡号 Luhn 校验）
3. 构造 decision memo：
   ```json
   {
     "decision_reason": "出纳<treasurer>完成打款",
     "decision_memo": "凭证=<voucher>，收款=<account>",
     "context": {
       "treasurer": ...,
       "paid_amount": ...,
       "account": ...,
       "voucher": ...
     },
     "job_card_url": "ToT/flows/invoice-approval/job_cards/pay.md",
     "next_handoff": "end (DONE)"
   }
   ```
4. 调用 `POST /wf/processTask/execute`：
   ```json
   {
     "processTaskId": <pay_task_id>,
     "operator": "<treasurer_user_id>",
     "result": 1,
     "comment": "已打款"
   }
   ```

## 4. 边界情况
- **paid_amount != variable.amount**：警告但允许（部分付款场景）
- **voucher 已存在**：抛错（防重复付款）
- **网络超时**：retry 机制 + idempotent key

## 5. 决策 Mem（透传到 instance.variables）
```json
{
  "decision_reason": "出纳<treasurer>完成打款，付款凭证=<voucher>",
  "decision_memo": "收款账户=<account>，付款金额=<paid_amount>",
  "context": {
    "treasurer": "u_treasurer",
    "paid_amount": 6000,
    "account": "6225****1234",
    "voucher": "PAY-2026-09-23-001"
  },
  "job_card_url": "ToT/flows/invoice-approval/job_cards/job_card_pay.md",
  "next_handoff": "end (DONE)"
}
```

## 6. 出口
- taskState → DONE
- instance 推进到 `end`
- instance.state → DONE(20)

## 6. 关联文档
- [NODES.md §N5](../NODES.md) — pay 节点定义
- [RESPONSES.md §N5](../RESPONSES.md) — pay 决策模板
- [ROLES.md §R3](../ROLES.md) — 出纳角色

## 7. 测试用例
- **正常**：paid_amount=6000, voucher="PAY-001" → 完成
- **异常**：paid_amount=5000（!= 6000）→ 警告但允许
- **异常**：voucher="" → 拒绝
