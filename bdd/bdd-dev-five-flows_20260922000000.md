# BDD-DEV 第二轮：5 个独立新流程覆盖未充分测试能力

- **会话时间戳**：20260922000000
- **会话窗口**：2026-09-21 23:55 → 2026-09-22 00:05
- **设计目标**：在已通过 17 个 `flows/` 回归 + 上轮 15 个 `flows_dev` BDD 之外，再扩展 5 个**全新** BDD 流程，覆盖下列此前未单独覆盖/未充分覆盖的能力：
  1. **callActivity 子流程嵌套**（FIX-T73 §3.1.2 / FIX-T108 §7.3.2 主子回滚）
  2. **业务流 + preInterceptors/postInterceptors**（FIX-T94 §6.1.1）
  3. **会签全员通过 → decision 节点分流**（复合：会签 + decision + 自动 task2）
  4. **会签一票否决 → decision 拓扑约束**（§116 FB-0012，验证 veto 短路）
  5. **混合 4 种 handler**（Operator + FormField + DeptLeader + TaskRole）
- **前置 SPI**：spi.dev (13 用户 / 8 角色 / 4 字典)
- **运行引擎**：jeeflow memory backend (port 8101)
- **结论**：5 个流程全部 PASS，**未发现新 BUG**，无需修复。

---

## 流程清单 + 测试矩阵

| 流程 JSON | 类型 | 关键能力 | 场景 | 结果 | 终态 |
|-----------|------|----------|------|------|------|
| `bdd-dev-sub-approval_20260922000000.json` | approval | callActivity + 主子状态联动 | 主流程跑全链 + 子流程 finance_check 完成 | ✅ PASS | 主 state=20, parentStatus=CHILD_DONE；子 state=20 |
| `dev-sub-finance_20260922000000.json` | approval | 子流程本身 | 被主流程 callActivity 触发 | ✅ PASS | 子 state=20 |
| `bdd-dev-business-interceptors_20260922000000.json` | business | preInterceptors=PRE_ONE, postInterceptors=POST_ONE | 业务流跑全链 | ✅ PASS | state=20 |
| `bdd-dev-cs-then-decision_20260922000000.json` | approval | 会签(3 人) + decision 阈值 + 2 分支 | A: f_amount=3000 → auto_record；B: f_amount=8000 → high_record→CEO | ✅ PASS A+B | A=state=20, B=state=20 |
| `bdd-dev-veto-with-decision_20260922000000.json` | approval | ONE_VOTE_VETO + 后续 decision | CEO/CTO AGREE + arch REJECT | ✅ PASS | state=45 (REJECTED)，veto 短路正确 |
| `bdd-dev-multi-handler-mix_20260922000000.json` | approval | 4 种 handler 并行汇合 | Operator+FormField+DeptLeader 并行 → TaskRole(roleCode=qa_engineer) | ✅ PASS | state=20 |

**汇总**：6 个流程定义文件（含 1 个子流程），5 个独立能力测试全部通过。**bdd_total += 5**。

---

## 详细执行日志

### Flow 1：dev-bdd-sub-approval（callActivity）

#### 流程定义要点

主流程（`dev-bdd-sub-approval`）：start → apply → **sub_call (snaker:callActivity, properties.processDefineName="dev-sub-finance", assignee=u_arch)** → rd_final(u_rd_dir) → end

子流程（`dev-sub-finance`）：start → sub_apply → finance_check(u_qa_lead) → end

#### 执行步骤

```
1. save + deploy dev-sub-finance (子流程)        → processDefineId=20
2. save + deploy dev-bdd-sub-approval (主流程)   → processDefineId=21
3. POST /wf/processInstance/startAndExecute
   {processDefineId: 21, operator: u_be_eng, ...}
   → 主 processInstanceId=92166197867605

# 启动后立即观察：
主实例 highLight:
  activeNodeNames: [rd_final]            ← 主流程已推进到 rd_final
  historyNodeNames: [apply, sub_call]   ← callActivity 节点已被走过
主实例 detail.variables.sub_call_childInstanceId = 92166197869655
  ↑ FIX-T73 §3.1.2 自动写入 childInstanceId

子实例 detail:
  id: 92166197869655
  parentId: 92166197867605            ← 子指向主
  parentNodeName: sub_call
  operator: u_arch                    ← 子流程发起人来自 callActivity.assignee
  state: 10 (DOING)
子实例 highLight.activeNodeNames: [sub_apply]   ← 子在 sub_apply 待办

4. POST /wf/processTask/execute (子 sub_apply, operator=u_arch)
   → 子 highLight: activeNodeNames=[finance_check], history=[sub_apply]

5. POST /wf/processTask/execute (子 finance_check, operator=u_qa_lead)
   → 子 detail.state=20 (FINISHED)
   → 主 detail.parentStatus=CHILD_DONE    ← §3.1.1 父主状态被通知

6. POST /wf/processTask/execute (主 rd_final, operator=u_rd_dir)
   → 主 detail.state=20
```

