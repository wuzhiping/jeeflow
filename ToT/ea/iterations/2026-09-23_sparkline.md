# Iteration #26 · 2026-09-23 · W34 · dashboard sparkline

> **驱动**：W34（trend 表太简陋，加 sparkline 增强可视化）
> **核心成果**：✅ **SVG sparkline** —— per-flow 最近 10 次跑的趋势柱状图（颜色编码 + tooltip）

---

## 1. 时间线（~25 分钟）

| 时段 | 工作 |
|------|------|
| 0~10 min | 设计：SVG inline（无外部依赖）+ 每根柱 = 一次跑 |
| 10~20 min | 实现 render_sparkline + dashboard trend 列 |
| 20~25 min | 修复字段错误（summary → per-flow entry）+ 5 次跑测试 |

---

## 2. 设计

### 2.1 SVG sparkline 结构
```xml
<svg width="120" height="24">
  <rect x="0"   y="4" width="23" height="20" fill="#28a745">
    <title>run 1: 3/3</title>
  </rect>
  <rect x="24"  y="4" width="23" height="20" fill="#28a745">
    <title>run 2: 3/3</title>
  </rect>
  ...
</svg>
```

### 2.2 颜色编码
| 条件 | 颜色 | 含义 |
|------|------|------|
| `passed == total` | 🟢 `#28a745` | 全通过 |
| `ratio >= 0.8` | 🟢 `#28a745` | 大部分通过 |
| `ratio >= 0.5` | 🟡 `#ffc107` | 部分通过 |
| `ratio < 0.5` | 🔴 `#dc3545` | 大部分失败 |
| `total == 0` | ⚪ `#ccc` | 无数据 |

### 2.3 高度
- 全通过：`height - 4`（最大 20px）
- 部分通过：按 `ratio = passed / total` 缩放

---

## 3. 使用方式

### 3.1 自动启用
```bash
./ToT/bin/jf python3 ToT/sop/tdd-flow.py \
    --tests-file ToT/tdd/tests.json --all-flows \
    --report-html ToT/tdd/dashboard.html
# → dashboard.html 含 sparkline 列（per-flow 最近 10 次）
```

### 3.2 浏览器打开
```bash
open ToT/tdd/dashboard.html
```

---

## 4. 测试证据

### 4.1 sparkline 渲染
```
共 2 个 sparkline（每 flow 一个）

sparkline 1 (fdep):
  run 1: 3/3  🟢  height=20
  run 2: 3/3  🟢  height=20
  run 3: 3/3  🟢  height=20
  run 4: 3/3  🟢  height=20
  run 5: 3/3  🟢  height=20

sparkline 2 (invoice-approval):
  ... 同样的 5 根绿柱
```

### 4.2 ea-compliance
```
OVERALL: 43/43 PASS (100.0%)
```

---

## 5. 闭环示意

```
┌── "trend 表太简陋" ──┐
↓                  │
设计 SVG sparkline   │
↓                  │
render_sparkline()  │
↓                  │
per-flow entry 字段 │
↓                  │
✓ 5 根绿柱显示     │
↓                  │
→ 飞轮第 26 圈 ✅  │
```

---

## 6. 度量（飞轮 26 圈累积）

| 指标 | Iter#25 | **Iter#26** |
|------|---------|-------------|
| §9 检查项 | 43 | **43** |
| dashboard 可视化 | trend 表 | **trend 表 + sparkline** |
| dashboard.html 大小 | 6266 B | **~7.5 KB** |
| **trend 颗粒度** | 全局 summary | **per-flow 最近 10 次** |

**关键变化**：从"全表数据"→"每 flow 趋势柱状图"。

---

## 7. 经验沉淀

### 7.1 SVG sparkline vs Canvas
| 维度 | SVG | Canvas |
|------|-----|--------|
| 可嵌入 HTML | ✅ | ❌（需 data URL）|
| 无 JS | ✅ | ❌ |
| 矢量缩放 | ✅ | ❌ |
| 单文件 HTML 友好 | ✅ | ❌ |

### 7.2 sparkline 适用场景
- ✅ 趋势可视化（时间序列）
- ✅ 类别对比（flow vs flow）
- ✅ 状态聚合（DONE/REJECT 比例）
- ❌ 详细数值（用 table）

### 7.3 颜色编码原则
- 🟢 通过类（绿）
- 🟡 警示类（黄）
- 🔴 失败类（红）
- ⚪ 无数据（灰）

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第二十六轮迭代 · W34 sparkline**：① **`render_sparkline()` 函数**（SVG inline，width=120 height=24）；② **颜色编码**：绿（通过）/ 黄（部分）/ 红（失败）/ 灰（无数据）；③ **每 flow 一列 sparkline**（最近 10 次跑）；④ **tooltip** 显示 "run N: passed/total"；⑤ **修 build_dashboard_entry** 加 `passed_scenarios` 字段（之前漏）；⑥ **修 sparkline** 用 per-flow entry 而非 summary；⑦ **5 次跑测试全过**：每 flow 5 根绿柱 + tooltip 正确；⑧ ea-compliance 43/43 PASS；⑨ 新增 iterations/2026-09-23_sparkline.md。 |