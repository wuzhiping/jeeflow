# Iteration #11 · 2026-09-23 · W12 · invoice-approval 加驳回分支

> **驱动**：W12（Iter#9 留下的 TODO）
> **目标**：approve 驳回后回到 submit，员工可修改后重新提交（用引擎内置 RE_APPLY）
> **结论**：✅ **驳回 + 重新提交 + 通过 + 完成** 完整闭环跑通

---

## 1. 时间线（~1.5 小时）

| 时段 | 工作 |
|------|------|
| 0~15 min | 读 engine.py，找驳回机制（submitType=2 vs 5） |
| 15~30 min | 加 e_resurrect 边 + 测试 → 发现孤儿 task bug |
| 30~45 min | 移除 e_resurrect 边，改用 submitType=5 引擎内置 |
| 45~70 min | 改 tdd-flow.py：per-scenario submitType + 智能防循环 |
| 70~90 min | 3 scenarios 全过（small/big/reject）+ 自动 baseline |
| 90~110 min | 更新 CHANGELOG / NODES / Job Card |
| 110~120 min | ea-compliance 43/43 PASS + 写 iteration |

---

## 2. 关键发现：驳回机制

| submitType | 行为 | 引擎 API | 用途 |
|------------|------|----------|------|
| 1 (AGREE) | 通过，推进到下一节点 | `execute_process_task` | 默认 |
| 2 (REJECT) | instance.state=REJECT(45) | `execute_and_jump_to_end` | 永久驳回 |
| **5 (RE_APPLY)** | **跳回第一个 task 节点** | `execute_and_jump_to_first_task_node` | **驳回后重提** ✅ |
| 3 (ROLLBACK) | 退回上一节点 | `execute_and_jump_task` | 撤回上一步 |

**W12 选择 submitType=5**：保留 instance.state=DOING，员工可继续修改。

---

## 3. 关键 Bug + 修复

### Bug 1：孤儿 task（approve 通过后多了一个 submit）

**现象**：approve 通过（submitType=1）后，instance 同时有：
- pay（DOING）
- submit（DOING）← 孤儿

**原因**：`_follow_edges` 不区分 submitType，遍历所有出边。approve 有 2 条出边：`e4`(pay) 和 `e_resurrect`(submit)，**两条都创建 task**。

**修复**：移除 `e_resurrect` 边，用 `submitType=5` 让引擎内置逻辑跳回 submit。

### Bug 2：tdd-flow reject scenario 死循环

**现象**：submitType=5 应用到所有 task，导致 submit → approve → submit → approve 无限循环。

**修复**：智能判断 task 类型 + 出现次数
```python
if task_name == "submit":
    exec_submit_type = 1   # submit 永远用 1
elif submit_type == 5 and task_name == "approve" and task_exec_count[task_name] == 1:
    exec_submit_type = 5   # approve 第一次用 5（驳回）
else:
    exec_submit_type = 1   # 之后用 1（通过）
```

---

## 4. 3 scenarios 完整跑通

```
=== Test: small / big / reject ===
[small] step 1: execute pay → DONE ✅
[big] step 1-2: execute approve + pay → DONE ✅
[reject] step 1: execute approve (submitType=5)  ← 驳回
       step 2: execute submit (重新提交)
       step 3: execute approve (submitType=1)     ← 通过
       step 4: execute pay → DONE ✅
```

驳回 + 重新提交 + 通过 + 完成，**完整闭环**。

---

## 5. 闭环示意

```
┌── "W12: invoice-approval 加驳回分支" ──┐
↓                                       │
研究驳回机制：submitType=5 (RE_APPLY)    │
↓                                       │
加 e_resurrect 边 → 失败（孤儿 task）    │
↓                                       │
移除边，改用引擎内置 RE_APPLY           │
↓                                       │
改 tdd-flow 加 per-scenario submitType │
↓                                       │
智能防循环（submit 永远 1，approve      │
       第一次 5，之后 1）                │
↓                                       │
3 scenarios 全过 + baseline 自动生成   │
↓                                       │
→ 飞轮第 11 圈（驳回场景）✅            │
```

---

## 6. 度量（飞轮 11 圈累积）

| 指标 | Iter#1 | Iter#2 | Iter#3 | Iter#4 | Iter#5 | Iter#6 | Iter#7 | Iter#8 | Iter#9 | Iter#10 | **Iter#11** |
|------|--------|--------|--------|--------|--------|--------|--------|--------|--------|---------|------------|
| §9 检查项 | 0 | 27 | 31 | 31 | 31 | 35 | 39 | 43 | 43 | 43 | **43** |
| 流程示例数 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 3 | 3 | **3** |
| **驳回场景支持** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **✅** |

**关键变化**：从"驳回=流程终止"→"驳回=回到 submit，重新提交"。

---

## 7. 经验沉淀

### 7.1 驳回机制选择
- **submitType=5 (RE_APPLY)**：驳回后跳回第一个 task 节点（推荐 — 员工可修改）
- **submitType=2 (REJECT)**：驳回后流程终止（不推荐 — 除非业务不允许重提）
- **submitType=3 (ROLLBACK)**：驳回到上一节点（适合多步审批）

### 7.2 驳回边设计原则
- ❌ **不要**为驳回专门加 edge（`_follow_edges` 不区分 submitType → 孤儿 task）
- ✅ **用引擎内置** submitType=5/2/3
- ✅ **task.properties** 加 `onReject: true` 仅作文档标记

### 7.3 tdd-flow scenario submitType 语法
```
'small:{json}|big:{json}|reject:{json}:5'
                              ^^^^^^^^ 可选 submitType（默认 1）
```
智能处理 JSON 中的 `:`（brace 计数）。

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第十一轮迭代 · W12 驳回分支**：① **invoice-approval 加驳回**（submitType=5 RE_APPLY 跳回 submit）；② **删除 e_resurrect 边**（避免孤儿 task — `_follow_edges` 不区分 submitType）；③ **tdd-flow 加 per-scenario submitType**（`name:json:submitType`）；④ **智能防循环**（submit 永远 1，approve 第一次 5，之后 1）；⑤ **3 scenarios 全过**：small/big/reject（DONE 全部）；⑥ **自动 baseline v0_3** 生成；⑦ ea-compliance 43/43 PASS 无 regression；⑧ 新增 iterations/2026-09-23_reject-branch.md。 |