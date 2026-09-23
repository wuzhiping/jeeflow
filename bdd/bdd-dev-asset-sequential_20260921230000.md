# BDD-DEV-004 dev-asset-sequential (20260921230000)

## 流程设计

```mermaid
flowchart LR
    start([开始]) --> apply[提交采购]
    apply --> leaders_sign[领导会签(顺序)<br/>u_cto→u_arch→u_ceo]
    leaders_sign --> procurement[采购执行<br/>u_rd_dir]
    procurement --> end([结束])
```

## 场景

资产采购 - 顺序会签。CTO → 架构师 → CEO 依次审批，全部通过后由研发总监执行采购。

## 用到的能力

- `performType=1` + `countersignType=SEQUENTIAL` 顺序会签
- `assignee="u_cto,u_arch,u_ceo"` 字面量多 actor 列表
- `field.candidateUsers` 候选人过滤
- `PERMISSION_f_amount:1` + `PERMISSION_f_item:1` 只读字段权限

## 执行脚本

```bash
# reset + deploy
curl -s -X POST http://127.0.0.1:8101/api/reset
CONTENT=$(jq -c . bdd/bdd-dev-asset-sequential_20260921230000.json)
curl -s -X POST http://127.0.0.1:8101/wf/processDesign/save \
  -d "$(jq -nc --arg c "$CONTENT" '{name:"dev-asset-sequential", displayName:"BDD-DEV-资产采购-顺序会签", type:"approval", content:$c}')"
curl -s -X POST http://127.0.0.1:8101/wf/processDesign/deploy -d '{"id":"1"}'
# → processDefineId=20

PID=$(curl -s -X POST http://127.0.0.1:8101/wf/processInstance/startAndExecute \
  -d '{"processDefineId":"20","operator":"u_arch","title":"资产采购-BDD-004",
       "assignees":{"apply":"u_arch"},
       "variables":{"submitType":0,"f_item":"GPU 服务器","f_amount":80000,
                    "u_userId":"u_arch","u_realName":"陈静"}}' \
  | jq -r .data.processInstanceId)

# 1. CTO 第一个 active
T1=$(curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList \
  -d '{"operator":"u_cto","pageNum":1,"pageSize":20}' | jq -r '.data.rows[0].id')
curl -s -X POST http://127.0.0.1:8101/wf/processTask/execute \
  -d "{\"processTaskId\":\"$T1\",\"submitType\":1,\"operator\":\"u_cto\",\"variables\":{\"u_userId\":\"u_cto\",\"u_realName\":\"李娜\"}}"

# 2. u_arch 进入 active（顺序推进）
T2=$(curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList \
  -d '{"operator":"u_arch","pageNum":1,"pageSize":20}' | jq -r '.data.rows[0].id')
curl -s -X POST http://127.0.0.1:8101/wf/processTask/execute \
  -d "{\"processTaskId\":\"$T2\",\"submitType\":1,\"operator\":\"u_arch\",\"variables\":{\"u_userId\":\"u_arch\",\"u_realName\":\"陈静\"}}"

# 3. u_ceo 进入 active（最后）
T3=$(curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList \
  -d '{"operator":"u_ceo","pageNum":1,"pageSize":20}' | jq -r '.data.rows[0].id')
curl -s -X POST http://127.0.0.1:8101/wf/processTask/execute \
  -d "{\"processTaskId\":\"$T3\",\"submitType\":1,\"operator\":\"u_ceo\",\"variables\":{\"u_userId\":\"u_ceo\",\"u_realName\":\"张伟\"}}"

# 4. procurement 流转到 u_rd_dir
TRD=$(curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList \
  -d '{"operator":"u_rd_dir","pageNum":1,"pageSize":20}' | jq -r '.data.rows[0].id')
curl -s -X POST http://127.0.0.1:8101/wf/processTask/execute \
  -d "{\"processTaskId\":\"$TRD\",\"submitType\":1,\"operator\":\"u_rd_dir\",\"variables\":{\"u_userId\":\"u_rd_dir\",\"u_realName\":\"王强\"}}"
```

## 校验

| 项 | 期望 | 实际 | 结果 |
|---|---|---|---|
| 顺序会签 active 推进 | u_cto→u_arch→u_ceo 依次 active | ✅ | ✅ |
| approvalRecord 中 leaders_sign 出现次数 | 3 (按 actor 顺序) | 3 | ✅ |
| leaders_sign 的 operator 顺序 | u_cto, u_arch, u_ceo | u_cto, u_arch, u_ceo | ✅ |
| `state` | 20 (DONE) | 20 | ✅ |
| procurement 阶段 operator | u_rd_dir | u_rd_dir | ✅ |
| `bizData.f_item/f_amount` | 保留原值 | "GPU 服务器"/80000 | ✅ |

## 结果

- memory (8101): ✅ **PASS**（顺序会签按 actor 列表顺序推进）
- pg (8102): skipped

## 备注

- 顺序会签引擎行为：第 1 个 actor 提交后才创建第 2 个 actor 的 task（不是一次性创建），因此 `processTask/todoList` 在 u_cto 完成前查 u_arch 一定是空。
- `taskType:2`(RECORD) 与"汇合后由人办理"语义不符；本流程 `procurement` 改用 `taskType:0`。