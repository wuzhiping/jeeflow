# T7-Case-B §30 join 后 end 未触发 — 流程图设计缺陷

**测试时间**：2026-09-17 13:00  
**测试 ID**：`fix-multi-in-edge-join-fix_<TS>`  
**关联**：BDD Task 15 (position-transfer) / T7 Case A + known-issues §30

---

## 1. 现象

BDD Task 15 Case B 跑完后：
- 期望：state=20 DONE，highLight 含 `end`
- 实际：state=10 卡死，highLight `historyNodeNames=['apply','branch_A','branch_B','fanin_task','fork1','fanin_join']` — **`end` 不在历史**

`/tmp/jee-fix.log` 无任何 warning，说明端到端无解析异常。

---

## 2. 调查路径

### 2.1 引擎行为理解（基于 docs/flow.md + engine 公开语义）
- `engine.execute_process_task` 完成 task 后调用下游节点的执行（文档行为预期）。
- `join` 节点：所有 doing 任务完成时流转到下游 task 节点（docs/flow.md §3.2 "无活跃任务时放行"）。
- `end` 节点：触发 `inst.finish()` 或 `inst.reject()`（docs/flow.md §3.2）。

### 2.2 流程图边列表检查
fix-multi-in-edge-join.json edges：
```
e1: start → apply
e2: apply → fork1
e_to_A: fork1 → branch_A
e_to_B: fork1 → branch_B
e_A_fanin: branch_A → fanin_join
e_B_fanin: branch_B → fanin_join
e_join_fanin: fanin_join → fanin_task
```

**🚨 关键发现：fanin_task 没有任何出边，end 节点是孤儿（无入边任务节点指向）**

引擎按节点下游边列表流转 → `_follow_edges(fanin_task)` 返回 `[]` → end 节点永不触发 → state=10 卡死。

### 2.3 docs/flow.md 缺失约束
§3.2 仅说明 start/end/fork/join 节点的 properties，无 **"end 节点必须有入边任务节点"** 或 **"task 节点必须有出边（除非终点 end）"** 的设计约束，导致设计 Agent 可产出孤儿 end 流程图。

---

## 3. 根因

**流程图设计缺陷**：fanin_task → end 的边遗漏，end 节点成孤儿。

引擎行为符合文档预期：
- join 流转到 fanin_task ✓
- fanin_task 创建 task ✓
- 完成 fanin_task 后查下游节点 = 空，state 不变 ✗（符合语义）

---

## 4. 修复验证

创建 `fix-multi-in-edge-join-fix_<TS>.json`，新增边：
```json
{"id": "e_fanin_end", "sourceNodeId": "fanin_task", "targetNodeId": "end"}
```

执行流程：
1. apply (startAndExecute, user1) → state=10, branch_A+branch_B doing
2. branch_A agree (leader) → state=10, branch_B doing
3. branch_B agree (manager) → join 触发 fanin_task
4. fanin_task agree (userA) → 流转下游 end → inst.finish → state=20 ✅

**结果**：
- state=20 DONE
- highLight.historyNodeNames = `['apply','branch_A','branch_B','fanin_task','fork1','fanin_join','end']` ✅

---

## 5. 结论与改进

### 5.1 状态
- §30 不是引擎 bug，是 **流程图设计缺陷**
- 修复版流程图归档在 `./tdd/fix-multi-in-edge-join-fix_<TS>.json`

### 5.2 改进建议
**文档补充**：docs/flow.md §3.2 增加设计约束：
> - **流程图连通性**：所有 task / decision / fork / join 节点必须至少有一条出边（终点 end 节点除外）
> - **end 节点必须有入边**：禁止"孤立 end"——若 end 无任何 task/decision/join 节点指向，永不触发，实例卡 state=10
> - 设计 Agent 自检：扫描 edges 中 sourceNodeId 集合 ≠ 含 start/end 的 nodes 集合 ⇒ 警告
