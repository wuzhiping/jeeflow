# Invoice Approval · 节点工作步骤

> 每个节点的：入口条件 / 角色 / 表单字段 / 决策逻辑 / 出口处理。

---

## N1 · `start`（发起）

### 入口条件
- 任何已认证用户都可发起

### 角色
- 操作人：`operator` 字段（任意用户 ID）

### 输入
- `businessKey`（必填，业务单号如 INV-XXX）
- `title`（必填，发票标题）
- `variable.amount`（必填，发票金额，int）
- `variable.purpose`（必填，用途说明，str）
- `variable.applicant`（可选，默认 = operator）

### 处理
- 引擎自动创建 instance + 推进到 submit

### 出口
- 到达 `submit` 节点

---

## N2 · `submit`（提交发票）

### 入口条件
- 流程已发起，task 处于 DOING

### 角色
- **assignee**：员工（任意用户）

### 表单
- 表单 Key：`invoice-submit-form`
- 字段：金额 / 用途 / 附件URL / 申请人

### 操作
- 员工填写并提交
- 调用：`POST /wf/processTask/execute`
- `processTaskId`：submit task 的 ID
- `operator`：员工 user_id
- `result`：1（提交）

### 出口
- 到达 `decision_amount` 节点

### 数据传递
- `variable` 透传到 instance

---

## N3 · `decision_amount`（金额分支）

### 入口条件
- submit 已完成

### 角色
- 系统自动判断（无人工介入）

### 决策表达式
```python
#variable.amount >= 5000
```

### 路由表
| 条件 | 出口 |
|------|------|
| `#variable.amount >= 5000` | → `approve` |
| `#variable.amount < 5000` | → `pay` |

### 实现细节
- 在 Snaker 模型中，decision 节点的表达式写在 **edge** 上
- `e_big` 边：`{"expr": "#variable.amount >= 5000"}` → target=approve
- `e_small` 边：`{"expr": "#variable.amount < 5000"}` → target=pay
- 引擎按顺序评估，第一个匹配的边生效

### 出口
- 命中 approve → N4
- 命中 pay → N5

---

## N4 · `approve`（主管复核，仅大额）

### 入口条件
- `variable.amount >= 5000`

### 角色
- **assignee**：主管

### 表单
- 表单 Key：`approve-form`
- 字段：审批人 / 审批意见 / 审批时间

### 操作
- 主管审批
- 调用：`POST /wf/processTask/execute`
- `processTaskId`：approve task 的 ID
- `operator`：主管 user_id
- `result`：1（通过）/ 2（驳回）
- `comment`：必填，≥ 10 字符
- **`submitType`**：
  - `1` (AGREE)：通过 → 推进到 pay
  - `5` (RE_APPLY)：驳回 → 跳回 submit（员工可修改后重新提交）

### 驳回处理（v0.4 新增）
- 用 `submitType=5` (RE_APPLY) 而非 `submitType=2` (REJECT)
- 引擎内置 `execute_and_jump_to_first_task_node` 自动跳回 submit
- instance.state 保持 DOING（不变成 REJECT）
- 员工可在 submit 修改金额/附件后重新提交
- 历史记录完整保留（每次 submit/approve 都新建 task）

### 出口
- 通过 → `pay` 节点
- 驳回（RE_APPLY） → `submit` 节点（员工重新提交）

---

## N5 · `pay`（出纳付款）

### 入口条件
- 小金额（直接到达）或大金额（approve 通过后到达）

### 角色
- **assignee**：出纳

### 表单
- 表单 Key：`pay-form`
- 字段：收款账户 / 付款金额 / 付款时间

### 操作
- 出纳完成打款
- 调用：`POST /wf/processTask/execute`
- `processTaskId`：pay task 的 ID
- `operator`：出纳 user_id
- `result`：1（完成）
- `comment`：必填，含付款凭证号

### 出口
- 到达 `end` 节点

---

## N6 · `end`（完成）

### 入口条件
- pay 已完成

### 状态
- instance.state = DONE(20)

### 收尾
- 引擎自动调用 postInterceptors（如果有）
- 触发 `self-auditor`（未来功能）

---

## 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-23 | 初稿 —— 6 节点（start/submit/decision_amount/approve/pay/end） |
---

## Actor Resolver（v0.5 新增）

| 节点 | assignee 写法 | 解析为 | 解析机制 |
|------|--------------|--------|----------|
| `submit` | `"applicant"` | `u_alice`（发起人） | engine 内置 substring 替换 |
| `approve` | `"tf_manager"` | `vars_["tf_manager"]` 的值 | engine `_resolve_actors` 变量查表 |
| `pay` | `"tf_treasurer"` | `vars_["tf_treasurer"]` 的值 | 同上 |

### 启动时调用方式

```bash
POST /wf/processInstance/startAndExecute
{
  "processDefineId": 29,
  "operator": "u_alice",        # 发起人 → applicant 解析
  "businessKey": "INV-001",
  "variable": {                  # 嵌套业务变量
    "amount": 8000,
    "purpose": "服务器"
  },
  "tf_manager": "u_bob_manager",     # 顶级变量 → tf_manager 解析
  "tf_treasurer": "u_carol_treasurer" # 顶级变量 → tf_treasurer 解析
}
```

### ⚠️ 避坑

- **不要用 `tf_applicant`**：engine 的 `"applicant" in token` substring 替换会把 `tf_applicant` 错误变成 `tf_u_alice`！
- 正确做法：submit task 用 `"applicant"`（内置占位符），其他 task 用 `tf_*` 但避开 "applicant" 子串
