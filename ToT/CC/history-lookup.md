# History Lookup · 任务历史找回

> **读者**：所有参与者
> **场景**：员工想看「我请过几次假」「上次请几天」「谁委派给我」

---

## 4 个历史查询 API

依据 `vendor/jeeflow/facade.py`：

| # | API | 函数位置 | 用途 |
|---|---|---|---|
| 1 | `/wf/processTask/todoList` | facade.py:599 | **当前**待办（不算历史）|
| 2 | `/wf/processTask/doneList` | facade.py:654 | **我已完成**的任务 |
| 3 | `/wf/processTask/delegateHistory` | facade.py:2036 | **委派历史** |
| 4 | `/wf/processInstance/approvalRecord` | facade.py:1405 | **审批记录**（按 instance）|

---

## 1 · 我发起的实例

**API**：暂无独立 endpoint；通过 `processInstance/page` 过滤

**临时方案**（待补 endpoint）：
```bash
# 在 PG 直接查
SELECT id, process_define_id, started_at, ended_at, state
FROM process_instance
WHERE started_by = 'user1'
ORDER BY started_at DESC
LIMIT 50;
```

**前端展示**：等 ToT/CC 路线图完成后由前端调用

---

## 2 · 我审批过的（doneList）

**API**：`POST /wf/processTask/doneList`

```bash
curl -sX POST http://localhost:8101/wf/processTask/doneList \
  -H "Content-Type: application/json" \
  -d '{"operator":"user1","limit":20}' | jq
```

**返回**：
```json
{
  "code": 0,
  "data": [
    {
      "id": 12340,
      "processInstanceId": 1001,
      "processDefineName": "请假",
      "applicant": "user2",
      "submitType": "AGREE",
      "comment": "同意",
      "completedAt": "2026-09-20T15:30:00Z",
      "duration": 3600
    }
  ]
}
```

**过滤参数**：
- `operator`：工号（必填）
- `limit`：返回条数
- `processDefineId`：按流程过滤
- `submitType`：按结果过滤（`AGREE` / `REJECT` / `JUMP`）

---

## 3 · 委派历史（delegateHistory）

**API**：`POST /wf/processTask/delegateHistory`（BDD #1106, FIX-T74）

```bash
curl -sX POST http://localhost:8101/wf/processTask/delegateHistory \
  -H "Content-Type: application/json" \
  -d '{"processTaskId":12345}' | jq
```

**返回**：
```json
{
  "code": 0,
  "data": [
    {
      "id": 1,
      "processTaskId": 12345,
      "fromUser": "leader1",
      "toUser": "leader2",
      "createdAt": "2026-09-25T09:45:00Z",
      "comment": "周三出差"
    }
  ]
}
```

---

## 4 · 审批记录（approvalRecord）

**API**：`POST /wf/processInstance/approvalRecord`

```bash
curl -sX POST http://localhost:8101/wf/processInstance/approvalRecord \
  -H "Content-Type: application/json" \
  -d '{"processInstanceId":1001}' | jq
```

**返回**：
```json
{
  "code": 0,
  "data": [
    {"nodeName": "lead_approve", "operator": "leader1", "submitType": "AGREE", "comment": "同意", "createdAt": "..."},
    {"nodeName": "dept_approve", "operator": "dept_leader", "submitType": "REJECT_TO_START", "comment": "数据有误", "createdAt": "..."},
    {"nodeName": "lead_approve", "operator": "leader1", "submitType": "AGREE", "comment": "已修正", "createdAt": "..."}
  ]
}
```

**用途**：
- 看流程全链路审批记录
- 包含驳回 → 重提 → 通过 的完整轨迹

---

## 5 · 我的所有活动（拼装）

```bash
# 我发起的 + 我审批过的 + 委派给我的 + 抄送给我的
USER="user1"
{
  echo "=== 待办 ==="
  curl -sX POST http://localhost:8101/wf/processTask/todoList \
    -d "{\"operator\":\"$USER\"}" | jq

  echo "=== 已审批 ==="
  curl -sX POST http://localhost:8101/wf/processTask/doneList \
    -d "{\"operator\":\"$USER\",\"limit\":20}" | jq
} | less
```

---

## 6 · 时间范围 + 状态过滤

**没有直接的 date 过滤参数**，建议：

1. **客户端过滤**（jq）：
   ```bash
   curl -sX POST http://localhost:8101/wf/processTask/doneList \
     -d '{"operator":"user1","limit":100}' | \
     jq '.data[] | select(.completedAt > "2026-09-01")'
   ```

2. **PG 直接查**（更精确）：
   ```sql
   SELECT id, process_instance_id, completed_at
   FROM process_task
   WHERE operator = 'user1'
     AND completed_at BETWEEN '2026-09-01' AND '2026-09-30'
   ORDER BY completed_at DESC;
   ```

---

## 7 · 缺失能力（建议补 endpoint）

| 缺失 | 建议 endpoint |
|---|---|
| 我发起的实例列表 | `POST /wf/processInstance/myStarted` |
| 委派给我的列表 | `POST /wf/processTask/delegatedToMe` |
| 抄送给我的列表 | `POST /wf/processTask/ccToMe` |
| 时间范围过滤参数 | `startDate` / `endDate` |

**跟踪**：已在 03 plan 中列为未来动作

---

## 8 · 历史找回 FAQ

### 8.1 我怎么知道被谁委派了？

```bash
curl -sX POST http://localhost:8101/wf/processTask/delegateHistory \
  -d '{"processTaskId":<你的 task ID>}' | jq
```

### 8.2 我怎么查上个月的请假记录？

```bash
curl -sX POST http://localhost:8101/wf/processTask/doneList \
  -d '{"operator":"user1","limit":100}' | \
  jq '.data[] | select(.completedAt | startswith("2026-08"))'
```

### 8.3 抄送给我的记录怎么找？

目前无独立 endpoint；查 `/wf/processInstance/ccList`：
```bash
curl -sX POST http://localhost:8101/wf/processInstance/ccList \
  -d '{"operator":"user1","limit":50}' | jq
```

---

**版本**：v1.11.5 · **来源**：03 plan A5 W4 末 · 故事 001（T5 小李查历史）