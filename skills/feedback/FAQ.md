# jeeflow 流程设计 FAQ · 1.1 升级 (W47 Day 3)

> **升级日期**: 2026-11-12 (W47 Day 3)
> **状态**: 🟡 **v1.1 draft** (新增 2 题: Q2.5 PARALLEL countersign REJECT + Q3.5 验证规则)
> **来源**: 8 条已闭环 FB (FB-0006/0008/0009/0010/0011/0012/0013/0014/0015) + omarchy 贡献 + hermes SLA 工具集
> **累计题目**: 24 题 (1.1 版本)

---

## 1. 节点配置类

### Q1.1 assignee / candidate_groups / assignee_expr 何时用?

**A**: 三种方式互斥, 按优先级从高到低:

| 字段 | 用途 | 适用场景 |
|------|------|----------|
| `assignee` | 直接指定 1 人 | 流程固定审批人, 如"采购员" |
| `candidate_groups` | 候选组 | 多角色中任一可处理, 如"任意经理" |
| `assignee_expr` | 表达式动态计算 | 复杂规则, 如 `manager_of(流程发起人)` |

**实战建议**:
- 简单场景 → `assignee`
- 候选池 → `candidate_groups`
- 复杂规则 → `assignee_expr` (需谨慎, 见 Q3.1 变量作用域)
- 来源: FB-0006 (auto-assignee-by-org 派生)

### Q1.2 delegate 与 assignee 区别?

**A**: `delegate` 是 `assignee` 的代理, 临时授权处理.

| 字段 | 是否必填 | 是否可空 |
|------|----------|----------|
| `assignee` | ✅ 主处理人 | ❌ 必须有值 |
| `delegate` | 🟡 可选 | ✅ 可空 (无人代理) |

**实战场景**:
- 主处理人请假 → 设置 `delegate` = 同事 A
- 任务仍归 `assignee` 名下, 但 `delegate` 可代处理
- 来源: FB-0008 + FB-0009 (docs 缺口)

### Q1.3 auto-assignee-by-org 何时启用?

**A**: 当流程发起人想"按组织自动分配审批人"时启用. 引擎按"流程实例所在组织"查找该组织下的"流程审批人".

**数据需求**:
- `org_id` 字段 (从发起人上下文获取)
- `org.flow_approver` 字段 (每个组织 1 个默认审批人)

**待实施**: Phase 9 Month 2 (W44-W47)
**来源**: FB-0006

### Q1.4 (新增 · v0.2) auto-assignee-by-org 解析逻辑 + 回退顺序?

**A**: 按优先级从高到低解析 (org_repo v0.2 实现):

| # | 字段 | 解析逻辑 | 失败回退 |
|---|------|----------|----------|
| 1 | `auto_assignee_by_org=true` | 查 `org.flow_approvers[]` | → fallback_chain → fallback_assignee → E1803 |
| 2 | `fallback_assignee` (新) | 单人指定 | → 无回退 |
| 3 | `assignee` | 显式单人 | → 无回退 |
| 4 | `assignee_expr` | 表达式动态 | → E1805 (eval 异常) |
| 5 | `candidate_groups` | 候选池 | → E1804 (无人处理) |

**实战**: simple 流程 → task1 用 `auto_assignee_by_org=true` + 配 `fallback_assignee="leader"` (org 不存在时回退).

**错误码** (W45 Day 2 起草):
- E1801: `auto_assignee_by_org=true` 但 context 无 `org_id`
- E1802: `org_id` 不在 org_repo 且无 fallback
- E1803: `org.flow_approvers` 和 `fallback_chain` 都为空
- E1804: 全部解析路径失败
- E1805: `assignee_expr` 表达式异常

**来源**: auto-assignee-by-org 0.2 (W45 Day 2 方案)

---

## 2. 拓扑类

### Q2.1 countersign 节点 submitType 与拓扑关系?

