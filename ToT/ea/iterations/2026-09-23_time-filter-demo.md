# Iteration #27 · 2026-09-23 · W36 + W35 · time filter + DEMO 文档

> **驱动**：W36（trend 表需要时间筛选）+ W35（团队需要培训材料）
> **核心成果**：① **dashboard 时间 filter**（4 按钮 + JS 过滤）② **EA DEMO.md**（团队培训实战手册）

---

## 1. 时间线（~45 分钟）

| 时段 | 工作 |
|------|------|
| 0~20 min | W36：filter-bar HTML + JS filterByDays + data-ts |
| 20~45 min | W35：DEMO.md（3 个 demo + FAQ + 速查 + 演练）|

---

## 2. W36 · dashboard 时间 filter

### 2.1 设计
```html
<div class="filter-bar">
  <button id="filter-1" onclick="filterByDays(1)">最近 1 天</button>
  <button id="filter-7" onclick="filterByDays(7)">最近 7 天</button>
  <button id="filter-30" onclick="filterByDays(30)">最近 30 天</button>
  <button id="filter-all" class="active" onclick="filterByDays(0)">全部</button>
  <span class="count">显示 X / Y</span>
</div>
```

### 2.2 JS 逻辑
```javascript
function filterByDays(days) {
  const rows = document.querySelectorAll('tr[data-ts]');
  rows.forEach(row => {
    const ts = new Date(row.dataset.ts);
    const diffDays = (now - ts) / (1000 * 60 * 60 * 24);
    if (days === 0 || diffDays <= days) {
      row.classList.remove('hidden');
    } else {
      row.classList.add('hidden');
    }
  });
}
```

### 2.3 CSS
```css
tr.hidden { display: none; }
.filter-bar button.active { background: #007bff; color: white; }
```

---

## 3. W35 · EA DEMO.md

### 3.1 结构
- **3 个 demo**（5/15/20 分钟）
- **FAQ**（5 个常见问题）
- **速查命令**（10 个核心命令）
- **3 个实战演练**（60 分钟动手）

### 3.2 Demo 内容
| Demo | 时长 | 内容 |
|------|------|------|
| Demo 1 | 5 min | 启动引擎 + dry-run + 实跑 + dashboard |
| Demo 2 | 15 min | flow_designer 设计 + completeness + 5 文档 + Job Cards + tests.json |
| Demo 3 | 20 min | GitHub Actions CI 集成（PR dry-run / merge baseline-only / push 实跑）|

### 3.3 实战演练
1. **完整端到端**（30 min）：设计一个新流程达 100%
2. **Bug 修复流程**（20 min）：改坏 → 跑 FAILED → 修 → PASSED
3. **CI 集成**（10 min）：改 workflow → push → 跑

---

## 4. 测试证据

### 4.1 dashboard 时间 filter
```
✅ HTML 含 5 处 filter 相关（filterByDays 函数 + 4 个按钮）
✅ ea-compliance 43/43 PASS
```

### 4.2 DEMO.md
```
✅ 创建 ToT/ea/DEMO.md（团队培训实战手册）
✅ 3 个 demo + FAQ + 速查 + 演练
```

---

## 5. 闭环示意

```
┌── "团队需要培训材料 + dashboard 可筛选" ──┐
↓                                       │
W36: filter 按钮 + JS + data-ts          │
↓                                       │
W35: DEMO.md 实战手册                     │
↓                                       │
✓ ea-compliance 43/43                    │
↓                                       │
→ 飞轮第 27 圈（团队就绪）✅            │
```

---

## 6. 度量（飞轮 27 圈累积）

| 指标 | Iter#26 | **Iter#27** |
|------|---------|-------------|
| §9 检查项 | 43 | **43** |
| dashboard 交互 | sparkline | **sparkline + 时间 filter** |
| 培训材料 | ❌ | **DEMO.md（实战手册）** |
| dashboard.html 大小 | ~7.5 KB | **~8 KB** |

**关键变化**：从"工具能用"→"团队能用"。

---

## 7. 经验沉淀

### 7.1 dashboard 时间 filter 设计原则
- **按钮分级**：1天 / 7天 / 30天 / 全部（覆盖常见需求）
- **data-ts 属性**：标准 HTML5 做法，无外部库
- **CSS .hidden class**：纯 CSS 隐藏，无 JS 状态管理

### 7.2 培训材料设计原则
- **demo 驱动**：3 个循序渐进（5/15/20 分钟）
- **可复制命令**：所有 demo 命令可直接 copy-paste
- **实战演练**：让学员动手而非只看
- **FAQ 优先**：常见问题前置（节省提问时间）

### 7.3 DEMO 文档更新
- 每次 EA 大版本更新，重写 DEMO 关键章节
- 实战演练随场景增加（如：测试驳回、resurrect）

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第二十七轮迭代 · W36 + W35**：① **W36 dashboard 时间 filter**：4 按钮（1/7/30/全部天）+ JS filterByDays + data-ts 属性；② **W35 EA DEMO.md**（团队培训实战手册：3 个 demo + FAQ + 速查 + 演练）；③ **dashboard.html ~8 KB**（+ filter 按钮 + JS 过滤）；④ **§5 新增 Pattern 31**（培训材料 —— "30 分钟内掌握 EA = 3 个 demo"）；⑤ **ea-compliance 43/43 PASS**；⑥ 新增 iterations/2026-09-23_time-filter-demo.md。 |