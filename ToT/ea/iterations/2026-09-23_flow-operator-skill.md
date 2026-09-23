# Iteration #31 · 2026-09-23 · W40 · 执行者角色模型 + flow-operator skill

> **驱动**：用户口头讨论"如何定义 jeeflow 流程实例的使用者角色……专注在执行层面"
> **核心成果**：① **2-lens 模型**（initiator / assignee → `flow-operator` 统一名）；② **`ToT/skills/flow-operator/SKILL.md` v0.3**（102 行 / 5 节 / 0 处设计层泄露）

---

## 1. 时间线（~60 分钟 / 3 个会话回合）

| 时段 | 工作 |
|------|------|
| 0~25 min | **角色讨论**（3 轮收敛到 2-lens 模型 + 统一名 `flow-operator`） |
| 25~55 min | **SKILL.md 撰写**（v0.1 骨架 → v0.2 +mermaid → v0.3 隐藏设计层） |
| 55~60 min | **本迭代留档**（含 README 刷新） |

---

## 2. 角色讨论 · 3 轮收敛

### 2.1 第一轮 · 5 候选定位 + 6 角色猜想

用户原话列出 **11 类活动**（发起 / 接单 / 看上下文 / 看指南 / 完成任务 / 转交 / 提交决策 / 追踪进度 / 回顾统计 / 复盘细节 / 其他）。

我先盘出 5 候选定位：
- A 权限模型
- B 协作视角（推荐）
- C 审计标签
- D 运营效率
- E 业务建模

并基于 jeeFlow 已有资产（Decision Mem / actor resolver / Job Card）推测 **6 个执行层角色**：
- ① 发起人
- ② 经办人
- ③ 委托人
- ④ 关注人
- ⑤ 主管
- ⑥ 流程观察者

### 2.2 第二轮 · 用户简化到 2 视角

用户回答让我**大刀砍掉**——核心回复：
> "按需要发起授权的流程并追踪进度，**或者**完成被指派的任务"

→ 角色 = `initiator` 视角 OR `assignee` 视角（不是 2 个权限墙，是 2 个协作关系）。

3 条朴素边界：
1. 同一用户同一实例允许自交叉
2. 转交是设计者的事，使用者层不掺和
3. 复盘 = 读 log

### 2.3 第三轮 · 命名收口

3 候选命名：
- A `Initiator` / `Assignee`（BPMN 标准，引擎字段一致）
- B `Originator` / `Handler`
- C `Applicant` / `Operator`

用户进一步收口 → **统一名 `flow-operator`**，2 视角是其在每个实例上的状态：

| 概念 | 英文 | 含义 |
|------|------|------|
| 执行者（人） | `flow-operator` | 执行层使用者总称 |
| 实例状态 1 | `initiator`（我创建的） | flow-operator 是该实例发起人 |
| 实例状态 2 | `assignee`（我被指派的） | flow-operator 是该实例某节点经办人 |
| 引擎字段（已存在） | `applicant` / `assignee` | 与状态一一对应，无须改引擎 |

---

## 3. SKILL.md 撰写 · 3 轮迭代

### 3.1 v0.1 · 骨架填齐（5 节）

填了 4 个空 section：
- **overview**: 定位 + 边界
- **Knowledge**: API-first 原则（不塞背景，塞怎么查）
- **Tools**: 按场景分 5 组（A 发起 / B 接单 / C 追踪 / D 统计 / E 系统层）+ ❌ 设计层（应剔除）
- **Others**: 安全约束 3 条

### 3.2 v0.2 · 加 mermaid demo

在 Knowledge 与 Tools 之间插入 `## flow` 节：
- mermaid `sequenceDiagram`
- 通用 demo（不绑定具体流程）
- 4 阶段 6 endpoint：发起 → 接单 → 决策 → 复盘

### 3.3 v0.3 · 隐藏设计层 endpoint（最小知情原则）

用户指令：**"隐藏设计层 endpoint，不要让它知晓"**

| 改动 | 旧 | 新 |
|------|----|----|
| 删除 ❌ 设计层小节 | `processDesign/*` `processSurrogate/*` 表 | （不存在） |
| overview 改写 | "不涉及流程定义 / 节点设计 / 表单配置等**设计层**" | "范围限定在执行层：发起 / 接单 / 决策 / 追踪 / 复盘" |
| Tools §A 行 1 | `processDesign/listByType` | `processDefine/page` |
| 安全约束 #2 | `不调设计层 endpoint` | `只用 ## Tools 列出的 endpoint：不试探未列出的 API` |

**全文扫描** `design / surrogate / 设计层 / 流程设计 / 表单配置` = **0 处泄露**。

---

## 4. 关键决策（ADR 风格）

### ADR-31.1 · 角色不是权限墙，是协作视角
- **背景**：用户活动 11 类，但实际只需 2 个视角
- **决策**：flow-operator 是 1 类人，2 个视角是其在每个实例上的状态
- **后果**：允许自交叉；转交是设计层问题；复盘 = 读 log

