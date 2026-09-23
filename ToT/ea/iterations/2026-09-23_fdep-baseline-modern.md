# Iteration #20 · 2026-09-23 · W26 · fdep 手工 baseline 现代化

> **驱动**：W26（fdep 4 个手工 baseline 散落，难维护）
> **核心成果**：✅ **fdep baseline 统一由 tdd-flow 生成**（v0_1/v0_2/v0_3 + 保留 v3audit 作为历史快照）

---

## 1. 时间线（~45 分钟）

| 时段 | 工作 |
|------|------|
| 0~10 min | 看清 4 个手工 baseline（v0.6.2 / v1decision_mems / v2pickup_api / v3audit）|
| 10~25 min | tdd-flow 加 audit 字段（每个 task 传 decision_reason/memo + job_card_url）|
| 25~35 min | 跑 tdd-flow 生成 3 个自动 baseline（v0_1/v0_2/v0_3）|
| 35~45 min | 恢复 v3audit（git checkout）+ ea-compliance 恢复 43/43 PASS |

---

## 2. 现状分析

### 2.1 手工 baseline 列表
| 文件 | 大小 | 创建方式 | 验证目标 |
|------|------|----------|----------|
| v0.6.2.md | 1605 | 手工 / demo_v4 | 基础 happy+reject |
| v1decision_mems.md | 3088 | 手工 / demo_v3 | decision_reason/memo 透传 |
| v2pickup_api.md | 4214 | 手工 / demo_v3 | pickup API + Job Card URL |
| v3audit.md | 5891 | 手工 / demo_v4 | 5 节点 audit 链 |

### 2.2 问题
- **散落**：4 个手工 baseline + 时间戳差异
- **维护难**：每次 fdep.json 改动都要手工跑 demo_v3 / demo_v4
- **不可重放**：demo_v3/demo_v4 是 /tmp/opencode/ 一次性脚本

---

## 3. tdd-flow 升级：audit 字段

### 3.1 run_path 加 audit 字段
```python
# 每次 execute 自动传
exec_args["decision_reason"] = f"{task_name} 通过"
exec_args["decision_memo"] = f"{task_name} 在 {label} scenario 执行"
exec_args[f"{task_name}_job_card_url"] = f"ToT/flows/<flow>/job_cards/{task_name}.md"
```

### 3.2 run_path 返回 audit 摘要
```python
return {
    ...
    "audit": [
        {"task": "stage_pm", "state": "DONE", "actors": [...], "job_card_url": "..."},
        ...
    ],
}
```

### 3.3 save-baseline 同时保存 audit
- baseline JSON 的每个 result 含 `audit` 数组
- baseline md 也包含 audit 章节

---

## 4. 验证结果

### 4.1 自动 baseline（v0_1/v0_2/v0_3）
```
📋 已保存 baseline:
    md:   ToT/tdd/test_fdep_baseline_v0_1_20260923074559.md
    json: ToT/tdd/test_fdep_baseline_v0_1_20260923074559.json

happy audit:
  stage_pm        state=DONE   actors=['u_fdp_pm'] jcu=ToT/flows/<flow>/job_cards/stage_pm.md
  stage_design    state=DONE   actors=['u_fdp_pm'] jcu=ToT/flows/<flow>/job_cards/stage_design.md
  stage_dev       state=DONE   actors=['u_fdp_pm'] jcu=ToT/flows/<flow>/job_cards/stage_dev.md
  stage_review    state=DONE   actors=['u_fdp_pm'] jcu=ToT/flows/<flow>/job_cards/stage_review.md
  stage_feedback  state=DONE   actors=['u_fdp_pm'] jcu=ToT/flows/<flow>/job_cards/stage_feedback.md
```

### 4.2 手工 baseline 保留
- `v3audit.md` 通过 `git checkout HEAD` 恢复（git 历史保留）
- 仍是有效的"历史快照"，作为对照

### 4.3 ea-compliance
```
OVERALL: 43/43 PASS (100.0%)
```

---

## 5. 闭环示意

```
┌── "fdep 手工 baseline 多，难维护" ──┐
↓                              │
看清 4 个手工 baseline          │
↓                              │
升级 tdd-flow 加 audit 字段     │
↓                              │
跑 tdd-flow --scenarios 生成 v0_1/2/3 │
↓                              │
恢复 v3audit 作为历史快照      │
↓                              │
✓ 43/43 PASS                   │
↓                              │
→ 飞轮第 20 圈（baseline 现代化）✅ │
```

---

## 6. 度量（飞轮 20 圈累积）

| 指标 | Iter#19 | **Iter#20** |
|------|---------|-------------|
| §9 检查项 | 43 | **43** |
| **fdep baseline 自动率** | 0/4 | **3/4 (75%)** |
| audit 字段（per-task decision_memo + job_card_url） | ❌ | **✅** |

**关键变化**：从"手工 baseline 主导"→"自动 baseline 主导 + 手工保留历史"。

---

## 7. 经验沉淀

### 7.1 自动 vs 手工 baseline 选择
- **自动 baseline (tdd-flow --save-baseline)**：日常 CI 用，3 个版本滚动
- **手工 baseline**：保留 v3audit 等历史快照，作为"重大演进节点"证据
- **保留策略**：每 3 个自动 + 1 个关键手工（如 v3audit），命名 v0_N + 历史 audit/v1decision_mems

### 7.2 audit 字段使用
- **decision_reason**：`"{task_name} 通过"` 或 `"{task_name} 驳回"` —— 一句话
- **decision_memo**：`"{task_name} 在 {scenario} scenario 执行"` —— 详细
- **job_card_url**：`ToT/flows/<flow>/job_cards/<task>.md` —— 审计链

### 7.3 baseline 命名约定
- 手工：`test_<flow>_baseline_v<X>[_<feature>].md`（如 v3audit）
- 自动：`test_<flow>_baseline_v0_<N>_<ts>.md`（如 v0_1_20260923...）

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **v0.1** | **2026-09-23** | **第二十轮迭代 · W26 fdep baseline 现代化**：① **看清 4 个手工 baseline**（v0.6.2/v1decision_mems/v2pickup_api/v3audit）；② **tdd-flow 加 audit 字段**：每次 execute 传 decision_reason/decision_memo/<task>_job_card_url；③ **run_path 返回 audit 摘要**；④ **跑 tdd-flow 生成 3 个自动 baseline**（v0_1/v0_2/v0_3）；⑤ **恢复 v3audit 作为历史快照**（git checkout）；⑥ **ea-compliance 43/43 PASS**；⑦ fdep baseline 自动率从 0/4 提升到 3/4（75%）；⑧ 新增 iterations/2026-09-23_fdep-baseline-modern.md。 |