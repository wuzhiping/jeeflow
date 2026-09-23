# 节点工作手册（Node Manual）

> 本文件详述 fdep.json 中每个节点的工作说明与注意事项。
> 节点顺序：`start → stage_intake → decision_intake → stage_pm → stage_design → stage_dev → stage_review → stage_feedback → end`（含 `end_rejected` 驳回分支）。

---

## start（snaker:start）

- **说明**：任意来源的需求/请求入口。
- **输入**：人类 / AI Agent / 外部用户 提交。
- **输出**：触发 `stage_intake`。
- **工作步骤**：
  1. 接收请求（不限制提交者角色）。
  2. 不做内容判定；不写代码；不修改任何文件。
- **注意事项**：
  - **不限制提交者角色**（任何人 / Agent / 外部用户）。
  - start ≠ R3（PM 是后续接收窗口，不是入口）。
  - 一旦 `stage_intake` 被激活，引擎自动流转。

---

## stage_intake（snaker:task）

- **说明**：PM 接收窗口（登记原始请求，决定立项或驳回）。
- **输入**：`start` 触发。
- **输出**：登记记录 → 触发 `decision_intake`。
- **工作步骤**：
  1. 读取请求内容。
  2. 评估：是否在本系统范围？是否重复请求？是否优先级合理？
  3. 决定：
     - **立项** → `submitType=1` (AGREE)
     - **驳回** → `submitType=2` (REJECT)
  4. 登记原始请求到 `ToT/pm/intake/<date>/<id>.md`。
- **注意事项**：
  - 决策结果必须显式记录（立项/驳回 + 理由）。
  - 驳回必须写理由（归档到 `ToT/pm/intake/rejected/`）。
  - 不要直接进入"接收 + 立项"两件事，decision_intake 节点负责分流。
- **关联角色**：R3 / `fdep_intake` / u_fdp_pm
- **关联产出物路径**：`ToT/pm/intake/`
- **TDD 实测**：✅ 启动后 stage_intake 自动 DONE（因为 startAndExecute 注入 operator=u_fdp_pm）

---

## decision_intake（snaker:decision）

- **说明**：决策路由节点，根据 `submitType` 路由到 `stage_pm` 或 `end_rejected`。
- **输入**：`stage_intake` 完成。
- **输出**：
  - `submitType==1` (AGREE) → `stage_pm`
  - `submitType==2` (REJECT) → `end_rejected`
  - 其他（含 submitType=0 默认值）→ `stage_pm`（default edge 兜底）
- **工作步骤**：
  - 引擎自动评估三条出边的 `expr`，选择匹配的第一条。
  - 无 `expr` 匹配的边：触发 FIX-T112 兜底（走第一条边），default edge 是显式兜底。
- **注意事项**：
  - **必须部署后立即回归决策路由**（FIX-T113 §117 历史 BUG：`_cleanup_orphan_decision_tasks` 可能抛 TypeError）。
  - default edge 不可省略（W013 警告）。
  - 不要修改 `expr` 表达式除非明确要改路由。
- **TDD 实测**：✅ 触发 FIX-T112 警告日志（兜底到 stage_pm），但流程仍正确流转

---

## stage_pm（snaker:task）

- **说明**：RML 立项。PM 编写 RML（Requirements Markup Language）文档。
- **输入**：`decision_intake` 路由通过（approve 分支）。
- **输出**：`RML 文档` → 触发 `stage_design`。
- **工作步骤**：
  1. 阅读 stage_intake 登记的请求。
  2. 编写 RML：背景 / 目标 / 用户故事 / 验收标准 / 范围。
  3. RML 自审通过。
  4. 落档到 `ToT/pm/rml/<date>/<id>.md`。
  5. 指派下一阶段（架构师）。
- **注意事项**：
  - RML 必须可独立阅读（包含完整上下文）。
  - RML 通过后才推 stage_design，不要"未完成即推"。
- **关联角色**：R3 / `fdep_rml` / u_fdp_pm
- **关联产出物路径**：`ToT/pm/rml/`
- **TDD 实测**：✅ DONE

---

## stage_design（snaker:task）

- **说明**：架构 / 接口设计。架构师输出架构文档 + 接口设计 + Mock 数据。
- **输入**：`stage_pm` 完成（RML 通过）。
- **输出**：`架构文档 + 接口设计 + Mock 数据` → 触发 `stage_dev`。
- **工作步骤**：
  1. 阅读 RML。
  2. 编写架构文档（模块划分、数据流、关键决策）。
  3. 接口设计：URL / method / request / response / 状态码。
  4. **接口编号必须连续**（API 接口规范 §8 要求）。
  5. Mock 数据：覆盖正常响应 + 异常场景。
  6. 落档到 `ToT/design/<date>/<id>.md`。
- **注意事项**：
  - 接口编号从 1 起递增、不可跳号、不可重复。
  - Mock 数据必须有正常 + 异常两种。
  - 不要直接进入开发（必须 R6 评审通过）。
- **关联角色**：R7 / `fdep_arch` / u_fdp_pm
- **关联产出物路径**：`ToT/design/`
- **TDD 实测**：✅ DONE

---

## stage_dev（snaker:task）

