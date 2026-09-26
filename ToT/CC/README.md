# ToT/CC · Customer Central 客户中心

> **定位**：ToT/docs 是底层文档体系，CC（Customer Central）是「以客户为中心」的应用层——为四类用户提供**量身定制**的使用指南、反馈机制、迭代计划。
>
> **不重复造轮**：CC 不重复 ToT/docs 的技术细节，而是**精选 + 重排 + 加场景化例子 + 闭环反馈**。

---

## 0. 飞轮架构（核心）

**03-participant（参与者）是飞轮中枢**——其他 3 个 plan 通过反馈自动接收参与者的痛点。

```
            ┌──────────────────────────────────┐
            │     03 参与者（飞轮中枢）⭐        │
            │   高频使用 + 自助解决率指标        │
            └──────────────┬───────────────────┘
                           │ feedback-triage.py 自动分流
            ┌──────────────┼──────────────────┐
            ▼              ▼                  ▼
      ┌──────────┐   ┌──────────┐       ┌──────────┐
      │ 01 引擎   │   │ 02 设计   │       │ 04 运维   │
      │ bug 路由  │   │ design   │       │ perf     │
      └────┬─────┘   └────┬─────┘       └────┬─────┘
           │              │                  │
           └──────────────┼──────────────────┘
                          ▼
                 ┌────────────────┐
                 │ release.sh     │
                 │ ship improvements│
                 └────────┬───────┘
                          ▼
                 客户系统 / 参与者体验改善
                          ▼
                 反馈更多 → 飞轮加速
```

**North Star**：参与者自助解决率 ≥ 80%、任务平均时长 ≤ 30 秒。**所有其他 plan 的成功都通过这两个指标验证。**

详见：[`03-participant.md`](./03-participant.md) §0, §8, §9

---

## 1. 服务四类人

| # | Persona | 时间预算 | 核心诉求 | CC 计划 | 飞轮角色 |
|---|---|---|---|---|---|
| **1** | 流程引擎开发升级 | 半天/周 | 改引擎不破坏契约 | [`01-engine-developer.md`](./01-engine-developer.md) | 下游：`bug` 路由 |
| **2** | 业务流程设计管理者（含 FDEP）| 半天/周 | 设计好流程、持续改进 | [`02-process-designer.md`](./02-process-designer.md) | 下游：`design-issue` / `process-gap` |
| **3** | **业务流程参与者** ⭐ | <5 分钟/任务 | 把当前任务做对、不卡住 | [`03-participant.md`](./03-participant.md) | **中枢**（飞轮入口）|
| **4** | 系统管理运维审计 | 偶发/事件驱动 | 跑得稳、查得清、追得到 | [`04-ops-audit.md`](./04-ops-audit.md) | 下游：`system-perf` / `system-down` / `audit-trace` |

---

## 2. CC 体系原则

