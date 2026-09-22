# jeeFlow 工作规范（Working Charter）

> 本文档由协作者共同**逐步制定**，任何章节的增删改均需双方确认，并在文末「变更日志」留档。
> 当前版本（v1.4）已落：§1 读写边界规则、§4 角色分工、§5 流程、§9 SOP 索引（4 个 SOP）、§10 流程定义组织规范（v1.3 加强：文件名小写强制）；附 ToT/mapping.md（v1.1）、ToT/sop/（spi-verify v0.2 + tdd-flow v0.1 + flow-folder v0.1 + flow-lint v0.1 + auto-deploy-fdep v0.1）、ToT/flows/fdep.json（v0.6.2）+ ToT/flows/fdep/（4 文件示范）、ToT/tdd/（含 INDEX.md + 多份测试日志）；其余章节为占位，待逐章确认后填充。

---

## 0. 制定方式（Meta-Process）

- **节奏**：一次只起草一个章节，提交后由你确认；确认通过再进入下一节。
- **依据**：禁止自由发挥；缺失信息必须显式提问，不替用户做决定。
- **版本**：每次确认后升一版（如 v0.1 → v0.2），并在「变更日志」记录。

---

## 1. 读写边界规则（Read/Write Boundary Rules）

| # | 规则 | 状态 |
|---|------|------|
| 1 | 所有协作产出（文档、代码、笔记、配置等）一律写入 `./ToT/` 目录及其子目录 | ✅ 已确认 |
| 2 | 除有确实的正当事由外，**不得**对 `./ToT/` 以外的任何路径进行新建、修改、删除 | ✅ 已确认 |
| 3 | 正当事由（如修复 CI、修正上游缺陷）需在「变更日志」留档：原因 / 时间 / 影响范围 | ✅ 已确认 |
| 4 | （待补充） | ⏳ 占位 |

---

## 2. ToT 目录结构与命名约定

⏳ 占位 — 待你确认目录骨架与命名规则后起草。

---

## 3. 产出物分类标准

⏳ 占位 — 待你确认分类维度（如 wip / review / final）后起草。

---

## 4. 角色分工（Role Division）

> 角色 = 流程职能主体；类型可能是人类、AI Agent 或"作为人类助理的 AI"。
> 每条职责只写**边界**（做什么 / 不做什么），不写具体操作步骤（操作步骤归第 2、3、5、6、7 节）。

### 4.1 角色清单（v0.3 已校对）

| # | 角色 | 类型 | 核心职责 | 不做什么 | 移交对象 | 准入 / 退出 | 权限边界 |
|---|------|------|----------|----------|----------|--------------|----------|
| R1a | 流程参与者 | 人类 / AI Agent / 人类助理 AI | 执行既有流程；提交产出物供评审；提供反馈 | 不修改规范；不裁决需求；不擅自改动 ToT/ 外文件 | R2、R5、R6 | 任何协作者默认拥有；可被收回 | 写入 ToT/ 执行位；只读本规范其他章节 |
| R1b | 流程制定者 | 人类（主导） | 修改本规范、增删角色、调整流程骨架 | 不写实现代码；不替代 R3 做需求裁决 | 所有 R1a–R7 | 由组织授权；可被收回 | 写入 ToT/README.md；变更日志必填 |
| R2 | 流程引擎开发者 Agent | AI Agent | 功能实现、Fix Bug、功能改进 | 不做需求裁决；不擅自变更 ToT/ 外文件 | R3（PM）、R6（评审） | 经 R3 立项后方可启动；停用由 R3 触发 | ToT/ 内源码；变更日志必填 |
| R3 | 产品经理 PM | 人类（主导） + AI 助理 | 收集用户反馈、生成 RML 文档、追踪 Issue 进度 | 不直接合并代码；不裁定技术方案 | R2、R4、R5、R6 | 长期存在角色 | ToT/ 内 PRD/RML；只读历史变更日志 |
| R4 | 系统管理员 | 人类 | 顶端审视：系统统计数据、运行健康度、合规风险 | 不参与具体功能实现；不修改业务逻辑 | R3、R5 | 由组织授权 | 只读 ToT/ + 监控指标 |
| R5 | 知识管理员 | 人类 + 知识 Agent | 为每类用户群体 / AI 提供完备的知识库服务；统一负责知识技能的**入库、索引、更新**；围绕 Task 沉淀有用知识，杜绝沉睡文档 | 不沉淀无 Task 关联的孤立文档；不替其他角色下结论 | R1–R4、R6 | 长期存在角色 | ToT/ 内知识库；外部 KB 只读 |
| R6 | 评审 Agent | AI Agent | 评审代码 / 文档 / 产出物一致性 | 不做需求裁决；不写实现代码 | R2、R3、R5 | 由 R1b 启用；可停用 | ToT/ 内只读；产出评审记录入 ToT/reviews/ |
| R7 | 架构 / 设计 Agent | AI Agent | 架构设计、接口设计、文档起草 | 不写最终实现代码；不擅自变更既有架构 | R2、R3、R6 | 由 R1b 启用；可停用 | ToT/ 内 design/ 子目录 |
| R8 | （开放位） | — | 待补充 | — | — | — | — |

