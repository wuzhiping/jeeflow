# 变更记录（CHANGELOG）

> fdep.json 与本文件夹（README/ROLES/NODES/CHANGELOG）作为整体同步维护。

| 版本 | 日期 | 改动 | 引擎测试 | 关联测试日志 | 备注 |
|------|------|------|----------|--------------|------|
| v0.1 | 2026-09-22 | 5 阶段线性骨架（PM立项/架构/开发/评审/反馈） | 静态校验 ✅ | — | ToT/READMe#5 初稿 |
| v0.5 | 2026-09-22 | 采纳反馈"PM ≠ start"；新增 Stage 0 接收窗口；新增驳回路径 `end_rejected` | TDD 实跑 ❌ FAILED | [`test_FDEP_20260922081228.md`](../../tdd/test_FDEP_20260922081228.md) | 发现 P0 × 2（W012 + 角色解析断裂） |
| v0.6 | 2026-09-22 | 插入 decision_intake 节点修 W012；assignee 从 R3/R6/R7 → fdep_* SPI 角色 | TDD 实跑 ⚠️ PARTIAL | — | FIX-T112 兜底；角色仍未解析到 u_fdp_pm |
| v0.6.1 | 2026-09-22 | assignee 从 fdep_* → 直接 `u_fdp_pm`（占位场景） | TDD 实跑 ✅ PASSED | — | SPI 角色自动解析留待 v0.7+ assignmentHandler |
| **v0.6.2** | **2026-09-22** | 加 default edge 处理 W013 警告 | **TDD 实跑 ✅ PASSED（基线）** | [`test_FDEP_20260922082028`](../../tdd/test_FDEP_20260922082028.md) | happy path 6 阶段全 DONE |
| v0.6.2 + 文件夹 | 2026-09-22 | 创建 `ToT/flows/fdep/` 文件夹（README/ROLES/NODES/CHANGELOG） | `flow-lint.py` ✅ | — | §10 流程定义组织规范首例 |
| **v0.6.2 + Job Card** | **2026-09-22** | 新增 Job Card 模板（README §5）+ 首张示范卡 `job_card_stage_pm.md`（8 节：身份/输入/目标/checklist/产出/handoff/关联/变更） | — | — | 与 RESPONSES.md Decision Mem 协议 v1.1 lite+ 配套（含 next_handoff 字段） |
| **v0.6.2 + Job Cards 子目录** | **2026-09-22** | 采纳用户建议，job_cards 集中到 `fdep/job_cards/` 子目录，便于多卡管理 | — | — | 相对路径更新：fdep/ 内文件用 `../`，跨包文件用 `../../../` |
| **v0.6.2 + Job Card Generator** | **2026-09-22** | 写 `ToT/sop/gen-job-cards.py`（读 fdep.json + NODES.md + RESPONSES.md §X.2.1 → 批量产出 6 张卡到 `fdep/job_cards/`） | — | — | 默认跳过已存在的卡（保护手工），`--force` 覆盖；自动校验 §5 JSON 合法 + job_card_url 引用一致性 |

---

## 详细变更说明

### v0.5 → v0.6（结构性重构）

**问题**：

1. **W012 BUG-1 §110 重现**：stage_intake 有 2 条出边（approve + reject），引擎遍历两条边后误把 end_rejected 标记为终点，导致 instance.state=20 (DONE) 但下游 task 仍 DOING，无法继续执行。
2. **角色解析断裂**：assignee="R3" 是抽象角色，引擎不会自动通过 SPI 映射到 `u_fdp_pm`，导致后续 task 的 actors 列表只有 `['R3']`，无人可拾起。

**修复**：

1. 在 stage_intake 后插入 `decision_intake` (snaker:decision) 节点，用 `submitType` 路由（1=approve→stage_pm, 2=reject→end_rejected）。
2. assignee 从抽象 R 角色 (R3/R6/R7) → 直接 `u_fdp_pm`（占位场景的务实简化）。

### v0.6 → v0.6.1（assignee 直接赋值）

发现即使 assignee 改为 `fdep_rml` 等 SPI 角色名，引擎也不会自动解析到 `u_fdp_pm`。需通过 `assignmentHandler` 机制才能让 SPI 角色 → 多用户自动解析（v0.7+）。

