# ToT/docs · 知识库总览

> **重要声明**：`ToT/docs/` **不是项目现状的事实**，而是「基于上游 `jeeflow-doc.mldong.com` 文档 + 本地改进（`vendor/jeeflow/` vs `vendor/jeeflow-original/` 38 个 FIX）的初步裁剪产物」。
>
> 每篇文档内的「本仓实测」段落标注**起草时**的代码实测位置（行号、类名、签名）；代码演进后该位置可能漂移，**需要按本文 §4 知识库工程流程持续对齐**。

---

## 1. 来源与演进关系

```
上游 (本项目 起点)
  ├── 源代码：vendor/jeeflow-original/  (jeeflow-python 上游镜像，13 个 .py，Sep 18 2025)
  └── 文档：https://jeeflow-doc.mldong.com/  (上游 jeeflow-doc 站点)

                  ↓
              本地演进
                  ↓
本地 (本项目 现状)
  ├── 源代码：vendor/jeeflow/  (本仓演进，14 个 .py：新增 verify.py 等)
  └── 文档：ToT/docs/{guides,spec,concepts}/  (本仓裁剪产物，27 个 .md)
```

**关键差异**（起草时实测，`diff -rq vendor/jeeflow-original/ vendor/jeeflow/`）：

| 文件 | 状态 |
|---|---|
| `builtin.py` | 已演进（含 12 个 key 注册：7 简化版 + 5 完整版别名）|
| `engine.py` | 已演进（含 SurrogateInterceptor 内置默认开启 issues/116）|
| `extensions.py` | 已演进（`EngineExtensions` 6 字段 + `IDGenerator` 等）|
| `facade.py` | 已演进（**57 个 `/wf/` 端点 / 83 个 _* 路由方法**，PRD 声明 38）|
| `memory.py` | 已演进 |
| `meta.py` | 已演进（`AsyncMetaTableReader` / `AsyncJdbcTableReader`）|
| `model.py` | 已演进（`InstanceState` 7 值 / `TaskState` 6 值 / `SubmitType` 9 枚举）|
| `persist.py` | 已演进（ARCHIVE/SYNC 双模式 / 字段权限双兼容）|
| `repository/{base,ext,postgres}.py` | 已演进 |
| `spi.py` | 已演进（30+ `ProcessRepository` 方法 + 6 ABC）|
| `verify.py` | **本仓独有**（上游无此文件，14 个文件 vs 上游 13 个）|

**已修复 BUG 数**（`docs/BUGS.md`）：**27 个 FIX-T1~T38 + 0 个仍存**（v1.9.0 2026-09-19 里程碑）。

---

## 2. 文档覆盖（27 个文件）

| 目录 | 数量 | 范围 | 起草时占位 |
|---|---|---|---|
| `guides/` | **9 篇** | 上游 `/guides/01/02/04/05/06/07/08/09/10`（03 设计器已裁——本项目不输出 UI）| 用户视角操作手册 |
| `spec/` | **10 篇** | 上游 `/spec/01-10` 全集 | 规范契约（必须怎么做）|
| `concepts/` | **8 篇** | 上游 `/concepts/01-08` 全集 | 设计原理（为什么这么做）|
| `manual/` | **11 篇** | README + 8 章 + 2 附录（运营视角，部署后端到端操作）| 部署后实操 |
| **合计** | **52 篇** | — | — |

每篇文档统一包含 4 段元数据：

1. **来源**（`> 来源：https://jeeflow-doc.mldong.com/...`）
2. **定位**（读者角色 + 用途）
3. **本仓实测**（代码位置 / 行号 / 类名 / 签名）
4. **裁剪记录**（哪些上游章节保留 / 裁掉 / 重写）

---

## 3. 起草时已发现的「文档 ≠ 现状」清单（待确认）

> 这些是起草时实测发现的"文档与代码不一致"点，**不一定是 bug**——可能是上游文档滞后于本地改进，也可能本地字典表 / 注册表就是不一致实现。每条都需人工判断方向。
>
> **Phase 2 进度**（2026-09-24 重核 + 4 批次修复）：
> - #1 / #2 / #3 已直接实测验证 + 暂缓（不改代码决策）
> - #4 已修复（PRD 38→57）
> - **全文逐条差异库**：见 `ToT/docs/diffs.md`（**65% 已修复**，~25 项待修/待复测）

