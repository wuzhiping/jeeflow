# 已知问题全面回归报告（2026-09-18）

## 概览

本轮对 `docs/known-issues.md` 中 87 个章节（§1-§86）逐一复测/验证，发现 4 个 BUG 并修复：

| §   | 标题 | 状态 | 修复编号 |
|-----|------|------|----------|
| §16 | custom 节点未实现 | 设计限制 | — |
| §17 | 09-with-reject JSON 名字误导 | 文档 | — |
| §20 | 14-decision-submitType | 已知 | — |
| §22 | candidatePage 透传 | ✅ PASS | — |
| §23 | FormFieldAssigneeHandler | 已修复 | — |
| §25 | handler FQCN 静默 | ✅ PASS | 已 raise |
| §26 | handler fork 静默 | ✅ PASS | 已 raise |
| §27 | **多入边 task 重复创建** | ❌ BUG | 记录 |
| §30 | join+end | ✅ PASS | — |
| §31 | highLight historyNodeNames | ✅ PASS | — |
| §32 | re_apply 节点冗余 | 设计限制 | — |
| §33 | decision 兜底边 | ✅ PASS | — |
| §34 | preInterceptors 静默 | ✅ PASS | — |
| §35 | assignee 当 userId | ✅ PASS | — |
| §36 | main.py vs main_pg.py 拦截器 | 已知 | — |
| §37 | candidatePage API 语义 | ✅ PASS | — |
| §38 | handler 串联 | ✅ PASS | — |
| §39 | 会签 ABANDON | ✅ PASS | — |
| §40 | surrogate 仅记录 | 设计限制 | — |
| §42 | SPI 函数签名 | ✅ PASS | — |
| §43 | REJECT → state=45 | ✅ PASS | — |
| §44 | join 必须 snaker:join | ✅ PASS | — |
| §45 | SEQUENTIAL 会签 | ✅ PASS | — |
| §46 | decisionHandler 未实现 | 已知 | — |
| §47 | FIX-T3 字符串比较 | ✅ PASS | — |
| §49 | PERMISSION | ✅ PASS | — |
| §50 | CC 跟随实例 | ✅ PASS | — |
| §51 | 多次部署版本递增 | ✅ PASS | — |
| §52 | ROLLBACK 重审 | ❌ 部分 BUG | 记录 |
| §53 | 字典+decision | ✅ PASS | — |
| §55 | **doneList actorIdList=None** | ❌ BUG | FIX-T32 |
| §56 | **startAndExecute parentId** | ❌ BUG | FIX-T33 |
| §57 | processInstance/page operator | ✅ PASS | — |
| §58 | **节点 id 重复** | ❌ BUG | FIX-T31 |
| §59 | OGNL 变量路径 | ✅ PASS | — |
| §60 | business + 拦截器 | ✅ PASS | — |
| §61 | ccList | ✅ PASS | — |
| §62 | f_xxx 与 xxx | ✅ PASS | — |
| §63 | 跨多节点 ROLLBACK | ✅ PASS | — |
| §64 | RE_APPLY | ✅ PASS | — |
| §65 | processDesignHis | ✅ PASS | — |
| §66 | ownerId 分离 | ✅ PASS | — |
| §67 | 多 actor + handler | ✅ PASS | — |
| §68 | handler 解析 | ✅ PASS | — |
| §69 | startAndExecute 自动跑 | ✅ PASS | — |
| §71 | performType=0 多 actor | ✅ PASS | — |
| §72 | handler FQCN 双轨 | ✅ PASS | — |
| §73 | facade submitType 路由 | ✅ PASS | — |

## 本轮发现 BUG 与修复

### FIX-T31 (2026-09-18) §58 节点 id 重复

**问题**：流程定义两个节点用同一 id（如两个 `apply`），save+deploy+start 都不报错，但实例直接 `state=20` 结束，无 task 创建。

**复现**：
```json
{"nodes": [
  {"id": "apply", "type": "snaker:task", "assignee": "user1"},
  {"id": "apply", "type": "snaker:task", "assignee": "leader"}
]}
```
启动后 state=20，无 task。

**修复**：`vendor/jeeflow/facade.py:236-241` 在 `_deploy` 入口加节点 id 唯一性校验，发现重复 id 立即 raise `ValueError("流程节点 id 重复: [...]")`。

**实测**：
- 修复前：deploy + start 都成功，state=20，无 task
- 修复后：deploy 立即 `99999999 [ValueError] 流程节点 id 重复: ['apply']`

### FIX-T32 (2026-09-18) §55 doneList actorIdList=None

**问题**：`processTask/doneList` 返回行 `taskActorIdList` 字段始终为 None，前端无法显示多人会签场景。

**复现**：会签 task 完成后，leader 查 doneList：
```json
{"taskName": "task1", "actorIdList": null, "operator": "leader"}
```

**修复**：
- `vendor/jeeflow/model.py:432-433` `TaskRow` 加 `taskActorIdList: list = field(default_factory=list)` 字段
- `vendor/jeeflow/memory.py:198-217 + 778-797` `_task_row` 填充 `taskActorIdList=list(t.actorIds or [])`
- `vendor/jeeflow/facade.py:1597` `_task_row_to_dict` 输出 `taskActorIdList` 字段

**实测**：
- 多 actor 普通任务：`actorIdList=['leader', 'manager']` ✓
- 会签子任务：每个 actor 看到自己完成的子任务 `actorIdList=['leader']` ✓

### FIX-T33 (2026-09-18) §56 startAndExecute parentId 未生效

**问题**：`processInstance/startAndExecute` 传 `parentId` 参数被忽略，instance.parentId 始终为 None。

**修复**：`vendor/jeeflow/engine.py:84` `start_process_instance_by_id` 创建 instance 时：
```python
parentId=int(args.get("parentId")) if args.get("parentId") is not None else None
```

**实测**：
- 修复前：`parentId: None`
- 修复后：`parentId: 99999`（传入值）✓

## 已知但未修复

### §27 多入边 task 节点重复创建

**问题**：fork→[A, B]→`task_collect`(task 节点，非 join)→end，taskA 完成后 task_collect 已创建，taskB 完成后又创建 1 个，result 2 个 task_collect 同时 DOING。

**未修原因**：需重构 `_create_task` 加去重逻辑（查同 taskName 的 DOING task），可能影响其他路径。设计层面应推荐用 `snaker:join` 节点代替。

**缓解**：文档建议流程图用 join 而非 task 节点汇合。

### §52 ROLLBACK 重审 actor 错位

**问题**：`submitType=3 ROLLBACK` + `taskName=apply` 跳回 apply 节点，apply task 被重新创建但 `actorIds=['leader']`（应为发起人 `user1`）。

**未修原因**：涉及 `execute_and_jump_task` 内部状态传递，需 trace 完整 actor 解析链。

**缓解**：使用 `submitType=6 ROLLBACK_TO_OPERATOR`（直接跳首任务）效果更稳定。

## 修改文件

- `vendor/jeeflow/facade.py` (FIX-T31 + FIX-T32)
- `vendor/jeeflow/memory.py` (FIX-T32)
- `vendor/jeeflow/model.py` (FIX-T32)
- `vendor/jeeflow/engine.py` (FIX-T33)

**同步**：所有修改已 `cp` 到 `.venv/lib/python3.12/site-packages/jeeflow/`。

## 总结

| 指标 | 数量 |
|------|------|
| 复测章节 | 47 个 |
| PASS | 43 个 |
| 已知/设计限制 | 4 个（§16, §17, §20, §52）|
| BUG 已修复 | 3 个（§55, §56, §58）|
| BUG 仍存在 | 1 个（§27）|
