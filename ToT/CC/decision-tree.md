# Decision Tree · 委派/加签/转办/驳回 决策

> **读者**：被审批人（领导）/ 任务执行人
> **场景**：王组长发现自己周三出差，赵副组长在，怎么办？

---

## 决策树 1 · 我要出差（审批人视角）

```
你要出差，task 在你这里？
    │
    ├ 出差 1-2 天能回来？
    │    └ 是 → 委派（delegate）
    │           - targetUserId=同事工号
    │           - 副作用：原 task 仍属于你，回来后你能看历史
    │           - API: POST /wf/processTask/delegate
    │           - 字段: processTaskId, operator, targetUserId
    │
    ├ 出差 3+ 天？
    │    └ 是 → 转办（transfer，需修改流程定义）
    │           - 不是临时操作，是「这个 task 永久归别人」
    │           - 联系 02 流程管理员 改 processDefine
    │
    └ 需要多人同时审批？
         └ 是 → 加签（addSign）
                - 加签后会出现多人 task（会签模式）
                - API: POST /wf/processTask/addSign（待引擎支持，参考 01 plan A5）
```

---

## 决策树 2 · 我要请假（发起人视角）

```
你要请假？
    │
    ├ 1-3 天？
    │    └ 直接 2 级审批：直属领导 → HR 备案
    │       - 预计 4 小时内完成
    │
    ├ 4-7 天？
    │    └ 3 级审批：直属 → 部门 → HR
    │       - 预计 1 个工作日
    │
    └ 7+ 天？
         └ 4 级审批 + 总经理签字
            - 预计 2-3 个工作日
```

---

## 决策树 3 · 我想驳回（审批人视角）

```
要驳回当前 task？
    │
    ├ 只想打回申请人重写？
    │    └ 驳回到 start 节点
    │       - submitType=REJECT_TO_START
    │
    ├ 想打回到中间某个审批人？
    │    └ 驳回到任意节点（需引擎支持，见 01 plan A3）
    │       - submitType=REJECT_TO_NODE
    │       - args.rejectToNodeId=目标节点 ID
    │
    └ 想直接结束整个流程？
         └ 终止（terminate）
            - API: POST /wf/processInstance/terminate
            - 数据全部归档，不可恢复
```

---

## 反例（不要这样做）

| 反例 | 后果 |
|---|---|
| 用委派而不是转办 → 出差回来发现 task 不在你名下 | 历史看得到但不能再操作 |
| 用加签而不是委派 → 让 5 个人都批一次 | 流程变慢 + 责任分散 |
| 把「请假」驳回到 start 而非中间节点 | 申请人所有字段清空 |
| 不写 `targetUserId` 而写 `assignee` | 服务端报 400「字段名错」（FB-0009）|

---

## 相关 FAQ

- 委派后还能收回吗？ → [faq.md](./faq.md) Q4
- 加签/委派历史在哪查？ → [history-lookup.md](./history-lookup.md)
- 驳回后申请人能看到我写的意见吗？ → [faq.md](./faq.md) Q5

---

**版本**：v1.11.1 · **来源**：故事 001（王组长出差）→ 03 persona review