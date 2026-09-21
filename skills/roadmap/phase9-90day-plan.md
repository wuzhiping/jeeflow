# Phase 9 · 90 天工作清单 (解冻后)

> **周期**: 2026-09-22 ~ 2026-12-21 (3 个月)
> **主题**: 客户反馈驱动的修复 + 文档 + 流程模式补齐 + 客户增长启动
> **节奏**: 每周 1 个里程碑 + 每月 1 次大复盘
> **不做**: 新功能 (除客户反馈驱动) / 扩编 / 发版

---

## Month 1 (2026-09-22 ~ 2026-10-22) · 修复推进

### Week 1-2 · 修复验证期

| Day | 行动 | 负责人 | 产出 |
|-----|------|--------|------|
| Mon | flowuser 回看 FB-0007/0008/0009/0010 修复确认 | flowuser + hermes | 4 项 confirmed |
| Tue | bro 双端 (MEM + PG) 集成测试 | bro | BDD PASS 报告 |
| Wed | 反馈闭环 metric 第一次周报 | hermes | `metrics/weekly-W1.md` |
| Thu | 启动 L1 软接触 (Step 1 画像锁定) | hermes | `customers/l1-acquisition-v2.md` |
| Fri | 第 1 周复盘 + W40 周报 | hermes | `weekly/2026-W40.md` |

| Day | 行动 | 负责人 | 产出 |
|-----|------|--------|------|
| Mon | 加入 1 个工作流社区 (观察 3 天) | hermes | 软接触记录 |
| Tue | 跟踪 C-001 阶段 6 自然续办 | hermes | `C-001.yaml stage_6` 更新 |
| Wed | FB-0007/0008/0009/0010 lessons 整理 | hermes | lessons-learned.md |
| Thu | 起草 FAQ 文档 (BL-002) | hermes | `FAQ.md` 初稿 |
| Fri | 第 2 周复盘 | hermes | `weekly/2026-W41.md` |

### Week 3-4 · 验证 + 修复

| Day | 行动 | 负责人 | 产出 |
|-----|------|--------|------|
| Mon | BUG-2 双端集成测试 | bro | BDD 报告 |
| Tue | 处理 flowuser 任何新反馈 | hermes | 新 FB-NNNN |
| Wed | 第 1 次月度 metrics 报告 | hermes | `monthly-2026-10.json` |
| Thu | 季度复盘 Q3 准备 | hermes + bro | `roadmap/quarterly/2026-Q3.md` |
| Fri | Q3 季度复盘 | hermes + bro | Q3 复盘文档 |

| Day | 行动 | 负责人 | 产出 |
|-----|------|--------|------|
| Mon | Q3 复盘产出执行 | hermes + bro | 行动清单 |
| Tue | 处理 flowuser 任何新反馈 | hermes | 新 FB-NNNN |
| Wed | 起草 Phase 9 后半详细计划 | hermes | `phase9-month2-3-plan.md` |
| Thu | 持续 L1 软接触 | hermes | 软接触更新 |
| Fri | Month 1 总结 + 2026-W43 周报 | hermes | 月度总结 |

**Month 1 验收标准**:
- ✅ flowuser 4 项修复全部 confirmed
- ✅ BUG-2 双端 BDD PASS
- ✅ 1 个新 FB 闭环 (来自 flowuser 持续对话)
- ✅ Q3 季度复盘完成
- ✅ L1 软接触 Step 2-3 完成

---

## Month 2 (2026-10-22 ~ 2026-11-22) · 文档 + 流程模式补齐

### Week 5-6 · 文档沉淀

| Day | 行动 | 负责人 | 产出 |
|-----|------|--------|------|
| Mon | auto-assignee-by-org 示例落地 | hermes | `spi/demo/org_assignee_handler.py` + 文档 |
| Tue | FAQ 文档完善 | hermes | `FAQ.md` v2 (从客户反馈持续沉淀) |
| Wed | journey-evidence 模板化 (BL-006) | hermes | `customers/_templates/journey-evidence-template.md` |
| Thu | L1 软接触持续 | hermes | 渠道铺设 |
| Fri | W45 周报 | hermes | weekly log |

| Day | 行动 | 负责人 | 产出 |
|-----|------|--------|------|
| Mon | 处理 flowuser 任何新反馈 | hermes | 新 FB-NNNN |
| Tue | 流程模式 Top-1 (客户反馈驱动) | hermes | 新 `flows/NN-name.json` |
| Wed | docs 全面体检 | hermes | docs audit 报告 |
| Thu | verify 规则新增 (基于客户反馈) | hermes | W014+ |
| Fri | W46 周报 | hermes | weekly log |

### Week 7-8 · 集成测试

| Day | 行动 | 负责人 | 产出 |
|-----|------|--------|------|
| Mon | 新流程集成测试 | bro + hermes | BDD 报告 |
| Tue | 处理 flowuser 任何新反馈 | hermes | 新 FB-NNNN |
| Wed | 第 2 次月度 metrics 报告 | hermes | `monthly-2026-11.json` |
| Thu | L1 软接触持续 (目标: 1 个 L1 客户) | hermes | L1 客户档案 |
| Fri | W47 周报 | hermes | weekly log |

