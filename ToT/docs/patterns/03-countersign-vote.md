# 设计模式 03 · 会签四模式

> **场景**：合同 / 立项 / 决策性事项需要多人共同决策
> **依据**：`vendor/jeeflow/engine.py:8 CountersignType`（`PARALLEL`/`SEQUENTIAL`/`VOTE`/`CUSTOM`） + `:150-175` 会签判定逻辑

---

## 1. 会签四模式对照

| 模式 | 行为 | 适用场景 | 节点配置 |
|---|---|---|---|
| `PARALLEL` | 所有人同时收到，全部完成才推进 | 平行审批（财务复核）| `countersignType=PARALLEL` |
| `SEQUENTIAL` | 按顺序签，前一个完成下一个才收到 | 顺序审批（HR → IT → 财务）| `countersignType=SEQUENTIAL` |
| `VOTE` | 投票制，过半同意推进 | 委员会决议 | `countersignType=VOTE` + `ratio=0.5` |
| `CUSTOM` | 自定义策略 | 业务方自己实现 | `countersignType=CUSTOM` + 自定义 |

---

## 2. PARALLEL（并行）

**配置**：
```json
{
  "nodeId": "parallel_approve",
  "type": "task",
  "taskType": "APPROVE",
  "countersignType": "PARALLEL",
  "assignmentHandler": "FormFieldAssigneeHandler",
  "args": {"field": "approverList"}
}
```

**引擎行为**（`engine.py:175`）：
```
ct = node.countersignType
if ct in ("PARALLEL",) and not cs_veto:
    # 所有人同时创建 task，DOING 列表里全有
    # 全部完成才推进
```

**适用**：
- 3 个财务同时审 1 张发票
- 5 个评委同时打分

**不适用**：
- 有明确先后顺序的（用 SEQUENTIAL）

---

## 3. SEQUENTIAL（顺序）

**配置**：
```json
{
  "nodeId": "sequential_approve",
  "type": "task",
  "taskType": "APPROVE",
  "countersignType": "SEQUENTIAL",
  "assignmentHandler": "FormFieldAssigneeHandler",
  "args": {"order": ["hr", "it", "finance"]}
}
```

**引擎行为**（`engine.py:159`）：
```
if ct == "SEQUENTIAL" and not cs_veto:
    # 按 order 顺序，前一个 DONE 才创建下一个 task
```

**适用**：
- 入职流程（HR 备案 → IT 建账号 → 财务建工资）
- 多级审批（领导 1 → 领导 2 → 领导 3）

**陷阱**：
- 第 1 个人卡住 → 全流程卡住
- 中间人不可用 → 需要加签/委派机制

---

## 4. VOTE（投票）

**配置**：
```json
{
  "nodeId": "vote_decide",
  "type": "task",
  "taskType": "APPROVE",
  "countersignType": "VOTE",
  "countersignConfig": {"ratio": 0.5, "minVotes": 3},
  "assignmentHandler": "TaskRoleAssigneeHandler",
  "args": {"role": "committee_member"}
}
```

**判定**：
- `agree_count / total_voters >= ratio` → 通过
- 或 `agree_count >= minVotes` → 通过

**适用**：
- 董事会决议
- 招标委员会
- 采购委员会

**不适用**：
- 决策需要 100% 同意的（用 SEQUENTIAL + 所有人同意）

---

## 5. CUSTOM（自定义）

**配置**：
```json
{
  "nodeId": "custom_approve",
  "type": "task",
  "taskType": "APPROVE",
  "countersignType": "CUSTOM",
  "countersignConfig": {"strategy": "weighted_majority"},
  "args": {"weights": {"dept1": 0.4, "dept2": 0.4, "dept3": 0.2}}
}
```

**实现**：
- 在 `engine.py` 注册自定义 strategy 函数
- 返回 `(passed: bool, reason: str)`

**适用**：
- 业务方有复杂规则
- 一票否决（引擎已支持 `ONE_VOTE_VETO` magic value，见 `engine.py:150-155`）

---

## 6. 一票否决（Veto）

**配置**（任意会签模式都可加）：
```json
{
  "countersignConfig": {"oneVoteVeto": true}
}
```

或 `args.csCond = "ONE_VOTE_VETO"`（`engine.py:150-155` 处理）

**引擎逻辑**：
```python
cs_veto = ct != "" and cs_cond.upper() == "ONE_VOTE_VETO"
if cs_veto and any_actor_rejected:
    return REJECTED  # 一票否决
```

**适用**：
- 法务部对所有合同有否决权
- 安全部门对所有生产变更有一票否决

---

## 7. 节点配置完整示例

```json
{
  "processDefineId": 100,
  "name": "合同审批（3 部门会签）",
  "nodes": [
    {"nodeId": "start", "type": "start"},
    {
      "nodeId": "applicant_dept_lead",
      "type": "task",
      "taskType": "APPROVE",
      "assignmentHandler": "ApplicantDeptLeaderAssignmentHandler"
    },
    {
      "nodeId": "parallel_legal_finance",
      "type": "task",
      "taskType": "APPROVE",
      "countersignType": "PARALLEL",
      "countersignConfig": {"oneVoteVeto": true},
      "assignmentHandler": "FormFieldAssigneeHandler",
      "args": {"field": "legalAndFinanceApprovers"}
    },
    {
      "nodeId": "ceo_final",
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

## 8. 验收 checklist

- [ ] `verify_flow` 返回 0 errors（`vendor/jeeflow/verify.py`）
- [ ] 模拟 N 人同时 submit → 全部完成才推进
- [ ] 一票否决：1 人 reject → 流程直接 REJECTED
- [ ] `/api/admin/stats/overview` 会签时长纳入统计
- [ ] 03 决策树中加入「会签 N 人卡了怎么办」

---

**版本**：v1.11.5 · **来源**：02 plan A2 W2 末 · 与 concepts/03-execution-engine.md §1 联动