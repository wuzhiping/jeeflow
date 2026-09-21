# SKILL-TREE.md · 每角色实用技能进阶 (RML 扩展)

> **基础**: RML.md §1-§5 (10 角色 + 7 核心技能树 + AIFE 七层).
> **演化**: 把"角色定位 + 核心技能" 扩展为**可学习、可考核、可进阶**的体系.
> **视角**: 不仅"工程师", 包含客户视角的运营 / 反馈 / 培训角色.

---

## 1. 7 层能力阶梯 (沿用 AIFE · 演化)

```
 L7 造局    ←  定义场本身 (引擎开发者, 长期最高目标)
 L6 格局    ←  看见更大的场 (架构师 / 审计)
 L5 判断    ←  信息不足时决策 (流程开发者 / 客户接口人)
 L4 系统    ←  让流程自运转 (SRE / 集成)
 L3 协作    ←  跟人一起做 (培训师 / 反馈接收)
 L2 优化    ←  把事做更好 (QA)
 L1 完成    ←  把事做了 (业务审批人 / 客户)
```

**核心变化**:
- RML 把"角色" 和"层" 对应. 本文件增加**层与层之间**的进阶路径.
- 客户视角的 L3 / L5 / L6 角色被显式纳入 (RML 未明确).

---

## 2. 11 个角色 × 实用技能

> RML §1 列出 10 角色. 本文件增加"客户接口人" (L3 / L5 关键角色), 共 11.

### 角色 1 · 引擎开发者 (Engine Developer)

**目标**: 能独立修改 `vendor/jeeflow/*.py` 并通过 BDD.

| 层 | 能力 | 教材 | 考核 |
|----|------|------|------|
| L1 | 读懂现有引擎代码 + 跑通 BDD | `vendor/jeeflow/` + `docs/architecture.md` | 通读 1 周, 输出笔记 |
| L2 | 改一处不影响其它 (回归) | `bdd/*.sh` + `docs/BUGS.md` | 修复 1 个简单 BUG (他人验证) |
| L3 | 与流程设计师协作设计 API | `docs/api.md` + `docs/AGENTS.md` | 设计 1 个新 action 的契约 |
| L4 | 性能 / 并发 / 持久化 | `vendor/jeeflow/persist.py` | 双端一致性能测试 |
| L5 | 判断哪些 BUG 值得修 | `docs/known-issues.md` + 反馈数据 | 月度提交"应修 Top-3" |
| L6 | 引擎在 AIFE 大图定位 | `roadmap.md` (历史) + `RML.md` | 季度战略 review |
| L7 | 重新设计引擎核心 | 所有 docs/ | 重大重构 PR |

**关键产出** (按层):
- L1: 学习笔记
- L2: 1 个 BUG 修复 (FIX-T 编号)
- L3: 1 份 API 草案
- L4: 性能 baseline
- L5: 月度 BUG 优先级排序
- L6: 季度架构 review 报告
- L7: 重构设计文档

---

### 角色 2 · 引擎测试 (Engine QA)

**目标**: 跑全量 BDD 不漏, 发现回归.

| 层 | 能力 | 教材 | 考核 |
|----|------|------|------|
| L1 | 跑通 BDD / 解读结果 | `bdd/*.sh` | 跑通 1 套 |
| L2 | 写新 BDD 用例 | `bdd/` 模板 | 写 1 个新场景 |
| L3 | 配合流程测试找回归 | `tdd/` 历史 | 共建 1 个回归案例 |
| L4 | 设计压测 / 性能基线 | `bdd/bdd-1336-1340-perf-baseline.sh` | 出基准报告 |
| L5 | 判断哪些 BUG 是真 BUG | `docs/known-issues.md` | 提交 3 个"误报" |
| L6 | 建立测试战略 | `sla/check.sh` | 测试覆盖率报告 |
| L7 | 自动化整个测试体系 | 全部测试脚本 | CI/CD 集成方案 |

**关键产出**:
- L1: 跑通记录
- L2: BDD-NNNN.sh
- L3: 回归案例库
- L4: 性能报告
- L5: 误报清单
- L6: 测试战略文档
- L7: CI/CD 配置

---

### 角色 3 · 流程开发者 / 流程设计师 (Process Designer)

**目标**: 用现有 API 设计真实业务可跑通的流程.

| 层 | 能力 | 教材 | 考核 |
|----|------|------|------|
| L1 | 读懂 6 节点 + 写简单 JSON | `docs/flow.md` §3-§4 | 写 1 个 3 节点流程 |
| L2 | 字段权限 + 会签 4 模式 | `docs/flow.md` §5 | 写 1 个会签流程 |
| L3 | 决策 / 委托 / 回退 / 并发 | `docs/flow.md` §6 | 写 1 个决策流程 |
| L4 | 复杂场景 (嵌套决策 / fork-join) | `flows/04-fork-join.json` | 复刻一个复杂流程 |
| L5 | 判断哪些场景"流程能表达" | `docs/known-issues.md` §3-§5 | 月度"反模式清单" |
| L6 | 流程架构师 (跨流程一致) | `flows/README.md` | 流程族设计 |
| L7 | 自创流程范式 | 历史 19 个流程 | 提出 1 个新范式 |

