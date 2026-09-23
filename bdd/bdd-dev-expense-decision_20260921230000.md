# BDD-DEV-002 dev-expense-decision (20260921230000)

## 流程设计

```mermaid
flowchart LR
    start([开始]) --> apply[提交报销]
    apply --> decision_amount{金额判定}
    decision_amount -- f_amount<=5000 --> leader_approve_small[组长审批]
    decision_amount -- f_amount>5000 --> cto_approve_large[CTO 审批]
    leader_approve_small --> finance_record[财务登记]
    cto_approve_large --> finance_record
    finance_record --> end([结束])
```

## 场景

报销审批 - 金额分支。小额（≤5000）走组长 + 财务；大额（>5000）走 CTO + 财务。

## 用到的能力

- `snaker:decision` 决策节点 + 两条出边 expr
- `expr: "#f_amount<=5000"` / `expr: "#f_amount>5000"` SimpleExprEvaluator 评估
- 多入边 task 节点（finance_record 由两个分支汇合）— 等同 join 但不显式声明
- 顶层 `f_amount` 直接传，decision expr 可读（FIX-DOC-4 §7.1）

## 执行脚本

```bash
# 1. reset + deploy
curl -s -X POST http://127.0.0.1:8101/api/reset
CONTENT=$(jq -c . bdd/bdd-dev-expense-decision_20260921230000.json)
curl -s -X POST http://127.0.0.1:8101/wf/processDesign/save \
  -d "$(jq -nc --arg c "$CONTENT" '{name:"dev-expense-decision", displayName:"BDD-DEV-报销审批-金额分支", type:"approval", content:$c}')"
curl -s -X POST http://127.0.0.1:8101/wf/processDesign/deploy -d '{"id":"1"}'
# → processDefineId=20

# 2. 场景A：小额 3000
PID_A=$(curl -s -X POST http://127.0.0.1:8101/wf/processInstance/startAndExecute \
  -d '{"processDefineId":"20","operator":"u_be_eng","title":"报销-小额-BDD-002A",
       "assignees":{"apply":"u_be_eng"},"f_amount":3000,
       "variables":{"submitType":0,"f_amount":3000,"f_item":"办公椅",
                    "u_userId":"u_be_eng","u_realName":"钱琳"}}' \
  | jq -r .data.processInstanceId)

# highLight 显示走 leader_approve_small
curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList -d '{"operator":"u_be_lead","pageNum":1,"pageSize":20}' \
  | jq -r '.data.rows[0].id'  # T1 for u_be_lead
curl -s -X POST http://127.0.0.1:8101/wf/processTask/execute \
  -d '{"processTaskId":"<T1>","submitType":1,"operator":"u_be_lead","variables":{"u_userId":"u_be_lead","u_realName":"孙婷"}}'

curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList -d '{"operator":"u_qa_lead","pageNum":1,"pageSize":20}' \
  | jq -r '.data.rows[0].id'  # T2 for u_qa_lead
curl -s -X POST http://127.0.0.1:8101/wf/processTask/execute \
  -d '{"processTaskId":"<T2>","submitType":1,"operator":"u_qa_lead","variables":{"u_userId":"u_qa_lead","u_realName":"冯雪"}}'

# 3. 场景B：大额 8000
PID_B=$(curl -s -X POST http://127.0.0.1:8101/wf/processInstance/startAndExecute \
  -d '{"processDefineId":"20","operator":"u_be_eng","title":"报销-大额-BDD-002B",
       "assignees":{"apply":"u_be_eng"},"f_amount":8000,
       "variables":{"submitType":0,"f_amount":8000,"f_item":"服务器机柜",
                    "u_userId":"u_be_eng","u_realName":"钱琳"}}' \
  | jq -r .data.processInstanceId)

# highLight 显示走 cto_approve_large
curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList -d '{"operator":"u_cto","pageNum":1,"pageSize":20}' \
  | jq -r '.data.rows[0].id'  # T1 for u_cto
curl -s -X POST http://127.0.0.1:8101/wf/processTask/execute \
  -d '{"processTaskId":"<T1>","submitType":1,"operator":"u_cto","variables":{"u_userId":"u_cto","u_realName":"李娜"}}'

curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList -d '{"operator":"u_qa_lead","pageNum":1,"pageSize":20}' \
  | jq -r '.data.rows[0].id'
curl -s -X POST http://127.0.0.1:8101/wf/processTask/execute \
  -d '{"processTaskId":"<T2>","submitType":1,"operator":"u_qa_lead","variables":{"u_userId":"u_qa_lead","u_realName":"冯雪"}}'
```

## 校验

| 项 | 期望 (小额 3000) | 期望 (大额 8000) | 实际 | 结果 |
|---|---|---|---|---|
| decision 路由 | leader_approve_small | cto_approve_large | ✅✅ | ✅ |
| `state` | 20 (DONE) | 20 (DONE) | 20,20 | ✅ |
| `approvalRecord` 节点数 | 3 (apply+leader+finance) | 3 (apply+cto+finance) | 3,3 | ✅ |
| `bizData.f_amount` | 3000 | 8000 | ✅✅ | ✅ |
| `u_*` 操作人不持久化 | null | null | ✅✅ | ✅ |

## BUG 发现与修复

### BUG-3 (FIX-T113) · 2026-09-21
- **现象**: `startAndExecute` 返回 `[TypeError] EngineImpl._cleanup_orphan_decision_tasks() takes 6 positional arguments but 7 were given`
- **根因**: `vendor/jeeflow/engine.py:680/690/705` 3 处调用点传了 6 个位置参数 `(flow, inst, edges, edge, operator, vars_)`，但函数签名 `(self, flow, inst, selected_edge, operator, vars_)` 只接受 5 个参数。函数内部已用 `flow.edges` 遍历 sibling edges，调用方多传的 `edges` 参数未被使用。
- **修复**: 删除 3 处调用点的 `edges,` 冗余参数。
- **验证**: 重启 `main.py` 后 decision 节点正常求值，金额分支按 expr 正确分流。

### 设计自检 (lesson learned)
- ⚠️ `taskType:2` (RECORD) 会**自动完成**，无需手动 execute；若期望"汇合后由人办理"，用 `taskType:0`。
- 最初 finance_record 误用 taskType=2，导致 leader_approve_small 执行后 finance_record 自动 DONE + operator="" + instance.state=20。修正为 taskType:0 后恢复正常。

## 结果

- memory (8101): ✅ **PASS**（决策分支 + 双路径汇合）
- pg (8102): skipped