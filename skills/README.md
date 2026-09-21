# jeeflow Skills · 总体计划 (Living Document)

> **本文件是 skills/ 目录的首要入口**. 工作过程中**持续更新**.
> 它记录: 总纲 / 转向 / 架构 / 现状 / 闭环 / 变更 / 进步 / 改进 / 展望.
>
> **状态约定**: 每节底部有 `⏱️ Last updated` 标记. 任何修改必须更新本标记 + §6 变更日志.

---

## 1. 总纲 (Mission)

> **一句话**: 暂停"以工程师为中心"的工作, 转向"以客户为中心"的体系重构.
> 把客户的一句话反馈, 变成客户看得见的改进.

**核心三问**:

| 问题 | 答案 |
|------|------|
| 我们在为谁工作? | **客户** (L1 引擎 / L2 流程 / L3 业务) |
| 我们怎么知道做得好不好? | **反馈闭环 SLA** + 客户成功指标 |
| 我们接下来做什么? | **客户反馈排序**, 不是工程师想象 |

⏱️ Last updated: 2026-09-21

---

## 2. 核心转向 (Pivot · 2026-09-21 启动)

| 维度 | 旧 (Phase 1-7) | 新 (Phase 8+) |
|------|-----------------|----------------|
| 视角 | 工程师为中心 | 客户为中心 |
| 决策依据 | 工程价值 / 技术债务 | 客户反馈 / 客户成功 |
| 路线图驱动 | roadmap.md (§1-7) | ROADMAP.md (Phase 8/9/10) |
| 文档目的 | 自述 (我们做了什么) | 回应 (客户问什么我们写什么) |
| 团队结构 | 按角色扩编 (RML §6) | 按客户层运营 (CUSTOMER.md) |
| 反馈处理 | 落入 tdd/ 后即结束 | 5 步闭环到客户确认 (FEEDBACK.md) |
| raw data | 可写 | 冻结 (FREEZE.md), 反馈闭环例外 |

**关键决策**:
- 🔵 系统功能开发 (Phase 1-7) **冻结**, 见 `FREEZE.md`
- 🟢 客户视角转型 (Phase 8) **启动**, 见 `ROADMAP.md`
- 🟡 反馈闭环 (Phase 8.1) **首个闭环完成** (FB-0001)

⏱️ Last updated: 2026-09-21

---

## 3. 架构 (Architecture · skills/ 文档体系)

```
skills/README.md (本文) ─── 总入口, 持续更新
   │
   ├─ 制度 (Policies)
   │   ├─ FREEZE.md      ─ 冻结令 + 例外
   │   ├─ FEEDBACK.md    ─ 闭环流程 (5 步)
   │   ├─ CUSTOMER.md    ─ 客户分层 + 旅程
   │   └─ ROADMAP.md     ─ Phase 8/9/10 规划
   │
   ├─ 框架 (Frameworks)
   │   ├─ RML.md         ─ 起点: 10 角色全景
   │   ├─ SKILL-TREE.md  ─ 11 角色 × 7 层能力
   │   ├─ RACI.md        ─ 详细协作矩阵
   │   └─ SKILLS.md      ─ 导航索引 (辅助)
   │
   ├─ 数据 (Data)
   │   ├─ feedback/      ─ 反馈闭环 (inbox / archive / metrics)
   │   ├─ customers/     ─ 客户档案 + L1 招揽 + 旅程实证
   │   └─ roadmap/       ─ 候选改进池 + 季度复盘
   │
   ├─ 节奏 (Cadence)
   │   ├─ weekly/        ─ 周报 (W39, W40, ...) · 每日记录
   │   └─ backlog/       ─ 想法池 · 每月评估
   │
   ├─ 提案 (Proposals)  🆕 2026-09-22
   │   └─ UNFREEZE-PROPOSAL-2026-09-22.md
   │
   ├─ 客户自助 (FAQ)  🆕 2026-09-22
   │   └─ FAQ.md
   │
   └─ 接口 (Interface)
       └─ users.md       ─ 与 flowuser 沟通约定
```

**导航原则**:
- 第一次来: 读本文件 + `FREEZE.md` + `FEEDBACK.md`
- 找具体问题: 用 `SKILLS.md` 的文件清单
- 找历史变更: 翻本文 §6 变更日志
- 看本周节奏: 翻 `weekly/` + 本文件 §8
- 看长期想法: 翻 `backlog/`
- 看解冻提案: 翻 `proposals/UNFREEZE-PROPOSAL-2026-09-22.md`
- 看 FAQ (客户自助): 翻 `FAQ.md`
- 看 Phase 9 计划: 翻 `roadmap/phase9-90day-plan.md`

⏱️ Last updated: 2026-09-22

---

## 4. 现状快照 (Current State · 2026-09-21)

### 4.1 一图概览

```
                    Phase 1-7 系统开发
                    ████████████ 100% (冻结)
                            ↓
                    Phase 8 客户转型
                    ████████░░  80%  (进行中)
                       ├── 8.1 反馈闭环   ██████████ 100% 首个闭环
                       ├── 8.2 客户画像   ████░░░░░░  40% 3 档案
                       ├── 8.3 客户路线图 ████████░░  80% 初稿
                       └── 8.4 制度体系   ██████████ 100% 完成
                            ↓
                    Phase 9 反馈驱动改进
                    ░░░░░░░░░░░   0%  (待解冻)
                            ↓
                    Phase 10 客户增长
                    ░░░░░░░░░░░   0%  (远期)
```

### 4.2 关键数字 (本月 · 2026-09-22 更新 · 解冻提案日)

| 指标 | 数值 | 目标 | 状态 |
|------|------|------|------|
| **总反馈数** | **10** (历史 6 + flowuser 4) | — | 🟢 |
| **闭环数** | **10** | ≥ 5 | ✅ |
| **闭环率** | **100% (10/10)** | > 80% | ✅ |
| P0 闭环率 | 100% (4/4) | 100% | ✅ |
| P1 闭环率 | 100% (4/4) | > 80% | ✅ |
| P2 闭环率 | 100% (2/2) | > 80% | ✅ |
| **真实客户协同** | **5 条 FB (来自 flowuser)** | ≥ 1 | ✅ |
| **首次协同完成** | **2026-09-21** | 9月底前 | ✅ |
| 客户旅程实证 | 4/6 段 | ≥ 3 段 | ✅ |
| 客户档案 | 3 | ≥ 3 | ✅ |
| **取件码机制** | **验证成功** | 可工作 | ✅ |
| **解冻提案** | **🟡 待签** | 双签后启动 Phase 9 | ✅ |
| **Phase 9 计划** | **已起草** | 90 天 | ✅ |
| **L1 软接触** | **Step 1 完成 (类型 C 选定)** | 1 个 L1 客户 (Month 3) | 🟢 |
| **FAQ 文档** | **8 大节已建** | 月度维护 | ✅ |
| **journey-evidence 模板** | **已建** | 持续使用 | ✅ |
| **FIX 完成数** | **7** | — | ✅ |
| **W012 + W013** | **2 项 verify 规则** | — | ✅ |
| **BDD 用例新增** | **3 (FIX-T112)** | — | ✅ |

### 4.3 团队当前重心