**关键产出**:
- L1: `flows/01-simple.json` 复刻
- L2: `flows/05-countersign-parallel.json` 复刻
- L3: `flows/03-decision-expr.json` 复刻
- L4: `flows/04-fork-join.json` 复刻
- L5: `insights/03_pitfalls.md`
- L6: 流程族白皮书
- L7: 新范式 RFC

---

### 角色 4 · 流程测试 (Process QA)

**目标**: 把流程跑通并固化证据.

| 层 | 能力 | 教材 | 考核 |
|----|------|------|------|
| L1 | 用 curl 调 API 跑通 | `docs/api.md` | 跑通 1 个简单流程 |
| L2 | 校验 approvalRecord + 节点顺序 | `tdd/*.json` | 输出 tdd 报告 |
| L3 | 设计异常分支覆盖 | `flows/09-with-reject.json` | 写驳回场景 |
| L4 | 性能 / 并发 / 委托测试 | `bdd/bdd-1336-1340-perf-baseline.sh` | 性能报告 |
| L5 | 判断"是不是 BUG" | `docs/BUGS.md` | 提交 1 个真 BUG + 1 个误报 |
| L6 | 建立流程测试体系 | `tdd/README.md` | 测试覆盖率 |
| L7 | 自动化回归 | `sla/check.sh` | CI/CD 接入 |

**关键产出**:
- L1: `tdd/test_simple_<ts>.md`
- L2: `tdd/test_countersign_<ts>.md`
- L3: 异常分支矩阵
- L4: 性能报告
- L5: BUG 报告 (含 root cause)
- L6: 流程测试方法论
- L7: CI/CD 集成

---

### 角色 5 · 业务审批人 (Approver)

**目标**: 在 UI 上顺利提交 / 审批 / 委托 / 查进度.

| 层 | 能力 | 教材 | 考核 |
|----|------|------|------|
| L1 | 看懂通知, 点同意/拒绝 | UI 教程视频 | 提交 1 个申请 |
| L2 | 填字段不漏, 上传附件 | 字段说明 | 提交 3 个不同流程 |
| L3 | 看上下文, 委托他人 | 委托功能文档 | 委托 1 次 |
| L4 | 紧急回退 / 主动催办 | 回退功能文档 | 回退 1 次 |
| L5 | 给反馈 (FB-NNNN) | `skills/FEEDBACK.md` | 提交 1 条反馈 |
| L6 | 帮同事用 (非培训师) | FAQ | 帮 3 个同事 |
| L7 | 流程反推 (建议改流程) | `docs/flow.md` | 提出 1 个流程改进 |

**关键产出**:
- L1: 完成 1 次提交
- L2: 完成 3 次提交
- L3: 委托 1 次
- L4: 回退 1 次
- L5: 1 个 FB-NNNN (L3 客户最关键的能力)
- L6: 帮 3 个同事 (L3 客户成为"扩展团队")
- L7: 流程改进建议

**注意**: RML 把业务审批人列为角色 5 (内部); 本文件也把他视为 L3 客户.
两者**合体**, 这是私用项目的特殊性.

---

### 角色 6 · 架构师 / EA (Enterprise Architect)

**目标**: 把 jeeflow 放在企业架构大图里.

| 层 | 能力 | 教材 | 考核 |
|----|------|------|------|
| L1 | 理解 jeeflow 能力边界 | `docs/architecture.md` | 输出能力地图 |
| L2 | 对标 Camunda / Flowable | 公开资料 | 选型对比表 |
| L3 | 集成 ERP / OA | `docs/integration.md` | 集成方案 1 份 |
| L4 | 流程分层 (L0-L4) | TOGAF | 分层图 |
| L5 | 选型决策 | 决策树 | 1 个决策案例 |
| L6 | 长期战略 | 路线图 | 战略 review |
| L7 | 重新设计生态 | — | 战略重构 |

---

### 角色 7 · SRE / 运维

**目标**: 系统稳定 + 可监控.

| 层 | 能力 | 教材 | 考核 |
|----|------|------|------|
| L1 | 启动 / 重启 / 看日志 | `main.py` + `main_pg.py` | 启动双端 |
| L2 | 跑 SLA 检查 | `sla/check.sh` | 月度 SLA 100 分 |
| L3 | 看监控 + 告警 | `docs/deployment.md` | 监控面板 |
| L4 | trace / 排查 | `docs/api.md` trace 部分 | 定位 1 个慢请求 |
| L5 | 容量规划 | 历史指标 | 容量预测 |
| L6 | 灰度 / 回滚策略 | 部署文档 | 灰度方案 |
| L7 | 平台化 | K8s / Helm | 平台设计 |

