# Iteration #10 · 2026-09-23 · tdd-flow 支持 variable + scenarios

> **驱动**：Iter#9 发现 tdd-flow.py 跑 invoice-approval 时卡住（decision expr 无法评估，无 variable 参数）
> **意义**：让 tdd-flow.py **真正可用**于任何流程（含 variable 的），并支持 **多 scenario 自动化** + **自动 baseline 生成**

---

## 1. 时间线（~1 小时）

| 时段 | 工作 |
|------|------|
| 0~10 min | 读 tdd-flow.py，理清结构 |
| 10~25 min | 加 `--variable` 参数（透传到 startAndExecute） |
| 25~40 min | 加 `--scenarios "name:json\|name:json"` 多场景 |
| 40~50 min | 修 2 bug：flow.auto 绕过 actor / KeyError 'taskName' |
| 50~60 min | 改 generate_md 支持多 scenario |
| 60~75 min | 加 `--save-baseline` 自动保存 baseline md |
| 75~90 min | 测试 + ea-compliance 自验证 + 写 iteration |

---

## 2. 关键改动（tdd-flow.py）

### 2.1 新增 3 个 CLI 参数
```python
--variable '{"amount": 500, "purpose": "办公"}'   # 单 variable 透传所有 path
--scenarios 'small:{"amount":500}|big:{"amount":8000}'  # 多 scenario
--save-baseline   # 自动保存 test_<flow>_baseline_v0_N.md
```

### 2.2 修 2 个 bug

**Bug 1**: actor 是 role 名（"主管"/"出纳"），用 `u_fdp_pm` 无法执行
- **修**：execute 时用 `flow.auto` 绕过 actor 校验
- 同时改用 `processInstance/detail.activeTaskList` 找 active task（不过滤 actor）

**Bug 2**: `KeyError: 'taskName'`（用 `t["taskName"]` 但 detail 字段是 `name`）
- **修**：`t.get("taskName") or t.get("name")`

### 2.3 md 生成支持多 scenario

- 之前：hardcoded `results["happy"]` + `results["reject"]`
- 现在：循环 `results.items()`，每 scenario 一节，含 variable 信息

---

## 3. 4 个测试结果

| 测试 | 命令 | 结果 |
|------|------|------|
| A | `--variable '{"amount":500}' --no-reject` | ✅ DONE (1 path) |
| B | `--scenarios 'small:...\|big:...'` | ✅ 2 paths DONE |
| C | `--scenarios ... --save-baseline` | ✅ 自动保存 v0_2 baseline |
| D | fdep (兼容老用法) | ✅ DONE + REJECT (无 regression) |

---

## 4. 闭环示意

```
┌── "tdd-flow 不能跑 variable 流程" ──┐
↓                                   │
加 --variable / --scenarios / --save-baseline │
↓                                   │
修 2 bug（flow.auto + KeyError）    │
↓                                   │
generate_md 支持多 scenario         │
↓                                   │
4 测试全过（含 fdep 兼容）          │
↓                                   │
ea-compliance 43/43 PASS 无 regression │
↓                                   │
→ 飞轮第 10 圈（自动化维度）✅      │
```

---

## 5. 度量（飞轮 10 圈累积）

| 指标 | Iter#1 | Iter#2 | Iter#3 | Iter#4 | Iter#5 | Iter#6 | Iter#7 | Iter#8 | Iter#9 | **Iter#10** |
|------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------------|
| §9 检查项 | 0 | 27 | 31 | 31 | 31 | 35 | 39 | 43 | 43 | **43** |
| 工具数 | 0 | 1 | 2 | 6 | 6 | 7 | 7 | 9 | 9 | **9** |
| **tdd-flow scenario 支持** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **✅** |

**关键变化**：从"tdd-flow 只能跑无 variable 流程" → "支持任意 variable + 多 scenario + 自动 baseline"。

---

## 6. 经验沉淀（SOP 候选）

### 6.1 tdd-flow 新用法（标准流程）
```bash
# 1. 跑 baseline（自动生成 test_<flow>_baseline_v0_N.md）
python3 ToT/sop/tdd-flow.py ToT/flows/<flow>.json \
    --scenarios 'small:{"x":1}|big:{"x":2}|edge:{"x":-1}' \
    --save-baseline

# 2. 验证 baseline 存在
ls ToT/tdd/test_<flow>_baseline_v0_*.md

# 3. 跑 flow_completeness 验证 §C3 = 100%
python3 ToT/sop/flow_completeness.py ToT/flows/<flow>.json
# → §C3 基线级 (15/15, 100%)
```

### 6.2 actor 绕过原则
- TDD/测试场景：execute 用 `flow.auto`（绕过 actor 校验）
- 生产环境：必须用 actor resolver（role → user_id）或 surrogate

### 6.3 scenario 设计原则
- **每个 decision 分支至少 1 个 scenario**
- **每个 edge case 1 个 scenario**
- **happy path 必须有**
- 用 `--save-baseline` 自动归档

---

## 7. 验证证据

### Test B 实跑
```
[small] instance=92281279856641 variable={'amount': 500, 'purpose': '办公'}
[small] step 1: execute pay (submitType=1)
[small] 终止 state=DONE (20)
✓ small final state = DONE

[big] instance=92281279866884 variable={'amount': 8000, 'purpose': '服务器'}
[big] step 1: execute approve (submitType=1)
[big] step 2: execute pay (submitType=1)
[big] 终止 state=DONE (20)
✓ big final state = DONE

✅ PASSED — 2 scenarios all DONE
```

### ea-compliance 自验证
```
OVERALL: 43/43 PASS (100.0%)
```

### fdep 兼容性
```
[happy] 终止 state=DONE (20)
[reject] 终止 state=REJECT (45)
✅ PASSED — happy state=DONE
```

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第十轮迭代 · tdd-flow 自动化增强**：① **加 `--variable` 参数**（JSON 字符串透传到 startAndExecute）；② **加 `--scenarios` 多场景**（`name:json\|name:json` 格式）；③ **加 `--save-baseline` 自动归档**；④ **修 2 bug**：flow.auto 绕过 actor / KeyError 'taskName'；⑤ **generate_md 支持多 scenario**（每 scenario 一节，含 variable 信息）；⑥ **fdep 兼容性**测试通过（happy+reject 仍工作）；⑦ ea-compliance 43/43 PASS 无 regression；⑧ 新增 iterations/2026-09-23_tdd-flow-variable.md。 |