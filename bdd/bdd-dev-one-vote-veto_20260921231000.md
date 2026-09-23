# BDD-DEV-009 dev-one-vote-veto (20260921231000)

## 流程设计

```mermaid
flowchart LR
    start([开始]) --> apply[提交合规审查]
    apply --> review_panel[审查会签<br/>u_ceo+u_cto+u_arch<br/>PARALLEL + ONE_VOTE_VETO]
    review_panel --> end([结束])
```

## 场景

合规审查 - 一票否决会签。任一 reject 立即 state=45 REJECT，其余任务 ABANDONED；全员 approve 才流转到 end。

## 用到的能力

- `performType=1` + `countersignType=PARALLEL` 并行会签
- `countersignCompletionCondition="ONE_VOTE_VETO"` 字符串常量（**不是**表达式）
- `task → end` 直连拓扑（FB-0012 §116 拓扑约束：必须直连 end，decision 节点截断 cs_veto）
- 触发者 taskState=20 (DONE) + updateUser=触发者 + instance state=45 (REJECT)

## 执行脚本

**场景A: 一票否决**
```bash
PID=$(curl ... startAndExecute ... | jq -r .data.processInstanceId)
TCEO=$(curl ... todoList -d '{"operator":"u_ceo"}' | jq -r .data.rows[0].id)
curl ... processTask/execute -d "{\"processTaskId\":\"$TCEO\",\"submitType\":20,\"operator\":\"u_ceo\"}"
# instance.state → 45 (REJECT)
# u_cto, u_arch taskState → 99 (ABANDONED, updateUser=u_ceo)
```

**场景B: 全员通过**
```bash
PID=$(curl ... startAndExecute ...)
for op in u_ceo u_cto u_arch; do
  T=$(curl ... todoList -d "{\"operator\":\"$op\"}" | jq -r .data.rows[0].id)
  curl ... execute -d "{\"processTaskId\":\"$T\",\"submitType\":1,\"operator\":\"$op\"}"
done
# instance.state → 20 (DONE)
```

## 校验

| 场景 | submitType | instance.state | 期望 | 实际 | 结果 |
|---|---|---|---|---|---|
| A (u_ceo reject) | 20 | REJECT(45) | u_ceo DONE, u_cto/u_arch ABANDONED | ✅ | ✅ |
| B (all approve) | 1,1,1 | DONE(20) | 3 reviewer 都 DONE | ✅ | ✅ |

## 关键发现

- **u_ceo taskState=20 (DONE) 不是 bug**: taskState=20 表示该用户完成了决策（reject 决策），不表示"审批通过"。instance.state=45 反映整体被否决。
- **u_cto/u_arch taskState=99 (ABANDONED)** 正确：FIX-T46+T47 一票否决触发后，所有其他 DOING 任务被废弃
- **拓扑约束验证 (FB-0012 §116)**: review_panel → end 直连，没有 decision 节点截断，cs_veto 正常生效

## 结果

- memory (8101): ✅ **PASS**（一票否决会签 + 全员通过两种语义）
- pg (8102): skipped