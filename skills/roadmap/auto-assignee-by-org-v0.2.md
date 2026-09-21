# auto-assignee-by-org 方案 v0.2

> **起草日期**: 2026-10-21 (W44 Day 2)
> **基于**: v0.1 (W43 Day 3 起草) + W43 反馈
> **来源**: FB-0006 (C-flowuser, L2 用户)
> **状态**: 🟡 v0.2 draft, 待 W44 Day 3 review + Day 4 实施

---

## 1. v0.1 → v0.2 改动

| 改动 | 说明 |
|------|------|
| **数据模型明确** | `org.flow_approver` 改为 `org.flow_approvers` (支持多个审批人) |
| **回退策略细化** | 引擎 fallback 顺序: org.flow_approvers > assignee > assignee_expr > candidate_groups |
| **新增 candidates 模式** | 多个审批人 → candidate_groups (而非单 assignee) |
| **新增单元测试场景** | tdd/1801 列出 5 个测试场景 |
| **错误处理** | 缺 org / 缺 flow_approver → 明确错误码 (E1801 / E1802) |

---

## 2. 数据模型 v0.2

### 2.1 task 节点配置

```python
# 现有 (v0.1)
task = {
    "id": "task-1",
    "assignee": "user-A",  # 手动
    "candidate_groups": ["manager"],
}

# 新增 (v0.2 · auto-assignee-by-org)
task = {
    "id": "task-1",
    "auto_assignee_by_org": True,  # 新字段 (布尔)
    # 其他字段留空, 引擎按 org 填充
}

# 混合模式 (v0.2 新增 · 优先级最高)
task = {
    "id": "task-1",
    "auto_assignee_by_org": True,
    "fallback_assignee": "user-B",  # org 解析失败时回退
}
```

### 2.2 组织数据

```python
# 内存仓库 (v0.2 实现)
org_repo = {
    "org-A": {
        "name": "总部",
        "flow_approvers": ["user-1", "user-2"],  # 多个审批人 (v0.2 新增)
        "fallback_chain": ["user-3", "user-4"],   # 备用链 (v0.2 新增)
    },
    "org-B": {
        "name": "分公司",
        "flow_approvers": ["user-5"],
        "fallback_chain": ["user-6"],
    },
}
```

### 2.3 流程实例上下文

```python
# 流程实例 context (已有)
process_instance.context = {
    "org_id": "org-A",
    "initiator": "user-X",
    "vars": {...},
}

# 新增 (v0.2 · 引擎自动填充)
process_instance.context["resolved_assignees"] = [...]  # 解析结果
```

---

## 3. 引擎解析逻辑 v0.2

```python
def _resolve_assignees(task, process_instance):
    """v0.2 解析逻辑 (按优先级回退)"""
    
    # 优先级 1: auto_assignee_by_org
    if task.get("auto_assignee_by_org"):
        org_id = process_instance.context.get("org_id")
        if not org_id:
            raise EngineError("E1801", "auto_assignee_by_org=True but no org_id in context")
        
        org = org_repo.get(org_id)
        if not org:
            # 优先级 1.5: fallback_assignee
            if task.get("fallback_assignee"):
                return [task["fallback_assignee"]]
            raise EngineError("E1802", f"org {org_id} not found in repo")
        
        approvers = org.get("flow_approvers", [])
        if approvers:
            # 多个 → candidate_groups 模式
            return {"candidate_groups": approvers, "source": "auto_by_org"}
        else:
            # 优先级 1.6: fallback_chain
            fallback = org.get("fallback_chain", [])
            if fallback:
                return {"candidate_groups": fallback, "source": "auto_by_org_fallback"}
            # 优先级 1.7: fallback_assignee
            if task.get("fallback_assignee"):
                return [task["fallback_assignee"]]
            raise EngineError("E1803", f"org {org_id} has no flow_approvers")
    
    # 优先级 2: assignee (显式)
    if task.get("assignee"):
        return [task["assignee"]]
    
    # 优先级 3: assignee_expr (表达式)
    if task.get("assignee_expr"):
        result = eval(task["assignee_expr"], process_instance.context)
        return [result] if isinstance(result, str) else result
    
    # 优先级 4: candidate_groups (候选池)
    if task.get("candidate_groups"):
        return {"candidate_groups": task["candidate_groups"], "source": "manual"}
    
    # 全部为空
    return None  # 引擎警告: task 无 assignee
```

---

## 4. 错误码 v0.2

