# auto-assignee-by-org 流程模式示例 · v0.1 (W45 Day 4)

> **起草日期**: 2026-10-22 (W45 Day 4)
> **状态**: 🟡 v0.1 起草就绪, 等 W46 Day 3 v1 published
> **关联**: FB-0006 (auto-assignee-by-org 提案) · auto-assignee-by-org 0.2 (W45 Day 2)

---

## 1. 流程模式概述

**目标**: 当 task 配置 `auto_assignee_by_org=true` 时, 引擎自动根据"流程实例所在组织"查找该组织下的"流程审批人", 自动填充 `task.assignee`.

**来源**: 客户 C-flowuser 反馈 (FB-0006, 2026-09-15). 影响 ≥ 50% 的流程发起人.

---

## 2. 示例流程 JSON

```json
{
  "name": "auto-assignee-by-org-example",
  "displayName": "按组织自动分配审批人示例",
  "type": "approval",
  "properties": {
    "variables": {
      "f_requestType": "leave",
      "f_days": 5,
      "u_userId": "user1",
      "u_orgId": "org-A"
    }
  },
  "nodes": [
    {
      "id": "start",
      "type": "snaker:start",
      "x": 100, "y": 200,
      "properties": {"width": 50, "height": 50},
      "text": {"value": "开始"}
    },
    {
      "id": "apply",
      "type": "snaker:task",
      "x": 200, "y": 200,
      "properties": {
        "width": 100, "height": 50,
        "form": "leave-form",
        "assignee": "applicant",
        "taskType": 0,
        "performType": 0
      },
      "text": {"value": "发起申请"}
    },
    {
      "id": "leader_approval",
      "type": "snaker:task",
      "x": 400, "y": 200,
      "properties": {
        "width": 100, "height": 50,
        "form": "leave-form",
        "auto_assignee_by_org": true,
        "fallback_assignee": "leader",
        "taskType": 0,
        "performType": 0
      },
      "text": {"value": "按组织自动分配审批人"}
    },
    {
      "id": "end",
      "type": "snaker:end",
      "x": 600, "y": 200,
      "properties": {"width": 50, "height": 50},
      "text": {"value": "结束"}
    }
  ],
  "edges": [
    {"id": "e0", "sourceNodeId": "start", "targetNodeId": "apply", "properties": {}},
    {"id": "e1", "sourceNodeId": "apply", "targetNodeId": "leader_approval", "properties": {}},
    {"id": "e2", "sourceNodeId": "leader_approval", "targetNodeId": "end", "properties": {}}
  ]
}
```

**关键字段**:
- `auto_assignee_by_org=true` (新字段)
- `fallback_assignee="leader"` (org 不存在时回退)
- 流程变量含 `u_orgId="org-A"` (用于查 org_repo)

---

## 3. org_repo 配置 (内存示例)

```python
# vendor/jeeflow/org_repo.py (待实施)
org_repo = {
    "org-A": {
        "name": "总部",
        "flow_approvers": ["user-1", "user-2"],   # 多审批人 → candidate_groups
        "fallback_chain": ["user-3"]                # 备用链
    },
    "org-B": {
        "name": "分公司",
        "flow_approvers": ["user-5"],                # 单审批人 → assignee
        "fallback_chain": ["user-6"]
    },
    "org-C": {
        "name": "新组织",
        "flow_approvers": [],                       # 空 → fallback_chain
        "fallback_chain": ["user-7"]
    }
}
```

---

## 4. 解析逻辑 (5 种)

### 场景 1: org 存在 + 多审批人 → candidate_groups

```python
输入: org-A + auto_assignee_by_org=true
输出: candidate_groups=["user-1", "user-2"], source="auto_by_org"
```

### 场景 2: org 存在 + 单审批人 → assignee

```python
输入: org-B + auto_assignee_by_org=true
输出: assignee="user-5", source="auto_by_org"
```

### 场景 3: org 不存在 → fallback_assignee

```python
输入: org-MISSING + auto_assignee_by_org=true + fallback_assignee="leader"
输出: assignee="leader"
```

### 场景 4: org 存在但 flow_approvers 空 → fallback_chain

```python
输入: org-C + auto_assignee_by_org=true (fallback_assignee 未设)
输出: candidate_groups=["user-7"], source="auto_by_org_fallback"
```

### 场景 5: org 存在但全部为空 → E1803 异常

```python
输入: org-D (空) + auto_assignee_by_org=true (fallback_assignee 未设)
输出: 异常 E1803 "org org-D has no flow_approvers"
```

