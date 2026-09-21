# Month 2 启动清单 · W44 (2026-10-20 ~ 10-26) 启动准备

> **Month 2**: 2026-10-22 ~ 2026-11-22
> **核心目标**: auto-assignee-by-org + FAQ 文档 + 1 个新流程模式
> **本周 (W43 Day 3)**: 启动清单 + auto-assignee-by-org 方案 v0.1
> **Month 2 启动日**: 2026-10-22 (W44 Day 3 / 周三)
> **状态**: ✅ **published v1.0** (2026-10-22 Month 2 正式启动日)

---

## 1. Month 2 启动清单 (5 项)

| # | 项目 | 状态 | 备注 |
|---|------|------|------|
| 1 | auto-assignee-by-org 方案 v0.1 | ✅ W43 Day 3 (本文件 §2) | 起草就绪 |
| 2 | FAQ 文档 v0.1 | 🟡 W43 Day 4 | 起草 |
| 3 | top-N 客户反馈驱动流程模式 | 🔵 W44 Day 1-3 | Month 2 Week 1 |
| 4 | BDD 18xx 系列 (auto-assignee-by-org 回归测试) | 🔵 W44 Day 4-5 | Month 2 Week 1 |
| 5 | 月度 metrics 11 月 (W46 Day 3) | 🔵 11 月初 | Month 2 Week 3 |

---

## 2. auto-assignee-by-org 方案 v0.1

### 2.1 来源

- **来源**: FB-0006 (C-flowuser, L2 用户)
- **提出时间**: 2026-09-15 (Phase 8 期间)
- **场景**: 流程发起人不需要手动选择 assignee, 引擎按"流程所在组织"自动分配
- **优先级**: P1 (高频场景, 影响 ≥ 50% 流程)

### 2.2 现状

| 项 | 当前状态 |
|----|----------|
| **手动 assignee** | ✅ 支持 (task.assignee 显式指定) |
| **按角色分配** | ✅ 支持 (task.candidate_groups) |
| **按表达式** | ✅ 支持 (task.assignee_expr) |
| **按组织自动分配** | ❌ 不支持 (FB-0006 缺口) |
| **标准做法** | 手动指定 assignee 或 candidate_groups |

### 2.3 设计方案 v0.1 (草案)

**目标**: 当 task 配置 `auto_assignee_by_org=true` 时, 引擎自动根据"流程实例所在组织"查找该组织下的"流程审批人", 自动填充 `task.assignee`.

**数据模型** (扩展):
```python
# 当前 (已支持)
task = {
    "id": "task-1",
    "assignee": "user-A",  # 手动指定
    "candidate_groups": ["manager"],  # 候选组
}

# 新增 (auto_assignee_by_org=true 时)
task = {
    "id": "task-1",
    "auto_assignee_by_org": True,  # 新字段
    # assignee 留空, 引擎按 org 填充
}
```

**解析逻辑** (在 engine.py):
```python
def _resolve_assignee(task, process_instance):
    if task.get("auto_assignee_by_org"):
        org = process_instance.context.get("org_id")
        # 从组织表查找该 org 的流程审批人
        approver = org_repo.get_flow_approver(org)
        return approver
    elif task.get("assignee"):
        return task["assignee"]
    elif task.get("assignee_expr"):
        return eval(task["assignee_expr"], process_instance.context)
    elif task.get("candidate_groups"):
        # 现有逻辑, 候选人池
        return None  # 候选池模式
    else:
        return None
```

**新增配置**:
- `org_repo` (组织仓库): 简单 dict 即可, 支持后续扩展为 DB
- `flow_approver` 字段: 每个 org 关联 1 个默认流程审批人

### 2.4 风险与回退

