# BDD 任务 #120: 空 submitType 默认 0 (APPLY)

## 目标
验证 `startAndExecute` + `processTask/execute` 都不传 submitType 时的默认行为

## 流程
apply → task1 → end

## 实测
- startAndExecute 不传 submitType → state=10 (DOING)，apply 自动跑完
- processTask/execute 不传 submitType → state=20 (DONE)

## 结论
✅ **PASS**：空 submitType 默认 0 (APPLY) = 通过

## 引擎行为
- `engine._prepare_execute_task` 取 `args.get("submitType", 0)`
- `facade._processTask_execute` 取 `args.get("submitType", SUBMIT_APPLY)`
- 双重兜底，缺省 0 = APPLY
- 测试时可省略 submitType 字段

## 设计要点
- 测试时建议**显式传 submitType=0**（不依赖默认）
- 防止 facade/engine 后续版本修改默认值
