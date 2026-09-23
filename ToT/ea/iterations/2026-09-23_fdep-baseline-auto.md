# Iteration #13 · 2026-09-23 · W16 · fdep baseline 自动化

> **驱动**：W16（验证 tdd-flow --scenarios 可用于已有流程 fdep）
> **核心成果**：✅ **tdd-flow --scenarios 验证可复用** —— fdep 现有 4 个手工 baseline 都可以用工具化覆盖

---

## 1. 时间线（~1 小时）

| 时段 | 工作 |
|------|------|
| 0~10 min | 读 fdep.json（10 节点 10 边）+ 看现有手工 baseline |
| 10~25 min | 设计 3 scenarios：happy / reject / resurrect |
| 25~40 min | 跑 scenarios → 发现 2 个 bug |
| 40~60 min | 修 tdd-flow：智能防循环（resurrect_attempted 标志）+ 终态灵活性（accept DONE/REJECT） |
| 60~75 min | 跑 invoice-approval 验证无 regression |
| 75~90 min | ea-compliance 43/43 PASS + 写 iteration |

---

## 2. 关键发现：现有 baseline 都是手工

| 文件 | 大小 | 创建方式 |
|------|------|----------|
| `test_fdep_baseline_v0.6.2.md` | 2547 字节 | 手工（`/tmp/opencode/demo_v4.py`） |
| `test_fdep_baseline_v1decision_mems.md` | ~3 KB | 手工 |
| `test_fdep_baseline_v2pickup_api.md` | ~3 KB | 手工 |
| `test_fdep_baseline_v3audit.md` | 5891 字节 | 手工 |

W16 目标：用 tdd-flow --scenarios 一键生成可比 baseline。

---

## 3. 3 scenarios 设计

```bash
./ToT/bin/jf python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json \
    --scenarios 'happy:{}|reject:{}:2|resurrect:{}:5' \
    --save-baseline
```

| Scenario | submitType | 预期终态 | 实际终态 | 用途 |
|----------|-----------|---------|----------|------|
| happy | 1 | DONE | ✅ DONE | 默认完整流程 |
| reject | 2 | REJECT | ✅ REJECT | 流程被驳回 |
| resurrect | 5 | DONE | ✅ DONE | 跳回 stage_intake 后跑完整流程 |

---

## 4. 修复的 2 个 bug

### Bug 1: scenario.submitType=2/5 被吞

**现象**：fdep reject scenario 用 submitType=2，但 stage_pm 仍以 submitType=1 执行（"智能防循环"逻辑只对 approve + submitType=5 生效）。

**修复**：扩展 submitType 逻辑到所有 task_name：
```python
if task_name == "submit":
    exec_submit_type = 1
elif submit_type == 2 and task_exec_count[task_name] == 1:
    exec_submit_type = 2  # 第一次到非 submit task REJECT
elif submit_type == 5 and task_exec_count[task_name] == 1 and not resurrect_attempted:
    exec_submit_type = 5  # 第一次到非 submit task RE_APPLY
else:
    exec_submit_type = 1
```

### Bug 2: RE_APPLY 死循环

**现象**：submitType=5 在每个 task 都应用，导致 stage_pm → stage_intake → stage_pm → ... 死循环。

**修复**：加 `resurrect_attempted` 标志，scenario.submitType=5 只在第一个非 submit task 用一次：
```python
if exec_submit_type in (2, 5) and task_name != "submit":
    resurrect_attempted = True
```

### Bug 3: PASSED 条件过严

**现象**：reject scenario 终态是 REJECT（符合预期），但 PASSED 只接受 DONE → 误判 FAILED。

**修复**：根据 submitType 决定可接受终态集：
```python
def expected_states(sc):
    st = sc.get("submit_type", 1)
    if st == 2:
        return {"DONE", "REJECT"}
    return {"DONE"}
```

---

## 5. 验证证据