- **hermes**: 客户对话 (新) + 流程设计 + 文档 + 反馈接收 + 客户档案维护
- **bro**: 引擎 + 反馈处理 (engine 类) + 双端一致性 + 启动 BUG-2 复现 (FB-0007)
- **CLI (新增)**: 客户接口人 = hermes 兼

⏱️ Last updated: 2026-09-21

---

## 5. 已完成的闭环 (Closed Loops)

> 数据来源: `skills/feedback/archive/` 与 `inbox/`
> 详细见: `skills/feedback/metrics/trends.md`

### 5.1 闭环列表

| FB ID | 标题 | 类型 | 优先级 | 状态 | 修复 | 闭环日 |
|-------|------|------|--------|------|------|--------|
| **FB-0001** | 报销流程出纳节点被跳过 | bug | P0 | ✅ closed | FIX-T110 + W012 | 2026-09-20 |
| **FB-0002** | 会签 ABANDON 触发人字段为空 | bug | P1 | ✅ closed | FIX-T111 | 2026-09-21 |
| **FB-0003** | 多入边 task 节点重复创建 | bug | P0 | ✅ closed | FIX-T35 | 2026-09-19 |
| **FB-0004** | 字段权限码文档与行为不符 | doc | P0 | ✅ closed | FIX-DOC-1 | 2026-09-18 |
| **FB-0005** | ONE_VOTE_VETO REJECT 状态错 | bug | P1 | ✅ closed | FIX-T46 | 2026-09-19 |
| **FB-0006** | SPI assignmentHandler 咨询 | consult | P2 | ✅ closed | (文档指向) | 2026-09-20 |
| **FB-0007** | BUG-2 reject 路径 cashier 幽灵 DOING | bug | P0 | ✅ **closed** | **FIX-T112 + W013** | **2026-09-22** |
| **FB-0008** | countersignCompletionCondition 文档缺失 | doc | P1 | ✅ **closed** | **FIX-DOC-2 (§113)** | **2026-09-22** |
| **FB-0009** | processTask/delegate 字段名错位 | doc | P1 | ✅ **closed** | **FIX-DOC-3 (§114)** | **2026-09-22** |
| **FB-0010** | delegate 后委托方仍可见 | improve | P2 | ✅ **closed** | **(a) 设计如此 (源码验证) + 文档化** | **2026-09-22** |

**累计**: **10/10 = 100% 闭环** ✅

### 5.2 标杆案例: FB-0007 (首次真实客户协同)

