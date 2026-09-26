# 第 2 章 · 部门、用户与角色

> **来源**：https://jeeflow-doc.mldong.com/manual/02-dept-user-role
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**操作手册第 2 章**——本章是 `OrgUserProvider` SPI 数据前提 + `TaskRoleAssigneeHandler` roleCode 双轨制的**业务侧配置参考**。**流程配得没错却没人收到待办，九成是这里没配。**
>
> **本仓实测**：本仓 `vendor/jeeflow/spi.py:161 OrgUserProvider(ABC)` 3 方法（`find_dept_leaders` / `find_dept_main_leaders` / `find_by_role`）+ `vendor/jeeflow/builtin.py:170-183` 注册 12 个 key —— 数据由集成方通过本 SPI 注入，**引擎核心不感知**。
>
> **裁剪记录**：§1 部门（负责人与分管领导）+ §2 用户（所属部门与角色）+ §3 角色（普通 vs 工作流）+ §4 岗位 + §5 配完之后的影响范围**全部保留**（设计相关）+ §6 卡住了（6 排错）**保留并重写为本仓实测**。

---

## §1. 部门：负责人与分管领导

**系统设置 → 部门管理**。树形列表，工具栏有 新增 / 展开 / 自动调整排序，行操作有 详情 / 编辑 / 上移 / 下移 / 更多。

点某行的 **编辑**，两个字段直接决定"部门经理审批"这类节点派给谁：

| 字段 | 形态 | 引擎里对应 | 用在哪个参与人处理类 |
|---|---|---|---|
| **部门负责人** | 用户多选 | `OrgUserProvider.find_dept_leaders(dept_id)` | 发起人所属部门经理、当前用户所属部门经理 |
| **分管领导** | 用户单选 | `OrgUserProvider.find_dept_main_leaders(dept_id)` | 发起人所属部门分管领导、当前用户所属部门分管领导 |

多选负责人时，这几个人都会收到同一条待办，**任一人办理即通过**（普通参与，`performType=0`）。**没配负责人，用到部门经理处理类的节点就不会产生任务。**

> **本仓实测**（`vendor/jeeflow/builtin.py:111 DeptLeaderAssignmentHandler` + `:118 DeptMainLeaderAssignmentHandler`）：
>
> - `DeptLeaderAssignmentHandler.assign(node, inst, operator)` 调 `OrgUserProvider.find_dept_leaders(operator_dept_id)` → 返回 list[str]
> - `DeptMainLeaderAssignmentHandler.assign(...)` 调 `OrgUserProvider.find_dept_main_leaders(operator_dept_id)`
> - **空列表 = 该组织维度无匹配用户 → 任务不创建**（`extensions.py:68 IAssignmentHandler` 约定）
>
> 详见 `../spec/05-spi.md` §IOrgUserProvider + `../ToT/guides/07-assignment-handlers.md` §2。

**演示数据里的对应关系**（净装镜像）：

| 部门 | 部门负责人 | 分管领导 |
|---|---|---|
| 研发部 | 蒙立东、李娜 | 王强 |
| 财务部 | 见部门管理 | 见部门管理 |
| 总经理办 | 王强 | — |

---

## §2. 用户

**系统设置 → 用户管理**。与流程相关的是两项：

- **所属部门**：部门经理类处理类靠它找部门，没部门就取不到领导
- **角色**：候选用户组、按角色取人靠它

> **本仓实测**（`vendor/jeeflow/spi.py:157 UserProvider(ABC).get_user`）：用户信息注入流程变量 `u_userId` / `u_realName` / `u_deptId` / `u_deptName` / `u_postId` / `u_postName` 6 字段。集成方实现此 SPI 提供数据源（用户中心 / LDAP / 远程服务）。

新增用户后如果登录不上或看不到菜单，检查是否给了角色、角色是否授权了菜单。

---

## §3. 角色：普通角色与工作流角色

**系统设置 → 角色管理**。

演示数据里有 7 个角色，**类型不同**：

| 角色名称 | 角色编码 | 类型 | 用途 |
|---|---|---|---|
| 管理员 | `manage` | 系统角色 | 管后台菜单权限 |
| 工程师 | `engineer` | 工作流角色 | 流程里按角色取人 |
| 部门经理 | `manager` | 工作流角色 | 同上 |
| 会计 | `accountant` | 工作流角色 | 同上 |
| 财务复核 | `finance_reviewer` | 工作流角色 | 同上 |
| 人事专员 | `hr_specialist` | 工作流角色 | 同上 |
| 总经理 | `general_manager` | 工作流角色 | 同上 |

工作流角色**不参与后台菜单授权**，只被流程使用，出现在两个地方：

1. **节点属性 → 人员配置 → 候选用户组** 的下拉里（下拉只列工作流角色）
2. **`com.mldong.jeeflow.interceptor.impl.TaskRoleAssigneeHandler` 处理类**：**节点的唯一编码 = 角色编码**，该角色的成员就成为这个节点的参与人

