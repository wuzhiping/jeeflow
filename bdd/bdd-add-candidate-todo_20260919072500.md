# BDD 任务 #109: addCandidate 动态扩展 actor

## 目标
验证 addCandidate API 调用后，非 actor 用户能进入待办列表

## 流程
apply(user1) → task1(assignee=manager, candidateUsers=manager) → end

## 实测
1. startAndExecute → instId=91843380879376
2. manager 待办看到 task1 (id=91843380880402) ✓
3. director 待办看不到 ✓
4. **addCandidate 首次失败**：传 `operator:"director"` → `99999999 processTaskId/actorIds 缺失`
5. **修正**：传 `actorIds:["director"]` → 0 成功
6. director 待办看到 task1 ✓
7. director execute → 0 成功
8. final state=20 (DONE) ✓

## 结论
✅ **PASS**：addCandidate 动态扩展 actor 工作正常

## 关键发现
⚠️ **API 命名不一致**：
- `addCandidate` 参数是 `actorIds: List[str]`，**不是** `operator`
- vendor/jeeflow/facade.py:1099 `actor_ids = self._to_str_list(args.get("actorIds"))`
- 错误信息 "processTaskId/actorIds 缺失" 提示明显
- 但 BDD#106 报告 §4.4.1 写的 `args.operator` 实际是 `args.actorIds`，文档需修正

## 修复建议
- docs/flow.md §3.3 任务节点 properties 补充 addCandidate 用法
- facade 错误信息可更友好：`"addCandidate 需要 actorIds: List[str]，请使用 processTaskId+actorIds 字段"`
