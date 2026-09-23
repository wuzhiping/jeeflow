# FDEP（Foundational Development & Engagement Process）

> **JSON 定义**：[`../fdep.json`](../fdep.json)（version: 0.6.2）
> **适用场景**：jeeFlow 自身的协作主流程——从"任意来源的需求提出"到"反馈/知识沉淀"的全闭环。
> **发起者**：任意来源（人类 / AI Agent / 外部用户均可触发 `start`）

---

## 1. 流程概览

FDEP 是 jeeFlow 引擎**吃自己狗粮**的范例：用 jeeFlow 自身的 Snaker 流程定义格式，描述 jeeFlow 自身的协作闭环。

**6 个正式阶段**（+ 1 个接收决策节点 + 1 个驳回终点）：

```
start → stage_intake → decision_intake → stage_pm → stage_design
      → stage_dev → stage_review → stage_feedback → end
                                       ↘ end_rejected (驳回)
```

**关键设计决策**：

- **start ≠ R3**：start 接受**任何来源**的请求（人类 / AI / 外部用户），R3 是后续**接收窗口**
- **decision_intake 用 submitType 路由**：1=立项, 2=驳回, 默认=立项（兜底避免孤儿 task）
- **占位用户 u_fdp_pm**：当前所有阶段由 `u_fdp_pm` 一人担当，便于自动化测试；多人分工需 v0.7+ 引入 `assignmentHandler`

---

## 2. 节点清单

| 节点 ID | 类型 | 阶段 | 角色 |
|---------|------|------|------|
| `start` | snaker:start | 入口 | — |
| `stage_intake` | snaker:task | 0. 接收/登记 | R3 / fdep_intake / u_fdp_pm |
| `decision_intake` | snaker:decision | 接收决策路由 | — |
| `stage_pm` | snaker:task | 1. RML 立项 | R3 / fdep_rml / u_fdp_pm |
| `stage_design` | snaker:task | 2. 架构/接口设计 | R7 / fdep_arch / u_fdp_pm |
| `stage_dev` | snaker:task | 3. 开发实现 | R2 / fdep_dev / u_fdp_pm |
| `stage_review` | snaker:task | 4. 评审/验收/发布 | R6 / fdep_review / u_fdp_pm |
| `stage_feedback` | snaker:task | 5. 反馈/知识沉淀 | R5 / fdep_kb / u_fdp_pm |
| `end` | snaker:end | 协作闭环 | — |
| `end_rejected` | snaker:end | 驳回闭环 | — |

**完整工作手册**：见 [`NODES.md`](./NODES.md)

---

## 3. 角色清单

| 抽象 R | SPI 角色 | 实际用户（占位） | 流程节点 |
|--------|----------|------------------|----------|
| — | — | 任意来源 | start |
| R3 | `fdep_intake` | u_fdp_pm | stage_intake |
| R3 | `fdep_rml` | u_fdp_pm | stage_pm |
| R7 | `fdep_arch` | u_fdp_pm | stage_design |
| R2 | `fdep_dev` | u_fdp_pm | stage_dev |
| R6 | `fdep_review` | u_fdp_pm | stage_review |
| R5 | `fdep_kb` | u_fdp_pm | stage_feedback |
| R3 | — | u_fdp_pm | end_rejected（驳回记录） |

**完整角色矩阵**：见 [`ROLES.md`](./ROLES.md)
**角色映射原理**：见 [`../../mapping.md`](../../mapping.md)

---

## 4. 变更记录

详见 [`CHANGELOG.md`](./CHANGELOG.md)

主要里程碑：
- **v0.5**：5 阶段线性骨架（双出边触发 W012）
- **v0.6.2**：插入 decision_intake 节点修 W012 + assignee 改 u_fdp_pm 占位；happy path 实测 PASSED

---

## 5. Job Card 模板（v1.0）

> 每个**任务节点**（stage_*）配一张 `job_card_<node>.md`，给执行者（人或 AI）一站式干活。
> **目标**：executor 拿到 taskId + 打开本卡片 → 立即知道做什么 / 怎么做 / 产出什么 / 传给谁。
> **协议**：与 §RESPONSES.md Decision Mem 协议 v1.1 lite+ 配套（含 `next_handoff` 字段）。

