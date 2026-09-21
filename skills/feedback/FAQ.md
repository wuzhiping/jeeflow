# jeeflow 流程设计 FAQ · v0.1 起草 (W43 Day 4)

> **起草日期**: 2026-10-16 (W43 Day 4)
> **截止日期**: W46 内 published v1.0
> **来源**: 6 条已闭环 FB (FB-0006/0008/0009/0010/0011/0012) + 客户实战经验
> **状态**: 🟡 v0.1 draft

---

## 1. 节点配置类

### Q1.1 assignee / candidate_groups / assignee_expr 何时用?

**A**: 三种方式互斥, 按优先级从高到低:

| 字段 | 用途 | 适用场景 |
|------|------|----------|
| `assignee` | 直接指定 1 人 | 流程固定审批人, 如"采购员" |
| `candidate_groups` | 候选组 | 多角色中任一可处理, 如"任意经理" |
| `assignee_expr` | 表达式动态计算 | 复杂规则, 如 `manager_of(流程发起人)` |

**实战建议**:
- 简单场景 → `assignee`
- 候选池 → `candidate_groups`
- 复杂规则 → `assignee_expr` (需谨慎, 见 Q3.1 变量作用域)
- 来源: FB-0006 (auto-assignee-by-org 派生)

### Q1.2 delegate 与 assignee 区别?

**A**: `delegate` 是 `assignee` 的代理, 临时授权处理.

| 字段 | 是否必填 | 是否可空 |
|------|----------|----------|
| `assignee` | ✅ 主处理人 | ❌ 必须有值 |
| `delegate` | 🟡 可选 | ✅ 可空 (无人代理) |

**实战场景**:
- 主处理人请假 → 设置 `delegate` = 同事 A
- 任务仍归 `assignee` 名下, 但 `delegate` 可代处理
- 来源: FB-0008 + FB-0009 (docs 缺口)

### Q1.3 auto-assignee-by-org 何时启用?

**A**: 当流程发起人想"按组织自动分配审批人"时启用. 引擎按"流程实例所在组织"查找该组织下的"流程审批人"。

**数据需求**:
- `org_id` 字段 (从发起人上下文获取)
- `org.flow_approver` 字段 (每个组织 1 个默认审批人)

**待实施**: Phase 9 Month 2 (W44-W47)
**来源**: FB-0006

---

## 2. 拓扑类

### Q2.1 countersign 节点 submitType 与拓扑关系?

**A**: `submitType` 仅在 `countersign task → end` 直接拓扑下生效.

| 拓扑 | submitType 路径 | 行为 |
|------|----------------|------|
| task → end | cs_veto / cs_all / cs_majority | submitType 生效 ✅ |
| task → decision → 任意 | decision expr 路径 | submitType **沉默** ⚠️ |

**反模式**: 假设 submitType=20 (一票否决) 在 task → decision 拓扑下生效 → 设计错误.

**正确做法**: 拆为 2 个独立节点:
```
[start] → [countersign task, submitType=20] → [end]
       ↘ [decision, expr=cs_veto_result] → [后续]
```

**来源**: FB-0012 (草稿中, 待 flowuser 实证)

### Q2.2 decision 节点 expr 与 submitType 区别?

**A**:

| 字段 | 用途 | 类型 |
|------|------|------|
| `decision.expr` | 决策表达式 (Python-like) | 字符串 |
| `task.submitType` | 会签合流策略 | 枚举 (10/20/30) |

**实战**: decision 用 expr, task (countersign) 用 submitType. 不混用.

### Q2.3 parallel gateway 何时用, 何时用 countersign?

**A**:

| 场景 | 节点 |
|------|------|
| **多分支并行, 无需合流** | parallel gateway |
| **多 assignee 协同, 需合流** | countersign task |

**反模式**: 用 countersign 处理"两个独立分支" → 应改 parallel gateway + join.

---

## 3. 变量作用域类

### Q3.1 流程变量在 task → decision 是否共享?

**A**: ✅ **共享** (同一流程实例内, 变量是流程级, 不是节点级).

```python
# task 节点设置变量
task.set_variable("approved", True)

# decision 节点可访问
decision.expr = "approved == True"
```

**反模式** (常见错误):
```python
# task 节点
x = 10  # 局部? 全局?

# decision 节点
expr = "x == 10"  # ❌ 如果 x 是 task 局部, 此处 None
```

**铁律**: 流程实例内的变量 = 流程级, 所有节点共享. 节点不持有"私有变量".

**来源**: FB-0011 (变量作用域铁律)

### Q3.2 跨节点的变量如何传递?

**A**: 流程级变量自动共享. 无需手动传递.

```python
# node-A
process_instance.set_variable("data", {"key": "value"})

# node-B (后续节点)
data = process_instance.get_variable("data")  # 直接可用
```

### Q3.3 变量作用域铁律 (FB-0011)

**A**:

1. **流程实例级变量**: 全流程所有节点可见
2. **节点无私有变量**: 节点不持有局部变量
3. **跨节点数据流**: 通过流程级变量传递, 不通过节点参数
4. **ndjson 解读**: `vars` 字段是流程级, 任何节点可读可写

**反模式**: 假设某变量是 task 节点"私有", 在 decision 节点读不到 → 设计错误.

**来源**: FB-0011 (3 处文档修订就绪)

---

## 4. 设计决策类

### Q4.1 为什么某处 "设计如此"?

**A**: jeeflow 的"设计如此"决策, 通常源于:

| 类别 | 例子 | 原因 |
|------|------|------|
| 性能 | decision expr 不支持 submitType | 简化决策路径, 避免双逻辑 |
| 安全 | vendor/ 不修改 (FREEZE 期) | 防止失控造新功能 |
| 简洁 | submitType 仅 3 个枚举 | 避免枚举爆炸 |
| 客户驱动 | 不主动造功能 | Phase 9 原则 |

**实战**: 遇到"为什么这样设计"时, 先看 `docs/known-issues.md §X` + `feedback/attachments/FB-XXXX/`.

**来源**: FB-0010 (验证 "设计如此")

### Q4.2 引擎不修改 vendor/ 的边界在哪里?

**A**:

| 状态 | vendor/ 可改? | docs/ 可改? |
|------|---------------|-------------|
| **FREEZE 期** (Phase 8 + 当前) | ❌ 仅 FB-NNNN 关联可改 | ✅ 任何时候 |
| **解冻后** (Phase 9 双签后) | ✅ 按 FB 关联 | ✅ 任何时候 |

**当前**: 未解冻, vendor/ 改 = 需 FB-NNNN 关联 (例: FB-0007 FIX-T112 改过 1 次).
**来源**: FREEZE.md §6

### Q4.3 客户反馈驱动的改进 vs 工程师想象的增强?

**A**:

| 类型 | 来源 | 例子 |
|------|------|------|
| ✅ 客户反馈驱动 | FB-NNNN 关联 | auto-assignee-by-org (FB-0006) |
| ❌ 工程师想象 | "我觉得用户需要" | 加 3 个新功能 |

**铁律**: Phase 9 严禁后者. 仅前者可改 vendor/.

---

## 5. 工程实践类

### Q5.1 流程 ndjson 如何解读?

**A**: 每个流程实例对应 1 个 ndjson 文件 (或多行 JSON).

**关键字段**:
- `process_instance_id`: 流程实例 ID (唯一)
- `node_id`: 当前节点 ID
- `vars`: 流程级变量 (所有节点共享)
- `event`: 事件类型 (start / task_created / task_completed / decision_evaluated / end)
- `timestamp`: 时间戳

**实战**: 定位 BUG 时, 按 `process_instance_id` 过滤, 按时间戳排序.

### Q5.2 引擎日志如何定位 BUG?

**A**:

1. 找到流程实例 ID (从用户报告)
2. 读 ndjson (按 process_instance_id 过滤)
3. 检查事件序列 (start → task_created → task_completed → ...)
4. 找到异常事件 (decision_evaluated 返回错误, 或 task 卡住)
5. 对照 `docs/flow.md §X.X` 看是否符合预期

**反模式**: 不读 ndjson 直接猜 → 浪费时间.

### Q5.3 Phase 9 反馈闭环流程?

**A**:

```
用户提交反馈 (FB-NNNN)
  ↓
hermes 接收 + 分类 (P0/P1/P2)
  ↓
判断: BUG / DOC / UX / 撤回
  ↓
修复 (按 FREEZE 规则, 仅 FB 关联可改 vendor/)
  ↓
BDD 回归测试 (双端 PASS)
  ↓
通知用户 + 等 review
  ↓
用户确认 → 闭环
```

**关键**: 客户沉默 14 天 → hermes 主动询问.

---

## 6. 待补充 (FAQ v0.2 计划)

| # | 主题 | 来源 | 状态 |
|---|------|------|------|
| Q1.4 | 节点回退 (rollback) 如何配置? | TBD | 待客户反馈 |
| Q2.4 | subprocess 何时用? | TBD | 待客户反馈 |
| Q3.4 | 变量命名规范? | TBD | 待客户反馈 |
| Q4.4 | jeeflow 与 Camunda / Flowable 区别? | TBD | 待 L1 软接触 |
| Q5.4 | 引擎版本升级策略? | TBD | 待 Phase 10 规划 |

---

## 7. 关联文档

- `feedback/attachments/FB-0008-patches/` · delegates 字段
- `feedback/attachments/FB-0009-patches/` · delegate 字段
- `feedback/attachments/FB-0011-patches/README.md` · 变量作用域铁律
- `feedback/attachments/FB-0012-patches/README.md` · submitType 拓扑
- `docs/flow.md` (修订待 apply)
- `docs/AGENTS.md` (修订待 apply)
- `docs/known-issues.md §115/§116` (新增待 apply)

---

⏱️ Last updated: 2026-10-16 (W43 Day 4) · FAQ v0.1 draft