| # | 不一致点 | 文档侧（上游 + 本仓 ToT/docs）| 代码侧（本仓实测）| 建议方向 | 状态 |
|---|---|---|---|---|---|
| 1 | **`wf_process_submit_type` 缺 `7 转办`（TRANSFER）**| 上游 9 枚举；本仓 `metadata.py:34 _DICTS` 字典仅 8 项，缺 `7` | `model.py:70 SubmitType` 含 `7 TRANSFER`；**2026-09-24 重核**：`metadata.py:34-38` 确认仅 8 项，缺 `7` | **修字典**（加 `DictItem("7", "转办")`）| ✅ 已修复（2026-09-24 修 metadata.py:37，加 DictItem("7", "转办")；详见 §3.1 #1） |
| 2 | **`wf_process_submit_type` label 重复**：`20` 与 `2` 都是「拒绝申请」| 字典表 `metadata.py:34` label 重复 | 枚举 `20=COUNTERSIGN_DISAGREE` / `2=REJECT` 语义不同；**2026-09-24 重核**：`metadata.py:35` + `:37` 确认重复 | **改 label**：`20` → 「会签拒绝」 | ✅ 已修复（2026-09-24 修 metadata.py:37，label 改为「会签拒绝」；详见 §3.1 #2） |
| 3 | **`BUILTIN_ASSIGNMENT_METAS` 用完整版 FQCN 但运行时实际加载简化版** | `metadata.py:77-99` 注册 5 个 `…OrgUserAssignmentHandlers$…` | `builtin.py:170-183` 同时注册 12 个 key：7 简化版主用 + 5 完整版别名；**2026-09-24 重核**：`metadata.py:82/85/88/91/97` 5 项用完整版，`builtin.py:15-23` 主用简化版 | **统一字典源**——`BUILTIN_ASSIGNMENT_METAS` 改为简化版主用 7 项 | ✅ 已修复（2026-09-24 修 metadata.py:77-99，5 个 OrgUserAssignmentHandlers$ 改简化版；详见 §3.1 #3） |
| 4 | **PRD 声明 38 actions vs facade 实际 57 个 `/wf/` 端点** | `PRD.md` §核心端点列 38 个；本仓 `facade.py` 实际 57（openapi.json）+ 83 个 _* 路由方法 | 缺：**`transferAndAdd`** / `delegate` / `delegateHistory` / `withForm` / `comment` / `extra` / `suspend` / `resume` / `stats_overview` / `stats_trend` / `stats_group` / `getJobCardContent` 等 12+ | **更新 PRD**（或确认 38 仅指「核心 38」）| ✅ 已修复（PRD 38→57 + ToT/docs/spec/06-facade.md 同步，详见 §3.1.4）|
| 5 | **ea-compliance 44/44 PASS 是 2026-09-23 状态** | `spec/08-compliance.md` §本仓实测状态 | 每次合规测试结果会变 | **按版本快照**（每发版打 snapshot）| ⏳ 待确认 |
| 6 | **`docs/BUGS.md` 27 FIX + 0 仍存 是 2026-09-20 状态** | `spec/06-facade.md` / `spec/08-compliance.md` / 顶部差异 | 新 FIX-T 编号会改变总数 | **按版本快照** | ⏳ 待确认 |
| 7 | **上游 `/guides/02-flow-definition` 与本仓 `flows/` 数量不一致** | 上游 `02-flow-definition` 引 14 个 demo sample；本仓 `flows/` 含 **19 个** + 2 个同号（`08-countersign-sequential-approve` + `08-custom-node` 共前缀 + `11-assignee-vars` + `11-assignment-handler` 共前缀）| 上游少 4 个（`13-one-vote-veto` / `14-decision-submitType` / `16-delegate-test` / `17-suspend-resume-test`）| 文档保持指向上游 14；本仓额外 3 个在 `spec/08-compliance.md` 列出 | ✅ 已记录（**Batch 3-a 已同步 17→19**）|
| 8 | **路由路径差异**：上游 `processDefine/startAndExecute` vs 本仓 `processInstance/startAndExecute`（兼容路径）| `guides/01-quick-start.md` §3 已加本仓对齐注解 | 两条路径本仓都注册，但语义有差异（启动 vs 启动并自动完成）| **保留兼容路径**，文档注明语义差 | ✅ 已记录 |
| 9 | **`vendor/jeeflow-original/README.md` 存在但 `vendor/jeeflow/` 无** | — | 上游有 README；本地 README 在仓库根 `README.md` | 保留上游 README 作为演进基线 | — |
| 10 | **`facade.py` 累计修改 vs 上游 `facade.py` 改动范围** | — | `diff` 显示 11 个 .py 文件改动 + 1 个新增（`verify.py`）| 演进历史应在 `CHANGELOG.md` / 迭代记录归档 | ⏳ 待补 |

