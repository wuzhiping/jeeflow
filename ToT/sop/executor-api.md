# Executor Pickup API 设计

> 本节定义 `POST /api/executor/pickup` 端点——为执行者（人或 AI Agent）提供**一站式启动包**：
> 上一节点的 handoff + 本节点的 Job Card 全文 + execute body 模板。

---

## 1. 设计动机

当前 executor 拾起一个新 task 时，需要手动：

1. 调 `processTask/todoList` 找到 task
2. 调 `processInstance/detail` 找上一节点的 `variable.decision_memo.next_handoff`
3. 读 `next_handoff.job_card_url` 指向的本地文件
4. 手工拼接 execute body 字段

→ 步骤多、易遗漏、不利于 AI Agent 自动化。

**本 API 把这 4 步合 1 步**：调一次 → 拿到全部 docs + execute body 模板。

---

## 2. 端点定义

### `POST /api/executor/pickup`

**Request**：

```json
{
  "taskId": 92201234567890,
  "operator": "u_fdp_pm"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `taskId` | long | ✅ | 当前要拾起的 task ID（来自 `processTask/todoList`） |
| `operator` | str | ✅ | 执行者用户名（用于权限校验） |

**Response（成功）**：

```json
{
  "code": 0,
  "msg": "成功",
  "data": {
    "task": {
      "id": 92201234567890,
      "taskName": "stage_pm",
      "processInstanceId": 92201234560000,
      "operator": "u_fdp_pm",
      "taskState": 10,
      "displayName": "1. RML 立项",
      "createTime": "2026-09-22 11:42:00"
    },
    "previousHandoff": {
      "fromTask": "stage_intake",
      "decisionReason": "立项：业务诉求清晰...",
      "decisionMemo": {
        "intake_record_path": "ToT/pm/intake/2026-09-22/001.md",
        "priority": "high"
      },
      "context": {"businessNo": "DEMO-001"},
      "nextHandoff": {
        "next_node": "stage_pm",
        "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_pm.md",
        "input_files": ["ToT/pm/intake/2026-09-22/001.md"],
        "checklist": ["读 RML 5 段", "..."]
      }
    },
    "jobCard": {
      "url": "ToT/flows/fdep/job_cards/job_card_stage_pm.md",
      "absolutePath": "/opt/.../fdep/job_cards/job_card_stage_pm.md",
      "exists": true,
      "content": "# Job Card · stage_pm\n\n## 1. 你的身份\n..."
    },
    "executeTemplate": {
      "processTaskId": 92201234567890,
      "operator": "u_fdp_pm",
      "submitType": 1,
      "decision_reason": "<待填>",
      "decision_memo": {
        "<节点特定字段>": "<占位>"
      },
      "context": {"node": "stage_pm"},
      "next_handoff": {
        "next_node": "stage_design",
        "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_design.md",
        "input_files": ["ToT/pm/rml/<date>/<taskId>/<本节点产出>"]
      }
    }
  }
}
```

**Response（错误）**：

| 场景 | code | msg |
|------|------|-----|
| taskId 不存在 | 404 | `task not found: <taskId>` |
| operator 不匹配 | 403 | `operator '<op>' not authorized for task '<taskName>'` |
| task 已 DONE/REJECT | 400 | `task '<taskName>' is in state <state>, not actionable` |
| Job card 文件缺失 | 200 + warning | `data.jobCard.exists=false`, 仍返回其他字段 |

---

## 3. 实现逻辑

```
1. find_task_by_id(taskId) → t
2. 校验 t.operator == operator（或 t.actorIds 包含 operator）
3. 校验 t.taskState == DOING
4. 找前一 task: 同 instance 下，taskState == DONE 的最新 taskName
5. 解析前一 task 的 variable JSON：
   - decision_reason / decision_memo / context
   - decision_memo.next_handoff
6. 加载本 task 的 Job Card：
   - 路径约定: ToT/flows/fdep/job_cards/job_card_<taskName>.md
   - 相对 → 绝对路径转换
   - 文件不存在: warning，content=null
7. 构造 executeTemplate：
   - 复制 §5 模板字段
   - next_handoff 指向下一节点的 card
8. 返回 data dict
```

---

## 4. 与已有端点的差异

| 端点 | 用途 |
|------|------|
| `/wf/processTask/todoList` | 列出某 operator 的待办 |
| `/wf/processInstance/detail` | 查实例所有 task + variable |
| `/wf/processTask/execute` | **执行** task（提交结果） |
| **`/api/executor/pickup`** 🆕 | **拾起** task（拿 docs + 模板） |

---

## 5. 安全考虑

- **认证**：复用 `access_guard` 装饰器（与其他 `/api/*` 一致）
- **授权**：operator 必须等于 `task.operator` 或在 `task.actorIds` 中
- **不修改任何数据**：纯 GET-like（虽然 POST），不动 wf_process_task 表

---

## 6. 测试用例

| # | 场景 | 期望 |
|---|------|------|
| 1 | 合法 taskId + 匹配 operator | 200 + data 包含 4 部分 |
| 2 | 错误 operator | 403 |
| 3 | taskId 不存在 | 404 |
| 4 | task 已 DONE | 400 |
| 5 | 缺 Job Card 文件 | 200 + exists=false, warning msg |
| 6 | 前一 task 无 handoff | previousHandoff.nextHandoff=null |

---

## 7. 关联文档

- `ToT/flows/fdep/RESPONSES.md §0` — Decision Mem 协议
- `ToT/flows/fdep/job_cards/` — Job Card 文件位置
- `ToT/README.md §11` — 三环境部署
- `main_common.py:auto_deploy_fdep` — 类似模式（启动时检查 + 跳过）

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 初稿：单端点 `/api/executor/pickup`，单源信息（task + 前 handoff + job card + execute 模板） |