**A**: `submitType` 仅在 `countersign task → end` 直接拓扑下生效.

| 拓扑 | submitType 路径 | 行为 |
|------|----------------|------|
| task → end | cs_veto / cs_all / cs_majority | submitType 生效 ✅ |
| task → decision → 任意 | decision expr 路径 | submitType **沉默** ⚠️ |

**反模式**: 假设 submitType=20 (一票否决) 在 task → decision 拓扑下生效 → 设计错误.

**正确做法**: 拆为 2 个独立节点:
```
[start] → [countersign task, submitType=20] → [end]
       ↘ [decision, expr=cs_veto_result] → [后续]
```

**来源**: FB-0012 (草稿中, 待 flowuser 实证)

### Q2.2 decision 节点 expr 与 submitType 区别?

**A**:

| 字段 | 用途 | 类型 |
|------|------|------|
| `decision.expr` | 决策表达式 (Python-like) | 字符串 |
| `task.submitType` | 会签合流策略 | 枚举 (10/20/30) |

**实战**: decision 用 expr, task (countersign) 用 submitType. 不混用.

### Q2.3 parallel gateway 何时用, 何时用 countersign?

**A**:

| 场景 | 节点 |
|------|------|
| **多分支并行, 无需合流** | parallel gateway |
| **多 assignee 协同, 需合流** | countersign task |

**反模式**: 用 countersign 处理"两个独立分支" → 应改 parallel gateway + join.

### Q2.5 (新增 · v1.1) PARALLEL countersign REJECT (submitType=2) 有何陷阱?

**A**: **submitType=2 在 PARALLEL countersign 节点上 REJECT 时, 其他成员任务**残留 DOING**, 这是 BUG-4 (P0 真引擎 BUG)**.

**来源**: omarchy BDD-1601 5-run bug-hunt (取件码 39376, FB-0015) + FIX-T114.

**问题**: REJECT (submitType=2) 路径 (`engine.py:220-236 execute_and_jump_to_end`) 缺少 sibling DOING task 清理. 与 ONE_VOTE_VETO 路径 (`engine.py:184-210`) 不一致.

**实证** (instance 92137028795620, rejecter=userA):
- instance.state = 45 REJECT ✅
- userA task = 20 DONE ✅
- userB task = **10 DOING** (❌ orphan, 阻塞后续)
- userC task = **10 DOING** (❌ orphan)

**修复 (FIX-T114)**: 复刻 cs_veto 路径的 abandon 逻辑:
1. 找到当前会签节点
2. sibling DOING task → ABANDON (state=99, updateUser=rejecter)
3. 其他节点 DOING 也清

**修复后预期**:
- userB task = 99 ABANDONED + updateUser=userA ✅
- userC task = 99 ABANDONED + updateUser=userA ✅

**关联 BDD**: `bdd-1901-1905-fix-t114-reject-orphan_20261110.sh` (5 场景, 设计就绪)

**来源**: omarchy 第 3 次持续贡献

---

## 3. 变量作用域类

### Q3.1 流程变量在 task → decision 是否共享?

**A**: ✅ **共享** (同一流程实例内, 变量是流程级, 不是节点级).

```python
# task 节点设置变量
task.set_variable("approved", True)

# decision 节点可访问
decision.expr = "approved == True"
```

**反模式** (常见错误):
```python
# task 节点
x = 10  # 局部? 全局?

# decision 节点
expr = "x == 10"  # ❌ 如果 x 是 task 局部, 此处 None
```

**铁律**: 流程实例内的变量 = 流程级, 所有节点共享. 节点不持有"私有变量".

**来源**: FB-0011 (变量作用域铁律)

### Q3.2 跨节点的变量如何传递?

**A**: 流程级变量自动共享. 无需手动传递.

```python
# node-A
process_instance.set_variable("data", {"key": "value"})

# node-B (后续节点)
data = process_instance.get_variable("data")  # 直接可用
```

