# BDD #1801 设计文档 · auto-assignee-by-org 回归测试

> **起草日期**: 2026-10-23 (W44 Day 4)
> **状态**: 🟡 设计就绪, 等解冻后 W45 Day 2 实施
> **覆盖**: 5 个场景 (S1-S5)

---

## 1. BDD #1801 测试列表

| # | 场景 | 期望 | 双端 |
|---|------|------|------|
| #1801.1 | 单 org · 单 approver | resolved_assignees=["user-1"], source=auto_by_org | mem + pg |
| #1801.2 | 单 org · 多 approver | candidate_groups=["user-1","user-2"], source=auto_by_org | mem + pg |
| #1801.3 | org 不存在 · fallback_assignee | resolved_assignees=["user-X"] | mem + pg |
| #1801.4 | org 存在但无 approver · fallback_chain | candidate_groups=["user-3"], source=auto_by_org_fallback | mem + pg |
| #1801.5 | 全部为空 · E1803 异常 | error_code=E1803, message_contains="org org-A has no flow_approvers" | mem + pg |

---

## 2. BDD 脚本设计 (实施模板)

```bash
#!/bin/bash
# BDD #1801: auto-assignee-by-org 回归测试
# 状态: 设计就绪, 待解冻后 W45 Day 2 实施

set -e
HOST=http://localhost:8101
PASS=0
FAIL=0
RESULTS=""

assert_eq() {
  local desc="$1" actual="$2" expected="$3"
  if [ "$actual" = "$expected" ]; then
    PASS=$((PASS + 1))
    RESULTS="$RESULTS\n✅ #$1 [$desc]"
  else
    FAIL=$((FAIL + 1))
    RESULTS="$RESULTS\n❌ #$1 [$desc]  expected=$expected actual=$actual"
  fi
}

# ─────────────────────────────────────────────────────────────────────
# #1801.1 单 org · 单 approver
# ─────────────────────────────────────────────────────────────────────
echo "=== #1801.1 single org single approver ==="
# 配置 org_repo: org-A → user-1
# 创建流程: 1 task with auto_assignee_by_org=True
# 启动流程, 上下文 org_id=org-A
# 断言: task.assignee == "user-1"
# 断言: task.source == "auto_by_org"

# ─────────────────────────────────────────────────────────────────────
# #1801.2 单 org · 多 approver → candidate_groups
# ─────────────────────────────────────────────────────────────────────
echo "=== #1801.2 single org multiple approvers ==="
# 配置 org_repo: org-A → [user-1, user-2]
# 创建流程: 1 task with auto_assignee_by_org=True
# 断言: task.candidate_groups == ["user-1", "user-2"]
# 断言: task.source == "auto_by_org"

# ─────────────────────────────────────────────────────────────────────
# #1801.3 org 不存在 · fallback_assignee
# ─────────────────────────────────────────────────────────────────────
echo "=== #1801.3 missing org fallback_assignee ==="
# 配置: 空 org_repo
# 创建流程: 1 task with auto_assignee_by_org=True, fallback_assignee="user-X"
# 启动流程, 上下文 org_id=org-MISSING
# 断言: task.assignee == "user-X"

# ─────────────────────────────────────────────────────────────────────
# #1801.4 org 存在但无 approver · fallback_chain
# ─────────────────────────────────────────────────────────────────────
echo "=== #1801.4 org empty approvers fallback_chain ==="
# 配置 org_repo: org-A → {flow_approvers: [], fallback_chain: [user-3]}
# 创建流程: 1 task with auto_assignee_by_org=True
# 断言: task.candidate_groups == ["user-3"]
# 断言: task.source == "auto_by_org_fallback"

# ─────────────────────────────────────────────────────────────────────
# #1801.5 全部为空 · E1803 异常
# ─────────────────────────────────────────────────────────────────────
echo "=== #1801.5 all empty E1803 error ==="
# 配置 org_repo: org-A → {}
# 创建流程: 1 task with auto_assignee_by_org=True, no fallback
# 启动流程
# 断言: 引擎抛出 EngineError, code=E1803
# 断言: message 包含 "org org-A has no flow_approvers"

echo -e "\n=== BDD #1801 Results ==="
echo -e "$RESULTS"
echo "PASS=$PASS  FAIL=$FAIL"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
```

---

## 3. 双端测试

| 端 | 端口 | 启动命令 |
|----|------|----------|
| **mem** (本地) | 8101 | `python main.py` |
| **pg** (服务端) | 8102 | `python main_pg.py` |

**双端 PASS 标准**:
- mem 端: 5/5 PASS
- pg 端: 5/5 PASS
- 累计: 10/10 PASS

---

## 4. 实施依赖

### 解冻后路径

1. 修改 `vendor/jeeflow/engine.py` (`_resolve_assignees` 函数)
2. 新增 `vendor/jeeflow/org_repo.py` (内存仓库)
3. 新增错误码常量 E1801-E1805 (`vendor/jeeflow/engine.py`)
4. 实施本 BDD 脚本 (`bdd/bdd-1801-auto-assignee-by-org_20261024.sh`)
5. mem + pg 双端测试
6. 报告 PASS/FAIL

### 不解冻路径 (本设计仅保持)

1. 本设计文档 published (本文件)
2. FAQ v0.2 扩展 (新增 Q1.4 auto-assignee-by-org FAQ)
3. 流程模式示例 (`flows/auto-assignee-by-org-example.md`)
4. 等解冻后实施 (W47+ 或 Month 3)

---

## 5. 与 Phase 9 节奏的关系

- 本 BDD 设计为 Month 2 Week 1 核心交付
- 实施依赖解冻 + bro 签
- 不解冻 = Week 1 仅有设计, Week 2 转入 FAQ + 流程模式

---

## 6. 关联文档

- `roadmap/auto-assignee-by-org-v0.2.md` · 方案 v0.2
- `feedback/attachments/FB-0006-patches/tdd-1801-design.md` · tdd 用例
- `roadmap/month2-launch-checklist.md` · Month 2 启动清单
- `proposals/UNFREEZE-PROPOSAL-2026-09-22.md` · 解冻提案

---

⏱️ Last updated: 2026-10-23 (W44 Day 4) · BDD #1801 设计 v0.1
