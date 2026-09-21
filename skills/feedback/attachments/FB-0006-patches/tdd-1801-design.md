# tdd/auto-assignee-by-org v0.2 (S1-S5)

> **tdd_id**: 1801 (auto-assignee-by-org 流程模式)
> **起草日期**: 2026-10-21 (W44 Day 2)
> **状态**: 🟡 5 个用例设计就绪, 待 W45 Day 1-2 实施 (需解冻)

## 5 个测试场景

### S1 · 单 org · 单 approver

```python
setup = {
    "org_repo": {"org-A": {"flow_approvers": ["user-1"]}},
    "task": {"id": "task-1", "auto_assignee_by_org": True},
    "process_instance": {"context": {"org_id": "org-A"}},
}
expected = {
    "resolved_assignees": ["user-1"],
    "source": "auto_by_org",
}
```

### S2 · 单 org · 多 approver → candidate_groups

```python
setup = {
    "org_repo": {"org-A": {"flow_approvers": ["user-1", "user-2"]}},
    "task": {"id": "task-1", "auto_assignee_by_org": True},
    "process_instance": {"context": {"org_id": "org-A"}},
}
expected = {
    "candidate_groups": ["user-1", "user-2"],
    "source": "auto_by_org",
}
```

### S3 · org 不存在 · fallback_assignee

```python
setup = {
    "org_repo": {},
    "task": {
        "id": "task-1",
        "auto_assignee_by_org": True,
        "fallback_assignee": "user-X",
    },
    "process_instance": {"context": {"org_id": "org-MISSING"}},
}
expected = {
    "resolved_assignees": ["user-X"],
}
```

### S4 · org 存在但无 approver · fallback_chain

```python
setup = {
    "org_repo": {"org-A": {"flow_approvers": [], "fallback_chain": ["user-3"]}},
    "task": {"id": "task-1", "auto_assignee_by_org": True},
    "process_instance": {"context": {"org_id": "org-A"}},
}
expected = {
    "candidate_groups": ["user-3"],
    "source": "auto_by_org_fallback",
}
```

### S5 · 全部为空 · E1803 异常

```python
setup = {
    "org_repo": {"org-A": {}},
    "task": {"id": "task-1", "auto_assignee_by_org": True},
    "process_instance": {"context": {"org_id": "org-A"}},
}
expected_error = {
    "code": "E1803",
    "message_contains": "org org-A has no flow_approvers",
}
```

## 关联文档

- `roadmap/auto-assignee-by-org-v0.2.md` · 完整方案 v0.2
- `roadmap/month2-launch-checklist.md` · Month 2 启动清单
- `feedback/attachments/FB-0006-patches/` · FB-0006 提案

⏱️ Last updated: 2026-10-21 (W44 Day 2)