> **本仓实测 roleCode 双轨制**（`vendor/jeeflow/builtin.py:143 TaskRoleAssigneeHandler`，FIX-T8 §68）：
>
> ```python
> class TaskRoleAssigneeHandler(IAssignmentHandler):
>     async def assign(self, node, inst, operator):
>         if node is None or self.org_prov is None:
>             return []
>         # FIX-T8：优先 properties.roleCode，回落 node.id
>         role_code = (node.properties or {}).get("roleCode") or node.id
>         return await self.org_prov.find_by_role(role_code) or []
> ```
>
> - **优先** `properties.roleCode`（Java 设计器规范字段）
> - **回落** `node.id`（向后兼容 §68 行为）
> - 节点 `id` / `roleCode` 必须等于 SPI `DEMO_ROLE_TO_USERS.json` 的 key
>
> 示例：节点编码写成 `manager` + 处理类选 `…TaskRoleAssigneeHandler` → `OrgUserProvider.find_by_role("manager")` 返回「部门经理」角色成员列表 → 该节点参与人 = 「部门经理」角色全部成员。
>
> 详见 `../ToT/guides/07-assignment-handlers.md` §3.7。

---

## §4. 岗位

**系统设置 → 岗位管理**。岗位用于用户归类，**内置参与人处理类不按岗位取人**；要按岗位审批，用固定参与人或自建处理类。

> **本仓实测**：本仓 `UserProvider.get_user` 返回 6 字段（含 `post_id` / `post_name`），但**引擎核心不基于岗位解析参与者**——岗位信息仅作 `u_postId` / `u_postName` 注入流程变量，不影响 handler 行为。

---

## §5. 配完之后

改部门、改用户、改角色**不影响已在途的实例**（任务创建时已经把参与人写进任务表了），只影响之后新产生的任务。改完想验证，重新发起一条。

> **本仓实测**：任务创建时 `task.actor_ids` 已落库（`wf_process_task_actor` 表），后续 `OrgUserProvider.find_*` 返回值变化不影响历史任务——但**新任务**走新解析。这是数据库事务一致性的副产品，符合 `spi.py:53 add_task_actor` 的**追加**语义（详见 `../spec/05-spi.md` §IProcessRepository）。

---

## §6. 卡住了看这里（重写为本仓实测）

| 现象 | 原因 | 处理 |
|---|---|---|
| 部门经理节点没有待办 | 该部门没配部门负责人 | 编辑部门 → 部门负责人，选上人 |
| 分管领导节点没有待办 | 只配了负责人没配分管领导 | 编辑部门 → 分管领导 |
| 按角色取人取不到 | 节点唯一编码与角色编码不一致（区分大小写），或角色下没有成员 | 对齐编码；到用户管理确认成员已挂该角色 |
| 候选用户组下拉是空的 | 没建工作流角色 | 角色管理里新增，类型选工作流角色 |
| 换了负责人但老单子还是原来的人 | 任务参与人在创建时已确定 | 属正常；需要改判就撤回重发或由当前办理人转交（`processTask/transfer`）|
| 引擎抛 `ValueError(handler 未注册: …OrgUserAssignmentHandlers$DeptLeaderAssignmentHandler)` | `OrgUserProvider` 未注入；或节点 properties 中 `assignmentHandler` 字段值是完整版 FQCN 但本仓 SPI 仅注册简化版主用 | 检查 `main_common.py:build_assignment_handlers` 是否调 `register_builtin_assignments(registry, user_prov, org_prov)`；可改用简化版 `…DeptLeaderAssignmentHandler`（无 `OrgUserAssignmentHandlers$` 嵌套前缀）|

> **本仓实测完整版 vs 简化版警示**（FIX-T67 §67）：本仓 `builtin.py:170-183` **同时**注册 12 个 key（7 简化版主用 + 5 完整版别名），历史 FQCN 仍能跑；但 `metadata.py:77 BUILTIN_ASSIGNMENT_METAS` 与运行时**部分不一致**（设计器字典源与引擎加载 key 不完全一致）。详见 `../spec/07-metadata.md` §SPI 实现清单 + `ToT/docs/README.md` §3-3。

---

## 跨文档交叉引用

- `OrgUserProvider` SPI 契约（3 方法）：`../spec/05-spi.md` §IOrgUserProvider
- 7 个内置 handler FQCN + 解析优先级：`../ToT/guides/07-assignment-handlers.md` §2 + §3
- `TaskRoleAssigneeHandler` roleCode 双轨制（FIX-T8 §68）：`../ToT/guides/07-assignment-handlers.md` §3.7
- 任务参与人追加语义（`add_task_actor` 不覆盖）：`../spec/05-spi.md` §IProcessRepository + `../docs/known-issues.md §67`
- 设计器字典源与运行时一致性警示：`ToT/docs/README.md` §3-3 + `../spec/07-metadata.md` §SPI 实现清单