### Q3.3 变量作用域铁律 (FB-0011)

**A**:

1. **流程实例级变量**: 全流程所有节点可见
2. **节点无私有变量**: 节点不持有局部变量
3. **跨节点数据流**: 通过流程级变量传递, 不通过节点参数
4. **ndjson 解读**: `vars` 字段是流程级, 任何节点可读可写

**反模式**: 假设某变量是 task 节点"私有", 在 decision 节点读不到 → 设计错误.

**来源**: FB-0011 (3 处文档修订就绪)

### Q3.4 (新增 · v0.2) decision expr 引用未声明变量会怎样?

**A**: **引擎静默走默认边**, 下游节点永远不被访问. 这是 **BUG-3** (P0 真引擎 BUG).

**来源**: omarchy BDD-1517 5-run bug-hunt (取件码 97841, FB-0014) + FIX-T113

**问题**: expr `days > 3` 但 variables 用 `f_days=5` → KeyError → 引擎 except 吞掉 → 走默认边 (无 expr).

**修复 (FIX-T113)**: expr 与 variables key 对齐 (`f_days > 3`).

**验证规则 (W014)**: 在 `vendor/jeeflow/verify.py` 中新增 W014, save 时检测未知变量引用, 提示拼写错误.

**实战**: 见 `flows/03-decision-expr-fixA1.json` (修复版本).

**Hermes SLA 工具集**: 已纳入 `sla/check_w014_decision_expr_unknown_var.sh` (32/32 PASS)

### Q3.5 (新增 · v1.1) verify 规则 (W001-W014) 有什么用?

**A**: **verify 规则 = save 时拦截** 的设计验证, 帮流程设计者提前发现问题.

| 规则 | 类型 | 触发条件 | 来源 |
|------|------|----------|------|
| **W001-W010** | 节点/边基础检查 | 名称/重复/缺失/类型 | jeeflow 基础 |
| **W011-W012** | 节点扩展 | task multi-out / 自定义节点 | BDD #127-#250 |
| **W013** | 决策多分支风险 | decision 缺 expr 或全 false | **BUG-2 (FIX-T112)** |
| **W014** | decision expr 未知变量 | 引用未声明 key | **BUG-3 (FIX-T113, omarchy)** |
| **E001-E015** | 阻塞性错误 | name/cycle/start-end | 流程必填 |

**核心价值**:
- **早期发现问题** (save 时拦截, 不等运行时)
- **非阻塞警告** (W 类不阻塞, 仅存入 design.remark)
- **多轮演化** (每 BDD 新增 → 新增 W 规则)

**实战**: hermes SLA 工具集 `sla/check_w014_decision_expr_unknown_var.sh` 是 W014 规则的实现 (omarchy 贡献).

**来源**: BDD #127-#250 + BUG-2/3 修复链

---

## 4. 设计决策类

### Q4.1 为什么某处 "设计如此"?

**A**: jeeflow 的"设计如此"决策, 通常源于:

| 类别 | 例子 | 原因 |
|------|------|------|
| 性能 | decision expr 不支持 submitType | 简化决策路径, 避免双逻辑 |
| 安全 | vendor/ 不修改 (FREEZE 期) | 防止失控造新功能 |
| 简洁 | submitType 仅 3 个枚举 | 避免枚举爆炸 |
| 客户驱动 | 不主动造功能 | Phase 9 原则 |

**实战**: 遇到"为什么这样设计"时, 先看 `docs/known-issues.md §X` + `feedback/attachments/FB-XXXX/`.

**来源**: FB-0010 (验证 "设计如此")

### Q4.2 引擎不修改 vendor/ 的边界在哪里?

**A**:

| 状态 | vendor/ 可改? | docs/ 可改? |
|------|---------------|-------------|
| **FREEZE 期** (Phase 8 + 当前) | ❌ 仅 FB-NNNN 关联可改 | ✅ 任何时候 |
| **解冻后** (Phase 9 双签后) | ✅ 按 FB 关联 | ✅ 任何时候 |

