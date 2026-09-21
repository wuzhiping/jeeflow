# BDD-DEV-021/022 用户反馈 3 项修复 (20260922)

- **会话时间戳**：20260922000000（用户反馈修复阶段）
- **触发**：用户反馈 3 个错误 (FB-0014/0015/0016)
- **结论**：3 项中 2 项确认 + 1 项不成立。已修复 2 项 + 19 流程全量回归通过

---

## 用户反馈 vs 实测结论

| # | 用户反馈 | 实测结论 | 状态 |
|---|---------|---------|------|
| 1 | 07-countersign-ratio `field.countersignCompletionCondition` 字段位置错 | ✅ 部分确认：engine.py:148 只读顶层；当前数据在 field.，靠 RatioCapableEngine 包装器兜底 | 🔧 已修复 FIX-T116 |
| 2 | 11-assignment-handler SPI 缺 task1/task2/task3/task4 + role_code | ❌ 不成立：SPI dev 完整 (13 users / 8 roles / qa_engineer 都有) | 📝 仅 docs 说明 |
| 3 | assignees 字段静默无效，引擎用 properties.assignee literal | ✅ 完全确认：vendor/jeeflow/ 零处读取 assignees | 🔧 已修复 FIX-T115 |

---

## 修复 1：FIX-T115 assignees 字段死字段 (engine.py)

### 根因

`vendor/jeeflow/engine.py:_resolve_actors` 仅读 `properties.assignee` literal + 替换 `applicant` token + 查 `vars_[token]`，**零处读取 `vars_["assignees"]`**。

历史原因：mldong 体系下 `args.assignees` 是另一套 endpoint (`startProcessInstanceByName`) 的协议，本仓 facade 未实现该协议但仍透传 `assignees` 字段到 `vars_`，造成"调用方误以为生效"。

### 修复

`vendor/jeeflow/engine.py:867-880`:

```python
# FIX-T115 (2026-09-22 FB-0015)：assignees 字段死字段修复
assignees_map = vars_.get("assignees") if isinstance(vars_.get("assignees"), dict) else {}
a_val = assignees_map.get(node.id) or assignees_map.get(token)
if a_val is not None:
    if isinstance(a_val, (list, tuple)):
        actors.extend(str(x) for x in a_val)
    else:
        actors.append(str(a_val))
else:
    actors.append(token)
```

**优先级** (OR 累加语义):
1. `properties.assignee` literal + 特殊 token（`applicant` / `@role:xxx`）
2. `vars_[token]` 直接命中
3. `vars_["assignees"][node.id]` (FIX-T115 新增)
4. `vars_["assignees"][token]` token 名作为 assignees key 的回退 (FIX-T115)

### 复测

| 姿势 | properties.assignee | assignees | 期望 actor | 实测 actor | 结果 |
|---|---|---|---|---|---|
| 1 | "applicant" | {"apply": "u_qa_lead"} | u_qa_lead + u_be_eng | u_qa_lead + u_be_eng | ✅ |
| 2 | "applicant" | {} | u_be_eng | u_be_eng | ✅ (向后兼容) |
| 3 | "u_fe_eng" | {"apply": "u_qa_lead"} | u_fe_eng + u_qa_lead | u_fe_eng + u_qa_lead | ✅ |

```bash
# 复现姿势 1:
curl -X POST /wf/processInstance/startAndExecute -d '{
  "processDefineId": "20", "operator": "u_be_eng",
  "assignees": {"apply": "u_qa_lead"},
  "variables": {"submitType": 0, "u_userId": "u_be_eng"}
}'
# result:
# activeNodeNames[0]: apply → u_qa_lead + u_be_eng (done), task1 → u_fe_lead (active)
```

---

## 修复 2：FIX-T116 07 字段位置 (数据修正)

### 根因

`flows/07-countersign-ratio.json` 把 `countersignCompletionCondition` 放在 `properties.field`，但 `vendor/jeeflow/engine.py:148` 只读顶层。当前靠 `main.py:69` 的 `RatioCapableEngine` 包装器兜底（`main_common.py:225-228`）。

### 修复

**`flows/07-countersign-ratio.json`** (canonical spi.dev 适配版):
```json
"properties": {
  "assignee": "u_fe_eng,u_be_eng,u_qa_eng,u_fe_senior",
  "taskType": 0,
  "performType": 1,
  "countersignType": "PARALLEL",
  "countersignCompletionCondition": "#nrOfCompletedInstances==2",  ← 移至顶层
  "field": {
    "candidateUsers": "u_fe_eng,u_be_eng,u_qa_eng,u_fe_senior"   ← field 仅留权限字段
  }
}
```

**`flows_demo/07-countersign-ratio.json`** (Java 源副本镜像同步):
```json
"properties": {
  "assignee": "userA,userB,userC,userD",
  "taskType": 0,
  "performType": 1,
  "countersignType": "PARALLEL",
  "countersignCompletionCondition": "#nrOfCompletedInstances==2",  ← 移至顶层
  "field": {
    "candidateUsers": "userA,userB,userC,userD"
  }
}
```

