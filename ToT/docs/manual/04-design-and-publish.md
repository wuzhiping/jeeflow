# 第 4 章 · 画流程与发布

> **来源**：https://jeeflow-doc.mldong.com/manual/04-design-and-publish
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**操作手册第 4 章**——从零画一条审批流到发布上线的**完整操作流程**。本章讲"在哪里点、填了会怎样"；属性字段的引擎语义查[规范 02 · 配置项完整参考](../spec/02-flow-definition.md)。
>
> **本仓实测**：基于 `vendor/jeeflow/facade.py` 57 个 /wf/ 端点 中的 `processDesign/*`（10 个）+ `processDefine/*`（9 个）+ 节点 properties 21 字段（spec/02）。
>
> **裁剪记录**：§1 设计稿 vs 流程定义 + §2 新建设计稿 + §3 设计器 + §4 节点属性（4 页签）+ §5 流程属性 + §6 保存与发布 2 步 + §7 怎么算成功 + §8 卡住了（7 排错）**全部保留并重写为本仓实测**；§9 下一步仅保留跨链引用（11/12 设计器二开与本项目不输出 UI 无关）。

---

## §1. 设计稿与流程定义是两个东西

| 设计稿 | 流程定义 |
|---|---|
| **在哪看**：工作流程 → 流程设计 | **在哪看**：工作流程 → 流程定义 |
| **是什么**：画布草稿 + 历史快照 | **是什么**：可执行的版本化模型 |
| **怎么产生**：新增 + 设计器保存 | **怎么产生**：部署 |
| **关键字段**：是否部署 | **关键字段**：状态（启用/禁用）、版本号 |

> **本仓实测**（`facade.py:773 processDesign_page` + `:865 processDesign_save` + `:347 processDefine_deploy`）：
>
> - **设计稿** = `wf_process_design` 表（content JSON 存画布快照）
> - **流程定义** = `wf_process_define` 表（content JSON 存可执行模型）
> - **部署**动作 = `processDesign/deploy` → 引擎按 `name` 自动 `version+1` 生成新定义记录
>
> **改了画布但没部署，发起时用的还是旧定义**——这是新手最常踩的一条。详见 `../spec/06-facade.md` §4.1 / §4.4。

---

## §2. 新建设计稿

**工作流程 → 流程设计 → 新增**。

7 字段：

| 字段 | 必填 | 说明 |
|---|---|---|
| 显示名称 | ✅ | 发起页卡片上显示的名字，也用于待办列表定位 |
| 唯一编码 | ✅ | 流程 `name`，建议用 `biz_xxx` 风格；部署后按它做版本归并 |
| 流程分类 | ✅ | 决定发起页的分组标题（假勤管理 / 人事管理 / 智能财务 / 法务管理 / 行政管理 / 业务管理 / 其他）|
| 图标 | ✅ | 发起页卡片图标，支持 ant-design 与 svg 两组 |
| 是否部署 | ❌ | 默认"否"。新建时不用管，部署后自动变"是" |
| 备注 | ❌ | 自己看的 |

> **本仓实测**（`facade.py:865 processDesign_save`）：
>
> - **UPSERT**（实测警告）：以 `name` 为唯一键，**复用现有行 id**。`/api/reset` 后 design 表仅 1 行；多次 save 不同 `name` 全部返回同一 id（**name 字段被覆盖**）
> - 设计师**禁止硬编码 `design_id`**，必须从响应实时取
> - 详见 `docs/AGENTS.md §7.2.5` + `ToT/docs/README.md §3-7`

---

## §3. 设计器

在该行点 **设计**，全屏打开设计器。新流程默认只有一条最简链：开始 → 发起申请（申请人）→ 结束。

> **本仓实测**：本仓 `vendor/jeeflow/` 是**纯引擎实现**——设计器渲染由前端 `jeeflow-ui` / `mldong-flow-designer-plus` 负责（不在本仓范围）。设计师只需关注产出 JSON 契约——详见 `../spec/02-flow-definition.md`。

---

## §4. 节点属性

点任意节点，右侧滑出「设置【节点名】节点属性」抽屉，四个页签。

### 4.1 常规配置

**基础信息**：

| 字段 | 可选值 | 说明 |
|---|---|---|
| 唯一编码 | 文本 | 节点编码，同时是任务名来源；改它会影响"按节点编码关联角色"这类取人规则。**严格** `^[A-Za-z0-9_]+$`（FIX-T34 §93）|
| 显示名称 | 文本 | 节点在流程图和待办里显示的名字 |
| 任务类型 | 主办 / 协办 | 主办=常规审批节点；协办=协助办理 |
| 参与类型 | 普通参与 / 会签参与 | 选会签后才会出现会签类型与加签按钮 |

