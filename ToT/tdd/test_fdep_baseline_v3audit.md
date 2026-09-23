# FDEP Baseline v3 · job_card_url 审计 · 2026-09-22

> **核心**：验证 Decision Mem 协议 v1.2 lite+ `job_card_url` 审计字段
> **驱动**：用户口头指令 *"when record the mem log, recod the job_card_url also, that need be auditing also with log, need to be show in the tdd report"*
> **协议**：`ToT/flows/fdep/RESPONSES.md §0 v1.2 lite+`

---

## 1. 验证目标

| # | 验证项 | 通过条件 |
|---|--------|----------|
| 1 | 每节点 `wf_process_task.variable.job_card_url` 真实存在 | 5/5 task 文件可访问 |
| 2 | 每节点 `wf_process_task.variable.next_handoff.job_card_url` 真实存在 | 4/5 task 文件可访问 + 1/5 terminal 标记 |
| 3 | 提交值 == 引擎存储值（透传无失真） | 5/5 task |
| 4 | 审计链匹配：`T.next_handoff.jcu == next(T).job_card_url` | 4/4 链路 + 1/1 terminal |
| 5 | 流程跑到底 | instance state=20 (DONE) |

---

## 2. 测试执行

| 实例 ID | 时间 | 流程 | 发起 |
|--------|------|------|------|
| 92210956748829 | 2026-09-22 ~12:00 | fdep v0.6.2 | `startAndExecute` by `u_fdp_pm` |

**触发**：`/tmp/opencode/demo_v4.py` 跑 5 节点完整循环，每节点：
1. pickup 拿 `jobCard.url`（executor 实际用的卡）+ `executeTemplate.next_handoff`
2. execute 提交时**同时填 2 个字段**：`job_card_url` + `next_handoff`
3. 引擎透传到 `wf_process_task.variable`

---

## 3. 审计结果

### 3.1 每节点提交 vs 存储

| Task | Used (提交) | Next (提交) | Audit |
|-------|------------|-------------|-------|
| stage_pm | job_card_stage_pm.md | job_card_stage_design.md | ✓ PASS |
| stage_design | job_card_stage_design.md | job_card_stage_dev.md | ✓ PASS |
| stage_dev | job_card_stage_dev.md | job_card_stage_review.md | ✓ PASS |
| stage_review | job_card_stage_review.md | job_card_stage_feedback.md | ✓ PASS |
| stage_feedback | job_card_stage_feedback.md | terminal | ✓ PASS |

### 3.2 链路一致性

| From | next_handoff.jcu | == | To.jcu | Audit |
|------|-------------------|---|--------|-------|
| stage_pm | job_card_stage_design.md | == | stage_design.job_card_url | ✓ |
| stage_design | job_card_stage_dev.md | == | stage_dev.job_card_url | ✓ |
| stage_dev | job_card_stage_review.md | == | stage_review.job_card_url | ✓ |
| stage_review | job_card_stage_feedback.md | == | stage_feedback.job_card_url | ✓ |
| stage_feedback | terminal | == | (end).job_card_url | ✓ |

### 3.3 文件存在性

| 文件 | 大小 | 验证 |
|------|------|------|
| job_card_stage_pm.md | 3814 B | ✓ |
| job_card_stage_design.md | 4195 B | ✓ |
| job_card_stage_dev.md | 4066 B | ✓ |
| job_card_stage_review.md | 4143 B | ✓ |
| job_card_stage_feedback.md | 3819 B | ✓ |

---

## 4. Execute Body 示例（stage_pm）

```json
{
  "processTaskId": "<from todoList>",
  "operator": "u_fdp_pm",
  "submitType": 1,

  "decision_reason": "RML 5 段齐全：背景/目标/用户故事/AC/范围",
  "decision_memo": {
    "rml_path": "ToT/pm/rml/demo-v4/rml.md",
    "rml_length_lines": 50,
    "key_requirements": ["job_card_url 审计字段", "完整链路接力"]
  },
  "context": {"rml_drafted_by": "AI", "draft_duration_min": 5},

  "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_pm.md",
  "next_handoff": {
    "next_node": "stage_design",
    "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_design.md",
    "input_files": ["ToT/design/<date>/<taskId>/<本节点产出>"]
  }
}
```

**注意**：`job_card_url` 与 `next_handoff` 都是 **top-level** 字段，与 `decision_reason` 同级。

---

## 5. 审计回查（任意 instance）

```bash
# 任意 instance 的所有节点决策 + job_card_url 审计
INSTANCE="<processInstanceId>"
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/detail \
    -H "Content-Type: application/json" \
    -d "{\"id\":$INSTANCE}" | python3 -c "
import sys, json
d = json.load(sys.stdin)['data']
print(f'{\"Task\":<18s} {\"Used\":<55s} {\"Next\":<55s} Audit')
for t in d['tasks']:
    v = json.loads(t.get('variable') or '{}')
    jcu = v.get('job_card_url', 'MISSING')
    nh = v.get('next_handoff') or {}
    njcu = nh.get('job_card_url', 'terminal')
    # 审计字段缺失则标 FAIL
    audit = '✓' if jcu != 'MISSING' else '✗'
    print(f'{t[\"taskName\"]:<18s} {jcu:<55s} {njcu:<55s} {audit}')"
```

---

## 6. 验证结论

✅ **Decision Mem 协议 v1.2 lite+ `job_card_url` 审计落地验证通过**

1. **透传 OK**：引擎 `facade.py:713` 把 `job_card_url` 透传到 `wf_process_task.variable`
2. **文件可达**：所有 5 个节点提交的 job_card_url 都指向真实存在的文件
3. **链路完整**：4/4 链路匹配 + 1/1 终态节点正确标记
4. **流程跑到底**：instance state=20 (DONE)
5. **审计可见**：任何时候 `processInstance/detail` 都能查到 executor 用的是哪张卡

**审计价值**：
- **追溯责任**：每个决策用了哪份 SOP/Job Card 可查
- **文档对齐**：Job Card 更新时，能立即找出历史 instance 引用了哪版
- **质量门禁**：CI 可断言所有 instance 的 task 都含 job_card_url

## 7. 关联

- `ToT/flows/fdep/RESPONSES.md §0 v1.2 lite+` — 协议定义
- `ToT/sop/gen-job-cards.py` — 6 张卡 + §5 模板自动含 job_card_url
- `ToT/sop/executor-api.md v0.1` — pickup API 返回 jobCard.url 给 executor 复制
- `main_common.py:executor_pickup` — pickup 核心实现
- `ToT/tdd/test_fdep_baseline_v2pickup_api.{md,json}` — 上一个 baseline

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v3 | 2026-09-22 | 初稿：Decision Mem 协议 v1.2 lite+ `job_card_url` 审计字段落地；demo cycle v4 实测 instance 92210956748829，5/5 task 提交带审计字段，4/4 链路匹配，1/1 终态标记；TDD 报告展示完整审计表 + 链路一致性 + 文件存在性；新增 `ToT/tdd/test_fdep_baseline_v3audit.{md,json}` |
