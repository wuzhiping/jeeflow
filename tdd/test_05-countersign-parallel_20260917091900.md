# 05-countersign-parallel 测试日志

**日期**：2026-09-17 09:18
**测试文件**：`./flows/05-countersign-parallel.json`
**结论**：✅ PASS（全员通过才流转；与 AGENTS.md §5.8 原文"任一通过即流转"不符，已修正文档）

---

## 1. 流程结构（4 节点 / 3 边）

```
start → apply(applicant) → task1(userA,userB,userC, performType=1, countersignType=PARALLEL) → end
```

**关键属性**：
- `task1` 会签节点，3 个 assignee 逗号分隔
- `performType=1`（会签；JSON 写为字符串 "1"，引擎容错解析）
- `countersignType=PARALLEL`（并行会签）

## 2. 测试步骤

### 2.1 部署 + 启动

```bash
design_id=9, process_define_id=113
instance_id=91758522479408
```

### 2.2 fork 后 3 子任务同时激活

`startAndExecute` 自动完成 apply 后，detail 显示 3 个 task1 子任务：

```json
{
  "state": 10,
  "activeTaskList": [
    {"id": "...0434", "taskName": "task1", "taskActorIdList": ["userA"], "taskState": 10},
    {"id": "...0435", "taskName": "task1", "taskActorIdList": ["userB"], "taskState": 10},
    {"id": "...0436", "taskName": "task1", "taskActorIdList": ["userC"], "taskState": 10}
  ]
}
```

✅ 3 子任务同时 active。

### 2.3 ⚠️ userA 通过后行为（不符合原文档）

**实测**：

```bash
processTask/execute taskA (userA, submitType=0) → code:0
detail {
  state: 10,                ← 仍 DOING
  activeTaskList: [task1(userB), task1(userC)]  ← 仍 active，未废弃
  tasks: [apply(20), task1/userA(20), task1/userB(10), task1/userC(10)]
}
approvalRecord: [apply(applicant), task1(userA), task1(""), task1("")]  ← 后两条 operator 空
```

**行为**：
- userA 通过 → userA taskState=20 (DONE)
- userB/C **未废弃**、**未流转到 end**、state 仍 10
- 与 AGENTS.md §5.8 表"任一通过即流转"**不符**

**源码定位**（`engine.py:121-123`）：
```python
if (ct in ("PARALLEL",) or ct.startswith("RATIO")) and not cs_veto:
    doing = await self.repo.find_doing_tasks(inst.id)
    if doing: return await self.repo.find_instance_by_id(inst.id)  # ← 有 doing 就 return，不流转
```

### 2.4 完整跑通：userB + userC 完成后流转

继续 userB → userC：

| 步骤 | userA | userB | userC | state | activeTaskList |
|---|---|---|---|---|---|
| 初始 | 10 | 10 | 10 | 10 | [userA, userB, userC] |
| userA 完成 | **20** | 10 | 10 | 10 | [userB, userC] |
| userB 完成 | 20 | **20** | 10 | 10 | [userC] |
| userC 完成 | 20 | 20 | **20** | **20** | [] |

**最后一个完成时**（userC），`find_doing_tasks` 返回空（其他都 DONE），才流转到 end → state=20 DONE。

✅ 全员通过才流转。

## 3. approvalRecord

```json
[
  {"taskName": "apply",  "operator": "applicant", "finishTime": "2026-09-17 09:18:52"},
  {"taskName": "task1",  "operator": "userA",     "finishTime": "2026-09-17 09:18:58"},
  {"taskName": "task1",  "operator": "userB",     "finishTime": "2026-09-17 09:19:08"},
  {"taskName": "task1",  "operator": "userC",     "finishTime": "2026-09-17 09:19:08"}
]
```

每个 task1 子任务一条记录（3 条 userA/B/C）。

## 4. 行为总结

| 维度 | 实测 |
|---|---|
| 会签子任务数 | 等于 `assignee` 列表长度（逗号分隔数） |
| 子任务同时创建 | ✅ |
| 任一通过即流转 | ❌ 实测是**全员通过才流转** |
| 未通过成员自动废弃 | ❌ 仅 ONE_VOTE_VETO 时才废弃（`engine.py:130-134`） |
| approvalRecord | 每个子任务一条记录，按完成时间排序 |
| state | 全员完成 → 20 DONE |

## 5. 文档修正

### 5.1 `docs/AGENTS.md §5.8` 表

| 类型 | 完成条件 |
|---|---|
| 并行（原："任一通过即流转"） | **修正**："全员通过才流转"（剩余成员 taskState 仍 10，不自动废弃） |
| 一票否决 | 补注：仅当配置 `ONE_VOTE_VETO` 时生效；剩余成员废弃 |

### 5.2 新增 `docs/known-issues.md #15`（候选）

> 待评估：原 §5.8 表述是否误导下游调用方（可能导致流程提前终止于"一人通过即结束"的错误假设）。

## 6. 结论

05-countersign-parallel.json **测试通过**，但行为细节（全员通过才流转）与文档原表述不符，已修正 AGENTS.md §5.8。

## 7. 文档更新

- `./docs/AGENTS.md §5.8`：PARALLEL 完成条件修正 + ⚠️ 实测警示
- `./flows/README.md`：05 状态保持 ✅ PASS（备注实测语义）