---

### 补充 A · 培训师 / 推广

**目标**: 让普通员工会用 jeeflow.

| 层 | 能力 | 教材 | 考核 |
|----|------|------|------|
| L1 | 自己会用 | 角色 5 全部 | 跑通 5 个流程 |
| L2 | 录屏 + 写 SOP | OBS + Markdown | 1 个 5 分钟视频 |
| L3 | 培训新人 | SOP | 培训 3 人 |
| L4 | FAQ 维护 | `skills/FEEDBACK.md` 派生 | 20 条 FAQ |
| L5 | 飞书机器人答疑 | bot 框架 | 答疑 bot 上线 |
| L6 | 推广到其他团队 | 培训材料 | 1 个新团队 |
| L7 | 培训体系化 | 教材体系 | 完整培训计划 |

---

### 补充 B · 审计 / 合规

**目标**: 流程合规 + 反腐反舞弊.

| 层 | 能力 | 教材 | 考核 |
|----|------|------|------|
| L1 | 读懂审批记录 | `docs/architecture.md` | 输出 1 个审批链 |
| L2 | 反查决策 | `tdd/audit_logs/` | 反查 1 个案例 |
| L3 | 法规对接 | GDPR / 等保 / SOX | 合规清单 |
| L4 | 自动审计 | `bdd/bdd-1326-1330-trace-persist.sh` | 审计脚本 |
| L5 | 风险识别 | 审计案例 | 1 份风险报告 |
| L6 | 战略层审计 | 流程架构 | 季度报告 |
| L7 | 反舞弊机制 | 风控 | 反舞弊体系 |

---

### 补充 C · 集成开发者

**目标**: jeeflow ↔ 外部系统对接.

| 层 | 能力 | 教材 | 考核 |
|----|------|------|------|
| L1 | 调 API | `docs/api.md` | 调用 10 个 action |
| L2 | 写适配器 | `spi/` | 1 个 HR 同步适配器 |
| L3 | 事件驱动 | `docs/integration.md` | webhook 处理 |
| L4 | 数据同步 | HR / ERP | 双向同步方案 |
| L5 | 容错 / 重试 | 集成案例 | 容错设计 |
| L6 | 集成架构 | 集成大图 | 集成蓝图 |
| L7 | 平台化集成 | iPaaS | 平台设计 |

---

### 补充 D · 客户接口人 Customer Liaison (CLI · RML 未列, 本阶段新增)

> **正式名称**: 客户接口人 / Customer Liaison (CLI)
> **代号**: +D (RML 11 角色中第 11 个)
> **创建日期**: 2026-09-21 (Phase 8 启动)
> **创建原因**: RML §1 列出 10 个角色都是"系统内部角色", 但客户中心化转型需要**专职桥梁**
> **现状**: hermes 兼任 (Phase 8 小团队), Phase 10 后可独立

#### 1. 定位

**一句话**: 在 jeeflow 团队与客户之间建立可持续的双向对话, 让客户声音驱动系统改进.

**不做什么**:
- ❌ 不修引擎代码 (那是 bro / 角色 1)
- ❌ 不设计流程 JSON (那是 hermes 流程设计师部分 / 角色 3)
- ❌ 不承诺客户做不到的事 (无授权)
- ❌ 不替客户执行流程 (那是角色 5)
- ❌ 不冒充工程师身份 (必须明示 "hermes 助理" 不冒充 bro)

#### 2. 为什么需要

| 没有 CLI 的问题 | 有 CLI 后的改进 |
|------------------|------------------|
| 客户反馈 → tdd/ 后无人跟 | 反馈有专人接, 走 5 步闭环 |
| 工程师不知道客户要什么 | CLI 翻译客户语言 → 流程语言 |
| 客户不知道修没修 | CLI 给闭环通知 |
| 客户旅程没人跟踪 | CLI 维护客户档案 + 旅程实证 |
| 客户分层没人做 | CLI 按 L1/L2/L3 分层运营 |

#### 3. 与其他角色的关系

| 与谁 | 关系 | 协作方式 |
|------|------|----------|
| 角色 1 引擎开发者 (bro) | CLI ↔ bro | CLI 把客户反馈翻译给 bro, bro 修复后 CLI 通知客户 |
| 角色 3 流程设计师 (hermes 设计) | CLI ∈ hermes 一部分 | 同一团队, CLI 关注客户对话, 流程设计师关注实现 |
| 角色 4 流程测试 (PROCT) | CLI ↔ PROCT | CLI 收到 BUG 后通知 PROCT 复现验证 |
| 角色 5 业务审批人 | CLI ↔ L3 客户 | 角色 5 同时是 L3 客户代表, CLI 直接对话 |
| 角色 6 架构师 | CLI → 架构师 | CLI 输出客户洞察, 架构师纳入长期规划 |
| 角色 7 SRE | CLI ↔ SRE | SRE 关注健康度, CLI 关注客户感知 (性能 / 稳定性反馈) |
| +D 培训师 | CLI ↔ 培训师 | CLI 反馈高频问题, 培训师出 FAQ / SOP |

