# 第 5 章 · 参与人：任务派给谁

> **来源**：https://jeeflow-doc.mldong.com/manual/05-participants
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**操作手册第 5 章**——这是流程能不能跑通的分水岭。配错了不报错，只是**没人收到待办**。入口：设计器 → 点节点 → 常规配置 → 人员配置。
>
> **本仓实测**：基于 `vendor/jeeflow/engine.py:761 _resolve_actors` + `extensions.py:50 IAssignmentHandler` + `builtin.py:170-183` 注册 12 个 key（7 简化版主用 + 5 完整版别名）。
>
> **裁剪记录**：§1 解析顺序 + §2 固定参与人 + §3 7 个处理类 + §4 候选 + §5 会签 + §6 临时改道 + §7 卡住了 **全部保留并重写为本仓实测**。

---

## §1. 引擎按什么顺序找人

> **本仓实测**（`vendor/jeeflow/engine.py:761 _resolve_actors`）：

```
1. tf_nextNodeOperator 变量          → 动态指定下一节点处理人（最高优先）
2. assignee 非空                    → 固定参与者（含 "applicant" → 发起人）
3. assignmentHandler 注册名          → 内置或自定义处理器（推荐）
4. 都没有                          → 不创建任务（流程不中断，继续推进）
```

> **实测警示**：上游说"② 参与人 / 参与人处理类"——本仓实测 **tf_nextNodeOperator 优先级高于 assignee**（FIX-T17）。详见 `../spec/04-engine-ops.md` §退回上一步 + `../docs/known-issues.md`。

**不要同时填参与人和参与人处理类**——填了参与人那一栏，处理类就是摆设（assignee 静态优先于 assignmentHandler 动态）。

---

## §2. 参与人（固定）

多选用户，也可以直接写 `applicant` 表示发起人本人。演示数据里"发起申请"节点的参与人就是 `applicant`。

适合：审批人固定不变的小团队。**人一走就要改流程**，规模大了请改用处理类。

> **本仓实测**（`engine.py:_resolve_actors`）：`"applicant"` 命中 `inst.operator`（发起人 userId）字段解析；token 优先按 `inst.variables` 解析（list / tuple 展开）。

---

## §3. 参与人处理类（动态取人，7 个内置）

> **本仓实测**（`vendor/jeeflow/builtin.py:170-183 register_builtin_assignments`）：注册 **12 个 key** —— 7 个简化版主用 + 5 个完整版别名（兼容历史 FQCN）。

下拉里就这 7 项，按界面显示名对照：

| 界面显示名 | 取谁 | 依赖的数据 | 典型用法 |
|---|---|---|---|
| 流程发起人 | 发起人本人 | 无 | 提交后再确认一次、申请人签收 |
| 发起人所属部门经理 | **发起人**所在部门的部门负责人 | 部门的负责人 | 无论流程走到哪，都由发起人的经理审批 |
| 发起人所属部门分管领导 | 发起人所在部门的分管领导 | 部门的分管领导 | 超过权限额度时升级到分管领导 |
| 当前用户所属部门经理 | **上一个节点办理人**所在部门的部门负责人 | 部门的负责人 | 逐级上报：谁批的，就由谁的经理接着批 |
| 当前用户所属部门分管领导 | 上一个节点办理人所在部门的分管领导 | 部门的分管领导 | 同上，但要分管 |
| 根据表单字段值分配参与者 | 表单里某个字段填的人 | 表单有对应人员字段 | 申请人自己指定审批人、指定会签名单 |
| 根据任务节点唯一编码关联角色分配参与者 | **节点编码 = 角色编码** 的那个工作流角色的成员 | 工作流角色 + 成员 | 财务角色审、总经理角色审 |

> **本仓 FQCN**（`builtin.py:15-30` 完整版定义）：
>
> ```python
> HANDLER_OPERATOR_ASSIGNMENT = "com.mldong.jeeflow.interceptor.impl.OperatorAssignmentHandler"
> HANDLER_FORM_FIELD_ASSIGNEE = "com.mldong.jeeflow.interceptor.impl.FormFieldAssigneeHandler"
> HANDLER_DEPT_LEADER = "com.mldong.jeeflow.interceptor.impl.DeptLeaderAssignmentHandler"
> HANDLER_DEPT_MAIN_LEADER = "com.mldong.jeeflow.interceptor.impl.DeptMainLeaderAssignmentHandler"
> HANDLER_APPLICANT_DEPT_LEADER = "com.mldong.jeeflow.interceptor.impl.ApplicantDeptLeaderAssignmentHandler"
> HANDLER_APPLICANT_DEPT_MAIN_LEADER = "com.mldong.jeeflow.interceptor.impl.ApplicantDeptMainLeaderAssignmentHandler"
> HANDLER_TASK_ROLE_ASSIGNEE = "com.mldong.jeeflow.interceptor.impl.TaskRoleAssigneeHandler"
> ```

