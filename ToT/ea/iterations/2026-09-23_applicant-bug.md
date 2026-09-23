# Iteration #19 · 2026-09-23 · W18 · 修 engine applicant substring bug

> **驱动**：W18（Iter#12 发现的 substring bug，今天正式修复）
> **Bug**：`token = "tf_applicant"` 被错误解析为 `tf_u_alice`（应为 `u_alice`）
> **修复**：vendor/jeeflow/engine.py 用 word boundary 匹配替换 substring 匹配

---

## 1. 时间线（~30 分钟）

| 时段 | 工作 |
|------|------|
| 0~5 min | 复现 bug（tf_applicant → tf_u_alice）|
| 5~10 min | 修 engine.py 加 `_is_applicant_token()` word boundary 辅助函数 |
| 10~15 min | 改 2 处 substring 替换（line 379 同步版 + line 887 异步版）|
| 15~25 min | 验证：tf_applicant 现在正确解析为 u_alice |
| 25~30 min | regression 测试（invoice-approval + fdep）+ ea-compliance |

---

## 2. Bug 详解

### 2.1 错误代码（之前）
```python
# vendor/jeeflow/engine.py:379
if "applicant" in token:                    # ← substring 匹配
    token = token.replace("applicant", inst.operator)
```

### 2.2 问题
| token | "applicant" in token | token.replace() 结果 |
|-------|---------------------|---------------------|
| `"applicant"` | ✅ True | `"u_alice"` ✅ |
| `"tf_applicant"` | ❌ True（substring 命中）| `"tf_u_alice"` ❌ |
| `"applicant_role"` | ❌ True | `"u_alice_role"` ❌ |
| `"my_applicant"` | ❌ True | `"my_u_alice"` ❌ |

### 2.3 修复后代码
```python
def _is_applicant_token(token: str) -> bool:
    """FIX-W18：word boundary 匹配"""
    if token == "applicant":
        return True
    for part in token.split(","):
        if part.strip() == "applicant":
            return True
    return False

# 调用
if _is_applicant_token(token):
    token = inst.operator
```

现在只有 token 完整等于 `applicant`（或 `applicant,<other>` / `<other>,applicant`）才被替换。

---

## 3. 测试证据

### 3.1 修复前（bug）
```
test_applicant_task (assignee="tf_applicant"):  actors=['tf_u_alice', 'u_alice']  ❌
applicant_task (assignee="applicant"):          actors=['u_alice']  ✅
```

### 3.2 修复后
```
test_applicant_task (assignee="tf_applicant"):  actors=['u_alice']  ✅
applicant_task (assignee="applicant"):          actors=['u_alice']  ✅
```

### 3.3 Regression 测试
| 流程 | 结果 |
|------|------|
| invoice-approval 3 scenarios | ✅ PASSED（100%）|
| fdep 3 scenarios | ✅ PASSED（100%）|
| ea-compliance | ✅ 43/43 PASS |

---

## 4. 闭环示意

```
┌── "Iter#12 留下的 substring bug 还没修" ──┐
↓                                      │
复现 bug：tf_applicant → tf_u_alice     │
↓                                      │
设计 _is_applicant_token() 辅助函数     │
↓                                      │
改 2 处 substring 替换                  │
↓                                      │
✓ tf_applicant 现在解析为 u_alice     │
↓                                      │
✓ invoice-approval + fdep 无 regression│
↓                                      │
→ 飞轮第 19 圈（bug fix）✅           │
```

---

## 5. 度量（飞轮 19 圈累积）

| 指标 | Iter#18 | **Iter#19** |
|------|---------|-------------|
| §9 检查项 | 43 | **43** |
| **engine bug 修复** | 0 | **1 (substring → word boundary)** |
| 字面量 token 名限制 | "避开 applicant" | **无限制（任何 token 名都安全）** |

**关键变化**：从"用户必须避开 'applicant' 子串"→"任何 token 名都安全"。

---

## 6. 经验沉淀

### 6.1 substring vs word boundary 原则
- ❌ **`if "keyword" in token`** —— 易误命中（如 `tf_applicant`, `my_role`, `applicant_id`）
- ✅ **`if token == "keyword"`** —— 精确匹配
- ✅ **`_is_keyword_token(token)`** —— 处理逗号分隔（`"applicant,manager"` 等）

### 6.2 占位符命名现在完全自由
- `tf_applicant` ✓（不会被误替换，会到 vars_ 查找）
- `my_applicant_role` ✓
- `applicant_backup` ✓
- `applicant` ✓（内置占位符仍工作）

### 6.3 engine 修改影响范围
- `_resolve_actors` (async)：line 887 → 已改
- `_sync_resolve_actors` (sync, rollback 用)：line 379 → 已改
- 两者都用 `_is_applicant_token()` 统一逻辑

---

## 7. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第十九轮迭代 · W18 applicant substring bug 修复**：① **复现 bug**：`tf_applicant` 被错误解析为 `tf_u_alice`；② **加 `_is_applicant_token()` 辅助函数**（word boundary 匹配）；③ **改 2 处 substring 替换**（line 379 同步版 + line 887 异步版）；④ **验证**：tf_applicant 正确解析为 u_alice（actor=[u_alice]）；⑤ **regression 全过**：invoice-approval 100% + fdep 100% + ea-compliance 43/43 PASS；⑥ **占位符命名现在完全自由**（用户无需避开 "applicant" 子串）；⑦ 新增 iterations/2026-09-23_applicant-bug.md。 |