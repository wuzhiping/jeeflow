# 规范 08 · 合规测试

> **来源**：https://jeeflow-doc.mldong.com/spec/08-compliance
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**27 个合规测试场景参考**——这些场景是 jeeFlow 各语言实现必须通过的**行为契约**，也是设计者流程 JSON 设计的**最低质量门槛**。
>
> **本仓实测状态**：`docs/BUGS.md` 已声明"**27 个已修复 BUG（FIX-T1~T38）+ 0 个仍存**"（v1.9.0 2026-09-19 里程碑），所有 27 场景**全 PASS**。
>
> **裁剪记录**：6 节共 27 场景全部保留 + 加本仓实测注解（样例路径 + facade action 映射 + 实测位置）。

---

## §1. 引擎核心（v1.0，10 场景）

| # | 场景 | 验证点 | 本仓对应路径 |
|---|---|---|---|
| 1 | 简单线性 | `start → apply → task → end`，实例完成 | `flows/01-simple.json` |
| 2 | 多级审批 | 3 个 task 顺序审批，每个操作人校验 | `flows/02-multi-task.json` |
| 3 | 条件分支 | decision 根据 args 选分支 | `flows/03-decision-expr.json` + `flows/15-decision-amount.json` |
| 4 | 并行分支 | fork→\[A,B\]→join→end | `flows/04-fork-join.json` |
| 5 | 并行会签 | 3 个 actor 并行创建，全部完成 | `flows/05-countersign-parallel.json` |
| 6 | 串行会签 | 2 个 actor 顺序创建 | `flows/06-countersign-sequential.json` |
| 7 | 按比例会签 | 4 个 actor 并行，阈值完成 | `flows/07-countersign-ratio.json`（`#nrOfCompletedInstances` 表达式）|
| 8 | 退回发起人 | `submitType=6` 后第一个任务节点重执行（参与者=发起人），发起人收到新待办，实例保持 10 | `flows/09-with-reject.json` |
| 9 | 权限校验 | 非 actor 不可操作任务 | — |
| 10 | 拦截器 + 事件 | pre/post 拦截器、start/task/finish 事件 | `flows/08-custom-node.json`（含 custom handler）|

> **设计者实操**：跑完一遍 `flows/01-09` 即视为"核心场景已覆盖"；`flows_completeness.py <flow>.json` 0-100% 打分 + 6 层 31 项对齐可作为设计质量自检。

---

## §2. 引擎增强（v1.0.1 ~ v1.1.0，5 场景）

| # | 场景 | 验证点 | 本仓对应路径 |
|---|---|---|---|
| 11 | assignee 变量解析 | 变量命中 / 字面量回退 / `tf_nextNodeOperator` 优先 | `flows/11-assignee-vars.json` |
| 12 | 系统代执行 | `flow.auto` / `flow.admin` 放行 + 跳过用户注入 | `engine.py:107 _resolve_actors` 系统代执行路径 |
| 13 | 定义写操作 | `saveDefine` / `updateDefine` / `updateDefineState` / `removeDefine` | `flows/10-mixed-mode.json`（含 deploy）|
| 14 | `updateInstance` 级联 | 聚合根任务状态随实例更新落库 | `spi.py:37 update_instance`（v1.0.1 契约）|
| 15 | 门面路由 | `flow(action, map)` 各 action 返回 `code=0` + 正确 data | `facade.py:63` |

> **关键行为契约**（`model.py:112 ProcessInstance.withdraw` + `TaskState.abandon`）：
> - `update_instance` 走同一连接持久化——撤回/挂起/终止等聚合命令改完任务状态后级联落库
> - 引擎在完成任务后同步聚合内任务副本——确保下次 `update_instance` 拿到的是最新状态

---

## §3. 视图端点（v1.2.0，3 场景）

| # | 场景 | 验证点 | 本仓 facade action |
|---|---|---|---|
| 16 | 视图端点 | `getLastByName` / `approvalRecord` / `taskDetail` / `jumpAbleTaskNameList` / `latest` / 抄送操作 | `processDefine/getLastByName`（:1220）+ `processInstance/approvalRecord`（:1405）+ `processTask/detail`（:1473）+ `processTask/jumpAbleTaskNameList`（:1521）+ `processTask/latest`（:1634）+ `processInstance/createCCInstance`（:1436）|
| 17 | 高亮 | `highLight` 活跃/历史节点与路径补全 | `processInstance/highLight`（:1276）|
| 18 | 候选人 | `candidatePage` 候选配置映射 / 用户搜索钩子 | `processTask/candidatePage`（:1535）|