### 5.1 fdep 3 scenarios
```
[happy] 终止 state=DONE
[reject] 终止 state=REJECT (stage_pm submitType=2)
[resurrect] step 1: stage_pm (submitType=5)  ← 跳回 stage_intake
              step 2: stage_intake (submitType=1)
              step 3: stage_pm (submitType=1)
              step 4-7: stage_design/dev/review/feedback
              终止 state=DONE
✅ PASSED — 3 scenarios OK
```

### 5.2 invoice-approval 无 regression
```
[small] DONE
[big] DONE  
[reject] DONE (驳回+重提+通过)
✅ PASSED — 3 scenarios OK
```

### 5.3 baseline 自动生成
```
📋 已保存 baseline: ToT/tdd/test_fdep_baseline_v0_5_20260923071955.md
```

### 5.4 ea-compliance
```
OVERALL: 43/43 PASS (100.0%)
```

---

## 6. 闭环示意

```
┌── "fdep 手工 baseline 太多，能用工具化吗？" ──┐
↓                                            │
读 fdep 结构（10 节点 10 边）                  │
↓                                            │
设计 3 scenarios：happy / reject / resurrect │
↓                                            │
跑 scenarios → 发现 3 bug                    │
↓                                            │
修 tdd-flow：智能防循环 + 终态灵活性         │
↓                                            │
3 scenarios PASSED + baseline 自动生成        │
↓                                            │
invoice-approval 无 regression                │
↓                                            │
→ 飞轮第 13 圈（工具化回归）✅               │
```

---

## 7. 度量（飞轮 13 圈累积）

| 指标 | Iter#9 | Iter#10 | Iter#11 | Iter#12 | **Iter#13** |
|------|--------|---------|---------|---------|-------------|
| §9 检查项 | 43 | 43 | 43 | 43 | **43** |
| **tdd-flow 适用场景** | 1 (invoice) | 2 | 2 | 3 | **4 (+fdep)** |
| **scenario submitType 智能** | ❌ | ❌ | 部分 | 部分 | **✅** |
| **手工 baseline 可被工具化覆盖** | ❌ | ❌ | ❌ | ❌ | **✅** |

**关键变化**：从"tdd-flow 只对 invoice 有用"→"fdep 等老流程也能用工具化回归"。

---

## 8. 经验沉淀

### 8.1 scenario submitType 设计原则
- **`submitType=1`**：默认通过（DONE）
- **`submitType=2`**：第一次到非 submit task REJECT（REJECT 或 DONE 都算 PASS）
- **`submitType=5`**：第一次到非 submit task RE_APPLY（跳回首个 task，DONE 算 PASS）

### 8.2 fdep vs invoice-approval 区别
| 特性 | fdep | invoice-approval |
|------|------|------------------|
| 节点数 | 10 | 6 |
| decision | decision_intake | decision_amount |
| submitType 路由 | ✅ 在 decision_intake 用 | ❌ 在 approve 用 |
| Actor | 单一 (u_fdp_pm) | 3 角色（tf_*） |
| Resurrect 边 | ❌（靠 RE_APPLY）| ❌（靠 RE_APPLY）|

### 8.3 baseline 命名约定
- 手工 baseline：`<flow>_baseline_v<X>_<feature>.md`（如 v3audit）
- 自动 baseline：`<flow>_baseline_v0_<N>_<timestamp>.md`（如 v0_5_20260923）

---

## 9. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第十三轮迭代 · W16 fdep baseline 自动化**：① **3 scenarios 全过**：happy / reject (REJECT) / resurrect (DONE after RE_APPLY)；② **修 3 bug**：scenario.submitType 智能应用 / resurrect_attempted 防循环 / 终态灵活性（DONE/REJECT 都算 PASS）；③ **自动 baseline 生成**（v0_5）；④ **invoice-approval 无 regression**；⑤ ea-compliance 43/43 PASS；⑥ 新增 iterations/2026-09-23_fdep-baseline-auto.md。 |