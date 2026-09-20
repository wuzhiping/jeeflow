# TDD 测试: §112 FIX-T111 TaskState.ABANDON.updateUser 语义双义

> **测试日期**: 2026-09-21
> **关联 BUG**: flowuser 反馈 BUG-3（state=99 ABANDON updateUser 误为 createUser=发起人）
> **复现实例**: 92060892440807 (recruit_hire) / 92062553090304 (doc_review_v4) / 92069283659795 (本地验证)

## 1. 背景

flowuser 通过 hermes peer dm 提交 BUG-3:
- 现象: 比例会签完成条件命中后,被 ABANDON 的子任务 `updateUser=user1`(发起人),而非真正「触发废弃的人」
- 数据:
  - recruit_hire `92060892440807`: manager approve → deptLeader task state=99, `updateUser=user1`
  - doc_review_v4 `92062553090304`: userB approve → userC task state=99, `updateUser=user1`
- 影响: 审计追溯误判为「user1 手动废弃」,实际是「另一个会签人的提交触发完成条件」

## 2. 根因分析（本地 v1.9.0 源码确认）

`vendor/jeeflow/model.py` 原 `abandon()` API:

```python
def abandon(self, now) -> None:
    """废弃任务"""
    self.taskState = TaskState.ABANDONED
    self.updateTime = now
    # ❌ 不写 updateUser → 保持 createUser (=发起人)
```

调用方 (`main_common.py:248` 比例会签 / `engine.py:185` ONE_VOTE_VETO/merged / `facade.py:585` withdraw) 全部调用 `t.abandon(now)` 无 `abandoned_by` 参数。

## 3. 修复（FIX-T111）

### 3.1 `abandon()` API 升级

```python
def abandon(self, now, abandoned_by: str = "") -> None:
    """废弃任务
    abandoned_by (FIX-T111): 非空时同步写 task.updateUser = abandoned_by
    留空保持 backward compat (仅 taskState=99 + updateTime=now)
    """
    self.taskState = TaskState.ABANDONED
    self.updateTime = now
    if abandoned_by:
        self.updateUser = abandoned_by
```

### 3.2 调用方全部显式传 abandoned_by

| 文件:行号 | 触发场景 | abandoned_by 值 |
|---|---|---|
| `main_common.py:248` | RatioCapableEngine 比例/PARALLEL 条件命中 | `operator` (命中条件的人) |
| `engine.py:187` | ONE_VOTE_VETO/全部完成 节点 merged | `operator` |
| `engine.py:202` | ONE_VOTE_VETO REJECT (state=45) | `operator` (原本就写,保留) |
| `facade.py:586` | withdraw 流程撤回 | `operator` (撤回人) |

## 4. BDD 验证 (10/10 PASS)

`bdd/bdd-1511-1516-fix-t111-taskstate-abandon_20260921.sh`:

| # | 描述 | 期望 | 实际 |
|---|------|------|------|
| §112.1.1 | 比例会签 2/3 命中, instance.state=20 | 20 | 20 ✅ |
| §112.1.2 | ABANDON task.updateUser=userB (修复前是 user1) | userB | userB ✅ |
| §112.1.3 | ABANDON task.createUser=user1 (不变) | user1 | user1 ✅ |
| §112.1.4 | ABANDON task.finishTime=null (永久 NULL) | null | null ✅ |
| §112.2.1 | ONE_VOTE_VETO REJECT, instance.state=45 | 45 | 45 ✅ |
| §112.2.2 | 所有 ABANDON.updateUser=userA (否决人) | userA,userA | userA,userA ✅ |
| §112.3.1 | withdraw instance.state=30 WITHDRAW | 30 | 30 ✅ |
| §112.3.2 | leader ABANDON.updateUser=user1 (撤回人) | user1 | user1 ✅ |
| §112.4 | approvalRecord 包含 state=99 ABANDON (审计可见) | 1 | 1 ✅ |
| §112.5 | userC todoList=0 (ABANDON 不算待办) | 0 | 0 ✅ |
| §112.6 | backward compat: 默认参数不覆盖 updateUser | OK | OK ✅ |

## 5. 回归 (无 regression)

- P0 全量回归: 17/17 PASS
- P1 全量回归: 26/26 PASS
- Phase2 全量回归: 9/9 PASS

## 6. 关联文档

- `docs/state.md §5.1` 新增 ABANDON 字段语义表
- `docs/state.md §5.2` 新增 ABANDON 触发场景表
- `docs/state.md §5.3` 新增 `abandon()` API 约定
- `docs/known-issues.md §112` 新增详细说明
- `docs/BUGS.md` 新增 FIX-T111 条目
- `docs/AGENTS.md` §6 新增约束 #30
- `statics.json` fix_total 107→108, bdd_total 1188→1198

## 7. 设计决策

- **保留 finishTime=null**: ABANDON 不是正常完成,语义上不应有 finishTime
- **不写 updateUser=null**: 比例会签场景下,「谁触发的废弃」是有意义的审计信息;与 ONE_VOTE_VETO 行为一致
- **backward compat**: 默认参数 `abandoned_by=""` 保持原行为(仅 taskState+updateTime),不破坏现有调用
