# EA: 流程全生命周期体系架构 (Flow Lifecycle Enterprise Architecture) · v1.0

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