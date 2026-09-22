# 角色清单（Roles）

> 本流程涉及的角色矩阵：抽象 R 角色（语义层，README §4）+ SPI 角色（机器层，spi/dev）+ 实际用户（占位/未来真实）。

---

## 1. 角色映射总表

| 抽象 R | SPI 角色 | 实际用户（v0.6.2 占位） | 流程节点 | 备注 |
|--------|----------|-------------------------|----------|------|
| — | — | **任意来源**（人类 / AI / 外部用户） | `start` | 不限制提交者 |
| **R3** | `fdep_intake` | u_fdp_pm | `stage_intake` | PM 接收窗口 |
| **R3** | `fdep_rml` | u_fdp_pm | `stage_pm` | RML 立项 |
| **R7** | `fdep_arch` | u_fdp_pm | `stage_design` | 架构/接口 |
| **R2** | `fdep_dev` | u_fdp_pm | `stage_dev` | 开发实现 |
| **R6** | `fdep_review` | u_fdp_pm | `stage_review` | 评审/验收 |
| **R5** | `fdep_kb` | u_fdp_pm | `stage_feedback` | 知识沉淀 |
| **R3** | — | u_fdp_pm | `end_rejected` | 驳回记录归档 |

---

## 2. 各角色在本流程中的职责

### R1a（流程参与者）—— 不在本流程 assignee 中

R1a 仅在 `start` 节点作为发起者出现（无角色限制），不在任何 task 的 assignee 列表中。

### R1b（流程制定者）—— 不在本流程 assignee 中

R1b 仅维护本流程的 fdep.json + fdep/ 文件夹，不参与任务执行。

### R3（产品经理 PM）

| 节点 | 职责 |
|------|------|
| `stage_intake` | 接收窗口：登记原始请求，决定立项/驳回 |
| `stage_pm` | RML 立项：编写 RML 文档 |
| `end_rejected` | 驳回记录归档（虽然 assignee=— 但实际由 PM 操作） |

### R7（架构师 / 架构 / 设计 Agent）

| 节点 | 职责 |
|------|------|
| `stage_design` | 架构文档 + 接口设计 + Mock 数据 |

### R2（开发者 Agent）

| 节点 | 职责 |
|------|------|
| `stage_dev` | 源代码 + 单元测试 |

### R6（评审 Agent）

| 节点 | 职责 |
|------|------|
| `stage_review` | 评审 + 验收 + 发布 |

### R5（知识管理员 + 知识 Agent）

| 节点 | 职责 |
|------|------|
| `stage_feedback` | Issue 追踪 + 知识库条目 |

---

## 3. 当前占位用户 u_fdp_pm

| 项 | 值 |
|----|----|
| uid | `u_fdp_pm` |
| name | `占位·待分配` |
| post | `FDEP 流程占位` |
| dept | `DFDEP`（FDEP协作组，顶层，无 parent） |
| level | `P5` |
| email | `fdp-pm@flowmatrix.io` |
| 担当角色 | 全部 6 个 fdep_* 节点角色（一人分饰 6 角） |

---

## 4. v0.7+ 多用户分工路线图

当真实人员到位时，按以下优先级分配：

| 节点 | 建议接手 | 备注 |
|------|----------|------|
| `stage_intake` | 实际 PM（如 u_pm_alice） | 接收窗口需要人工判断 |
| `stage_pm` | 实际 PM 或 RML Owner | RML 编写 |
| `stage_design` | 架构师 / tech_lead | 架构决策 |
| `stage_dev` | 开发者 Agent（具体视项目） | 自动代码生成 |
| `stage_review` | R6 + R3 双签（fork-join） | 评审自动化 + 人工验收 |
| `stage_feedback` | R5 | 知识库管理员 |

**多用户场景技术条件**：

1. spi/dev 添加真实用户 + SPI 角色映射
2. fdep.json 每个 task 加 `assignmentHandler`（参见 `flows_demo/` 中的样例）
3. 重跑 `spi-verify.py` + `tdd-flow.py` + `flow-lint.py` 验证

---

## 5. 关联文档

- [`../../mapping.md`](../../mapping.md) — 抽象 R → SPI 角色 → 用户的映射原理
- [`../../README.md#4-角色分工`](../../README.md) — 抽象 R 角色的定义与边界
- [`../fdep.json`](../fdep.json) — 流程定义 JSON