### ADR-31.2 · Knowledge 节采用 API-first
- **背景**：用户回答"流程相关问题原则上都能用 API 查"
- **决策**：Knowledge 不塞背景，塞"先用 API 查不猜"
- **后果**：Knowledge 极简（1 行）；Tools 成为 reference manual

### ADR-31.3 · 最小知情（隐藏设计层 endpoint）
- **背景**：用户明确"不要让它知晓"
- **决策**：SKILL.md 完全不提 `processDesign/*` `processSurrogate/*`
- **后果**：安全约束改为正向引导"只用 Tools 列出的"

### ADR-31.4 · mermaid demo 用通用 demo，不绑流程
- **背景**：避免误导 + 保持 skill 通用性
- **决策**：用 sequenceDiagram 抽象表达，不引用具体流程
- **后果**：可被任何流程复用，无需维护多版本

---

## 5. 度量（飞轮 31 圈累积）

| 指标 | #30 | **#31** |
|------|-----|---------|
| §9 检查项 | 44 | **44**（未变，本轮无配置改动） |
| skills 目录 | ❌ | **✅ ToT/skills/flow-operator/SKILL.md v0.3** |
| AI 伙伴定义 | ❌ | **✅ flow-operator（执行层使用者的 AI 代理）** |
| SKILL 节数 | 0 | **5 节齐全** |
| mermaid demo | 0 | **1 个（通用 sequenceDiagram）** |
| 配置文件数 | 2 (servers + share) | **2** |
| 工具数 | 10 | **10** |
| SOP 数 | 15 | **15** |
| EA roadmap 版本 | v3.8 | **v3.8** |

**关键变化**：从"面向人类执行者"→"面向人类 + AI 伙伴 + skill 模板"。

---

## 6. 闭环示意

```
┌── "如何定义执行层使用者角色？" ──┐
↓                       │
3 轮讨论收敛到 2-lens 模型 │
↓                       │
统一名 flow-operator       │
↓                       │
写 SKILL.md v0.1 骨架    │
↓                       │
v0.2 加 mermaid demo     │
↓                       │
v0.3 隐藏设计层 endpoint │
↓                       │
v0.3 定版（102 行 / 0 泄露）│
↓                       │
→ 飞轮第 31 圈 ✅           │
```

---

## 7. 经验沉淀

### 7.1 角色建模的反模式
- **不要从"权限"出发**：权限是约束，角色是关系
- **不要先列 6 个角色再合并**：用户可能一开始只要 2 个
- **不要把"挑战转交"塞进角色层**：转交是流程设计问题
- **不要把"挑战复盘"复杂化**：复盘 = 读 log，没新概念

### 7.2 SKILL 撰写的奥卡姆
- **逐节确认**：用户能 sign-off 每一节，避免最后一刻大改
- **先填骨架再优化**：骨架对齐后再扩内容
- **隐藏 = 安全**：最小知情原则，不该看见的别让看见
- **mermaid 通用 demo**：不绑定具体业务，skill 才能复用

### 7.3 与 jeeFlow 引擎的对齐
- `applicant` ↔ `initiator`（已存在）
- `assignee` ↔ `assignee`（已存在）
- **无须改引擎**——引擎侧机制已够支撑 2-lens 模型
- 引擎侧的 actor resolver（`@role:` / `tf_*`）继续按设计者决策使用

---

## 8. SKILL.md 节标题索引（最终态）

```
## overview            ← 定位 + 边界（5 行）
## Knowledge           ← API-first 原则（1 行）
## flow                ← mermaid sequenceDiagram demo
## Tools (5 场景 + 系统层)
  ### A · 发起流程（initiator 视角）
  ### B · 处理待办（assignee 视角）
  ### C · 追踪进度（initiator + assignee 共用）
  ### D · 统计 + 复盘（个人视角）
  ### E · 系统层
## Others
  ### 安全约束（3 条）
```

---

## 9. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第三十一轮迭代 · W40 执行者角色 + flow-operator skill**：① **3 轮角色讨论**：5 候选定位 → 6 角色猜想 → **2-lens 模型收口**（initiator / assignee）+ **统一名 `flow-operator`**；③ **新建 `ToT/skills/flow-operator/SKILL.md` v0.3**（102 行 / 5 节齐全）；④ **3 轮迭代**：v0.1 骨架（overview/Knowledge/Tools/Others）+ v0.2 加 mermaid demo + v0.3 隐藏设计层 endpoint（最小知情原则）；⑤ **Tools 5 场景分**（A 发起 / B 接单 / C 追踪 / D 统计 / E 系统层）+ 系统层 2 endpoint（healthz / verify）；⑥ **全文扫描** `design / surrogate / 设计层 / 流程设计 / 表单配置` **0 处泄露**；⑦ **安全约束 3 条**：不硬编码 URL / 只用 Tools 列出的 / 决策必须携带 Decision Mem；⑧ **4 条 ADR 沉淀**（角色不是权限墙 / API-first / 最小知情 / mermaid 通用 demo）；⑨ 新增 iterations/2026-09-23_flow-operator-skill.md；⑩ iterations/README.md 刷新 30 → 31 圈。 |