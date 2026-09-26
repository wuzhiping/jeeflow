# 设计模式 05 · 条件分支

> **场景**：根据申请字段自动走不同分支（金额 / 类型 / 部门）
> **依据**：`vendor/jeeflow/engine.py` decision 节点 + SPI `ExpressionEvaluator`

---

## 1. Decision 节点

**类型**：`type=DECISION`

**行为**：根据表达式求值，选择下一个节点（通过 `edges` 的 `expr` 匹配）

**配置**：
```json
{
  "nodeId": "amount_branch",
  "type": "DECISION",
  "expression": "vars.amount > 10000 ? 'big' : 'small'",
  "edges": [
    {"targetNodeId": "ceo_approve", "expr": "vars.amount > 10000", "text": {"value": "大额"}},
    {"targetNodeId": "manager_approve", "expr": "vars.amount <= 10000", "text": {"value": "小额"}}
  ]
}
```

---

## 2. 4 种条件策略

### 2.1 金额分支

```python
# 报销：1000 元以下自动过
amount_branch
  ├ < 1000     → auto_approve（自动审批）
  ├ 1000-10000 → manager_approve（经理审批）
  └ > 10000    → ceo_approve（CEO 审批）
```

### 2.2 类型分支

```python
# 请假：根据类型走不同流程
type_branch
  ├ sick       → simple_leave（1 天假自动过）
  ├ annual     → normal_leave（2 级审批）
  └ personal   → strict_leave（3 级审批）
```

### 2.3 部门分支

```python
# 报销：根据部门走不同审批
dept_branch
  ├ sales      → sales_manager（销售部经理）
  ├ finance    → finance_director（财务总监）
  └ others     → default_manager（默认）
```

### 2.4 动态分支（运行时决策）

**用 SPI `ExpressionEvaluator`**：

```python
extensions.decision_handler(my_custom_decide)

async def my_custom_decide(flow, instance, vars):
    if vars.get("amount", 0) > 100000:
        return "ceo_approve"  # 100 万以上走 CEO
    elif vars.get("is_urgent"):
        return "urgent_path"  # 加急路径
    return "default_path"
```

详见 [`../spec/extension-hooks.md §6 决策 handler`](../spec/extension-hooks.md)

---

## 3. 表达式语法

**支持的变量**：
- `vars.amount`：`args` 里的字段
- `vars.applicantDeptId`：发起人部门 ID
- `vars.processDefineName`：流程定义名

**支持的运算符**：
- 比较：`>`, `<`, `>=`, `<=`, `==`, `!=`
- 逻辑：`and`, `or`, `not`
- 三元：`? :`

**示例**：
```python
"vars.amount > 1000 and vars.is_urgent"
"vars.applicantDeptId == 'D001'"
"vars.days >= 7 ? 'long' : 'short'"
```

---

## 4. 节点配置完整示例

```json
{
  "processDefineId": 200,
  "name": "报销审批（条件分支）",
  "nodes": [
    {"nodeId": "start", "type": "start"},
    {
      "nodeId": "amount_branch",
      "type": "DECISION",
      "edges": [
        {"targetNodeId": "auto_approve", "expr": "vars.amount <= 1000"},
        {"targetNodeId": "manager_approve", "expr": "vars.amount > 1000 and vars.amount <= 10000"},
        {"targetNodeId": "ceo_approve", "expr": "vars.amount > 10000"}
      ]
    },
    {
      "nodeId": "auto_approve",
      "type": "task",
      "taskType": "NOTIFY",
      "assignmentHandler": "TaskRoleAssigneeHandler",
      "args": {"role": "applicant"},
      "autoExecute": true
    },
    {
      "nodeId": "manager_approve",
      "type": "task",
      "taskType": "APPROVE",
      "assignmentHandler": "ApplicantDeptLeaderAssignmentHandler"
    },
    {
      "nodeId": "ceo_approve",
      "type": "task",
      "taskType": "APPROVE",
      "assignmentHandler": "TaskRoleAssigneeHandler",
      "args": {"role": "ceo"}
    },
    {"nodeId": "cc_notice", "type": "task", "taskType": "CC"},
    {"nodeId": "end", "type": "end"}
  ]
}
```

---

## 5. 风险点

| 风险 | 影响 |
|---|---|
| 表达式语法错 | 流程直接卡住 |
| 变量未定义 | 求值失败 → 走 default 分支 |
| 多个分支都满足 | 走第一个匹配的 |
| 没有 default 分支 | 卡死 |

---

## 6. 调试技巧

```bash
# 1. 看实例当前节点
curl -sX POST http://localhost:8101/wf/processInstance/detail \
  -d '{"processInstanceId":1001}' | jq '.currentNode'

# 2. 看表达式求值日志（如果有）
grep "DECISION.*expr" /var/log/jeeFlow/app.log

# 3. 高亮路径
curl -sX POST http://localhost:8101/wf/processInstance/highLight \
  -d '{"processInstanceId":1001}' | jq
```

---

## 7. 与其他模式组合

| 组合 | 适用 |
|---|---|
| 条件分支 + 多级审批 | 模式 02 |
| 条件分支 + 会签 | 大额 + 财务+法务会签 |
| 条件分支 + 驳回 | draft send to wrong dept → 驳回到 start |

---

## 8. 反模式

❌ **5+ 个分支**：可读性差，建议拆 2 个 processDefine
❌ **表达式依赖外部状态**：外部状态变了行为就变
❌ **没有 default 分支**：必卡死
❌ **金额阈值硬编码**：必须用 SPI 提取

---

## 9. 验收 checklist

- [ ] `verify_flow` 通过
- [ ] 3 个分支都覆盖（小额 / 中额 / 大额）
- [ ] default 分支存在
- [ ] `processInstance/highLight` 正确高亮走过的节点
- [ ] KPI 字典加入「分支命中率」

---

**版本**：v1.11.5 · **来源**：02 plan A2 W2 末 · 与 concepts/03-execution-engine.md §1 联动