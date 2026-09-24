# Iteration #36 · 2026-09-24 · W43 · initiate guide · 流程级工作指南

> **驱动**：用户审视 Job Card 体系完整度，意识到 start 节点（流程入口）无 Job Card；最终采用"流程级 initiate guide"方案
> **核心成果**：✅ **新增 `ToT/flows/<flow>/initiate.md`** + **facade `_processDefine_getJobCardContent` v0.1→v0.2 安全放宽** + **SKILL.md §A 加"发起前可读 initiate guide"**

---

## 1. 时间线（~30 min / 5 步）

| 时段 | 工作 |
|------|------|
| 0~5 min | 讨论 start 节点 Job Card 必要性 — 决定不加（任务说清楚就足够原则延伸） |
| 5~15 min | 用户澄清需求："具体流程的发起注意事项" → 写 `initiate.md` 草稿（fdep） |
| 15~20 min | SKILL.md §A 后加"发起前可读 initiate guide"引用 |
| 20~25 min | facade.py v0.2 安全检查扩展 + 6/6 测试通过 |
| 25~30 min | 2 个 git commit（Iter#35 fix + Iter#36 initiate guide）|

---

## 2. 决策路径（从"start 节点要不要 Job Card"到"initiate.md"）

### 2.1 第一轮：start 节点 Job Card 必要性分析

| 节点类型 | 当前 Job Card? | 评估 |
|----------|---------------|------|
| start | ❌ 跳过（`gen-job-cards.py:148 NON_TASK_NODES`）| 无 task 执行（纯路由）|
| task | ✅ | 8 节齐全（执行层完整）|
| decision | ❌ 跳过 | 路由节点（条件分支）|
| end | ❌ 跳过 | 终态节点 |

**第一轮结论**：不加 start Job Card（任务说清楚就够原则）。

### 2.2 第二轮：用户澄清需求

> "我想实现的是某个具体流程的指南而不是通用指南"

→ 不需要"通用发起流程指南"，需要**"fdep 怎么发起"**这类**具体流程**指南。

### 2.3 第三轮：落地方式选择

| 方案 | 利 | 弊 |
|------|----|----|
| A · `initiate.md` + API 读 | 复用 `getJobCardContent` | 需改 facade 安全检查 |
| B · 新增独立 endpoint | 专用 | 重复 endpoint |
| C · 放进 `job_cards/` 下 | 0 改动 | 与 task 节点语义混 |

→ 选 **A**。

---

## 3. initiate.md 模板（已应用于 fdep）

### 3.1 4 节结构

1. **何时发起**：触发场景 + 可发起者 + 发起动作
2. **必填参数**：processDefineId / operator / businessNo / variables
3. **发起后预期路径**：首 task + 流转链 + 终态
4. **注意事项**：易错点（无角色限制 / start ≠ R3 / 必须 active）

### 3.2 fdep 示例（1073 chars）

```markdown
# Initiate Guide · fdep
## 1. 何时发起
- 触发场景：任何新需求 / 请求（人类 / AI Agent / 外部用户均可）
- 可发起者：无角色限制（start ≠ R3，PM 是后续接收窗口 stage_intake）
- 发起动作：POST /wf/processDefine/startAndExecute
## 2. 必填参数
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| processDefineId | int | ✅ | 数字 ID（不是 processDefineName）|
| operator | str | ✅ | 发起人 uid |
| businessNo | str | ⛔ | 业务单号 |
| variables | dict | ⛔ | 业务变量 |
## 3. 发起后预期路径
- 首 task：stage_intake（PM 接收窗口）
- 后续流转：stage_intake → decision_intake → ... → end
- 终态：end / end_rejected
## 4. 注意事项
- ✅ 无角色限制
- ❌ start 不等于 R3
- ⚠ 发起前确认 fdep 流程已 deploy 且 active
```

---

## 4. facade.py `_processDefine_getJobCardContent` v0.1 → v0.2

### 4.1 安全检查变化

