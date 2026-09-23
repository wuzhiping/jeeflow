# Iteration #15 · 2026-09-23 · W22 · tests.json 集中管理

> **驱动**：W22（多流程的 scenarios 难统一管理）
> **核心成果**：✅ **`ToT/tdd/tests.json`** —— 一个文件管理所有流程的 tdd-flow scenarios + actor 变量 + baseline

---

## 1. 时间线（~45 分钟）

| 时段 | 工作 |
|------|------|
| 0~10 min | 设计 tests.json 结构（version + flows 字典） |
| 10~25 min | 实现 `load_tests_file()` + `--tests-file` 参数 |
| 25~35 min | **修 2 bug**：save-baseline 缺 json / load_tests_file 调用顺序 |
| 35~45 min | 创建 tests.json + 测试 + iteration |

---

## 2. tests.json 设计

```json
{
  "version": "1.0",
  "flows": {
    "fdep": {
      "scenarios": "happy:{}|reject:{}:2|resurrect:{}:5",
      "operator": "u_fdp_pm",
      "top_vars": {},
      "baseline": "test_fdep_baseline_*.json"   // glob 自动选最新自动 baseline
    },
    "invoice-approval": {
      "scenarios": "small:{...}|big:{...}|reject:{...}:5",
      "operator": "u_fdp_pm",
      "top_vars": {"tf_manager": "u_bob", "tf_treasurer": "u_carol"},
      "baseline": "test_invoice-approval_baseline_*.json"
    }
  }
}
```

### 字段含义
- `scenarios`：tdd-flow 的 --scenarios 字符串
- `operator`：发起人 / 执行人（默认 u_fdp_pm）
- `top_vars`：顶级变量（用于 actor resolver 如 tf_*）
- `baseline`：glob 模式，自动选最新的自动 baseline（带 `_baseline_meta`）

---

## 3. 使用方式

### 3.1 跑单个流程（最简）
```bash
./ToT/bin/jf python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json \
    --tests-file ToT/tdd/tests.json
# 自动加载 scenarios / operator / top_vars / baseline
```

### 3.2 CI 集成（一键回归）
```bash
# 跑所有流程
for flow in fdep invoice-approval; do
    ./ToT/bin/jf python3 ToT/sop/tdd-flow.py ToT/flows/$flow.json \
        --tests-file ToT/tdd/tests.json || exit 1
done
```

### 3.3 添加新流程
```bash
# 1. 在 tests.json flows 加新条目
# 2. 跑 save-baseline 生成 baseline
# 3. CI 自动覆盖
```

---

## 4. 修复的 2 个 bug

### Bug 1: save-baseline 只生 md，没 json
**现象**：compare-baseline 需要 json（结构化），但 save-baseline 只写 md。
**修复**：同时复制 raw_data JSON 为 `test_<flow>_baseline_v<N>_<ts>.json`，加 `_baseline_meta` 标记。

### Bug 2: load_tests_file 调用顺序
**现象**：load_tests_file 在 global_top_vars 解析之后调用，导致 load_tests_file 设置的 args.top_vars 不生效。
**修复**：load_tests_file 移到 global_top_vars 解析**之后**，并**重新解析**被覆盖的 global_var / global_top_vars。

---

## 5. 测试证据

### 5.1 fdep（3 scenarios）
```
📋 加载 tests-file: ToT/tdd/tests.json
   flow: fdep
   scenarios: happy:{}|reject:{}:2|resurrect:{}:5

[happy] state=DONE
[reject] state=REJECT
[resurrect] state=DONE (after RE_APPLY)

📊 对比 baseline: test_fdep_baseline_v0_6_20260923072653.json
✅ 无差异（与 baseline 完全一致）
✅ PASSED — 3 scenarios OK
```

### 5.2 invoice-approval（actor resolver）
```
📋 加载 tests-file
   top_vars: {'tf_manager': 'u_bob', 'tf_treasurer': 'u_carol'}

[small] pay actors=['u_carol']  ← tf_treasurer 解析
[big] approve actors=['u_bob']    ← tf_manager 解析
       pay actors=['u_carol']     ← tf_treasurer 解析
[reject] 驳回+重提+通过

✅ PASSED — 3 scenarios OK
```

### 5.3 ea-compliance
```
OVERALL: 43/43 PASS (100.0%)
```

---

## 6. 闭环示意

```
┌── "scenarios 散在命令行 + 文档里，难管理" ──┐
↓                                         │
设计 tests.json（flows 字典）                │
↓                                         │
实现 load_tests_file                        │
↓                                         │
修 2 bug（json + 调用顺序）                  │
↓                                         │
fdep / invoice-approval 全过                 │
↓                                         │
→ 飞轮第 15 圈（流程集中管理）✅            │
```

---

## 7. 度量（飞轮 15 圈累积）

| 指标 | Iter#12 | Iter#13 | Iter#14 | **Iter#15** |
|------|---------|---------|---------|-------------|
| §9 检查项 | 43 | 43 | 43 | **43** |
| tdd-flow CLI 参数 | 6 | 6 | 7 | **8 (+tests-file)** |
| **集中管理** | ❌ | ❌ | ❌ | **✅ tests.json** |

**关键变化**：从"每个流程独立命令行"→"一个文件管理所有流程回归"。

---

## 8. 经验沉淀

### 8.1 tests.json 优点
- **单点真相**：所有回归场景一目了然
- **可 diff**：git diff 能看到测试演进
- **可 review**：PR 时一起 review 测试改动
- **CI 友好**：循环遍历 flows 一键跑所有回归

### 8.2 baseline glob 模式
- `test_<flow>_baseline_*.json`：所有 baseline（含手工 v3audit 和自动 v0_*）
- 自动选最新带 `_baseline_meta` 的（自动生成的优先）
- 避免手工 baseline 干扰

### 8.3 添加新流程的最佳实践
1. 写 flow.json + 5 份 docs + Job Cards
2. 在 tests.json 加 flow 条目（scenarios + top_vars + baseline）
3. 跑 save-baseline 生成 baseline
4. CI 自动覆盖
5. 任何改动只需 `tdd-flow.py <flow> --tests-file tests.json`

---

## 9. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第十五轮迭代 · W22 tests.json 集中管理**：① **`ToT/tdd/tests.json`**：集中 fdep + invoice-approval 的 scenarios / top_vars / baseline；② **tdd-flow 加 `--tests-file <path>` 参数** + `load_tests_file()` 函数；③ **save-baseline 同时生成 md + json**（compare-baseline 需要 json），加 `_baseline_meta` 标记；④ **baseline glob 智能选择**：自动 baseline 优先（带 `_baseline_meta`）；⑤ **修 2 bug**：save-baseline 缺 json / load_tests_file 调用顺序；⑥ **CI 集成**：`for flow in fdep invoice-approval; do ...`；⑦ ea-compliance 43/43 PASS；⑧ 新增 iterations/2026-09-23_tests-json.md。 |