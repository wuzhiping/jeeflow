# 08-countersign-sequential-approve 测试日志

**日期**：2026-09-17 10:05
**测试文件**：`./flows/08-countersign-sequential-approve.json`
**结论**：✅ **PASS** — 串行会签 + 后续审批节点完整通过

---

## 1. 流程结构（5 节点 / 4 边）

```
start → apply(applicant) → task1(SEQUENTIAL: userA → userB) → approve(leader) → end
```

| 节点 | 类型 | 关键配置 |
|---|---|---|
| apply | snaker:task | assignee=applicant, performType=0 |
| task1 | snaker:task | assignee=userA,userB, performType=1, countersignType=**SEQUENTIAL** |
| approve | snaker:task | assignee=leader, performType=0 |

**设计意图**：串行会签后由 leader 审批 → 结束。

## 2. 测试步骤

### 2.1 部署
```
design_id=9, process_define_id=113
```

### 2.2 启动 + 全流程

```bash
assignees=user1, operator=user1, title=08-seq-approve
```

## 3. 实测状态流转

| 步骤 | 操作 | state | activeTasks | 关键 task 状态 |
|---|---|---|---|---|
| 1 | startAndExecute | 10 | 1 | apply=20 DONE, task1(用户A)=10 DOING |
| 2 | userA agree | 10 | 1 | apply=20, task1(A)=20, **task1(B)=10 创建并 DOING** |
| 3 | userB agree | 10 | 1 | apply=20, task1(A)=20, task1(B)=20, **approve=10 DOING** |
| 4 | leader agree | **20** | **0** | apply=20, task1(A)=20, task1(B)=20, approve=20, 流程结束 |

## 4. 关键观察

### 4.1 SEQUENTIAL 会签正确
- **第 1 步**：仅创建 userA 的 task1（DOING），userB 不创建
- **第 2 步**：userA 完成 → 创建 userB 的 task1（DOING）—— **loopCounter 推进机制工作**
- **第 3 步**：userB 完成 → 流转到 approve

### 4.2 流转衔接
- task1（SEQUENTIAL）→ approve 边 `e2` 正常触发
- approve → end 边 `e_approve_end` 正常触发
- 4 个 task 全部 state=20 DONE，最终 state=20 DONE

### 4.3 task.variables 验证
按 06 测试经验，SEQUENTIAL 会签的 task.variables 应包含：
- `operatorList_task1: [userA, userB]`
- `loopCounter_task1: 0→1`（userA=0, userB=1）
- `nrOfInstances_task1: 2`

### 4.4 07 RatioCapableEngine 扩展无影响
由于 task1 是 SEQUENTIAL（不是 PARALLEL+RATIO），cs_cond 不被读取，引擎走默认 SEQUENTIAL 顺序逻辑（engine.py:105-120）。

## 5. 结论

| 项 | 状态 |
|---|---|
| SEQUENTIAL 会签 | ✅ 仅创建第一个 userA → 完成 → 创建 userB |
| 多节点衔接 | ✅ task1 → approve → end 流转正常 |
| 最终状态 | ✅ state=20 DONE |
| task 计数 | ✅ 4 task 全 DONE（apply + task1×2 + approve） |
| 07 修复回归 | ✅ 无影响 |

**整体**：✅ PASS

## 6. 服务

PID 3365271 在 8101 运行中，healthz UP。
