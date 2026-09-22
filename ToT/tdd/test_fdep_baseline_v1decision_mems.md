# FDEP Baseline v1 · 含 Decision Mems · 2026-09-22

> **核心**：验证每个 task 的 **decision mems**（reason + memo + context）能通过 execute body 透传到 `wf_process_task.variable`
> **依据**：`ToT/flows/fdep/RESPONSES.md §0 Decision Mem 协议 v1.0 lite`

---

## 1. 协议摘要

每个 `processTask/execute` body 必须含：

| 字段 | 类型 | 必填 | 用途 |
|------|------|------|------|
| `decision_reason` | str | ✅ | 决策理由（人审看） |
| `decision_memo` | dict | ❌ | 节点特定的决策细节 |
| `context` | dict | ❌ | 上下文（天气/团队/外部） |

引擎代码位置：`vendor/jeeflow/facade.py:713`

```python
flow_args = {k: v for k, v in args.items() if k not in ("processTaskId", "operator")}
flow_args["submitType"] = submit_type
```

---

## 2. 测试执行

| 实例 ID | 时间 | 流程 | 发起 |
|--------|------|------|------|
| 92207862268963 | 2026-09-22 ~11:14 | fdep v0.6.1 | `startAndExecute` by `u_fdp_pm` |

**触发**：AI agent 通过 curl 依次推进 6 阶段，每个 task 都附 decision mems。

---

## 3. Decision Mems 回查（核心证据）

| Task | decision_reason | decision_memo (key fields) | context (key fields) |
|------|------------------|------------------------------|------------------------|
| stage_intake | (auto) | — | — |
| stage_pm | RML 完整：5 段齐全 | rml_path, rml_length_lines=50, key_requirements | rml_drafted_by=AI, draft_duration_min=5 |
| stage_design | 架构清晰 | arch_path, api_count=3, key_decisions=[snaker:decision_intake, default_edge] | architect=AI, design_duration_hours=0.1 |
| stage_dev | 代码 + 单测完成 | commit_hash=demo-v2, test_coverage_pct=100 | developer=AI, lines_changed=0 |
| stage_review | 评审通过 | r6_auto_passed=true, r3_human_signed=true, issues_found=0 | reviewer=u_fdp_pm |
| stage_feedback | 反馈沉淀完成 | issues_path, kb_entries, feedback_count=1 | knowledge_admin=u_fdp_pm, knowledge_owner=R5 |

**统计**：5/6 task 含完整 decision mems（stage_intake 是 auto，预期无 mem）

---

## 4. 验证结论

✅ **Decision Mem 协议 v1.0 lite 落地验证通过**

1. **引擎透传 OK**：`wf_process_task.variable` 正确存储所有额外字段
2. **节点决策可追溯**：每个 task 都有 reason + memo + context
3. **协议 lite**：3 字段足够覆盖审计需求
4. **stage_intake 例外**：自动完成的 task 不传 mem（与协议预期一致）

## 5. 关联

- `ToT/flows/fdep/RESPONSES.md` §0 Decision Mem 协议 v1.0
- `ToT/flows/fdep/RESPONSES.md` §2-8 每节点 Decision Mem 模板
- `vendor/jeeflow/facade.py:713` 引擎透传实现

## 6. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1 | 2026-09-22 | 初稿：用户口头指令"i can't seed desition mem data for each node ... i always need the test report show me this point"驱动。发现引擎透传能力（facade.py:713），设计 Decision Mem 协议 v1.0 lite（3 字段），在 RESPONSES.md 每节点加 Decision Mem 模板，重跑完整 demo cycle 验证 5/6 task 含完整 mems。 |
