# SOP: 流程设计引导 (flow-design)

> **所属**：组织 SOP 集（与 `customer-data-reset` / `env-config` 并列）
> **场景**：引导用户设计自己的流程 —— 从"我有模糊需求"到"能跑通的小闭环"
> **永久规则**：见 `ToT/README.md` §1 + §11 + `ToT/ea/roadmap.md` §10.2
> **核心原则**：**先跑通，再严谨** —— 不强求第一步达到 FDEP 的严谨度，逐步演进

---

## 1. 适用场景

| ✅ 适用 | ❌ 不适用 |
|--------|-----------|
| 业务团队有"重复流程"想自动化 | 一次性手工任务 |
| 现有流程太复杂想拆分 | 复杂多分支（需先 §1.5 的"演进式补严谨"）|
| 想做完整流程闭环（start → end） | 仅需状态通知（用 IM 而非流程）|
| 想让 AI / 多 executor 接力 | — |

## 2. 设计原则（v0.0 — 用户友好）

### 2.1 最小可发布原则（Minimum Viable Flow）

> **能用就好，严谨后补。**

| 阶段 | 优先级 | 严格度 |
|------|--------|--------|
| **第 1 天** | 跑通闭环 | 0%（只需 flow.json + 引擎能执行）|
| **第 1 周** | 测试稳定性 | 30%（README + flow-lint 通过）|
| **第 1 月** | 多用户协作 | 60%（Job Cards + Decision Mems 必填）|
| **第 3 月** | 审计 / 生产 | 90%+（含 baseline + 审计链路）|

### 2.2 完整性检测原则（Completeness Check）

每个流程都跑 `flow_completeness.py`：

```
得分 = sum(通过的检查项) / 总检查项
  0-30%：能跑，但没人知道为什么
  30-60%：可文档化，新人能上手
  60-90%：可协作，AI 能接力
  90-100%：可审计，可生产
```

**不强制 100%** —— 按需求演进。检测工具**主动提示**缺什么，用户按需补。

### 2.3 文本极简原则（Text Minimalism）

> **任务说清楚就足够**。`node.text.value` 只描述"这个节点做什么任务"。

**规则**：
- ✅ 允许：节点阶段名（如 "1. RML 立项"）、任务简称（如 "0. 接收/登记"）
- ❌ 避免：角色分配说明（如 `u_fdp_pm 直接`）、SPI 角色代号（如 `R3`）、未来 TODO（如 `待 v0.7+ 用 assignmentHandler`）
- ❌ 避免：括号补充说明（如 `(u_fdp_pm 直接, SPI 角色 R3 映射待 v0.7+ ...)`）

**为什么**：括号里的元信息已经分散在 NODES.md / Job Card / DESIGN.md / CHANGELOG 中。流程图本身只需传达"流程走向 + 任务名"，多余的元信息增加阅读成本不增加理解价值。

**元信息归宿**：
| 信息类型 | 应放哪里 |
|----------|----------|
| 节点具体工作步骤 | NODES.md（每节点"工作步骤"段）|
| 谁来做、什么角色 | properties.assignee + NODES.md |
| 表单字段 | properties.form |
| 出产物 / 出口标准 | properties.artifact + properties.exitCriteria |
| 未来 TODO / 设计变更 | CHANGELOG.md / roadmap.md |
| 完整工作指导（8 节）| job_cards/job_card_<node_id>.md |

## 3. 执行步骤（用户引导版）

### Step 1 · 启动设计助手

```bash
python3 ToT/sop/flow_designer.py
```

助手会问 5 个核心问题：

| # | 问题 | 答 → flow.json 字段 |
|---|------|-------------------|
| 1 | **业务目标**（一句话） | `displayName` / `purpose` |
| 2 | **谁发起？**（任意来源 / 特定角色） | `start` + 默认 `operator` |
| 3 | **几个阶段？**（3-7 个，每个阶段：名 / 执行者 / 产出） | `nodes` 数组 |
| 4 | **需要分支决策吗？**（y/n） | `snaker:decision` 节点 |
| 5 | **什么时候算完成？** | `end` 节点 |

输出：`ToT/flows/<flow-name>.json` 草稿。

### Step 2 · 跑通最小闭环

```bash
# 1. 部署
python3 ToT/sop/auto_deploy_fdep.py  # 内嵌 main_common（已支持）

# 2. 启动实例
curl -X POST .../wf/processDefine/startAndExecute -d '{"processDefineId":<id>,"operator":"<op>"}'

# 3. 一路 execute 到 DONE
# （参考 ToT/sop/customer-data-reset.md §6.4 冒烟测试）
```

### Step 3 · 跑完整性检测

```bash
python3 ToT/sop/flow_completeness.py ToT/flows/<flow>.json
```

输出示例：

