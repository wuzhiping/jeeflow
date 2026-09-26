# FAQ · 异常场景 10 问

> **读者**：所有参与者
> **来源**：故事 001（小李请假）+ 客服记录 + 内部 IM 高频问题

---

## Q1 · 我点了「同意」但流程没动？

**原因 1**：`submitType` 字段名错。正确值是字符串 `AGREE` / `REJECT` / `JUMP` / `DELEGATE`，不是 `agree` / `1`（数字枚举）。

**原因 2**：task 已经超时或被其他人审批过了。先 `todoList` 看 task 是否还在。

**原因 3**：会签模式下，需要所有人同意才推进；你同意了但别人没同意。

**自检**：
```bash
curl -sX POST http://localhost:8101/wf/processTask/todoList \
  -H "Content-Type: application/json" \
  -d '{"operator":"user1"}' | jq '.[0].state'
# 返回 "TODO" → task 还在，等其他人
# 返回 null → task 不在你这里，可能被审批/委派过
```

---

## Q2 · 找不到我的待办？

**原因 1**：`operator` 字段没传或传错。必须是你的工号（字符串）。

**原因 2**：task 被委派/转办给别人了。查 `delegateHistory`。

**原因 3**：会签模式中其他会签人已经批完，task 自动消失了。

**自检**：
```bash
curl -sX POST http://localhost:8101/wf/processTask/todoList \
  -H "Content-Type: application/json" \
  -d '{"operator":"你的工号"}' | jq 'length'
# 0 → 没待办（要么批完了，要么 task 不在你这）
```

---

## Q3 · 我能驳回到申请人吗？

**答案**：可以，三种方式：
- `submitType=REJECT_TO_START`：打回到 start 节点（申请人重写）
- `submitType=REJECT_TO_NODE`：打回到中间任意节点（需引擎支持，参考 [decision-tree.md §3](./decision-tree.md)）
- 终止整个流程：`POST /wf/processInstance/terminate`（数据归档，不可恢复）

---

## Q4 · 委派后还能收回吗？

**答案**：**不能**。委派是「临时授权」，task 在对方手里处理完就结束，不会自动回你。

**变通**：
- 如果对方还没批，让他反向委派回你
- 如果对方已经批完，task 结束，只能等下次

**注意**：这是「delegate」与「transfer」的本质区别：
- delegate = 临时授权（不修改定义）
- transfer = 永久转移（修改 processDefine）

---

## Q5 · 抄送给我了但没任务？

**答案**：抄送 = 仅通知，不在 `todoList` 里。

**查看抄送**：
```bash
curl -sX POST http://localhost:8101/wf/processTask/ccToMe \
  -H "Content-Type: application/json" \
  -d '{"operator":"user1"}' | jq
```

---

## Q6 · 提交后等了 30 秒还没响应？

**可能**：
- 引擎执行慢（高峰期）
- DB 锁等待
- 网络问题

**自检**：
```bash
# 健康检查
curl -s http://localhost:8101/healthz | jq

# 流程实例详情看 lastError
curl -sX POST http://localhost:8101/wf/processInstance/detail \
  -H "Content-Type: application/json" \
  -d '{"processInstanceId":1001}' | jq '.lastError'
```

如果 `lastError` 非空 → 联系 04 运维（陈 DBA），参考 [runbook.md §PG pool 耗尽](./runbook.md)

---

## Q7 · 我想撤回我发起的申请？

**答案**：可以（如果还没审批完成）。

**API**：
```bash
curl -sX POST http://localhost:8101/wf/processInstance/withdraw \
  -H "Content-Type: application/json" \
  -d '{"processInstanceId":1001,"operator":"user1"}' | jq
```

**限制**：只能撤回自己发起的 + 流程还在 RUNNING 状态。

---

## Q8 · 委派时 `targetUserId` 还是 `assignee`？

**答案**：**必须是 `targetUserId`**（FB-0009，2024 上半年修过）。

历史版本用过 `assignee` 字段，已废弃。当前实现：`vendor/jeeflow/facade.py:1992 _processTask_delegate` 严格校验字段名，传错返 400。

---

## Q9 · 为什么我提交的申请自动跳过了某个审批？

**可能**：
- 你用了「自动跳过」规则（HR 配置的跳过条件）
- 会签模式中你被认定为「同等审批权」
- processDesign 中设置了「直属领导 = 申请人时不需审批」

**查看**：用 `processInstance/highLight` 看实际走过的节点。

---

## Q10 · 我能在手机上审批吗？

**答案**：本仓无移动端 UI，但 CLI 可以。

**最快 30 秒**：
```bash
# 1. 查待办（手机浏览器开 jeeFlow CLI 终端）
jftodo
# 2. 同意 task ID 12345
jfok 12345
```

完整移动 CLI 卡 → [mobile-quickref.md](./mobile-quickref.md)（W3 末）

---

## 反馈本 FAQ

如果你有 Q1-Q10 之外的高频问题 → 在 `ToT/CC/feedback/03-participant-<seq>.md` 提，会被自动归到 FAQ。

---

**版本**：v1.11.1 · **来源**：故事 001（小李请假）+ 客服高频问题 → 03 persona review