1. **以参与者为中心**：03 是中枢；其他 plan 都围绕参与者的体验改进
2. **以客户为中心**：每个 plan 的第一个 section 都是「Persona Profile + 典型任务」，不是「功能清单」
3. **用事实而非虚构**：每个 plan 都引用 ToT/docs/*.md + vendor/jeeflow/*.py 的真实行号；不写「可能会发生」
4. **闭环反馈**：通过 `feedback-triage.py` 自动分流，每周一评审
5. **不与 ToT/docs 重复**：技术原理、API 签名去 ToT/docs/spec + ToT/docs/concepts；CC 只讲「什么场景用什么 + 怎么避坑」

---

## 3. CC ↔ ToT/docs 关系

```
   ┌─────────────────────────────────────────────────────┐
   │  ToT/docs (底层知识库)                                │
   │  - guides/  user-manual/  spec/  concepts/  manual/  │
   │  - diffs.md  CHANGELOG.md  REPORT.html              │
   │  - health-check.py  health-report.py  release.sh    │
   └──────────────────┬──────────────────────────────────┘
                      │ 精选 / 重排 / 加场景化
   ┌──────────────────▼──────────────────────────────────┐
   │  ToT/CC (应用层 + 飞轮)                              │
   │  - 03-participant.md ⭐ 飞轮中枢（高频信号）           │
   │  - 01-engine-developer.md (bug 路由接收方)            │
   │  - 02-process-designer.md (design 路由接收方)         │
   │  - 04-ops-audit.md (perf 路由接收方)                 │
   │  - feedback/ + feedback-triage.py (自动分流)          │
   └─────────────────────────────────────────────────────┘
```

---

## 4. CC 自身健康指标

| 指标 | 当前 | 目标 |
|---|---|---|
| 4 计划文件存在 | ✅ 已建 | 持续维护 |
| 飞轮 RPM（每月闭环数）| 0 | ≥ 2 |
| 月分流条目数 | 0 | ≥ 8 |
| 闭环率 | N/A | ≥ 70% |
| 参与者自助解决率 | 未知基线 | ≥ 80% |
| 健康度门禁 | 100/100 | 不退化 |
| 客户同步 | 已 1.11.0 | 每 release 同步 |

---

## 5. CC 内部交叉引用矩阵

| Persona | 飞轮角色 | 引用 |
|---|---|---|
| 1. 引擎开发 | 下游 | ← 03 `bug` · ToT/docs/concepts/09-core-types.md · ToT/docs/spec/04-engine-ops.md |
| 2. 流程设计 | 下游 | ← 03 `design-issue` · ToT/docs/guides/02-flow-definition.md · spi/fdep/*.py |
| **3. 参与者** ⭐ | **中枢** | → 01/02/04 + ToT/docs/manual/06-start-and-approve.md |
| 4. 运维审计 | 下游 | ← 03 `system-perf` · ToT/docs/guides/06-deployment.md · main_common.py 监控端点 |

---

## 6. 飞轮反馈闭环（升级版）

```
参与者提反馈
  ↓
feedback/03-participant-<seq>.md（带 Tags 字段）
  ↓
feedback-triage.py 自动分流（每周一）
  ├ bug → feedback/_routes/01-*.md → 01-engine-developer
  ├ design-issue → feedback/_routes/02-*.md → 02-process-designer
  ├ system-perf → feedback/_routes/04-*.md → 04-ops-audit
  └ doc-gap / ux-issue → 03-participant 自己处理
  ↓
各 plan owner 执行修复/补充
  ↓
release.sh ship 到客户系统
  ↓
更新 ToT/CC/faq.md / decision-tree.md / runbook.md
  ↓
feedback/03-*.md 加「## 闭环」字段
  ↓
下次参与者自助解决率 ↑
```

详见：[`feedback/README.md`](./feedback/README.md)

---

## 7. 季度迭代节奏（飞轮 RPM 驱动）

| Week | 03 主导 | 01/02/04 接收 | 公共动作 |
|---|---|---|---|
| W1 | 收集反馈 + 跑 `feedback-triage.py` | 评审本周分流的 backlog | release.sh 输出 snapshot |
| W2 | 更新 FAQ + 5 分钟卡 | 接收本周新分流 | 客户系统同步 `/version` |
| W3 | 季度 NPS 调研 | 执行分流到的行动 | 月度 release |
| W4 | release + 复盘 RPM | release + 同步 FAQ | **季度回顾**：RPM / 自助解决率 / NPS |

---

## 8. 季度回顾与故事沉淀

- **2026 Q3 回顾**：[`_stories/_quarterly_retrospective_2026Q3.md`](./_stories/_quarterly_retrospective_2026Q3.md)（2026-09-18 → 2026-09-25）
- **故事 001**：[`_stories/_story_001_annual_leave.md`](./_stories/_story_001_annual_leave.md)（销售部小李请假 3 天）
- **飞轮 E2E 演示**：[`_stories/_flywheel_demo_e2e.md`](./_stories/_flywheel_demo_e2e.md)（3 反馈 100% 闭环）

---

## 9. 下季度方向

- **故事 002**：合同审批 3 部门会签（更复杂的会签链路 + 加签 / 转办）
- **真实反馈累积**：推 jffeedback CLI + 季度 NPS
- **容量基线实测**：跑 50 并发 / 1000 用户/天，写入 `capacity-baseline.md`
- **API 字段变更自动检测**：防止 FB-0009 类 rename 事件

---

## 10. ⚠️ 重大变更公告 · 文档体系 3 层定位（2026-09-26 v3.9）

> **重要**：所有 4 类 persona 在写文档前必读。

### 3 层定位模型

```
docs/         初创期 · 落地指南 · 一次性
ToT/          服务治理期 · 基本准则 · 持续运行
ToT/docs/     初创期的相关外部文档的引入、修正 · 半永久资产
```

**含义**：
- **docs/**（项目根）= 系统从 0 到 1 阶段的手册，教新人「怎么跑起来」
- **ToT/** = 系统进入生产后的工作准则，SOP + 治理 + 飞轮
- **ToT/docs/** = 上游 jeeflow-doc 的本地化裁剪产物，参考契约

### 版本更新保护（v1.12.2+）

> **原则**：`vendor/jeeflow/__init__.py:__version__` 反映**运行时行为变化**。纯文档变更不应自动 bump 版本。

**变更**：
- ✅ `bash ToT/sop/release.sh v1.12.2` → 代码变更，自动 bump
- ⚠️ `bash ToT/sop/release.sh v1.12.2 --reason "同步健康度数据"` → 纯文档变更也 bump（需理由）
- ❌ 默认情况下纯文档变更会被 `version-bump-guard.py` 阻止

详见：
- [`ToT/docs/_meta/layering.md`](../docs/_meta/layering.md)（完整 3 层定位）
- `ToT/sop/version-bump-guard.py --help`（保护机制）

### 影响

| Persona | 变化 |
|---|---|
| 🟢 流程设计者 | 新建流程应写到 `ToT/flows/<name>/` 而非 `docs/` |
| 🟡 流程审计者 | 审计清单在 `ea-compliance.py`，文档契约在 `ToT/docs/spec/` |
| 🔵 部署运维 | 客户系统同步受 `version-bump-guard` 保护，文档更新不静默 bump |
| 🟣 知识管理 | 案例/回顾放 `ToT/CC/_stories/`，契约放 `ToT/docs/spec/` |

**飞轮加速器**：当自助解决率 ↑，反馈量 ↑，闭环时长 ↓ → RPM ↑ → 体验更好 → 飞轮加速。