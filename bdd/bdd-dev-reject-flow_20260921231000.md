# BDD-DEV-015 dev-reject-flow (20260921231000)

## 流程设计

```mermaid
flowchart LR
    start([开始]) --> apply[提交请假]
    apply --> leader_decision[组长决策<br/>u_fe_lead]
    leader_decision --> end([结束])
```

## 场景

请假驳回路径 - submitType=2 (REJECT) 触发 instance.state=45。

## 用到的能力

- `submitType=2` (REJECT) 走 facade 拦截 → `execute_and_jump_to_end` → `inst.reject()` → state=45
- **不走 decision 节点**，绕过 expr 评估直接 REJECT
- 验证 InstanceState.REJECT 枚举值 = 45

## 执行脚本

```bash
# 启动 (u_fe_eng 发起, 99 天请假)
PID=$(curl ... startAndExecute ... | jq -r .data.processInstanceId)

# 组长驳回
T1=$(curl ... todoList -d '{"operator":"u_fe_lead"}' | jq -r .data.rows[0].id)
curl ... execute -d "{\"processTaskId\":\"$T1\",\"submitType\":2,\"operator\":\"u_fe_lead\",\"comment\":\"请假过长\"}"

# instance.state → 45 (REJECT)
```

## 校验

| 项 | 期望 | 实际 | 结果 |
|---|---|---|---|
| `submitType=2` 触发 instance.state=45 | 45 | 45 | ✅ |
| approvalRecord leader_decision taskState=20 | 20 | 20 | ✅ |
| leader_decision operator=u_fe_lead | u_fe_lead | u_fe_lead | ✅ |
| 不触发下游 end 处理 (facade 拦截) | end 未触发 reject/reject 逻辑 | ✅ | ✅ |

## 引擎行为

- `submitType=2` 走 facade.py `execute_and_jump_to_end` 路径
- 直接调 `inst.reject()` → instance.state=45
- 跳过 decision 节点的 expr 评估 (无 cycle 表)
- BUGS.md §43: REJECT 走 facade 拦截,不走 decision

## 结果

- memory (8101): ✅ **PASS**（驳回路径）
- pg (8102): skipped