```
=== expense-approval 完整性检测 ===

  §C1 流程级 (4/9):  44%
    ✓ flow.json 存在
    ✓ 文件名小写
    ✗ README.md 不存在
    ✓ ...

  §C2 Job Card 级 (0/5):  0%
    ✗ job_cards/ 子目录不存在
    ✗ 任何 job_card 文件不存在
    ...

总评分: 28% (10/36 通过)

下一步建议:
  - 创建 README.md (5 分钟)
  - 创建 job_cards/ 并生成每节点的执行器手册 (30 分钟)
  - 跑 tdd-flow.py 生成 baseline (5 分钟)
跑完后再跑 flow_completeness.py，分会到 60-80%。
```

### Step 4 · 按提示补严谨

按"下一步建议"清单**逐项完成**（不必一次全做）：

| 优先级 | 建议项 | 工作量 | 关联分数 |
|--------|--------|--------|----------|
| P1 | README.md | 5 分钟 | +10% |
| P2 | job_cards/ + gen-job-cards.py | 30 分钟 | +30% |
| P3 | Decision Mems 字段 | 10 分钟 | +10% |
| P4 | tdd-flow.py baseline | 5 分钟 | +10% |
| P5 | customer-data-reset SOP | 5 分钟 | +5% |

**关键**：**不必 100%**，按业务需求选做。

### Step 5 · issue 闭环（可选）

发现流程本身有 bug → 用 `issue_link.py` 创建 FDEP 实例处理：

```bash
python3 ToT/sop/issue_link.py \
    --flow expense-approval \
    --instance 92201234567890 \
    --severity high \
    --reason "expense-approval.stage_pm 决策不符合预期"
```

输出：
- 在 staging 端创建一个 fdep instance（issue tracking = 用 FDEP 自身）
- 把原 instance 的关键数据（task name / operator / variable）打包进 fdep 决策 mems
- 通过 FDEP 全流程：stage_intake（优先级 high）→ stage_pm（诊断）→ stage_dev（修复）→ stage_review → end

**元闭环**：FDEP 帮其他流程解决 bug。Issue 关闭 = bug 修复 + fdep instance state=DONE。

## 4. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 用户直接 copy FDEP 复杂结构 | 流程设计助手从 5 问开始，强制简化 |
| 跑通后忘记补严谨 | completeness 检测定期跑（手动/CI）|
| Issue 没真正闭环 | issue_link 强制写 fdep instanceId 才能 close |

## 5. 与其他 SOP 的关系

| SOP | 关系 |
|-----|------|
| `customer-data-reset` | 用户流程跑通后也可用此 reset |
| `flow-folder` / `flow-lint` | 用户流程的"最低门槛"（仅 flow.json + 文件名小写）|
| `tdd-flow` | 用户流程跑通后跑这个生成 baseline |
| `ea-compliance` | 用户流程 §C1-§C6 应被 §9 全套覆盖 |
| `new-trip` / `clean-customer-data` | 用户流程的留档也走这两个 |
| `env-config` | 用户流程的 deploy server URL 来自这里 |

## 6. 完整命令清单

```bash
# === 流程设计 ===
python3 ToT/sop/flow_designer.py                      # 5 问 → flow.json

# === 流程部署 ===
# (main_common 内嵌 auto_deploy)

# === 流程完整性 ===
python3 ToT/sop/flow_completeness.py ToT/flows/<flow>.json
python3 ToT/sop/flow_completeness.py ToT/flows/expense-approval.json --verbose

# === 流程演进 ===
python3 ToT/sop/gen-job-cards.py --force              # 生成 Job Cards
python3 ToT/sop/flow-lint.py ToT/flows/<flow>.json    # 静态检查
python3 ToT/sop/tdd-flow.py ToT/flows/<flow>.json     # 生成 baseline

# === Issue 闭环 ===
python3 ToT/sop/issue_link.py \
    --flow expense-approval \
    --instance 92201234567890 \
    --severity high \
    --reason "..."

# === EA 自验证（覆盖） ===
python3 ToT/sop/ea-compliance.py                     # §9 31 项 (含用户流程)
```

## 7. 关联文档

- `ToT/ea/roadmap.md §10.2` — 写新流程 7 步（精版本）
- `ToT/ea/roadmap.md §5 Pattern 9-10` — 配置集中化 + 用户引导
- `ToT/sop/flow_designer.py` — 5 问设计助手
- `ToT/sop/flow_completeness.py` — 完整性检测
- `ToT/sop/issue_link.py` — FDEP 元闭环

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-22** | **初稿**：用户友好流程设计 SOP。3 原则（最小可发布 / 完整性检测 / 先跑通后严谨）+ 5 步引导 + issue 闭环 + 与其他 SOP 关系。配套 3 个新脚本（designer + completeness + issue_link）。 |