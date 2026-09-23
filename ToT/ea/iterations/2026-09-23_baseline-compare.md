# Iteration #14 · 2026-09-23 · W20 · tdd-flow baseline 对比

> **驱动**：W20（让 baseline 不仅"留档"还能"回归"）
> **核心成果**：✅ **`--compare-baseline`** —— tdd-flow 可对比历史 baseline JSON，自动检测 regression，CI 可用

---

## 1. 时间线（~45 分钟）

| 时段 | 工作 |
|------|------|
| 0~10 min | 设计对比字段（scenarios / static_errors / engine_errors / results）|
| 10~25 min | 实现 `compare_with_baseline()` + 提取 signature 函数 |
| 25~40 min | 测试：相同（✅） / 跨流程（diff） / 故意改（exit 1） |
| 40~50 min | ea-compliance 43/43 PASS + 写 iteration |

---

## 2. 设计

### 2.1 对比什么？
- ✅ scenarios（数量 + 名字 + variable + submit_type）
- ✅ static_errors / engine_errors 数量
- ✅ 每个 scenario 的 final.state
- ✅ 每个 scenario 的 task_count / task_names / actors_per_task
- ✅ 每个 scenario 的 variables_top_keys（自动忽略 u_* user info）

### 2.2 忽略什么？
- ❌ timestamp（每次跑都不同）
- ❌ instance_id（每次跑都不同）
- ❌ create_time / update_time
- ❌ u_* 开头的用户信息（u_userId / u_realName 等）

### 2.3 退出码
- 无差异：exit 0
- 有差异：exit 1（CI 可 catch regression）

---

## 3. 使用方式

```bash
# 1. 第一次跑 + 保存 baseline
./ToT/bin/jf python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json \
    --scenarios 'happy:{}|reject:{}:2|resurrect:{}:5' \
    --save-baseline
# → 生成 ToT/tdd/test_fdep_baseline_v0_5_<ts>.md + 同名 .json

# 2. 后续跑 + 对比（CI 可用）
./ToT/bin/jf python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json \
    --scenarios 'happy:{}|reject:{}:2|resurrect:{}:5' \
    --compare-baseline 'test_fdep_baseline_v0_5_20260923071955.json'
# → ✅ 无差异（或 ❌ 列出 diff）
```

---

## 4. 测试证据

### 4.1 完全一致（✅ exit 0）
```
[happy] DONE → DONE
[reject] REJECT → REJECT
[resurrect] DONE → DONE

📊 对比 baseline: test_fdep_20260923071955.json
✅ 无差异（与 baseline 完全一致）
exit code: 0
```

### 4.2 故意改（❌ exit 1）
```
scenarios: 加了 'extra' scenario

📋 对比摘要：
❌ [extra] state —→DONE, tasks 0→6
✅ [happy] state DONE→DONE, tasks 6→6
✅ [reject] state REJECT→REJECT, tasks 2→2
✅ [resurrect] state DONE→DONE, tasks 8→8

exit code: 1
```

### 4.3 跨流程（invoice vs fdep）
```
❌ [small]: state None→DONE, task_names None→['submit','pay'],
   actors_per_task None→{'submit': ['u_fdp_pm'], 'pay': ['u_carol']}
```
正确识别出两个流程的差异（task names 不同 / actors 不同）。

### 4.4 ea-compliance
```
OVERALL: 43/43 PASS (100.0%)
```

---

## 5. 闭环示意

```
┌── "baseline 只是留档吗？能不能 catch regression？" ──┐
↓                                                │
加 --compare-baseline 参数                       │
↓                                                │
extract_signature 提取关键字段（忽略瞬态）         │
↓                                                │
逐字段对比 + 友好 diff 摘要                        │
↓                                                │
差异时 exit 1（CI 可用）                          │
↓                                                │
→ 飞轮第 14 圈（回归保护）✅                     │
```

---

## 6. 度量（飞轮 14 圈累积）

| 指标 | Iter#11 | Iter#12 | Iter#13 | **Iter#14** |
|------|---------|---------|---------|-------------|
| §9 检查项 | 43 | 43 | 43 | **43** |
| tdd-flow CLI 参数 | 5 | 6 | 6 | **7 (+compare)** |
| **regression detection** | ❌ | ❌ | ❌ | **✅** |

**关键变化**：从"baseline 留档"→"baseline 对比 + regression catch"。

---

## 7. 经验沉淀

### 7.1 baseline 对比 vs 留档
- **留档（--save-baseline）**：留证据，不强制对比
- **对比（--compare-baseline）**：CI 强制，regression 即 fail
- **最佳实践**：每次正式改动后跑对比，diff 0 才算 PASS

### 7.2 signature 提取原则
- **保留**：state / task structure / actor / variable keys
- **忽略**：时间戳 / instance_id / 用户信息（u_*）
- **原因**：确保"语义相同但物理不同"的两个 baseline 能正确识别为"无差异"

### 7.3 CI 集成示例
```bash
# CI 步骤：
# 1. 跑 tdd-flow + compare-baseline
./ToT/bin/jf python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json \
    --scenarios '...' \
    --compare-baseline 'test_fdep_baseline_v0_5_*.json'

# 2. 检查 exit code（0=PASS，1=FAIL）
# 3. FAIL 时把 diff 输出 attach 到 PR 评论
```

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第十四轮迭代 · W20 baseline 对比**：① **加 `--compare-baseline <path>` 参数**；② **`compare_with_baseline()` 函数**：提取 signature（忽略瞬态字段）+ 逐字段对比 + 友好 diff 摘要；③ **3 测试全过**：完全一致（exit 0）/ 故意改（exit 1）/ 跨流程（识别差异）；④ **支持跨流程对比**（invoice vs fdep）；⑤ **CI 友好**（diff → exit 1）；⑥ ea-compliance 43/43 PASS；⑦ 新增 iterations/2026-09-23_baseline-compare.md。 |