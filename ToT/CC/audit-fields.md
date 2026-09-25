# Audit Fields · 审计日志字段手册

> **读者**：04 运维 + 内部审计员
> **数据源**：`/api/admin/trace` + `/api/admin/trace/spans/{trace_id}`

---

## 1. 链路追踪字段

`GET /api/admin/trace?limit=20` 返回：

```json
{
  "spans": [
    {
      "trace_id": "abc123def456",
      "span_id": "span-001",
      "parent_id": null,
      "operation": "POST /wf/processInstance/startAndExecute",
      "operator": "user1",
      "args": {"processDefineId": 42, "operator": "user1", "args": {...}},
      "result": {"code": 0, "msg": "成功", "data": {...}},
      "started_at": "2026-09-25T09:00:00Z",
      "duration_ms": 245,
      "status": "ok"
    }
  ]
}
```

| 字段 | 类型 | 含义 |
|---|---|---|
| `trace_id` | string | 整个请求链路的唯一 ID |
| `span_id` | string | 当前 span 的 ID |
| `parent_id` | string\|null | 父 span ID（嵌套调用） |
| `operation` | string | 动作名（如 `processTask/execute`） |
| `operator` | string | 操作人工号 |
| `args` | object | 输入参数（敏感字段可能脱敏）|
| `result.code` | int | 0=成功，其他=失败 |
| `result.msg` | string | 结果消息 |
| `started_at` | string (ISO) | 开始时间 |
| `duration_ms` | int | 耗时（毫秒）|
| `status` | string | `ok` / `error` |

---

## 2. 高敏操作清单（必须留痕）

### 2.1 委派（delegate）

**operation**：`POST /wf/processTask/delegate`

**args 关键字段**：
- `processTaskId`：被委派的 task ID
- `operator`：原审批人
- `targetUserId`：被委派人 ⚠️ 不是 `assignee`

**result.code**：0=成功；非 0=失败

**审计关注**：
- 谁委派给谁
- 委派频率（某审批人是否经常委派 → 可能不负责任）
- 委派后 task 流向（→ KPI 5 委派率）

**关联查询**：
```bash
# 查某 task 的委派历史
curl -sX POST http://localhost:8102/wf/processTask/delegateHistory \
  -d '{"processTaskId":12345}' | jq
```

### 2.2 转办（transfer）

**operation**：当前为手动修改 processDefine，无独立 API
**审计方式**：查 `processDesign` 表的 `updated_by` + `updated_at`

**审计关注**：
- 修改人是谁
- 修改前后参与者解析差异

### 2.3 驳回（reject）

**operation**：`POST /wf/processTask/execute`（`submitType=REJECT`）

**args 关键字段**：
- `processTaskId`
- `submitType`: `REJECT` / `REJECT_TO_START` / `REJECT_TO_NODE`
- `comment`：驳回意见

**审计关注**：
- 驳回到哪个节点
- 驳回意见文本
- 驳回频率（某审批人是否经常驳回 → KPI 4 驳回率）

### 2.4 撤回（withdraw）

**operation**：`POST /wf/processInstance/withdraw`

**args 关键字段**：
- `processInstanceId`
- `operator`：发起人

**审计关注**：
- 撤回时间（发起后多久撤回 → 提示申请质量）
- 撤回原因（如果 args.comment 有）

---

## 3. 按 operator 查审计

**查某人最近操作**：
```bash
curl -s "http://localhost:8102/api/admin/trace?limit=100" | \
  jq '.spans[] | select(.operator == "user1")'
```

**查某人所有驳回**：
```bash
curl -s "http://localhost:8102/api/admin/trace?limit=100" | \
  jq '.spans[] | select(.operator == "user1") | select(.operation | contains("reject"))'
```

---

## 4. 按 processInstance 查全链路

**入口**：
```bash
# 1. 找 processInstance 的 trace_id
curl -s "http://localhost:8102/api/admin/trace?processInstanceId=1001&limit=50" | jq

# 2. 看完整 span
curl -s "http://localhost:8102/api/admin/trace/spans/abc123def456" | jq
```

**典型链路**：
```
POST /wf/processInstance/startAndExecute (root)
  └─ POST /wf/processTask/create (child)
  └─ POST /wf/processTask/execute (child)
            └─ POST /wf/processInstance/getAssigneeTextData
```

---

## 5. 审计常见查询

### 5.1 上季度谁委派最多？

```sql
-- 假设有 processTaskDelegateLog 表
SELECT operator, COUNT(*) as delegate_count
FROM process_task_delegate_log
WHERE created_at >= now() - interval '90 days'
GROUP BY operator
ORDER BY delegate_count DESC
LIMIT 10;
```

### 5.2 上季度驳回率最高的流程？

```sql
SELECT 
  pi.process_define_id,
  pd.name,
  COUNT(*) FILTER (WHERE pi.state = 'REJECTED') * 1.0 / COUNT(*) as reject_rate
FROM process_instance pi
JOIN process_define pd ON pi.process_define_id = pd.id
WHERE pi.started_at >= now() - interval '90 days'
GROUP BY pi.process_define_id, pd.name
ORDER BY reject_rate DESC
LIMIT 10;
```

### 5.3 异常操作（深夜 0-6 点提交）

```sql
SELECT operator, COUNT(*) as night_count
FROM process_instance
WHERE EXTRACT(HOUR FROM started_at) BETWEEN 0 AND 6
GROUP BY operator
ORDER BY night_count DESC
LIMIT 10;
```

---

## 6. 权限管理

**接口权限**（`main_common.py`）：
- `/api/admin/*`：需管理员 token
- `/wf/*`：业务端，按 operator 校验
- `/healthz` / `/version` / `/metrics`：公开

**审计日志权限**：
- `/api/admin/trace`：管理员
- 业务操作 trace：仅 operator 本人 + 管理员

---

## 7. 季度审计 checklist

- [ ] 导出全量 trace 到审计库（建议保留 1 年）
- [ ] 跑异常模式扫描（深夜操作 / 短时间高频操作）
- [ ] 委派率 / 驳回率分析（参考 KPI 字典）
- [ ] 检查权限变更日志
- [ ] 检查 schema 变更（processDefine 修改）
- [ ] 检查敏感操作（admin/expire/scan 调用频率）

---

**版本**：v1.11.1 · **来源**：故事 001（陈 DBA 准备季度审计 + 04 plan A3）→ 04 persona review