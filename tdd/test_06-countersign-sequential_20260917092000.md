# 06-countersign-sequential 测试日志

**日期**：2026-09-17 09:20
**测试文件**：`./flows/06-countersign-sequential.json`
**结论**：✅ PASS（串行逐人审批，loopCounter 正确递增）

---

## 1. 流程结构（4 节点 / 3 边）

```
start → apply(applicant) → task1(userA,userB, performType=1, countersignType=SEQUENTIAL) → end
```

**关键属性**：
- `task1` 会签节点，2 个 assignee 逗号分隔
- `performType=1`（会签）
- `countersignType=SEQUENTIAL`（串行会签，逐人审批）

## 2. 测试步骤

### 2.1 部署 + 启动

```bash
design_id=9, process_define_id=113
instance_id=91758619109268
```

### 2.2 启动后仅创建 userA 子任务

```json
{
  "state": 10,
  "activeTaskList": [{
    "id": "91758619109270",
    "taskName": "task1",
    "taskActorIdList": ["userA"],
    "taskState": 10,
    "variable": "{\"operatorList_task1\": [\"userA\", \"userB\"], \"loopCounter_task1\": 0, \"nrOfInstances_task1\": 2}"
  }],
  "tasks": [
    {"taskName": "apply", "taskActorIdList": ["applicant"], "taskState": 20},
    {"taskName": "task1", "taskActorIdList": ["userA"], "taskState": 10}
  ]
}
```

✅ SEQUENTIAL 启动时**仅创建第一个子任务**（userA），不是同时创建 userA+userB。

**`variable` 字段是 JSON 字符串**（与 known-issues.md #13 一致），包含串行状态：
- `operatorList_task1`: 全量 assignee 列表
- `loopCounter_task1`: 当前索引（0 → 1 → 退出）
- `nrOfInstances_task1`: 总人数

### 2.3 userA 完成 → userB 子任务创建

```bash
processTask/execute taskA (userA, submitType=0) → code:0
```

```json
{
  "activeTaskList": [{
    "taskName": "task1",
    "taskActorIdList": ["userB"],
    "taskState": 10,
    "variable": "{\"operatorList_task1\": [\"userA\", \"userB\"], \"loopCounter_task1\": 1, \"nrOfInstances_task1\": 2}"
  }],
  "tasks": [
    {"taskName": "apply", "taskActorIdList": ["applicant"], "taskState": 20},
    {"taskName": "task1", "taskActorIdList": ["userA"], "taskState": 20},
    {"taskName": "task1", "taskActorIdList": ["userB"], "taskState": 10}
  ]
}
```

✅ `loopCounter_task1` 从 0 递增到 1，userA 任务完成，userB 子任务创建。

### 2.4 userB 完成（最后一个）→ 流转到 end

```bash
processTask/execute taskB (userB, submitType=0) → code:0
```

```json
{
  "state": 20,
  "activeTaskList": [],
  "tasks": [
    {"taskName": "apply", "taskActorIdList": ["applicant"], "taskState": 20},
    {"taskName": "task1", "taskActorIdList": ["userA"], "taskState": 20},
    {"taskName": "task1", "taskActorIdList": ["userB"], "taskState": 20}
  ]
}
```

✅ state=20 DONE，最后一个完成时触发流转。

## 3. approvalRecord

```json
[
  {"taskName": "apply", "operator": "applicant", "finishTime": "2026-09-17 09:20:26"},
  {"taskName": "task1", "operator": "userA",     "finishTime": "2026-09-17 09:20:33"},
  {"taskName": "task1", "operator": "userB",     "finishTime": "2026-09-17 09:20:40"}
]
```

按完成时间排序，userA → userB，3 条记录。

## 4. 引擎行为总结

| 行为 | 实测 |
|---|---|
| 启动时子任务数 | 仅创建**第一个**（userA） |
| variable 状态 | operatorList 全量 + loopCounter 当前索引 + nrOfInstances 总数 |
| loopCounter 递增 | ✅ 0 → 1 → 退出（最后一个完成时） |
| 子任务顺序流转 | ✅ userA 完成 → userB 创建 |
| 最后一个完成触发下一节点 | ✅ userB 完成 → end → state=20 |
| 完成后未废弃（不像 ONE_VOTE_VETO） | ✅ userA 完成不废弃（自然流转） |

## 5. 文档同步

- ✅ 无新字段语义发现（`variable` 字段已知 JSON 字符串约束见 `docs/known-issues.md §13`）
- ✅ 串行行为符合 `docs/AGENTS.md §5.8` 表（修正后："仅最后一个通过即流转"）

## 6. 结论

06-countersign-sequential.json **完全通过**：
- ✅ 串行逐人创建子任务
- ✅ variable 字段含 operatorList/loopCounter/nrOfInstances
- ✅ loopCounter 正确递增
- ✅ 最后一个完成触发流转
- ✅ state=20 DONE，approvalRecord 顺序正确