**关键**: CLI 是**翻译者**, 不是替代者. CLI 不修代码, 不写流程 JSON, 不做 SRE. CLI 把客户问题翻译给对应角色, 把对应角色的输出翻译给客户.

#### 4. 7 层详细能力 (RML AIFE 对齐)

| 层 | 能力 | 教材 | 考核 | 当前状态 |
|----|------|------|------|----------|
| **L1 完成** | 听懂客户业务场景, 写客户档案 | `skills/customers/C-NNN.yaml` 模板 | 1 份档案 | ✅ 3 份 (C-001 / C-002 / C-006) |
| **L2 优化** | 翻译客户语言为流程语言 | `docs/flow.md` + `docs/AGENTS.md` | 客户描述 → 流程图 | ✅ FB-0006 已答 (SPI assignmentHandler) |
| **L3 协作** | 接收 / 分类反馈 (5 步闭环第 1-2 步) | `skills/FEEDBACK.md §3.1-§3.2` | 处理 5 个 FB | ✅ 8 个 FB (6 闭环 + 2 进行) |
| **L4 系统** | 设计反馈闭环演练, 走完 1 个闭环 (5 步全) | `skills/FEEDBACK.md §3` 全章 | 走完 1 个闭环 | ✅ FB-0001 完整闭环 |
| **L5 判断** | 判断客户真实需求, 写季度客户洞察 | `skills/CUSTOMER.md §4` + §6 | 季度洞察文档 | 🟡 阶段 6 待补 |
| **L6 格局** | 客户成功规划, 战略级客户分层 | 客户成功方法 (CSM) | 客户成功计划 | ☐ 远期 |
| **L7 造局** | 重新定义客户分层 + 客户战略 | 商业模型 | 客户战略白皮书 | ☐ 远期 |

#### 5. 关键产出物清单 (按层)

| 层 | 产出物 | 位置 |
|----|--------|------|
| L1 | `skills/customers/C-NNN.yaml` | 客户档案 |
| L2 | 客户原始描述 → 流程 JSON | `tdd/` 或回应文档 |
| L3 | `skills/feedback/inbox/FB-NNNN.json` (≥ 5) | 反馈登记 |
| L4 | `skills/feedback/archive/FB-NNNN.json` (≥ 1 完整闭环) | 闭环档案 |
| L5 | `skills/feedback/metrics/quarterly-YYYY-QX.md` | 季度洞察 |
| L6 | `skills/roadmap/customer-success-plan.md` | 客户成功计划 |
| L7 | `skills/strategy/customer-strategy.md` | 客户战略白皮书 |

#### 6. 实战案例 (来自真实 FB)

| 案例 | 关键能力 | 成果 |
|------|----------|------|
| **FB-0001** (2026-09-19~20) | L1 + L2 + L3 + L4 | C-001 报销流程出纳跳过 BUG 闭环, FIX-T110 + W012 |
| **FB-0002** (2026-09-20~21) | L3 + L4 | ABANDON updateUser 修复, FIX-T111 |
| **FB-0006** (2026-09-20) | L2 (consult) | SPI assignmentHandler 咨询, 客户文档化 |
| **FB-0007** (2026-09-21) | L1 + L2 + L3 (首次真实客户) | BUG-2 真 BUG 发现, repro manual 给 bro |
| **FB-0008** (2026-09-21) | L2 + L3 (客户反哺) | countersignCompletionCondition 文档缺失, 3 补丁就绪 |

**关键洞察**: FB-0008 是客户在确认 FB-0007 时**主动反哺**的. 这证明 CLI 协作机制工作: 客户感到被认真对待, 会主动提更多问题.

#### 7. 工具与话术

| 工具 / 话术 | 用途 | 文档 |
|-------------|------|------|
| `hermes peer list` | 检查 peer 通道 | `hermes peer --help` |
| `hermes peer dm flowuser "..."` | 同步一次性 DM | `users.md` |
| `hermes peer run` | 异步长任务 | (备而不用) |
| 多轮小问模板 | 避免信息过载 | `users.md` |
| 取件码机制 | 文件高效共享 | `feedback/retrospectives/2026-09-21-users-md-task.md` |
| 收到确认话术 | 闭环通知客户 | `users.md` |

#### 8. 失败模式 (反模式)

