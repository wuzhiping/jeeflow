# Invoice Approval · Decision Mem 协议

> 每节点的"决策内存"格式定义。对齐 FDEP 的 v1.2 lite+ 协议。

---

## 协议字段（top-level）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `decision_reason` | str | ✅ | 为什么这样决策（1 句话） |
| `decision_memo` | str | ⭕ | 详细备注（限制 500 字） |
| `context` | dict | ⭕ | 决策上下文（变量快照） |
| `job_card_url` | str | ✅ | 对应 Job Card 的相对路径 |
| `next_handoff` | str | ✅ | 下一节点的角色 |

---

## N2 · `submit` 决策模板

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

---

## N3 · `decision_amount` 决策模板

```json
{
  "decision_reason": "金额分支：<amount> >= 5000 走 approve，< 5000 走 pay",
  "decision_memo": "阈值 5000 是公司报销分级标准",
  "context": {
    "amount": 6000,
    "matched_edge": "e_big",
    "target_node": "approve"
  },
  "job_card_url": "ToT/flows/invoice-approval/job_cards/job_card_decision_amount.md",
  "next_handoff": "manager (大额) / treasurer (小额)"
}
```

---

## N4 · `approve` 决策模板

```json
{
  "decision_reason": "主管<manager>审批<result>（通过/驳回）",
  "decision_memo": "审批意见=<comment>",
  "context": {
    "approver": "u_manager",
    "result": 1,  # 1=通过 2=驳回
    "comment": "业务真实，金额合理"
  },
  "job_card_url": "ToT/flows/invoice-approval/job_cards/job_card_approve.md",
  "next_handoff": "treasurer (通过) / applicant (驳回)"
}
```

---

## N5 · `pay` 决策模板

```json
{
  "decision_reason": "出纳<treasurer>完成打款",
  "decision_memo": "收款账户=<account>，付款凭证=<voucher>",
  "context": {
    "treasurer": "u_treasurer",
    "amount": 6000,
    "account": "6225****1234",
    "voucher": "PAY-2026-09-23-001"
  },
  "job_card_url": "ToT/flows/invoice-approval/job_cards/job_card_pay.md",
  "next_handoff": "end (DONE)"
}
```

---

## 协议透传机制

决策 mem 通过 `facade.py:713` 的透传机制，从 task.variables 进入 instance.variables，可被下游节点读取。

测试代码：
```python
import requests
r = requests.post("http://127.0.0.1:8101/wf/processInstance/detail",
                  json={"id": "<instance_id>"})
vars_ = r.json()['data']['variables']
print(vars_.get('decision_reason'))
```

---

## 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-23 | 初稿 —— 4 节点决策模板（submit/decision/approve/pay），对齐 FDEP v1.2 lite+ |