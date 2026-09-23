# Job Card · decision_amount（金额分支）

> **节点 ID**：`decision_amount`
> **类型**：decision
> **角色**：系统自动判断
> **所属流程**：[invoice-approval](../README.md)

---

## 1. 入口条件
- submit 已完成（taskState = DONE）
- instance.variables.variable.amount 已写入

## 2. 决策表达式
```python
#variable.amount >= 5000
```

## 3. 路由表
| 条件 | 出口边 | 目标节点 |
|------|--------|----------|
| `#variable.amount >= 5000` | `e_big` | `approve` |
| `#variable.amount < 5000` | `e_small` | `pay` |

## 4. 操作步骤（引擎自动执行）
1. 引擎读取 `instance.variables.variable.amount`
2. 遍历 decision_amount 的所有出边（按顺序）
3. 对每条边的 `properties.expr` 求值
4. 第一个匹配的边生效（其他边清理孤儿 task，FIX-T112）
5. 推进到目标节点

## 5. 边界情况
- **所有 expr 评估失败**：兜底走第一条边 + 记录 WARN 日志（FIX-T112）
- **amount 缺失**：所有 expr 求值为 false，走第一条边（默认大金额路径，需人工修复 amount 缺失 bug）
- **amount 类型异常**：抛 ValueError（FIX-T1）

## 6. 出口
- 命中 e_big → `approve`（主管复核）
- 命中 e_small → `pay`（出纳付款，跳过复核）

## 5. 决策 Mem（透传到 instance.variables）
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

## 8. 关联文档
- [NODES.md §N3](../NODES.md) — decision 节点定义
- [RESPONSES.md §N3](../RESPONSES.md) — decision 决策模板
- [engine.py _evaluate_decision](../../../../vendor/jeeflow/engine.py) — 引擎实现