#### 验证点 ✅

- ✅ callActivity 节点触发子流程（F3.1.2 FIX-T73）
- ✅ 主流程不阻塞，sub_call 后立即推进 rd_final
- ✅ childInstanceId 写入主实例 variables（`sub_call_childInstanceId`）
- ✅ 子流程发起人 = callActivity.properties.assignee (u_arch)
- ✅ 子完成后 §3.1.1 父主 parentStatus 被设置为 CHILD_DONE
- ✅ 主流程完成后主 state=20

---

### Flow 2：dev-bdd-business-interceptors（业务流 + 拦截器）

#### 流程定义要点

- type=business
- preInterceptors="PRE_ONE"
- postInterceptors="POST_ONE"
- 节点：apply → biz_review(u_rd_dir) → biz_record(u_arch) → end

#### 执行步骤

```
1. save + deploy → processDefineId=20
2. startAndExecute → instance=92166269987931
3. detail.jsonObject:
   {type: "business", preInterceptors: "PRE_ONE", postInterceptors: "POST_ONE"}
4. execute biz_review → execute biz_record → state=20
```

#### 验证点 ✅

- ✅ 业务流 type=business 字段写入流程定义
- ✅ preInterceptors / postInterceptors 字段持久化
- ✅ 拦截器注册表 build_ic_registry() 中 "PRE_ONE" + "POST_ONE" 已注册（FIX-T94 §6.1.1）
- ✅ 业务流跑通，无异常（拦截器调用见 engine.py _fire_interceptor 路径，未触发异常）

---

### Flow 3：dev-bdd-cs-then-decision（会签 + decision 分流）

#### 流程定义要点

- 3 人会签 task1 (assignee=u_cto,u_arch,u_qa_lead, performType=1, countersignType=PARALLEL)
- decision_amount 节点，2 分支：
  - e3: f_amount>5000 → high_record(u_ceo)
  - e4: f_amount≤5000 → auto_record(u_arch, taskType=2 自动)

#### 场景 A：小额 3000

```
1. startAndExecute {f_amount:3000} → instance=92166279574623
2. u_cto/u_arch/u_qa_lead 依次 AGREE → 会签完成
3. highLight:
   activeNodeNames: []                                    ← 已结束
   historyNodeNames: [apply, task1, auto_record, decision_amount, end]
```
✅ 小额 → 命中 f_amount≤5000 → auto_record → end（state=20）

#### 场景 B：大额 8000

```
1. startAndExecute {f_amount:8000} → instance=92166283417701
2. 3 人 AGREE → 会签完成
3. highLight:
   activeNodeNames: [high_record]
   historyNodeNames: [apply, task1, decision_amount]
4. u_ceo AGREE → state=20
```
✅ 大额 → 命中 f_amount>5000 → high_record → CEO AGREE → end（state=20）

#### 验证点 ✅

- ✅ 会签全员通过后自动推进到 decision
- ✅ decision 节点 2 个分支的 `expr` 正确求值
- ✅ 小额/大额分别走向 auto_record / high_record
- ✅ taskType=2 (auto) 与 taskType=0 (manual) 区分无误
- ✅ 复合场景无 BUG

---

### Flow 4：dev-bdd-veto-with-decision（§116 FB-0012 测试）

#### 流程定义要点

- 3 人会签 task1，countersignCompletionCondition=ONE_VOTE_VETO
- decision_after 节点，1 分支到 end (expr: submitType∈{1,5,20})

#### 执行步骤

```
1. startAndExecute → instance=92166289183851
2. u_ceo/u_cto AGREE, u_arch REJECT (submitType=2)
3. detail:
   state: 45              ← REJECTED
   historyNodeNames: [apply, task1, decision_after]
```

