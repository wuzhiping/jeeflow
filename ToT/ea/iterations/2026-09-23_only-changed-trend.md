# Iteration #25 · 2026-09-23 · W28 + W32 · only-changed + 时间趋势

> **驱动**：W28（CI 智能选择 flow）+ W32（dashboard 看趋势）
> **核心成果**：① **`--only-changed`**（git diff 智能选择）② **dashboard 时间趋势表**（最近 10 次跑）

---

## 1. 时间线（~30 分钟）

| 时段 | 工作 |
|------|------|
| 0~15 min | W28：设计 + 实现 `--only-changed`（git diff + ls-files）|
| 15~30 min | W32：dashboard history 自动保存 + 时间趋势表 |

---

## 2. W28 · --only-changed

### 2.1 设计
检测 3 类 git 改动：
1. **工作区改动**：`git diff HEAD --name-only`（已 tracked 文件 modified）
2. **Staged 改动**：`git diff --cached --name-only`
3. **未追踪文件**：`git ls-files --others --exclude-standard`（新增未 add）

### 2.2 用法
```bash
# CI 默认：跑全部
./ToT/bin/jf python3 ToT/sop/tdd-flow.py \
    --tests-file ToT/tdd/tests.json --all-flows

# PR 智能：只跑改动
./ToT/bin/jf python3 ToT/sop/tdd-flow.py \
    --tests-file ToT/tdd/tests.json --all-flows --only-changed
```

### 2.3 测试证据
```
🔍 --only-changed: 只跑改动的 flow
   changed flows: ['fdep']
   flows: 1/1 PASSED   ← 只跑 fdep（invoice-approval 跳过）
```

---

## 3. W32 · dashboard 时间趋势

### 3.1 设计
- **自动保存**：每次 report-html 都保存 dashboard 到 `ToT/tdd/dashboard-history/dashboard_<ts>.json`
- **加载最近 10 次**：trend 表显示最近 10 次跑的 summary
- **保留 10 次**：超过 10 个文件时只保留最新 10 个（自动覆盖）

### 3.2 dashboard.html 新增趋势表
```
📈 历史趋势（最近 10 次）
┌──────────────────┬──────────────┬──────────────────┬────────┬──────┐
│ 时间              │ Flows (P/T) │ Scenarios (P/T) │ 总耗时 │ 状态 │
├──────────────────┼──────────────┼──────────────────┼────────┼──────┤
│ 2026-09-23 08:00 │ 2/2         │ 6/6              │ 0.65s  │ ✅   │
│ 2026-09-23 08:00 │ 2/2         │ 6/6              │ 0.65s  │ ✅   │
│ 2026-09-23 08:00 │ 2/2         │ 6/6              │ 0.65s  │ ✅   │
└──────────────────┴──────────────┴──────────────────┴────────┴──────┘
```

### 3.3 测试证据
```
3 次跑 → 3 个 history 文件
HTML 含 "历史趋势" 表
ea-compliance 43/43 PASS
```

---

## 4. 闭环示意

```
┌── "CI 跑所有 flow 浪费；dashboard 没趋势" ──┐
↓                                       │
git diff + ls-files 检测改动 → only-changed  │
↓                                       │
每次跑保存 dashboard.json → 自动 history  │
↓                                       │
dashboard.html 加 trend 表                  │
↓                                       │
→ 飞轮第 25 圈（智能化 + 可视化）✅     │
```

---

## 5. 度量（飞轮 25 圈累积）

| 指标 | Iter#24 | **Iter#25** |
|------|---------|-------------|
| §9 检查项 | 43 | **43** |
| tdd-flow CLI 参数 | 14 | **15 (+only-changed)** |
| dashboard.html 大小 | 5503 B | **6266 B** |
| **CI 智能选择** | ❌ | **✅ only-changed** |
| **时间趋势** | ❌ | **✅ trend 表** |

**关键变化**：从"全量跑 + 静态 dashboard"→"智能选择 + 趋势可视化"。

---

## 6. 经验沉淀

### 6.1 only-changed 适用场景
- ✅ PR 阶段（智能选择改动 flow 节省时间）
- ✅ 本地开发（改了哪个 flow 跑哪个）
- ❌ release 阶段（仍需跑全部）

### 6.2 git diff 三种类型都要考虑
- 工作区改动（modified）
- Staged 改动（cached）
- 未追踪文件（untracked）—— 这条最容易漏

### 6.3 dashboard history 价值
- **趋势可视化**：性能回归 / 通过率波动一眼可见
- **可对比**：vs 上一版本
- **可调试**：历史 baseline 可恢复

---

## 7. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第二十五轮迭代 · W28 + W32**：① **W28 --only-changed**：git diff 三种类型（工作区/staged/untracked）→ 智能选择 flow；② **W32 时间趋势**：每次跑保存 dashboard.json 到 history/；③ **dashboard.html 加 trend 表**（最近 10 次：时间/flows/scenarios/elapsed/状态）；④ **dashboard.html 6266 B**（+ trend 表 + JS 历史加载）；⑤ **CI 4 模式**：dry-run / baseline-only / 实跑 / only-changed；⑥ **3 测试全过**：only-changed 单 flow / only-changed 无改动（跑全部）/ trend history 自动保存；⑦ ea-compliance 43/43 PASS；⑧ 新增 iterations/2026-09-23_only-changed-trend.md。 |