### 4.2 通用规则

- **角色不是身份**：同一人类或同一 AI 可在不同任务中切换角色，但需在 ToT/ 的产出物中显式标注当前角色（R1a / R1b / R2–R7）。
- **移交必须留档**：角色之间的产出物交接必须在变更日志或对应 review 记录中可追溯。
- **权限边界是硬约束**：违反权限边界 = 视为违反本规范第 1 节，需走例外审批流程。
- **R1b 与 R1a 不可同任务叠加**：同一 Task 中禁止一人同时充当 R1a（执行）与 R1b（规则制定者），以防自审自批。

---

## 5. 流程（Process）

> 流程是 jeeFlow 协作的**核心骨架**，采用 jeeFlow 自有 Snaker 格式定义。
> 本节是**人类可读镜像**；机器可执行版本以 `ToT/flows/fdep.json` 为准，两边不同步时以 JSON 为准。

### 5.1 主干流程（6 个阶段 + 驳回分支 + decision 分流，v0.6.2）

| # | 阶段 | SPI 角色（执行人） | 抽象 R 角色 | 产出物 | 存放 | 出口条件 |
|---|------|-------------------|-------------|--------|------|----------|
| **0** | **PM 接收窗口（登记）** | **`fdep_intake`** → u_fdp_pm | **R3** | 原始请求登记记录 | `ToT/pm/intake/` | 登记完成 + 决定（submitType=1 立项 / submitType=2 驳回） |
| - | **接收决策** | `decision_intake` (snaker:decision) | — | — | — | submitType 路由：1→stage_pm, 2→end_rejected, 默认→stage_pm |
| 1 | RML 立项 | **`fdep_rml`** → u_fdp_pm | **R3** | RML 文档 | `ToT/pm/rml/` | RML 通过 R3 自审并指派下一阶段 |
| 2 | 架构 / 接口设计 | **`fdep_arch`** → u_fdp_pm | **R7** | 架构文档 + 接口设计 + Mock 数据 | `ToT/design/` | 接口编号连续、Mock 数据覆盖正常/异常场景 |
| 3 | 开发实现 | **`fdep_dev`** → u_fdp_pm | **R2** | 源代码 + 单元测试 | `ToT/src/` + `ToT/tdd/` | 通过 R6 自动评审 + 自测通过 |
| 4 | 评审 / 验收 / 发布 | **`fdep_review`** → u_fdp_pm | **R6**（R3 验收） | 评审记录 + 发布说明 | `ToT/reviews/` | 评审通过 + 验收 |
| 5 | 反馈 / 知识沉淀 | **`fdep_kb`** → u_fdp_pm | **R5**（R3 反馈） | Issue 追踪 + 知识库条目 | `ToT/issues/` + `ToT/kb/` | 每条反馈关联到 Task 或 Issue；无孤立文档 |
| 驳回 | 接收驳回 | — | R3 | 驳回记录 | `ToT/pm/intake/rejected/` | 记录入库即闭环 |

