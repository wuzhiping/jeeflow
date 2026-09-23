# BDD-DEV flows_dev 完整测试 (20260921233000)

## 概述

逐一测试 `flows_dev/*.json` (17 个流程)，验证 spi.dev 用户/角色适配 + 引擎功能完整。

## 测试结果

| # | 流程 | 验证场景 | 结果 |
|---|------|---------|------|
| 1 | 01-simple | 线性审批 + PERMISSION 字段权限 | ✅ |
| 2 | 02-multi-task | 4 级串行审批链 | ✅ |
| 3 | 03-decision-expr | decision 分流（金额阈值） | ✅ |
| 4 | 04-fork-join | 并行汇合 | ✅ |
| 5 | 05-countersign-parallel | 3 人并行会签全员通过 | ✅ |
| 6 | 06-countersign-sequential | 2 人顺序会签 | ✅ |
| 7 | 07-countersign-ratio | 2/4 比例会签 + ABANDON | ✅ |
| 8 | 08-countersign-sequential-approve | 串行会签 + 后续审批 | ✅ |
| 9 | 08-custom-node | TestCustomHandler | ✅ |
| 10 | 09-with-reject | submitType=2 REJECT (state=45) | ✅ |
| 11 | 10-mixed-mode | fork/join + decision 三路汇合 | ✅ |
| 12 | 11-assignee-vars | vars.deptLeader 变量 token 注入 | ✅ |
| 13 | 11-assignment-handler | 4 handler 链 (含 roleCode=qa_engineer) | ✅ |
| 14 | 12-candidate-page | candidatePage API (角色展开) | ✅ |
| 15 | 13-countersign-one-vote-veto | u_ceo 一票否决 (state=45) | ✅ (FIX-T115) |
| 16 | 14-decision-submitType | submitType 决策路由 | ✅ |
| 17 | 15-decision-amount | amount=8000 → task1=u_be_lead | ✅ |
| 18 | 16-delegate-test | u_fe_lead 委派 u_qa_lead | ✅ |
| 19 | 17-suspend-resume-test | suspend→50, resume→10, 完成→20 | ✅ |

**17/17 PASS**

## 修复的 Bug

### FIX-T115 (FIX-3) · 13-countersign-one-vote-veto 会签人映射

**根因**: userA,userB,userC 机械映射为 u_fe_eng,u_be_eng,u_qa_eng（3 个工程师），但 ONE_VOTE_VETO 需要有 veto 权限的 senior 角色。

**修复**: 改映射为 `u_ceo,u_cto,u_arch`（3 位决策层），与"任一 reject 立即驳回"语义匹配。

**验证**: u_ceo submitType=20 → instance.state=45 + 其他 2 个 task ABANDON=99 ✅

## 设计验证（无需修改）

- `flows_dev/11-assignment-handler.json` 沿用原 `flows/11-assignment-handler.json` 的无 apply 节点设计（start→task1 直连）。原 demo 流程就用此结构（test_11-assignment-handler_20260917105500 标注 PARTIAL）。
- 4 个 handler 链全部正常：`FormField`/`Operator`/`DeptLeader`/`TaskRole(roleCode=qa_engineer)`。

## 排查过程（FIX-T115 debug）

调试临时加 print 到 `_execute_node` / `_create_task` / `_follow_edges` / `save_task` / `page_todo_tasks`，确认：

1. `_follow_edges("start")` 返回 `[task1]`（不是 `[apply]`）→ 原 flow 无 apply 节点
2. `startAndExecute` 的 `doing` loop 对所有 DOING task 注入 operator → 注入 task1
3. `_create_task(task1)` → FormField handler 返回 `['u_qa_lead']` → actorIds=['u_qa_lead']
4. `add_task_actor(task1, [operator])` → actorIds 追加 `['u_qa_eng']`
5. `execute_process_task(task1, u_qa_eng)` → u_qa_eng 完成 task1
6. task2/3/4 由后续 handler 链路正确生成

引擎行为符合预期，无需修改。

## 文档同步

- `docs/flow.md` 中关于 FormField / TaskRole handler 的描述保持不变（沿用原流程行为）
- `flows_dev/11-assignment-handler.json` 的无 apply 节点特征已记录到测试报告 `bdd-dev-fd-11-handler_20260921231500.md`

## 结果

- memory (8101): ✅ **17/17 PASS**
- pg (8102): skipped
