# BDD-DEV-007 dev-recruit-simple-chain (20260921231000)

## 流程设计

```mermaid
flowchart LR
    start([开始]) --> apply[提交简历]
    apply --> leader_screen[组长筛选<br/>u_be_lead]
    leader_screen --> tech_interview[技术面<br/>u_arch]
    tech_interview --> rd_final[总监终审<br/>u_rd_dir]
    rd_final --> end([结束])
```

## 场景

招聘审批 - 简单多 task 链。提交简历 → 组长筛选 → 技术面 → 总监终审。

## 用到的能力

- 4 节点线性串行（apply + 3 个 task + end）
- 每个 task 不同 userId，验证 taskName 不同可独立 actor

## 执行脚本

```bash
# reset + deploy + start
PID=$(curl ... startAndExecute -d '... u_be_eng ...' | jq -r '.data.processInstanceId')

# 串行 3 个 execute
for op in u_be_lead u_arch u_rd_dir; do
  T=$(curl -d "{\"operator\":\"$op\"}" /wf/processTask/todoList | jq -r '.data.rows[0].id')
  curl -d "{\"processTaskId\":\"$T\",\"submitType\":1,\"operator\":\"$op\"}" /wf/processTask/execute
done
```

## 校验

| 项 | 期望 | 实际 | 结果 |
|---|---|---|---|
| 3 个 task 顺序流转 | leader_screen → tech_interview → rd_final | ✅ | ✅ |
| `state` | 20 (DONE) | 20 | ✅ |
| approvalRecord | 4 (apply + 3 tasks) | 4 | ✅ |

## 结果

- memory (8101): ✅ **PASS**（4 节点线性审批链）
- pg (8102): skipped