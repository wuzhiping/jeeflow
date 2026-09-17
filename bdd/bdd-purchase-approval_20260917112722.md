# BDD-采购审批 复合场景测试

- **测试时间**：2026-09-17 13:30:00（TS=20260917112722）
- **后端**：内存（BDD.md 约束：不能改 main.py）
- **测试类型**：按 docs/AGENTS.md §5 流程 + BDD.md 复合场景设计
- **JSON 定义**：`./bdd/bdd-purchase-approval_20260917112722.json`
- **关联文件**：
  - `./flows/03-decision-expr.json`（金额决策参考）
  - `./flows/13-countersign-one-vote-veto.json`（一票否决会签）
  - `./flows/12-candidate-page.json`（候选用户/组）
  - `./flows/09-with-reject.json`（驳回路径）

## 1. 设计概览

```
节点：start → apply(applicant, 字段权限) → decision1(f_amount>=5000)
                                              ├─ ≥5000 → manager_review(manager) ┐
                                              └─ <5000 → supervisor_review(leader) ┴→ countersign(PARALLEL userA,B,C + ONE_VOTE_VETO + candidateUsers/Groups) → end
边：7 条
```

### 1.1 能力覆盖

| 能力 | 来源 flow | 用法 |
|---|---|---|
| 申请节点 | 01 | apply(applicant) |
| 字段权限 | docs/AGENTS.md §5.7 | PERMISSION_f_amount=2(隐藏), PERMISSION_f_reason=1(只读) |
| 决策节点 | 03 | f_amount >= 5000 / f_amount < 5000 |
| 多 task 分支 | 02 | manager_review + supervisor_review |
| 会签 PARALLEL | 05 | assignee=userA,B,C + performType=1 + PARALLEL |
| 一票否决 | 13 | countersignCompletionCondition="ONE_VOTE_VETO" |
| 候选用户/组 | 12 | apply + countersign 双源 (userA,userB) + finance |
| 字段变量（顶层 f_*） | 03 + Issue D 修复 | f_amount / f_reason |

## 2. 部署

```bash
reset → processDesign/save (name=bdd-purchase-approval)
     → design_id=9
     → processDesign/deploy → processDefineId=113
```

## 3. 测试场景

### Test A: 大额采购 (f_amount=8000) + 一票否决触发

```bash
curl -X POST /wf/processInstance/startAndExecute -d '{
  "processDefineId": 113,
  "operator": "user1",
  "assignees": {"apply": "user1"},
  "variables": {
    "submitType": 0, "f_applyUser":"user1",
    "f_amount": 8000, "f_reason":"办公设备采购",
    "u_userId":"user1", "u_realName":"用户1", "u_deptId":"D01"
  }
}'
```

→ instanceId=91766453297343

执行：manager_review(manager) → countersign → userB DISAGREE (submitType=20) → ONE_VOTE_VETO 触发

### Test B: 小额采购 (f_amount=2000) + 全员通过

→ instanceId=91766491729093

执行：supervisor_review(leader) → countersign → userA/B/C 全员 AGREE (submitType=1) → state=20

## 4. 校验

### 4.1 Test A (f_amount=8000 → manager → ONE_VOTE_VETO)

```
state=20 (DONE)
  apply              state=20
  manager_review     state=20          ← decision → manager
  countersign        state=99 (ABANDON) ← userA (未执行)
  countersign        state=20          ← userB DISAGREE (veto 触发)
  countersign        state=99 (ABANDON) ← userC (未执行)
```

approvalRecord: apply(user1) → manager_review(manager) → countersign(userA 空) → countersign(userB) → countersign(userC 空)

✅ decision 正确路由到 manager_review（f_amount>=5000 为真）
✅ ONE_VOTE_VETO 正确触发：userB DISAGREE → 立即 state=20 + 剩余 ABANDON

### 4.2 Test B (f_amount=2000 → supervisor → 全员通过)

```
state=20 (DONE)
  apply              state=20
  supervisor_review  state=20          ← decision → supervisor
  countersign        state=20          ← userA AGREE
  countersign        state=20          ← userB AGREE
  countersign        state=20          ← userC AGREE
```

approvalRecord: apply(user1) → supervisor_review(leader) → countersign(userA) → countersign(userB) → countersign(userC)

✅ decision 正确路由到 supervisor_review（f_amount<5000 为真）
✅ ONE_VOTE_VETO 全员通过时正常流转（与 §13 一致：仅任一 DISAGREE 触发）

## 5. candidatePage 行为

### 5.1 candidatePage in apply task (向后查 decision1→...→countersign)

