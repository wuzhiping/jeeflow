# Invoice Approval 流程总览

## 流程概览

**目的**：规范公司内部发票审批流程，确保财务合规、控制付款风险。

**适用场景**：员工因公支出后提交发票申请，金额自动判定审批级别（小额直接付款，大额需主管复核）。

**业务价值**：
- 减少人工判断审批级别的成本
- 提高小额发票处理效率（不需要每次都找主管）
- 保留大额发票的合规审批链

---

## 节点清单（5 个，含决策）

| ID | 名称 | 类型 | 角色 | 出口 |
|----|------|------|------|------|
| `start` | 任意员工发起 | start | - | submit |
| `submit` | 提交发票 | task | 员工 | decision_amount |
| `decision_amount` | 金额分支（≥5000 需复核） | decision | - | approve (大) / pay (小) |
| `approve` | 主管复核（≥5000） | task | 主管 | pay |
| `pay` | 出纳付款 | task | 出纳 | end |
| `end` | 完成 | end | - | - |

---

## 角色清单（3 个）

| 角色 | 职责 | 出现在 |
|------|------|--------|
| **员工** | 填写发票申请单（金额/用途/附件） | submit |
| **主管** | 复核大额发票（≥5000） | approve |
| **出纳** | 完成打款 | pay |

---

## 决策路由

```
submit (员工提交)
   ↓
decision_amount: #variable.amount >= 5000 ?
   ├─ true  → approve (主管复核) → pay (出纳付款) → end
   └─ false → pay (出纳付款) → end
```

---

## 关键变量

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `variable.amount` | int | 发票金额（CNY） |
| `variable.purpose` | str | 用途说明 |
| `variable.applicant` | str | 申请人 ID |
| `businessKey` | str | 业务单号（如 INV-XXX） |

---

## 决策逻辑

**金额阈值**：5000 CNY
- `< 5000`：跳过审批环节，出纳直接打款（小额信任机制）
- `>= 5000`：必须主管复核后才付款（合规要求）

**理由**：5000 是常见公司报销分级标准，可按实际业务调整。

---

## 数据流向

```
start
  ↓ operator=u_alice
submit
  ↓ variable.amount=6000, variable.purpose="..."
decision_amount
  ↓ 选 approve (因为 >= 5000)
approve
  ↓ operator=flow.auto (主管)
pay
  ↓ operator=flow.auto (出纳)
end (state=20 DONE)
```

---

## 版本记录

详见 [`CHANGELOG.md`](./CHANGELOG.md)。

---

## Job Card 索引

详见 [`job_cards/`](./job_cards/) 子目录（每节点 1 张执行器手册）。

| 节点 | 文件 |
|------|------|
| submit | `submit.md` |
| decision_amount | `decision_amount.md` |
| approve | `approve.md` |
| pay | `pay.md` |

---

## 关联文档

- [`ROLES.md`](./ROLES.md) — 详细角色定义
- [`NODES.md`](./NODES.md) — 每个节点的工作步骤
- [`RESPONSES.md`](./RESPONSES.md) — Decision Mem 协议
- [`CHANGELOG.md`](./CHANGELOG.md) — 变更日志