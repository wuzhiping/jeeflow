# Iteration #18 · 2026-09-23 · W17 · 驳回 reason 记录到 decision_memo

> **驱动**：W17（驳回原因未结构化保存到 audit 链）
> **核心发现**：engine `_merge_exec_into_instance` 已自动把 `comment / decision_reason / decision_memo` 合并到 `instance.variables`
> **核心成果**：✅ **tdd-flow scenario 支持 `:comment` 字段**，驳回场景自动传 3 字段，audit 链完整

---

## 1. 时间线（~30 分钟）

| 时段 | 工作 |
|------|------|
| 0~10 min | 验证 engine `_merge_exec_into_instance` 行为（已自动处理 comment）|
| 10~20 min | 改造 tdd-flow：parse_scenarios 支持 `:submitType:comment` 三段 + run_path 传 comment |
| 20~30 min | 测试 + 更新 Job Card + tests.json + iteration |

---

## 2. 核心发现（早就支持）

engine `_merge_exec_into_instance`（`vendor/jeeflow/engine.py`）：

```python
def _merge_exec_into_instance(base, exec_vars):
    out = dict(base)
    for k, v in exec_vars.items():
        if k.startswith("u_"):
            continue  # 跳过 u_*（operator 上下文）
        out[k] = v   # ✅ 其他所有键（含 comment/decision_reason/decision_memo）合并
    return out
```

execute 时传的任何非 u_* 字段自动存入 instance.variables。

**W17 不是"实现"，而是"利用"**。

---

## 3. tdd-flow 改造

### 3.1 parse_scenarios 支持 comment

旧格式：`name:json:submitType`
新格式：`name:json:submitType:comment`

```bash
--scenarios 'reject:{"amount":8000}:5:金额异常，需补充材料'
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                          comment 字段
```

### 3.2 run_path 自动传 3 字段

```python
if exec_submit_type in (2, 5) and comment:
    exec_args["comment"] = comment
    exec_args["decision_reason"] = f"{task_name} 驳回..."
    exec_args["decision_memo"] = comment
```

驳回时自动传 3 字段，无需用户手动写。

---

## 4. 测试证据

### 4.1 comment 自动存入 instance.variables
```
[reject] step 1: execute approve (submitType=5)
   ↓
instance.variables:
  comment = 金额异常，需补充材料          ← ✅ 自动保存
  decision_reason = approve 驳回后回到首个 task 节点  ← ✅
  decision_memo = 金额异常，需补充材料    ← ✅
```

### 4.2 baseline 自动包含 comment 字段
```
📋 已保存 baseline: v0_4_20260923...
✅ 对比 baseline: v0_4_20260923...  ✅ 无差异
```

### 4.3 ea-compliance
```
OVERALL: 43/43 PASS (100.0%)
```

---

## 5. 闭环示意

```
┌── "驳回 reason 怎么结构化保存？" ──┐
↓                              │
读 engine _merge_exec_into_instance │
↓                              │
发现已自动处理 comment/decision_*  │
↓                              │
改造 tdd-flow scenario 格式       │
↓                              │
✓ comment/decision_reason/decision_memo 3 字段都进 instance.variables │
↓                              │
→ 飞轮第 18 圈（audit 链）✅    │
```

---

## 6. 度量（飞轮 18 圈累积）

| 指标 | Iter#15 | Iter#16 | Iter#17 | **Iter#18** |
|------|---------|---------|---------|-------------|
| §9 检查项 | 43 | 43 | 43 | **43** |
| **驳回 audit 字段** | ❌ | ❌ | ❌ | **3 字段** |
| scenario 语法字段 | 2 | 2 | 2 | **3 (+comment)** |

**关键变化**：从"驳回只有 reason 字符串"→"驳回含 3 个结构化字段入 audit 链"。

---

## 7. 经验沉淀

### 7.1 Decision Mem 字段使用建议
| 字段 | 用途 | 必填 |
|------|------|------|
| `comment` | UI 显示用 | ✅ 必填（≥ 10 字）|
| `decision_reason` | 统计/分类 | ✅ 必填（一句话）|
| `decision_memo` | 详细审计 | ⭕ 选填（≥ 20 字）|

### 7.2 scenario 语法扩展
```
name:json                        ← v1
name:json:submitType             ← v2 (Iter#10)
name:json:submitType:comment     ← v3 (Iter#18)
```

向后兼容：旧格式仍工作（submit_type 默认 1，comment 默认 None）。

### 7.3 audit 链价值
- **回溯**：能查到每个 instance 为什么驳回
- **统计**：驳回原因分布（金额异常 / 材料不全 / ...）
- **改进**：高频驳回原因 = 流程优化点

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第十八轮迭代 · W17 驳回 audit 链**：① **核心发现** engine `_merge_exec_into_instance` 已自动把 comment/decision_reason/decision_memo 合并到 instance.variables；② **tdd-flow parse_scenarios 扩展** 支持 `:comment` 字段（`name:json:submitType:comment`）；③ **run_path 自动传 3 字段**（驳回场景）；④ **tests.json 更新**（reject scenario 加 comment）；⑤ **Job Card approve.md 更新**（含 3 字段使用建议 + 自动保存机制说明）；⑥ **baseline 自动 v0_4** 含 comment；⑦ ea-compliance 43/43 PASS；⑧ 新增 iterations/2026-09-23_reject-memo.md。 |