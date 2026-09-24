# 附录 A · 页面与入口清单

> **来源**：https://jeeflow-doc.mldong.com/manual/appendix-a-pages
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**附录 A**——本附录面向**前端使用者**（菜单路径 / 路由清单），引擎契约相关仅 §4 系统设置（与工作流的关系）+ §5 权限码 7 动作。
>
> **本仓实测**：本仓 `vendor/jeeflow/` 是**纯引擎实现**——前端菜单 / 路由 / 页面布局由 `jeeflow-ui`（不在本仓范围）负责。
>
> **裁剪记录**：
> - **§1 工作流程（8 菜单 + 路由）+ §2 在线开发（3 菜单 + 路由）+ §4 业务档案（6 档案页 + 路由）三节路由清单整段裁剪**——本项目不输出 UI（PRD §3「不做什么」）；设计师若需 UI 路径请看 `jeeflow-ui` 仓库路由约定
> - **§3 系统设置（与工作流的关系）+ §5 权限码 7 动作原文保留**——含引擎契约相关权限码映射

---

## §3. 系统设置（参与人数据侧）

> **本节为系统设置菜单中与工作流参与人解析数据相关的子集**——7 菜单的路由为本仓范围外（前端 UI），仅保留「与工作流的关系」字段。

| 菜单 | 与工作流的关系 |
|---|---|
| 部门管理 | 部门负责人、分管领导：部门类处理类的取人来源 |
| 用户管理 | 用户的部门与角色：固定参与人、候选用户的来源 |
| 角色管理 | 工作流角色：候选用户组、按节点编码取人 |
| 岗位管理 | 内置处理类不按岗位取人 |
| 菜单管理 | 给角色授权工作流菜单与按钮 |
| 数据字典 | 表单里 `ApiDict` 组件用的字典项 |

> **本仓实测**（`vendor/jeeflow/builtin.py:111/118/125/134 DeptLeaderAssignmentHandler + DeptMainLeaderAssignmentHandler + ApplicantDeptLeaderAssignmentHandler + ApplicantDeptMainLeaderAssignmentHandler`）：所有 4 个部门维度 handler **依赖** `OrgUserProvider` SPI（`spi.py:161`）提供 3 方法数据：
>
> - `find_dept_leaders(dept_id)` → 部门经理
> - `find_dept_main_leaders(dept_id)` → 分管领导
> - `find_by_role(role_code)` → 工作流角色（用户管理 + 角色管理）
>
> 业务方实现此 SPI 后，**菜单管理 / 角色管理** 中授权的数据自动被引擎消费。详见 `manual/02-dept-user-role.md` + `../spec/05-spi.md` §IOrgUserProvider。

---

## §5. 权限码

> **本节为引擎契约关键参考**——工作流接口的权限码规律是 `wf:` + action 路径里的 `/` 换成 `:`：

| 动作 | 权限码 |
|---|---|
| 流程设计分页 | `wf:processDesign:page` |
| 保存画布 | `wf:processDesign:updateDefine` |
| 部署 | `wf:processDesign:deploy` |
| 重新部署 | `wf:processDesign:redeploy` |
| 定义分页 | `wf:processDefine:page` |
| 发起 | `wf:processInstance:startAndExecute` |
| 待办列表 | `wf:processTask:todoList` |
| 办理 | `wf:processTask:execute` |

> **本仓实测**（`spec/06-facade.md` §2.6 已完整覆盖）：
>
> - `superAdmin` 全部放行
> - 普通角色需在 **角色管理 → 授权菜单** 里勾上对应按钮
> - 改完重新登录生效
> - 完整 57 个 /wf/ 端点 权限码映射详见 `../spec/06-facade.md` §3
> - 默认规则 + OR 语义 + 放行清单详见 `../spec/06-facade.md` §2.6
> - 部分 action 为 OR 语义（如 `processDefine/detail` → `wf:processDefine:detail` 或 `wf:processDesign:listByType`）

---

## 设计者视角

> 本附录**对流程设计师不直接有用**——设计师关心的是引擎契约（哪些 action 可调用、参数 / 返回结构、权限码），不是前端 UI 路径。UI 路由相关请走 `jeeflow-ui` 仓库。

| 设计师关心 | 应看文档 |
|---|---|
| 哪些 action 可调用 | `../spec/06-facade.md` §3 清单（57 个 /wf/ 端点）|
| 权限码默认规则 + OR 语义 | `../spec/06-facade.md` §2.6 |
| 接口参数 + 返回结构 | `../spec/06-facade.md` §4 各 action 详解 |
| 失败 msg 跨栈字面量 | `../spec/06-facade.md`「失败 msg 跨栈统一文案」 |
| 参与人解析数据前提 | `manual/02-dept-user-role.md` |

---

## 跨文档交叉引用

- Facade 57 个 /wf/ 端点 完整契约 + 权限码默认规则 + 失败 msg 字面量：`../spec/06-facade.md`
- 7 个内置 assignmentHandler + 解析 4 优先级：`../ToT/guides/07-assignment-handlers.md`
- `OrgUserProvider` SPI 契约（3 方法）：`../spec/05-spi.md` §IOrgUserProvider
- 集成方权限码 SPI（`IActionPermissionProvider` 默认映射）：`../spec/06-facade.md` §2.6
- 设计者完整知识图谱：`../../README.md` §2 + §8.1