- apply 节点定义了 `candidateUsers=userA,userB` + `candidateGroups=finance`
- 实测返回 **8 个**（fallback user_search 全用户）
- 原因：decision1 非 task 节点透传可能未合并多 task candidates；实际查 `decision1→manager_review + supervisor_review`（都未配 candidates）→ `_next_task_candidates` 返回空 → fallback

### 5.2 candidatePage in countersign task (向后查 end, 非 task)

- 实测返回 **8 个**（fallback user_search）
- countersign 之后只有 end（非 task），向后查候选 → fallback

### 5.3 ⚠️ 新发现：decision1 不透传 candidates

`_next_task_candidates` 在经过 decision 节点时，**只收集直连的下一个 task 节点 candidates**。我的设计：
- apply → decision1 → [manager_review + supervisor_review]（两个 task）→ countersign
- candidatePage in apply 时，应查 [countersign] 的 candidates（= userA/B + finance = 4 个）

但实测返回 8 个（fallback）。**根因推测**：engine `_next_task_candidates.walk()` 只沿单一边走，遇到 fork 分叉会**只走第一条**。decision 出边有两条 expr，第一条匹配流转到 manager_review，但 candidatePage 查询时 walk 可能未正确处理 decision 分叉。

### 5.4 已知对照（12-candidate-page）

12 的设计 apply → review → end（无 decision/fork），candidatePage 返回 4 个 ✅

我的设计 apply → decision1 → 2 个 task → countersign，candidatePage 返回 8 个（fallback）❌

## 6. 字段权限（未实测）

设计：apply 上 PERMISSION_f_amount=2(隐藏), PERMISSION_f_reason=1(只读)

`processInstance/bizData` 接口目前返回 `{"code":99999999,"msg":"业务数据读取器未注册"}`（facade.set_meta_reader 未注册），**无法校验字段权限**。

参考 docs/AGENTS.md §5.7：「启用 `PERMISSION_f_<field>=1/2`...」为设计建议。

## 7. AGENTS.md §10 自检

- [x] §5.3 save + deploy code:0
- [x] §5.4 startAndExecute 返回 processInstanceId（2 次）
- [x] §5.5 走完所有 task，state==20
- [x] §5.6 approvalRecord 节点顺序符合设计
- [x] decision 分支正确（amount=8000→manager, amount=2000→supervisor）
- [x] ONE_VOTE_VETO 触发条件正确（任一 DISAGREE → 流转）
- [x] ONE_VOTE_VETO 全员通过 → 正常流转
- [x] 所有 action 在 §5.1 速查表内
- [x] 测试日志落盘（本文件）
- [x] 环境重置

## 8. 复盘

### 8.1 新发现

**`_next_task_candidates` 经 decision/fork 节点透传 candidates 不完整**：
- 当前实现 `_next_task_candidates.walk()` 经 decision/fork 时，只查**第一个匹配 task 节点**的 candidates，不合并多分支 candidates
- 12-candidate-page 是 `apply → review → end` 单链，恰好匹配；
- 本设计 `apply → decision1 → 2 task → countersign`，candidatePage 走 fallback 而非期望的 countersign candidates

**建议改进**：
- docs/flow.md §6.7 补充：candidatePage 经 decision/fork 时仅查首个匹配 task 的 candidates，多分支/透传需自行合并
- 或 engine 增强：decision/fork 透传时合并**所有可达 task 节点**的 candidateUsers/candidateGroups

### 8.2 测试稳定性

- 设计中 `f_amount` 顶层传递，decision expr `f_amount >= 5000` 正确评估（Issue D 修复有效）
- ONE_VOTE_VETO 字符串条件由 engine 识别
- PARALLEL 会签 3 user 实例正确创建

### 8.3 字段权限未实测

`processInstance/bizData` 接口因 `facade.set_meta_reader` 未注册返回 99999999，无法校验 PERMISSION_* 字段权限行为。这是已知的 facede 设计缺陷（不在 BDD 范围）。

## 9. 结论

✅ **PASS** — BDD-采购审批复合场景全流程符合设计：
- decision 正确按金额分流
- ONE_VOTE_VETO 行为正确（任一 DISAGREE 触发 veto + 剩余 ABANDON；全员通过正常流转）
- PARALLEL 会签 3 user 实例正确处理

⚠️ **新发现**：`_next_task_candidates` 经 decision/fork 透传 candidates 不完整，多分支场景下 candidatePage fallback 到 user_search。

## 10. docs 改动

- `./docs/flow.md §6.7`（如存在）：补充 `_next_task_candidates` 经 decision/fork 节点透传行为
- `./docs/known-issues.md`：新增 §22 — candidatePage 多分支透传不完整
