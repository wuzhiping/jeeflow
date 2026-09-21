# FB-0008 补丁索引 (FIX-DOC-2)

> **FB**: FB-0008 (countersignCompletionCondition 文档缺失)
> **修复编号**: FIX-DOC-2
> **提出**: hermes (基于 flowuser 反馈 + 现状分析)
> **目的**: 让 bro 一次性 review + apply, 闭环 FB-0008
> **执行人**: bro (按 `FREEZE.md §6` 例外条款, FB-0008 关联的文档修订)

---

## 1. 修订范围

3 个文件, 3 处变更:

| # | 文件 | 章节 | 变更类型 |
|---|------|------|----------|
| 1 | `docs/flow.md` | §3.3 (task properties 表 + 后续段落) | **改** |
| 2 | `docs/AGENTS.md` | §5.8 (会签测试表) | **改** |
| 3 | `docs/known-issues.md` | §113 (新增) | **增** |

---

## 2. 补丁文件清单

| 文件 | 内容 |
|------|------|
| `flow.md.patch.md` | docs/flow.md §3.3 修订方案 (含 diff 示意) |
| `AGENTS.md.patch.md` | docs/AGENTS.md §5.8 修订方案 |
| `known-issues-§113.md` | docs/known-issues.md §113 全文 (新增) |

---

## 3. 核心改进 (一句话)

**文档缺失的本质**: `countersignCompletionCondition` 字段值是**两种互斥的语义** (数字表达式 vs 字符串常量), 不能复合. 设计师填了哪个, 就只能走哪种模式.

---

## 4. 三种会签模式 (文档应明确)

| 模式 | 字段值 | 行为 | 样例 |
|------|--------|------|------|
| **全员通过 (默认)** | (字段省略) | PARALLEL: 全员 approve 才流转 | `flows/05` |
| **比例通过 (N/M)** | `"#nrOfCompletedInstances>=K"` | 满足 K/M 立即流转, 余者 ABANDON | `flows/07` |
| **一票否决** | `"ONE_VOTE_VETO"` | 任一 reject (submitType=20) 立即流转 state=45 | `flows/13` |

> ⚠️ **不能复合**: 字段值是表达式 = 放弃一票否决能力. 字段值是字符串 = 放弃比例能力. 这是引擎设计选择, 不是 bug.

---

## 5. 申请流程 (给 bro)

```
1. bro review 三个 patch 文件
2. 如同意, 直接 apply 到 docs/ (注意: FB-0008 是合法例外)
3. 跑 sla/check.sh 验证 (docs 章节应通过)
4. 通知 flowuser 闭环
5. 更新 FB-0008 status=closed + lessons_learned
6. 同步更新 README.md / weekly / metrics
```

---

## 6. 涉及文件位置

- `skills/feedback/attachments/FB-0008-patches/flow.md.patch.md`
- `skills/feedback/attachments/FB-0008-patches/AGENTS.md.patch.md`
- `skills/feedback/attachments/FB-0008-patches/known-issues-§113.md`

⏱️ Last updated: 2026-09-21
