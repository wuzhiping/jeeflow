# FDEP Baseline v2 · Pickup API + Job Card URL · 2026-09-22

> **核心**：验证 `/api/executor/pickup` 端点返回完整文档包，且每个 task 的 `next_handoff.job_card_url` 都指向真实存在的文件
> **关联**：`ToT/sop/executor-api.md` v0.1（API 设计） + `ToT/flows/fdep/job_cards/`（Job Card 仓库）

---

## 1. 验证目标

| # | 验证项 | 通过条件 |
|---|--------|----------|
| 1 | Job Card 文件齐全 | 6 张卡都存在于 `ToT/flows/fdep/job_cards/` |
| 2 | pickup API 全部节点可调 | 5 个 task 节点都返回 200 + 4 部分数据 |
| 3 | next_handoff.job_card_url 合法 | 4 个非终态节点的 URL 都指向真实文件 |
| 4 | 终态节点处理正确 | stage_feedback → end 标记 `is_terminal=true`，无 job_card_url |
| 5 | 完整流程可跑通 | instance 最终 state=20（DONE） |

---

## 2. 测试执行

| 实例 ID | 时间 | 流程 | 发起 |
|--------|------|------|------|
| 92210601465864 | 2026-09-22 ~11:55 | fdep v0.6.2 | `startAndExecute` by `u_fdp_pm` |

**触发**：`/tmp/opencode/demo_v3.py` 跑 5 节点完整循环，每个节点：pickup → execute (带 decision_reason/decision_memo/context)。

---

## 3. 验证结果

```
[1] start → instance=92210601465864

[2] 验证 job_card_url 文件存在性：
  ✓ ToT/flows/fdep/job_cards/job_card_stage_intake.md
  ✓ ToT/flows/fdep/job_cards/job_card_stage_pm.md
  ✓ ToT/flows/fdep/job_cards/job_card_stage_design.md
  ✓ ToT/flows/fdep/job_cards/job_card_stage_dev.md
  ✓ ToT/flows/fdep/job_cards/job_card_stage_review.md
  ✓ ToT/flows/fdep/job_cards/job_card_stage_feedback.md

[3] 逐节点 pickup + execute：
  ✓ stage_pm           pickup OK, card=2859B, next_url=✓
  ✓ stage_design       pickup OK, card=3027B, next_url=✓
  ✓ stage_dev          pickup OK, card=2981B, next_url=✓
  ✓ stage_review       pickup OK, card=3044B, next_url=✓
  ✓ stage_feedback     pickup OK, card=2755B, next_url=terminal

[4] final state: 20 (DONE)
[5] all next_handoff.job_card_url valid: ✅
```

---

## 4. Pickup API 响应示例（节选）

**请求**：

```json
POST /api/executor/pickup
{"taskId": 92210601468938, "operator": "u_fdp_pm"}
```

**响应 data 字段**：

```json
{
  "task": {
    "id": 92210601468938,
    "taskName": "stage_pm",
    "processInstanceId": 92210601465864,
    "operator": "u_fdp_pm",
    "taskState": 10,
    "displayName": "1. RML 立项"
  },
  "previousHandoff": {
    "fromTask": "stage_intake",
    "decisionReason": null,
    "nextHandoff": null
  },
  "jobCard": {
    "url": "ToT/flows/fdep/job_cards/job_card_stage_pm.md",
    "exists": true,
    "content": "# Job Card · stage_pm\n..."
  },
  "executeTemplate": {
    "processTaskId": 92210601468938,
    "operator": "u_fdp_pm",
    "submitType": 1,
    "next_handoff": {
      "next_node": "stage_design",
      "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_design.md",
      "input_files": ["ToT/design/<date>/<taskId>/<本节点产出>"]
    }
  }
}
```

---

## 5. 验证结论

✅ **Pickup API v0.1 落地验证通过**

1. **Job Card 仓库完整**：6 张卡齐全，§5 JSON 合法
2. **API 端点工作**：所有 5 个 task 节点都成功返回 200 + 4 部分数据
3. **next_handoff.job_card_url 全部指向真实文件**：4/4 非终态节点通过；stage_feedback → end 正确标记 terminal
4. **流程完整跑通**：instance state=20 (DONE)
5. **executeTemplate 自动构造**：executor 拿到后只需填决策字段即可 execute

## 6. 关联

- `ToT/sop/executor-api.md` v0.1 — API 设计
- `ToT/flows/fdep/job_cards/` — Job Card 仓库
- `main_common.py:executor_pickup` — 核心实现
- `main_common.py:api_executor_pickup` — 路由注册
- `ToT/tdd/test_fdep_baseline_v1decision_mems.{md,json}` — 上一个 baseline（Decision Mems 验证）

## 7. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v2 | 2026-09-22 | 初稿：实现 `/api/executor/pickup` + 验证 job_card_url 全链路；6 张 Job Card + 5 节点 pickup/execute 全通过；新增 `ToT/sop/executor-api.md` 设计文档；新增 `ToT/sop/node-execution.md` SOP 入口；新基线 `test_fdep_baseline_v2pickup_api.{md,json}` |