**三条最容易混的**：

1. **"发起人"和"当前用户"不是一回事**——转交、代理、跨部门会签之后，办理人可能已经不是发起人，这时"当前用户所属部门经理"取的是新办理人的经理。要始终跟着发起人走，就选带"发起人"字样的那两项。

2. **按角色取人靠节点编码**——节点唯一编码写成 `manager`，处理类选"根据任务节点唯一编码关联角色分配参与者"，则角色编码为 `manager` 的成员收到待办。**改节点编码等于换角色**。

3. **表单字段取人要求字段名精确匹配**——字段值支持逗号分隔字符串或数组；节点编码以 `_数字` 结尾时会去掉后缀再匹配（`task_01` 找 `task`）。

> **本仓实测警示**（`vendor/jeeflow/engine.py:_resolve_actors`）：
>
> - 7 个 handler **依赖 `OrgUserProvider` SPI 提供部门领导 / 分管领导 / 角色数据**——不实现本 SPI 时，组织维度 handler 返回空，任务不创建
> - 业务方实现 `spi.py:161 OrgUserProvider`（3 方法：`find_dept_leaders` / `find_dept_main_leaders` / `find_by_role`）
> - 集成示例：`main_common.py:build_assignment_handlers(user_prov, org_prov)`
>
> 详见 `../spec/05-spi.md` §IOrgUserProvider + `../ToT/guides/07-assignment-handlers.md` §2 + `manual/02-dept-user-role.md`。

---

## §4. 候选用户 / 候选用户组 / 候选用户处理类

这三项**不决定任务派给谁**，只决定办理时"指定下一节点处理人"下拉里能选谁。

| 字段 | 内容 |
|---|---|
| 候选用户 | 手选若干用户 |
| 候选用户组 | 选工作流角色，取该角色成员 |
| 候选用户处理类 | 净装镜像里没有注册项，下拉为空属正常；需要自定义候选逻辑见 `../ToT/guides/04-extensions.md` |

> **本仓实测**（`docs/flow.md §3.3` + `engine.py:_next_task_candidates:1569`）：候选用户属性放 `node.properties.candidate_users` / `candidate_groups`，可放根或 `properties.field` 内（FIX-T113 双位置语义）。**`processTask/candidatePage` 端点**返回候选分页，集成方需实现 `IUserSearchProvider` 提供用户搜索 fallback。详见 `../spec/06-facade.md` §4.3。

三项都不填时，"指定下一节点处理人"会开放全部用户供搜索。

---

## §5. 会签：一个节点多个人

在 **常规配置 → 基础信息** 里把参与类型改成 **会签参与**，会出现会签类型与完成条件：

| 配置 | 取值 | 效果 |
|---|---|---|
| 参与类型 | 普通参与 / 会签参与 | 普通参与时任一人办理即通过；会签要求多人 |
| 会签类型 | 并行会签 / 顺序会签 | 并行=同时给所有人建任务；顺序=一个一个来 |
| 会签完成条件 | 表达式，如 `#nrOfCompletedInstances >= 3` | 达到条件才往下走；**留空即全部完成** |

会签节点的办理按钮与普通节点不同：只有 **同意**、**不同意**、**加签**，没有退回上一步和跳转。

> **本仓实测 4 模式**（`docs/flow.md §3.3` + `engine.py:394 _create_task_with_actors` 会签任务创建；详见 `ToT/docs/diffs.md` §3-2）：
>
> | 模式 | 配置 | 完成条件 |
> |---|---|---|
> | **PARALLEL**（全员通过）| `performType=1 + countersignType=PARALLEL` | 全部 `submitType=0` 通过才流转 |
> | **SEQUENTIAL**（按顺序审）| `performType=1 + countersignType=SEQUENTIAL` | 仅最后一个通过即流转 |
> | **RATIO**（比例完成）| `performType=1 + countersignType=PARALLEL + countersignCompletionCondition=<OGNL>` | 表达式命中即流转，余者 ABANDON |
> | **一票否决** | `performType=1 + countersignType=PARALLEL + countersignCompletionCondition="ONE_VOTE_VETO"` | 任一 reject 立即流转 + 余者 ABANDON |
>
> ⚠️ **RATIO 与 ONE_VOTE_VETO 互斥**（FB-0008 §113）：字段值 = 表达式 → 比例模式；字段值 = 字符串 `"ONE_VOTE_VETO"` → 一票否决模式。两种语义不可复合。
>
> ⚠️ **submitType=20 拓扑约束**（FB-0012 §116）：会签 task → end **直连**时 submitType=20 才生效；后接 decision 节点会截断 cs_veto 路径，一票否决失效。
>
> 详见 `../ToT/guides/02-flow-definition.md` §2.5 + `../docs/known-issues.md §113/§116`。