| 反模式 | 后果 | 防范 |
|--------|------|------|
| 一次问太多 | 客户信息过载, 漏重点 | 多轮小问, 拆 4 小问 |
| 不要原始证据 | 没法复现 | 索取 ndjson / worklog + 取件码 |
| 不确认收到 | 客户不知是否被关注 | 立即给"收到 + 已登记 + 已分派"反馈 |
| 不闭环通知 | 客户失去信心 | 修完第一时间通知 + 致谢 |
| 冒充身份 | 信任崩塌 | 明示"hermes 助理", 不冒充 bro |
| 替客户执行操作 | 越权 | 仅回复咨询, 不替客户操作 |
| 把所有反馈当 P0 | 失去优先级 | 按 FEEDBACK.md §3.2 分类 |
| reset 用户数据 | 数据丢失, 不可挽回 | 严守 FREEZE.md §6.2 |

#### 9. 晋升路径

```
L1 (完成)     → L2 (优化)     → L3 (协作)     → L4 (系统)
   ↓              ↓              ↓              ↓
 1 份档案       1 次咨询        5 个 FB         1 个闭环
   ↓              ↓              ↓              ↓
L5 (判断)     → L6 (格局)     → L7 (造局)
   ↓              ↓              ↓
 季度洞察       客户成功计划    客户战略白皮书
```

**时间预期** (Phase 8 节奏):
- L1 → L2: 1 周 (本周)
- L2 → L3: 2 周 (累计)
- L3 → L4: 1 个月 (累计)
- L4 → L5: 季度
- L5 → L6: 季度+
- L6 → L7: 远期

#### 10. 与 RML + FEEDBACK + RACI + CUSTOMER 的交叉引用

| 文档 | CLI 章节 |
|------|----------|
| `RML.md §4` | CLI 是 RACI 中反馈活动的 R / A |
| `skills/FEEDBACK.md §10` | CLI 是反馈闭环的总 A |
| `skills/RACI.md §3.1` | CLI = 客户相关活动 R/A |
| `skills/RACI.md §3.2` | CLI = 反馈闭环总 A, 各步骤有具体 R |
| `skills/CUSTOMER.md §6` | CLI 处理 L1/L2/L3 客户优先级冲突 |
| `skills/users.md` | CLI 与 flowuser 沟通的入口约定 |
| `skills/FREEZE.md §6.2` | CLI 守 reset 禁令 (最高优先级) |

#### 11. 当前评级

| 层 | 状态 | 证据 |
|----|------|------|
| L1 | ✅ 完成 | 3 份档案 (C-001/002/006) |
| L2 | ✅ 完成 | FB-0006 文档化咨询 |
| L3 | ✅ 完成 | 8 个 FB 处理 |
| L4 | ✅ 完成 | FB-0001 完整闭环 |
| L5 | 🟡 部分 | 待 L3 客户旅程阶段 6 跟踪 |
| L6 | ☐ 未到 | 远期 |
| L7 | ☐ 未到 | 远期 |

**当前综合等级**: **L4** (系统级) · 距 L5 (季度洞察) 差阶段 6 跟踪.

⏱️ Last updated: 2026-09-21 · backlog BL-008 落地

---

## 3. 角色 × 层矩阵 (RML §5 演化)

| 角色 \ 层 | L1 | L2 | L3 | L4 | L5 | L6 | L7 |
|-----------|----|----|----|----|----|----|----|
| 1 引擎开发者 | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ |
| 2 引擎测试 | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ |
| 3 流程设计师 | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ |
| 4 流程测试 | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ |
| 5 业务审批人 | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ |
| 6 架构师 | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ |
| 7 SRE | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ |
| +A 培训师 | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ |
| +B 审计 | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ |
| +C 集成 | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ |
| +D 客户接口人 (新增) | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ | ▣ |

**▣ = 应达到; ☐ = 不强求**

---

## 4. 团队内最小配比

> 不同阶段需要不同角色比例.

| 阶段 | 角色配比建议 |
|------|--------------|
| Phase 8 客户转型 | 1 hermes (L3/L5) + 1 bro 助理 (L2/L3) |
| Phase 9 改进启动 | + 1 bro (L1-L7 全栈) |
| Phase 10 规模化 | + 角色 2 / 4 / 7 各 1 + 角色 +A +D 各 1 |

**不要**: 一次性配齐所有角色. 按阶段补.

---

## 5. 学习路径示例 (新加入者)

> 假设新成员加入 jeeflow 团队 (非客户).

### 路径 A · 工程师路径

```
D1-7     L1 跑通 README + 启动 main.py 看效果
D8-14    L1 读 vendor/jeeflow/ 理解 engine.py
D15-30   L2 跑通 bdd/*.sh 修复 1 个简单 BUG
D31-60   L3 配合流程设计师设计 1 个 API
D61-90   L4 性能测试 + 集成
D91-180  L5-L7 视情况
```

### 路径 B · 设计师路径

```
D1-7     L1 读 docs/flow.md + 跑通 flows/01-simple
D8-14    L2 写 1 个会签流程
D15-30   L3 写 1 个决策 + 1 个委托
D31-60   L4 复刻 1 个复杂流程 (04-fork-join)
D61-90   L5 输出 pitfalls.md
D91-180  L6+ 视情况
```

### 路径 C · 客户接口人路径

