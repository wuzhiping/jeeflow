# CC · 02 · 业务流程设计管理者

> **Persona**：业务流程设计者 + 流程管理者 + FDEP 流程持续改进者
> **时间预算**：半天/周（设计 + 监控）+ 半天/迭代（改进周期）
> **典型任务**：设计新流程 / 发布 / 跑一段时间看数据 / 改流程 / 沉淀到模式库

---

## 1. Persona Profile

| 维度 | 内容 |
|---|---|
| 角色 | 流程 Owner（业务部门骨干）+ 流程管理员（IT 流程科） |
| 工具 | jeeFlow 后台 + `/api/admin/stats/overview` + FDEP 字典 |
| 痛点 | 设计时不知有没有现成模式 / 跑了一周不知道哪里卡 / 改进没数据 |
| 期望 | 复制好模式 / 一眼看出瓶颈 / 改之前能 AB |
| 成功标志 | 流程通过率 ↑、平均时长 ↓、返工率 ↓ |

---

## 2. Evidence（事实现状）

| 维度 | 数据 | 来源 |
|---|---|---|
| 流程定义 9 个 spec doc | ToT/docs/spec/01-10 | `ls ToT/docs/spec/` |
| 流程设计 9 个 guides | ToT/docs/guides/01-10 | `ls ToT/docs/guides/` |
| 用户手册 11 个 manual | ToT/docs/manual/* | `ls ToT/docs/manual/` |
| **FDEP 实现** | 8 个 .py + 5 个 JSON 数据文件 | `ls spi/fdep/` |
| FDEP 文档 | **0 个 doc**（未沉淀）| `grep -rl FDEP ToT/docs/` → 0 hit |
| 设计模式/反模式集 | 0 个 | `ls ToT/docs/patterns/` → 不存在 |
| 流程 KPI 字典 | 0 个 | 缺失 |
| `/api/admin/stats/overview` | ✅ 已实现 | `main_common.py:950` |
| `/api/admin/stats/trend` | ✅ 已实现 | `main_common.py:973` |
| `/api/admin/stats/group` | ✅ 已实现 | `main_common.py:985` |

---

## 3. 当前缺口（Gaps）

1. **FDEP 模块零文档**：`spi/fdep/` 有 8 个 .py + 5 个 JSON，但 ToT/docs 无任何介绍——核心用户群「设计者」完全看不到
2. **设计模式未沉淀**：上游 `guides/02-flow-definition` 是通用建议，缺本仓典型场景（年假/报销/合同审批）的具体模板
3. **改进缺数据**：知道 `/api/admin/stats/overview` 有数据，但不知道哪些 KPI 怎么解读
4. **跨流程对比缺**：5 个并行流程谁是瓶颈？无横向 dashboard
5. **A/B 改进无工具**：改了字段怎么评估？无对比机制

---

## 4. 短期行动计划（4 周）

### A1. FDEP 模块完整文档
- **位置**：`ToT/docs/concepts/10-fdep.md`（新建）
- **内容**：
  - FDEP 模块定位（`spi/fdep/` 8 个文件 + 5 个 JSON）
  - 8 个 SPI 实现：`user_map.py` / `get_user.py` / `find_dept_leaders.py` / `find_dept_main_leaders.py` / `user_search.py` / `dicts.py` / `data.py` / `__init__.py`
  - JSON 数据契约：`FDEP_DICTS.json` / `FDEP_ROLES.json` / `FDEP_DEPT_LEADERS.json` / `FDEP_DEPT_MAIN_LEADERS.json` / `FDEP_FIND_USER_BY_ROLE_DEPT.json`
  - 调用链示例：流程设计时如何用 FDEP 解析「申请人部门领导」
- **ETA**：W1 末
- **成功标准**：新人能在 5 分钟内理解 FDEP 是什么、怎么用

### A2. 设计模式库（10 个本仓典型）
- **位置**：`ToT/docs/patterns/`（新建目录，5 个 .md）
- **内容**（每文件 1-2 个模式）：
  - `01-approval-and-cc.md`：审批 + 抄送模式
  - `02-multi-level-with-jump.md`：多级 + 跳转
  - `03-countersign-vote.md`：会签 + 投票
  - `04-reject-loop.md`：驳回 + 循环
  - `05-condition-branching.md`：条件分支 + 决策
- **每个模式**：适用场景 + BPMN 示意 + 字段表 + 反模式警告
- **ETA**：W2 末
- **成功标准**：设计新流程时，参考 5 个 pattern，平均设计时间 ↓ 30%

### A3. 反模式清单（10 个常见错误）
- **位置**：`ToT/docs/patterns/anti-patterns.md`（新建）
- **内容**：调研 + 历史 issue 提炼
  - start 节点直接条件分支（应先收集变量）
  - decision 节点无 default 边（会卡住）
  - 多人任务无会签类型（默认 parallel 但预期 sequential）
  - 抄送放审批后（应在审批前提示）
  - 自循环无人能终止
  - ... 共 10 条
- **数据源**：`vendor/jeeflow/verify.py` 的 `verify_flow` 实际能检测到的
- **ETA**：W2 末
- **成功标准**：`verify_flow` warnings 被设计者当作 checklist

### A5. KPI 字典（流程指标解读）
- **位置**：`ToT/docs/spec/kpi-dictionary.md`（新建）
- **内容**：
  - 12 个核心 KPI 定义（通过率、平均时长、瓶颈任务、返工率、积压量、SLA 达标率 ...）
  - 每个 KPI：计算公式 + 数据源（`/api/admin/stats/*`）+ 解读阈值 + 改进建议
  - 案例：「平均时长 > 48h」通常意味着「某审批人积压」
- **ETA**：W3 末
- **成功标准**：管理者不开会就能看出哪条流程病了

### A6. FDEP 持续改进闭环工具
- **位置**：`ToT/sop/fdep-trend.py`（新建）
- **动作**：每周扫 `/api/admin/stats/overview` × N 个流程 → 输出退化榜单
- **输出**：Markdown 表（流程名 / 7d 趋势 / 是否需要改进）+ 自动 commit 到 ToT/sop/snapshots/fdep-trend-*.md
- **ETA**：W4 末
- **成功标准**：管理者每周一打开就有榜单

---

## 5. 反馈闭环（Feedback Loop）

| 渠道 | 内容 | 频率 |
|---|---|---|
| `feedback/02-process-designer-<seq>.md` | 设计卡点 / 模式缺失 / 流程退步 | 随时 |
| `feedback/_routes/02-*.md`（来自 **03-participant**）| 参与者反馈中带 `design-issue` / `process-gap` 标签 | 每周自动分流 |
| `/api/admin/stats/overview` 数据 | 自动 trigger 「退步告警」 | 每周 |
| FDEP JSON 变更 | git diff 触发 review | 每次 |

**反馈处理 SLA**：
- P0（流程卡住所有人）：立即（4h 内）
- P1（设计卡点）：1 周内加 pattern
- P2（指标解读不清）：季度评审
- **来自 03-participant 的 design-issue**：48h 内评估 + 决定是加 pattern 还是改流程

---

## 5.5 ★ 来自参与者反馈的接收（飞轮下游）

本 plan 是飞轮的 3 个下游之一。参与者反馈中带以下标签的会自动路由到本 plan：

| 反馈标签 | 触发行动 | 路由工具 |
|---|---|---|
| `design-issue` + 流程卡死/走错 | A1 FDEP 文档 / A2 模式库 | `feedback-triage.py` |
| `design-issue` + 找不到合适模式 | A2 模式库 + A3 反模式 | `feedback-triage.py` |
| `process-gap` + KPI 不清晰 | A5 KPI 字典 | `feedback-triage.py` |
| `ux-issue`（虽然归 03，但根因在设计）| A2 模式库优化 | `feedback-triage.py` |

**闭环要求**：
- 模式/反模式更新后，在 `feedback/_routes/02-<seq>.md` 标注 `状态: 已闭环`
- 同步到 `feedback/03-participant-<seq>.md` 的 `## 闭环` 字段
- 同步更新 `ToT/CC/decision-tree.md` 或 `ToT/CC/faq.md`

---

## 6. Success Metrics（量化）

| 指标 | 当前 | 目标（4 周末）|
|---|---|---|
| FDEP 模块文档数 | 0 | 1 个完整 doc |
| 设计模式库 | 0 | ≥ 5 个 pattern |
| 反模式清单 | 0 | ≥ 10 条 |
| KPI 字典 | 0 | ≥ 12 个 KPI 解读 |
| FDEP trend 工具 | 不存在 | 每周输出榜单 |
| 流程平均通过率 | 未知基线 | ↑ 5% |

---

## 7. 跨 Persona 引用

- ← 01-engine-developer：引擎升级可能影响 FDEP SPI 兼容性
- → 03-participant：模式里要标注「参与者体验」（会签等多久、能否加签）
- → 04-ops-audit：流程 KPI 数据也是审计依据（谁长期积压）
- → ToT/docs/guides/02-flow-definition.md：设计起点
- → ToT/docs/manual/04-design-and-publish.md：发布流程
- → ToT/docs/concepts/03-execution-engine.md：会签四模式理论