# FB-0011 补丁索引 (FIX-DOC-4)

> **FB**: FB-0011 (execute 时 tf_* 变量只写到 task.variable, 不到 instance.variables)
> **修复编号**: FIX-DOC-4
> **来源**: W40 Day 2 · flowuser 反馈 (实例 92116610518127 复测 PASS 实证)
> **执行人**: bro (按 `FREEZE.md §6` 例外, FB 关联)

---

## 1. 修订范围

3 个文件, 3 处变更:

| # | 文件 | 章节 | 变更 |
|---|------|------|------|
| 1 | `docs/flow.md` | §7 (新增 §7.1 变量作用域铁律) | **改 + 增** |
| 2 | `docs/AGENTS.md` | §7 (新增变量作用域约束) | **改 + 增** |
| 3 | `docs/known-issues.md` | §115 (新增) | **增** |

---

## 2. 补丁文件清单

| 文件 | 内容 |
|------|------|
| `flow.md.patch.md` | docs/flow.md §7 修订方案 (变量作用域铁律 + 示例) |
| `AGENTS.md.patch.md` | docs/AGENTS.md §7 修订方案 (新增约束) |
| `known-issues-§115.md` | docs/known-issues.md §115 全文 (新增) |
| `README.md` | 补丁索引 (本文件) |

---

## 3. 核心改进 (一句话)

**铁律**: `f_*` (启动持久化) vs `tf_*` (执行临时) vs `u_*` (操作人), 决策节点 expr 只能读 `f_*` (instance 级) 和 `u_*`, **不能读 tf_*** (task 级).

---

## 4. 变量作用域表 (应文档化)

| 前缀 | 作用域 | 持久化 | 可见节点 | 示例 |
|------|--------|--------|----------|------|
| `f_*` | instance | ✅ (启动持久化) | 全部下游 | `f_amount` (报销金额) |
| `tf_*` | task | ❌ (执行临时) | 当前 task + 后置拦截器 | `tf_mgr_decision` (经理审批结果) |
| `u_*` | execution context | ❌ (操作人临时) | 当前 execute + 当前 task | `u_userId` (当前操作人) |
| `submitType` | execution context | ❌ | 当前 execute | `submitType=0/1/2/3/5/6/20` |
| `KEY_NEXT_NODE_OPERATOR` | instance | ✅ | 下游预指派 | `tf_nextNodeOperator` (FIX-T6) |

---

## 5. 申请流程 (给 bro)

```
1. bro review 三个 patch 文件
2. 同意 → 直接 apply 到 docs/ (FREEZE.md §6 例外)
3. 跑 sla/check.sh 验证 (docs 章节通过)
4. 通知 flowuser 闭环
5. FB-0011 status → closed + lessons_learned
6. 同步 README.md / weekly / metrics
```

---

## 6. 风险评估

- **风险**: 低 (仅文档新增 + 修订)
- **兼容性**: 0 影响 (现有流程仍按现有规则运行)
- **回滚**: 易

⏱️ Last updated: 2026-09-24 · W40 Day 4 · 等 bro apply
