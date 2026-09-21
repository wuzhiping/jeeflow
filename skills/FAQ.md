# jeeflow 客户 FAQ

> **来源**: 从客户反馈沉淀 (FB-0006 / FB-0008 / FB-0009 / 隐含咨询)
> **目的**: 让客户自助找到答案, 减少重复询问
> **维护**: 每次新 FB 闭环后, 检查是否值得入 FAQ

---

## 1. 字段权限

### Q1.1: `PERMISSION_f_<name>` 字段权限码是什么?

**A**: 三个值:
- `1` = **只读** (字段显示但不可编辑)
- `2` = **编辑** (字段可编辑) ⚠️ **注意: 不是隐藏!**
- `3` = **隐藏** (前端不可见, 后端不持久化)

**来源**: FB-0004 (字段权限码文档与实际行为不符) → FIX-DOC-1
**详见**: `docs/known-issues.md §82` + `docs/AGENTS.md §6 约束 #16`

### Q1.2: 字段权限必须用 `PERMISSION_f_<name>` 前缀吗?

**A**: 是. 必须用 `PERMISSION_f_<name>` 前缀, 不带 `f_` 前缀可能不生效.
**详见**: `docs/AGENTS.md §6 约束 #16`

---

## 2. 会签 (countersign)

### Q2.1: `countersignCompletionCondition` 字段值是表达式还是字符串?

**A**: **两种语义互斥, 必须二选一**:

| 模式 | 字段值 | 行为 |
|------|--------|------|
| **全员通过** | (字段省略) | PARALLEL: 全员 approve 才流转 |
| **比例通过 (N/M)** | `"#nrOfCompletedInstances>=K"` | 满足 K/M 立即流转 + 余者 ABANDON |
| **一票否决** | `"ONE_VOTE_VETO"` | 任一 reject (submitType=20) 立即流转 state=45 |

⚠️ **不能复合**: 字段值是表达式 = 放弃一票否决能力. 字段值是字符串 = 放弃比例能力.

**如果需要复合规则**: 用嵌套 decision + expr 或自定义节点.
**来源**: FB-0008 → FIX-DOC-2
**详见**: `docs/flow.md §3.3` + `docs/AGENTS.md §5.8` + `docs/known-issues.md §113`

### Q2.2: 会签一票否决怎么配置?

**A**:
1. `performType=1`
2. `countersignType=PARALLEL`
3. `countersignCompletionCondition="ONE_VOTE_VETO"`
4. 节点上配 `submitType=20` 按钮 (拒绝一票否决)
**详见**: `flows/13-countersign-one-vote-veto.json`

---

## 3. 委托 (delegate / surrogate)

### Q3.1: `processTask/delegate` 的字段名是什么?

**A**: **`targetUserId`**, 不是 `assignee`!

```bash
# ✅ 正确
POST /wf/processTask/delegate
{"processTaskId": "...", "operator": "...", "targetUserId": "leader"}

# ❌ 错误 (报 [ValueError] targetUserId 缺失)
POST /wf/processTask/delegate
{"processTaskId": "...", "operator": "...", "assignee": "leader"}
```

**来源**: FB-0009 → FIX-DOC-3
**详见**: `docs/flow.md §5.3.1` + `docs/actions.md §3` + `docs/known-issues.md §114`

### Q3.2: 委托后, 委托方还能在 todoList 看到任务吗?

**A**: **能**. 当前设计是"协助"语义, 不是"移交":
- `actorIds` = `[operator, targetUserId]` (双方都列)
- 双方都可在 todoList 看到
- 任何一方都可执行

**来源**: FB-0010 (验证结论)
**详见**: `docs/flow.md §5.3.1` (委托当前行为表) + `docs/known-issues.md §114`

---

## 4. 集成 / SPI

### Q4.1: 怎么按组织架构自动选审批人 (而不是硬编码)?

**A**: jeeflow 支持 `assignmentHandler` 自定义 + SPI 集成:

```python
# 1. 实现 SPI provider
from spi import OrgUserProvider
class MyOrgProvider(OrgUserProvider):
    def get_dept_leader(self, user_id, levels=1):
        # 你的实现
        pass

# 2. 流程 properties 用 handler
{"assignmentHandler": "com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$DeptLeaderAssignmentHandler"}

# 3. 引擎调用 get_dept_leader(operator) → 返回审批人
```

**来源**: FB-0006 (客户咨询)
**详见**: `docs/integration.md` + `spi/demo/`

### Q4.2: 内置 handler 有哪些?

**A**: 7 个 (见 `docs/flow.md §6`):
- `OperatorAssignmentHandler` (兜底 = inst.operator)
- `FormFieldAssigneeHandler` (按表单字段值)
- `…DeptLeaderAssignmentHandler` (操作人部门领导)
- `…DeptMainLeaderAssignmentHandler` (分管领导)
- `…ApplicantDeptLeaderAssignmentHandler` (发起人部门领导)
- `…ApplicantDeptMainLeaderAssignmentHandler` (发起人分管)
- `…TaskRoleAssigneeHandler` (按角色, roleCode=node.id)

---

## 5. 状态机

### Q5.1: 实例状态有哪些?

**A**: 7 种 (`docs/state.md`):
- `10` DOING - 进行中
- `20` DONE - 完成
- `45` REJECT - 驳回
- `50` PENDING - 挂起 (FIX-T70 v1.9.0+)
- `99` ABANDON - 废弃 (更新人为触发者, FIX-T111 §112)
- `WITHDRAW` - 撤回 (FIX-T107 §7.3.1)
- `CHILD_*` - 主子联动 (FIX-T72 §3.1.1)

### Q5.2: 任务被 ABANDON 后, 谁是 updateUser?

**A**: **触发废弃的人** (FIX-T111 §112):
- 比例会签完成条件命中: 触发者 (最后一个 approve 的人)
- ONE_VOTE_VETO REJECT: rejecter (投 reject 的人)
- ROLLBACK: rollbacker
- 流程撤回: withdrawer

**backward compat**: 不传 `abandoned_by` 时, 默认 `createUser` (发起人).

---

## 6. BUG / 已知限制

### Q6.1: task 节点多条无条件出边会有什么问题?

**A**: BUG-1 (FIX-T110 §111): task 节点 ≥2 条无条件出边且含 end, end 会被提前遍历, instance.state=20 但下游 task 仍 DOING, 流程永远卡住.
**修复**: 用 decision 节点分隔分支 (不要 task 直接接多出边).
**验证**: verify W012 警告 (deploy 时触发).

### Q6.2: decision 节点多分支怎么避免孤儿 task?

**A**: BUG-2 (FIX-T112): decision 多分支 expr 全部评估失败时, 引擎兜底走第一条边, 可能创建孤儿 DOING task.
**修复**:
1. 加默认边 (`expr=""` 作为兜底)
2. 引擎 `_cleanup_orphan_decision_tasks` 清理
3. verify W013 警告

---

## 7. 反馈与支持

### Q7.1: 发现 BUG / 文档问题 怎么办?

**A**: 通过 hermes peer dm 反馈:
```
hermes peer dm flowuser "[hermes · 流程设计师助理]
1. 现象 (一句话)
2. 复现步骤 (3-5 步)
3. 涉及的 instance_id
4. 是否有 ndjson / txt 文件? (给取件码)"
```

### Q7.2: 反馈的 SLA 是多少?

**A**: `skills/FEEDBACK.md §5`:
- P0 (流程阻塞): 24h 首次响应, 7d 闭环
- P1 (体验差): 3d 首次响应, 30d 闭环
- P2 (改进建议): 7d 首次响应, 90d 排期
- P3 (远期需求): 30d 归档或转需求池

---

## 8. 维护规则

- 每月初检查 FAQ, 合并高频咨询
- 每次 FB 闭环后, 检查是否值得入 FAQ
- 季度大复盘时整体体检
- 新增 FAQ 项必须标 FB 来源 + FIX 编号 (如有)