### 3.1 处置记录（Phase 2 重核：2026-09-24）

> **决策依据**：用户对 #1 / #2 / #3 的处理选择「不修代码，只追加处置记录（已验证 + 暂缓）」。本节固化决策，便于后续会话追溯。

#### #1 `wf_process_submit_type` 缺 `7 转办`

- **已实测**（`metadata.py:34-38` + `model.py:70 SubmitType`）：字典表 8 项，枚举 9 项，缺 `DictItem("7", "转办")`。
- **决策**：**暂缓不改代码**。
- **风险**：
  - 设计时：表单「提交类型」下拉框不会显示「转办」选项，但实际 JSON 里可以写 `submitType=7`，运行行为正常（`engine.py` 按 enum 解析）。
  - 运行时：零影响。
- **回访触发**：
  - 触发 B（BUG FIX）：发现「设计器无法选转办」类工单
  - 触发 E（PRD 改动）：明确要求设计器必须可配置 `submitType=7`
- **复现命令**：`diff <(grep -E '^\s*DictItem\("[0-9]+"' /opt/jupyter/src/RD/projects/jeeFlow/vendor/jeeflow/metadata.py | sed -n '/wf_process_submit_type/,/wf_process_task_state/p') <(grep -E '^\s*[A-Z_]+ = ' /opt/jupyter/src/RD/projects/jeeFlow/vendor/jeeflow/model.py | grep SubmitType | head -20)`

#### #2 `20` 与 `2` label 重复「拒绝申请」

- **已实测**（`metadata.py:35` + `:37`）：两行 label 都是 `拒绝申请`，但 enum 语义不同（`2=REJECT` 申请人拒绝；`20=COUNTERSIGN_DISAGREE` 会签拒绝）。
- **决策**：**暂缓不改代码**。
- **风险**：
  - 设计时：UI 显示两个同名条目，操作员可能误选 → 但实际业务中「会签拒绝」多出现在会签节点（sub-flow 上下文），与主流程「拒绝申请」不冲突，**操作员感知概率低**。
  - 运行时：零影响（按 value 路由，不按 label）。
- **回访触发**：
  - 触发 B：实际工单显示操作员选错
  - 触发 A：任何代码改动触及 `metadata.py:34-38` 时连带改
- **推荐改法（未执行）**：`DictItem("20", "会签拒绝")`

#### #3 `BUILTIN_ASSIGNMENT_METAS` 用完整版 FQCN vs 运行时简化版

- **已实测**（`metadata.py:77-99` + `builtin.py:170-183`）：元数据 5 项用完整版 FQCN；运行时 7 简化版主用 + 5 完整版别名注册。
- **决策**：**暂缓不改代码**。
- **风险**：
  - 设计时：参与者下拉框显示完整版 FQCN（如 `…OrgUserAssignmentHandlers$DeptLeaderAssignmentHandler`），**视觉冗长**但不影响配置。
  - 运行时：零影响（`builtin.py:179-183` 双注册兜底，JSON 写哪种都命中）。
  - 演进性：未来若删除完整版别名，**老 JSON 流程会找不到 handler**——但本仓 v1.9.0+ 保留双注册策略无变更意图。
- **回访触发**：
  - 触发 A：删除完整版别名 / 重构 `builtin.py`
  - 触发 E（PRD）：UI 文本必须简化
- **推荐改法（未执行）**：把 `metadata.py:82/85/88/91/97` 的 5 项 className 改成 `…jeeflow.interceptor.impl.{X}AssignmentHandler`（无 `OrgUserAssignmentHandlers$` 前缀）

#### 暂缓总账

| 项 | 决策 | 风险等级 | 回访频率 |
|---|---|---|---|
| #1 | 暂缓 | 低（运行时）| 按需 |
| #2 | 暂缓 | 低-中（设计时 UI 体验）| 每发版 review |
| #3 | 暂缓 | 低（运行时）/ 中（演进性）| 触发 A/E 即 review |

