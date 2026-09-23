# Iteration #21 · 2026-09-23 · W27 · report-json dashboard

> **驱动**：W27（CI 集成需要结构化输出）
> **核心成果**：✅ **`--all-flows` + `--report-json`** —— 一键跑所有 flow + 生成 dashboard JSON

---

## 1. 时间线（~1 小时）

| 时段 | 工作 |
|------|------|
| 0~15 min | 设计 dashboard JSON schema（summary + flows[]）|
| 15~45 min | 重构 main：拆 main_legacy + 加 run_all_flows + 加 build_dashboard |
| 45~55 min | 修复 compare_with_baseline 函数（重构时删了）+ run_single_flow 返回 3 值 |
| 55~65 min | 测试 + ea-compliance |

---

## 2. 设计

### 2.1 dashboard JSON schema
```json
{
  "version": "1.0",
  "generated_at": "2026-09-23T07:50:08",
  "summary": {
    "total_flows": 2,
    "passed_flows": 2,
    "failed_flows": 0,
    "total_scenarios": 6,
    "passed_scenarios": 6,
    "all_passed": true
  },
  "total_elapsed_seconds": 0.699,
  "flows": [
    {
      "flow_name": "fdep",
      "exit_code": 0,
      "elapsed_seconds": 0.646,
      "passed": true,
      "scenario_count": 3,
      "scenarios": [
        {"name": "happy", "submit_type": 1, "state": "DONE", "task_count": 6, "actors": ["u_fdp_pm"]},
        {"name": "reject", "submit_type": 2, "state": "REJECT", "task_count": 2, "actors": ["u_fdp_pm"]},
        {"name": "resurrect", "submit_type": 5, "state": "DONE", "task_count": 8, "actors": ["u_fdp_pm"]}
      ],
      "static_errors": 0,
      "engine_errors": 0
    },
    {
      "flow_name": "invoice-approval",
      "exit_code": 0,
      ...
    }
  ]
}
```

### 2.2 三个新参数
| 参数 | 作用 |
|------|------|
| `--all-flows` | 迭代 tests.json 中所有 flow |
| `--report-json <path>` | 写 dashboard JSON 到指定路径 |
| `--tests-file <path>` | 提供 tests.json（all-flows 必需）|

---

## 3. 使用方式

### 3.1 一键回归（所有 flow）
```bash
./ToT/bin/jf python3 ToT/sop/tdd-flow.py \
    --tests-file ToT/tdd/tests.json \
    --all-flows \
    --report-json ToT/tdd/dashboard.json
# 2/2 flows PASSED
# 6/6 scenarios OK
# Dashboard JSON 写到 ToT/tdd/dashboard.json
```

### 3.2 CI 集成示例
```yaml
- name: TDD regression
  run: |
    ./ToT/bin/jf python3 ToT/sop/tdd-flow.py \
      --tests-file ToT/tdd/tests.json \
      --all-flows \
      --report-json dashboard.json

- name: Upload dashboard
  uses: actions/upload-artifact@v3
  with:
    name: tdd-dashboard
    path: dashboard.json
```

---

## 4. 重构要点

### 4.1 main 拆为 2 个函数
```python
async def main():
    parser + args parse
    if args.all_flows:
        return await run_all_flows(args)  # 多 flow 模式
    return await run_single_flow(args, None)  # 单 flow 模式

async def run_single_flow(args, flow_path_ignored):
    start_time = time.time()
    exit_code, raw_data = await main_legacy(args)
    elapsed = time.time() - start_time
    return exit_code, raw_data, elapsed

async def run_all_flows(args):
    # 迭代 tests.json flows
    # 对每个 flow 调 run_single_flow
    # 收集 entries + 生成 dashboard
```

### 4.2 修过的 bug
- `compare_with_baseline` 在重构时被误删 → 重新写
- `run_single_flow` 返回 3 值（exit, raw, elapsed）需要解包对应

---

## 5. 测试证据

### 5.1 --all-flows 跑 2 flow
```
🚀 --all-flows 模式：迭代 2 个 flow

============================================================
📊 DASHBOARD SUMMARY
============================================================
   flows: 2/2 PASSED
   scenarios: 6/6 OK
   total elapsed: 0.70s
   all_passed: True

✅ ALL FLOWS PASSED

📄 Dashboard JSON: /opt/jupyter/src/RD/projects/jeeFlow/ToT/tdd/dashboard.json
```

### 5.2 单 flow 仍工作（向后兼容）
```
./ToT/bin/jf python3 ToT/sop/tdd-flow.py ToT/flows/fdep.json \
    --scenarios 'happy:{}|reject:{}:2|resurrect:{}:5'
# ✅ PASSED — 3 scenarios OK
```

### 5.3 ea-compliance
```
OVERALL: 43/43 PASS (100.0%)
```

---

## 6. 闭环示意

```
┌── "CI 需要结构化输出" ──┐
↓                     │
设计 dashboard JSON schema  │
↓                     │
重构 main：拆 main_legacy + run_all_flows + build_dashboard │
↓                     │
修 compare_with_baseline（重构时误删） │
↓                     │
✓ 一键跑 2 flows + dashboard.json │
↓                     │
→ 飞轮第 21 圈（CI 集成）✅ │
```

---

## 7. 度量（飞轮 21 圈累积）

| 指标 | Iter#20 | **Iter#21** |
|------|---------|-------------|
| §9 检查项 | 43 | **43** |
| **dashboard 输出** | ❌ | **✅ JSON** |
| **--all-flows 一键跑** | ❌ | **✅ 2/2 PASSED** |
| tdd-flow CLI 参数 | 10 | **11 (+report-json/+all-flows)** |

**关键变化**：从"每次手动跑每个 flow"→"一键跑所有 + 结构化 dashboard"。

---

## 8. 经验沉淀

### 8.1 dashboard schema 设计原则
- **summary**：CI 快速读取（all_passed / counts）
- **flows[]**：详细（每个 flow 的 scenarios / errors / actors）
- **json-stable**：忽略瞬态字段（timestamp / instance_id），确保 CI diff 干净

### 8.2 CI 集成模板
```yaml
# .github/workflows/tdd.yml
- name: TDD regression
  run: ./ToT/bin/jf python3 ToT/sop/tdd-flow.py --tests-file ToT/tdd/tests.json --all-flows --report-json dashboard.json
- uses: actions/upload-artifact@v3
  with: {name: dashboard, path: dashboard.json}
```

### 8.3 重构教训
- 大改动前先备份函数列表（避免重构时漏删/多删）
- `--all-flows` 等新参数应在 main 入口处早期检查，避免 main_legacy 重复解析

---

## 9. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第二十一轮迭代 · W27 report-json dashboard**：① **加 `--all-flows` 参数**（迭代 tests.json 所有 flow）；② **加 `--report-json <path>` 参数**（写 dashboard JSON）；③ **重构 main**：拆为 main + run_all_flows + run_single_flow + main_legacy；④ **加 build_dashboard_entry / build_dashboard 函数**；⑤ **修 compare_with_baseline**（重构时误删，重写）；⑥ **修 run_single_flow 返回 3 值**；⑦ **dashboard JSON schema** 含 summary + flows[]（每个 flow 含 scenarios + errors + actors）；⑧ **3 测试全过**：单 flow / all-flows / ea-compliance；⑨ 新增 iterations/2026-09-23_report-json.md。 |