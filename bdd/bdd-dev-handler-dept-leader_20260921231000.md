# BDD-DEV-012 dev-handler-dept-leader (20260921231000)

## 流程设计

```mermaid
flowchart LR
    start([开始]) --> apply[提交申请<br/>u_fe_eng D02]
    apply --> dept_leader_review[部门领导审批<br/>DeptLeaderAssignmentHandler]
    dept_leader_review --> dept_main_leader_review[分管领导审批<br/>DeptMainLeaderAssignmentHandler]
    dept_main_leader_review --> end([结束])
```

## 场景

通用审批 - 使用 `assignmentHandler` 自动按部门解析处理人。`u_fe_eng`(D02) 发起 → 自动找 D02 部门领导 `u_fe_lead` → 自动找 D02 分管领导 `u_rd_dir`。

## 用到的能力

- `assignmentHandler="com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$DeptLeaderAssignmentHandler"`
- `assignmentHandler="com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$DeptMainLeaderAssignmentHandler"`
- handler FQCN 精确匹配（FIX-T2 §6.1）
- 引擎从 `inst.operator.u_deptId` 取部门 → SPI `find_dept_leaders` 查 leader

## 执行脚本

```bash
# u_fe_eng (D02) 发起
PID=$(curl ... startAndExecute -d '{"operator":"u_fe_eng",...}' | jq -r .data.processInstanceId)

# todoList 验证 handler 自动分配 (u_fe_lead)
curl ... todoList -d '{"operator":"u_fe_lead"}' | jq .data.rows

# execute
T1=$(curl ... todoList -d '{"operator":"u_fe_lead"}' | jq -r .data.rows[0].id)
curl ... execute -d "{\"processTaskId\":\"$T1\",\"operator\":\"u_fe_lead\"}"

# 验证分管领导 u_rd_dir (D02 main_leader) 自动接收
T2=$(curl ... todoList -d '{"operator":"u_rd_dir"}' | jq -r .data.rows[0].id)
curl ... execute -d "{\"processTaskId\":\"$T2\",\"operator\":\"u_rd_dir\"}"
```

## 校验

| 项 | 期望 | 实际 | 结果 |
|---|---|---|---|
| D02 部门领导 = u_fe_lead | u_fe_lead 收到 dept_leader_review | ✅ | ✅ |
| D02 分管领导 = u_rd_dir | u_rd_dir 收到 dept_main_leader_review | ✅ | ✅ |
| handler 链路独立性 | 两个 handler 各自解析, 不互相影响 | ✅ | ✅ |
| `state` | 20 (DONE) | 20 | ✅ |

## SPI 数据

- `SPI_DEPT_LEADERS[D02] = ['u_fe_lead']`
- `SPI_DEPT_MAIN_LEADERS[D02] = ['u_rd_dir']`

## 结果

- memory (8101): ✅ **PASS**（handler 自动按部门解析处理人）
- pg (8102): skipped