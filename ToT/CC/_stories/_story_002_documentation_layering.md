# CC 故事 002 · 文档体系 3 层定位（2026-09-26）

> **类型**：架构变更故事（不是具体业务场景，而是元治理）
> **触发**：随着 ToT/docs v2 体系建立，3 层文档定位模型正式落地

---

## 故事背景

**人物**：
- 🟢 流程设计师 张工：常问「这个字段应该写在哪？」
- 🟡 流程审计员 王工：常问「哪些是契约文档，哪些是教程？」
- 🔵 部署运维 陈 DBA：常问「文档改了为什么版本号也变了？」
- 🟣 知识管理员 林工：常问「为什么同一件事在不同地方说了两遍？」

**问题触发**：用户口头指令「docs/ 是系统初创期的指导纲领，落地指南；ToT/ 是系统服务治理期的指导纲领和基本准则；ToT/docs/ 是 初创期的相关外部文档的引入，修正。这个变化需要变更记录下来，广而告之。」

---

## 故事主轴

### T0 · 问题显化

张工拿到一个新流程需求，写了一份 README 在 `docs/flow-definitions.md`。3 个月后，这篇文档没人维护——因为系统已经进入治理期，docs/ 不该放这类内容。

王工做审计时发现 `docs/api.md` 和 `ToT/docs/spec/` 的 API 描述有冲突——没人知道哪份是真相。

陈 DBA 跑了 release，发现版本号自动 bump 到 1.12.2 — 但他只改了 `docs/AGENTS.md` 一句话。

林工整理客户反馈，发现同样的"5 步请假流程"在 3 个地方有不同版本——`docs/manual/06`、`ToT/docs/guides/02`、`ToT/CC/quickstart-card.md`。

### T1 · 3 层定位模型落地

**关键决策**（用户确认）：
- `docs/` = 初创期 · 落地指南（一次性）
- `ToT/` = 服务治理期 · 基本准则（持续运行）
- `ToT/docs/` = 初创期外部文档的引入、修正（半永久资产）

**落地动作**：
1. **新建** [`ToT/docs/_meta/layering.md`](../_meta/layering.md) —— 完整 3 层定位说明（4 节 + 1 关系图 + 1 演进原则）
2. **更新** `ToT/README.md` —— 顶部摘要加 3 层定位链接
3. **更新** `ToT/CC/README.md` §10 —— 4 类 persona 都看到的「重大变更公告」
4. **新建** `ToT/sop/version-bump-guard.py` —— 防止纯文档变更自动 bump 版本

### T2 · 版本守卫原理

```bash
$ git status
modified:   docs/AGENTS.md  ← 唯一变更

$ bash ToT/sop/release.sh v1.12.2
▶ Step 0.5: version-bump-guard.py
❌ 检测到纯文档变更，version-bump 需要人工确认
💡 提示：release.sh 支持 --reason "<理由>" 参数

$ bash ToT/sop/release.sh v1.12.2 --reason "同步健康度数据到 README"
▶ Step 0.5: version-bump-guard.py
⚠️ 纯文档变更，但已通过 --confirm-doc-only 确认
   理由：同步健康度数据到 README
✅ 继续 bump 版本
```

**规则**：
- ✅ 含 `*.py` / `*.json`（非文档）/ `*.sh` 改动 → 自动 bump
- ⚠️ 仅含 `*.md` / `docs/` / `ToT/docs/` / `ToT/CC/` 等改动 → 需 `--reason`
- ❌ 仅含 doc + 无 `--reason` → 阻止

### T3 · 4 persona 影响

| Persona | 影响 | 后续动作 |
|---|---|---|
| 🟢 张工 | 新流程写到 `ToT/flows/<name>/` 而非 `docs/` | 加引导至 GETTING_STARTED §2.1 |
| 🟡 王工 | 审计清单来自 `ea-compliance.py` 44 项；契约在 `ToT/docs/spec/` | cc/README §10 加 persona 影响表 |
| 🔵 陈 DBA | 文档改动不再静默 bump 版本 | `release.sh --reason` 走显式确认 |
| 🟣 林工 | 案例放 `_stories/`，契约放 `spec/`，教程放 `guides/` | `layering.md` §3 加「何时写入哪一层」表 |

### T4 · 飞轮验证

- 健康度 100/100 🟢
- 0 drift
- 21+ snapshot 累积
- 客户 `/version` 同步

---

## 闭环自检（双圈）

### 内圈：4 persona review

**🟢 张工**：GETTING_STARTED §2.1 已经指向 `flow-design.md`，现在还要补一句「产物放 ToT/flows 而非 docs/」。

**🟡 王工**：ea-compliance.py 44 项覆盖完整，加上 3 层定位的「spec 是契约」认知后，审计职责更清晰。

**🔵 陈 DBA**：version-bump-guard.py 是直接收益——以前改了 README 就 bump，现在会拦截。

**🟣 林工**：CC/_stories/ 已经独立，layering.md §3 给了「何时放哪」决策表，零摩擦。

### 外圈：架构层 review

- ✅ 3 层定位明确（无歧义）
- ✅ `__version__` 语义清晰（代码变更驱动）
- ✅ 守卫机制简单（git diff 分类 + 理由）
- ⚠️ 后续需要：监控「连续 3 次 release 都是纯文档」的反模式

---

## 经验沉淀（给下个故事）

1. **文档体系 3 层定位是常识但容易被忽视**——元治理文档（`layering.md`）必须有，否则新人会乱放
2. **version bump 应有触发条件**——纯文档变更不应静默 bump，否则版本语义混乱
3. **守卫机制要简单**——git diff 分类即可，不要引入复杂规则引擎

---

## 相关文档

- [`ToT/docs/_meta/layering.md`](../_meta/layering.md) — 3 层定位完整说明
- `ToT/sop/version-bump-guard.py` — 版本更新守卫
- `ToT/CC/README.md` §10 — 4 persona 视角的变更公告
- [`_flywheel_demo_e2e.md`](./_flywheel_demo_e2e.md) — 飞轮 E2E 演示（验证机制）

---

**版本**：v3.9 · **来源**：用户口头指令「docs/ 是初创期 · ToT/ 是治理期 · ToT/docs/ 是外部引入」