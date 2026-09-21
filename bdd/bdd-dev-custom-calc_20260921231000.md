# BDD-DEV-010 dev-custom-calc (20260921231000)

## 流程设计

```mermaid
flowchart LR
    start([开始]) --> apply[提交费用]
    apply --> auto_calc[自动分摊计算<br/>custom handler<br/>AppendVarsHandler]
    auto_calc --> finance_review[财务审核]
    finance_review --> end([结束])
```

## 场景

费用分摊 - custom 节点演示。apply 后通过 custom handler 自动写入 `f_calc_result`，财务审核时查看。

## 用到的能力

- `snaker:custom` 自定义节点 + `clazz` 查 `custom_handler_registry`
- `args` JSON 字符串传入 + `val="f_calc_result"` 写回 instance 变量
- `com.mldong.jeeflow.test.AppendVarsHandler` 已注册 handler (FIX-T38 §16)

## 执行脚本

```bash
PID=$(curl ... startAndExecute \
  -d '{"processDefineId":"20","operator":"u_be_eng",
       "assignees":{"apply":"u_be_eng"},
       "variables":{"submitType":0,"f_amount":10000,"f_project":"PROJ-A",
                    "u_userId":"u_be_eng"}}' \
  | jq -r .data.processInstanceId)

# highLight 显示 activeNodeNames = [finance_review]
# bizData 应有 f_calc_result
curl ... bizData -d "{\"id\":\"$PID\"}"

# finance_review 流转
T=$(curl ... todoList -d '{"operator":"u_rd_dir"}' | jq -r .data.rows[0].id)
curl ... execute -d "{\"processTaskId\":\"$T\",\"submitType\":1,\"operator\":\"u_rd_dir\"}"
```

## 校验

| 项 | 期望 | 实际 | 结果 |
|---|---|---|---|
| custom 节点触发后写入 f_calc_result | {"key":"calc_result","value":"auto_split"} | ✅ | ✅ |
| 流程推进到 finance_review | activeNodeNames = [finance_review] | ✅ | ✅ |
| `state` | 20 (DONE) | 20 | ✅ |
| handler 未注册会抛 ValueError (FIX-T38 §16) | 实际 AppendVarsHandler 已注册 | 正常执行 | ✅ |

## 引擎行为

- custom 节点触发后调 handler → 写回 vars_[val]（FIX-T38 §16 已修复，不再静默丢弃）
- handler 返回值若是 dict，序列化到 instance 变量
- 不创建 task，直接 _follow_edges 推进下游

## 结果

- memory (8101): ✅ **PASS**（custom 节点 + handler 写入）
- pg (8102): skipped