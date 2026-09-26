# Quick Start Card · 5 分钟走完请假

> **读者**：第一次使用 jeeFlow 的人
> **场景**：销售部小李请 3 天年假

---

## 3 步走完

### Step 1 · 发起申请（09:00 上午）

```bash
curl -X POST http://localhost:8101/wf/processInstance/startAndExecute \
  -H "Content-Type: application/json" \
  -d '{
    "processDefineId": 42,
    "operator": "user1",
    "args": {
      "leaveType": "annual",
      "days": 3,
      "startDate": "2026-09-26",
      "reason": "family trip"
    }
  }'
```

**返回**：`{"code":0,"msg":"成功","data":{"processInstanceId":1001}}`

**字段说明**：
| 字段 | 含义 | 必填 |
|---|---|---|
| `processDefineId` | 流程定义 ID（HR 给你）| 是 |
| `operator` | 你的工号 | 是 |
| `args.leaveType` | `annual` / `sick` / `personal` | 是 |
| `args.days` | 请假天数（数字）| 是 |
| `args.startDate` | 开始日期（YYYY-MM-DD）| 是 |

### Step 2 · 等审批（09:00 - 11:00）

查看「我发起过的」进度：

```bash
curl -X POST http://localhost:8101/wf/processInstance/myStarted \
  -H "Content-Type: application/json" \
  -d '{"operator":"user1"}'
```

返回里有 `state`（`RUNNING` / `COMPLETED`）+ `currentNode`（当前在哪个审批人）。

### Step 3 · 收到结果（11:00 后）

- 状态变 `COMPLETED` → 审批通过，去 ToT/CC/history-lookup.md 看历史
- 状态变 `REJECTED` → 看 `lastRejectReason` 字段，问 HR

---

## 高频操作（如果用 CLI）

把以下贴到 `~/.bashrc`：

```bash
jfstart() {
  curl -sX POST http://localhost:8101/wf/processInstance/startAndExecute \
    -H "Content-Type: application/json" \
    -d "{\"processDefineId\":$1,\"operator\":\"$USER\",\"args\":${2:-{}}}" | jq
}

jftodo() {
  curl -sX POST http://localhost:8101/wf/processTask/todoList \
    -H "Content-Type: application/json" \
    -d "{\"operator\":\"$USER\"}" | jq
}

jfok() {
  curl -sX POST http://localhost:8101/wf/processTask/execute \
    -H "Content-Type: application/json" \
    -d "{\"processTaskId\":$1,\"operator\":\"$USER\",\"submitType\":\"AGREE\"}" | jq
}

jfreject() {
  curl -sX POST http://localhost:8101/wf/processTask/execute \
    -H "Content-Type: application/json" \
    -d "{\"processTaskId\":$1,\"operator\":\"$USER\",\"submitType\":\"REJECT\",\"comment\":\"$2\"}" | jq
}
```

用法：
```bash
jfstart 42 '{"leaveType":"annual","days":3,"startDate":"2026-09-26"}'
jftodo
jfok 12345
jfreject 12345 "需要补充材料"
```

---

## 端口对照

| 模式 | 端口 | 说明 |
|---|---|---|
| 内存（演示）| 8101 | `python3 -m uvicorn main:app --port 8101` |
| PG（生产）| 8102 | `python3 -m uvicorn main_pg:app --port 8102` |
| 健康检查 | 同端口 `/healthz` | `curl http://localhost:8101/healthz` |
| 版本查询 | 同端口 `/version` | `curl http://localhost:8101/version` |

---

## 下一步

- 出差怎么审批？ → [decision-tree.md](./decision-tree.md)
- 找不到我的待办？ → [faq.md](./faq.md) Q2
- 看历史请假？ → [history-lookup.md](./history-lookup.md)（W4 末）

---

**版本**：v1.11.1 · **来源**：故事 001（销售部小李请假 3 天）→ 03 persona review