> **设计者实操**：6 个视图端点共同构成「流程详情抽屉」+「流程图高亮」+「候选人选择」3 大前端组件数据源；调错或参数错位即对应前端空白。

---

## §4. 对齐修复（v1.3.0，2 场景）

| # | 场景 | 验证点 | 本仓实现位置 |
|---|---|---|---|
| 19 | 抄送分页 | `ccList` 按抄送人分页 + 关联定义名/版本 | `facade.py:1457 processInstance_ccList` + `spi.py:70 page_cc_instances` |
| 20 | 参与者追加 | `addTaskActor` 追加不覆盖、去重 | `spi.py:53 add_task_actor`（v1.3.0 修复：v1.2.0 曾为覆盖语义，先删后插）|

> ⚠️ **设计陷阱**（FIX-T67 §67）：`addTaskActor` 是**追加**语义——原处理人保留可办。**转办**（摘原人）走 `processTask/transfer`，不要在薄壳里自拼 SQL 绕过引擎。**详见** `../ToT/guides/04-extensions.md` §5 + `../docs/known-issues.md §67`。

---

## §5. 元数据能力（v1.4.0，2 场景）

| # | 场景 | 验证点 | 本仓实现位置 |
|---|---|---|---|
| 21 | 枚举字典 | 7 个 key 对齐 boot3，value/label 与 Java enums 一致 | `metadata.py:55 enum_dict_keys()` + `:60 enum_dict(key)` |
| 22 | SPI 清单 | HandlerRegistry 注册 → 按类型/分组列出，order 升序 | `metadata.py:102 HandlerRegistry` |

> **本仓实测 2 处字典差异**（详见 `../ToT/spec/07-metadata.md`）：
> - `wf_process_submit_type` **缺 `7 转办`（TRANSFER）**
> - `wf_process_submit_type` **`20 拒绝申请` 与 `2 拒绝申请` label 重复**
>
> 设计者实操：前端下拉按 `value` 区分，避免依赖 label。

---

## §6. 撤回 / 转办 / 委托（issues 113~116，5 场景）

> **本仓实测位置**：`facade.py:565 processInstance_withdraw` + `:1880 processTask_transfer` + `:1611 processTask_surrogate` + `engine.py` 内置 `SurrogateInterceptor`（v1.9.0 默认开启，issues/116）。

| # | 场景 | 验证点 | 关键陷阱 |
|---|---|---|---|
| 23 | 撤回状态码与级联落库 | `processInstance/withdraw` 后，原进行中任务在**内存仓与 SQL 仓均 `taskState=30`**（不是 99）；已完成(20)/已终止(40) 任务行不被改写；`AbandonAllDoing` 与会签一票否决路径仍写 99 | 30 vs 99 区分：30=WITHDRAW（撤回），99=ABANDON（废弃）|
| 24 | 撤回鉴权 | 发起人撤回成功；实例任一进行中任务的参与者可撤回整单；无关第三人 → `99999999` + msg；**缺 operator → 明确报错，不得回落 `user1`**；`flow.auto`/`flow.admin` 放行；实例 `update_user` 与被撤任务的 `update_user` = 真实撤回人 | `operator` 硬必填，缺省 `user1` 会静默失真 |
| 25 | 转办 | `processTask/transfer` 后 A 待办消失、B 待办出现（**同一 `processTaskId`，高亮图/节点进度不变**）；审批记录出现 `submitType=7` 与 `tf_transferHistory` 一条；**B 再转给 C 后 A→B 那条仍在**（变量按"实例←任务←本次提交参数"合并，不得整体替换）；会签节点只摘 `fromActor` 一行、其余成员不受影响；**转办不得覆写任务 `actor_id`/`operator`**——转办后撤回/终止该单，`fromActor` 的 `doneList` 里不得凭空出现这条他没办过的单 | 7 条转办语义 + 10 条失败 msg 字面量文案（详见 `../ToT/spec/06-facade.md`）|
| 26 | 委托自动生效 | 窗口内配"张三→李四"后新单到达任务节点时，**李四待办出现该单且张三待办保留**（任一可办）；窗外 / `enabled=0` / 自己委托给自己 → 代理人不收到；**未配置 `IProcessExtRepository` 时建单不被打断**（静默跳过）；显式关闭后回到"仅台账"行为 | 委托是**追加**不是转办；不级联（A→B 不展开 B→C）；仅取**最新一条**生效委托 |
| 27 | 委托查询判据双仓一致 | 同一份委托数据，内存仓与 SQL 仓给出同一结论：空 `processName` 全流程兜底、时间窗 NULL=不限、`surrogate <> operator` 自委托过滤、`enabled` 只认 1 且脏值不当启用 | 4 条件跨栈必须同答案；`enabled` 读写两侧语义必须对齐 |

