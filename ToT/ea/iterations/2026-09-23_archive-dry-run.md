# Iteration #29 · 2026-09-23 · W39 · archive dry-run 预览

> **驱动**：W39（archive 前能先预览，避免误删/误传）
> **核心成果**：✅ **`--dry-run`** —— 显示会做什么，不实际执行任何操作

---

## 1. 时间线（~20 分钟）

| 时段 | 工作 |
|------|------|
| 0~5 min | 设计：3 个预览维度（tar.gz 内容 / report.md 预览 / 清理列表）|
| 5~20 min | 实现 + 测试 |

---

## 2. 设计

### 2.1 dry-run 预览 3 维度
1. **tar.gz 内容**：会收集哪些文件 + 文件清单
2. **report.md 预览**：报告前 30 行
3. **清理列表**：会删除哪些文件（仅 --clean 时）

### 2.2 dry-run 不做什么
- ❌ 不实际打包（tar -czvf 跳过）
- ❌ 不上传（file-share 跳过）
- ❌ 不清理（rm 跳过）
- ❌ 不修改 tests.json / baseline

---

## 3. CLI 用法

```bash
# 预览（不实际打包/上传/清理）
./ToT/bin/jf python3 ToT/sop/archive_flow.py invoice-approval --dry-run

# 预览 + 清理列表
./ToT/bin/jf python3 ToT/sop/archive_flow.py invoice-approval --dry-run --clean

# 实际执行（去掉 --dry-run）
./ToT/bin/jf python3 ToT/sop/archive_flow.py invoice-approval --clean
```

---

## 4. 测试证据

### 4.1 dry-run 输出
```
[4/5] 打包 tar.gz
   📦 预览 tar.gz: ToT/archive/20260923-081134_invoice-approval.tar.gz
   📁 包含 19 个文件：
      - flows/invoice-approval.json
      - flows/invoice-approval/CHANGELOG.md
      ...

[5/5] 上传 + 清理（dry-run 预览）
   跳过实际执行（--dry-run）
   --no-upload = False
   --clean = False
   --expire-days = 7

   📤 预览上传：curl POST http://10.17.1.26:12345/share/file/
      file=@ToT/archive/20260923-081134_invoice-approval.tar.gz
      expire_value=7, expire_style=day
   🧹 预览清理：见下方文件列表

🔍 DRY-RUN 预览完成（未实际执行任何操作）
   流程: invoice-approval
   预览 tar.gz: ToT/archive/20260923-081134_invoice-approval.tar.gz
   运行真实归档：去掉 --dry-run
```

### 4.2 dry-run --clean 输出
```
   🧹 预览清理：见下方文件列表
      将清理 2 个文件：
        - test_invoice-approval_20260923081135.json
        - test_invoice-approval_20260923081135.md
```

### 4.3 验证：没实际打包
```
最新 tar.gz: 20260923-080949_invoice-approval.tar.gz (Iter#28 生成)
新 dry-run 没生成新 tar.gz ✅
```

### 4.4 ea-compliance
```
OVERALL: 43/43 PASS (100.0%)
```

---

## 5. 闭环示意

```
┌── "archive 前能先预览吗？" ──┐
↓                       │
加 --dry-run 模式        │
↓                       │
预览 tar.gz + report + cleanup │
↓                       │
✓ 0 个实际打包          │
↓                       │
→ 飞轮第 29 圈（预览）✅ │
```

---

## 6. 度量（飞轮 29 圈累积）

| 指标 | Iter#28 | **Iter#29** |
|------|---------|-------------|
| §9 检查项 | 43 | **43** |
| archive 模式 | 实跑 | **实跑 + dry-run** |
| archive CLI 参数 | 3 | **4 (+dry-run)** |
| **安全性** | 不可预览 | **✅ 预览后执行** |

**关键变化**：从"一次性执行"→"预览 + 确认 + 执行"。

---

## 7. 经验沉淀

### 7.1 dry-run 设计原则
- **3 维度预览**：内容（tar.gz）+ 报告 + 清理
- **明确标识**："跳过实际执行" + "运行真实归档：去掉 --dry-run"
- **不修改任何东西**：无副作用
- **可重复执行**：每次都重新预览

### 7.2 dry-run 适用场景
- ✅ 第一次 archive 新流程
- ✅ archive 前想看会清理什么
- ✅ CI/CD pipeline（自动加 --dry-run 看能否成功）
- ❌ 真实归档（去掉 --dry-run）

### 7.3 与其他 dry-run 模式一致
- tdd-flow `--dry-run`：静态校验 + verify_flow（不实跑）
- archive `--dry-run`：预览 + 不打包 + 不上传 + 不清理
- 共性：跳过副作用，保留只读操作

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第二十九轮迭代 · W39 archive dry-run**：① **`--dry-run` 参数**；② **3 维度预览**（tar.gz 内容 / report.md 前 30 行 / 清理文件列表）；③ **跳过实际打包/上传/清理**；④ **明确标识"运行真实归档：去掉 --dry-run"**；⑤ **3 测试全过**：dry-run（19 文件预览）/ dry-run --clean（清理列表）/ 验证无副作用；⑥ ea-compliance 43/43 PASS；⑦ archive CLI 参数 3 → 4；⑧ 新增 iterations/2026-09-23_archive-dry-run.md。 |