```
D1-7     L1 读 CUSTOMER.md + 写 1 个客户档案
D8-14    L2 与 1 个客户对话, 翻译为流程
D15-30   L3 处理 5 个 FB (用 FEEDBACK.md)
D31-60   L4 走完 1 个完整反馈闭环
D61-90   L5 输出季度洞察
D91-180  L6+ 视情况
```

---

## 6. 角色"不能做"清单

| 角色 | 不能做 |
|------|--------|
| 1 引擎开发者 | 不设计具体业务流程 (那是角色 3) |
| 2 引擎测试 | 不修 BUG (那是角色 1) |
| 3 流程设计师 | 不改 vendor/jeeflow/ (那是角色 1) |
| 4 流程测试 | 不下业务结论 (那是角色 5) |
| 5 业务审批人 | 不改流程定义 (那是角色 3) |
| 6 架构师 | 不写代码 |
| 7 SRE | 不设计流程 |
| +A 培训师 | 不修引擎 BUG |
| +B 审计 | 不审批 |
| +C 集成 | 不设计业务流程 |
| +D 客户接口人 | 不写代码 |

---

## 7. 跨角色翻译表

| 我说 | TA 听到 | 应翻译为 |
|------|----------|----------|
| "流程卡住了" (业务) | 状态没变 | 哪个 instance? state? |
| "审批人没收到" (业务) | 通知失败 | 检查飞书 webhook + instance 历史 |
| "BUG" (流程测试) | 行为不对 | 是 expected vs actual? |
| "反模式" (流程设计) | 不规范 | 触发哪条 verify 规则? |
| "客户要" (客户接口人) | 真需求 | 是 P0 BUG 还是 P2 改进? |

---

## 8. 与 FREEZE / FEEDBACK / RACI 的关系

| 文档 | 关系 |
|------|------|
| `FREEZE.md` | 技能进阶中"修改 raw data" 的部分受 FREEZE 约束, 见 §6 例外条款 |
| `FEEDBACK.md` | L5 (所有角色) + L4 (角色 +D) 必须掌握 |
| `RACI.md` | 跨角色协作的具体矩阵 |
| `CUSTOMER.md` | 角色 +D 必读, 角色 5 必读 |

---

## 9. 行动项 (本月)

- [ ] 角色 1 + 3 + 5 各完成 1 次自评 (我在哪一层)
- [ ] 选定 1 个新人启动"路径 C" 演练
- [ ] 输出第一份"角色 × 层" 自评表
- [ ] 把本文件加入新人 onboarding 资料包

### 9.1 持续渠道 + 月度节奏行动项 (Month 3 起)

- [ ] 角色 +D (客户接口人) 每天检查 omarchy 取件码 (L3 持续贡献)
- [ ] 角色 +D 每周联系 flowuser (L2 主动沟通)
- [ ] 角色 1 + 6 每月询问 bro (L6 解冻协调)
- [ ] 角色 1 + 5 每月起草 retrospective (L5 决策级)
- [ ] 角色 4 每季度发布 SLA 评分 (L4 系统级)

---

## 10. 版本

- v1.0 · 2026-09-21 · 角色实用技能体系 (RML §2 扩展 + 新增客户接口人角色)
- v1.1 · 2026-11-17 · **扩展持续渠道 + Q4 准备 + Phase 10 衔接**
  - §11 新增持续反馈渠道 (L3 升级 L3+)
  - §12 新增 hermes-peer-dm + file-share 双向通道 (L5 决策级)
  - §13 新增 bro 月度询问节奏 (L6 协调级)
  - §14 月度 metrics + 季度复盘 + 文档沉淀 (L2 优化级)
  - §15 Phase 9 → Phase 10 衔接 (L4 系统级)

---

## 11. 持续反馈渠道 (L3 升级 L3+)

### 11.1 持续贡献定义

**贡献方** 多次 (>2 次) 主动上传工件 (BDD 工件 / fix 方案 / verify 规则), 价值密度递增.

**L3 升级 L3+ 条件**:
1. ≥ 2 次持续贡献
2. 至少 1 次贡献是 真 BUG 修复
3. 至少 1 次贡献是 工具化贡献 (脚本 / verify 规则)

### 11.2 omarchy 案例 (Q4 已达成)

| 维度 | 第 1 次 | 第 2 次 | 第 3 次 |
|------|--------|---------|---------|
| **取件码** | 77045 | 97841 | 39376 |
| **类型** | BDD 验证 | **真 BUG + verify** | **真 BUG + runner** |
| **等级** | L3 | L3+ | **L3+** |

**实战**:
- `customers/C-omarchy.yaml` · 客户档案
- `contrib/_index.json` · 用户索引
- `feedback/retrospectives/2026-10-22-extraction-code-final-retro.md` · 持续渠道 SOP

---

## 12. hermes-peer-dm + file-share 双向通道 (L5 决策级)

### 12.1 通道对比

