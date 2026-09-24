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
| `facade.py` | 已演进（60+ action，PRD 声明 38）|
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
| **合计** | **27 篇** | — | — |

每篇文档统一包含 4 段元数据：

1. **来源**（`> 来源：https://jeeflow-doc.mldong.com/...`）
2. **定位**（读者角色 + 用途）
3. **本仓实测**（代码位置 / 行号 / 类名 / 签名）
4. **裁剪记录**（哪些上游章节保留 / 裁掉 / 重写）

---

## 3. 起草时已发现的「文档 ≠ 现状」清单（待确认）

> 这些是起草时实测发现的"文档与代码不一致"点，**不一定是 bug**——可能是上游文档滞后于本地改进，也可能本地字典表 / 注册表就是不一致实现。每条都需人工判断方向。

| # | 不一致点 | 文档侧（上游 + 本仓 ToT/docs）| 代码侧（本仓实测）| 建议方向 | 状态 |
|---|---|---|---|---|---|
| 1 | **`wf_process_submit_type` 缺 `7 转办`（TRANSFER）**| 上游 9 枚举；本仓 `metadata.py:34 _DICTS` 字典仅 8 项，缺 `7` | `model.py:70 SubmitType` 含 `7 TRANSFER`；`SubmitType` 枚举 = 字典源 → 字典应自动包含 | **修字典**（自动生成而非手写）| ⏳ 待确认 |
| 2 | **`wf_process_submit_type` label 重复**：`20` 与 `2` 都是「拒绝申请」| 字典表 `metadata.py:34` label 重复 | 枚举 `20=COUNTERSIGN_DISAGREE` / `2=REJECT` 语义不同 | **改 label**：`20` → 「会签拒绝」 | ⏳ 待确认 |
| 3 | **`BUILTIN_ASSIGNMENT_METAS` 用完整版 FQCN 但运行时实际加载简化版** | `metadata.py:77-99` 注册 5 个 `…OrgUserAssignmentHandlers$…` | `builtin.py:170-183` 同时注册 12 个 key：7 简化版主用 + 5 完整版别名；运行解析按简化版命中 | **统一字典源**——`BUILTIN_ASSIGNMENT_METAS` 应与 `builtin.py` 注册 key 一致 | ⏳ 待确认 |
| 4 | **PRD 声明 38 actions vs facade 实际 60+ actions** | `PRD.md` §核心端点列 38 个；本仓 `facade.py` 实际 60+ | 缺：**`transferAndAdd`** / `delegate` / `delegateHistory` / `withForm` / `comment` / `extra` / `suspend` / `resume` / `stats_overview` / `stats_trend` / `stats_group` / `getJobCardContent` 等 12+ | **更新 PRD**（或确认 38 仅指「核心 38」）| ⏳ 待确认 |
| 5 | **ea-compliance 44/44 PASS 是 2026-09-23 状态** | `spec/08-compliance.md` §本仓实测状态 | 每次合规测试结果会变 | **按版本快照**（每发版打 snapshot）| ⏳ 待确认 |
| 6 | **`docs/BUGS.md` 27 FIX + 0 仍存 是 2026-09-20 状态** | `spec/06-facade.md` / `spec/08-compliance.md` / 顶部差异 | 新 FIX-T 编号会改变总数 | **按版本快照** | ⏳ 待确认 |
| 7 | **上游 `/guides/02-flow-definition` 与本仓 `flows/` 数量不一致** | 上游 `02-flow-definition` 引 14 个 demo sample；本仓 `flows/` 含 **17 个** + 2 个废弃名（`08-countersign-sequential-approve` + `08-custom-node`）| 上游少 4 个（`13-one-vote-veto` / `14-decision-submitType` / `16-delegate-test` / `17-suspend-resume-test`）| 文档保持指向上游 14；本仓额外 3 个在 `spec/08-compliance.md` 列出 | ✅ 已记录 |
| 8 | **路由路径差异**：上游 `processDefine/startAndExecute` vs 本仓 `processInstance/startAndExecute`（兼容路径）| `guides/01-quick-start.md` §3 已加本仓对齐注解 | 两条路径本仓都注册，但语义有差异（启动 vs 启动并自动完成）| **保留兼容路径**，文档注明语义差 | ✅ 已记录 |
| 9 | **`vendor/jeeflow-original/README.md` 存在但 `vendor/jeeflow/` 无** | — | 上游有 README；本地 README 在仓库根 `README.md` | 保留上游 README 作为演进基线 | — |
| 10 | **`facade.py` 累计修改 vs 上游 `facade.py` 改动范围** | — | `diff` 显示 11 个 .py 文件改动 + 1 个新增（`verify.py`）| 演进历史应在 `CHANGELOG.md` / 迭代记录归档 | ⏳ 待补 |

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
| `ToT/sop/doc-link-checker.py`（建议）| 扫描 `ToT/docs/**/*.md` 中所有 `<行号>` 引用 + `vendor/jeeflow/<file>.py` 行号比对 | ❌ 待建 |
| `ToT/sop/doc-archive-snapshot.py`（建议）| 每次发版时 `git tag ToT/docs/vX.Y.Z` | ❌ 待建 |
| `ToT/sop/doc-vs-code-drift.py`（建议）| §3 10 个不一致项自动检测脚本 | ❌ 待建 |

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

- CI 流程加入 `doc-link-checker.py`（每次 PR）
- `ea-compliance.py` 含「文档链接完整性」子项（检查所有 `../spec/XX` / `../concepts/XX` 链接指向的文件存在）

---

## 6. 当前路线图

| 阶段 | 时间 | 目标 | 状态 |
|---|---|---|---|
| **Phase 1**（已完成）| 2026-09-24 | 起草 27 篇文档（9+10+8）| ✅ |
| **Phase 2**（进行中）| 2026-09-25 → | 处理 §3 10 个不一致项（逐项确认方向）| 🟡 待启动 |
| **Phase 3** | 2026-Q4 | 新增 `doc-link-checker.py` / `doc-archive-snapshot.py` / `doc-vs-code-drift.py` | ⏳ 待规划 |
| **Phase 4** | 2026-Q4 | CI 集成（每次 PR 跑 link-checker）| ⏳ 待规划 |
| **Phase 5** | 2027-Q1 | 第 1 次全量季度 review（验证知识库工程流程有效）| ⏳ 待规划 |

---

## 7. 关键决策与未决问题

### 7.1 已决策

- ✅ `ToT/docs/` 起点 = upstream `jeeflow-doc.mldong.com`（9+10+8 = 27 篇）
- ✅ 起点 = `vendor/jeeflow-original/` Sep 18 2025 快照
- ✅ 演进态 = `vendor/jeeflow/` 14 文件（38 FIX 全 PASS）
- ✅ 文档不是事实，需持续对齐（§4 流程）

### 7.2 未决（需 R1b / R5 决策）

- ⏳ §3 表 10 个不一致项的具体方向（修代码 / 修文档 / 双改）
- ⏳ 是否建立 `CHANGELOG.md` 跟踪 doc 变更历史
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
2026-09-20  BUGS.md 27/27 PASS（v1.9.0 里程碑）
2026-09-23  ea-compliance.py 44/44 PASS
2026-09-24  ToT/docs 起草完成（27 篇）
2026-09-24  ToT/docs/README.md 建立（知识库工程起点）
```

---

> **下次动作**：R5 知识管理员按 §3 表逐条处理（Phase 2 启动）；先 §3-1 / §3-2（字典差异，最易修）。