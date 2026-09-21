# FB-0012 patches 草稿 (待 flowuser 实证最终定稿)

> **FB-0012**: submitType=20 (COUNTERSIGN_DISAGREE) 在 task → decision 拓扑下无效
> **类型**: doc (P1)
> **当前状态**: 🟡 received, 等 flowuser 实证
> **起草日期**: 2026-10-07 (W42 Day 2)

---

## ⚠️ 注意

本 patches **仅为草稿**, 最终修订以 flowuser 提供的实证实例 (1 个 submitType=20 的真实流程 ndjson) 为准.

如果您 (flowuser) 看到草稿, 请:
1. 核对"现象描述"是否准确
2. 补充"教训"或"注意事项"
3. 如方便, 提供 1 个实证实例 ID + 关键 ndjson 行 (脱敏)

---

## 1. `docs/flow.md §3.3` 修订 (草稿)

### 原章节结构 (估计)

```markdown
## 3.3 countersign (会签) 节点

countersign 节点支持多 assignee 并行处理, 通过 `submitType` 控制合流策略:
- submitType=10 (ALL): 全部 assignee 通过
- submitType=20 (COUNTERSIGN_DISAGREE): 一票否决
- submitType=30 (MAJORITY): 过半通过
```

### 草稿新增段落

```markdown
### 3.3.1 submitType 拓扑约束 (新增)

submitType 的语义仅在 **countersign task 节点直接连 end 边** 时生效.

**拓扑陷阱**: 如果 countersign task → decision 节点 → 任意节点,
submitType=20 (一票否决) 不生效, 走 decision expr 评估路径而非 cs_veto 路径.

**正确拓扑** (submitType 生效):
```
[start] → [countersign task, submitType=20] → [end]
```

**错误拓扑** (submitType 沉默):
```
[start] → [countersign task, submitType=20] → [decision, expr=...] → [任意]
                          ↑                                ↑
                  走 cs_veto 路径?               实际走 decision expr 路径
                  (设计预期)                    (实际行为) ← 沉默陷阱
```

**实战建议**: 如需要 "会签 + 后续决策" 语义, 请拆为 2 个独立节点:
- 节点 1: countersign task (submitType=20) → end
- 节点 2: 单独 decision 节点, 用变量 (`cs_veto_result`) 判定

详见 `docs/known-issues.md §116`.
```

---

## 2. `docs/AGENTS.md §5.8` 修订 (草稿)

### 原约束结构 (估计)

```markdown
### §5.8 会签测试

会签节点测试必须覆盖:
- submitType=10 (ALL): 多人提交后合流
- submitType=20 (DISAGREE): 一票否决
- submitType=30 (MAJORITY): 过半
```

### 草稿新增段落

```markdown
### §5.8.1 submitType 拓扑测试 (新增)

测试会签节点时, 必须区分两种拓扑:

| 拓扑 | submitType 路径 | 测试要求 |
|------|----------------|----------|
| task → end | cs_veto 路径 | 测 1 次即可 (per submitType) |
| task → decision → 任意 | decision expr 路径 | 必须分别测试 submitType + expr 组合 |

**反模式**: 假设 submitType=20 在 task → decision 拓扑下也生效 → 设计错误.
```

**新增约束 #33 (待定)**:

```markdown
# 33. submitType 拓扑约束
会签 task 节点的 submitType 仅在 task → end 直接拓扑下生效.
如 task 后接 decision/网关, submitType 不生效, 走 decision expr 评估.
正确做法: 拆为独立 task + 独立 decision 节点, 用变量传递结果.
```

---

## 3. `docs/known-issues.md §116` 修订 (草稿)

```markdown
## §116 submitType 拓扑陷阱 (会签 task → decision) · FB-0012

**现象**: submitType=20 (COUNTERSIGN_DISAGREE) 在 countersign task → decision 拓扑下不生效.

**根因**: `vendor/jeeflow/engine.py` 的 `_evaluate_decision` 短路逻辑,
   优先走 decision expr 路径, 不进入 cs_veto 分支.

**影响**: 所有设计 "会签 + 后续决策" 的流程.

**复现**: 1 步:
1. 配置 countersign task 节点, submitType=20, 后接 decision 节点

**预期**: submitType=20 生效, 一票否决 → 流程 end
**实际**: 走 decision expr 路径, submitType=20 被忽略 → 决策错误

**解决方案**: 拆为 2 个独立节点:
```
[start] → [countersign task, submitType=20] → [end]
       ↘ [decision, expr=cs_veto_result] → [后续]
```

**教训**:
1. submitType 是 task 节点的合流策略, 不是跨节点的语义
2. 复杂流程 (会签 + 决策) 必须显式拆分
3. 文档 `docs/flow.md §3.3.1` 已新增拓扑约束章节

**客户**: C-flowuser (L2, hermes-peer-dm)
**报告时间**: 2026-09-23
**修复版本**: docs-only (no vendor change)
**修复提交**: 待 bro apply
```

---

## 4. 关联文件 (待创建)

| 文件 | 内容 | 状态 |
|------|------|------|
| `docs/flow.md §3.3.1` | submitType 拓扑约束 | 🟡 草稿就绪 |
| `docs/AGENTS.md §5.8.1 + #33` | submitType 拓扑测试 | 🟡 草稿就绪 |
| `docs/known-issues.md §116` | submitType 拓扑陷阱 | 🟡 草稿就绪 |
| `bdd/bdd-1701-1702-submitType-topology_20261007.sh` | 回归测试 | 🔵 待起草 |

---

## 5. hermes 行动项

| 步骤 | 动作 | 时间 |
|------|------|------|
| 1 | 草稿就绪 (本文件) | W42 Day 2 ✅ |
| 2 | 联系 flowuser, 请实证 (1 实例 + ndjson) | W42 Day 2 |
| 3 | 如实证已到 → patches 最终化 + 起草 bdd-17xx | W42 Day 3 |
| 4 | 等 bro apply (解冻后) | W42 Day 4-5 |

---

## 6. 与 FB-0011 的协同

FB-0011 (变量作用域铁律) 与 FB-0012 (submitType 拓扑约束) 都是 **doc 类 FB**, 都针对 docs/ 修订.

如 hermes 一并起草, bro 可一并 apply:

| FB | 修订处数 | 关联文件 |
|----|---------|----------|
| FB-0011 | 3 | docs/flow.md §7.1 + AGENTS.md §6 #32 + known-issues §115 |
| FB-0012 | 3 | docs/flow.md §3.3.1 + AGENTS.md §5.8.1 + #33 + known-issues §116 |
| **合计** | **6** | docs/ (3 文件) |

**bro apply 工作量**: 1 次合并即可.

---

⏱️ Last updated: 2026-10-07 (W42 Day 2)