v0.6.1 务实方案：直接 `assignee: "u_fdp_pm"`，SPI 角色名保留为语义标签（写在 `text.value` 与 `metadata`）。

### v0.6.1 → v0.6.2（W013 兜底）

引擎 verify 报 W013：decision 节点有 2 条带 expr 的出边，无默认边兜底。加 `e_decision_default` (expr="") → stage_pm。

新增 W008：decision_intake → stage_pm 有 2 条边（approve + default 冗余），接受为语义必要。

### v0.6.2 + 文件夹（落地 §10）

按 `ToT/README.md#10` 流程定义组织规范，创建 `ToT/flows/fdep/` 文件夹 + 4 文件。

### v0.6.2 + Job Card（执行者手册化）

**问题**：每个 stage_* 节点由不同 executor（人/AI Agent）执行，但他们都需要"一站式干活指南"。原 NODES.md 是纯文本工作手册，缺：
- 决策 mems 字段模板（execute body 该传什么）
- next_handoff 设计（如何把信息传给下个 executor）
- checklist 化的执行步骤

**方案**：新增 Job Card 模板（README §5）+ 第 1 张示范卡 `job_card_stage_pm.md`。

**卡片结构（8 节）**：
1. 你的身份（node id / assignee / SPI 角色 / 触发）
2. 你的输入（前节点 next_handoff + 流程定义 + 必要文件）
3. 你的目标（produce / storage / exitCriteria）
4. 你的 checklist（6~10 步）
5. 你的产出（execute body 完整 JSON 模板，含 next_handoff）
6. 你的 handoff（下一节点 + 它需要的输入 + 时机）
7. 关联文档 + SOP
8. 变更日志

**配套协议**：RESPONSES.md §0 Decision Mem 协议 v1.1 lite+（新增 `next_handoff` 字段，含 next_node/next_executor/job_card_url/input_files/checklist/context_for_next）。

**未来**：`ToT/sop/gen-job-cards.py` 读 fdep.json + NODES.md + RESPONSES.md → 批量产出剩余 5 张卡（stage_intake/design/dev/review/feedback）。

---

## 测试日志索引

完整测试日志位于 `ToT/tdd/`：

| 时间戳 | 版本 | 结果 |
|--------|------|------|
| `test_FDEP_20260922081228` | v0.5 | ❌ FAILED |
| `test_FDEP_20260922081800` | v0.6.2 | ✅ PASSED（hand-written） |
| `test_FDEP_20260922082028` | v0.6.2 | ✅ PASSED（脚本生成基线） |
| `test_FDEP_20260922082136` | v0.6.2 | ✅ PASSED（最新回归） |

详见 [`../../tdd/INDEX.md`](../../tdd/INDEX.md)

---

## 已知问题（v0.7+ 候选改进）

| Q# | 问题 | 当前状态 |
|----|------|----------|
| Q2 | stage_review 拆 fork-join（R6 自动评审 + R3 人工验收并行） | 未拆 |
| Q3 | stage_feedback → stage_pm 回环（持续改进环） | 未实现 |
| Q4 | R1b 规则变更如何挂入流程 | 未实现 |
| Q5 | 其他阶段驳回扩展 | 仅 intake 有驳回 |
| Q6 | stage_intake 与 stage_pm 同 R3 是否拆 R3a/R3b | 未拆 |
| Q7 | 驳回后能否 resurrect | 当前 end_rejected 是终止态 |
| Q8 | SPI 角色自动解析（assignmentHandler） | 当前 assignee=u_fdp_pm 直接赋值 |

---

## 关联文档

- [`../fdep.json`](../fdep.json) — 流程定义
- [`./README.md`](./README.md) — 流程总览
- [`./ROLES.md`](./ROLES.md) — 角色清单
- [`./NODES.md`](./NODES.md) — 节点工作手册
- [`../../README.md#10-流程定义组织规范`](../../README.md) — 组织规范
- [`../../mapping.md`](../../mapping.md) — 角色映射原理
- [`../../sop/flow-folder.md`](../../sop/flow-folder.md) — SOP
