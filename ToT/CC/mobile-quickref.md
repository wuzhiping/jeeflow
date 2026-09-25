# Mobile Quickref · 手机 30 秒审批

> **读者**：在外的审批人
> **场景**：出差路上收到钉钉通知，需要 30 秒内决定同意 / 驳回

---

## 前提

本仓**无移动端 UI**（`PRD.md §3「不做什么」`），但 CLI 在手机上完全可用。

**最低要求**：
- SSH 到跳板机（公司提供）
- 或 Termux + SSH 客户端（Android）
- 或 Blinksh（iOS）

---

## 30 秒流程

### Step 1 · 查待办（5 秒）

```bash
ssh user@jump
jftodo
```

输出示例：
```json
[
  {"id": 12345, "processDefineName": "请假", "applicant": "user1", "args": {"days": 3}, "createdAt": "..."},
  {"id": 12346, "processDefineName": "报销", "applicant": "user2", "args": {"amount": 500}, "createdAt": "..."}
]
```

### Step 2 · 同意 task（5 秒）

```bash
jfok 12345
```

或带意见：
```bash
jfok 12345 -m "同意，注意按规章补交发票"
```

### Step 3 · 驳回（10 秒）

```bash
jfreject 12345 "金额过大，建议重写"
```

### Step 4 · 委派（5 秒）

```bash
jfdelegate 12345 user2
# （需先在 .bashrc 定义 jfdelegate，见下方）
```

---

## 必须配置的 shell 函数

把以下贴到 `~/.bashrc`（每台服务器 + 每台手机）：

```bash
# === jeeFlow 移动 CLI ===

JEEFLOW_URL="${JEEFLOW_URL:-http://localhost:8101}"

jftodo() {
  curl -sX POST "$JEEFLOW_URL/wf/processTask/todoList" \
    -H "Content-Type: application/json" \
    -d "{\"operator\":\"${USER}\"}" | jq -r '.[] | "\(.id)\t\(.processDefineName)\t\(.applicant)"' | column -t
}

jfok() {
  local task_id=$1
  local msg="${2:-同意}"
  curl -sX POST "$JEEFLOW_URL/wf/processTask/execute" \
    -H "Content-Type: application/json" \
    -d "{\"processTaskId\":$task_id,\"operator\":\"${USER}\",\"submitType\":\"AGREE\",\"comment\":\"$msg\"}" | jq
}

jfreject() {
  local task_id=$1
  local msg="${2:-驳回}"
  curl -sX POST "$JEEFLOW_URL/wf/processTask/execute" \
    -H "Content-Type: application/json" \
    -d "{\"processTaskId\":$task_id,\"operator\":\"${USER}\",\"submitType\":\"REJECT\",\"comment\":\"$msg\"}" | jq
}

jfdelegate() {
  local task_id=$1
  local target=$2
  curl -sX POST "$JEEFLOW_URL/wf/processTask/delegate" \
    -H "Content-Type: application/json" \
    -d "{\"processTaskId\":$task_id,\"operator\":\"${USER}\",\"targetUserId\":\"$target\"}" | jq
}

jfhistory() {
  curl -sX POST "$JEEFLOW_URL/wf/processTask/doneList" \
    -H "Content-Type: application/json" \
    -d "{\"operator\":\"${USER}\",\"limit\":20}" | jq
}
```

加载：
```bash
source ~/.bashrc
```

---

## 快捷数字键

```bash
# 用 alias 加快速度
alias 1='jftodo'
alias o='jfok'        # o = OK
alias r='jfreject'    # r = REJECT
alias d='jfdelegate'  # d = DELEGATE
alias h='jfhistory'   # h = HISTORY
```

用法：
```bash
1               # 查待办
o 12345         # 同意 12345
r 12345 "原因"  # 驳回
d 12345 user2   # 委派给 user2
h               # 历史
```

---

## 高级 · 一次性批量处理

```bash
# 同意所有待办（不推荐，但有时需要）
for id in $(jftodo | awk '{print $1}'); do
  jfok $id
done
```

⚠️ **慎用**：批量处理可能错过重要意见，建议至少看一眼。

---

## 紧急情况：服务挂了

```bash
# 1. 检查健康
curl -s $JEEFLOW_URL/healthz | jq

# 2. 看版本
curl -s $JEEFLOW_URL/version | jq

# 3. 紧急联系运维（参考 [runbook.md §PG pool 耗尽](./runbook.md)）
```

---

## iOS / Android 推荐 App

| 平台 | App | 备注 |
|---|---|---|
| iOS | [Blink Shell](https://blink.sh/) | 支持 SSH + Mosh |
| Android | [Termux](https://termux.com/) | 免费，需装 ssh/sshpass |
| 跨平台 | [Termius](https://termius.com/) | UI 好 |

---

## 与 ToT/CC 关联

- 完整命令 → [`quickstart-card.md §高频操作`](./quickstart-card.md)
- 历史查询 → [`history-lookup.md`](./history-lookup.md)
- 决策树（出差/请假/加签）→ [`decision-tree.md`](./decision-tree.md)

---

**版本**：v1.11.5 · **来源**：03 plan A4 W3 末 · 故事 001 场景（T2 王组长出差）