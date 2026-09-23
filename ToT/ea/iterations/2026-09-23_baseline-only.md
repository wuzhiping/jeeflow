# Iteration #22 · 2026-09-23 · W24 · baseline-only 模式

> **驱动**：W24（用户只改 baseline 时，不需要重跑测试）
> **核心成果**：✅ **`--baseline-only`** —— 不实跑引擎，**只验证 baseline 文件存在 + 完整**

---

## 1. 时间线（~30 分钟）

| 时段 | 工作 |
|------|------|
| 0~5 min | 设计：验证 baseline 存在 + scenarios 完整 |
| 5~20 min | 实现：在 run_all_flows 加 baseline-only 分支 |
| 20~30 min | 测试：2 scenarios 全过 / 缺 baseline 报错 |

---

## 2. 设计

### 2.1 三种 CI 模式对比
| 模式 | 实跑 | 时间 | 用途 |
|------|------|------|------|
| `--dry-run` | ❌ | 0.16s | 静态校验 |
| `--baseline-only` | ❌ | 0.15s | baseline 完整性检查 |
| 默认实跑 | ✅ | ~0.7s | 完整回归 |

### 2.2 baseline-only 通过条件
- baseline 文件存在（glob 解析）
- baseline JSON 可解析
- baseline 含 `scenarios` 字段
- 每个 scenario 的 `final.state` ∈ {DONE, REJECT}

---

## 3. 使用方式

### 3.1 仅检查 baseline 完整性（最快）
```bash
./ToT/bin/jf python3 ToT/sop/tdd-flow.py \
    --tests-file ToT/tdd/tests.json \
    --all-flows \
    --baseline-only \
    --report-json ToT/tdd/dashboard.json
# 0.15s（vs 实跑 0.7s）
```

### 3.2 CI 三阶段
```yaml
# Stage 1: PR 阶段（dry-run）
- run: tdd-flow --tests-file tests.json --all-flows --dry-run

# Stage 2: merge 阶段（baseline-only）
- run: tdd-flow --tests-file tests.json --all-flows --baseline-only

# Stage 3: release 阶段（实跑）
- run: tdd-flow --tests-file tests.json --all-flows
```

---

## 4. 测试证据

### 4.1 性能对比
| 模式 | 耗时 | 加速 |
|------|------|------|
| 实跑 | ~0.7s | 1x |
| **baseline-only** | **0.155s** | **4.5x** |

### 4.2 完整 baseline
```
✅ baseline 完整：3 scenarios, 3 results   (fdep)
✅ baseline 完整：3 scenarios, 3 results   (invoice-approval)

📊 DASHBOARD SUMMARY
   flows: 2/2 PASSED
   scenarios: 6/6 OK
   total elapsed: 0.00s
   all_passed: True
```

### 4.3 缺 baseline
```
❌ 1 FLOW(S) FAILED
   - fdep: exit=1
exit code: 1
```

### 4.4 ea-compliance
```
OVERALL: 43/43 PASS (100.0%)
```

---

## 5. 闭环示意

```
┌── "用户只改了 baseline，需要重跑吗？" ──┐
↓                                  │
加 --baseline-only 短路             │
↓                                  │
验证 baseline 完整性（4 条件）      │
↓                                  │
✓ 0.155s（4.5x 加速）             │
↓                                  │
→ 飞轮第 22 圈（CI 加速）✅       │
```

---

## 6. 度量（飞轮 22 圈累积）

| 指标 | Iter#21 | **Iter#22** |
|------|---------|-------------|
| §9 检查项 | 43 | **43** |
| **CI 三阶段** | ❌ | **✅ dry-run + baseline-only + 实跑** |
| baseline-only 速度 | - | **0.155s** |
| tdd-flow CLI 参数 | 12 | **13 (+baseline-only)** |

**关键变化**：从"2 阶段 CI"→"3 阶段 CI（含 baseline-only 加速）"。

---

## 7. 经验沉淀

### 7.1 baseline-only 适用场景
- ✅ baseline 文件刚更新（手动或 CI）
- ✅ baseline 结构完整性需要快速确认
- ❌ 实跑引擎（必须 default 模式）
- ❌ 检测回归（必须实跑 + 对比）

### 7.2 CI 三阶段策略
| 阶段 | 触发 | 模式 | 时间 |
|------|------|------|------|
| PR check | PR push | `--dry-run` | 0.16s |
| Merge check | merge to main | `--baseline-only` | 0.15s |
| Release | tag | 默认实跑 | 0.7s |

### 7.3 baseline 文件健康检查
- 文件存在性（glob 解析）
- JSON 格式可解析
- 含 `scenarios` 字段
- 每个 scenario final.state 在合法集（DONE/REJECT）

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第二十二轮迭代 · W24 baseline-only 模式**：① **加 `--baseline-only` 参数**；② **run_all_flows 加 baseline-only 分支**（验证 baseline 完整性）；③ **4.5x 加速**（0.7s → 0.155s）；④ **3 测试全过**：正常 baseline（exit 0）/ 缺 baseline（exit 1）/ ea-compliance（43/43）；⑤ **CI 三阶段支持**（PR dry-run + merge baseline-only + release 实跑）；⑥ 新增 iterations/2026-09-23_baseline-only.md。 |