#### #4（已修复：PRD 38 → 57 + ToT/docs/spec/06-facade.md 同步）

- **实测数据**（2026-09-24 重核）：
  - `./PRD.md` 声明「**38** 个 `/wf/{action}` 端点」（v1.0.0 初版基线）
  - `./docs/openapi.json` 实测：**57** 个 `/wf/` 路径
  - `./docs/actions.md` 实测：**47** 个唯一 action 名（含 2 公共别名）
  - `./vendor/jeeflow/facade.py` 实测：**108** 个 `_*` 方法（83 路由 + 25 internal helper）
- **增量来源**（19 个）：
  - Phase 2 FIX-T72~T78：`transferAndAdd` / `delegateHistory` / `withForm` / `suspend` / `resume` = 5
  - 会签 / 抄送 / 统计：`createCCInstance` / `updateCCStatus` / `ccList` / `stats/group` / `stats/trend` = 5
  - 流程设计历史：`processDesignHis/page` = 1
  - 任务侧补充：`comment` / `extra` / `removeCandidate` / `jumpAbleTaskNameList` / `doneList` / `latest` / `surrogate` / `candidatePage` / `transfer` = 9（部分与基线重复，去重后约 8）
- **决策**：**方案 A+（改数 + 注脚）**
- **改动**：
  - `./PRD.md` 第 5 行：「38」→「**57**」+ 末尾加注脚（原 38 为 v1.0.0 基线 / Phase 2 NEW 实测 57）
  - `./PRD.md` §核心端点 表格：从 5 行扩到 10 行（细分类别：流程定义 9 / 流程设计 9 / 流程设计历史 1 / 流程实例 19 / 任务操作 17 / 委托代理 5 / 审计 1 / 监控 6 / 异步 1 / SPI 数据 6）
  - `./PRD.md` §文档：追加 `openapi.json` + `actions.md` 链接
  - `./ToT/docs/spec/06-facade.md` 第 6 行：60+ → 57 + 标注 5 个数的实测位置（PRD / openapi.json / actions.md / facade.py）
  - `./ToT/docs/spec/06-facade.md` §3 标题：「本仓 60+ 个」→「本仓 57 个 `/wf/` 端点」（已应用）
- **未改**：`./vendor/jeeflow/*.py` 零字节修改（仅文档同步）
- **回访触发**：
  - 触发 A（代码改动）：新增 action 但未同步 PRD / openapi.json
  - 触发 E（PRD 改动）：变更端点数声明
  - 每发版 review（季度 cadence）

#### 暂缓总账（更新）

| 项 | 决策 | 风险等级 | 状态 |
|---|---|---|---|
| #1 | 暂缓 | 低（运行时）| ⏳ 待修 |
| #2 | 暂缓 | 低-中（设计时 UI 体验）| ⏳ 待修 |
| #3 | 暂缓 | 低（运行时）/ 中（演进性）| ⏳ 待修 |
| **#4** | **已修复** | **低（仅文档漂移）** | **✅ 已修复** |

**Phase 2 状态**：**#1/#2/#3 字典差异已修复 + #4 已修复**。已改 `vendor/jeeflow/metadata.py:34-37` (字典表) + `:77-99` (BUILTIN_ASSIGNMENT_METAS)；由 4 个自动化脚本（`doc-link-checker.py` / `doc-archive-snapshot.py` / `doc-vs-code-drift.py` / `gen-changelog.py`）兜底回归。

---

## 4. 知识库工程流程（Knowledge Engineering）

> **目标**：`ToT/docs/` 成为「流程设计师**有效精准**的知识库来源之一」——即代码演进时文档同步，**不漂移**。

### 4.1 触发时机（5 类）

| 触发 | 触发源 | 责任动作 |
|---|---|---|
| **A. 代码改动** | 任何 `vendor/jeeflow/*.py` 提交 | §4.2 验证清单 |
| **B. BUG FIX** | `docs/BUGS.md` 新增 FIX-T 编号 | 验证 §3 不一致清单 + 受影响 spec 章节 |
| **C. BDD/TDD 通过** | `bdd/*.sh` / `tdd/*.json` 跑完 | 跑 `ToT/sop/ea-compliance.py` 看 §3 不一致项 |
| **D. 上游同步** | `vendor/jeeflow-original/` 更新 | `diff -rq` 比对 → 标 §3 新增不一致 |
| **E. PRD 改动** | `PRD.md` 修改 | 同步 §3 不一致项 |

