# 设计模式 04 · 驳回 + 循环

> **场景**：需要驳回 + 申请人重提 + 循环审批的流程
> **依据**：`vendor/jeeflow/facade.py:461 _processInstance_rollback` + `:565 withdraw` + `engine.py` 驳回判定

---

## 1. 驳回 3 种类型

| `submitType` | 行为 | 数据保留 | 适用 |
|---|---|---|---|
| `REJECT_TO_START` | 整个流程作废，申请人重写 | 保留驳回意见；字段清空 | 申请人填错 |
| `REJECT_TO_NODE` | 跳到指定中间节点 | 保留驳回意见 + 部分字段 | 领导要中间人重审 |
| `REJECT`（默认）| 整个流程作废 | 同 `REJECT_TO_START` | 同上 |

---

## 2. 驳回状态机

```
              ┌─────────────┐
              │   start     │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
        ┌─────┤  lead_approv├─────┐
        │     └──────┬──────┘     │
   REJECT_TO_START   AGREE       │
        │            │           │
        ▼     ┌──────▼──────┐    │
    [回到 start]│dept_approve │    │
              └──────┬──────┘    │
                     │           │
              ┌──────▼──────┐    │
              │  hr_record  │    │
              └──────┬──────┘    │
                     │           │
              ┌──────▼──────┐    │
              │  end        │    │
              └─────────────┘    │
        ▲                       │
        └───────────────────────┘
            REJECT_TO_NODE
```

---

## 3. 驳回 API

### 3.1 驳回到 start

```bash
curl -sX POST http://localhost:8101/wf/processTask/execute \
  -H "Content-Type: application/json" \
  -d '{
    "processTaskId":12345,
    "operator":"dept_leader",
    "submitType":"REJECT_TO_START",
    "comment":"请假天数超出本月剩余额度"
  }' | jq
```

**副作用**：
- `processInstance.state` = `REJECTED`
- 后续 task 全部 CANCELLED
- 申请人收到通知

### 3.2 驳回到中间节点

```bash
curl -sX POST http://localhost:8101/wf/processTask/execute \
  -H "Content-Type: application/json" \
  -d '{
    "processTaskId":12345,
    "operator":"hr",
    "submitType":"REJECT_TO_NODE",
    "args":{"targetNodeId":"lead_approve"},
    "comment":"请直属领导重新核对"
  }' | jq
```

**副作用**：
- 流程回到 `lead_approve` 节点
- 后续 task CANCELLED
- 历史完整保留

---

## 4. 撤回 vs 驳回

| 维度 | 撤回（withdraw）| 驳回（reject）|
|---|---|---|
| 操作人 | 发起人 | 审批人 |
| API | `processInstance/withdraw` | `processTask/execute` REJECT_* |
| 限制 | 仅发起人 + RUNNING | 仅当前 task 参与者 |
| 流程方向 | 整个流程作废 | 驳回到任意节点 |

**典型场景**：
- 申请人发现填错了 → 撤回
- 审批人认为需要重审 → 驳回

---

## 5. 循环审批（自循环）

**陷阱场景**：
```
申请人 → 直属领导 → 部门领导 → 财务 → 直属领导 → 部门领导 → ...
         ↑___________________________________↓
                 财务驳回到直属领导
```

**问题**：
- 流程可能无限循环
- 浪费审批资源
- 申请人体验差

**解决方案**：
1. **限制最大驳回次数**：在 processDefine 配置 `maxRejectLoop=2`
2. **驳回必填 comment**：强制审批人说明理由
3. **加 KPI 监控**：循环次数 > 3 触发告警

**引擎行为**（待确认是否已实现）：
```python
if reject_loop_count > MAX_LOOP:
    return ERROR_TOO_MANY_LOOPS
```

---

## 6. 驳回记录查询

```bash
curl -sX POST http://localhost:8101/wf/processInstance/approvalRecord \
  -H "Content-Type: application/json" \
  -d '{"processInstanceId":1001}' | jq
```

**返回**：
```json
{
  "code": 0,
  "data": [
    {"nodeName": "lead_approve", "operator": "leader1", "submitType": "AGREE", "comment": "同意", "createdAt": "..."},
    {"nodeName": "dept_approve", "operator": "dept_leader", "submitType": "REJECT_TO_START", "comment": "请假天数超出", "createdAt": "..."},
    {"nodeName": "lead_approve", "operator": "leader1", "submitType": "AGREE", "comment": "已修正", "createdAt": "..."}
  ]
}
```

---

## 7. KPI 字典

[`../spec/kpi-dictionary.md` §KPI 4 驳回率](../spec/kpi-dictionary.md)

**驳回率阈值**：
- < 5%：申请人质量高
- 5-15%：关注，可能字段不清
- > 15%：异常，流程设计有问题

---

## 8. 反模式

❌ **驳回不写 comment**：审计无法追踪
❌ **驳回到 start 不通知申请人**：体验差
❌ **无限循环**：必须限制最大次数
❌ **审批人随意驳回**：KPI 监控 + 培训

---

## 9. 验收 checklist

- [ ] `REJECT_TO_START` 测试：流程变 REJECTED，字段清空
- [ ] `REJECT_TO_NODE` 测试：流程回到指定节点
- [ ] `withdraw` 测试：发起人撤回成功
- [ ] `/api/admin/trace` 记录驳回事件
- [ ] 03 FAQ Q3「驳回规则」明确

---

**版本**：v1.11.5 · **来源**：02 plan A2 W2 末 · 与 concepts/03-execution-engine.md §4 联动