### 5.1 卡片结构（8 节）

| § | 名称 | 内容 |
|---|------|------|
| 1 | 你的身份 | node id / assignee / SPI 角色 / 触发方式 |
| 2 | 你的输入 | 前节点的 `variable.decision_memo.next_handoff` + 流程定义 + 必要文件 |
| 3 | 你的目标 | produce / storage / exitCriteria |
| 4 | 你的 checklist | 按顺序的执行步骤（6~10 条） |
| 5 | 你的产出 | execute body 完整 JSON 模板（含 `next_handoff` 字段） |
| 6 | 你的 handoff | 下一节点 + 它需要的输入 + 时机 |
| 7 | 关联 + SOP | NODES.md / RESPONSES.md / SOP / mapping 引用 |
| 8 | 变更日志 | 版本记录 |

### 5.2 命名规则（§10 强制约束）

| 规则 | 说明 |
|------|------|
| 文件名 | `job_card_<node_id>.md`，全小写 |
| 位置 | `ToT/flows/fdep/job_cards/`（fdep/ 子目录，与 fdep.json 同包） |
| 一一对应 | fdep.json 中每个 `snaker:task` 节点一张卡（决策 / 起止节点不需要） |
| 节点 ↔ 文件 | `stage_pm` ↔ `job_cards/job_card_stage_pm.md` |

### 5.3 当前已立 Job Cards

| 节点 | 卡 | 状态 |
|------|----|------|
| stage_intake | [`job_cards/job_card_stage_intake.md`](./job_cards/job_card_stage_intake.md) | ✅ v0.1 自动生成 |
| stage_pm | [`job_cards/job_card_stage_pm.md`](./job_cards/job_card_stage_pm.md) | ✅ v0.1 自动生成 |
| stage_design | [`job_cards/job_card_stage_design.md`](./job_cards/job_card_stage_design.md) | ✅ v0.1 自动生成 |
| stage_dev | [`job_cards/job_card_stage_dev.md`](./job_cards/job_card_stage_dev.md) | ✅ v0.1 自动生成 |
| stage_review | [`job_cards/job_card_stage_review.md`](./job_cards/job_card_stage_review.md) | ✅ v0.1 自动生成 |
| stage_feedback | [`job_cards/job_card_stage_feedback.md`](./job_cards/job_card_stage_feedback.md) | ✅ v0.1 自动生成 |

**决策节点 / 起止节点不需要卡**（`start` / `decision_intake` / `end` / `end_rejected` 都是引擎自动流转）。

### 5.4 生成器

`ToT/sop/gen-job-cards.py` 读 fdep.json + NODES.md + RESPONSES.md → 批量产出 6 张卡到 `job_cards/`。

**用法**：

```bash
# 默认：跳过已存在的卡（保护手工编辑）
python3 ToT/sop/gen-job-cards.py

# 强制重新生成（覆盖全部）
python3 ToT/sop/gen-job-cards.py --force
```

**何时重跑**：
- fdep.json 节点定义变化（新增/删除 task 节点）
- NODES.md 工作步骤 / 注意事项更新
- RESPONSES.md §X.2.1 模板调整

**自动解析**：
- `assignee` / `form` / `stage` / `artifact` / `storage` / `exitCriteria` ← fdep.json props
- 工作步骤 / 注意事项 ← NODES.md 工作步骤段
- Decision Mem 模板 ← RESPONSES.md §X.2.1

**校验**：生成后 §5 JSON 必为可解析 JSON；所有 `job_card_url` 必指向 `job_cards/` 内真实存在的文件。

---

## 6. 关联文档

| 文档 | 用途 |
|------|------|
| [NODES.md](./NODES.md) | 每个节点的纯文本工作手册（无 handoff 字段） |
| [ROLES.md](./ROLES.md) | 角色清单 + SPI 映射 |
| [RESPONSES.md](./RESPONSES.md) | AI 起草响应的模板 + Decision Mem 协议 v1.1 lite+ |
| [CHANGELOG.md](./CHANGELOG.md) | 流程变更记录（含 Job Card 增删） |
| [../fdep.json](../fdep.json) | 流程定义 JSON（唯一权威） |
| [../../mapping.md](../../mapping.md) | R 角色 ↔ SPI ↔ 用户三层映射 |
