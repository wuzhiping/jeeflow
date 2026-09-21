# FB-0012 patches 最终版 (v1.0) · 2026-11-10 (W46 Day 2)

> **FB-0012**: submitType=20 (COUNTERSIGN_DISAGREE) 在 task → decision 拓扑下无效 (中间节点失效)
> **类型**: doc (P1)
> **当前状态**: 🟡 v1.0 draft, 等 flowuser 给 submitType=20 实证 ndjson
> **起草日期**: 2026-11-10

---

## ⚠️ 待 flowuser 实证

本 patches **最终** 版, 需要 flowuser 提供:
1. **1 个 submitType=20 的真实流程实例** (脱敏 instance_id)
2. **该实例对应的 ndjson 关键行** (脱敏)
3. **您当时遇到的痛点** (1-2 句话)

如方便, 上传后给 hermes, hermes 立即 apply。

---

## 1. `docs/flow.md §3.3.1` 新增 (草稿)

### 3.3.1 submitType 拓扑约束 (新增)

**submitType 的语义仅在 countersign task 节点直接连 end 边时生效。**

#### 拓扑陷阱

如果 countersign task → decision 节点 → 任意节点，submitType=20 (一票否决) **不生效**, 走 decision expr 评估路径而非 cs_veto 路径。

#### 正确拓扑 (submitType 生效)

```
[start] → [countersign task, submitType=20] → [end]
```

#### 错误拓扑 (submitType 沉默)

```
[start] → [countersign task, submitType=20] → [decision, expr=...] → [任意]
                          ↑                                ↑
                  走 cs_veto 路径?               实际走 decision expr 路径
                  (设计预期)                    (实际行为) ← 沉默陷阱
```

#### 实战建议

如需要 "会签 + 后续决策" 语义, 请拆为 2 个独立节点:
- **节点 1**: countersign task (submitType=20) → end
- **节点 2**: 单独 decision 节点, 用变量 (`cs_veto_result`) 判定

详见 `docs/known-issues.md §116`.

---

## 2. `docs/AGENTS.md §5.8.1` 新增 (草稿)

### §5.8.1 submitType 拓扑测试 (新增)

测试会签节点时, 必须区分两种拓扑:

| 拓扑 | submitType 路径 | 测试要求 |
|------|----------------|----------|
| **task → end** | cs_veto 路径 | 测 1 次即可 (per submitType) |
| **task → decision → 任意** | decision expr 路径 | 必须分别测试 submitType + expr 组合 |

**反模式**: 假设 submitType=20 在 task → decision 拓扑下也生效 → 设计错误.

### 新增约束 #33 (待定)

```markdown
# 33. submitType 拓扑约束
会签 task 节点的 submitType 仅在 task → end 直接拓扑下生效.
如 task 后接 decision/网关, submitType 不生效, 走 decision expr 评估.
正确做法: 拆为独立 task + 独立 decision 节点, 用变量传递结果.
```

---

## 3. `docs/known-issues.md §116` 新增 (草稿)

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
**修复提交**: 待 flowuser 给 submitType=20 实证后最终 apply
```

---

## 4. hermes 行动项

| 步骤 | 动作 | 时间 | 状态 |
|------|------|------|------|
| 1 | 草稿就绪 (本文件 v1.0) | W46 Day 2 | ✅ |
| 2 | 等 flowuser 给 submitType=20 实例 + ndjson | W46 Day 2-3 | 🟡 |
| 3 | 拿到实证后立即 finalize patches + apply | W46 Day 3-5 | 待执行 |
| 4 | 起草 bdd-17xx (submitType 拓扑回归测试) | W46 Day 5 | 待起草 |
| 5 | 联系 bro apply (解冻后) | W47+ | 待执行 |

---

## 5. 关联文档

- `feedback/inbox/FB-0012.json` · 原报告 (2026-09-23)
- `feedback/attachments/FB-0012-patches/README.md` · 草稿
- `docs/flow.md §3.3` · countersign 节点原章节
- `docs/AGENTS.md §5.8` · 会签测试原章节
- `docs/known-issues.md §116` · 待新增

---

⏱️ Last updated: 2026-11-10 (W46 Day 2) · FB-0012 patches v1.0 ล ฟริเวอร์