**人员配置**（决定"谁收到待办"）：

| 字段 | 形态 | 说明 |
|---|---|---|
| 参与人 | 用户多选 | 固定参与人，可多选；填 `applicant` 表示发起人本人 |
| 参与人处理类 | 下拉（7 项）| 动态取人，按部门/角色/表单字段算出处理人 |
| 候选用户 | 用户多选 | 办理时"指定下一节点处理人"的可选名单 |
| 候选用户组 | 角色多选 | 同上，按工作流角色给候选人 |
| 候选用户处理类 | 下拉 | 净装镜像里没有注册项，下拉为空属正常 |

> **本仓实测**（`docs/flow.md §3.3` 任务节点 properties 21 字段）：
>
> - **参与人和参与人处理类不要同时填**：填了参与人就按参与人走，处理类不生效
> - 7 个内置处理类实测位置：`vendor/jeeflow/builtin.py:170-183` 注册 12 个 key（7 简化版主用 + 5 完整版别名）
> - **5 个未实现字段**（实测缺失）：`candidateHandler` / `reminderTime` / `reminderRepeat` / `autoExecute` / `callback` —— 写了不生效，需走 `EngineExtensions.event_listener` 自定义扩展
> - 详见 `../ToT/guides/02-flow-definition.md` §4 + `../ToT/guides/07-assignment-handlers.md` §2

### 4.2 表单配置

| 字段 | 说明 |
|---|---|
| **任务表单** | 处理人打开这条待办时看到的业务表单，从已注册表单里选。不选则审批页只显示审批意见区 |
| **操作按钮** | 这个节点上允许出现哪些审批动作。默认全选：同意 / 拒绝 / 退回上一步 / 退回发起人 / 跳转；会签节点另有会签不同意与加签。只留"同意"就能做出"只能往下走、不能驳回"的节点 |

> **本仓实测**：任务表单绑定通过 `node.properties.form` 字段。详见 `../spec/02-flow-definition.md` §4 + `manual/03-forms.md` §3.2。

### 4.3 高级配置

| 字段 | 说明 |
|---|---|
| **时限控制** | 提醒时间、重复提醒间隔、期待完成时间、是否自动完成、回调处理 |
| **拦截器** | 前置拦截器、后置拦截器。节点级这里是**填类全限定名**的文本框，不是下拉；下拉版在流程属性里（§5）|

> **本仓实测未实现**：`reminderTime` / `reminderRepeat` / `autoExecute` / `callback` 4 字段写了不生效；拦截器注册方式见 `../ToT/guides/04-extensions.md` §3。详见 `../ToT/guides/02-flow-definition.md` §4「本仓实现性差异」表。

### 4.4 扩展配置

当前是占位页，显示"待开发"，无需配置。

---

## §5. 流程属性

在画布空白处**点右键**打开，配置整条流程。

11 字段：

| 字段 | 说明 |
|---|---|
| 流程定义唯一编码 / 显示名称 | 与设计稿的 `name` / `displayName` 对应 |
| 期望完成时间 | 整条流程的时限 |
| **实例启动表单** | 发起人填的那张表。选**元数据表单**后可直接在设计器里编辑内嵌表单；没选会提示"未选择表单" |
| 启用字段权限 | 打开后每个节点可按字段设只读 / 可编辑 / 不可见 |
| 实例编号生成类 | 实例流水号生成规则，留空用默认 |
| 前置 / 后置拦截器 | 流程级拦截器，下拉选择，作用于所有节点 |
| **关联业务表** | 业务数据落库的目标表，如 `biz_leave` |
| **持久化模式** | `ARCHIVE`（缺省，结束归档）/ `SYNC`（发起 INSERT → 节点 UPDATE → 定稿）|
| 是否发起时选人 | 打开后发起时可指定下一步处理人 |
| 启用抄送人 / 启用申请理由 / 启用附件 | 控制发起与审批页上这几个输入项是否出现 |

> **本仓实测**（`vendor/jeeflow/persist.py:404 _resolve_define`）：
>
> - `关联业务表` = `relTableName`（缺省回落流程 `name`）
> - `持久化模式` = `persistMode`（缺省 `ARCHIVE`，非 `SYNC` 值一律回落 `ARCHIVE`）
> - 拦截器注册：流程顶层 `postInterceptors` 声明名字，引擎按名从注册表解析
> - 详见 `../spec/02-flow-definition.md` §2 + `../spec/09-persist.md` §4.0

---

## §6. 保存与发布是两步

1. 设计器里点 **保存** → 提示"保存成功"，画布内容存成设计稿快照，列表的**是否部署**变成"否"
2. 关闭设计器回到列表，该行 **更多 → 部署** → 弹提示"部署会生成新的流程定义版本，确定部署吗？" → **确认**