| 风险 | 缓解 |
|------|------|
| **未配置 flow_approver 的 org** | 引擎 fallback 到现有 assignee 字段 |
| **org 数据源不确定** | v0.1 用 dict, v0.2 接 DB (待 Month 3+) |
| **改动 vendor/** | 🟡 等解冻 (Month 2 内可能不解冻) |

### 2.5 Month 2 推进策略

| 周 | 动作 |
|----|------|
| W44 (Week 1) | 方案 v0.1 + tdd/1801 (用例设计) |
| W45 (Week 2) | 引擎实现 (需解冻) + bdd/18xx |
| W46 (Week 3) | FAQ 文档 + 月度 metrics 11 月 |
| W47 (Week 4) | Month 2 收官 + top-N 流程模式启动 |

**关键依赖**: W45 改 vendor/ 需要 bro 签解冻.
如不解冻, Month 2 进度受阻, 但**文档/tdd/bdd 部分仍可推进**.

### 2.6 与 FB 闭环的关系

- **FB-0006**: auto-assignee-by-org 提案 (已归档, status: closed)
- **新 FB**: 暂不开, 等引擎实现后再开 1 个 FB 跟踪实施
- **闭环策略**: 实施完成后, 再开 1 个 "auto-assignee-by-org 实施完成" FB

---

## 3. FAQ 文档计划 (W43 Day 4 起草)

### 3.1 FAQ 来源 (已闭环 FB)

| FB | 标题 | 提炼为 FAQ? |
|----|------|-------------|
| FB-0006 | auto-assignee-by-org 需求 | ✅ "为什么 assignee 字段是手动?" |
| FB-0008 | 文档缺口 (delegates 字段) | ✅ "如何配置 delegates?" |
| FB-0009 | 文档缺口 (delegate 字段) | ✅ "delegate 与 assignee 区别?" |
| FB-0010 | 验证 (a) 设计如此 (设计决策) | ✅ "为什么某处 '设计如此'?" |
| FB-0011 | 变量作用域铁律 | ✅ "变量作用域规则是什么?" |
| FB-0012 | submitType 拓扑陷阱 | ✅ "submitType 在哪些拓扑下生效?" |

### 3.2 FAQ v0.1 大纲

```markdown
# jeeflow 流程设计 FAQ

## 1. 节点配置类
- Q1.1: assignee / candidate_groups / assignee_expr 何时用?
- Q1.2: delegate 与 assignee 区别?
- Q1.3: auto-assignee-by-org 何时启用?

## 2. 拓扑类
- Q2.1: countersign 节点 submitType 与拓扑关系?
- Q2.2: decision 节点 expr 与 submitType 区别?
- Q2.3: parallel gateway 何时用, 何时用 countersign?

## 3. 变量作用域类
- Q3.1: 流程变量在 task → decision 是否共享?
- Q3.2: 跨节点的变量如何传递?
- Q3.3: 变量作用域铁律 (FB-0011)

## 4. 设计决策类
- Q4.1: 为什么某处 "设计如此"?
- Q4.2: 引擎不修改 vendor 的边界在哪里?
- Q4.3: 客户反馈驱动的改进 vs 工程师想象的增强?

## 5. 工程实践类
- Q5.1: 流程 ndjson 如何解读?
- Q5.2: 引擎日志如何定位 BUG?
- Q5.3: Phase 9 反馈闭环流程?
```

---

## 4. Month 2 Week 1 (W44) 详细计划

### Day 1 (周一 2026-10-20) · Month 2 启动

- [ ] 写 W44 周报
- [ ] Month 2 正式启动仪式 (本启动清单 published)
- [ ] 跟踪 bro 解冻提案状态 (第 3 次询问)

### Day 2 (周二 2026-10-21)

- [ ] auto-assignee-by-org 方案 v0.2 (基于 Day 1 反馈)
- [ ] tdd/1801-auto-assignee-by-org.json 用例

### Day 3 (周三 2026-10-22) · Month 2 正式启动日

- [ ] auto-assignee-by-org 引擎实现 (需解冻)
- [ ] bdd/1801-auto-assignee-by-org-mem.sh
- [ ] bdd/1801-auto-assignee-by-org-pg.sh
- [ ] metrics W43 周统计

### Day 4 (周四 2026-10-23)

- [ ] auto-assignee-by-org 集成测试
- [ ] C-001 阶段 6 跟踪 (Day 31)

### Day 5 (周五 2026-10-24)

- [ ] 写 W45 周报
- [ ] auto-assignee-by-org README
- [ ] 月度 metrics 10-22 提交

### Weekend

- [ ] 整理 Week 1 沉淀

---

## 5. Month 2 关键监控指标

| 指标 | 阈值 | 触警 |
|------|------|------|
| auto-assignee-by-org 闭环 | W47 内 | 未达 → 复盘 |
| FAQ v1.0 published | W46 内 | 未达 → 复盘 |
| top-N 流程模式 | W47 内 | 未达 → 复盘 |
| bro 解冻签 | Week 1 Day 1 | 未签 → 跟踪 |
| BDD 18xx 双端 PASS | 100% | 未达 → 修 |

---

## 6. 关联文档

- `roadmap/phase9-90day-plan.md` · Phase 9 详细计划
- `weekly/2026-W43.md` · W43 周报 (本周)
- `feedback/attachments/FB-0012-patches/README.md` · FB-0012 草稿
- `proposals/UNFREEZE-PROPOSAL-2026-09-22.md` · 解冻提案
- `proposals/UNFREEZE-TRACKING-2026-10-13.md` · 第 2 次询问记录

---

⏱️ Last updated: 2026-10-15 (W43 Day 3) · Month 2 启动清单 v0.1
