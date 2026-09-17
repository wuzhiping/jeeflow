# BDD Task 26: 委派场景（surrogate 仅记录授权，不影响 task 处理权限）

- **时间**：2026-09-17 14:06:00（TS=20260917140600）
- **JSON 定义**：`./bdd/bdd-delegate-test_20260917140600.json`
- **服务**：main.py（PID 3435402）
- **修改文件**：无（探索 surrogate 行为）

## 1. 场景设计

| 节点 | 流转 |
|---|---|
| start → apply → leader_review → end | 简单串行 |

目标：leader 把任务**委派**给 manager（surrogate），让 manager 处理

## 2. 测试结果

### Step 1: 创建 surrogate 记录

```
POST /wf/processSurrogate/save
body: {operator: "leader", surrogate: "manager", startTime, endTime, enabled:1}
响应: {"code":0,"msg":"成功","data":{"id":"11"}}  ✅
```

### Step 2: 验证 surrogate 不影响 task 处理权限

```
# 即使有 surrogate 记录，manager execute 仍失败
manager execute → {"code":99999999,"msg":"operator manager not allowed"} ❌
leader execute → {"code":0,"msg":"成功"} ✅
```

## 3. 关键发现 — 已知问题 #40

**Python 引擎 surrogate 实际行为**：
- surrogate 仅是流程级授权记录（用于前端"我的委托"列表）
- **surrogate 不会修改 task.actorIds**，引擎 execute_process_task 仍严格校验 `operator in actorIds`
- Java boot2 有 processTask/delegate 接口（任务级委托），Python facade **未实现该接口**
- 后果：流程发起后，被委托人**无法直接处理**任务，必须被委托人自己执行

## 4. 引擎行为细节

`engine.py:execute_process_task`:
```python
if operator not in self.repo._actors.get(task_id, []):
    raise ValueError(f"operator {operator} not allowed")
```

`facade.py` 无 `_processTask_delegate` 方法（未实现任务级委托 API）。

## 5. 文档改进

- docs/known-issues.md §40 新增：Python 引擎 surrogate 仅做记录，不影响 task 处理权限
- docs/flow.md §7 委托章节：明确 surrogate vs delegate 区别

## 6. 缓解措施

1. **临时方案**：使用 countersign（multi-actor + performType=1）让多个 actor 都能处理
2. **彻底方案**：Python 引擎需在 facade 实现 `_processTask_delegate`，engine.execute_process_task 增加 surrogate 解析

## 7. 后续

- Task 27: 边界场景 + 修复尝试