| 错误码 | 触发条件 | 引擎动作 |
|--------|----------|----------|
| **E1801** | `auto_assignee_by_org=True` 但 context 无 `org_id` | 抛异常, 流程卡住 |
| **E1802** | `org_id` 不在 `org_repo` 中, 无 `fallback_assignee` | 抛异常, 流程卡住 |
| **E1803** | `org.flow_approvers` 和 `fallback_chain` 都为空, 无 `fallback_assignee` | 抛异常, 流程卡住 |
| **E1804** (新) | 全部解析路径失败, 最终返回 None | 引擎警告, task 进入"无人处理"状态 |
| **E1805** (新) | assignee_expr 表达式执行异常 | 抛异常, 流程卡住 |

---

## 5. tdd/1801-auto-assignee-by-org.json · 5 个测试场景

```json
{
  "tdd_id": "1801",
  "title": "auto-assignee-by-org 流程模式",
  "version": "v0.2",
  "scenarios": [
    {
      "id": "S1",
      "title": "单 org · 单 approver",
      "setup": {
        "org_repo": {"org-A": {"flow_approvers": ["user-1"]}},
        "task": {"id": "task-1", "auto_assignee_by_org": true},
        "process_instance": {"context": {"org_id": "org-A"}}
      },
      "expected": {
        "resolved_assignees": ["user-1"],
        "source": "auto_by_org"
      }
    },
    {
      "id": "S2",
      "title": "单 org · 多 approver → candidate_groups",
      "setup": {
        "org_repo": {"org-A": {"flow_approvers": ["user-1", "user-2"]}},
        "task": {"id": "task-1", "auto_assignee_by_org": true},
        "process_instance": {"context": {"org_id": "org-A"}}
      },
      "expected": {
        "candidate_groups": ["user-1", "user-2"],
        "source": "auto_by_org"
      }
    },
    {
      "id": "S3",
      "title": "org 不存在 · fallback_assignee",
      "setup": {
        "org_repo": {},
        "task": {
          "id": "task-1",
          "auto_assignee_by_org": true,
          "fallback_assignee": "user-X"
        },
        "process_instance": {"context": {"org_id": "org-MISSING"}}
      },
      "expected": {
        "resolved_assignees": ["user-X"]
      }
    },
    {
      "id": "S4",
      "title": "org 存在但无 approver · fallback_chain",
      "setup": {
        "org_repo": {"org-A": {"flow_approvers": [], "fallback_chain": ["user-3"]}},
        "task": {"id": "task-1", "auto_assignee_by_org": true},
        "process_instance": {"context": {"org_id": "org-A"}}
      },
      "expected": {
        "candidate_groups": ["user-3"],
        "source": "auto_by_org_fallback"
      }
    },
    {
      "id": "S5",
      "title": "全部为空 · E1803 异常",
      "setup": {
        "org_repo": {"org-A": {}},
        "task": {"id": "task-1", "auto_assignee_by_org": true},
        "process_instance": {"context": {"org_id": "org-A"}}
      },
      "expected_error": {
        "code": "E1803",
        "message_contains": "org org-A has no flow_approvers"
      }
    }
  ]
}
```

---

## 6. 实施计划

### 6.1 解冻后路径 (W45 Day 1-2)

1. 修改 `vendor/jeeflow/engine.py` `_resolve_assignees` 函数 (新增 v0.2 逻辑)
2. 新增 `vendor/jeeflow/org_repo.py` (内存仓库)
3. 新增错误码常量 E1801-E1805
4. tdd/1801 published v0.2 (本文件)
5. bdd/1801-mem.sh 双端测试
6. bdd/1801-pg.sh 双端测试

### 6.2 不解冻路径 (W45 仅文档层)

1. 方案 v0.2 published (本文件)
2. FAQ v0.2 扩展 (新增 Q1.4 auto-assignee-by-org FAQ)
3. 流程模式示例文档 (`flows/auto-assignee-by-org-example.md`)
4. tdd/1801 用例设计就绪 (待实施)
5. bdd/1801 设计文档就绪 (待实施)
6. W47 Day 5 收官: 等解冻再实施

---

## 7. 与已有 FB 的关系

| FB | 关联 |
|----|------|
| **FB-0006** | auto-assignee-by-org 提案 (已闭环) |
| **新 FB (待开)** | 实施完成后, 开 1 个 FB 跟踪 (post-Phase 9) |

---

## 8. 关联文档

- `feedback/attachments/FB-0006-patches/` · FB-0006 提案附件
- `roadmap/month2-launch-checklist.md` · Month 2 启动清单
- `feedback/FAQ.md` · FAQ v0.1 (待扩展 v0.2)
- `proposals/UNFREEZE-PROPOSAL-2026-09-22.md` · 解冻提案

---

⏱️ Last updated: 2026-10-21 (W44 Day 2) · auto-assignee-by-org 方案 v0.2