| 通道 | 工具 | 适用 | 决策点 |
|------|------|------|--------|
| **DM 通道** | hermes-peer-dm | flowuser 等可双向 | 同步 DM, 客户响应 ≤ 24h |
| **file-share 通道** | skills:file-share | omarchy 等无法 DM | 异步, 取件码唯一 |

### 12.2 决策树 (L5 关键)

```
看到 chat 贴文件 + 取件码
  ├─ chat 是 hermes 自己文件? → incomplete-info / P3 (不假装分析)
  ├─ chat 是用户真实数据? → 下载取件码 + 解读 + 登记 FB
  └─ chat 是混合? → 仅处理用户数据部分
```

### 12.3 hermes SOP 10 步

- Step 1 · 先问主人 (关键)
- Step 2-3 · 下载 + 解压
- Step 4 · 列文件清单
- Step 5 · 判断文件性质 (关键)
- Step 6 · 解读 issue
- Step 7 · 登记 FB
- Step 8 · 归档 + 索引
- Step 9 · 教训 + 自反思
- Step 10 · 通知 / 归档

**实战**: `users.md §核心原则 + §取件码机制 SOP`

---

## 13. bro 月度询问节奏 (L6 协调级)

### 13.1 询问节奏

| 节奏 | 周期 | 时间 |
|------|------|------|
| **密集** | 1 周 | W42-W45 |
| **月度** | 4 周 | W47, W51, W3, ... |

### 13.2 协调原则

- 不催 bro
- 月度询问 + 状态报告
- 等 bro 自然决定
- 不影响 Phase 9 推进 (Phase 9 不依赖解冻)

**实战**: `proposals/UNFREEZE-TRACKING-2026-11-10.md`

---

## 14. 月度 metrics + 季度复盘 + 文档沉淀 (L2 优化级)

### 14.1 月度节奏

| 输出 | 频率 | 路径 |
|------|------|------|
| **周报** | 每周 Day 5 | `skills/weekly/2026-WNN.md` |
| **月度 metrics** | 每月初 | `skills/feedback/metrics/monthly-YYYY-MM.json` |
| **季度复盘** | 季度末 | `skills/feedback/retrospectives/YYYY-QN-quarterly.md` |
| **月报收官** | 月末 | `skills/feedback/retrospectives/YYYY-NN-monthN-final.md` |

### 14.2 沉淀机制

- FAQ v1.0 published (22 题) → v1.1 (24 题)
- 模板 4 份 (bug2-recheck, work_log, FAQ, BDD)
- roadmap 4 份 (auto-assignee, top-N, month2-launch, phase9-90day)
- retrospective 5 份 (取件码机制 4 + DM 会话 1)

---

## 15. Phase 9 → Phase 10 衔接 (L4 系统级)

### 15.1 Phase 9 收官 (W51 Day 5)

- Q4 季度复盘 published v1.0
- Phase 9 收官报告
- Phase 10 启动准备

### 15.2 Phase 10 启动 (W52 Day 1)

- 持续推进 + L1 客户获取
- 新流程模式 + 新 verify 规则
- Phase 10 计划 (Q1 2027)

### 15.3 系统级指标 (L4)

| 指标 | Phase 9 | Phase 10 (Q1 2027) |
|------|---------|---------------------|
| **SLA 评分** | 100/100 | 100/100 维持 |
| **客户档案** | 4 | 5+ (含 1 L1) |
| **固化脚本** | 32/32 | 33-35/33-35 |
| **闭环率** | 100% | ≥ 95% |
| **FAQ** | 24 题 | 30+ |
| **retrospective** | 5 份 | 8+ |

---

## 16. 关联文档

- `RML.md` · 角色矩阵基础
- `users.md` · 取件码机制 SOP
- `CUSTOMER.md` · 客户视角
- `FEEDBACK.md` · 反馈闭环
- `RACI.md` · 跨角色协作
- `customers/C-omarchy.yaml` · 持续贡献用户档案
- `proposals/UNFREEZE-TRACKING-2026-11-10.md` · bro 月度询问
- `feedback/retrospectives/2026-11-month2-final.md` · Month 2 收官
- `feedback/retrospectives/2026-q4-quarterly-prep.md` · Q4 季度复盘准备
- `feedback/retrospectives/2026-11-17-flowuser-dm-no-feedback.md` · DM 通道 0 新反馈诚实交代 (W47 Day 5)

---

## 16. SPI 路由 dispatcher 架构 (v22-v29)

> 新增章节 (v1.51 同步) · 详见 `RML.md §SPI 能力` + `spi/SPEC.md §8` + `feedback/retrospectives/2026-11-17-spi-*.md` (10 份)