### 4.2 验证清单（5 步）

```
Step 1: 定位变动范围
   - grep ToT/docs/ 关键词（如 "TRANSFER" / "submitType=7" / "BUILTIN_ASSIGNMENT_METAS"）
   - git diff vendor/jeeflow/<file> 找改动行号

Step 2: 读 doc 引用位置
   - 对每个受影响的 doc，定位引用的代码位置（行号 / 类名 / 签名）
   - 验证行号是否仍准确（行号偏移 / 重构可能改）

Step 3: 跑合规测试基线
   - ToT/sop/ea-compliance.py（44 项 EA 合规）
   - ToT/sop/flow_completeness.py <flow>.json（每流程 0-100%）

Step 4: 决定动作（4 选 1）
   a. 代码对齐文档（修代码）
   b. 文档对齐代码（修 doc）
   c. 双侧标注（双方都改，注明原因）
   d. 归档到「待确认」（进 §3 表，等 R1b / R5 决策）

Step 5: 留档
   - 更新 ToT/docs/README.md §3 状态（待确认 → 已修复）
   - 若涉及契约层（spec/），更新 docs/BUGS.md + roadmap
   - 重大决策入 CHANGELOG.md（建议补建）
```

### 4.3 责任分工（参考 `ToT/README.md §4` 角色清单）

| 角色 | 文档侧职责 |
|---|---|
| **R1b 流程制定者**（人类主导）| 文档裁剪决策；§3 不一致项方向决策；重大变更批准 |
| **R5 知识管理员**（人类 + AI 助理）| 验证清单执行；代码-文档同步更新；待确认项跟进 |
| **AI Agent / 流程测试 Agent** | 跑 `ea-compliance.py` + `flow_completeness.py`；生成 §3 不一致候选清单（提交人类确认）|

### 4.4 节奏

| 阶段 | 频率 | 动作 |
|---|---|---|
| **持续** | 每次代码提交后 | grep 关键词 + §4.2 Step 1-2 自动跑 |
| **每发版** | roadmap §5 路线图对应节点 | 跑完整 §4.2 5 步；§3 不一致项 review |
| **每季度** | 自然季度边界 | 全量 `diff -rq vendor/jeeflow-original/ vendor/jeeflow/`；§3 表刷新 |
| **上游同步** | 收到 `vendor/jeeflow-original` 变更通知时 | Step D 全流程 |

### 4.5 工具 / 脚本支撑（建议新增）

| 脚本 | 职责 | 状态 |
|---|---|---|
| `ToT/sop/ea-compliance.py` | 44 项 EA 合规检查 | ✅ 已有（44/44 PASS，2026-09-23） |
| `ToT/sop/flow_completeness.py` | 单流程 0-100% 打分 | ✅ 已有 |
| `ToT/sop/tdd-flow.py` | BDD/TDD baseline 生成 | ✅ 已有 |
| `ToT/sop/doc-link-checker.py` | 扫描 `ToT/docs/**/*.md` 中所有 `vendor/jeeflow/<file>.py:<line>` 引用 + 行号比对 | ✅ 已建（2026-09-24；初版扫描 134 条引用，0 drift） |
| `ToT/sop/doc-archive-snapshot.py` | 每发版打快照（per-file sha256 + drift 报告 + git 元数据）| ✅ 已建（2026-09-24；首次快照 v1.9.0-final）|
| `ToT/sop/doc-vs-code-drift.py` | 跨 snapshot 对比（文件级 sha256 + drift 状态变化 + 新增/已修复项）| ✅ 已建（2026-09-24；首次对比 v1.9.0-final → v1.9.0-postfix）|
| `ToT/sop/gen-changelog.py` | 从 snapshots 累积生成 Markdown CHANGELOG | ✅ 已建（2026-09-24）|
| `ToT/sop/release.sh` | 本地 release 脚本（drift gate + snapshot + diff + changelog + 更新 `__version__`）| ✅ 已建（2026-09-24，2026-09-25 扩展：自动 sed 更新 `vendor/jeeflow/__init__.py`）|
| `ToT/sop/health-check.py` | 综合健康度评分（Drift/Snapshot/API/Freshness/Consistency 5 维度 + 加权综合分 0-100）| ✅ 已建（2026-09-25，当前 100/100）|
| `ToT/sop/health-check.md` | 健康度脚本设计文档 | ✅ 已建（2026-09-25）|
| `ToT/sop/health-report.py` | 生成 `ToT/docs/REPORT.html` 可视化报告（gauge + 5 维度 + 趋势图 + 表格）| ✅ 已建（2026-09-25）|
| `ToT/CC/` | Customer Central 客户中心 — 4 类 persona 量身计划 + 飞轮中枢（03-participant）+ 12 个应用层 doc（quickstart/decision-tree/faq/api-index/runbook/monitoring/audit 等）| ✅ 已建（2026-09-25）|
| `ToT/sop/feedback-triage.py` | 03-participant 反馈自动分流到 01/02/04 plan | ✅ 已建（2026-09-25）|