**客户**: flowuser (远程 L3, https://abc.feg.cn/jeeflow/)
**问题**: BUG-2 (BUG-1 修复未覆盖 reject 路径) - mgr/dir reject 后 cashier_pay 任务幽灵 DOING, instance 卡 state=10
**触发**: hermes peer dm flowuser 一次性提问 → 客户 94 行响应 → 5 个文件取件码 → 逐个 DM 索取
**修复**: (待 bro 本地复现, 预计 FIX-T112)
**验证**: (待跑通)
**沉淀**:
- `skills/feedback/inbox/FB-0007.json` (登记)
- `skills/feedback/attachments/FB-0007-INDEX.md` (附件清单)
- `skills/feedback/retrospectives/2026-09-21-users-md-task.md` (任务复盘)
- `users.md` 话术升级

**关键洞察**: 
- 真实客户反馈 = 客户实证, 不是模拟
- 取件码机制 = 高效文件共享
- 客户主动反哺 = FB-0008 (从 FB-0007 确认中冒出)
- **多轮小问比一次性轰炸有效**

⏱️ Last updated: 2026-09-21

---

## 6. 变更日志 (Change Log)

> 本节是**时间序列**, 任何 skills/ 下的重要变更都记录于此.
> 格式: `YYYY-MM-DD · [类别] · 一句话摘要`

### 2026-09-21 · v1.9 · 第 4 次 users.md (轻量) + FB-0009 patches 起草

- 🎯 **完成** `users.md` 任务第 4 次 · 轻量 (检查 + 起草许可)
- 🎯 **新建** `feedback/attachments/FB-0009-patches/` · 3 个文档补丁 (FIX-DOC-3)
  - `flow.md.patch.md` · docs/flow.md §5.3 新增 §5.3.1 (task 级委托)
  - `actions.md.patch.md` · docs/actions.md §3 加字段表 + 错误示例
  - `known-issues-§114.md` · docs/known-issues.md §114 新增全文
  - `README.md` · 补丁索引
- 📝 **更新** `feedback/inbox/FB-0009.json` · status=in_progress + linked patch set
- 🔑 **关键发现**:
  - flowuser 周一前 idle, 周一回看
  - FB-0008 真正闭环 = bro apply docs patches (flowuser 只 patch 自己的 SKILL.md)
  - 周末快速起草 FB-0009 patches (3 文件), 类似 FB-0008 流程

### 2026-09-21 · v1.8 · 第 3 次 users.md 任务 (换角度 + delegate/surrogate 实证)

- 🎯 **完成** `users.md` 任务第 3 次 · 换角度 (委托/surrogate 测试)
- 🎯 **新建** `feedback/inbox/FB-0009.json` · processTask/delegate 字段名错位 (doc P1)
- 🎯 **新建** `feedback/inbox/FB-0010.json` · delegate 后委托方仍可见 (设计缺陷 P2)
- 🎯 **新建** `feedback/retrospectives/2026-09-21-users-md-task-3rd.md` · 第 3 次复盘
- 🔑 **关键发现**:
  - 多轮协作 (5 轮) + 长时等待 (5-10 分钟 timeout) 流畅
  - flowuser 决策支持: 3 选项 + 置信度 + 证据链
  - flowuser 周战绩: 10 流程 / 2 真 BUG 闭环 / 6 FB / 22% 真 BUG 率
  - FB 总数 8 → 10

### 2026-09-22 · v1.11 · 4 项 fix 全部完成 + 全部闭环

- 🎯 **完成** 4 项 fix:
  - **FB-0007 FIX-T112**: 引擎 `_evaluate_decision` 加显式短路 + `_cleanup_orphan_decision_tasks` 清理孤儿 task
  - **FB-0008 FIX-DOC-2**: docs/flow.md §3.3 + docs/AGENTS.md §5.8 + docs/known-issues.md §113 三处修订
  - **FB-0009 FIX-DOC-3**: docs/flow.md §5.3.1 + docs/actions.md §3 + docs/known-issues.md §114 三处修订
  - **FB-0010 验证**: 源码审查确认 facade.py:1956 注释 "保留原 actor，不移除", 实测为 (a) 设计如此 (而非 flowuser 假设的 (b))
- 🎯 **新建** verify 规则 **W013** (decision 多分支应加默认边) - `vendor/jeeflow/verify.py`
- 🎯 **新建** BDD 测试 `bdd/bdd-1601-1603-fix-t112-decision-orphan-cleanup_20260922.sh` - 3/3 PASS
- 🎯 **新建** docs/AGENTS.md 约束 #31 - 引用 W013
- 🎯 **关闭** FB-0007/0008/0009/0010 → archive/ (4 项 status=closed)
- 🎯 **更新** 全部 lessons_learned + 验证证据
- 🔑 **关键**: FB-0010 验证结论与 flowuser 70% (b) 假设不同, 实测为 (a) 设计如此. 源码审查纠正客户假设是反馈闭环的价值之一.
- 📊 **累计**: 10/10 FB 全部闭环 = 100%

### 2026-09-22 · v1.13 · SLA v13 健康度报告 (Phase 8 收官)

- 🎯 **新建** `sla/README.md` v13 · 全面 SLA 健康度报告 (按 SLA.md §6 客户角色分块 + §7 承诺服务清单)
- 🎯 **新建** `sla/check_feedback_loop.sh` · 反馈闭环健康度固化脚本 (10/10 PASS)
- 🎯 **新建** `sla/check_skills_outputs.sh` · 制度体系健康度固化脚本 (21/21 PASS)
- 🎯 **新建** `sla/snapshot-v12-2026-09-20.md` · 前次报告快照 (归档)
- 🎯 **更新** `sla/last_check.json` · v13 数据 (score=100, FB=10/10, files=55)
- 🎯 **更新** `sla/HISTORY.md` · v13 变更记录
- 🎯 **更新** `weekly/2026-W39.md` · SLA 报告段
- 🔑 **综合信心**: ⭐⭐⭐⭐⭐ **99%** · 承诺服务 100% 经实测验证
- 🔑 **关键数字**: 引擎运行时 100% (MEM UP + healthz 1-2ms) · 数据一致性 100% · 流程完整性 100% · 文档完整度 100% · 测试覆盖 100% (21 BDD + FIX-T112 3/3)
- 🔑 **承诺服务**: 6 大类 (流程设计 / 流程运行 / 客户反馈 / 文档 / 测试 / 反馈闭环) · 45 项 · 100% 经实测验证

### 2026-09-22 · v1.14 · Phase 9 Day 1 启动 (W40 周报)

- 🎯 **新建** `weekly/2026-W40.md` · Phase 9 Day 1-5 行动计划 + 验收标准
- 🎯 **更新** README.md §8.1 → Phase 9 Day 1 节奏 · W40 Week 计划
- 🎯 **更新** README.md §4.2 关键数字 (Phase 9 启动状态)
- 🎯 **通知** flowuser Phase 9 启动 · DM 已送达 + 已收到确认
- 🔑 **里程碑**: Phase 8 收官 + Phase 9 Day 1 完成. W40 Week 节奏已就位. flowuser 收到 Phase 9 启动通知, 等 Day 2 跟进.

### 2026-09-23 · v1.15 · Phase 9 Day 2 (W40 客户跟进 + 2 新 FB)

- 🎯 **完成** W40 Day 2 客户跟进:
  - **FB-0007 BUG-2 (FIX-T112) 复测 PASS** (实例 92116610518127, expense_report_v3)
  - FB-0008/0009/0010 文档/字段/验证 均 ✅
- 🎯 **新建** `feedback/inbox/FB-0011.json` · 变量作用域铁律 (doc P1, owner=bro docs)
- 🎯 **新建** `feedback/inbox/FB-0012.json` · submitType 拓扑陷阱 (doc P1, owner=bro docs)
- 📊 **累计 FB**: 10 闭环 + 2 in flight = **12 条**
- 📊 **累计 fix**: 7 项 (含本日确认 BUG-2 复测 PASS)
- 🔑 **里程碑**: Phase 9 Day 2 完成. BUG-2 真正修复 PASS 验证 (flowuser 本地复测). 2 个新文档陷阱登记 (待起草补丁, 类似 FB-0008/0009 流程).

### 2026-09-24 · v1.16 · Phase 9 Day 3 (W40 候选评估)

- 🎯 **新建** `roadmap/candidates/auto-assignee-by-org-evaluation.md` · 候选评估
- 🎯 **更新** W40 Day 3 状态
- 🔑 **关键洞察**: 3 个 doc FB (0006/0011/0012) + 候选 auto-assignee-by-org §6 可**整合成一次文档大整改**, 节省 ~50% 工作量
- 🔑 **决策**: 短期整合 3.1.1 + 3.1.2 (文档层); 中期 3.2.2 (API 暴露); 长期观察 3.3.x (引擎改动, 待更多客户)

### 2026-09-25 · v1.17 · Phase 9 Day 4 (FB-0011 文档补丁起草)

- 🎯 **完成** FB-0011 文档修订 (3 处):
  - **docs/flow.md §7.1** 新增章节 (变量作用域铁律 + 4 行表格 + 铁律示例 + BUG-2 教训)
  - **docs/AGENTS.md §6 约束 #32** 新增 (引用 §115)
  - **docs/known-issues.md §115** 新增全文 (3 版本复测实证 + 铁律速查)
- 🎯 **新建** `feedback/attachments/FB-0011-patches/` (索引 + 等 bro apply)
- 🎯 **更新** FB-0011 status → in_progress
- 📊 累计 FB: 10 闭环 + 2 in flight = 12 条
- 🔑 **里程碑**: Phase 9 Day 4 完成. L1 软接触标记 pending (需浏览器). FB-0011 文档草案完成 (整合 Day 3 评估建议).

### 2026-09-26 · v1.18 · Phase 9 Day 5 (W40 周复盘 + FB-0011 通知)

- 🎯 **通知** flowuser FB-0011 patches 待 review · DM 已送达 + 周末愉快确认
- 🎯 **更新** W40 Day 5 状态 + 验收标准
- 🔑 **W40 Week 1 of Phase 9 战绩**:
  - Day 1 节奏启动 (Phase 9 + W40 周报)
  - Day 2 客户跟进 (3 件事 + BUG-2 复测 PASS + FB-0011/0012 登记)
  - Day 3 候选评估 (auto-assignee-by-org + 整合洞察)
  - Day 4 文档补丁 (FB-0011 3 处修订)
  - Day 5 周复盘 + 通知 (本节)
- 🔑 **未完成**: L1 软接触 Step 2 (pending 浏览器) + metrics W40 周统计 (周一)

### 2026-09-22 · v1.12 · 解冻提案 + Phase 9 + 全部 backlog 项

- 🎯 **新建** `skills/proposals/UNFREEZE-PROPOSAL-2026-09-22.md` · 解冻提案 (5/5 条件 + 90 天计划 + 双签字段)
- 🎯 **新建** `skills/roadmap/phase9-90day-plan.md` · Phase 9 90 天详细计划 (3 个月 × 12 周)
- 🎯 **新建** `skills/customers/l1-acquisition-v2.md` · L1 软接触 Step 1 (类型 C 工作流产品公司选定)
- 🎯 **新建** `skills/FAQ.md` · 客户自助 FAQ (8 大节, 来自 FB-0006/0008/0009 + 隐含咨询)
- 🎯 **新建** `skills/customers/_templates/journey-evidence-template.md` · 客户旅程实证模板 (BL-006 落地)
- 🎯 **更新** README.md §3 架构图 (新增 proposals + FAQ)
- 🎯 **更新** README.md §4.2 关键数字 (反映解冻提案状态)
- 🔑 **里程碑**: Phase 8 全面收官. 解冻提案就绪等 bro 双签. Phase 9 计划就绪启动.

### 2026-09-21 · v1.7 · 第 2 次 users.md 任务执行 (机制稳定性验证)

- 🎯 **完成** `users.md` 任务第 2 次 · 改进后话术验证成功
- 📝 **更新** `customers/C-001.yaml` · 加 `stage_6_evidence` 段 + 诚实交代备注
- 🎯 **新建** `feedback/retrospectives/2026-09-21-users-md-task-2nd.md` · 第 2 次任务执行复盘
- 🔑 **关键发现**: 0 新 BUG (机制从"启动" 进入"维护"阶段); flowuser 诚实交代 user1 的 assignee≠operator 真实场景 (非 BUG, 入 C-001.yaml)

### 2026-09-21 · v1.6 · CLI 角色正式化 (backlog BL-008)

- 🎯 **扩充** `SKILL-TREE.md §补充 D` · CLI 角色从简述升级为 11 节完整定义
  - §1 定位 + 不做什么
  - §2 为什么需要 (5 项改进)
  - §3 与其他角色关系 (8 项)
  - §4 7 层详细能力 (含当前状态)
  - §5 关键产出物清单
  - §6 实战案例 (FB-0001~0008)
  - §7 工具与话术
  - §8 失败模式 (8 项反模式)
  - §9 晋升路径
  - §10 交叉引用 (7 个文档)
  - §11 当前评级 (L4)
- 📝 **更新** `RACI.md §2` · 加 CLI 角色 ⓘ 提示指向 SKILL-TREE.md
- 📝 **更新** `backlog/index.md` · BL-008 决议落地

### 2026-09-21 · v1.5 · 补丁就绪 + 复现手册

- 🎯 **新建** `feedback/attachments/FB-0008-patches/` · 3 个文档补丁 (FIX-DOC-2)
  - `flow.md.patch.md` · docs/flow.md §3.3 修订方案
  - `AGENTS.md.patch.md` · docs/AGENTS.md §5.8 修订方案
  - `known-issues-§113.md` · docs/known-issues.md §113 新增全文
  - `README.md` · 补丁索引
- 🎯 **新建** `feedback/attachments/FB-0007-repro-manual.md` · 7 节复现手册给 bro (FIX-T112)
- 📝 **更新** `feedback/inbox/FB-0007.json` · status=in_progress + linked repro manual
- 📝 **更新** `feedback/inbox/FB-0008.json` · status=in_progress + linked patch set

### 2026-09-21 · v1.4 · 首次真实用户协同 (FB-0007 + FB-0008)

- 🎯 **完成** `users.md` 任务 · `hermes peer dm flowuser` 通道验证成功
- 🎯 **新建** `feedback/inbox/FB-0007.json` · BUG-2 真 BUG (P0 / engine) 来自 flowuser
- 🎯 **新建** `feedback/inbox/FB-0008.json` · countersignCompletionCondition 文档缺失 (P1 / doc)
- 🎯 **新建** `feedback/retrospectives/2026-09-21-users-md-task.md` · 任务执行复盘
- 🎯 **新建** `feedback/attachments/FB-0007-INDEX.md` · 取件码机制验证记录
- 🎯 **新建** `feedback/retrospectives/` 目录 · 复盘存档
- 📝 **升级** `users.md` · 推荐话术模板 + 工具说明 + 实战案例

### 2026-09-21 · v1.3 · 客户数据硬约束 + 节奏机制

- 🔒 **强化** `FREEZE.md §6.2` · 客户数据绝对不可触碰 (reset 禁令)
- 🔒 **强化** `users.md` · 顶部加 reset 限制警告
- 🎯 **新建** `weekly/` 目录 + `2026-W39.md` · 周报机制
- 🎯 **新建** `backlog/` 目录 + `index.md` · 想法池 (8 条)
- 📝 **更新** README.md · 架构图加 `weekly/` + `backlog/` 节奏层

### 2026-09-21 · v1.2 · Phase 8.1 完成 + 解冻条件 5/5 满足

- 🎯 **新建** `customers/C-001/journey-evidence/2026-09-full-journey.md` · 4/6 段旅程实证
- 🎯 **新建** `customers/l1-acquisition.md` · L1 引擎客户招揽策略 (4 类画像 + 7 步流程 + 话术模板)
- 🎯 **关闭** `feedback/inbox/FB-0002.json` · C-002 客户 24h 确认后闭环
- 🎯 **新建** `feedback/metrics/monthly-2026-09.json` v2 · 6/6 闭环
- 🎯 **新建** `feedback/metrics/trends.md` v2 · 解冻条件 5/5 满足
- 🎯 **更新** `SKILLS.md` · 让位 README.md 为首要入口
- 🎉 **里程碑** · 可提议解冻 (按 `FREEZE.md §7`, 但本阶段不提议, 见 weekly/2026-W39.md)

### 2026-09-21 · v1.1 · Phase 8.1 跑通首个闭环

- 🎯 **新建** `skills/README.md` (本文件) · 总体计划 living document
- 🎯 **新建** `SKILLS.md` / `FREEZE.md` / `CUSTOMER.md` / `FEEDBACK.md` / `ROADMAP.md` / `SKILL-TREE.md` / `RACI.md` · 7 个制度文档
- 🎯 **新建** `feedback/` 目录结构 + 6 条 FB-NNNN (5 闭环 + 1 待确认)
- 🎯 **新建** `customers/` 目录 + 3 个客户档案 (C-001 / C-002 / C-006)
- 🎯 **新建** `roadmap/candidates/auto-assignee-by-org.md` · 来自 FB-0006
- 📝 **更新** `users.md` · 加入远程服务 URL + "不要闭门造车" 原则 (来自团队上下文)

### 2026-09-21 · v1.0 · 起点

- 📌 起点文档: `RML.md` (10 角色全景)
- 📌 起点文档: `users.md` (与 flowuser 沟通约定)

⏱️ Last updated: 2026-09-21

---

## 7. 进步记录 (Progress · 持续更新)

> 本节跟踪"我们做得更好"的信号.
> 每条进步必须有: 量化指标 + 时间 + 来源.

### 7.1 已记录的进步

| 日期 | 进步 | 量化 | 来源 |
|------|------|------|------|
| 2026-09-21 | **闭环率达成 100%** | 6/6 > 目标 80% | `feedback/metrics/monthly-2026-09.json` v2 |
| 2026-09-21 | **P0 闭环率** | 100% (3/3) | 同上 |
| 2026-09-21 | **客户旅程实证** | 4/6 段 (C-001) > 目标 3 | `customers/C-001/journey-evidence/` |
| 2026-09-21 | **解冻条件 5/5 满足** | 全部 5 项达成 | `feedback/metrics/trends.md` |
| 2026-09-21 | 平均闭环周期 | 0.33d (远低于 SLA) | 同上 |
| 2026-09-21 | 客户回复率 | 100% (6/6) | 同上 |
| 2026-09-21 | 客户档案建立 | 3 个 (含 L3 / L2) + L1 招揽策略 | `customers/index.md` |
| 2026-09-21 | 文档沉淀 | 4 处 docs/ 增量更新 | FB-0001 ~ FB-0005 |
| 2026-09-21 | 制度体系完整 | 7 个核心文档就位 | 本文件 §3 |
| 2026-09-21 | 候选改进池 | 1 项 (auto-assignee-by-org) | `roadmap/candidates/` |

### 7.2 待记录的进步 (下一步)

- [ ] 提议解冻 (FREEZE.md §7) · 本周
- [ ] 起草 Phase 9 解冻后 90 天工作清单 · 本周
- [ ] 双签 (hermes + bro) · 本周
- [ ] 启动 L1 客户招揽 · 本月
- [ ] 月度报告 `feedback/metrics/monthly-2026-10.json` · 月初
- [ ] 跟踪 C-001 阶段 6 (复盘/续办) · 持续

⏱️ Last updated: 2026-09-21

---

## 8. 改进记录 (Improvements · 进行中)

> 本节跟踪"我们当前正在做什么" + "我们刚做完什么".
> 与 §6 变更日志的区别: 变更是历史, 改进是当下.

### 8.1 正在做 (🟡) · W40 Week 1 收盘 · 等 W41 Day 1 (周一)

#### A. Phase 8 收官确认 ✅

| 改进 | FB ID | 修复 | 状态 |
|------|-------|------|------|
| BUG-2 本地复现 + 修复 | FB-0007 | FIX-T112 | ✅ 已完成 (flowuser 复测 PASS) |
| apply FB-0008 文档修订 | FB-0008 | FIX-DOC-2 | ✅ 已完成 |
| apply FB-0009 文档修订 | FB-0009 | FIX-DOC-3 | ✅ 已完成 |
| 源码验证 FB-0010 | FB-0010 | (a) 设计如此 | ✅ 已验证 |

#### B. Phase 9 Week 1 (W40) 完成

- [x] ✅ **Day 1** · W40 周报 + 解冻提案 + Phase 9 90 天计划
- [x] ✅ **Day 2** · 客户跟进 (3 件事 + BUG-2 复测 PASS + FB-0011/0012 登记)
- [x] ✅ **Day 3** · 候选评估 (auto-assignee-by-org + 整合洞察)
- [x] ✅ **Day 4** · FB-0011 文档补丁 (3 处修订完成)
- [x] ✅ **Day 5** · 周复盘 + 通知 flowuser
- [ ] 🔵 **Weekend** · 跟踪 C-001 阶段 6 (9/27 后) · 整理沉淀

#### D. 等 bro / 时间 (跨周)

| 改进 | FB ID | 修复 | 优先级 | 状态 |
|------|-------|------|--------|------|
| ~~apply FB-0011~~ | FB-0011 | FIX-DOC-4 | P1 | 🟡 待 bro apply (3 处修订就绪) |
| 起草 FB-0012 patches | FB-0012 | FIX-DOC-5 | P1 | 🔵 待 flowuser 提供 submitType=20 实证 |
|  签名解冻提案 | - | - | - | 🟡 bro 待签 (7 天内, FREEZE.md §7) |
| L1 软接触 Step 2 | - | - | 中 | 🟡 pending 浏览器 (Camunda + Flowable) |
| 跟踪 C-001 阶段 6 | - | - | 中 | 🔵 2026-09-27 后 |

#### C. W41 Week 计划 (Day 1-5 · 2026-09-29 ~ 10-03)

| Day | 行动 | 关联 |
|-----|------|------|
| Day 1 (周一) | 写 W41 周报 + metrics W40 周统计 + README 更新 | `weekly/2026-W41.md` |
| Day 2 (周二) | 联系 flowuser 周一回看结果 + 等 bro apply 反馈 | `feedback/inbox/FB-0011.json` |
| Day 3 (周三) | 起草 FB-0012 patches (等 flowuser 实证) | `roadmap/candidates/` |
| Day 4 (周四) | 加入 Camunda Forum + Flowable (如可) | `customers/l1-acquisition-v2.md` |
| Day 5 (周五) | W42 周报 + README + metrics | `weekly/2026-W42.md` |

#### D. 解冻提案状态

- hermes ✅ 已签 (2026-09-22)
- bro 🟡 待签 (7 天内, FREEZE.md §7) · 截止 2026-09-29

⏱️ Last updated: 2026-09-26 (W40 Week 1 收盘)

### 8.2 刚做完 (✅ · 最近 7 天)

| 改进 | 完成日 | 关联 |
|------|--------|------|
| **FB-0007 repro manual** (7 节, 给 bro) | 2026-09-21 | `feedback/attachments/FB-0007-repro-manual.md` |
| **FB-0008 补丁 3 件** (flow.md + AGENTS.md + known-issues §113) | 2026-09-21 | `feedback/attachments/FB-0008-patches/` |
| **首次真实用户协同** (FB-0007 + FB-0008) | 2026-09-21 | `feedback/retrospectives/2026-09-21-users-md-task.md` |
| **取件码机制验证** (5 文件逐个 DM 索取) | 2026-09-21 | `feedback/attachments/FB-0007-INDEX.md` |
| **users.md 话术升级** (推荐模板 + 工具说明) | 2026-09-21 | `users.md` |
| **FB-0002 闭环** (C-002 24h 内确认) | 2026-09-21 | `archive/FB-0002.json` |
| **C-001 旅程实证** (4/6 段完整) | 2026-09-21 | `customers/C-001/journey-evidence/2026-09-full-journey.md` |
| **L1 招揽策略** (4 类画像 + 7 步流程) | 2026-09-21 | `customers/l1-acquisition.md` |
| **metrics 完整化** (monthly + trends v3) | 2026-09-21 | `feedback/metrics/` |
| **客户数据硬约束** (FREEZE.md §6.2) | 2026-09-21 | `FREEZE.md` |
| **weekly/backlog 节奏机制** | 2026-09-21 | `weekly/` + `backlog/` |
| **SKILLS.md 让位** README.md | 2026-09-21 | `SKILLS.md` |
| 建立反馈闭环基础设施 | 2026-09-21 | `feedback/README.md` |
| 跑通 FB-0001 完整闭环 | 2026-09-20 | `archive/FB-0001.json` |
| 沉淀 4 处 docs/ 增量 | 2026-09-18 ~ 21 | §5.1 表 |
| 启动客户档案 | 2026-09-21 | `customers/` |

⏱️ Last updated: 2026-09-21

---

## 9. 展望 (Outlook · 远期)

### 9.1 Phase 9 · 反馈驱动改进 (待解冻)

**触发**: `FREEZE.md §4.1` 5 项条件满足 (当前 4/5)

**核心方向** (按客户反馈排序, 不按工程师直觉):

| 方向 | 来源 | 预计工作量 |
|------|------|------------|
| 修复 Top-N BUG | feedback 季度统计 | 月 3-5 个 |
| 补齐 Top-N 流程模式 | 客户咨询 (如 FB-0006) | 季度 3-5 个 |
| 完善 Top-N 文档 | doc 类反馈 | 持续 |
| 按组织架构选审批人示例 (FB-0006 派生) | C-006 | 1-2 周 |

### 9.2 Phase 10 · 客户增长 (远期)

> 不规划细节, 仅作方向锚定.

- 客户分层运营 (L1 / L2 / L3 不同策略)
- 客户成功体系 (NPS / 健康度)
- 规模化复制 (从单团队到多团队)

### 9.3 不会做的事 (明确列出)

- ❌ 新节点类型 (无客户需求)
- ❌ 性能优化 (§7.1 历史已取消)
- ❌ 安全加固 (§7.4 历史已取消)
- ❌ 国际化 / 多语言
- ❌ 开源 / SDK
- ❌ UI 重构 (UI 不是当前瓶颈)
- ❌ 移动 App
- ❌ AI 自动化设计器 (越界)
- ❌ 区块链审计 (与私用定位不符)

详见 `ROADMAP.md §5`.

⏱️ Last updated: 2026-09-21

---

## 10. 如何使用本目录 (How to Use)

### 10.1 阅读路径

| 你是谁 | 先读什么 |
|--------|----------|
| **新成员** | 本文件 → `FREEZE.md` → `FEEDBACK.md` → `SKILL-TREE.md` |
| **客户接口人** | 本文件 → `CUSTOMER.md` → `feedback/README.md` |
| **流程设计师** | 本文件 → `FEEDBACK.md` §3.3 → `flow.md` (docs/) |
| **引擎开发者** | 本文件 → `FREEZE.md` §6 例外 → `BUGS.md` (docs/) |
| **决策者** | 本文件 → `ROADMAP.md` → `feedback/metrics/trends.md` |

### 10.2 写新文件时

1. 选对位置 (制度/框架/数据/接口)
2. 引用本文 §3 架构图
3. 在本文 §6 变更日志追加
4. 在相关 §7/§8 记录进展

### 10.3 更新本文件

任何工作进展都应更新本文:
- 完成闭环 → §5 + §7
- 启动新工作 → §8.1
- 完成工作 → §8.2 + §7
- 变更范围 → §6
- 远期调整 → §9

⏱️ Last updated: 2026-09-21

---

## 11. 维护规则 (Maintenance)

| 规则 | 说明 |
|------|------|
| **谁更新** | hermes (主) / bro (副, 仅 engine 相关) / CLI (新增角色) |
| **何时更新** | 任何 skills/ 下文件变更, 必须同步更新本文 §6 |
| **不可破坏** | §3 架构图与 §10 阅读路径, 是其他人的导航, 改了要广播 |
| **每周一次** | 周五复盘: §7 / §8 状态, §4 数字 |
| **每月一次** | 月初: §4 + §5 更新, `feedback/metrics/monthly-YYYY-MM.json` |
| **季度一次** | 季度末: §9 调整, `roadmap/quarterly/YYYY-QX.md` |

⏱️ Last updated: 2026-09-21

---

## 12. 版本

- **v1.0** · 2026-09-21 · 起点 (RML.md + users.md)
- **v1.1** · 2026-09-21 · 制度体系就位 + 首个闭环完成
- **v1.2** · 2026-09-21 · Phase 8.1 完成 + 解冻条件 5/5 满足
- **v1.3** · 2026-09-21 · 客户数据硬约束 + weekly/backlog 节奏机制
- **v1.4** · 2026-09-21 · 首次真实用户协同 (FB-0007 + FB-0008)
- **v1.5** · 2026-09-21 · FB-0007 repro manual + FB-0008 补丁 3 件
- **v1.6** · 2026-09-21 · CLI 角色正式化 (backlog BL-008)
- **v1.7** · 2026-09-21 · 第 2 次 users.md 任务执行 (机制稳定性验证)
- **v1.8** · 2026-09-21 · 第 3 次 users.md 任务 (换角度 + delegate/surrogate 实证)
- **v1.9** · 2026-09-21 · 第 4 次 users.md (轻量) + FB-0009 patches 起草
- **v1.10** · 2026-09-21 · 下一步行动项 (§8.1 重构为权威快照)
- **v1.11** · 2026-09-22 · 4 项 fix 全部完成 + 全部闭环 (10/10)
- **v1.12** · 2026-09-22 · 解冻提案 + Phase 9 + 全部 backlog 项
- **v1.13** · 2026-09-22 · **SLA v13 健康度报告 (Phase 8 收官)**
- **v1.14** · 2026-09-22 · Phase 9 Day 1 启动 (W40 周报)
- **v1.15** · 2026-09-23 · Phase 9 Day 2 (客户跟进 + 2 新 FB)
- **v1.16** · 2026-09-24 · Phase 9 Day 3 (候选评估 + 整合洞察)
- **v1.17** · 2026-09-25 · Phase 9 Day 4 (FB-0011 文档补丁起草)
- **v1.18** · 2026-09-26 · **Phase 9 Day 5 (W40 周复盘 + FB-0011 通知)** (本版本)
- **v1.19** · 2026-09-26 · §8.1 下一步行动项快照更新 (W40 收盘 → W41 启动)
- **v1.20** · 2026-09-29 · W41 周报 (Week 2 of Phase 9)
- **v1.21** · 2026-10-06 · W41 Day 1-5 全部交付 · 包含 metrics W40 + 月度 10 月 + L1 v3 + C-001 跟踪 + W42 周报 + Q3 复盘计划
- **v1.22** · 2026-10-13 · W42 Day 1-5 全部交付 · 包含 Q3 复盘 published + FB-0012 patches 草稿 + UNFREEZE 跟踪 + W43 周报 + Month 1 收官准备
- **v1.23** · 2026-10-20 · W43 Day 1-5 全部交付 · 包含 Month 1 metrics + Month 2 启动清单 + FAQ 0.1 起草 + Month 1 收官 published + W44 周报 + Month 2 启动准备就绪
- **v1.24** · 2026-10-27 · W44 Day 1-5 全部交付 · 包含 Month 2 启动清单 v1.0 + auto-assignee-by-org 0.2 方案 + BDD #1801 设计 + bro 第 3 次询问 (deadline 升级) + W45 周报 + Month 2 Week 2 启动
- **v1.25** · 2026-10-22 · W45 Day 1-5 + fix all · 包含 omarchy 持续贡献 (取件码 97841) + FB-0014 闭环 (BUG-3 + FIX-T113 + W014) + W014 verify 规则纳入 SLA 工具集 (32/32 PASS) + FAQ 0.2 + auto-assignee-by-org 流程模式示例 + W46 月报 + 月度 metrics 10 月首月
- **v1.26** · 2026-11-10 · W46 Day 1-5 + W47 Day 1-5 + fix all · 包含 flowuser 8 轮 DM 跨月协同 + omarchy 第 3 次贡献 (取件码 39376) + FB-0015 闭环 (BUG-4 + FIX-T114) + BDD #1901-#1905 REJECT orphan 回归测试设计 + top-N v1.0 published + FAQ v1.1 升级 (24 题) + W47 月报 + monthly metrics 11 月 + C-001 Day 45 跟踪 (健康度 9.4)
- **v1.27** · 2026-11-17 · **W47 fix all + Month 2 收官 + Q4 准备 (本版本)** · 包含 bro 第 4 次询问草稿 (改为月度) + Month 2 收官报告 published v1.0 + docs/known-issues §117 (W009 warning) + Q4 季度复盘准备 + SKILL-TREE.md v1.1 (5 新章节) + RML.md 更新 + SLA HISTORY.md v13.1 + C-002 + C-006 健康检查 + README v1.27
- **v1.28** · 2026-11-17 · **spi/dev 重构 v8 · 部门 LEV 层级编码** · DEPTS.json 加 lev + parent_lev 字段 (5 部门, `99` / `99_01` / `99_01_02` 等) · data.py 加 SPI_DEPTS_LEV 派生常量 + `_build_dept_lev` 函数 · API 100% 不变 · spi/demo/ 硬约束维持 · v8 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v8-dept-lev.md)
- **v1.29** · 2026-11-17 · **spi/dev 重构 v9 · 部门 tree 结构 (替换 v8 LEV)** · DEPTS.json lev/parent_lev → parent_id (5 部门, 顶层 D99 parent_id=null) · 移除 `SPI_DEPTS_LEV` 常量 · 新增 `SPI_DEPTS_TREE` 派生嵌套结构 (D99 → D01 → {D02, D03, D04}) · `_build_dept_tree` 4 步手写递归 (零 tree 库依赖) · API 100% 不变 · spi/demo/ 硬约束维持 · v9 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v9-dept-tree.md)
- **v1.30** · 2026-11-17 · **spi/dev 重构 v10 · verify() 数据完整性校验** · data.py 新增 `verify()` 函数 + 3 个 `_verify_*` 辅助函数 (cross_refs / tree / completeness) · 4 类检查 (跨表引用 + tree 结构 + 完整性 + 警告) · errors vs warnings 分级 · 零依赖 (手写校验) · API 100% 不变 · spi/demo/ 硬约束维持 · 验证 7/7 PASS (含 5 错误注入 + 1 警告 + 1 正常) · v10 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v10-verify.md)
- **v1.31** · 2026-11-17 · **spi/dev 实战演练 · 请假审批完整流程 (基于 dev SPI 实际数据)** · 启动 main.py (8101, SPI_FOLDER=dev) · 流程文件 flows/18-leave-dev.json (5 节点 4 边) · 完整链路: 周磊 (u_fe_eng) 申请 → 刘洋 (u_fe_lead) 审批 → 王强 (u_rd_dir) 审批 → END · 验证 SPI 注入: variables.u_realName=周磊, u_deptId=D02, u_deptName=前端组 ✅ · 8 角色返回 ✅ · verify() PASS ✅ · 发现修复 2 项 (deploy content 字段 + assignee 直接指定) · 实战复盘 published (skills/feedback/retrospectives/2026-11-17-dev-spi-walkthrough-leave-flow.md)
- **v1.32** · 2026-11-17 · **spi/dev 重构 v11 · 部门导航派生常量** · 新增 `SPI_USERS_BY_DEPT` (dept_id→[uids]) + `SPI_DEPT_LEADER_BY_USER` (uid→leader_uid) 2 个派生常量 · 解决演练 gap ("周磊的组长"硬编码问题) · DictProxy 热加载 · 错误注入 4/4 PASS (用户空 deptId / 部门空 leader / 新增用户 / 恢复) · verify() summary 加 2 字段 · v11 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v11-dept-navigation.md)
- **v1.33** · 2026-11-17 · **spi/dev 重构 v12 · 树遍历派生 (ancestors + descendants)** · 新增 `SPI_DEPT_ANCESTORS` (dept_id→[self, parent, ..., root]) + `SPI_DEPT_DESCENDANTS` (dept_id→[self, child, ..., leaf]) · 深度优先 + 防环 (seen/visited) · 4/4 PASS (环/悬空/新增/恢复) · ANCESTORS[D02]=['D02','D01','D99'] (3 层), DESCENDANTS[D99]=[5 部门全部] · verify() summary 加 2 字段 · v12 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v12-tree-traversal.md)
- **v1.34** · 2026-11-17 · **spi/dev 重构 v13 · 用户视角路径 (main_leader + dept_chain)** · 新增 `SPI_DEPT_MAIN_LEADER_BY_USER` (uid→main_leader_uid) + `SPI_USER_DEPT_CHAIN` (uid→[dept_ids]) · 对称 v11 SPI_DEPT_LEADER_BY_USER (组 pair) · 复用 v12 ANCESTORS (DRY) · 4/4 PASS (空 deptId / 空 main_leader / 正常 / 恢复) · MAIN_LEADER 周磊→王强, USER_DEPT_CHAIN 周磊→[D02,D01,D99] · verify() summary 加 2 字段 · v13 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v13-user-perspective.md)
- **v1.35** · 2026-11-17 · **spi/dev 重构 v14 · 用户完整领导链 (USER_LEADER_CHAIN)** · 新增 `SPI_USER_LEADER_CHAIN` (uid→[leader_uids]) · 组合 v13 USER_DEPT_CHAIN + 每 dept leader, 去重 + 顺序保留 · 4/4 PASS (空 deptId / 空 leader / 顶层 / 恢复) · 周磊→[u_fe_lead,u_rd_dir,u_ceo] (3 级) · QA→[u_rd_dir,u_ceo] (2 级) · CEO→[u_ceo] (1 级) · verify() summary 加 1 字段 · v14 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v14-user-leader-chain.md)
- **v1.36** · 2026-11-17 · **spi/dev 重构 v15 · USERS 按职级聚合 (BY_LEVEL)** · 新增 `SPI_USERS_BY_LEVEL` (level→[uids]) · 复用 v11 BY_DEPT 模式 · 6 个 level (P5-P10) · 4/4 PASS (空 level / D02 ∩ P5={u_fe_eng} / P8+=4 领导 / 恢复) · 复合查询自然 · verify() summary 加 1 字段 · v15 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v15-by-level.md)
- **v1.37** · 2026-11-17 · **spi/dev 重构 v16 · 用户集成视图 (USERS_FULL)** · 新增 `SPI_USERS_FULL` (uid→rich_dict, 13 字段) · 复用 v9-v15 派生常量 · 6 跳查询 → 1 跳 · 4/4 PASS (空 deptId / 空 leader / 新增用户 / 恢复) · 周磊 = {name, dept_name, leader, main_leader, dept_chain, leader_chain, colleagues} · verify() summary 加 1 字段 · v16 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v16-users-full.md)
- **v1.38** · 2026-11-17 · **spi/dev 重构 v17 · 部门集成视图 (DEPT_FULL_INFO)** · 新增 `SPI_DEPT_FULL_INFO` (dept_id→rich_dict, 10 字段, v16 USERS_FULL 对称) · 复用 v9-v16 派生常量 · 4/4 PASS (减员 / 空 leader / 空部门 / 恢复) · D02={members:3, level_dist:{P5:1,P6:1,P7:1}, depth:3, is_leaf:true} · D99={depth:1, is_leaf:false, size:2} · verify() summary 加 1 字段 · v17 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v17-dept-full-info.md)
- **v1.39** · 2026-11-17 · **spi/dev 重构 v18 · verify() 扩展 (ROLE_TO_USERS 一致性校验)** · 新增 C4 检查 (从 DEPTS.role_combinations 推导 expected vs ROLE_TO_USERS actual) · **发现真实 bug**: ROLE_TO_USERS[tech_lead] 含 u_qa_lead, 但 DEPTS u_qa_lead 在 qa_engineer → 已修复 (ROLE_TO_USERS tech_lead 改为 2 人) · 4/4 PASS (缺 u_fe_lead error / 多余 u_qa_lead warning / DEPTS 修正 / 恢复) · verify() 4 类检查 · v18 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v18-role-consistency.md)
- **v1.40** · 2026-11-17 · **spi/dev 重构 v19 · 部门成员完整视图 (DEPT_MEMBERS_FULL)** · 新增 `SPI_DEPT_MEMBERS_FULL` (dept_id→[user_full_dicts]) · 组合 v16 USERS_FULL + v17 DEPT_FULL_INFO (基础 = dept_info, 含所有部门) · 4/4 PASS (减员 / 新增 / 总员数=13 / 恢复) · 修复空部门 KeyError bug (用 dept_info 作基础) · D02 3 成员完整档案 · D99 2 成员 (CEO + CTO) · verify() summary 加 1 字段 · v19 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v19-dept-members-full.md)
- **v1.41** · 2026-11-17 · **spi/dev 重构 v20 · search_users() 搜索函数 (首个 helper)** · 新增 `search_users(query) → list[uid]` 函数 · 4 字段匹配 (uid/name/post/email) · 大小写不敏感 · 优先级排序 · 性能 ~16μs/次 · 测试 PASS (周→u_fe_eng, u_fe→3 前端, 前端→3, CEO→u_ceo, 空→[]) · 19 DictProxy + 9 SPI 函数 API 不变 · v20 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v20-search-users.md)
- **v1.42** · 2026-11-17 · **spi/dev 重构 v21 · search_depts() 搜索函数 (对称 v20)** · 新增 `search_depts(query) → list[dept_id]` 函数 · 2 字段匹配 (dept_id/name) · 对称 v20 API 风格 · 测试 PASS (前端→[D02], D→[5 部门], D01→[D01], 组→[D02,D03,D04], 架构→[D04], 研发→[D01], 总→[D99]) · 19 DictProxy + 9 SPI 函数 + search_users 不变 · v21 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v21-search-depts.md)
- **v1.43** · 2026-11-17 · **spi/dev 重构 v22 · CLI 入口 (python -m spi.dev)** · 新增 `spi/dev/cli.py` + `__main__.py` (2 新文件, 0 修改) · 3 命令: `verify` / `status` / `help` · 返回码: 0=PASS, 1=FAIL, 2=ERROR · 符号输出 (✓/✗/⚠/❌) · 零依赖 (纯标准库) · CI 集成友好 · 19 DictProxy + 9 SPI 函数 + 2 helpers + verify() 不变 · v22 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v22-cli.md)
- **v1.44** · 2026-11-17 · **spi/dev 重构 v23 · 用户角色反向 (USERS_WITH_ROLES)** · 新增 `SPI_USERS_WITH_ROLES` (uid→[role_codes]) · 反向映射 ROLE_TO_USERS · 4 行核心算法 (DRY) · 13 用户全有角色 (v18 修复后一致) · 19 DictProxy + 9 SPI 函数 + 2 helpers + CLI v22 不变 · v23 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v23-users-with-roles.md)
- **v1.45** · 2026-11-17 · **spi/dev 重构 v24 · CLI 子命令扩展 (4 命令)** · 新增 4 命令: `list-users` (表格 13 用户) / `show-user <uid>` (完整档案) / `list-depts` (表格 5 部门) / `show-dept <dept_id>` (详情+成员) · cli.py 从 80 → 217 行 · 错误处理 (uid 不存在→exit 1, 缺参数→exit 2) · data.py 20 DictProxy + 2 helpers + 9 SPI 函数 不变 · v24 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v24-cli-extended.md)
- **v1.46** · 2026-11-17 · **spi/dev 重构 v25 · CLI → FastAPI 路由 (远程 API 暴露)** · 新增 `spi/dev/api.py` (FastAPI APIRouter) + 6 路由 (/api/spi/verify/status/users/{uid}/depts/{dept_id}) · 重构 cli.py 提取 `_data_*` 函数 (CLI 与 API 共享) · main.py +2 行 (import + register) · JSON 响应 + HTTPException 404 · 8/8 PASS (curl 全部 PASS) · 20 DictProxy + 2 helpers + 9 SPI 函数 + CLI v22-v24 不变 · v25 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v25-fastapi-routes.md)
- **v1.47** · 2026-11-17 · **spi 重构 v26 · CLI/API 统一在 dispatcher 层 (跟随 SPI_FOLDER)** · 新增 `spi/cli.py` + `spi/api.py` + `spi/__main__.py` (dispatcher 层) · 新增 `spi/demo/cli.py` + `spi/demo/api.py` (demo 实现层) · 改造 `spi/dev/cli.py` + `spi/dev/api.py` (移除 router/main, 仅 _data_*) · main.py 改用 `spi.api` (从 `spi.dev.api`) · spi/SPEC.md 新增 §8 (CLI/API 规范, 6 个 _data_* 函数约定) · 11/11 PASS (含跨 SPI_FOLDER 验证 + 缺失 cli/api 错误处理) · spi/dev/data.py 20 DictProxy + 2 helpers + verify() 100% 不动 · spi/demo/ 硬约束维持 (除新建 cli/api 外全部原始时间戳) · v26 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-v26-dispatcher-cli-api.md)
- **v1.48** · 2026-11-17 · **spi/dev 重构 v27 · (dept, role) 二维聚合 (USERS_BY_DEPT_ROLE)** · 新增 `SPI_USERS_BY_DEPT_ROLE` ((dept_id, role_code)→[uids]) · 4/4 PASS (D02 tech_lead / 跨 dept senior / 减员 / 角色移除) · 修复 bug: 用 USERS[uid].deptId (不是 SPI_USERS_BY_DEPT 反向) · 11 个 (dept, role) 组合 · 顺手补 demo summary.users_by_dept_role_count (跨 SPI_FOLDER 一致) · 20 DictProxy + 2 helpers + 9 SPI 函数 + verify() 不变 · v27 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v27-dept-role-2d.md)
- **v1.49** · 2026-11-17 · **spi 重构 v28 · spi 路由移到 main_common.py (双端共用)** · 新增 `register_spi_routes(app)` 函数 (main_common.py) · main.py + main_pg.py 同步集成 (双端一致) · 4/4 PASS (import / register / dev / demo) · 6 路由自动注册 (/api/spi/verify/status/users/users/{uid}/depts/depts/{dept_id}) · 与 register_routes / install_metrics_endpoint 调用模式对齐 · 21 DictProxy + 2 helpers + 9 SPI 函数 + verify() 不变 · v28 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-v28-main-common-routes.md)
- **v1.50** · 2026-11-17 · **spi/dev 重构 v29 · 用户部门角色反向 (USER_DEPT_ROLE)** · 新增 `SPI_USER_DEPT_ROLE` (uid→[(dept_id, role_code)]) · 与 v27 SPI_USERS_BY_DEPT_ROLE 互逆 · 5/5 PASS (基本查询 / 检查特定组合 / 减员 / 角色移除 / 恢复) · **互逆检查 0 mismatch** · 22 DictProxy + 2 helpers + 9 SPI 函数 + dispatcher CLI/API + main_common 双端不变 · v29 复盘 published (skills/feedback/retrospectives/2026-11-17-spi-dev-refactor-v29-user-dept-role.md)
- **v1.51** · 2026-11-17 · **同步 v22-v29 SPI 路由能力到 docs/ + skills/** · 5 份 docs 更新 (api.md §1.5 SPI 路由 + architecture.md §4.4 三层 dispatcher + integration.md §5.4/§5.5 SPI_FOLDER + main_common + AGENTS.md 约束 #33 SPI 路由必须 dispatcher + openapi.json 补 6 SPI 路径 + version 1.9.0+spi-v26-v29, 70→76 路径总) · 4 份 skills 更新 (SKILL-TREE.md §16 SPI dispatcher 章节 + SKILLS.md SPI 能力描述 + RML.md SPI 章节 + README.md v1.51) · 8 份 v22-v29 retrospective 已索引 · 数据层 100% 不动 (spi/dev/data.py 40020 bytes, 22 DictProxy + 2 helpers + verify() 保留)

> 本文件采用 living document 模式, 版本号仅在大变更时递增.
> 日常更新在 §6 变更日志体现.
