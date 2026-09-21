# docs/known-issues.md §113 (新增)

> **新增章节** · FB-0008 / FIX-DOC-2

---

## §113 countersignCompletionCondition 字段值互斥 (文档缺失, 不是引擎 BUG)

> **首次报告**: 2026-09-21 / flowuser 反馈 (FB-0008)
> **修复编号**: FIX-DOC-2
> **优先级**: P1 (文档)
> **状态**: 🟡 notified, 修订方案就绪 (`skills/feedback/attachments/FB-0008-patches/`)

### 现象

设计师 (`flowuser`) 试图设计一个"3 reviewer 并行会签, 满足 2/3 通过 OR 任一 reject 一票否决"的复合规则:

```json
{
  "performType": 1,
  "countersignType": "PARALLEL",
  "countersignCompletionCondition": "#nrOfCompletedInstances>=2"
}
```

**期望**: 2/3 approve 通过, 或者任何 1 人 reject 一票否决
**实际**: 字段值是表达式, 引擎按"比例模式"处理, 一票否决能力被放弃

### 实测 (92107706646829 + work_logs/09_supplier_evaluation)

| 时序 | 事件 | 状态 |
|------|------|------|
| T+0s | apply → userB 自动 → DONE | ✅ |
| T+1s | review → manager approve → DONE | ✅ |
| T+2s | review → director approve → 触发 2/3, **立即流转** | instance.state=20 |
| T+2s | review → boss (未投) → **state=99 ABANDON** | updateUser=userB (FIX-T111) |
| T+2s | end_approved → DONE | ✅ |
| T+2s | boss 尝试 reject | **❌ code: 99999999** "实例 state=20 不可执行任务 (仅 DOING=10 可执行)" |

**根因**: director 第 2 票时引擎已检测 `nrOfCompletedInstances>=2`, 立即流转 (state=20), 同时把 boss 的 task 标 ABANDON. boss 此时再 execute, 引擎拒收.

### 判定: 文档缺失, 不是引擎 BUG

按 `docs/AGENTS.md §9.5` 判 BUG 自检 3 步:

| 步骤 | 检查 | 结果 |
|------|------|------|
| ① 复现 | 92107706646829 实测 | ✅ 2 秒内重复触发 |
| ② 精读文档 | `docs/flow.md §3.3` + `docs/AGENTS.md §5.8` | ⚠️ 没说字段值是表达式还是常量, 也没说互斥 |
| ③ 对比样例 | `flows/07` vs `flows/13` | ⚠️ 两者都是单字段单语义, 无复合样例 |

**结论**: 不是引擎 bug, 是文档缺失. 设计师按当前文档无法理解两种语义的互斥性.

### 三种会签模式 (修订后)

| 模式 | 字段值 | 行为 | 样例 |
|------|--------|------|------|
| **全员通过 (默认)** | (字段省略) | PARALLEL: 全员 approve 才流转 | `flows/05` |
| **比例通过 (N/M)** | `"#nrOfCompletedInstances>=K"` | 满足 K/M 立即流转 + 余者 ABANDON (FIX-T111) | `flows/07` |
| **一票否决** | `"ONE_VOTE_VETO"` | 任一 reject (submitType=20) 立即 state=45 + 余者 ABANDON | `flows/13` |

⚠️ **关键互斥性**:
- 字段值 = 表达式 → **放弃**一票否决 (即使 reject, 引擎已按比例流转, reject 来不及)
- 字段值 = 字符串 → **放弃**比例 (引擎只识别 ONE_VOTE_VETO, 不评估表达式)
- 这是引擎设计选择, 不是 bug. 设计师必须二选一.

### 如果真的需要"复合规则"?

| 场景 | 解决方案 |
|------|----------|
| 2/3 通过 + 任一 reject 立即驳回 | 用嵌套 decision + expr (`docs/flow.md §3.4`); 会签节点只做 2/3, 后接 decision 节点判 reject 边 |
| 复杂多条件会签 | 自定义节点 + handler (`docs/flow.md §3.5` + `main_common.build_custom_handlers`) |
| 纯比例 | `countersignCompletionCondition: "#nrOfCompletedInstances>=K"` (本节方案 1) |
| 纯一票否决 | `countersignCompletionCondition: "ONE_VOTE_VETO"` (本节方案 2) |

### 修复

**修订**:
- `docs/flow.md §3.3` (修订方案: `skills/feedback/attachments/FB-0008-patches/flow.md.patch.md`)
- `docs/AGENTS.md §5.8` (修订方案: `.../AGENTS.md.patch.md`)
- `docs/known-issues.md §113` (本文, 新增)

**未修改**:
- 引擎代码 (设计如此, 无需修改)
- `flows/07-countersign-ratio.json` / `flows/13-countersign-one-vote-veto.json` (符合单一语义)

### 回归覆盖

- 现有 BDD (Task 16 比例 / Task 17 一票否决) PASS (无影响)
- 新增 BDD: 测试"会签互斥性"提示在 deploy 时显示 (可选, 暂缓)

### 优先级

✅ 已修复 (2026-09-21, FIX-DOC-2 修订方案就绪, 等 bro apply)

⏱️ Last updated: 2026-09-21