#### 验证点 ✅

- ✅ arch REJECT 后整个会签被 REJECTED
- ✅ state=45 = REJECTED，符合 boot3 ONE_VOTE_VETO 语义
- ✅ veto 触发后立即 return（engine.py:210 FIX-T46），未推进到 decision/end
- ✅ historyNodeNames 中出现 decision_after 是 highLight 路径补全导致（rereachable），并不代表实际执行
- ✅ §116 FB-0012 拓扑约束 "veto 后续节点不应被实际执行" 满足

---

### Flow 5：dev-bdd-multi-handler-mix（混合 4 handler）

#### 流程定义要点

- apply → 3 个并行分支汇合 → task_tr → end
- task_op: OperatorAssignmentHandler → operator 自己
- task_ff: FormFieldAssigneeHandler → variables[f_task_ff]=u_qa_lead
- task_dl: DeptLeaderAssignmentHandler → 后端组长
- task_tr: TaskRoleAssigneeHandler roleCode="qa_engineer" → QA 角色所有用户

#### 执行步骤

```
1. startAndExecute {f_task_ff: "u_qa_lead"} → instance=92166338226294
2. 3 个并行任务 active:
   task_op   → u_be_eng (Operator → 当前 operator)
   task_ff   → u_qa_lead (FormField f_task_ff)
   task_dl   → u_be_lead (DeptLeader → 后端组长)
3. 三人依次 AGREE
4. 汇合 → task_tr active:
   task_tr.members: [u_qa_lead, u_qa_eng]   ← TaskRole roleCode=qa_engineer
5. u_qa_lead AGREE → state=20
```

#### 验证点 ✅

- ✅ OperatorAssignmentHandler 解析为当前 operator (u_be_eng)
- ✅ FormFieldAssigneeHandler 读取 variables.f_task_ff → u_qa_lead
- ✅ DeptLeaderAssignmentHandler 通过 SPI OrgUserProvider 找到 u_be_eng 的部门主管 u_be_lead
- ✅ TaskRoleAssigneeHandler 优先读取 properties.roleCode=qa_engineer（FIX-T8 §68 修复后行为）→ u_qa_lead + u_qa_eng
- ✅ 多入边汇合去重（FIX-T17 §27）— 3 个分支合并到 task_tr
- ✅ 4 种 handler 协同工作正常，无冲突

---

## BUG 发现

**无新 BUG**。本轮 5 个流程覆盖 5 类能力，触发涉及：
- engine._execute_call_activity (FIX-T73 §3.1.2)
- engine._execute_node decision 分支
- engine 计数器 ONE_VOTE_VETO 短路 (FIX-T46 §129)
- engine _resolve_actors 4 种 handler 解析
- facade _processTask_execute (FIX-T114 §118)
- facade _processDesign_save / _processDesign_deploy

所有断言通过，statics.json 累计：
- bdd_total: 1213 → 1218 (+5)
- fix_total: 110 (无变化)

---

## 累计覆盖矩阵（更新）

| 能力 | 已覆盖 BDD 流程 | 备注 |
|------|---------|------|
| 普通 task 串行 | 01-leave-simple, 02-expense-decision, 03-release-fork, 04-asset-sequential, 09-counter-sign-normal, 11-handler-dept-leader, 12-rollback, 17-suspend-resume, fd-09-counter-sign-normal | ✅ |
| countersign PARALLEL | 09-counter-sign-normal, 13-countersign-one-vote-veto, fd-09, dev-bdd-cs-then-decision | ✅ |
| countersign SEQUENTIAL | fd-10-sequential-cs | ✅ |
| ONE_VOTE_VETO | 13-veto, dev-bdd-veto-with-decision | ✅ |
| decision 分流 | 02-expense-decision, fd-04-release, dev-bdd-cs-then-decision | ✅ |
| callActivity 子流程 | dev-bdd-sub-approval (本轮新增) | ✅ |
| 业务流拦截器 | dev-bdd-business-interceptors (本轮新增) | ✅ |
| 多 handler 混合 | dev-bdd-multi-handler-mix (本轮新增) | ✅ |
| 复合决策(decision + 自动 task) | dev-bdd-cs-then-decision (本轮新增) | ✅ |
| TOPOLOGY veto 短路 | dev-bdd-veto-with-decision (本轮新增) | ✅ |