| Day | 行动 | 负责人 | 产出 |
|-----|------|--------|------|
| Mon | Month 2 中期复盘 | hermes + bro | 复盘文档 |
| Tue | 处理 flowuser 任何新反馈 | hermes | 新 FB-NNNN |
| Wed | 双端集成测试 (新流程) | bro | BDD 报告 |
| Thu | 起草 Phase 10 候选 | hermes | `roadmap/phase10-candidates.md` |
| Fri | Month 2 总结 + W48 周报 | hermes | 月度总结 |

**Month 2 验收标准**:
- ✅ auto-assignee-by-org 落地
- ✅ FAQ 文档 v2
- ✅ journey-evidence 模板
- ✅ 1 个新流程模式 (客户反馈驱动)
- ✅ 月度 metrics 100% 闭环

---

## Month 3 (2026-11-22 ~ 2026-12-21) · 客户增长启动

### Week 9-10 · L1 客户获取

| Day | 行动 | 负责人 | 产出 |
|-----|------|--------|------|
| Mon | L1 客户深度接触 (目标 1 个) | hermes | 客户档案 C-NNN.yaml |
| Tue | 处理 flowuser 任何新反馈 | hermes | 新 FB-NNNN |
| Wed | L1 客户 onboarding | hermes + bro | onboarding 文档 |
| Thu | L1 客户首轮反馈 | hermes | FB-NNNN |
| Fri | W49 周报 | hermes | weekly log |

| Day | 行动 | 负责人 | 产出 |
|-----|------|--------|------|
| Mon | L1 客户首轮反馈闭环 | bro + hermes | 修复 |
| Tue | 处理 flowuser 任何新反馈 | hermes | 新 FB-NNNN |
| Wed | Q4 季度规划准备 | hermes + bro | `roadmap/quarterly/2026-Q4-plan.md` |
| Thu | 第 3 次月度 metrics | hermes | `monthly-2026-12.json` |
| Fri | W50 周报 | hermes | weekly log |

### Week 11-12 · Phase 10 规划

| Day | 行动 | 负责人 | 产出 |
|-----|------|--------|------|
| Mon | Phase 10 候选评审 | hermes + bro | `roadmap/phase10-plan.md` |
| Tue | 处理 flowuser 任何新反馈 | hermes | 新 FB-NNNN |
| Wed | Phase 9 90 天总复盘 | hermes + bro | `roadmap/phase9-final-report.md` |
| Thu | 起草 Phase 10 双签 | hermes + bro | 提案 |
| Fri | W51 周报 | hermes | weekly log |

| Day | 行动 | 负责人 | 产出 |
|-----|------|--------|------|
| Mon | Phase 10 启动准备 | hermes + bro | 准备 |
| Tue | 处理 flowuser 任何新反馈 | hermes | 新 FB-NNNN |
| Wed | 季度复盘 Q4 | hermes + bro | `roadmap/quarterly/2026-Q4.md` |
| Thu | 写 Phase 9 收尾文档 | hermes | `phase9-closing.md` |
| Fri | Phase 9 收官 + Phase 10 启动 | hermes + bro | 公告 |

**Month 3 验收标准**:
- ✅ L1 客户 1 个获取 + onboarding 完成
- ✅ L1 客户首轮反馈闭环
- ✅ Phase 10 规划完成 + 双签
- ✅ Phase 9 90 天总复盘
- ✅ Q4 季度复盘

---

## 关键监控指标

| 指标 | 阈值 | 触警动作 |
|------|------|----------|
| 反馈接收时间 | < 24h | 主动询问 |
| P0 BUG 闭环率 | 100% | 自动升级 |
| 双端 BDD PASS | 100% | 禁止合并未通过 |
| 客户确认率 | > 50% | 沉默 14 天主动联系 |
| L1 客户数 (Month 3 末) | ≥ 1 | 未达 → 重新评估渠道 |

---

## 与 Phase 8 的对比

| 维度 | Phase 8 (2026-09-21) | Phase 9 (2026-09-22 ~) |
|------|---------------------|----------------------|
| 视角 | 客户为中心转型 | 客户反馈驱动改进 |
| 自由 | 受限 (FREEZE) | 解冻 (受监控) |
| 节奏 | 启动 + 维护 | 持续 |
| 客户参与 | 5 FB / 1 客户 | 持续 1 客户 + 加 1 L1 客户 |
| 输出 | 制度 + 反馈闭环 | 修复 + 文档 + 流程模式 |

---

## 不做 (明确列出)

- ❌ 新节点类型 (无客户需求)
- ❌ 性能优化 (§7.1 历史已取消)
- ❌ 安全加固 (§7.4 历史已取消)
- ❌ 国际化 / 多语言
- ❌ 开源 / SDK
- ❌ UI 重构
- ❌ 移动 App
- ❌ AI 自动化设计器
- ❌ 区块链审计
- ❌ 主动造功能 (除客户反馈驱动)

⏱️ Created: 2026-09-22 · 待 bro 审核 + 双签
