# L1 软接触 v3 · 2026-10-02 (周四) · W41 Day 4

> **渠道**: Camunda Forum + Flowable GitHub Discussions
> **本步**: 加入 + 首次发帖 (软自我介绍 + 询问社区)
> **节奏**: 一天 1 步, 不贪多

---

## 1. 今日目标 (1 步)

| 步骤 | 动作 | 期望产出 |
|------|------|----------|
| **加入 Camunda Forum** | 注册 + 浏览版块 | 1 帖 "自我介绍" |
| **加入 Flowable GitHub Discussions** | 注册 + 浏览版块 | 1 帖 "自我介绍" |

> ⚠️ **环境受限**: 当前沙箱无浏览器, 需 hermes 手动执行.
> 若 hermes 当前环境不可访问, 则:
> - 起草 2 篇自我介绍文稿
> - 列入 "待 hermes 手动执行" 清单
> - **不阻塞本周计划**

---

## 2. 自我介绍文稿 · Camunda Forum 版

**Title**: Workflow Engine Maintainer from China — Learning from the Community

**Body**:
```
Hi everyone,

I'm hermes, maintainer of a small workflow engine called jeeflow
(roughly 8K LoC Python, BPMN 2.0 subset).

Currently running a "Phase 9 — Customer-Centric Pivot":
1. Freeze the codebase (FREEZE.md)
2. Collect customer feedback (12 feedback items so far)
3. Build a customer profile & feedback loop (skills/CUSTOMER.md)
4. Use feedback to drive ALL future changes

Why I'm here:
- Learn how Camunda handles BPMN edge cases (especially countersign
  semantics and parallel gateway race conditions)
- See how the community thinks about engine observability
- Maybe share some lessons learned from jeeflow's small-scale approach

I'm not looking for users (jeeflow is internal-only).
I'm looking for wisdom from people who've done this longer.

If anyone has advice on:
- How to handle "countersign互斥" (mutual exclusion in countersign)
  elegantly in BPMN 2.0
- How to design decision-task topology when submitType=20 enters the picture

I'd love to learn from your war stories.

Thanks,
hermes
```

---

## 3. 自我介绍文稿 · Flowable GitHub Discussions 版

**Title**: Workflow Engine Maintainer — BPMN 2.0 Subset Engine — Learning from Flowable

**Body**:
```
Hi Flowable community,

I'm hermes, maintainer of jeeflow, a small BPMN 2.0 workflow engine
in Python (~8K LoC).

We're in a 90-day "customer-first" pivot:
- Freeze the codebase
- Collect & close 100% of customer feedback (10/10 closed so far)
- Use feedback to drive ALL future changes
- Track via SLA scorecard (currently 100/100, 31固化 checks PASS)

I'm here to learn:
- How Flowable handles parallel gateway + countersign semantics
- Observability patterns for workflow engines
- Community wisdom on "don't ship what users don't ask for"

jeeflow is internal-only, so I'm not here for users.
I'm here for the lessons.

If anyone has war stories about:
- submitType topology in decision tasks
- Variable scope traps in BPMN 2.0
- The "ship less, ask more" discipline

I'd love to hear them.

Thanks,
hermes
```

---

## 4. 待 hermes 手动执行

> 当前沙箱无浏览器, 此节作为 hermes 手动执行清单.

| # | 动作 | URL | 备注 |
|---|------|-----|------|
| 1 | 注册 Camunda Forum 账号 | https://forum.camunda.io/ | 工作邮箱 |
| 2 | 发文 "Workflow Engine Maintainer..." | /c/community | 用上面文稿 |
| 3 | 注册 Flowable GitHub Discussions 账号 | https://github.com/flowable/flowable-engine/discussions | 工作邮箱 |
| 4 | 发文 "Workflow Engine Maintainer..." | Discussions | 用上面文稿 |
| 5 | 更新 `customers/l1-acquisition-v3.md` | skills/customers/ | 记录首次发帖 |

---

## 5. 本周后续 (Day 5 周五)

- 写 W42 周报 (待建)
- Q3 季度复盘准备
- 更新 README §6/§7/§8 (反映 W41 收盘)
- 周末沉淀

---

⏱️ Last updated: 2026-10-02 (周四) · W41 Day 4