### 复测

| 场景 | 期望 | 实测 | 结果 |
|---|---|---|---|
| 1/4 完成 | task1 仍 active (nrOfCompletedInstances=1 < 2) | activeNodeNames=[task1] | ✅ |
| 2/4 完成 | task1 done + 余者 ABANDON → state=20 | activeNodeNames=[] state=20 | ✅ |

修复后**去掉对 RatioCapableEngine 包装器兜底的依赖**，engine.py 单点真相。

---

## 不修复：11-assignment-handler SPI 数据（不成立）

### 实测结论

SPI dev 配置（`spi/dev/jsons/`）完整：
- 13 用户 (含 u_ceo/u_cto/u_rd_dir/u_arch/u_fe_lead/u_fe_senior/u_fe_eng/u_be_lead/u_be_senior1/u_be_senior2/u_be_eng/u_qa_lead/u_qa_eng)
- 8 角色 (ceo/cto/rd_director/tech_lead/architect/senior_engineer/engineer/qa_engineer)
- `qa_engineer` 角色 → [u_qa_lead, u_qa_eng]
- 4 个 handler FQCN 全部在 `vendor/jeeflow/builtin.py` 已注册

流程默认 deploy 报错**实际原因是 FormField handler 期望 `variables.f_task1`**，而非 SPI 缺数据。

### 复测

加 `f_task1="u_qa_lead"` 变量后跑全链：

```bash
curl -X POST /wf/processInstance/startAndExecute -d '{
  "processDefineId": "32", "operator": "u_be_eng",
  "variables": {"submitType": 0, "u_userId": "u_be_eng", "f_task1": "u_qa_lead"}
}'
```

| 节点 | handler | 解析路径 | 实测 actor | 结果 |
|---|---|---|---|---|
| task1 | FormFieldAssigneeHandler | variables.f_task1 | u_qa_lead + u_be_eng (applicant) | ✅ |
| task2 | OperatorAssignmentHandler | operator | u_be_eng | ✅ |
| task3 | DeptLeaderAssignmentHandler | SPI find_dept_leaders | u_be_lead | ✅ |
| task4 | TaskRoleAssigneeHandler | SPI find_by_role("qa_engineer") | [u_qa_lead, u_qa_eng] | ✅ |

state=20 ✅

### 文档同步

仅 docs/flow.md §5.4 补充 handler 配套变量约定，无代码改动。

---

## 全 19 流程回归

修复后全量回归 19 flows (01-simple + 02-multi-task + 03-decision-expr + 04-fork-join + 05-countersign-parallel + 06-countersign-sequential + 07-countersign-ratio + 08-countersign-sequential-approve + 08-custom-node + 09-with-reject + 10-mixed-mode + 11-assignee-vars + 11-assignment-handler + 12-candidate-page + 13-countersign-one-vote-veto + 14-decision-submitType + 15-decision-amount + 16-delegate-test + 17-suspend-resume-test)：

| 流程 | pdId | 终态 | 结果 |
|------|------|------|------|
| 01-simple | 20 | state=20 | ✅ |
| 02-multi-task | 21 | state=20 | ✅ |
| 03-decision-expr | 22 | state=20 | ✅ |
| 04-fork-join | 23 | state=20 | ✅ |
| 05-countersign-parallel | 24 | state=20 | ✅ |
| 06-countersign-sequential | 25 | state=20 | ✅ |
| 07-countersign-ratio | 26 | state=20 | ✅ (FIX-T116 验证) |
| 08-countersign-sequential-approve | 27 | state=20 | ✅ |
| 08-custom-node | 28 | state=20 | ✅ (自动) |
| 09-with-reject | 29 | state=20 | ✅ |
| 10-mixed-mode | 30 | state=20 | ✅ |
| 11-assignee-vars | 31 | state=20 | ✅ (FIX-T115 验证) |
| 11-assignment-handler | 32 | state=20 | ✅ (4 handler 链) |
| 12-candidate-page | 33 | state=20 | ✅ |
| 13-countersign-one-vote-veto | 34 | state=20 | ✅ |
| 14-decision-submitType | 35 | state=20 | ✅ |
| 15-decision-amount | 36 | state=20 | ✅ |
| 16-delegate-test | 37 | state=20 | ✅ |
| 17-suspend-resume-test | 38 | state=20 | ✅ |

**19/19 PASS, 零回归**。

---

## 统计更新

- bdd_total: 1218 → 1220 (+2)
- fix_total: 110 → 112 (+2: FIX-T115, FIX-T116)
- docs/known-issues.md: +3 章节 (§119 §120 §121)
- statics.json: last_bdd_session.bugs_fixed 更新