- **说明**：开发实现。开发者 Agent 输出源代码 + 单元测试。
- **输入**：`stage_design` 完成（架构/接口/Mock 就绪）。
- **输出**：`源代码 + 单元测试` → 触发 `stage_review`。
- **工作步骤**：
  1. 阅读架构文档 + 接口设计 + Mock 数据。
  2. 实现源代码（按接口规范）。
  3. 编写单元测试（覆盖正常 + 异常 + 边界）。
  4. 本地自测通过。
  5. 落档到 `ToT/src/<module>/` + `ToT/tdd/test_<module>.py`。
- **注意事项**：
  - **不修改 ToT/ 外的文件**（§1 边界规则），即使是"看起来无关"的修正。
  - 不擅自变更架构（需要回 stage_design）。
  - 单元测试覆盖率 ≥ 80%（项目基线）。
- **关联角色**：R2 / `fdep_dev` / u_fdp_pm
- **关联产出物路径**：`ToT/src/` + `ToT/tdd/`
- **TDD 实测**：✅ DONE

---

## stage_review（snaker:task）

- **说明**：评审 / 验收 / 发布。R6 自动评审 + R3 验收签字。
- **输入**：`stage_dev` 完成（代码 + 单测完成）。
- **输出**：`评审记录 + 发布说明` → 触发 `stage_feedback`。
- **工作步骤**：
  1. R6 自动评审：lint / 编译 / 单元测试覆盖率 / 接口契约。
  2. R3 验收：业务正确性 / 用户体验 / 文档完整性。
  3. 编写评审记录 + 发布说明。
  4. 落档到 `ToT/reviews/<date>/<id>.md`。
- **注意事项**：
  - **R6 评审通过 + R3 验收签字** 两者都需完成（v0.6.2 暂合并为一个 task，v0.7+ 拆 fork-join）。
  - 评审不通过 → 回到 stage_dev 重做（v0.7+ 引入回退边）。
  - 验收不通过 → 回到 stage_design 重做架构。
- **关联角色**：R6（评审） / `fdep_review` / u_fdp_pm（R3 验收留待 fork-join）
- **关联产出物路径**：`ToT/reviews/`
- **TDD 实测**：✅ DONE
- **未来改进**：拆为 fork-join（Q2），R6 自动评审 + R3 人工验收并行

---

## stage_feedback（snaker:task）

- **说明**：反馈 / 知识沉淀。R3 收集反馈 + R5 入库知识。
- **输入**：`stage_review` 完成。
- **输出**：`Issue 追踪记录 + 知识库条目` → 触发 `end`。
- **工作步骤**：
  1. 收集用户/Agent 反馈（issues/ 反馈渠道）。
  2. R5 把有价值的反馈入库到知识库。
  3. 每条反馈关联到 Task 或 Issue（不允许孤立文档）。
  4. 落档到 `ToT/issues/<date>/<id>.md` + `ToT/kb/<topic>.md`。
- **注意事项**：
  - **每条反馈必须关联到 Task 或 Issue**（无孤立文档是 R5 的硬约束）。
  - 反馈内容必须可执行（具体问题 / 复现步骤 / 期望行为）。
  - 知识库条目必须是经过提炼的通用知识，不是原始聊天记录。
- **关联角色**：R5（知识） / `fdep_kb` / u_fdp_pm（R3 反馈收集待 fork-join）
- **关联产出物路径**：`ToT/issues/` + `ToT/kb/`
- **TDD 实测**：✅ DONE

---

## end（snaker:end）

- **说明**：协作闭环。流程正常完成的终点。
- **输入**：`stage_feedback` 完成。
- **输出**：instance state = 20 (DONE)。
- **工作步骤**：引擎自动流转，无人工操作。
- **注意事项**：到达此节点表示全流程完成。

---

## end_rejected（snaker:end）

- **说明**：驳回闭环。PM 在 stage_intake 阶段判定请求不应进入流程。
- **输入**：`decision_intake` 路由到 reject 分支（`submitType==2`）。
- **输出**：instance state = 45 (REJECT) 或 20 (DONE)。
- **工作步骤**：
  1. PM 已登记驳回理由（stage_intake 步骤 4）。
  2. 引擎直接流转到 end_rejected。
- **注意事项**：
  - 驳回记录必须保留在 `ToT/pm/intake/rejected/`，**不可删除**（可追溯）。
  - 当前 end_rejected 是终止态，驳回后无法重新激活（Q7 未来改进）。
- **TDD 实测**：⚠️ 当前 reject path 实测作用在 stage_pm（因 submitType=0 触发 FIX-T112 兜底跳过 decision_intake），真正的"intake 阶段驳回"需手动 orchestration（不通过 startAndExecute，单独 execute stage_intake with submitType=2）。

---

## 关联文档

- [`../fdep.json`](../fdep.json) — 流程定义 JSON
- [`./ROLES.md`](./ROLES.md) — 角色清单
- [`./README.md`](./README.md) — 流程总览
- [`./CHANGELOG.md`](./CHANGELOG.md) — 变更记录
- [`../../README.md#5-流程`](../../README.md) — FDEP 在 jeeFlow 工作规范中的位置