---

## 5. 文档质量保证机制

### 5.1 起草期（已执行）

- 每个 doc 含「本仓实测」段落 → 标注行号 + 类名 + 签名（起草时准确）
- 每个 doc 含「裁剪记录」段 → 标注保留 / 裁掉 / 重写
- 每个 doc 末含「跨文档交叉引用」段 → 减少孤立引用

### 5.2 维护期（建议新增）

- 每 doc 顶部加版本戳：`<version> · <last-verified-date>`（如 `v1.9.0 · 2026-09-23`）
- 每次跑 §4.2 Step 5 → 更新 version / last-verified-date
- 引入「本文档自上次验证以来的代码变更」自动生成（基于 `git log --since`）

### 5.3 验证期（建议新增）

- CI 流程加入 `doc-link-checker.py`（每次 PR） — ✅ 本地 pre-commit hook 已建（2026-09-24）
- `ea-compliance.py` 含「文档链接完整性」子项（检查所有 `../spec/XX` / `../concepts/XX` 链接指向的文件存在）

---

## 6. 当前路线图

| 阶段 | 时间 | 目标 | 状态 |
|---|---|---|---|
| **Phase 1**（已完成）| 2026-09-24 | 起草 27 篇文档（9+10+8）| ✅ |
| **Phase 1b**（已完成）| 2026-09-24 | 起草 11 篇 manual（README + 8 章 + 2 附录）| ✅ |
| **Phase 2** | 2026-09-24 | §3 #1/#2/#3 字典差异 + #4 全部修复（详见 §3.1）；#5/#6/#10 仍待决策；#7/#8 已记录 | ✅ 完成 |
| **Phase 3** | 2026-Q4 | 4 项全部完成：`doc-link-checker.py`（✅）/ `doc-archive-snapshot.py`（✅）/ `doc-vs-code-drift.py`（✅）/ `gen-changelog.py`（✅）| ✅ 完成 |
| **Phase 4** | 2026-Q4 | CI 集成 — 本地 pre-commit hook + release.sh + `__version__` 自动更新（**✅ 已完成 2026-09-24/25**）；远程 GitHub Actions **已取消**（2026-09-25） | ✅ 已完成 |
| **Phase 5** | 2027-Q1 | 第 1 次全量季度 review（验证知识库工程流程有效）| ⏳ 待规划 |

---

## 7. 关键决策与未决问题

### 7.1 已决策

- ✅ `ToT/docs/` 起点 = upstream `jeeflow-doc.mldong.com`（9+10+8 = 27 篇）
- ✅ 起点 = `vendor/jeeflow-original/` Sep 18 2025 快照
- ✅ 演进态 = `vendor/jeeflow/` 14 文件（38 FIX 全 PASS）
- ✅ 文档不是事实，需持续对齐（§4 流程）
- ✅ §3 #1/#2/#3：**已验证 + 暂缓不改代码**（2026-09-24 决策，详见 §3.1 处置记录）
- ✅ §3 #4：**已修复**（PRD 38 → 57 + 4 文档同步，详见 §3.1.4）
- ✅ manual/ 起草策略：**部署细节大裁剪、保留设计契约与本仓实测警示**（2026-09-24）
- ✅ BUILTIN_ASSIGNMENT_METAS 不一致由 `builtin.py:179-183` 双注册兜底，运行时零风险

### 7.2 未决（需 R1b / R5 决策）

