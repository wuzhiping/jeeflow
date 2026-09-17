# 13-countersign-one-vote-veto 测试日志

**日期**：2026-09-17 11:05
**测试文件**：`./flows/13-countersign-one-vote-veto.json`
**结论**：✅ **PASS**（ONE_VOTE_VETO 正确触发）

---

## 1. 流程结构（4 节点 / 3 边）

```
start → apply(applicant) → task1(PARALLEL, ONE_VOTE_VETO, userA/userB/userC) → end
```

## 2. 关键字段

| 字段 | 值 |
|---|---|
| `performType` | 1（会签） |
| `countersignType` | `PARALLEL` |
| `countersignCompletionCondition` | `ONE_VOTE_VETO` |
| `assignee` / `field.candidateUsers` | `userA,userB,userC` |

## 3. 测试步骤

### 3.1 启动

```bash
startAndExecute → inst=91761628727146
state=10 activeTasks=3
apply    → user1     DONE
task1    → userA     DOING
task1    → userB     DOING
task1    → userC     DOING
```

### 3.2 userA DISAGREE (submitType=20)

```bash
processTask/execute -d '{"processTaskId":...,"submitType":20,"operator":"userA"}'
```

### 3.3 实测结果

```
state=20 activeTasks=0
apply    → user1     state=20 DONE
task1    → userA     state=20 DONE
task1    → userB     state=99 ABANDONED
task1    → userC     state=99 ABANDONED
```

**流程通过**：state=20 DONE（**注意：不是 state=45 REJECT**）

## 4. 引擎路径

`engine.py:94-104`：

```python
ct = cur_node.properties.get("countersignType", "")
cs_cond = str(cur_node.properties.get("countersignCompletionCondition", "") or "").strip()
try:
    cs_veto = ct != "" and cs_cond.upper() == "ONE_VOTE_VETO" and \
        int(vars_.get(KEY_SUBMIT_TYPE, -1)) == int(SubmitType.COUNTERSIGN_DISAGREE)
except (ValueError, TypeError):
    cs_veto = False
```

`engine.py:121-123`：

```python
if ct == "PARALLEL" and not cs_veto:
    doing = await self.repo.find_doing_tasks(inst.id)
    if doing:
        return  # PARALLEL 门控：还有其他 doing，不流转
```

**cs_veto=True 路径**：
- submitType=20 + ONE_VOTE_VETO → cs_veto=True
- 跳过 PARALLEL 门控 → 流程正常流转到 end
- 完成者 task1 state=20 DONE（软拒绝，**不是 reject**）
- 剩余 DOING 任务被 `engine.abandon_remaining_countersign` 置为 state=99 ABANDONED

## 5. 关键发现

### 5.1 ONE_VOTE_VETO 语义

| 字段 | 软拒绝语义 |
|---|---|
| TaskState | 完成任务 = 20 DONE（不是 45 REJECT） |
| InstanceState | 流程 = 20 DONE（不是 45 REJECT） |
| 其他会签成员 | state=99 ABANDONED |
| 后续流转 | 正常流转到下个节点 |

**这不是 reject 流程**，是"会签软拒绝→流程通过"。

### 5.2 与 REJECT (submitType=2) 区别

| submitType | 任务状态 | 流程状态 | 适用场景 |
|---|---|---|---|
| 2 (REJECT) | 20 DONE | **45 REJECT**（实例级终止） | 通用驳回 |
| 20 (COUNTERSIGN_DISAGREE) | 20 DONE | **20 DONE**（流程通过） | 会签软拒绝 |

### 5.3 cs_cond 引擎识别（实测）

引擎**仅**识别 `cs_cond.upper() == "ONE_VOTE_VETO"` 字符串：

- `"ONE_VOTE_VETO"` → 触发软拒绝门控 ✅
- 其他字符串（如 `"#nrOfCompletedInstances==2"`）→ 走 `RatioCapableEngine` 扩展逻辑（07 已修复）

## 6. 文档同步

`./docs/state.md §2`、`./docs/AGENTS.md §5.8`、`./docs/known-issues.md §15` 已记录 ONE_VOTE_VETO 语义。**实测验证通过**。

## 7. 结论

| 项 | 状态 |
|---|---|
| PARALLEL 会签创建 | ✅ 3 个 task1 都 DOING |
| ONE_VOTE_VETO 触发 | ✅ userA submitType=20 立即流转 |
| 完成者 task 状态 | ✅ state=20 DONE |
| 剩余成员 | ✅ state=99 ABANDONED |
| 流程完整跑通 | ✅ state=20 DONE |

**整体**：✅ PASS

## 8. 服务

PID 3365271 在 8101 运行中，healthz UP。
