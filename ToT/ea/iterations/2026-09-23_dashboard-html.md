# Iteration #23 · 2026-09-23 · W29 · dashboard HTML 渲染

> **驱动**：W29（CI 集成需要人类可读输出）
> **核心成果**：✅ **`--report-html`** —— dashboard JSON 渲染为美化的 HTML，CI artifact 可直接预览

---

## 1. 时间线（~25 分钟）

| 时段 | 工作 |
|------|------|
| 0~5 min | 设计 HTML 结构（summary cards + flow table）|
| 5~20 min | 实现 `render_html_dashboard()` + `--report-html` 参数 |
| 20~25 min | 测试 + ea-compliance |

---

## 2. 设计

### 2.1 HTML 结构
```
<div class="container">
  <h1>TDD Regression Dashboard <span class="badge">✅ ALL PASSED</span></h1>
  <div class="summary">
    [5 个 summary card：Total/Passed/Failed Flows + Total/Passed Scenarios]
  </div>
  <table>
    [每个 flow 一行：name / passed / elapsed / scenarios list / errors]
  </table>
  <div class="footer">TDD Flow Regression · jeeflow EA · v2.31+</div>
</div>
```

### 2.2 关键样式
- **PASSED/FAILED 徽章**：绿色/红色
- **summary cards**：左色边 + 大数字
- **flow table**：tr.passed 浅绿 / tr.failed 浅红
- **state-DONE/REJECT/DOING**：颜色编码
- **响应式**：grid auto-fit

### 2.3 内联 CSS（无外部依赖）
- 单文件 HTML，可直接发邮件 / 上传 artifact
- 浏览器打开即用，无需服务器

---

## 3. 使用方式

### 3.1 同时生成 JSON + HTML
```bash
./ToT/bin/jf python3 ToT/sop/tdd-flow.py \
    --tests-file ToT/tdd/tests.json --all-flows \
    --report-json ToT/tdd/dashboard.json \
    --report-html ToT/tdd/dashboard.html
```

### 3.2 CI artifact 上传
```yaml
- uses: actions/upload-artifact@v3
  with:
    name: tdd-dashboard
    path: |
      ToT/tdd/dashboard.json
      ToT/tdd/dashboard.html
```

### 3.3 直接浏览器打开
```bash
open ToT/tdd/dashboard.html  # macOS
xdg-open ToT/tdd/dashboard.html  # Linux
```

---

## 4. 测试证据

### 4.1 生成结果
```
📄 Dashboard JSON: ToT/tdd/dashboard.json
🌐 Dashboard HTML: ToT/tdd/dashboard.html
```

### 4.2 HTML 文件
- 大小：3858 字节（内联 CSS）
- 内容：summary cards + flow table
- 样式：响应式，颜色编码

### 4.3 ea-compliance
```
OVERALL: 43/43 PASS (100.0%)
```

---

## 5. 闭环示意

```
┌── "CI 跑完输出 JSON 但人看不懂" ──┐
↓                            │
加 render_html_dashboard()    │
↓                            │
5 个 summary cards + 1 个 table │
↓                            │
✓ 单文件 HTML（3858 字节）    │
↓                            │
→ 飞轮第 23 圈（可视化）✅  │
```

---

## 6. 度量（飞轮 23 圈累积）

| 指标 | Iter#22 | **Iter#23** |
|------|---------|-------------|
| §9 检查项 | 43 | **43** |
| **dashboard 输出格式** | JSON only | **JSON + HTML** |
| tdd-flow CLI 参数 | 13 | **14 (+report-html)** |
| dashboard.html 大小 | - | **3858 字节** |

**关键变化**：从"机器可读 JSON"→"机器 + 人类双可读"。

---

## 7. 经验沉淀

### 7.1 dashboard 双格式设计原则
- **JSON（机器）**：CI / 脚本消费
- **HTML（人类）**：直接打开看 / email 附件 / Slack 通知
- **同时生成**：一份数据，两种消费方式

### 7.2 HTML 内联 vs 外部 CSS
- ✅ **内联**：单文件可移植，邮件友好，artifact 直接打开
- ❌ 外部 CSS：需要服务器 / 多个文件

### 7.3 dashboard.html 用法
- PR 评论：贴 HTML（部分平台支持）
- email 通知：附 dashboard.html
- 本地开发：`open dashboard.html`
- CI artifact：上传供后续 review

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第二十三轮迭代 · W29 dashboard HTML**：① **加 `--report-html` 参数**；② **`render_html_dashboard()` 函数**（单文件 HTML + 内联 CSS）；③ **summary cards + flow table 结构**；④ **样式：响应式 + 颜色编码（DONE 绿/REJECT 红/DOING 黄）**；⑤ **2/2 flows PASSED + 6/6 scenarios OK**；⑥ **dashboard.html 3858 字节**；⑦ ea-compliance 43/43 PASS；⑧ 新增 iterations/2026-09-23_dashboard-html.md。 |