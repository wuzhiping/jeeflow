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
