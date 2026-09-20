# TDD 测试: §110 FIX-T110 task 节点多出边隐式 fork 致实例提前 finish

> **测试日期**: 2026-09-20
> **关联 BUG**: flowuser 反馈 BUG-1（expense_report cashier_pay 跳过）
> **复现实例**: 92066757424129（v1 坏设计）/ 92067239349249（v2 修复 happy path）

## 1. 背景

flowuser 通过 hermes peer dm 提交 BUG-1:
- 现象: `f_amount=4800` 走 mgr_approve，mgr 同意后 `cashier_pay` task 应创建并等待执行
- 实际: instance.state=20 (DONE)，但 `cashier_pay` 仍为 DOING (state=10)，`cashier execute` 返回 code=99999999 "实例 state=20 不可执行任务"

## 2. 根因分析（本地 v1.9.0 复现确认）

```bash
# 复现脚本（已固化到 tdd/expense_report_repro.json）
curl -X POST http://127.0.0.1:8101/wf/processInstance/startAndExecute \
  -H 'Content-Type: application/json' \
  -d '{"processDefineId":20,"operator":"user1",...,"variables":{"f_amount":4800,...}}'
```

`vendor/jeeflow/engine.py:210` `_follow_edges` 遍历所有出边，不分流。当 `mgr_approve` 同时有 `e_mgr_to_cashier` + `e_mgr_to_rejected` 两条无条件出边时：

```python
for node in _follow_edges(flow, cur_node.id):
    await self._execute_node(flow, inst, node, operator, vars_)
```

执行顺序：
1. `_execute_node(cashier_pay)` → TYPE_TASK → `_create_task` → cashier_pay DOING
2. `_execute_node(end_rejected)` → TYPE_END → `inst.finish()` → instance.state=20 DONE

结果：instance DONE 但 cashier_pay 仍 DOING，execute 失败。

**这不是版本差异**：本地 v1.9.0+ 完整复现 flowuser 报告的现象。

## 3. 修复

### 3.1 新增 verify 规则 W012

`vendor/jeeflow/verify.py`:

```python
W_TASK_MULTI_OUT_TO_END = "W012"   # task 节点多条出边且 target 含 end（BUG-1: 隐式 fork 致实例提前 finish）
```

verify 逻辑：当 task 节点 ≥2 条出边且 target 含 end 节点时，发出警告（不阻塞 save/deploy，但写入 design.remark + 控制台 INFO 日志）。

### 3.2 正确流程设计 (v2)

**改动**: 在 `mgr_approve` / `dir_approve` 之后插入 decision 节点 `decision_mgr` / `decision_dir`，由 decision 的 `expr` 控制分支：

```
mgr_approve → decision_mgr
  ├─ expr="#tf_mgr_decision==1" → cashier_pay
  └─ expr="#tf_mgr_decision==2" → end_rejected

dir_approve → decision_dir
  ├─ expr="#tf_dir_decision==1" → cashier_pay
  └─ expr="#tf_dir_decision==2" → end_rejected
```

固化到 `tdd/expense_report_v2.json`。

## 4. BDD 验证（9/9 PASS）

`bdd/bdd-1501-1503-fix-t110-task-multi-out_20260920.sh`:

| # | 描述 | 期望 | 实际 |
|---|------|------|------|
| 110.1 | W012 在 mgr_approve + dir_approve 各发 1 次 | 2 | 2 ✅ |
| 110.2.1 | v1 mgr approve 后 instance.state=20 (BUG) | 20 | 20 ✅ |
| 110.2.2 | v1 cashier execute 返回 99999999 (BUG 签名) | 99999999 | 99999999 ✅ |
| 110.3.1 | v2 mgr approve (tf=1) 后 instance.state=10 | 10 | 10 ✅ |
| 110.3.2 | v2 cashier execute 返回 0 | 0 | 0 ✅ |
| 110.3.3 | v2 happy path 最终 state=20 | 20 | 20 ✅ |
| 110.3.4 | v2 mgr reject (tf=2) → end_rejected DONE | 20 | 20 ✅ |
| 110.3.5 | v2 dir path (f_amount=8000) cashier execute=0 | 0 | 0 ✅ |
| 110.3.6 | v2 dir path 最终 state=20 | 20 | 20 ✅ |

## 5. 实测实例 ID

| 实例 | 流程 | 操作 | 终态 |
|------|------|------|------|
| 92066757424129 | expense_report v1 | mgr approve | state=20 (BUG) + cashier_pay DOING |
| 92067239349249 | expense_report v2 | mgr approve(tf=1)→cashier | state=20 (DONE) |
| 92067260395525 | expense_report v2 | mgr approve(tf=2) | state=20 (end_rejected) |
| 92067260534792 | expense_report v2 | dir approve(tf=1)→cashier | state=20 (DONE) |

## 6. 关联文档

- `docs/BUGS.md` 新增 FIX-T110 条目
- `docs/known-issues.md` 新增 §110 详细说明
- `docs/flow.md` §3.3 增加「task 节点多出边 = 隐式 fork」反模式警告
- `AGENTS.md` §6 新增约束 #29

## 7. 引擎行为（保留）

引擎对 task 节点多出边的处理**保持现状**（遍历所有出边，不分流），原因是：
- 已有的 fork/decision 节点提供显式分流能力
- 改为「task 默认只走首边」会破坏已部署流程的兼容性
- W012 警告 + 文档明确约束足以引导设计者正确使用 decision 节点