### §6 设计与测试 5 条警示

1. **撤回场景写测试时**：operator 必填、归属判据 3 条（发起人 / 进行中任务 actor / `flow.auto`+`flow.admin`）—— 三者任一命中即放行
2. **转办场景写测试时**：必须 ≥3 步才能验证「A→B→C 多跳仍留痕」+「会签节点只摘 fromActor 一行」
3. **委托场景写测试时**：必须钉住「(operator, processName) 同一作用域，先建窗内有效记录、再建一条更'新'的无效记录 → 断言**不并入**」
4. **撤回 vs 废弃 状态码**：30（WITHDRAW）≠ 99（ABANDONED），混淆会让查询"我撤回的"vs"会签废弃的"过滤错位
5. **失败 msg 跨栈字面量**：撤回/转办 10 条 `msg` 在所有语言实现必须逐字一致（详见 `../ToT/spec/06-facade.md` 「失败 msg 跨栈统一文案」表）

---

## 测试流程 JSON 维护约定

> **上游原文**：测试流程 JSON 文件唯一编辑源在 `jeeflow-java` 仓库的 `test/resources/flows/`（15 个）；各语言仓自带 `flows/` 入库副本，测试读本仓副本，维护者机器执行时由 resolver 精确镜像同步（全量复制+删孤儿）。

> **本仓实测**：本仓 `flows/` 含 **19 个 sample**（`01-simple` / `02-multi-task` / `03-decision-expr` / `04-fork-join` / `05-countersign-parallel` / `06-countersign-sequential` / `07-countersign-ratio` / `08-countersign-sequential-approve` / `08-custom-node` / `09-with-reject` / `10-mixed-mode` / `11-assignee-vars` / `11-assignment-handler` / `12-candidate-page` / `13-countersign-one-vote-veto` / `14-decision-submitType` / `15-decision-amount` / `16-delegate-test` / `17-suspend-resume-test`），覆盖上游 15 个 + 本仓额外 4 个（一票否决 + decision+submitType + delegate + suspend/resume）。注：08 与 11 各有 2 个同名文件（前缀复用），独立内容。
>
> 本仓测试驱动（**双端 PASS**）：
> - **BDD**（1131 个）：`bash bdd/bdd-1001-1060-p0-regression.sh` 等 4 个 phase 脚本
> - **TDD**（19 个）：`flows/01-17` 对应 scenarios 在 `tdd/` 留档
> - **EA 合规自检**：`python3 ToT/sop/ea-compliance.py`（44/44 PASS）

---

## 设计者实操速查

| 设计阶段 | 必跑检查 |
|---|---|
| 写流程 JSON | `python3 ToT/sop/flow_completeness.py <flow>.json`（0-100% + 下一步建议）|
| 改完 JSON | `python3 ToT/sop/tdd-flow.py <flow>.json`（生成 baseline + scenarios）|
| 上线前 | `python3 ToT/sop/ea-compliance.py`（44/44 PASS，含 §9.9 路径可移植性 + 自动化）|
| 设计器「assignmentHandler 下拉」 | `metadata.py:120 list_handlers("AssignmentHandler")`（注意完整版/简化版差异）|
| 设计器「拦截器 post」 | `metadata.py:124 list_handlers_group("FlowInterceptor", "post")` + `register_persist_meta` 自动注册 PersistPostInterceptor |
| 委托配置后验证 | `metadata.py:60 enum_dict("wf_process_instance_state")` 取字典做状态徽标 |
| 跨语言契约保证 | 字典 key `wf_*` 一致；字典 value 数值一致；字典 label 文案一致——本仓 `metadata.py:25 _DICTS` 与 Java enum 对齐 |