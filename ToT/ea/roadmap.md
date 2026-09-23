# EA: 流程全生命周期体系架构 (Flow Lifecycle Enterprise Architecture) · v3.8

> **目的**：以 **FDEP** 为蓝本示例，建立一套**可复用、可持续迭代**的"流程开发 — 文档化 — 执行器化 — 测试 — 部署 — 运维 — 反馈 — 迭代"全生命周期方法论与文档体系。
> **目标读者**：任何想"开发一个像 FDEP 这样完整闭环的业务流程"的人（人或 AI Agent）。
> **核心原则**：文档先行、协议落地、自动化留痕、可被下一任执行者无障碍接力。
> **本文档定位**：**系统飞轮的架构基线**——不是工具，不是教程，是**方法论锚点**。
> **迭代历史**：`ToT/ea/iterations/<date>.md`（按日期归档每次完整迭代）

---

## 目录

| § | 标题 | 性质 |
|---|------|------|
| §1 | [飞轮定位](#1-飞轮定位why-this-is-the-flywheel) | 价值宣言（最高优先级） |
| §2 | [核心原则](#2-核心原则core-principles) | 哲学层 |
| §3 | [5 阶段生命周期](#3-5-阶段生命周期5-stages) | 流程层 |
| §4 | [制品分层](#4-制品分层artifact-layers) | 内容层 |
| §5 | [设计模式](#5-设计模式patterns-from-fdep) | 复用层 ⭐ NEW in v1.0 |
| §6 | [SOP 编排](#6-sop-编排sop-orchestration) | 工具层 |
| §7 | [三环境拓扑](#7-三环境拓扑three-environments) | 物理层 |
| §8 | [持续迭代机制](#8-持续迭代机制iteration-mechanism) | 演进层 |
| §9 | [合规检查清单](#9-合规检查清单compliance-checklist) | 验证层 ⭐ NEW in v1.0 |
| §10 | [传承与教学路径](#10-传承与教学路径inheritance--teaching) | 传播层 |
| §11 | [下次迭代路线图](#11-下次迭代路线图next-iterations) | 规划层 |
| §12 | [关键风险与缓解](#12-关键风险与缓解key-risks) | 治理层 |
| §13 | [关联文档索引](#13-关联文档索引references) | 链接层 |
| §14 | [变更日志](#14-变更日志changelog) | 历史层 |

---

## §1 飞轮定位（Why This Is The Flywheel）

> **本目录（`ToT/ea/`）是系统最具价值的资产 —— 方法论 + 落地架构 + 交付 + 改进闭环的飞轮，不是工具。**

| 维度 | 内涵 |
|------|------|
| **方法论** | 5 阶段生命周期（Discover/Design/Document/Validate/Operate）+ 持续迭代机制（baseline 演化 + 协议版本 + 反馈闭环） |
| **落地架构** | 制品分层（per-flow/per-task/per-instance）+ SOP 编排（10 个 SOP 4 大类）+ 三环境拓扑（8101/8102/abc.feg.cn） |
| **交付** | FDEP v0.6.2 蓝本 + 6 张 Job Card + 4 baselines + 10 SOPs + 客户服务器 push + 审计链路 |
| **改进闭环** | 决策 mems 审计 → 发现不足 → 改 SOP/Schema → 重跑 baseline → 部署 → 留档 → 写回 roadmap |

**飞轮效应**（每跑一次完整流程都让下一轮更快）：

```
   ┌──────── 跑流程 ────────┐
   ↓                        │
  产出 baselines            │
   ↓                        │
  完善 Job Cards ───→ 喂回 ──┤
   ↓                        │
  演化协议版本              │
   ↓                        │
  扩展 SOPs                 │
   ↓                        │
  写回 roadmap              │
   ↓                        │
  → 下一轮转得更快 ────────┘
```

**为什么是飞轮而不是工具**：

| 工具 | 飞轮 |
|------|------|
| 一次性使用 → 完成任务 → 价值固定 | 每次使用 → 沉淀知识 → 加速下次使用 → 复利增长 |
| 用完即弃 | 用得越多越值钱 |
| 价值线性 | 价值指数 |

**保护原则**：fa/ 不被工具链**任意改动** —— 它是**方法论锚点**，每次演进都应**主动写回**，不是被动修改。

---

## §2 核心原则（Core Principles）

> 这些原则是 EA 的"宪法"，所有具体规则都应可追溯到这些原则之一。

### 原则 1：文档先行（Documentation First）

| 项 | 内容 |
|----|------|
| **含义** | 代码 / 配置可改动之前，必须先有可读文档描述 |
| **体现** | §10 流程定义组织规范（4 文件强制）+ §5 Job Card 8 节结构 |
| **反例** | "先写代码再补文档" —— 永远会拖到忘记 |

### 原则 2：协议落地（Protocol Over Convention）

| 项 | 内容 |
|----|------|
| **含义** | 关键交互必须有**显式协议**（Decision Mem 字段、Job Card 路径），不靠"约定"或"记忆" |
| **体现** | Decision Mem 协议 v1.2 lite+（5 字段）+ Pickup API 4 部分响应 + 审计链规则 |
| **反例** | "executor 自己看 README 第 3 节" —— 易遗漏、易过时 |

### 原则 3：自动化留痕（Automated Audit Trail）

| 项 | 内容 |
|----|------|
| **含义** | 所有关键操作（reset / deploy / execute / 决策）必须**自动**写入留档文件 |
| **体现** | Decision Mems mems 透传 + job_card_url 审计字段 + `customer-resets/` + `customer-checks/` |
| **反例** | "操作完成就好" —— 几月后查不清"谁、什么时候、用什么 SOP 做了" |

### 原则 4：可接力执行（Chainable Execution）

| 项 | 内容 |
|----|------|
| **含义** | 每个 executor 必须留下足够信息给下一任 executor（不需要记忆） |
| **体现** | `next_handoff` 字段（含 next_node + job_card_url + input_files） |
| **反例** | "PM 知道下一步是设计" —— PM 离职了流程就断 |

### 原则 5：演进式改进（Iterative Improvement）

| 项 | 内容 |
|----|------|
| **含义** | 每个版本必须留下**可重放的证据**（baselines），让下次改进有基准 |
| **体现** | 4 baselines（v0.6.2 / v1 / v2 / v3）+ TDD 实跑 |
| **反例** | "新版本上线，老的不管了" —— 不知道改了什么是进步 |

---

## §3 5 阶段生命周期（5 Stages）

```
              ┌────────────────────────────────────────────────────────┐
              ↓                                                        │
   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
   │  1.Discover   │───→│  2.Design    │───→│  3.Document  │───→│  4.Validate  │───→│  5.Operate   │
   │  发现问题     │    │  设计流程     │    │  文档化      │    │  验证        │    │  运维        │
   └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
              ↑                                                                        │
              └──────────────────────── iterate (反馈) ──────────────────────────────┘
```

### 阶段 1：Discover（发现问题）

| 维度 | 内容 |
|------|------|
| 输入 | 业务诉求、用户反馈、痛点 |
| 产出 | 业务案例、待解决问题清单、责任人 |
| 负责 | R3（PM）+ R1a（参与者） |
| FDEP 实例 | "PM ≠ start" —— 任意来源都能发起，但 PM 是接收窗口 |

### 阶段 2：Design（设计流程）

| 维度 | 内容 |
|------|------|
| 输入 | 业务案例 |
| 产出 | `flow.json`（Snaker 格式）+ 节点定义（assignee/artifact/storage/exitCriteria）+ 决策路由 |
| 负责 | R7（架构师）+ R3 |
| FDEP 实例 | 5 阶段线性 → 6 阶段 + decision_intake + default edge（修 W012 BUG） |
| 关键产出模板 | 每个 task 节点必须含 5 个 props：assignee / form / artifact / storage / exitCriteria |

### 阶段 3：Document（文档化）

| 维度 | 内容 |
|------|------|
| 输入 | flow.json |
| 产出 | README + ROLES + NODES + CHANGELOG + RESPONSES + job_cards/* |
| 负责 | R7 + R5（知识沉淀）+ R3（业务校对） |
| FDEP 实例 | 6 文件 + 6 张 Job Card（`gen-job-cards.py` 自动生成） |
| §10 永久规则 | 文件名 `stem == stem.lower()`，必含 4 文件，1:1 节点↔job_card |

### 阶段 4：Validate（验证）

| 维度 | 内容 |
|------|------|
| 输入 | flow.json + docs + job_cards |
| 产出 | baselines（`test_<flow>_baseline_v<X.Y>.*`）+ 测试报告 |
| 负责 | AI（自动化）+ R6（评审） |
| FDEP 实例 | 4 baselines：v0.6.2 / v1 decision_mems / v2 pickup_api / v3 audit |
| 验证矩阵 | happy path + reject path + 审计链路 + Job Card URL 文件存在性 |

### 阶段 5：Operate（运维）

| 维度 | 内容 |
|------|------|
| 输入 | 已部署的 flow |
| 产出 | 部署留档 + 健康检查留档 + 审计记录 |
| 负责 | AI（操作服务器）+ R1b（人工 push 引擎） |
| FDEP 实例 | customer-resets/ 3 份 + customer-checks/ 2 份 + processInstance/detail 实时审计 |
| §11 v1.8 AI+人工分工 | 改代码 = 人工 / 操作 API = AI / 留档 = AI |

---

## §4 制品分层（Artifact Layers）

```
                     ┌─────────────────────────────────────┐
                     │  per-flow 制品（流程级，唯一权威）    │
   per-flow          │  flow.json + README/ROLES/NODES/... │
   ─────────────     └─────────────────────────────────────┘
                              ↓ 引用节点结构
                     ┌─────────────────────────────────────┐
                     │  per-task 制品（执行器手册）          │
   per-task          │  job_cards/job_card_<node>.md       │
   ─────────────     └─────────────────────────────────────┘
                              ↓ execute body 协议
                     ┌─────────────────────────────────────┐
                     │  per-instance 制品（运行时数据）       │
   per-instance      │  wf_process_instance + wf_process_task.variable │
                     └─────────────────────────────────────┘
```

### 4.1 per-flow 制品（流程级，唯一权威）

| 制品 | 位置 | 作用 | 必含 |
|------|------|------|------|
| **flow.json** | `ToT/flows/<flow>.json` | 流程定义（Snaker JSON） | ✅ 唯一权威 |
| **README.md** | `ToT/flows/<flow>/README.md` | 流程总览 + Job Card 模板 | ✅ §10 |
| **ROLES.md** | `ToT/flows/<flow>/ROLES.md` | 角色清单 | ✅ §10 |
| **NODES.md** | `ToT/flows/<flow>/NODES.md` | 节点工作手册 | ✅ §10 |
| **CHANGELOG.md** | `ToT/flows/<flow>/CHANGELOG.md` | 变更记录 | ✅ §10 |
| **RESPONSES.md** | `ToT/flows/<flow>/RESPONSES.md` | Decision Mem 协议 + 每节点模板 | 推荐 |
| **job_cards/** | `ToT/flows/<flow>/job_cards/` | 执行器手册子目录 | 推荐 |

### 4.2 per-task 制品（执行器手册）

| 制品 | 位置 | 作用 |
|------|------|------|
| **job_card_<node>.md** | `job_cards/` | 单节点 8 节执行器手册 |

**8 节结构**（详见 §5 Pattern 1）：

| § | 名称 |
|---|------|
| 1 | 身份 |
| 2 | 输入 |
| 3 | 目标 |
| 4 | checklist |
| 5 | 产出（execute body JSON 模板） |
| 6 | handoff |
| 7 | 关联 |
| 8 | 变更日志 |

**生成器**：`ToT/sop/gen-job-cards.py`

### 4.3 per-instance 制品（运行时）

| 制品 | 位置 | 作用 |
|------|------|------|
| **wf_process_instance** | 客户 PG | 实例状态、变量 |
| **wf_process_task.variable** | 客户 PG | Decision Mems + job_card_url 审计 |
| **baselines** | `ToT/tdd/` | 历史 instance 的回放测试 evidence |

**Decision Mem 协议 v1.2 lite+**（透传到 `wf_process_task.variable`）：

```json
{
  "decision_reason": "<必填，1 句话>",
  "decision_memo": { "<节点特定字段>": "..." },
  "context": { "<环境/团队/外部>": "..." },
  "job_card_url": "<executor 实际用的卡>",
  "next_handoff": {
    "next_node": "<下一节点>",
    "job_card_url": "<下一节点 executor 用的卡>",
    "input_files": ["<下一节点要读的文件>"]
  }
}
```

---

## §5 设计模式（Patterns from FDEP）

> **本节是 EA 的核心资产**：7 个可复用模式，每个模式描述"问题 → 解决方案 → 体现"。

### Pattern 1：Job Card 8 节结构

| 项 | 内容 |
|----|------|
| **问题** | executor（人/AI）拿到一个 task，不知道做什么、怎么做、产出什么 |
| **解决方案** | 单节点 8 节手册：身份/输入/目标/checklist/产出/handoff/关联/变更 |
| **FDEP 体现** | `ToT/flows/fdep/job_cards/job_card_*.md` × 6 张 |
| **适用场景** | 任何"需要不同 executor 接力"的流程节点 |

### Pattern 2：Decision Mem 透传协议

| 项 | 内容 |
|----|------|
| **问题** | 决策不可追溯 —— 谁、什么时候、为什么、参考什么 |
| **解决方案** | `processTask/execute` body 加 5 字段：decision_reason / decision_memo / context / job_card_url / next_handoff。引擎透传到 `wf_process_task.variable` |
| **FDEP 体现** | `facade.py:713` 透传机制 + `RESPONSES.md §0 v1.2 lite+` + 6 张 Job Card §5 模板 |
| **关键发现** | 引擎**已支持**透传，**零引擎改动** |
| **适用场景** | 任何需要"决策可审计"的流程 |

### Pattern 3：Pickup API 一站式启动

| 项 | 内容 |
|----|------|
| **问题** | executor 拾起 task 后要查 4 处 docs（task + 前 handoff + job card + execute 模板） |
| **解决方案** | 单端点 `POST /api/executor/pickup` 一次返回 4 部分 |
| **FDEP 体现** | `main_common.py:executor_pickup()` + `/api/executor/pickup` 路由 |
| **适用场景** | 任何"executor 需要一站式启动包"的流程 |

### Pattern 4：审计链路（job_card_url 链）

| 项 | 内容 |
|----|------|
| **问题** | Job Card 更新后，历史 instance 用了哪版无法追溯 |
| **解决方案** | 每个 task 的 `variable.job_card_url` 记录 executor 实际用的卡；`next_handoff.job_card_url` 传给下一节点；形成审计链 T.used ↔ next(T).used-prev.handoff |
| **FDEP 体现** | `RESPONSES.md §0 v1.2 lite+` + `baseline_v3audit` 验证 |
| **适用场景** | 任何"Job Card 可能演进"的流程 |

### Pattern 5：Baseline 演化

| 项 | 内容 |
|----|------|
| **问题** | 每次改进后无法证明"老版本也工作" / "新版本比老版本好" |
| **解决方案** | 每次重大改进生成新 baseline（`test_<flow>_baseline_v<X.Y>.*`），保留历史 |
| **FDEP 体现** | 4 baselines：v0.6.2 → v1 → v2 → v3 |
| **命名** | `baseline_v<X.Y.Z>.{md,json}` —— X.Y.Z 是流程版本，不是 baseline 版本 |
| **适用场景** | 任何"持续演进"的流程 |

### Pattern 6：三环境拓扑

| 项 | 内容 |
|----|------|
| **问题** | 单环境难兼顾"快速调试" / "集成测试" / "客户验证" |
| **解决方案** | 本地 dev (memory 8101) / 本地 dev (PG 8102) / 客户服务器 (abc.feg.cn) 三环境 |
| **FDEP 体现** | §11 v1.8 部署规范 |
| **约束** | 8102 ↔ 客户服务器共享 PG；reset 会同时清两边 |
| **适用场景** | 任何"需要多环境验证"的部署 |

### Pattern 7：AI + 人工协作分工

| 项 | 内容 |
|----|------|
| **问题** | AI 不能 SSH，AI 不能 drive 代码 review，但 AI 操作 API 极快 |
| **解决方案** | **改代码 = 人工**（git push + 重启）；**操作 API = AI**（reset / deploy / smoke test）；**留档 = AI** |
| **FDEP 体现** | §11 v1.8 AI+人工协作流程 |
| **原则** | AI 不擅改 ToT/ 外文件；AI 不 push 引擎 |
| **适用场景** | 任何"AI 操作远端服务器"的场景 |

### Pattern 8：EA 自证闭环（v1.1+）

| 项 | 内容 |
|----|------|
| **问题** | EA 本身怎么被验证不是"PPT 上的承诺"？ |
| **解决方案** | 把 §9 27 项合规清单自动化成 `ToT/sop/ea-compliance.py`，每次重要迭代后跑一次 |
| **FDEP 体现** | Iteration #2：27/27 PASS (100%) |
| **关键特性** | 1) 自动化（3 秒跑完）；2) 可纳入 CI；3) 跑出来就是飞轮转动证据 |
| **修正规范** | §9.3.5 baseline 命名放宽为 `<X>[<feature>]?`（实战用 feature 名比 X.Y.Z 更有信息量） |
| **适用场景** | 任何"想证明方法论有效"的需求（产品 / 工程 / 流程） |

### Pattern 9：环境配置集中化（v1.2+，v3.8+ 双配置域）

| 项 | 内容 |
|----|------|
| **问题** | 服务器 URL 散落硬编码在多个文件（脚本 / SOP / 留档），改一处遗漏全漏；外部服务 endpoint 同样散落 |
| **解决方案** | **2 套配置域（按职责拆分）**：① **引擎 server 域** `ToT/config/servers.json`（4 servers + active）+ `server_config.py` 加载器 + `env-config.md` SOP；② **外部服务域** `ToT/config/share.json`（upload_url + download_url_template + expire_unit）+ `archive_flow.load_share_config()` 加载器 + `archive-flow.md` §9 配置说明 |
| **FDEP 体现** | Iteration #3：5+ 处服务器硬编码 → 0 处；**Iteration #30**：archive_flow 2 处 share 硬编码 → 0 处 |
| **关键设计** | 1) 单一 JSON 真相源（每域一份）；2) 加载器 inline 或独立（share_config 轻量，inline 在 archive_flow.py）；3) §9.6 自动检查保证不变硬编码（每域 +1 项）；4) **域拆分原则**：管"流程引擎"的归 servers.json，管"外部服务"的归各自 <service>.json，不混合 |
| **历史兼容** | 留档保留当时 URL（不替换），仅新脚本/SOP 用 config |
| **适用场景** | 任何"多个环境 + 多脚本"或"多个外部服务 + 多工具"的部署场景 |
| **演进方向** | 未来新增外部服务（email / notification / monitoring）→ 新建 `ToT/config/<service>.json` + §9.6.X 检查 |

### Pattern 10：用户流程引导 + 完整性检测 + Issue 元闭环（v1.3+）

| 项 | 内容 |
|----|------|
| **问题** | 用户想设计流程但不知道从哪开始；流程严谨度不知怎么把握；issue 跟踪无系统化 |
| **解决方案** | **4 件套**（数据 + 脚本 + SOP + 元闭环）：① `flow_designer.py`（5 问 → flow.json 草稿）；② `flow_completeness.py`（6 层 31 项打分）；③ `issue_link.py`（FDEP 元闭环）；④ `flow-design.md`（8 节 SOP） |
| **FDEP 体现** | Iteration #4：expense-approval（极简 50%）vs fdep（蓝本 100%）；issue_link 真实跑通 FDEP 元闭环（stage_pm 拿到 issue 数据含 source_instance_id） |
| **核心原则** | **先跑通，再严谨** —— 完整性检测是工具不是门禁；用户按"下一步建议"自由演进 |
| **关键设计** | 1) 5 问简化设计；2) 0-100% 分让用户看到进度；3) FDEP 自身作为 issue tracker（自包含）；4) stage_pm 决策 mems 包含 issue 元数据 |
| **角色重定位** | FDEP 从"唯一流程"升级为"流程元平台"——任何流程都可在 EA 框架下自管理 |
| **适用场景** | 任何"业务团队想自动化流程"+"需要演进式严谨度"+"需要 issue 系统化"的工程团队 |

### Pattern 11：3 阶段环境流水线（v1.4+）

| 项 | 内容 |
|----|------|
| **问题** | 流程定义在哪测？local 测完怎么推到客户？有没有"团队共享 dev"层级？ |
| **解决方案** | **5 server × 3 tier × 权限矩阵**：`local-memory` / `local-pg`（stage-1-dev，AI 全权）→ `org-server`（stage-2-staging，AI 可推不可 reset）→ `customer-test` / `production-future`（stage-3-prod，AI 不可推不可 reset，需人工审批） |
| **FDEP 体现** | Iteration #6：promote.py CLI 6 子命令（list/status/push/request-promote/promote/rollback）+ env-pipeline.md SOP（10 节） |
| **核心原则** | **越接近生产，约束越严** —— Local 全自动 / Org 半自动 / Customer 强制人工审批 |
| **关键设计** | 1) tier 字段标注阶段；2) ai_can_push / ai_can_reset 权限矩阵；3) promote.py 双保险（--confirm-ai flag + server ai_can_push 检查）；4) env-pipeline.md SOP 显式化规则 |
| **闭环集成** | `ea-compliance.py` §9.7 加 4 项检查（35/35 PASS）—— 流水线不偏离自动检测 |
| **适用场景** | 任何"多环境 + 多权限 + 多人协作"的流程部署 |

---

## §6 SOP 编排（SOP Orchestration）

**当前 10 个 SOP + 2 个脚本**，按 4 大类分组：

### 6.1 数据类（修改 SPI 时）

| SOP | 脚本 | 何时跑 |
|-----|------|--------|
| `spi-verify.md` | `spi-verify.py` | 修改 `spi/<folder>/jsons/*.json` 后 |

### 6.2 定义类（修改流程时）

| SOP | 脚本 | 何时跑 |
|-----|------|--------|
| `flow-folder.md` | （手动规范） | 新建流程 / 改文件结构 |
| `flow-lint.md` | `flow-lint.py` | 流程结构变更后 |
| `tdd-flow.md` | `tdd-flow.py` | 改 `ToT/flows/*.json` 后 |
| `auto-deploy-fdep.md` | （main_common 内嵌） | 引擎启动后自动 |

### 6.3 操作类（部署 + 运维时）

| SOP | 何时跑 |
|-----|--------|
| `engine-deploy.md` | 引擎级文件改动后 |
| `customer-data-reset.md` | 客户服务器首次发布 / 大版本升级前 |
| `clean-customer-data.md` | reset 之后 / 项目移交 / 留档膨胀 |

### 6.4 文档类（整理时）

| SOP | 何时跑 |
|-----|--------|
| `new-trip.md` | 新会话 / 新项目启动前 |

### 6.5 API 类（接口设计时）

| 文档 | 何时参考 |
|------|----------|
| `executor-api.md` | 设计 executor 启动包 API 时 |
| `gen-job-cards.py` | 改 job_card 模板时 |

### 6.6 双轨调用顺序（典型场景）

```bash
# 场景 1：新增 / 修改流程
python3 ToT/sop/gen-job-cards.py --force
python3 ToT/sop/flow-lint.py ToT/flows/<flow>.json
python3 ToT/sop/tdd-flow.py ToT/flows/<flow>.json

# 场景 2：修改 SPI 数据
SPI_FOLDER=dev python3 ToT/sop/spi-verify.py

# 场景 3：客户服务器首次发布
python3 ToT/sop/customer-data-reset.md
python3 ToT/sop/clean-customer-data.md

# 场景 4：新会话 / 项目移交
python3 ToT/sop/new-trip.md
python3 ToT/sop/clean-customer-data.md
```

---

## §7 三环境拓扑（Three Environments）

| 环境 | 地址 | 端口 | 部署方式 | 数据后端 | 用途 |
|------|------|------|----------|----------|------|
| **本地 dev（memory）** | `127.0.0.1` | **8101** | `python -m uvicorn main:app --port 8101` | 内存（启动清空） | 快速调试 |
| **本地 dev（PG）** | `127.0.0.1` | **8102** | `python -m uvicorn main_pg:app --port 8102` | 共享 PG | 集成测试 |
| **客户测试服务器** | `https://abc.feg.cn/jeeflow/` | 443 | 人工 push 引擎 + AI 通过 API | 共享 PG | 验证 + 业务试用 |

**共享 PG**：`postgresql://llmproxy:dbpassword9090@10.17.1.26:6432/litellm`

**关键约束**：

| # | 约束 | 说明 |
|---|------|------|
| 1 | 本地 8102 ↔ 客户服务器同库 | reset 会**同时清两边** |
| 2 | 8101 内存后端独立 | 每次重启清空 |
| 3 | 客户服务器只能通过 HTTPS API | 无 SSH 给 AI |
| 4 | 引擎代码 push 是**人工**职责 | AI 不直接碰 `vendor/jeeflow/` |

---

## §8 持续迭代机制（Iteration Mechanism）

### 8.1 Baseline 演化（FDEP 实例）

```
v0.5 (5阶段线性)
   │ ↓ TDD 实跑发现 W012 BUG
v0.6 (插入 decision_intake + 修角色解析)
   │ ↓ assignee 直接赋值
v0.6.1
   │ ↓ 加 default edge 处理 W013
v0.6.2 (基线：happy path PASSED)
   │ ↓ Decision Mem 协议 v1.0 lite（facade.py:713 透传）
v1 (baseline)
   │ ↓ Pickup API（executor 一站式启动包）
v2 (baseline)
   │ ↓ job_card_url 审计字段
v3 (baseline)
   ↓ ↓ ... 持续
v4+ (候选：fork-join / 多 executor 接力 / 生产部署)
```

### 8.2 协议版本演进

| 版本 | 字段 | 触发 |
|------|------|------|
| **v1.0 lite** | decision_reason / decision_memo / context | 基础决策留档 |
| **v1.1 lite+** | + next_handoff | executor 接力不丢上下文 |
| **v1.2 lite+** | + job_card_url | 审计追溯"用了哪张卡" |
| **v2.0**（候选） | + assignee_chain | 多 executor 接力 |

### 8.3 反馈闭环

```
   Execute (生产/测试 instance)
        ↓
   processInstance/detail (审计查询)
        ↓
   发现不足（缺字段 / 链路断 / 文件丢失）
        ↓
   改 SOP / 改 flow.json / 改 Job Card 模板
        ↓
   重跑 tdd-flow.py (生成新 baseline)
        ↓
   验证 PASSED
        ↓
   Push + Deploy (走 §11 v1.8 流程)
        ↓
   留档 ToT/customer-resets/
        ↓
   写回 ToT/ea/roadmap.md（飞轮自转）
```

### 8.4 度量指标（建议）

| 指标 | 计算 | 期望 |
|------|------|------|
| baseline 数 | `ls ToT/tdd/test_*_baseline_v*` | ≥ 3 |
| Decision Mem 完整率 | 含 decision_reason 的 task / 总 task | ≥ 80% |
| job_card_url 审计通过率 | job_card_url 指向真实文件 / 总 task | = 100% |
| 链路完整率 | next_handoff 匹配下个 task / 总有 next 的 task | = 100% |
| 流程一次跑通率 | happy state=DONE / 总启动数 | ≥ 95% |

---

## §9 合规检查清单（Compliance Checklist）

> **目的**：让任何流程都能用本清单验证"是否遵循了 EA"。
> **使用方法**：CI 门禁 + 手动 review。

### 9.1 流程级（per-flow）

- [ ] **flow.json** 存在且能被 `flow-lint.py` 通过
- [ ] **文件名全小写**（`stem == stem.lower()`）
- [ ] **4 文件齐全**：README + ROLES + NODES + CHANGELOG
- [ ] **README** 含 §5 Job Card 模板段
- [ ] **NODES** 含每个节点的"工作步骤"+"注意事项"
- [ ] **CHANGELOG** 含每次版本变更 + 触发原因
- [ ] **RESPONSES** 含 §0 Decision Mem 协议 + 每个 task 的 §X.2.1 模板
- [ ] **job_cards/** 子目录存在
- [ ] **每节点 1 张 Job Card**（snaker:task 节点）

### 9.2 Job Card 级（per-task）

- [ ] **8 节结构齐全**：身份 / 输入 / 目标 / checklist / 产出 / handoff / 关联 / 变更
- [ ] **§5 execute body JSON 可解析**（`json.loads` 不报错）
- [ ] **§5 含 `decision_reason` / `decision_memo` / `context`**
- [ ] **§5 含 `job_card_url`**（指向自己的 job_card_*.md）
- [ ] **§5 含 `next_handoff.job_card_url`**（指向下一节点；终态节点含 `is_terminal: true`）

### 9.3 基线级（per-baseline）

- [ ] **happy path PASSED**（state=DONE）
- [ ] **reject path PASSED**（state=REJECT，可选）
- [ ] **审计链通过**：每个 task 的 `next_handoff.job_card_url` == 下一 task 的 `job_card_url`
- [ ] **Job Card 文件存在**：每个 task 提交的 `job_card_url` 指向真实存在的文件
- [ ] **文件名格式**：`test_<flow>_baseline_v<X.Y.Z>.{md,json}`

### 9.4 运维级（per-deploy）

- [ ] **客户服务器 healthz 返回 200 + pg=ok**
- [ ] **fdep 已部署**（`processDefine/getLastByName` 返回）
- [ ] **冒烟测试跑到底**（startAndExecute → DONE）
- [ ] **留档写入 customer-resets/**（含 instanceId + defineId + 时间戳）

### 9.5 飞轮级（per-iteration）

- [ ] **本次迭代有 iterations/<date>.md** 留档
- [ ] **本次迭代有 changelog 更新**（roadmap.md §14 + README.md §8）
- [ ] **新经验写回 Patterns**（§5）
- [ ] **新原则写回 Principles**（§2）

### 9.6 配置集中化（per-config-domain，5 项）

> **演进**：v1.2 起步（servers.json 4 项，Iter#3），v3.8 扩展（+ share.json 第 5 项，Iter#30）
> **原则**：每个外部端点/服务都应有 §9.6 子项，自动校验"存在且合法 + 加载器存在 + 不硬编码"

- [ ] **9.6.1** `ToT/config/servers.json` 存在且合法（含 `servers` + `active` 字段）
- [ ] **9.6.2** `ToT/sop/server_config.py` 加载器存在
- [ ] **9.6.3** `ea-compliance.py` 自身不硬编码 URL（必须 `get_url()` 读 config）
- [ ] **9.6.4** `servers.json` 含 `customer-test` 配置（当前主目标）
- [ ] **9.6.5** `ToT/config/share.json` 存在且合法（archive_flow endpoint 真相源，含 `upload_url` + `download_url_template` 含 `{code}` 占位）

**未来扩展模板**（v3.9+）：
- 9.6.6: email service config
- 9.6.7: notification service config
- 9.6.8: monitoring service config

---

## §10 传承与教学路径（Inheritance & Teaching）

### 10.1 新人上手（5 步）

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: ToT/README.md (工作规范)                              │
│         → 知道"我们怎么工作"（§1 边界 / §4 角色 / §11 部署）     │
├─────────────────────────────────────────────────────────────┤
│ Step 2: ToT/HANDBOOK.md (知识手册)                            │
│         → 知道"30 秒读懂 jeeFlow"（架构图 + 三环境 + 快速开始） │
├─────────────────────────────────────────────────────────────┤
│ Step 3: ToT/ea/roadmap.md (本文档)                            │
│         → 知道"流程怎么全生命周期开发"（5 阶段 + 制品 + SOP）   │
├─────────────────────────────────────────────────────────────┤
│ Step 4: ToT/flows/fdep/ (蓝本示例)                            │
│         → 看一个完整流程的所有制品（5 文件 + 6 张卡）           │
├─────────────────────────────────────────────────────────────┤
│ Step 5: 跑三轨 SOP + demo                                    │
│         → spi-verify + flow-lint + tdd-flow + demo_v4         │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 写新流程（7 步）

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: 在 ToT/flows/ 创建 <new-flow>.json + <new-flow>/ 文件夹 │
├─────────────────────────────────────────────────────────────┤
│ Step 2: 写 4 必含文档（README + ROLES + NODES + CHANGELOG）  │
│         模板见 ToT/sop/flow-folder.md §4                     │
├─────────────────────────────────────────────────────────────┤
│ Step 3: 写 RESPONSES.md（Decision Mem 模板 §X.2.1）          │
│         参考 ToT/flows/fdep/RESPONSES.md §4.2.1              │
├─────────────────────────────────────────────────────────────┤
│ Step 4: 跑 gen-job-cards.py 生成 job_cards/                  │
│         python3 ToT/sop/gen-job-cards.py --force             │
├─────────────────────────────────────────────────────────────┤
│ Step 5: 跑三轨 SOP 校验                                      │
│         python3 ToT/sop/flow-lint.py <new-flow>.json         │
│         python3 ToT/sop/tdd-flow.py <new-flow>.json          │
├─────────────────────────────────────────────────────────────┤
│ Step 6: 重命名为 baseline                                    │
│         mv test_<new-flow>_*.{md,json} test_<new-flow>_baseline_v<X.Y>.{md,json}│
│         编辑 ToT/tdd/INDEX.md 加新基线                        │
├─────────────────────────────────────────────────────────────┤
│ Step 7: Deploy（走 §11 v1.8 流程）                             │
│         - 人工 push 引擎代码                                  │
│         - AI 通过 API deploy flow.json                        │
│         - 跑 demo 验证 happy path                            │
│         - 留档 ToT/customer-resets/                          │
└─────────────────────────────────────────────────────────────┘
```

### 10.3 AI Agent 接力协议（每个会话开始必做）

1. **读 `ToT/README.md` 顶部摘要** → 知道当前 v?
2. **读 `ToT/HANDBOOK.md`** → 30 秒了解项目
3. **读本文 `ToT/ea/roadmap.md`** → 知道方法论
4. **ls `ToT/ea/iterations/`** → 看最近的迭代记录
5. **ls `ToT/customer-*/`** → 看最近运维活动
6. **跑三轨 SOP**（spi-verify + flow-lint + tdd-flow）→ 验证环境干净

然后**才能**开始改流程 / 改 SOP / 写新文档。

---

## §11 下次迭代路线图（Next Iterations）

### 11.1 短期（v0.7+ / v2.8+，本月内）

| # | 改进 | 价值 | 关联 |
|---|------|------|------|
| 1 | SPI 角色自动解析（assignmentHandler） | 多 executor 接力 | FDEP Q8 |
| 2 | stage_review 拆 fork-join | 提升评审效率 | FDEP Q2 |
| 3 | stage_intake 与 stage_pm 拆 R3a/R3b | 角色分工清晰 | FDEP Q6 |
| 4 | reset 后自动跑 `clean-customer-data` | 减少手工 | 自动化 |
| 5 | demo_v4 整合进 `tdd-flow.py` | 单命令跑全审计链路 | 工具整合 |

### 11.2 中期（v3.x，下季度）

| # | 改进 | 价值 |
|---|------|------|
| 1 | Stage 0 / Stage 1 拆 R3a/R3b | FDEP 角色矩阵重做 |
| 2 | 持续改进环（stage_feedback → stage_pm） | Q3 闭环 |
| 3 | Decision Mem 可视化工具 | 审计 UI |
| 4 | 多流程协同（fdep → invoice / approval） | 复用方法论 |
| 5 | engine-deploy 增加 Canary 灰度 | 降低升级风险 |

### 11.3 长期（v4.x+，半年+）

| # | 改进 | 价值 |
|---|------|------|
| 1 | 生产环境部署 | 上生产 |
| 2 | Decision Mem 跨流程聚合（businessNo 维度） | 业务全局视图 |
| 3 | 自动 SOP（决策 mems 反向触发 SOP 步骤） | 全自动运维 |
| 4 | Flow 模板市场（fdep-like 模板可复用） | 加速新流程开发 |

---

## §12 关键风险与缓解（Key Risks）

| # | 风险 | 缓解 |
|---|------|------|
| 1 | **客户服务器 reset 同时清本地测试库** | reset 前跑 `clean-customer-data` 备份留档 |
| 2 | **Job Card 与实际 SOP 不一致** | `gen-job-cards.py` 自动从 NODES.md + RESPONSES.md §X.2.1 生成；改一个必重生成 |
| 3 | **链路断（T.next_handoff.jcu ≠ next(T).jcu）** | baseline 自动化校验；CI 门禁（§9.3） |
| 4 | **AI 误改引擎代码** | §11 v1.8 强制：AI 不 push 引擎；只能改 ToT/ 内文件 |
| 5 | **私有数据泄露（customer-resets 留档含 instanceId）** | `clean-customer-data` SOP 定期清理；归档到 `/tmp/opencode/`（不进 git） |
| 6 | **W012 / W013 类引擎 BUG 重现** | `tdd-flow.py` + baselines 守住流程结构；新流程先 `validate_flow` 再实跑 |
| 7 | **Decision Mem 字段爆炸（v2.0+）** | 协议升级前先看是否兼容旧 instance；写迁移脚本 |
| 8 | **roadmap.md 自身失修** | 每次迭代必须更新 §14 changelog + §5 patterns（强制条款 §9.5） |

---

## §13 关联文档索引（References）

> 本文件**只读引用**以下文档，不修改其他文档。

### 13.1 顶层规范

| 文档 | 用途 | 何时读 |
|------|------|--------|
| `ToT/README.md` | 工作规范（v2.9） | 必读第 1 份 |
| `ToT/HANDBOOK.md` | 知识手册（v0.1） | 必读第 2 份 |
| `ToT/mapping.md` | R 角色 ↔ SPI ↔ 用户三层映射 | 写新流程时查 |

### 13.2 ea/ 元目录

| 文件 | 用途 |
|------|------|
| `ToT/ea/roadmap.md` | 本文档（架构基线） |
| `ToT/ea/README.md` | ea/ 索引 |
| `ToT/ea/iterations/<date>.md` | 每次完整迭代的复盘记录 |

### 13.3 蓝本示例（FDEP）

| 文档 | 用途 |
|------|------|
| `ToT/flows/fdep.json` | 流程定义（v0.6.2） |
| `ToT/flows/fdep/README.md` | 流程总览 + Job Card 模板 |
| `ToT/flows/fdep/ROLES.md` | 角色清单 |
| `ToT/flows/fdep/NODES.md` | 节点工作手册 |
| `ToT/flows/fdep/CHANGELOG.md` | 变更记录 |
| `ToT/flows/fdep/RESPONSES.md` | Decision Mem 协议 + 每节点模板 |
| `ToT/flows/fdep/job_cards/*.md` | 6 张执行器手册 |

### 13.4 SOP 集（10 个）

详见 `ToT/README.md §9 SOP 索引`。

### 13.5 测试证据（baselines）

| Baseline | 内容 |
|----------|------|
| `test_fdep_baseline_v0.6.2.{md,json}` | happy + reject PASSED |
| `test_fdep_baseline_v1decision_mems.{md,json}` | Decision Mem v1.0 lite 落地 |
| `test_fdep_baseline_v2pickup_api.{md,json}` | Pickup API v0.1 落地 |
| `test_fdep_baseline_v3audit.{md,json}` | job_card_url 审计链路 |

### 13.6 运维留档

| 文档 | 用途 |
|------|------|
| `ToT/customer-resets/*.md` | 客户服务器 reset + deploy 留档 |
| `ToT/customer-checks/*.md` | 健康检查 + new-trip 留档 |

### 13.7 工具脚本

| 脚本 | 用途 |
|------|------|
| `ToT/sop/spi-verify.py` | SPI 数据校验 |
| `ToT/sop/tdd-flow.py` | 流程 TDD |
| `ToT/sop/flow-lint.py` | 流程定义组织校验 |
| `ToT/sop/gen-job-cards.py` | Job Card 自动生成器 |

### 13.8 引擎代码（**只读**，push 由人工负责）

| 文件 | 改动点 |
|------|--------|
| `main_common.py` | +`executor_pickup()` +`/api/executor/pickup` 路由 +`auto_deploy_fdep()` |
| `vendor/jeeflow/facade.py:713` | 关键发现：透传机制（**不改，只读**） |

---

## §14 变更日志（Changelog）

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | 2026-09-22 | 初稿 —— 以 FDEP v0.6.2 + v1/v2/v3 baselines 为实例，建立流程全生命周期方法论。本文件只读引用 ToT 内其他文档 |
| **v0.1.1** | 2026-09-22 | **强化飞轮定位**：新增 §0 飞轮定位段（4 维度 + 飞轮效应图 + 工具 vs 飞轮对比 + 关键资产价值排序 + 保护原则） |
| **v1.0** | **2026-09-22** | **第一版正式架构**：① 从 v0.1.1 复盘型升级为架构型 —— 5 阶段框架 + 制品分层 + 10 SOP 编排 + 三环境拓扑 + 迭代机制 → 升级为正式 14 节架构文档；② **新增 §2 核心原则**（5 条哲学层原则：文档先行/协议落地/自动化留痕/可接力执行/演进式改进）；③ **新增 §5 设计模式**（7 个从 FDEP 提炼的可复用模式：Job Card 8 节结构 / Decision Mem 透传 / Pickup API / 审计链路 / Baseline 演化 / 三环境拓扑 / AI+人工协作）；④ **新增 §9 合规检查清单**（4 层检查：流程级 / Job Card 级 / 基线级 / 运维级 + 飞轮级）；⑤ **新增 §11 路线图 + §12 风险**（含"roadmap.md 自身失修"自指风险）；⑥ 复盘内容移至 `ToT/ea/iterations/2026-09-22.md`；⑦ 新增 `ToT/ea/README.md` 索引；⑧ v2.8 → v2.9 changelog 同步 |
| **v1.1** | **2026-09-22** | **EA 自证闭环**（用户口头指令"自证闭环"）：① **新建 `ToT/sop/ea-compliance.py`**（自动化跑 §9 27 项合规检查，260 行）；② **跑检查 → 27/27 PASS (100%)** —— 自证 EA 自洽；③ 修 3 个 bug：regex 不匹配 v3audit（放宽 §9.3.5 命名规范）/ happy 路径匹配语义化 / findall 用 re 模块；④ **新增 iterations/2026-09-22_ea-self-audit.md**（第二轮迭代记录：时间线 + 闭环示意 + 修复 ADR + 度量对比）；⑤ **§5 新增 Pattern 8**（EA 合规自验证 —— "用 §9 清单自动化自证"）；⑥ **§9.3.5 命名规范放宽**：`<X>[<feature>]?`（feature 可选，实战用 `v3audit` / `v1decision_mems` 更有信息量）；⑦ v2.9 → v2.10 changelog 同步。 |
| **v1.2** | **2026-09-22** | **环境配置集中化（Pattern 9）**（用户口头指令"客户测试服务器 https://abc.feg.cn/jeeflow 在不同的闭环环境是不一样的，希望可以集中到统一的地方修改"）：① **新建 `ToT/config/servers.json`**（4 servers：local-memory/local-pg/customer-test/production-future + active 字段 = 单点切换）；② **新建 `ToT/sop/server_config.py`**（70 行加载器，CLI + import 双模式）；③ **新建 `ToT/sop/env-config.md`**（8 节 SOP）；④ `ea-compliance.py` §9.6 加配置集中化 4 项检查（servers.json 合法 / 加载器存在 / ea-compliance 不硬编码 / 含 customer-test）；⑤ **`ea-compliance.py` 自身改造**：从硬编码 `TARGET = "https://..."` 改为读 config；⑥ **§9 检查项 27 → 31**（+4 项），**31/31 PASS (100%)**；⑦ **§5 新增 Pattern 9**（环境配置集中化 —— "3 件套：数据 + 加载器 + SOP"）；⑩ 新增 iterations/2026-09-22_env-config.md（第三轮迭代：5+ 处硬编码 → 0 处）；⑪ v2.10 → v2.11 changelog 同步。 |
| **v1.3** | **2026-09-22** | **用户流程设计引导 + 完整性检测 + Issue 元闭环（Pattern 10）**（用户口头指令"教用户设计流程 ... 用户的流程一开始不需要像fdep这样严谨的结构 ... 通过 fdep 这个流程，闭环issue的解决"）：① **新建 `ToT/sop/flow_designer.py`**（280 行，5 问交互 → flow.json 草稿）；② **新建 `ToT/sop/flow_completeness.py`**（280 行，6 层 31 项打分 0-100% + 下一步建议 + 4 级评级）；③ **新建 `ToT/sop/issue_link.py`**（230 行，FDEP 元闭环：原 instance 问题 → 创建 fdep 实例 → 透传 issue 数据到 stage_pm）；④ **新建 `ToT/sop/flow-design.md`**（250 行，8 节 SOP：适用场景 / 设计原则 / 5 步引导 / 风险 / 命令清单）；⑤ **新建 `ToT/flows/expense-approval.json`**（极简示例，2654 字节，演示 50% 评分）；⑥ **§5 新增 Pattern 10**（用户流程引导 + 完整性检测 + Issue 元闭环）；⑦ **现场演示 4 件套串联**：expense-approval 打分 50%（🟡）/ fdep 100%（✅）/ issue_link 真实跑通（fdep instance 92226177114139 stage_pm.variable 完整含 issue 数据含 source_instance_id）；⑧ 新增 iterations/2026-09-22_user-flow-design.md（第四轮迭代记录）；⑨ SOP 数 12→13（+flow-design）；⑩ v2.12 → v2.13 changelog 同步。 |
| **v1.4** | **2026-09-22** | **3 阶段环境流水线（Pattern 11）**（用户口头指令"我们提供和开发同步的快速实验环境 ... 1. 用户可以先本地memory 2. 上传至组织服务器 3. 正式发布流程，具体sop待定"）：① **`ToT/config/servers.json` v1.1**：加 `org-server`（stage-2-staging，tier=risk_level=ai_can_push=ai_can_reset 4 字段完整）；② **新建 `ToT/sop/env-pipeline.md`** v0.1（10 节 SOP：3 阶段模型 / 每阶段操作 / promote 流程 / 自动化范围 / 与其他 SOP 关系）；③ **新建 `ToT/sop/promote.py`** CLI（170 行，6 子命令：list/status/push/request-promote/promote/rollback，--confirm-ai 双保险 + ai_can_push 检查）；④ **`ea-compliance.py` §9.7 +4 项**（35/35 PASS，tier 完整 / ai_can_* 完整 / promote.py 存在 / env-pipeline.md 存在）；⑤ 演示完整流程（含 6 个边界场景全部正确处理：list / status / push / request-promote / 无 --confirm-ai 拒绝 / ai_can_push=false 拒绝）；⑥ **§5 新增 Pattern 11**（3 阶段环境流水线）；⑦ 新增 iterations/2026-09-22_env-pipeline.md（第六轮迭代记录：闭环示意 + ADR + 度量）；⑧ SOP 数 14→14（+env-pipeline）；⑨ v2.13 → v2.14 changelog 同步。 |
| **v1.5** | **2026-09-22** | **路径可移植性修复（用户口头指令"发现一个非常严重的问题，某些文档或代码出现了绝对路径 /opt/jupyter/**** 指令. 请检查修正，严重影响其他机器环境的sop的落地"）：① **修 5 个脚本 BASE 硬编码**（flow_designer.py / ea-compliance.py / promote.py / flow_completeness.py / issue_link.py）：`Path("/opt/jupyter/...")` → `Path(__file__).resolve().parent.parent.parent`（3 层上溯到项目根）；② **修 3 个 SOP 文档 `/opt/jupyter` 硬编码**（customer-data-reset.md / HANDBOOK.md / clean-customer-data.md）→ `$REPO_ROOT` 环境变量占位符；③ **`ea-compliance.py` §9.8 +4 项**（路径可移植性自动检查，39/39 PASS：脚本无硬编码 / SOP 无硬编码 / 用 Path(__file__) / BASE 推导正确 3 层上溯）；④ **跨机器验证**：`/tmp/myapp` 完整模拟部署（cp -r 后跑 5 项工具全过：ea-compliance / flow-completeness / promote / flow_designer / issue_link）；⑤ §9 检查项 35→39（+4 项）；⑥ 新增 iterations/2026-09-22_portability.md（第七轮迭代：闭环 + ADR + 度量对比）；⑦ v2.15 → v2.16 changelog 同步。 |
| **v1.6** | **2026-09-22** | **REPO_ROOT 自动化 · 第八轮飞轮转动**（用户口头指令"REPO_ROOT 需要人工设置？ 能否自动"）：① **新建 `ToT/bin/with-jf.sh`**（60 行 bash，4 优先级自动检测：已 export → git rev-parse → 路径反推 → 兜底）；② **新建 `ToT/bin/jf` wrapper**（30 行 bash，`cd $REPO_ROOT + exec "$@"`）；③ **更新 3 个 SOP 文档**用 jf wrapper 替代 `$REPO_ROOT` 注释（user 不需手动 export）；④ **`ea-compliance.py` §9.9 +4 项**（自动化检查，43/43 PASS：with-jf.sh 存在 / jf wrapper 可执行 / with-jf.sh 含自动检测 / 实测 source 正确导出）；⑤ **3 种用法验证**：source（会话）/ jf wrapper（单命令）/ 直接 cd（用户正常用法）—— 5 项工具 + 3 种姿势全过；⑥ 跨机器验证（`/tmp/test_jfhost` 完整模拟部署）；⑦ **§5 新增 Pattern 12**（REPO_ROOT 自动化 —— "with-jf.sh + jf + Path(__file__)" 三角链）；⑧ 新增 iterations/2026-09-22_repo-root-auto.md（第八轮迭代：闭环 + ADR + 度量）；⑨ §9 检查项 39→43（+4 项）；⑩ v2.16 → v2.17 changelog 同步。 |
| **v1.7** | **2026-09-23** | **端到端验证 · 第九轮飞轮转动**（自然推进，验证方法论对非 FDEP 流程可复用性）：① **新建 invoice-approval 流程**（6 节点 3 角色，含金额分支决策，6 edge）；② **8 步完整跑通**（flow_designer 设计 → deploy → e2e 2 条路径 → completeness 50→100% → 5 文件 + 4 Job Cards → baseline md → promote 演示 → ea-compliance 自验证）；③ **3 个 bug 当场修复**：decision expr 在 edge 而非 node / `#variable.amount` 嵌套变量 / actor 是 role 名需 flow.auto 绕过；④ **完整性评分从 50% → 100%**（6 层全 PASS）；⑤ **沉淀 5 条 SOP 经验**（decision expr 写法 / actor 限制 / Job Card 命名 / 8 节结构 / baseline md 命名）；⑥ **ea-compliance 43/43 PASS 无 regression**；⑦ **§5 新增 Pattern 13**（方法论可复用性验证 —— "跑 1 个新流程就够"）；⑧ 新增 iterations/2026-09-23_invoice-approval-end2end.md（第九轮迭代）；⑨ v2.17 → v2.18 changelog 同步。 |
| **v1.8** | **2026-09-23** | **tdd-flow 自动化增强 · 第十轮飞轮转动**：① **tdd-flow.py 加 `--variable` 参数**（JSON 字符串透传）；② **加 `--scenarios` 多场景**（`name:json\|name:json`）；③ **加 `--save-baseline` 自动归档**（生成 v0_N baseline md）；④ **修 2 bug**：flow.auto 绕过 actor / KeyError 'taskName'；⑤ **generate_md 支持多 scenario**（每 scenario 一节）；⑥ **fdep 兼容性**测试通过；⑦ **§5 新增 Pattern 14**（tdd-flow scenario 自动化 —— "每个 decision 分支一个 scenario"）；⑧ 新增 iterations/2026-09-23_tdd-flow-variable.md；⑨ v2.18 → v2.19 changelog 同步。 |
| **v1.9** | **2026-09-23** | **W12 驳回分支 · 第十一轮飞轮转动**：① **invoice-approval 加驳回**（`submitType=5 RE_APPLY` 跳回 submit）；② **删除 e_resurrect 边**（避免孤儿 task）；③ **tdd-flow 加 per-scenario submitType**（`name:json:submitType`）；④ **智能防循环**（submit 永远 1，approve 第一次 5，之后 1）；⑤ **3 scenarios 全过**：small/big/reject；⑥ **驳回闭环**：approve(驳回) → submit(重提) → approve(通过) → pay → DONE；⑦ **§5 新增 Pattern 15**（驳回机制选择 —— "submitType=5 RE_APPLY 是驳回+重提的正解"）；⑧ 新增 iterations/2026-09-23_reject-branch.md；⑨ v2.19 → v2.20 changelog 同步。 |
| **v2.0** | **2026-09-23** | **W13 actor resolver · 第十二轮飞轮转动**（里程碑：methodology 从"工具"升级为"架构"）：① **核心发现** engine `_resolve_actors` 已支持 3 种 actor resolver 语法（@role:/顶级变量/applicant）；② **invoice-approval v0.5 启用 resolver**；③ **传顶级变量 tf_manager/tf_treasurer**；④ **substring bug 发现**：tf_applicant 被错误解析 → 改用 applicant 占位符；⑤ **e2e 验证**：3 actor 全部解析为真实 user_id，**无需 flow.auto**；⑥ **tdd-flow 加 --top-vars**；⑦ **§5 新增 Pattern 16**（actor resolver 三选一 —— "申请节点用 applicant / 固定角色用 @role / 动态指定用 tf_*"）；⑧ 新增 iterations/2026-09-23_actor-resolver.md；⑨ v2.20 → v2.21 changelog 同步。 |
| **v2.1** | **2026-09-23** | **W16 fdep baseline 自动化 · 第十三轮飞轮转动**：① **3 scenarios 全过**：happy(DONE) / reject(REJECT) / resurrect(DONE after RE_APPLY)；② **修 3 bug**：scenario.submitType 智能应用 / resurrect_attempted 防循环 / 终态灵活性；③ **自动 baseline 生成**；④ **invoice-approval 无 regression**；⑤ **§5 新增 Pattern 17**（工具化回归 —— "老流程也能用 tdd-flow scenarios 一键覆盖"）；⑥ 新增 iterations/2026-09-23_fdep-baseline-auto.md；⑦ v2.21 → v2.22 changelog 同步。 |
| **v2.2** | **2026-09-23** | **W20 tdd-flow baseline 对比 · 第十四轮飞轮转动**：① **加 `--compare-baseline <path>` 参数**；② **`compare_with_baseline()` 函数**：提取 signature（忽略瞬态字段）+ 逐字段对比 + 友好 diff 摘要；③ **3 测试全过**：完全一致（exit 0）/ 故意改（exit 1）/ 跨流程（识别差异）；④ **CI 友好**（diff → exit 1）；⑤ **§5 新增 Pattern 18**（regression 自动化 —— "baseline 对比 = CI 看门狗"）；⑥ 新增 iterations/2026-09-23_baseline-compare.md；⑦ v2.22 → v2.23 changelog 同步。 |
| **v2.3** | **2026-09-23** | **W22 tests.json 集中管理 · 第十五轮飞轮转动**：① **`ToT/tdd/tests.json`** 集中 fdep + invoice-approval 的 scenarios / top_vars / baseline；② **tdd-flow 加 `--tests-file` 参数** + `load_tests_file()`；③ **save-baseline 同时生成 md + json**（compare-baseline 需要 json）+ `_baseline_meta` 标记；④ **baseline glob 智能选择**（自动 baseline 优先）；⑤ **修 2 bug**：save-baseline 缺 json / load_tests_file 调用顺序；⑥ **CI 集成**：`for flow in fdep invoice-approval; do tdd-flow.py <flow> --tests-file tests.json || exit 1; done`；⑦ **§5 新增 Pattern 19**（集中管理 —— "tests.json = 流程回归的 single source of truth"）；⑧ 新增 iterations/2026-09-23_tests-json.md；⑨ v2.23 → v2.24 changelog 同步。 |
| **v2.4** | **2026-09-23** | **W23 tdd-flow dry-run · 第十六轮飞轮转动**：① **tdd-flow 加 `--dry-run` 参数**；② **5x 提速**（0.85s → 0.16s）；③ **CI 两阶段**：PR 快速 + main 完整；④ **错误检测**：dry-run 仍能 catch 静态校验 errors + verify_flow errors；⑤ **tests-file + dry-run 兼容**；⑥ **§5 新增 Pattern 20**（CI 两阶段 —— "PR dry-run + main full-run"）；⑦ 新增 iterations/2026-09-23_dry-run.md；⑧ v2.24 → v2.25 changelog 同步。 |
| **v2.5** | **2026-09-23** | **W21 tdd-flow 并发执行 · 第十七轮飞轮转动**：① **tdd-flow 加 `--parallel N` 参数**；② **asyncio.gather + Semaphore 限流**；③ **6 scenarios 串行 vs 并行测试**（功能正常，加速有限 in-memory 场景）；④ **tests-file + parallel + compare-baseline 全集成**；⑤ **§5 新增 Pattern 21**（并发执行 —— "asyncio.gather + Semaphore 安全并发独立 scenarios"）；⑥ 新增 iterations/2026-09-23_parallel.md；⑦ v2.25 → v2.26 changelog 同步。 |
| **v2.6** | **2026-09-23** | **W17 驳回 audit 链 · 第十八轮飞轮转动**：① **核心发现** engine `_merge_exec_into_instance` 已自动合并 comment/decision_reason/decision_memo；② **tdd-flow parse_scenarios 扩展 `:comment`**；③ **run_path 自动传 3 字段**；④ **tests.json + Job Card 更新**；⑤ **§5 新增 Pattern 22**（audit 链 —— "execute 自动透传 comment → instance.variables"）；⑥ 新增 iterations/2026-09-23_reject-memo.md；⑦ v2.26 → v2.27 changelog 同步。 |
| **v2.7** | **2026-09-23** | **W18 applicant substring bug 修复 · 第十九轮飞轮转动**：① **加 `_is_applicant_token()` 辅助函数**（word boundary 匹配）；② **改 2 处 substring 替换**（同步 + 异步版本）；③ **占位符命名现在完全自由**（任何 token 名都安全）；④ **regression 全过**（invoice + fdep 100%）；⑤ **§5 新增 Pattern 23**（word boundary 优先 —— "占位符匹配永远用 word boundary，避免 substring 误命中"）；⑥ 新增 iterations/2026-09-23_applicant-bug.md；⑦ v2.27 → v2.28 changelog 同步。 |
| **v2.8** | **2026-09-23** | **W26 fdep baseline 现代化 · 第二十轮飞轮转动**：① **tdd-flow 加 audit 字段**（decision_reason/decision_memo/job_card_url）；② **生成 3 个自动 baseline**（v0_1/v0_2/v0_3）；③ **恢复 v3audit 历史快照**；④ **fdep baseline 自动率 0/4 → 3/4 (75%)**；⑤ **§5 新增 Pattern 24**（baseline 现代化 —— "自动 baseline 主导 + 手工保留历史快照"）；⑥ 新增 iterations/2026-09-23_fdep-baseline-modern.md；⑦ v2.28 → v2.29 changelog 同步。 |
| **v2.9** | **2026-09-23** | **W27 report-json dashboard · 第二十一轮飞轮转动**：① **加 `--all-flows`** + **`--report-json`**；② **dashboard JSON schema**（summary + flows[]）；③ **重构 main**：拆 main + run_all_flows + run_single_flow + main_legacy；④ **CI 集成模板**（dashboard.json 上传 artifact）；⑤ **§5 新增 Pattern 25**（dashboard 模式 —— "structured output 让 CI 可消费"）；⑥ 新增 iterations/2026-09-23_report-json.md；⑦ v2.29 → v2.30 changelog 同步。 |
| **v3.0** | **2026-09-23** | **W24 baseline-only 模式 · 第二十二轮飞轮转动**（里程碑：v3.0 —— EA 体系正式 3.0 版本）：① **加 `--baseline-only` 参数**；② **baseline 完整性 4 条件检查**；③ **4.5x 加速**（0.7s → 0.155s）；④ **CI 三阶段**：PR dry-run + merge baseline-only + release 实跑；⑤ **§5 新增 Pattern 26**（CI 三阶段 —— "PR dry-run / merge baseline-only / release full-run"）；⑥ 新增 iterations/2026-09-23_baseline-only.md；⑦ v2.30 → v2.31 changelog 同步。 |
| **v3.1** | **2026-09-23** | **W29 dashboard HTML 渲染 · 第二十三轮飞轮转动**：① **加 `--report-html`**；② **`render_html_dashboard()`** 单文件 HTML + 内联 CSS（3858 字节）；③ **summary cards + flow table 结构**；④ **样式**：响应式 + 颜色编码；⑤ **§5 新增 Pattern 27**（dashboard 双格式 —— "JSON 给机器 / HTML 给人类"）；⑥ 新增 iterations/2026-09-23_dashboard-html.md；⑦ v2.31 → v2.32 changelog 同步。 |
| **v3.2** | **2026-09-23** | **W30 + W31 index + dashboard 交互 · 第二十四轮飞轮转动**：① **iterations/README.md**（23 圈统一索引 + 主题分类 + 飞轮度量表）；② **dashboard.html 加 JS toggle**（点击 row 展开 scenario 详情）；③ **dashboard.html 5503 字节**（含交互）；④ **§5 新增 Pattern 28**（闭环 —— "iterations index + interactive dashboard"）；⑤ 新增 iterations/2026-09-23_index-dashboard.md；⑥ v2.32 → v2.33 changelog 同步。 |
| **v3.3** | **2026-09-23** | **W28 + W32 only-changed + 时间趋势 · 第二十五轮飞轮转动**：① **W28 --only-changed**（git diff 3 类：工作区/staged/untracked）；② **W32 时间趋势**（history 自动保存 + trend 表）；③ **CI 4 模式**（dry-run + baseline-only + 实跑 + only-changed）；④ **§5 新增 Pattern 29**（CI 智能化 —— "git diff → only-changed → 智能选择 + history → trend"）；⑤ 新增 iterations/2026-09-23_only-changed-trend.md；⑥ v2.33 → v2.34 changelog 同步。 |
| **v3.4** | **2026-09-23** | **W34 sparkline · 第二十六轮飞轮转动**：① **`render_sparkline()`** SVG inline；② **颜色编码**（🟢/🟡/🔴/⚪）；③ **每 flow 一列 sparkline**（最近 10 次跑）；④ **tooltip** 显示 passed/total；⑤ **修 build_dashboard_entry** 加 `passed_scenarios`；⑥ **§5 新增 Pattern 30**（sparkline 模式 —— "per-flow 时间序列柱状图，单文件 HTML 内嵌"）；⑦ 新增 iterations/2026-09-23_sparkline.md；⑧ v2.34 → v2.35 changelog 同步。 |
| **v3.5** | **2026-09-23** | **W36 + W35 time filter + DEMO 文档 · 第二十七轮飞轮转动**：① **W36 dashboard 时间 filter**（4 按钮 + JS filterByDays + data-ts）；② **W35 EA DEMO.md**（团队培训实战手册：3 个 demo + FAQ + 速查 + 演练）；③ **dashboard.html ~8 KB**（+ filter 按钮 + JS）；④ **§5 新增 Pattern 31**（培训材料 —— "30 分钟内掌握 EA = 3 个 demo"）；⑤ 新增 iterations/2026-09-23_time-filter-demo.md；⑥ v2.35 → v2.36 changelog 同步。 |
| **v3.6** | **2026-09-23** | **W38 archive-flow SOP · 第二十八轮飞轮转动**：① **`ToT/sop/archive-flow.md` + `archive_flow.py`**；② **5 步流程**：SPI API 背景 → 报告 → 打包 → file-share → 清理；③ **8 章节报告模板**；④ **file-share 集成**（取件码自动返回）；⑤ **§5 新增 Pattern 32**（归档自动化 —— "测完即归档 + 跨环境分享 + 本地清理"）；⑥ 新增 iterations/2026-09-23_archive-flow.md；⑦ v2.36 → v2.37 changelog 同步。 |
| **v3.7** | **2026-09-23** | **W39 archive dry-run · 第二十九轮飞轮转动**：① **`--dry-run` 参数**；② **3 维度预览**（tar.gz / report.md / 清理）；③ **跳过实际副作用**；④ **§5 新增 Pattern 33**（预览模式 —— "可逆性优于不可逆性"）；⑤ 新增 iterations/2026-09-23_archive-dry-run.md；⑥ v2.37 → v2.38 changelog 同步。 |
| **v3.8** | **2026-09-23** | **W39 share config 集中化 · 第三十轮飞轮转动**（用户口头指令："SHARE_URL 在 archive_flow 中写死了，需要转移到 config"）：① **新建 `ToT/config/share.json`** v1.0（upload_url + download_url_template + expire_unit + default_expire_value + max_expire_value）；② **`archive_flow.py` 移除 2 处硬编码 URL**（`SHARE_URL` 常量 + 下载 URL 模板）→ 新增 `load_share_config()` 加载器；③ **CLI `--expire-value` 替代 `--expire-days`**（语义化，单位由 share.json 决定；保留旧参数兼容）；④ **`archive-flow.md` v0.2** + §9 配置说明 + §10 changelog；⑤ **`ea-compliance.py` §9.6.5 新增**（share.json 存在合法检查，§9.6 4→5 项）；⑥ **§9 检查项 43 → 44，44/44 PASS**；⑦ **tdd-flow 回归 2/2 flows 6/6 scenarios**；⑧ **Pattern 9 升级**：单一配置 → **双配置域**（servers.json + share.json，按职责拆分）；⑨ **§9 新增 §9.6 配置集中化节**（5 项，含未来扩展模板 9.6.6-9.6.8）；⑩ 新增 iterations/2026-09-23_share-config.md；⑪ iterations/README.md 刷新至 30 圈。 |