4 动作：

| 动作 | 什么时候可点 | 效果 |
|---|---|---|
| **部署** | 设计稿处于"未部署"状态 | 取最新快照生成新版本（版本号 +1），已发起的实例仍走旧版本 |
| **重新部署** | 同上 | 按唯一编码原地替换最新版内容，版本号不变，**在途实例会受影响** |
| **停用 / 启用** | 流程定义列表 | 停用后发起页选不到它，在途实例不受影响 |

> **本仓实测**（`facade.py:347 processDefine_deploy` + `:432 processDefine_redeploy` + `:452 processDefine_upAndDown`）：
>
> - `deploy` 按 `name` 自动 `version+1` 插新记录
> - `redeploy` 按 `name` 找最新定义：有则原地替换（version 不变），无则新建
> - `upAndDown` 切换 state（1 启用 / 0 停用）
>
> 已经部署过、又没再改动的稿子，**deploy / redeploy 按钮都是灰的**——先改画布并保存，它们才会亮。

---

## §7. 怎么算成功

- **流程定义** 列表出现你的流程，版本号从 1 开始，状态"启用"
- **发起申请** 页按你选的分类出现对应卡片，点开能看到 §5 里选的实例启动表单
- 发起后，被指定的参与人账号在**我的待办**里能看到这条任务

> **本仓实测验收脚本**（推荐）：
>
> ```bash
> # 1. 部署验证（流程定义是否成功生成）
> curl -X POST http://localhost:8101/wf/processDefine/getLastByName \
>   -H "Content-Type: application/json" \
>   -d '{"processDefineName":"biz_xxx"}'
> # → data: {id, name, displayName, type, state, version}（state=1 启用）
>
> # 2. 发起 + 完成完整性（façade.processDesign/page 看 isDeployed=1）
> curl -X POST http://localhost:8101/wf/processDesign/page \
>   -H 'Content-Type: application/json' -d '{"pageNum":1,"pageSize":10}'
> ```
>
> 详见 `../spec/06-facade.md` §4.1 + `../spec/08-compliance.md` §1（27 合规场景 1-9）。

---

## §8. 卡住了看这里（重写为本仓实测）

| 现象 | 原因 | 处理 |
|---|---|---|
| 部署 / 重新部署 是灰的 | 设计稿已是已部署状态 | 改画布并保存后，是否部署变"否"，按钮才可用 |
| 点了保存，发起的还是旧流程 | 保存只存草稿 | 列表里再执行一次部署 |
| 部署后审批页没有业务表单 | 节点没选任务表单 | 表单配置里选上，再部署 |
| 发起页找不到自己的流程 | 分类不对，或定义被停用 | 检查流程分类与流程定义状态 |
| 提交后没人收到待办 | 参与人为空，或处理类取不到人 | 见 `../ToT/guides/07-assignment-handlers.md` §3 行为约定：部门类处理类要求部门已配负责人 |
| 想改已在途实例的走向 | 版本化语义 | 新版本只影响新发起；确需原地改用重新部署 |
| **本仓实测补充**：deploy 失败提示 `节点 ID 含非法字符` | 节点 `id` 不符合 `^[A-Za-z0-9_]+$` | 改纯字母数字下划线（FIX-T34 §93）|
| **本仓实测补充**：deploy 失败提示 `handler 未注册: ...OrgUserAssignmentHandlers$XXX` | 节点 properties 中 `assignmentHandler` 字段值是完整版 FQCN 但本仓 SPI 实际加载简化版 | 改用简化版主用 `…XXX`（无 `OrgUserAssignmentHandlers$` 嵌套前缀），或确保 `main_common.py:register_builtin_assignments` 12 个 key 全部注册 |

---

## 跨文档交叉引用

- 流程定义 JSON 完整契约（顶层字段 + 节点 properties + 边 properties）：`../spec/02-flow-definition.md`
- 任务节点 properties 21 字段 + 5 未实现注解：`../ToT/guides/02-flow-definition.md` §4
- 7 个内置 assignmentHandler + 解析优先级：`../ToT/guides/07-assignment-handlers.md`
- 字段权限 1/2/3 + 双键格式：`manual/03-forms.md` §4 + `../spec/02-flow-definition.md` §4.1
- 业务数据落库（relTableName + persistMode）：`../spec/09-persist.md` §4.0 + `../ToT/guides/08-persist.md` §3
- 设计稿 / 流程定义 UPSERT 语义（实测警告）：`ToT/docs/README.md` §3-7
- 27 合规测试场景 1-9：`../spec/08-compliance.md` §1
- 决策节点 + W012 / W013 警告（task 多路径警告 + decision 默认边）：`../docs/known-issues.md §111/§113`