### 16.1 三层分离 (v26 起)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 1: Dispatcher (spi/cli.py + spi/api.py + spi/__main__.py)    │
│  · 入口层, 跟随 SPI_FOLDER 环境变量                                    │
│  · 解析命令行参数 (cli) 或 HTTP 路由 (api)                              │
│  · 加载 spi/<SPI_FOLDER>/cli.py 或 spi/<SPI_FOLDER>/api.py            │
│  · 调用下层 _data_* 函数, 不含业务逻辑                                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 2: Implementation (spi/{demo,dev,fdep}/cli.py + api.py)      │
│  · 暴露 6 个 _data_* 函数 (CLI/API 共享契约)                            │
│  · cli.py + api.py 是薄包装, 几乎全部 re-export                         │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 3: Data (spi/{demo,dev}/data.py + *.json)                      │
│  · spi/dev/data.py: 22 DictProxy (v8-v29) + 2 helpers + verify()       │
│  · spi/demo/data.py: 基础 + verify() (99 errors 是已知问题)             │
└─────────────────────────────────────────────────────────────────────┘
```

### 16.2 6 个 _data_* 函数 (CLI/API 共享契约)

| 函数 | 返回 | 说明 |
| --- | --- | --- |
| `_data_verify()` | `dict` | 4 类完整性检查 (跨表引用 + tree + 完整性 + ROLE_TO_USERS 一致性) |
| `_data_status()` | `dict` | SPI 概况 (数据源 + 22 DictProxy 摘要) |
| `_data_list_users()` | `list[dict]` | 所有用户精简视图 |
| `_data_show_user(uid)` | `dict \| None` | 单用户完整档案 (13 字段集成视图 SPI_USERS_FULL) |
| `_data_list_depts()` | `list[dict]` | 所有部门精简视图 |
| `_data_show_dept(dept_id)` | `dict \| None` | 单部门详情 + 成员 |

### 16.3 6 个 API 端点 + 7 个 CLI 命令

**API 端点** (双端共用, `main_common.register_spi_routes(app)`):

| 方法 | 路径 |
| --- | --- |
| GET | `/api/spi/verify` |
| GET | `/api/spi/status` |
| GET | `/api/spi/users` |
| GET | `/api/spi/users/{uid}` |
| GET | `/api/spi/depts` |
| GET | `/api/spi/depts/{dept_id}` |

**CLI 命令** (`python -m spi.cli <cmd>`, 跟随 SPI_FOLDER):

```bash
SPI_FOLDER=dev python -m spi.cli verify
SPI_FOLDER=dev python -m spi.cli status
SPI_FOLDER=dev python -m spi.cli list-users
SPI_FOLDER=dev python -m spi.cli show-user u_fe_eng
SPI_FOLDER=dev python -m spi.cli list-depts
SPI_FOLDER=dev python -m spi.cli show-dept D02
SPI_FOLDER=dev python -m spi.cli help  # 帮助
```

### 16.4 SPI_FOLDER 路由规则

**默认 SPI_FOLDER = dev** (本地开发/测试推荐, 22 DictProxy + 2 helpers + verify() 完整).
代码层默认仍是 `"demo"` (spi/__init__.py:14, FREEZE.md 冻结, 本地请显式设置).

| SPI_FOLDER | cli/api | 行为 |
| --- | --- | --- |
| `dev` (推荐默认) | ✅ | 完整实现 (22 DictProxy + 2 helpers + 9 SPI 函数 + verify()) |
| `demo` (代码默认) | ✅ | 基础实现 (99 errors 是已知问题, v26 引入) |
| `fdep` | ❌ | 走 dispatcher 返回 404 (`{"detail": "SPI_FOLDER=fdep 不支持 API"}`) |
| 其它 | ❌ | 404 错误 |

### 16.5 main_common 双端集成 (v28)

```python
# main_common.py (1175 行)
def register_spi_routes(app: FastAPI):
    from spi.api import router as spi_router
    app.include_router(spi_router)

# main.py + main_pg.py 同步调用
from main_common import register_spi_routes
register_spi_routes(app)
```

### 16.6 8 份 v22-v29 retrospective 索引

- `feedback/retrospectives/2026-11-17-spi-dev-refactor-v22-cli.md` · CLI 入口
- `feedback/retrospectives/2026-11-17-spi-dev-refactor-v23-users-with-roles.md` · 用户角色反向
- `feedback/retrospectives/2026-11-17-spi-dev-refactor-v24-cli-extended.md` · CLI 子命令扩展
- `feedback/retrospectives/2026-11-17-spi-dev-refactor-v25-fastapi-routes.md` · FastAPI 路由
- `feedback/retrospectives/2026-11-17-spi-v26-dispatcher-cli-api.md` · dispatcher 三层分离
- `feedback/retrospectives/2026-11-17-spi-dev-refactor-v27-dept-role-2d.md` · (dept,role) 二维聚合
- `feedback/retrospectives/2026-11-17-spi-v28-main-common-routes.md` · main_common 双端集成
- `feedback/retrospectives/2026-11-17-spi-dev-refactor-v29-user-dept-role.md` · 用户部门角色反向 (v27 互逆)