**当前**: 未解冻, vendor/ 改 = 需 FB-NNNN 关联 (例: FB-0007 FIX-T112 改过 1 次).
**来源**: FREEZE.md §6

### Q4.3 客户反馈驱动的改进 vs 工程师想象的增强?

**A**:

| 类型 | 来源 | 例子 |
|------|------|------|
| ✅ 客户反馈驱动 | FB-NNNN 关联 | auto-assignee-by-org (FB-0006) |
| ❌ 工程师想象 | "我觉得用户需要" | 加 3 个新功能 |

**铁律**: Phase 9 严禁后者. 仅前者可改 vendor/.

### Q4.4 (新增 · v1.0) hermes 取件码 vs DM 通道的边界?

**A**: hermes 服务的两类用户, 通道互斥:

| 通道 | 工具 | 适用 | 关键区别 |
|------|------|------|----------|
| **DM 通道** | hermes-peer-dm | flowuser 等可双向沟通的用户 | 实时双向, hermes 主动 DM 等回复 |
| **file-share 通道** | skills:file-share | omarchy 等无法 DM 的用户 | 异步单向, 取件码是**唯一**信息 |

**边界判断**:
- 用户能 DM → DM 通道, 不需要取件码
- 用户只能上传文件 → file-share 通道, 必须用取件码
- 用户发文件 + 取件码 → file-share 频道是主, DM 是辅助

**反模式**:
- ❌ 默认所有用户 = DM 用户 (异步用户需求未满足)
- ❌ 默认所有用户 = file-share 用户 (没利用双向沟通机会)
- ❌ 混淆两个通道 (chat 内容 vs 取件码内容错位)

**来源**: omarchy 持续贡献 (取件码 77045 + 97841) + FB-0013/0014 复盘

---

## 5. 工程实践类

### Q5.1 流程 ndjson 如何解读?

**A**: 每个流程实例对应 1 个 ndjson 文件 (或多行 JSON).

**关键字段**:
- `process_instance_id`: 流程实例 ID (唯一)
- `node_id`: 当前节点 ID
- `vars`: 流程级变量 (所有节点共享)
- `event`: 事件类型 (start / task_created / task_completed / decision_evaluated / end)
- `timestamp`: 时间戳

**实战**: 定位 BUG 时, 按 `process_instance_id` 过滤, 按时间戳排序.

### Q5.2 引擎日志如何定位 BUG?

**A**:

1. 找到流程实例 ID (从用户报告)
2. 读 ndjson (按 process_instance_id 过滤)
3. 检查事件序列 (start → task_created → task_completed → ...)
4. 找到异常事件 (decision_evaluated 返回错误, 或 task 卡住)
5. 对照 `docs/flow.md §X.X` 看是否符合预期

**反模式**: 不读 ndjson 直接猜 → 浪费时间.

### Q5.3 Phase 9 反馈闭环流程?

**A**:

```
用户提交反馈 (FB-NNNN)
  ↓
hermes 接收 + 分类 (P0/P1/P2)
  ↓
判断: BUG / DOC / UX / 撤回
  ↓
修复 (按 FREEZE 规则, 仅 FB 关联可改 vendor/)
  ↓
BDD 回归测试 (双端 PASS)
  ↓
通知用户 + 等 review
  ↓
用户确认 → 闭环
```

**关键**: 客户沉默 14 天 → hermes 主动询问.

### Q5.4 (新增 · v0.2) 取件码 (file-share) 流程?

**A**: 异步用户通过 file-share 上传文件, hermes 按 SOP 10 步处理:

```
[用户] 通过 file-share 上传
  ↓
[file-share 服务] 返回取件码 + URL
  ↓
[用户] 把取件码告诉 hermes
  ↓
[hermes] Step 1: 先问主人 (哪个用户的取件码?)
  ↓
[hermes] Step 2-3: 下载 + 解压
  ↓
[hermes] Step 4: 列文件清单
  ↓
[hermes] Step 5: 判断文件性质
  ↓
[hermes] Step 6: 解读 issue
  ↓
[hermes] Step 7: 登记 FB
  ↓
[hermes] Step 8: 归档 + 索引
  ↓
[hermes] Step 9: 教训 + 自反思
  ↓
[hermes] Step 10: 通知 / 归档
```

**核心原则**:
- chat 内容 ≠ 取件码对应文件内容
- file-share = 持续反馈渠道
- 主人必须问, 不能假设
- hermes 自己的文件被贴 = 立即 incomplete-info
- 下载 + 解读 + 决定 = hermes SOP

**来源**: omarchy 取件码 77045 + 97841 (FB-0013 + FB-0014)

### Q5.5 (新增 · v1.0) omarchy 持续贡献渠道价值?

**A**: omarchy 通过 file-share 渠道已 2 次贡献, 价值密度递增:

| 维度 | 第 1 次 (取件码 77045) | 第 2 次 (取件码 97841) |
|------|----------------------|----------------------|
| **类型** | BDD 验证报告 | **真 BUG 修复 + verify 规则** |
| **贡献物** | `run_10_times.py` (4155 B) | **vendor/jeeflow/verify.py W014 + FIX-T113** |
| **结果** | 10/10 PASS, 无新 BUG | **BUG-3 找到 + 修复 + 5/5 PASS 验证** |
| **价值** | SLA 工具参考 | **SLA 32/32 PASS 累计** |
| **用户等级** | L3 | **L3+ (含 BUG 修复)** |

**关键洞察**:
- file-share 持续渠道 = 真实价值密度递增
- omarchy = 持续贡献型用户的标杆
- 用户类型升级: L1 (1次) → L2 (2次) → L3 (主动贡献) → **L3+ (含 BUG 修复)**

**实战策略**:
- hermes 每天检查 omarchy 新取件码 (L3+ 监控)
- W014 verify 规则已纳入 hermes SLA 工具集
- omarchy 的贡献方法论 = hermes 验证模板

### Q6.1 (新增 · v1.0) 客户旅程 6 段怎么跟踪?

**A**: jeeflow 客户旅程标准 6 段 (C-001 实证):

| 段 | 名称 | 跟踪项 | 文件 |
|----|------|--------|------|
| **1** | Awareness (认知) | 客户首次接触 jeeflow | `customers/C-XXX/journey-evidence/` |
| **2** | Onboarding (试用) | 首次跑通流程 | `customers/C-XXX/onboarding-log.md` |
| **3** | First Process (首个流程) | 提交第 1 个真实流程 | `customers/C-XXX/first-process-instance-id` |
| **4** | Iteration (迭代) | BUG 报告 + 修复闭环 | `feedback/inbox/FB-NNNN.json` |
| **5** | Post-Deployment (后部署) | 跟踪期 5+ 天, 健康度 ≥ 9.0 | `customers/C-XXX/journey-evidence/2026-XX-XX-stage6-tracking.md` |
| **6** | Long-term Success (长期成功) | 升级条件达成, ≥ 1 新流程模式 | `customers/C-XXX/journey-evidence/2026-XX-XX-stage7-launch.md` |

**C-001 当前**: 阶段 6 (Day 38) · 等 flowuser 升级到阶段 7

**来源**: C-001 阶段 6 跟踪记录 (`customers/C-001/journey-evidence/`)

### Q6.2 (新增 · v1.0) 季度复盘 vs 月度 metrics vs 周报 区别?

**A**: 三种 retrospective 区别在于**视角 + 详略**:

| 维度 | 周报 (weekly) | 月度 metrics | 季度复盘 |
|------|---------------|---------------|-----------|
| **周期** | 5 个工作日 | 1 个月 (~4 周) | 1 季度 (~3 个月) |
| **格式** | markdown 周报 | JSON 机读 + md 摘要 | 详细 md 复盘 |
| **内容** | Day 1-5 行动计划 | 累计 FB / fix / verify / BDD | 整体节奏 + 教训 + 路线图 |
| **触发** | 每周 Day 5 收盘 | 每月初 (10-01, 11-01, 12-01) | 季度末 (12-31, 3-31, 6-30) |
| **读者** | hermes 内部 | hermes + 自动化脚本 | hermes + 全员 |
| **文件路径** | `skills/weekly/2026-WNN.md` | `skills/feedback/metrics/monthly-YYYY-MM.json` | `skills/feedback/retrospectives/YYYY-QN-quarterly.md` |

**Month 1 (W40-W43)** 产出:
- 4 份周报 (W40/W41/W42/W43)
- 2 份月度 metrics (10-01, 10-14)
- 1 份 Q3 季度复盘 (10-08 published v1.0)
- 1 份 Month 1 收官报告 (10-17)

**Month 2 (W44-W47)** 计划:
- 4 份周报 (W44/W45/W46/W47)
- 1 份月度 metrics 11 月 (11-01)
- Month 2 收官报告 (11-17)

---

## 6. v1.0 完整题库 (22 题)

### 节点配置类 (4 题)
- ✅ Q1.1 assignee / candidate_groups / assignee_expr 优先级
- ✅ Q1.2 delegate 与 assignee 区别
- ✅ Q1.3 auto-assignee-by-org 何时启用
- ✅ Q1.4 auto-assignee-by-org 解析逻辑 + 回退顺序 (新增 · v0.2)

### 拓扑类 (3 题)
- ✅ Q2.1 countersign 节点 submitType 与拓扑关系
- ✅ Q2.2 decision 节点 expr 与 submitType 区别
- ✅ Q2.3 parallel gateway 何时用, 何时用 countersign

### 变量作用域类 (4 题)
- ✅ Q3.1 流程变量在 task → decision 是否共享
- ✅ Q3.2 跨节点的变量如何传递
- ✅ Q3.3 变量作用域铁律 (FB-0011)
- ✅ Q3.4 decision expr 引用未声明变量会怎样 (新增 · v0.2 · omarchy BUG-3)

### 设计决策类 (4 题)
- ✅ Q4.1 为什么某处 "设计如此"?
- ✅ Q4.2 引擎不修改 vendor/ 的边界在哪里?
- ✅ Q4.3 客户反馈驱动的改进 vs 工程师想象的增强?
- ✅ Q4.4 (新增 · v1.0) hermes 取件码 vs DM 通道的边界?

### 工程实践类 (5 题)
- ✅ Q5.1 流程 ndjson 如何解读?
- ✅ Q5.2 引擎日志如何定位 BUG?
- ✅ Q5.3 Phase 9 反馈闭环流程?
- ✅ Q5.4 取件码 (file-share) 流程? (新增 · v0.2)
- ✅ Q5.5 omarchy 持续贡献渠道价值? (新增 · v1.0)

### 综合应用类 (2 题 · v1.0 新增)
- ✅ Q6.1 客户旅程 6 段怎么跟踪?
- ✅ Q6.2 季度复盘 vs 月度 metrics vs 周报 区别?

---

## 7. 关联文档

- `feedback/attachments/FB-0008-patches/` · delegates 字段
- `feedback/attachments/FB-0009-patches/` · delegate 字段
- `feedback/attachments/FB-0011-patches/README.md` · 变量作用域铁律
- `feedback/attachments/FB-0012-patches/README.md` · submitType 拓扑
- `docs/flow.md` (修订待 apply)
- `docs/AGENTS.md` (修订待 apply)
- `docs/known-issues.md §115/§116` (新增待 apply)

---

⏱️ Last updated: 2026-10-16 (W43 Day 4) · FAQ v0.1 draft
