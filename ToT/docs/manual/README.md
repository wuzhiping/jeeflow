# 操作手册 · 总览与最短路径

> **来源**：https://jeeflow-doc.mldong.com/manual/
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**操作手册索引**——本目录归档上游 `/manual/` 8 章 + 2 附录，逐 link 起草中（详见 `ToT/docs/README.md` §2 + §8.1）。
>
> **本仓实测**：本目录对应上游 jeeflow-doc 站点的 `/manual/` 区段（部署后怎么用）。本仓 `vendor/jeeflow/` 是纯引擎实现（Python）；前端 `jeeflow-ui` + 12 套 mldong 框架集成镜像不在本仓范围。
>
> **裁剪记录**：§1 你会得到什么（4 容器）+ §2 部署（一条命令 + 13 语言栈端口）+ §3 净装演示数据（9 demo + 12 账号）三段**整段裁剪**（与「环境已部署」前提冲突；运维集成者参考 `ToT/sop/engine-deploy.md` / `env-config.md` / `env-pipeline.md`）。§4 30 分钟实操指南 + §5 7 个排错场景**整段裁剪**（运维 / 测试者职责）。§6 8 章 + 2 附录链接保留作为本目录归档指引。

---

## 本目录归档指引

`/manual/` 上游共 11 个子页面（含总览），本目录按以下结构归档：

| # | 文件 | 上游章节 | 起草状态 |
|---|---|---|---|
| 01 | `01-deploy-and-accounts.md` | 部署细节与多账号测试 | ✅ 已完成（58 行 / 仅保留 §5 权限码）|
| 02 | `02-dept-user-role.md` | 部门、用户与角色 | ✅ 已完成（135 行 / 含 OrgUserProvider SPI 实测）|
| 03 | `03-forms.md` | 表单 | ✅ 已完成（179 行 / 含字段权限 + f_ 前缀 + 任务表单绑定）|
| 04 | `04-design-and-publish.md` | 画流程与发布 | ✅ 已完成（216 行 / 流程设计 → 发布全流程）|
| 05 | `05-participants.md` | 参与人：任务派给谁 | ✅ 已完成（176 行 / 7 handler + 会签 4 模式 + 委托）|
| 06 | `06-start-and-approve.md` | 发起与办理 | ✅ 已完成（191 行 / 9 submitType 路由 + 退回/撤回）|
| 07 | `07-verify-and-troubleshoot.md` | 验证与排错 | ✅ 已完成（164 行 / 状态机 + 跨章排错）|
| 08 | `08-persist.md` | 让审批结果落到业务表 | ✅ 已完成（180 行 / 3 开关 + 8 排错）|
| A | `appendix-a-pages.md` | 页面与入口清单 | ✅ 已完成（82 行 / 系统设置 + 权限码）|
| B | `appendix-b-values.md` | 下拉与状态值对照 | ✅ 已完成（190 行 / 9 表对照 + 字典差异警示）|

> **11 篇全部完成**（2026-09-24）。下表参见 `../README.md §8.1` 同步列表。

---

## §6. 章节（原文保留）

**章节目的**：

| # | 章节 | 解决什么 |
|---|---|---|
| 01 | 部署细节与多账号测试 | 换端口、接自己的库、数据重置、一个人怎么切角色测 |
| 02 | 部门、用户与角色 | 参与人取人的数据前提：部门负责人、分管领导、工作流角色 |
| 03 | 表单 | 发起时填什么、审批时看什么、字段权限 |
| 04 | 画流程与发布 | 新建设计稿、节点属性、流程属性、保存与部署 |
| 05 | 参与人：任务派给谁 | 7 个内置处理类的用法、会签、候选、委托 |
| 06 | 发起与办理 | 发起页与办理弹窗每个开关、五种退回方式 |
| 07 | 验证一条流程跑对了没有 | 三处回看、状态码、接口自检、跨章排错总表 |
| 08 | 让审批结果落到业务表 | 后置拦截器、关联业务表、持久化模式 |
| A | 页面与入口清单 | 菜单、路由、权限码 |
| B | 下拉选项与状态值对照 | 界面中文选项 ↔ 引擎取值 |

再往下深入：属性语义查 [../spec/02-flow-definition.md](../spec/02-flow-definition.md)，接口契约查 [../spec/06-facade.md](../spec/06-facade.md)，把引擎接进自己的框架查 [../guides/10-mldong-integration.md](../guides/10-mldong-integration.md)。

---

## 设计者速查（待补文档期间）

> **本节为过渡期内容**：本目录 8 章 + 2 附录**未逐章归档前**，设计者可按以下路径获取所需信息：

| 设计者关心的问题 | 本仓已归档位置 |
|---|---|
| 流程定义 JSON 怎么写（节点 / properties / 边）| [../spec/02-flow-definition.md](../spec/02-flow-definition.md) + [../ToT/guides/02-flow-definition.md](../guides/02-flow-definition.md) |
| 7 个内置 assignmentHandler 用法 | [../ToT/guides/07-assignment-handlers.md](../guides/07-assignment-handlers.md) |
| 会签 / 一票否决 / 比例 / 拓扑约束 | [../ToT/guides/02-flow-definition.md](../guides/02-flow-definition.md) §2.5 + [../spec/06-facade.md](../spec/06-facade.md) §4.3 |
| 业务数据落库（ARCHIVE / SYNC + 字段权限双兼容）| [../ToT/guides/08-persist.md](../guides/08-persist.md) + [../ToT/guides/09-persist-meta.md](../guides/09-persist-meta.md) |
| submitType 9 枚举 + 退回/跳转/拒绝语义 | [../spec/04-engine-ops.md](../spec/04-engine-ops.md) + [../ToT/guides/05-scenarios.md](../guides/05-scenarios.md) |
| 流程详情回显（address 对象 / JSON / 子表）| [../ToT/guides/09-persist-meta.md](../guides/09-persist-meta.md) §6 |
| Facade 57 个 /wf/ 端点 完整契约 | [../spec/06-facade.md](../spec/06-facade.md) |
| 27 合规测试场景 | [../spec/08-compliance.md](../spec/08-compliance.md) |

> **设计者无需关心**：`/manual/` 中「部署细节」（01）/「演示账号」（03）/「30 分钟实操」（04）/「排错」（07）—— 这些是部署运维与最终用户上手内容，本仓定位的「流程设计师」不接触。

---

## 跨目录交叉引用

- 设计者完整知识图谱：`../../README.md` §2 文档覆盖
- guides/（用户视角操作手册）：`../guides/`
- spec/（规范契约）：`../spec/`
- concepts/（设计原理）：`../concepts/`
- 知识库工程流程（持续对齐代码与文档）：`../../README.md` §4
- 上游 manual/ 来源与子目录命名：`../../README.md` §8.1