| v0.1 | v0.2 |
|------|------|
| `ToT/flows/<flow>/job_cards/` | `ToT/flows/<flow>/`（任意子目录） |
| 只允许 job_card | job_card + initiate.md + 任意 .md |
| 拒绝 `<flow>.json` | 仍拒绝（**双层**：startswith + endswith .md）|

### 4.2 双层安全检查

```python
# 第一层：必须在流程子目录
expected_dir = f"ToT/flows/{name}/"
if not normalized_url.startswith(expected_dir):
    raise ValueError(f"url 不安全: {url}（应位于 {expected_dir} 下）")

# 第二层：必须 .md 后缀（自动补）
if not normalized_url.endswith(".md"):
    raise ValueError(f"url 后缀必须为 .md: {normalized_url}")
```

### 4.3 6/6 测试通过

| Test | 期望 | 结果 |
|------|------|------|
| 1. 读 `ToT/flows/fdep/initiate.md` | code 0, ~1073 chars | ✅ 1073 chars |
| 2. 读 `job_cards/job_card_stage_pm.md` | code 0, ~2900 chars（向后兼容） | ✅ 2900 chars |
| 3. `../../../etc/passwd` | 99999999 + 新错误信息 | ✅ "应位于 ToT/flows/fdep/ 下" |
| 4. `ToT/flows/fdep.json`（设计层）| 99999999 | ✅ "应位于 ToT/flows/fdep/ 下" |
| 5. 越界（invoice-approval 目录）| 99999999 | ✅ |
| 6. 自动补 `.md` | code 0 | ✅ |

---

## 5. SKILL.md §A 增量

```markdown
#### 发起前可读 initiate guide

- 文件位置：`ToT/flows/<processDefineName>/initiate.md`
- 读取方式：复用 `processDefine/getJobCardContent`，传 `url: "ToT/flows/<flow>/initiate.md"`
- 内容包含：何时发起 / 必填参数 / 发起后预期路径 / 注意事项
- 适用场景：发起流程前**总览**该流程的业务触发条件、首 task、终态分支
```

---

## 6. git 提交（2 个）

```
ce63407 Iter#36 initiate guide · flow-level work instruction via getJobCardContent
        ToT/flows/fdep/initiate.md (new, 1073 chars)
        vendor/jeeflow/facade.py (v0.1 → v0.2)
        ToT/skills/flow-operator/SKILL.md (§A 加 initiate guide)

af58071 Iter#35 fix: drop spi_role auto-derive in gen-job-cards.py
        (defensive fix for fdep v0.6.2 text.value simplify)
```

- 总变更：60 insertions, 8 deletions, 1 file created
- ahead of origin/dev by **4 commits**（等用户手动 push）

---

## 7. 经验沉淀

### 7.1 Job Card 体系的"双层"

```
ToT/flows/<flow>/
├── initiate.md           # 流程级指南（发起前读）
└── job_cards/
    ├── job_card_<task1>.md   # task 级指南（执行中读）
    ├── job_card_<task2>.md
    └── ...
```

- **流程级**（`initiate.md`）：发起前总览（何时/参数/路径/注意）
- **执行级**（`job_card_<task>.md`）：执行任务时具体工作（8 节）

### 7.2 getJobCardContent endpoint 双层化

| 层 | 内容 |
|----|------|
| 流程级 | initiate.md（流程发起指南）|
| 任务级 | job_card_<task>.md（任务执行指南）|

→ **同一个 endpoint，多用途**（奥卡姆）。

### 7.3 与 fdep v0.6.2 的连贯性

- fdep v0.6.2 text.value 简化 → Job Card 防御性修复（gen-job-cards.py）
- Iter#36 initiate.md → Job Card 体系扩展（facade v0.2）
- 一脉相承：**任务说清楚就足够** + **该写在哪写在哪**（initiate.md 是新位置，job_card 是原位置）

### 7.4 未来 backlog

- invoice-approval 补 initiate.md（B 计划）
- leave-approval 流程的 initiate.md（如果未来添加）
- gen-job-cards.py 是否需扩展：检测 `initiate.md` 存在性？