---

## §6. 临时改道：三种方式

| 场景 | 怎么做 | 位置 |
|---|---|---|
| 发起时就指定第一个审批人 | 流程属性里 **是否发起时选人** 打开，发起抽屉里选人 | 发起页 |
| 办理时指定下一步由谁办 | 办理弹窗勾 **指定下一节点处理人** 再选人 | 我的待办 → 办理 |
| 我要休假，单子交给别人 | **我的委托** 建一条委托代理 | 工作流程 → 我的委托 |

> **本仓实测**（`facade.py:1114 processSurrogate_page` + `:1125 processSurrogate_save` + `engine.py` 内置 `SurrogateInterceptor`，v1.9.0+ 默认开启 issues/116）：
>
> - 委托配置 = `wf_process_surrogate` 表（`processName` / `operator` / `surrogate` / `startTime` / `endTime` / `enabled`）
> - **运行期生效**：`SurrogateInterceptor` 在任务创建后对每个 actor 调 `get_surrogate(actor, process_name, now)`
> - 命中 → 把 `surrogate` **追加**为该任务参与人（原授权人保留，任一可办）
> - **跨栈 4 条件一致**：空 processName 兜底 / 时间窗 / `surrogate <> operator` / `enabled == 1`（读侧白名单）
> - **未配置 `IProcessExtRepository` 时静默跳过**——不打断建单流程
>
> 详见 `../spec/06-facade.md` §4.5 + `../concepts/07-admin-and-facade.md` §2 + `../ToT/guides/04-extensions.md` §3。

委托代理按流程授权，有生效时间段：

- 授权时间段内，该流程落到你名下的任务会转给代理人
- 关掉 **是否启用** 立刻停止委托

---

## §7. 卡住了看这里（重写为本仓实测）

| 现象 | 原因 | 处理 |
|---|---|---|
| 提交后没有任何待办 | 参与人为空，或处理类取不到人 | 先看 `manual/02-dept-user-role.md` 部门/角色数据，再看参与人是否填了个不存在的用户名 |
| 配了处理类没生效 | 同时填了参与人 | 清空参与人（assignee 静态优先于 assignmentHandler）|
| 部门经理节点派给了别的部门的人 | 选成了"当前用户所属部门经理" | 要跟发起人走就换"发起人所属部门经理" |
| 按角色取人取不到 | 节点编码与角色编码不一致（区分大小写），或角色无成员 | 对齐编码；确认是工作流角色（不是系统角色）|
| 会签只来了一个人 | 参与类型还是普通参与 | 改成会签参与并重新部署 |
| 指定下一节点处理人时可选名单为空 | 候选用户/候选用户组没配，且用户搜索未开放 | 配候选，或不勾选该项用默认处理人 |
| **本仓实测补充**：deploy 失败提示 `handler 未注册: ...OrgUserAssignmentHandlers$XXX` | 节点 properties 中 `assignmentHandler` 是完整版 FQCN 但本仓 SPI 仅注册简化版主用（`metadata.py:77 BUILTIN_ASSIGNMENT_METAS` 与运行时**部分不一致**）| 改用简化版主用 `…XXX`（无 `OrgUserAssignmentHandlers$` 嵌套前缀），或确保 `main_common.py:register_builtin_assignments` 12 个 key 全部注册 |

---

## 跨文档交叉引用

- 解析优先级 4 步 + tf_nextNodeOperator 最高优先（FIX-T17）：`../spec/04-engine-ops.md` §退回上一步
- 7 个内置 handler FQCN + 解析 4 优先级：`../ToT/guides/07-assignment-handlers.md` §2 + §3
- `OrgUserProvider` SPI 契约（3 方法）：`../spec/05-spi.md` §IOrgUserProvider
- 会签 4 模式 + 互斥铁律（FB-0008 §113）+ 拓扑约束（FB-0012 §116）：`../ToT/guides/02-flow-definition.md` §2.5 + `../docs/known-issues.md §113/§116`
- `SurrogateInterceptor` 运行期 6 条件：`../spec/06-facade.md` §4.5 + `../concepts/07-admin-and-facade.md` §2
- candidatePage 6 字段候选返回 + 用户搜索 fallback：`../spec/06-facade.md` §4.3
- 部门 / 角色数据前提：`manual/02-dept-user-role.md`