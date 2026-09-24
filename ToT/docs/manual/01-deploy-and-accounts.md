# 第 1 章 · 部署细节与多账号测试

> **来源**：https://jeeflow-doc.mldong.com/manual/01-deploy-and-accounts
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**操作手册第 1 章**。本章上游内容几乎全部为部署与运维操作，与「环境已部署」前提**高度冲突**——本章归档后仅保留「§5 权限码」一节作为跨链引用。
>
> **本仓实测**：本章对应本仓 `vendor/jeeflow/` 之外的 12 套 mldong 框架集成镜像（`mldong-boot4-jeeflow` 等），本仓 `vendor/jeeflow/` 是**纯引擎**（Python），不含前端 / 部署 / 鉴权；详细部署 / 端口 / 环境变量 / docker 命令请参考：
>
> - 部署 SOP：`ToT/sop/engine-deploy.md`
> - 环境配置：`ToT/sop/env-config.md` / `ToT/sop/env-pipeline.md`
> - 客户数据 reset：`ToT/sop/customer-data-reset.md`
> - 部署架构文档：`docs/deployment.md`
>
> **裁剪记录**：§1 一键包（4 容器端口）+ §2 常用改法（换端口 / 用自己的 MySQL/Redis / 指定后端镜像版本）+ §3 数据日志重置（6 个 docker 命令）+ §4 一个人怎么测多角色审批（退出重登 / 两浏览器 / 无痕窗口）+ §6 卡住了（5 个排错）**整段裁剪**（部署 / 测试 / 运维职责）。§5 权限码保留并加本仓跨链注解（spec/06-facade.md 已详尽覆盖）。

---

## §5. 权限码（保留）

> **本节为上游原文保留**：权限码 `wf:{action}` 形式是引擎契约的关键概念，与 `spec/06-facade.md` §2.6 完全对应。

后台所有工作流接口都走 `wf:{action.replace('/', ':')}` 形式的权限码，例如：

- `wf:processDesign:deploy`
- `wf:processTask:execute`
- `wf:processInstance:startAndExecute`

**默认规则**（`spec/06-facade.md` §2.6 已详尽）：

- `superAdmin` 全部放行
- 普通账号提示「您没有资源wf:xxx访问权限」时，去 **系统设置 → 角色管理** 选中角色 → 授权菜单，把对应功能与按钮勾上
- 部分 action 为 OR 语义（任一持有即可）：`processDefine/detail` → `wf:processDefine:detail` 或 `wf:processDesign:listByType`；`processTask/candidatePage` → `wf:processTask:execute` 或 `wf:processTask:candidatePage`
- 无注解的只读 / 轻量 action **登录即可访问**（放行）：`processInstance/detail` / `highLight` / `approvalRecord` / `bizData` / `processTask/detail` / `addCandidate` / `latest` / `getAssigneeTextData` / **`stats/overview` / `stats/trend` / `stats/group`**

> **本仓实测**（`spec/06-facade.md` §2.6 + 集成示例）：本仓 Python 引擎**不感知鉴权**——`IActionPermissionProvider` 是 SPI，集成方负责注册与校验；本仓 `main_common.py` 仅做引擎装配，不含权限码默认映射（需集成方配）。前端菜单来自后端下发的菜单数据，改完权限要**重新登录**才生效。

---

## 设计者视角

> 本章 §1-§4 + §6 内容**对流程设计师不直接有用**——设计师关心的是「我的流程 JSON 在这套环境里能跑通」，而不是「如何部署环境」「如何切角色测」。

| 设计师关心 | 应看文档 |
|---|---|
| 权限码 `wf:{action}` 形式（设计器配置 action 权限用）| `../spec/06-facade.md` §2.6 |
| 哪些 action 需要权限码 / 哪些放行 | `../spec/06-facade.md` §2.6 |
| Facade 60+ action 完整清单 | `../spec/06-facade.md` §3 |
| 集成方权限码 SPI 实测 | `../spec/05-spi.md` §可选 SPI |

> **下一步**：若设计者关心「发起 → 审批 → 完成」端到端链路（账号切换 / 待办 / 流程图高亮 / 审批记录），应转 `manual/06-start-and-approve.md`（待起草）；若关心业务数据如何落到业务表，转 `manual/08-persist.md`（待起草）；若关心本仓流程设计者完整知识图谱，转 `../README.md` §2 文档覆盖。

---

## 跨文档交叉引用

- 引擎契约层（默认规则 / OR 语义 / 放行清单）：`../spec/06-facade.md` §2.6
- 集成方权限码 SPI（`IActionPermissionProvider` 默认映射）：`../spec/05-spi.md` §可选 SPI + `../spec/06-facade.md` §2.6
- Facade 60+ action 完整契约：`../spec/06-facade.md` §3 + §4
- 用户视角权限流程（发起页 / 我的待办 / 审批页）：`manual/06-start-and-approve.md`（待补）
- 设计者知识图谱：`../../README.md` §2 + §8.1