> **关键原则**：
> 1. start **不等于** R3。start 接受**任何来源**（人类 / AI Agent / 外部用户），R3 是后续**接收窗口**，决定立项或驳回。
> 2. v0.6.2 起 `assignee` 字段使用 SPI 可解析的角色名（`fdep_intake` / `fdep_rml` 等），占位场景下由 `u_fdp_pm` 担当全部 6 阶段；多人分工场景需在 v0.7+ 引入 `assignmentHandler` 自动解析。
> 3. 抽象 R 角色（§4）保留为人类可读的语义层，SPI 角色为机器可执行层，映射见 `ToT/mapping.md`。

### 5.2 流程流转图（v0.6.2）

```
任何来源提出 (start, 无角色限制)
   │
   ▼
[0. 接收/登记 fdep_intake → u_fdp_pm]
   │
   ▼
[decision_intake] ──── submitType==2 ────▶ [驳回闭环 end_rejected] (ToT/pm/intake/rejected/)
   │
   │ submitType==1 (AGREE) 或默认 (兜底)
   ▼
[1. RML 立项 fdep_rml → u_fdp_pm] ──▶ [2. 架构/接口 fdep_arch → u_fdp_pm]
                                                   │
                                                   ▼
                                         [3. 开发实现 fdep_dev → u_fdp_pm]
                                                   │
                                                   ▼
                                       [4. 评审/验收 fdep_review → u_fdp_pm]
                                                   │
                                                   ▼
                                       [5. 反馈/沉淀 fdep_kb → u_fdp_pm] ──▶ end
```

### 5.3 待澄清（v0.7+ 候选改进）

- **Q2**：`stage_review` 是否要拆为 fork-join（并行 R6 自动评审 + R3 人工验收）？
- **Q3**：`stage_feedback` 之后是否要回环到 `stage_pm`，形成持续改进环？
- **Q4**：R1b 规则变更如何挂入流程？是横切旁路、还是独立节点？
- **Q5**：其他阶段驳回如何扩展？当前仅 decision_intake 有驳回路径
- **Q6**：stage_intake 与 stage_pm 同为 R3，是否需要拆 R3a/R3b 以避免自审自批？
- **Q7**：驳回后能否被重新激活（resurrect）？当前 `end_rejected` 是终止态
- **Q8**：v0.7+ 引入 `assignmentHandler` 让 SPI 角色 → 多用户自动解析（替换占位 u_fdp_pm）

### 5.4 流程与本规范其他章节的关系

| 关联章节 | 关系 |
|----------|------|
| §1 读写边界规则 | 所有流程产出物必须落在 `ToT/` 内 |
| §4 角色分工 | 阶段 `assignee` 引用 R1a–R7 角色编码 |
| §3 产出物分类 | 每阶段产出物需标注状态（wip / review / final）— §3 定稿后启用 |
| §6 知识管理 | 第 5 阶段产出物由 R5 入库，需遵循 §6 规则 |

---

## 6. 知识管理

⏳ 占位 — 待你确认知识库组织方式后起草。

---

## 7. API 工具的使用

⏳ 占位 — 待你确认 API 工具清单与调用规范后起草。

---

## 9. SOP 索引

> 所有 SOP 文档位于 `ToT/sop/`，配套可执行脚本同目录存放。

| SOP | 脚本 | 何时跑 | 必跑场景 |
|-----|------|--------|----------|
| [spi-verify.md](./sop/spi-verify.md) | `spi-verify.py` | 修改 `spi/<folder>/jsons/*.json` 后 | 新增/删除/调动部门/用户/角色 |
| [tdd-flow.md](./sop/tdd-flow.md) | `tdd-flow.py` | 修改 `ToT/flows/*.json` 后 | 新增/修改流程定义 |
| [flow-folder.md](./sop/flow-folder.md) | `flow-lint.py` | 流程定义组织合规检查 | 新增流程 / 文件夹结构变更 |
| [auto-deploy-fdep.md](./sop/auto-deploy-fdep.md) | （内嵌 main_common） | 引擎启动后 | fdep.json 自动部署（memory/PG 双端） |

