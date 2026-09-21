# BDD-DEV-003 dev-release-fork (20260921230000)

## 流程设计

```mermaid
flowchart LR
    start([开始]) --> apply[提交上线]
    apply --> fork1{fork1}
    fork1 --> tech_review[技术评审<br/>u_be_lead]
    fork1 --> qa_review[QA 复核(副审)<br/>u_qa_lead<br/>taskType=1]
    tech_review --> join1{join1}
    qa_review --> join1
    join1 --> release_execute[执行上线<br/>u_cto]
    release_execute --> end([结束])
```

## 场景

代码上线审批 - fork/join 并行汇合。技术评审（主审）+ QA 复核（副审）并行，两边都完成才推进到执行上线。

## 用到的能力

- `snaker:fork` + `snaker:join` 并行汇合模式
- `taskType=1` 副审标记（FIX-T30 §3.3 透传落库）
- join 节点 `find_doing_tasks` 守卫（无活跃 task 时才放行）

## 执行脚本

```bash
# reset + deploy
curl -s -X POST http://127.0.0.1:8101/api/reset
CONTENT=$(jq -c . bdd/bdd-dev-release-fork_20260921230000.json)
curl -s -X POST http://127.0.0.1:8101/wf/processDesign/save \
  -d "$(jq -nc --arg c "$CONTENT" '{name:"dev-release-fork", displayName:"BDD-DEV-上线审批-并行汇合", type:"approval", content:$c}')"
curl -s -X POST http://127.0.0.1:8101/wf/processDesign/deploy -d '{"id":"1"}'
# → processDefineId=20

# start
PID=$(curl -s -X POST http://127.0.0.1:8101/wf/processInstance/startAndExecute \
  -d '{"processDefineId":"20","operator":"u_be_senior1","title":"上线-BDD-003",
       "assignees":{"apply":"u_be_senior1"},
       "variables":{"submitType":0,"f_env":"prod","f_version":"v1.9.0",
                    "u_userId":"u_be_senior1","u_realName":"吴杰"}}' \
  | jq -r .data.processInstanceId)

# highLight 显示 activeNodeNames = ["tech_review", "qa_review"]
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/highLight -d "{\"id\":\"$PID\"}"

# u_qa_lead 先完成 (副审能办)
TQA=$(curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList \
  -d '{"operator":"u_qa_lead","pageNum":1,"pageSize":20}' | jq -r '.data.rows[0].id')
curl -s -X POST http://127.0.0.1:8101/wf/processTask/execute \
  -d "{\"processTaskId\":\"$TQA\",\"submitType\":1,\"operator\":\"u_qa_lead\",\"variables\":{\"u_userId\":\"u_qa_lead\",\"u_realName\":\"冯雪\"}}"

# 此时 u_cto 待办应仍为空 (join1 守卫等待 tech_review)
curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList -d '{"operator":"u_cto","pageNum":1,"pageSize":20}'

# 完成 tech_review，触发 join1 放行
TTECH=$(curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList \
  -d '{"operator":"u_be_lead","pageNum":1,"pageSize":20}' | jq -r '.data.rows[0].id')
curl -s -X POST http://127.0.0.1:8101/wf/processTask/execute \
  -d "{\"processTaskId\":\"$TTECH\",\"submitType\":1,\"operator\":\"u_be_lead\",\"variables\":{\"u_userId\":\"u_be_lead\",\"u_realName\":\"孙婷\"}}"

# u_cto 现在有 release_execute 待办
TCTO=$(curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList \
  -d '{"operator":"u_cto","pageNum":1,"pageSize":20}' | jq -r '.data.rows[0].id')
curl -s -X POST http://127.0.0.1:8101/wf/processTask/execute \
  -d "{\"processTaskId\":\"$TCTO\",\"submitType\":1,\"operator\":\"u_cto\",\"variables\":{\"u_userId\":\"u_cto\",\"u_realName\":\"李娜\"}}"
```

## 校验

| 项 | 期望 | 实际 | 结果 |
|---|---|---|---|
| fork 后双 task 并行创建 | activeNodeNames = [tech_review, qa_review] | ✅ | ✅ |
| qa_review 单边完成 → CTO 待办为空 (join 守卫) | u_cto 待办=[] | ✅ | ✅ |
| tech_review 完成 → 触发 join1 放行 | u_cto 出现 release_execute | ✅ | ✅ |
| `state` | 20 (DONE) | 20 | ✅ |
| `approvalRecord` 节点数 | 4 (apply+tech+qa+release) | 4 | ✅ |
| qa_review 的 taskType=1 落库 | taskType=1 | taskType=1 | ✅ |

## 结果

- memory (8101): ✅ **PASS**（fork/join 并行汇合 + 副审 taskType 落库）
- pg (8102): skipped

## 备注

- highLight.historyNodeNames 包含 release_execute/end 是因为 `_collect_path` 从 start 路径补全到所有可达节点，**不是实际访问历史**。判断 join 守卫是否生效请查 `processTask/todoList` 而非 highLight。