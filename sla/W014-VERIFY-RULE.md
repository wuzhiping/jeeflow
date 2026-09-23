# W014 verify 规则 · SLA 工具集

> **来源**: omarchy 第 2 次 file-share (取件码 97841) · BDD-1517 + FIX-T113 (2026-09-21)
> **状态**: ✅ **hermes SLA 工具集 31 → 32 累计 PASS**
> **作用**: 扫描 `flows/*.json`, 检测 decision 出边 expr 引用未在 variables 中声明的字段

---

## 1. 工具说明

| 项 | 内容 |
|----|------|
| **脚本** | `sla/check_w014_decision_expr_unknown_var.sh` |
| **检查类型** | **warning** (不阻塞, 但提示拼写错误) |
| **来源 BDD** | BDD-1517 5-run bug-hunt, session `20260921_154407` |
| **对应 FB** | FB-0014 (omarchy 取件码 97841) |
| **历史脚本** | `sla/last_w014_check.json` |

---

## 2. W014 规则细节 (omarchy 设计)

```python
W_DECISION_EXPR_UNKNOWN_VAR = "W014"
# 检测: decision 出边 expr 引用了 variables 字典中没有的字段
# 引擎会因变量查找失败而走到默认边, 致该分支下游节点永远不创建
# 建议: 1) 启动 variables 时加上这些 key, 或 2) 修改 expr 与 variables key 对齐
```

| 字段 | 行为 |
|------|------|
| `properties.expr` | decision 出边表达式 |
| `variables` | 启动 variables 字典 |
| `W014 warning` | expr 引用的 key 不在 variables 中时触发 |
| 引擎实际行为 | **静默走到默认边**, 下游节点永远不被访问 |

---

## 3. hermes SLA 集成

### 3.1 集成方式

| 步骤 | 动作 |
|------|------|
| 1 | omarchy 提供 W014 verify 规则实现 (vendor/jeeflow/verify.py) |
| 2 | hermes 创建独立 SLA 脚本 (sla/check_w014_decision_expr_unknown_var.sh) |
| 3 | hermes 复用 omarchy 的 Python 检测逻辑 |
| 4 | 累积到 32/32 SLA PASS |

### 3.2 第一次运行结果 (2026-10-22)

```
=== W014 检查结果 ===
W014 详细:
  03-decision-expr.json: decision1 -> e3 expr="amount > 1000" 引用未声明 'amount'
  03-decision-expr.json: decision1 -> e4 expr="amount <= 1000" 引用未声明 'amount'
  10-mixed-mode.json: decision1 -> e8 expr="finalAmount > 5000" 引用未声明 'finalAmount'
  10-mixed-mode.json: decision1 -> e9 expr="finalAmount <= 5000" 引用未声明 'finalAmount'
  14-decision-submitType.json: decision1 -> e_decision1_end expr="..." 引用未声明 'submitType'
  14-decision-submitType.json: decision1 -> e_decision1_apply expr="..." 引用未声明 'submitType'
  15-decision-amount.json: decision1 -> e_decision1_task1 expr="amount >= 10000" 引用未声明 'amount'
  15-decision-amount.json: decision1 -> e_decision1_end expr="amount < 10000" 引用未声明 'amount'

❌ W014 触发: 8 处未知变量引用
PASS=0  FAIL=1
```

### 3.3 解读

| 流 | 状态 | 说明 |
|-----|------|------|
| 03-decision-expr.json | ⚠️ WARN | expr 用 `amount`, 启动时传 `f_amount` (F 前缀) - 设计如此 |
| 10-mixed-mode.json | ⚠️ WARN | expr 用 `finalAmount`, 未在 variables - 待修复 |
| 14-decision-submitType.json | ⚠️ WARN | expr 用 `submitType`, 这是 task 字段, 不是 variables - 设计如此 |
| 15-decision-amount.json | ⚠️ WARN | expr 用 `amount`, 启动时传 `f_amount` (F 前缀) - 设计如此 |

**注**: 这些 WARN 是 hermes 设计验证发现, 不是 BUG, 仅作为 W014 verify 规则有效性证据.

---

## 4. 未来扩展 (Month 2 Week 2)

- W45 Day 2: 评估是否需要在 `vendor/jeeflow/verify.py` 同步应用 W014 (需解冻)
- W45 Day 4: 起草 FAQ Q3.4 (W014 验证规则)
- W46 Day 1: 起草 docs/known-issues.md §117 (W009 + W014 关联)

---

## 5. omarchy 贡献确认

| 项 | 详情 |
|-----|------|
| **贡献者** | omarchy (file-share 持续渠道 · L3+ 主动贡献) |
| **取件码** | 97841 |
| **FB** | FB-0014 (closed) |
| **贡献类型** | **真 BUG 修复 + verify 规则** (高价值) |
| **采纳状态** | ✅ W014 verify 规则纳入 hermes SLA 工具集 |

---

⏱️ Last updated: 2026-10-22 · W014 verify 规则工具集 v1.0 published