**双轨调用顺序**：
```bash
# 数据变更
SPI_FOLDER=dev python3 ToT/sop/spi-verify.py

# 流程变更
python3 ToT/sop/flow-lint.py ToT/flows/<name>.json
python3 ToT/sop/tdd-flow.py ToT/flows/<name>.json

# 引擎启动自动验证
# 已嵌入 main.py / main_pg.py，无需手动触发
# 验证方式：查看启动日志 [auto-deploy-fdep] ... 行
```

---

## 10. 流程定义组织规范（Flow Folder Spec）

> 🔒 **永久规则** —— 所有流程 JSON 必须按本节组织，操作细节见 `ToT/sop/flow-folder.md`。

### 10.1 强制约束

| # | 规则 | 验证 |
|---|------|------|
| 1 | 流程 JSON 必须放在 `ToT/flows/<name>.json` | `flow-lint.py` 检查路径 |
| 2 | 文件名必须**全小写**（不允许 `FDEP.json` 这种混合大小写） | `flow-lint.py` 检查 `stem == stem.lower()` |
| 3 | JSON 顶层 `name` 字段必须 **== 文件名去掉 `.json` 后**（即全小写一致） | `flow-lint.py` 比对 |
| 4 | 同名文件夹 `ToT/flows/<name>/` 必须存在（小写，与文件名一致） | `flow-lint.py` 检查目录 |
| 5 | 同名文件夹内必须含 4 个文件：`README.md` `ROLES.md` `NODES.md` `CHANGELOG.md` | `flow-lint.py` 检查文件 |
| 6 | `NODES.md` 必须包含 JSON 中所有 `node.id` 的工作说明 | `flow-lint.py` 比对 ID 集合 |
| 7 | `ROLES.md` 必须包含 JSON 中所有非空 `properties.assignee` 的角色清单 | `flow-lint.py` 比对 |

> 🔒 **永久约束**：所有流程文件/文件夹名**全小写**。例：`fdep.json` + `fdep/`。不允许 `FDEP.json`、`FDep.json` 等混合大小写。

### 10.2 标准目录结构（以 fdep.json 为例）

```
ToT/flows/
├── fdep.json               # 流程定义（顶层 name 字段必须 == "fdep"）
└── fdep/                   # 同名文件夹（全小写）
    ├── README.md           # 流程总览：用途 / 节点清单 / 角色清单 / 变更索引
    ├── ROLES.md            # 角色清单：抽象 R → SPI 角色 → 实际用户
    ├── NODES.md            # 节点工作手册：每节点一节，含说明/输入/输出/步骤/注意事项
    └── CHANGELOG.md        # 变更记录：版本/日期/改动/测试结果
```

### 10.3 工作流

| 动作 | 步骤 |
|------|------|
| **新增流程** | 创建 JSON → `mkdir <NAME>` → 创建 4 文件 → `flow-lint.py` → `tdd-flow.py` |
| **修改流程** | 改 JSON → 同步 `<NAME>/NODES.md`/`ROLES.md`/`CHANGELOG.md` → 双 SOP 验证 |
| **删除流程** | 删除 JSON + 同名文件夹 + 在本 README §8 变更日志留档 |

### 10.4 当前已立流程

| 流程 | JSON | 文件夹 | 状态 |
|------|------|--------|------|
| fdep | `ToT/flows/fdep.json` | `ToT/flows/fdep/` | ✅ v0.6.2（演示） |

---

## 8. 变更日志（Change Log）