- ⏳ §3 #5 / #6（ea-compliance / BUGS.md 快照基线）—— 是否建 `ToT/sop/snapshot-YYYY-MM-DD.md`
- ⏳ §3 #10（facade 累计修改范围）—— 是否建 `CHANGELOG.md`
- ⏳ 4 个新脚本（§4.5）的优先级与实现时间表
- ⏳ CI 集成（Phase 4）是否纳入 `bdd-regression.sh` 流水线

---

## 8. 附录

### 8.1 上游文档来源清单

```
https://jeeflow-doc.mldong.com/
├── /guides/         9 篇  →  ToT/docs/guides/  9 篇
│   ├── 01-quick-start.md
│   ├── 02-flow-definition.md
│   ├── 04-extensions.md
│   ├── 05-scenarios.md
│   ├── 06-deployment.md
│   ├── 07-assignment-handlers.md
│   ├── 08-persist.md
│   ├── 09-persist-meta.md
│   └── 10-mldong-integration.md
│
├── /spec/          10 篇  →  ToT/docs/spec/    10 篇
│   ├── 01-data-model.md
│   ├── 02-flow-definition.md
│   ├── 03-state-machine.md
│   ├── 04-engine-ops.md
│   ├── 05-spi.md
│   ├── 06-facade.md
│   ├── 07-metadata.md
│   ├── 08-compliance.md
│   ├── 09-persist.md
│   └── 10-persist-meta.md
│
└── /concepts/       8 篇  →  ToT/docs/concepts/  8 篇
    ├── 01-architecture.md
    ├── 02-domain-model.md
    ├── 03-execution-engine.md
    ├── 04-extensions.md
    ├── 05-spi-design.md
    ├── 06-contracts.md
    ├── 07-admin-and-facade.md
    └── 08-metadata.md

└── /manual/        总览 + 8 章 + 2 附录 →  ToT/docs/manual/  ✅ 已完成
    ├── README.md                      ✅ 总览 · 30 分钟跑通一条流程
    ├── 01-deploy-and-accounts.md       ✅ 仅保 §5 权限码
    ├── 02-dept-user-role.md            ✅ OrgUserProvider / TaskRoleAssigneeHandler
    ├── 03-forms.md                     ✅ 字段权限 / f_ 前缀 / 任务表单绑定
    ├── 04-design-and-publish.md        ✅ 流程设计 → 发布全流程
    ├── 05-participants.md              ✅ 7 handler + 会签 4 模式 + 委托
    ├── 06-start-and-approve.md         ✅ 9 submitType 路由 + 退回/撤回
    ├── 07-verify-and-troubleshoot.md    ✅ 状态机 + 跨章排错
    ├── 08-persist.md                   ✅ 3 开关 + 8 排错
    ├── appendix-a-pages.md             ✅ 系统设置 + 权限码
    └── appendix-b-values.md            ✅ 9 表对照 + 字典差异警示
```

### 8.2 本仓代码演进基线

```
vendor/jeeflow-original/  (Sep 18 2025, 13 文件)
   ↓ + 27 FIX (T1~T38) + 1 新增 (verify.py) + 11 文件改动
vendor/jeeflow/           (Sep 24 2026, 14 文件)
```

详见 `docs/BUGS.md`（38 项 FIX 含 27 修复 + 0 仍存 + 5 限制 + 16 项自检清单）。

### 8.3 合规基线

```
2026-09-19  v1.9.0 里程碑（38 FIX 全 PASS，详见 docs/BUGS.md）
2026-09-20  BUGS.md 27/27 PASS（v1.9.0 里程碑）
2026-09-23  ea-compliance.py 44/44 PASS
2026-09-24  ToT/docs 起草完成（27 篇：9 guides + 10 spec + 8 concepts）
2026-09-24  ToT/docs/manual/ 起草完成（11 篇：README + 8 章 + 2 附录）
2026-09-24  ToT/docs/README.md 建立（知识库工程起点）
2026-09-24  Phase 2 完成：§3 #1/#2/#3 字典差异修复（metadata.py:37 补 7 + 改 20 label；:77-99 改简化版）
2026-09-24  Phase 2 #4 已修复：PRD 38 → 57 + 4 文档同步（详见 §3.1.4）
```

---

> **下次动作**：
> 1. R5 知识管理员按 §3 表继续处理 **#5 / #6 / #10**（决策方向）
> 2. Phase 3 启动前先评估 4 个新脚本（§4.5）的优先级