---

## 5. 错误码 (5 种)

| 错误码 | 触发条件 | 引擎动作 |
|--------|----------|----------|
| **E1801** | `auto_assignee_by_org=true` 但 context 无 `org_id` | 抛异常 |
| **E1802** | `org_id` 不在 org_repo 且无 fallback_assignee | 抛异常 |
| **E1803** | org.flow_approvers 和 fallback_chain 都为空 | 抛异常 |
| **E1804** | 全部解析路径失败 | 引擎警告 + 进入"无人处理"状态 |
| **E1805** | assignee_expr 表达式异常 | 抛异常 |

---

## 6. 测试用例 (tdd/1801)

| # | 场景 | 期望 | 来源 |
|---|------|------|------|
| S1 | 单 org + 单 approver | assignee=user-1 | 简单流程 |
| S2 | 单 org + 多 approver | candidate_groups=[user-1, user-2] | 多候选人 |
| S3 | org 不存在 + fallback_assignee | assignee=leader | 回退 |
| S4 | org 空 + fallback_chain | candidate_groups=[user-3] | 备用链 |
| S5 | 全部为空 | E1803 异常 | 异常路径 |

详见 `roadmap/auto-assignee-by-org-v0.2.md §5`

---

## 7. BDD 回归测试 (BDD #1801)

```bash
#!/bin/bash
# bdd-1801-auto-assignee-by-org-mem.sh
# 5 个场景双端测试 (mem + pg)

set -e
HOST=http://localhost:8101
PASS=0; FAIL=0

# 场景 1: 单 org 单 approver
curl -X POST :8101/wf/processDesign/save -d '{"name":"auto-org-test-1",...}'
curl -X POST :8101/wf/processDesign/deploy -d '{"name":"auto-org-test-1"}'
# 配置 org_repo: org-A → [user-1]
# 启动流程, context org_id=org-A
# 断言: task.assignee == "user-1"
# 断言: task.source == "auto_by_org"

# (其他 4 个场景省略, 见 BDD #1801 设计)
```

**双端 PASS 标准**:
- mem 端 5/5 + pg 端 5/5 = 累计 10/10

---

## 8. 与已知现象的关联

### 8.1 与 omarchy BUG-3 区别

| 维度 | auto-assignee-by-org | omarchy BUG-3 (FB-0014) |
|------|----------------------|------------------------|
| **类型** | 功能扩展 | **真 BUG** |
| **优先级** | P1 | **P0** |
| **是否阻塞** | 否 (新功能) | **是 (引擎静默走默认边)** |
| **verify 规则** | 无 (新增字段) | W014 (omarchy 已实现) |

### 8.2 与 FB-0011 变量作用域铁律的区别

| 维度 | auto-assignee-by-org | FB-0011 |
|------|----------------------|---------|
| **解决** | "如何按组织分配" | "如何理解变量作用域" |
| **作用范围** | task 节点解析 | 全流程 |
| **时机** | Month 2 Week 1-2 实施 | 等 bro apply |

---

## 9. 实施依赖 (Month 2 Week 1-2)

### 9.1 解冻后路径

1. 修改 `vendor/jeeflow/engine.py` (`_resolve_assignees` 函数 + v0.2 逻辑)
2. 新增 `vendor/jeeflow/org_repo.py` (内存仓库)
3. 新增错误码常量 E1801-E1805
4. 实施 tdd/1801 + bdd/1801 双端 PASS
5. C-001 + C-flowuser 反馈验证

### 9.2 不解冻路径 (本示例仅文档层)

1. 本示例 published (本文件)
2. FAQ 0.2 扩展 (已补 Q1.4)
3. 流程模式示例 published (本文件)
4. 等解冻后实施 (W47+ 或 Month 3)

---

## 10. 关联文档

- `roadmap/auto-assignee-by-org-v0.2.md` · 完整方案 v0.2
- `feedback/attachments/FB-0006-patches/` · FB-0006 提案
- `feedback/attachments/FB-0006-patches/tdd-1801-design.md` · tdd 用例
- `feedback/attachments/FB-0006-patches/bdd-1801-design.md` · BDD 设计
- `feedback/FAQ.md` Q1.4 · 解析逻辑 + 回退顺序
- `proposals/UNFREEZE-PROPOSAL-2026-09-22.md` · 解冻提案

---

⏱️ Last updated: 2026-10-22 (W45 Day 4) · auto-assignee-by-org 流程模式示例 v0.1