| 版本 | 日期 | 变更内容 | 确认人 |
|------|------|----------|--------|
| v0.1 | 2026-09-22 | 初始化骨架；落第 1 节「读写边界规则」前 3 条 | 待确认 |
| v0.2 | 2026-09-22 | 新增第 4 节「角色分工」：R1–R7 角色骨架 + R8 开放位；新增 4.2 通用规则 | 待确认 |
| v0.3 | 2026-09-22 | 第 4 节定稿：R1 拆为 R1a 参与者 / R1b 制定者；R2 调整为"仅 Agent"；R6/R7 启用权由 R1a 改为 R1b；新增 4.2 第四条（R1a/R1b 互斥） | 待确认 |
| v0.4 | 2026-09-22 | 新增第 5 节「流程」：5 阶段线性骨架；新增 `ToT/flows/fdep.json`（Snaker 格式机器版）；原第 5/6/7 节顺延为第 6/7/8 节；变更日志本身由 §7 顺延为 §8 | 待确认 |
| v0.5 | 2026-09-22 | §5 流程修订：采纳反馈"PM ≠ start，提出者任何人，PM 是接收窗口"；新增 Stage 0 接收窗口（R3）、新增驳回路径（`end_rejected`）、Stage 1 改为纯 RML 立项；FDEP.json 同步升级为 v0.5；openQuestions Q1 已解决，新增 Q6/Q7 | 待确认 |
| v0.6 | 2026-09-22 | 新增 `ToT/mapping.md`：FDEP 节点 → 抽象 R 角色 → SPI 角色 → 占位用户（`u_fdp_pm`）三层映射提案；spi/dev 扩展方案（D05 FDEP协作组 + 占位用户）；6 个待决 Q；尚未实际修改 spi/dev 数据 | 待确认 |
| v0.7 | 2026-09-22 | **例外审批落地**：用户授权修改 spi/dev 三个 JSON 文件（依据 §1 第 2 条正当事由：FDEP 流程需要可执行的占位用户；依据第 3 条留档：本条）。① `spi/dev/jsons/USERS.json`：新增 `u_fdp_pm`（占位·待分配），用户数 13→14；② `spi/dev/jsons/DEPTS.json`：新增 `D05 FDEP协作组`，部门数 5→6；③ `spi/dev/jsons/ROLE_TO_USERS.json`：新增 6 个 FDEP 节点角色（fdep_intake/rml/arch/dev/review/kb），角色数 8→14。三个 JSON 校验通过。`ToT/mapping.md` 同步升 v0.8 修正命名一致性问题。 | 待确认 |
| v0.8 | 2026-09-22 | **永久规则录入**（用户口头授权）：FDEP 部门 ID 固定为 `DFDEP`、parent_id=null、main_leader 与 leader 一致；与 D99 总经办同级为"双顶层根"结构。spi/dev 三个 JSON 同步迁移：`USERS.json` 中 `u_fdp_pm.deptId` 由 `D05` 改为 `DFDEP`；`DEPTS.json` 中 `D05` 改名为 `DFDEP`、parent_id 改 null、main_leader 改 `u_fdp_pm`，版本 v1.2.0→v1.3.0 并更新 encoding 描述为"tree with parallel roots"；`ROLE_TO_USERS.json` 不变。`ToT/mapping.md` 升 v0.9，§3.0 新增永久约束条。 | 待确认 |
| v0.9 | 2026-09-22 | **新增 SPI 调整 SOP**：`ToT/sop/spi-verify.md`（v0.2）+ `ToT/sop/spi-verify.py`（可执行脚本）。脚本封装了 spi/dev 内置 `verify()` + FDEP 16 条不变量回归点；首次回放发现 ROLES.json 漏登记 6 个 fdep_* 角色（spi 跨表引用 C1 失败），已修复为 v1.1.0；负向测试通过（DFDEP→D05 改名立刻被抓，exit=1；恢复后 exit=0）。 | 待确认 |
| v1.0 | 2026-09-22 | **FDEP.json v0.5 TDD 实跑发现 P0 × 2**：(1) W012 BUG-1 §110 重现 —— stage_intake 双出边触发 instance.state=20 但下游 task 仍 DOING；(2) 角色解析断裂 —— actors=['R3'] 抽象角色未映射到 u_fdp_pm，导致后续 task 无人可拾起。已写入 `ToT/tdd/test_FDEP_20260922081228.md`。**FDEP.json 升 v0.6.2 修复**：(a) 在 stage_intake 后插入 snaker:decision 节点（decision_intake）用 submitType 分流 approve/reject/默认；(b) 6 个 task 的 assignee 从抽象 R 角色改为直接 `u_fdp_pm`（占位场景），SPI 角色名（fdep_intake/fdep_rml/...）保留为语义标签；(c) 加 default edge 处理 W013。**实跑验证 happy path 全程 6 阶段 DONE**，state=20；reject path 需手动 orchestration（stage_intake 时主动 submitType=2）。§5 镜像同步：负责人列加 "SPI 角色→u_fdp_pm" 双层标记，新增 Q8（v0.7+ 引入 assignmentHandler）。 | 待确认 |
| v1.1 | 2026-09-22 | **新增流程 TDD SOP**：`ToT/sop/tdd-flow.md`（v0.1）+ `ToT/sop/tdd-flow.py`（可执行脚本）。脚本封装：① `validate_flow.py` 静态校验 ② `vendor/jeeflow/verify_flow` 引擎校验 ③ 部署 + happy/reject 实跑 ④ 自动留档 `.md` 摘要 + `.json` 原始数据到 `ToT/tdd/`。CLI 参数：`<flow.json>` 必填 + `--spi` + `--operator` + `--no-reject`/`--max-steps`。`ToT/tdd/INDEX.md` 记录日志命名约定与基线（v0.6.2 = test_FDEP_20260922082028）。**SPI 与 TDD SOP 形成完整组织+流程双轨回归**：先 `spi-verify.py` 验数据，再 `tdd-flow.py` 验流程。 | 待确认 |
| v1.2 | 2026-09-22 | **新增流程定义组织规范**：① §10 永久规则（6 条强制约束）+ §9 SOP 索引；② `ToT/sop/flow-folder.md` SOP（v0.1）+ 4 文件模板（README/ROLES/NODES/CHANGELOG）；③ FDEP 示范：`ToT/flows/fdep/` 文件夹创建 + 4 文件填充；④ `ToT/sop/flow-lint.py` 自动校验脚本（验证 name 与文件名一致 / 同名文件夹存在 / 4 文件齐全 / 节点 ID 覆盖 / 角色覆盖）。所有新增流程必须按 §10 组织。 | 待确认 |
| v1.3 | 2026-09-22 | **文件名全小写永久规则**（用户口头授权，立即执行）：FDEP.json → fdep.json；FDEP/ 文件夹 → fdep/。§10 新增约束：文件名必须 `stem == stem.lower()`；`flow-lint.py` 升级加检查。全 ToT 文档同步引用（mapping.md / 4 SOP / README §10 / fdep/ 内 4 文件）。**保留不变的标识**：`DFDEP`（SPI 部门 ID，由更早规则锁定）/ `FDEP协作组`（部门 displayName）/ `fdep_*`（SPI 角色代码）/ `u_fdp_pm`（占位用户）/ `test_FDEP_*`（历史测试日志文件名，作为档案保留）。 | 待确认 |
| v1.4 | 2026-09-22 | **新增临时任务**：main_common.py 加 `auto_deploy_fdep(facade)` + `run_auto_deploy_fdep(facade)`；main.py (memory 8101) 与 main_pg.py (PG 8102) 双端接入；启动后自动检查 ToT/flows/fdep.json 存在性 + 引擎是否已有 fdep 定义，满足条件则部署。**双测验证**：memory 2/2 deploy（预期行为，每次重启清空）；PG 1 deploy + 1 skip（修正 getLastByName 参数名 bug 后）。**新增 SOP** `ToT/sop/auto-deploy-fdep.md` 记录验证矩阵与错误处置。 | 待确认 |
