# 第 7 章 · 验证一条流程跑对了没有

> **来源**：https://jeeflow-doc.mldong.com/manual/07-verify-and-troubleshoot
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**操作手册第 7 章**——「跑通 ≠ 跑对」。本章给"看哪里、看什么、状态码什么意思"，以及一份跨章排错总表。
>
> **本仓实测**：基于 `vendor/jeeflow/facade.py` 60+ action + `model.py:46 InstanceState` 7 枚举 + `:55 TaskState` 6 枚举 + `:70 SubmitType` 9 枚举。
>
> **裁剪记录**：§1 三处回看 + §2 提交类型对照**保留**+ 加本仓 facade 端点实测；§3 用接口自己验一遍 + §4 跨章排错总表**重写为本仓实测**；§5 还是没解决**保留原文**（反馈 3 件套是协作规范）。上游 §3 中 mldong 框架专属的 `sys/login` + `Authorization` token 流程裁掉（本仓不引入 mldong 框架）。

---

## §1. 三处回看

### 1.1 我发起的：整体状态

> **本仓实测**（`facade.py:158 processInstance_page` + `model.py:46 InstanceState`）：

| 状态 | 值 | 含义 | 本仓 enum |
|---|---|---|---|
| 进行中 | `10` | 还有节点没办完 | `InstanceState.DOING` |
| 已完成 | `20` | 正常走到结束节点 | `InstanceState.DONE`（上游 FINISHED）|
| 已撤回 | `30` | 发起人撤回 | `InstanceState.WITHDRAW` |
| 强行终止 | `40` | 管理员终止 | `InstanceState.INTERRUPT` |
| 已拒绝 | `45` | 某节点点了不同意 | `InstanceState.REJECT` |
| 挂起 | `50` | 暂停中 | `InstanceState.PENDING` |
| 已废弃 | `99` | 作废 | `InstanceState.ABANDON` |

行上点 **详情** 打开抽屉，**详情** 页签按表单回显当初提交的内容——怀疑"填错了或没提交上去"时先看这里。

> **本仓实测**（`facade.py:203 processInstance_detail`）：返回 `data` 含 `id` / `state` / `ext`（实例变量）/ `formData` / `jsonObject` / `tasks` / `activeTaskList`。详见 `../spec/06-facade.md` §4.2。

### 1.2 流程图：走过的路

实例详情 → **流程图** 页签。走过的节点标绿并显示实际处理人，没走到的分支保持原色。

> **本仓实测**（`facade.py:1276 processInstance_highLight`）：返回 `data` 含 `activeNodeNames` / `historyNodeNames` / `historyEdgeNames` / `nodeProgress`（节点成员进度 `{节点名: {members: [...], type?}}`）。详见 `../spec/06-facade.md` §4.6。

看这张图能一眼回答三个问题：

- 参与人解析对不对（节点下挂的人是不是预期的）
- 条件分支走了哪条（演示的请假流程：天数 5 走了 `>3天(再分管)`）
- 有没有卡住（结束节点没绿就是还在途中）

### 1.3 审批记录：谁在什么时候说了什么

> **本仓实测**（`facade.py:1405 processInstance_approvalRecord`）：返回 `rows[]` 含 `taskName` / `displayName` / `taskType` / `performType` / `taskState` / `operator` / `finishTime` / **`ext`**（含 `tf_approvalComment` / `tf_approvalAttachment` / `tf_transferHistory`）。

每个节点一条，含办理人、提交类型标签（发起申请 / 同意申请 / 拒绝申请 / 退回上一步 / 退回发起人 / 跳转 / 重新提交）、审批意见、附件。查责任链、查为什么被退回，看这里。

> **本仓实测转办留痕**（FIX-T75）：`tf_transferHistory` 列表包含 `{submitType:7, fromActor, toActor, reason, time, operator}`，跨跳**只追加不覆盖**——B 再转给 C 后 A→B 那条仍在。详见 `../spec/06-facade.md` §4.3 processTask/transfer。

---

## §2. 提交类型对照

> **本仓实测**（`model.py:70 SubmitType(IntEnum)`）：

| 值 | 枚举 | 含义 | 由哪个按钮产生 |
|---|---|---|---|
| `0` | `APPLY` | 发起申请 | 发起 |
| `1` | `AGREE` | 同意申请 | 同意 |
| `2` | `REJECT` | 拒绝申请 | 不同意（普通节点）|
| `3` | `ROLLBACK` | 退回上一步 | 退回上一步 |
| `4` | `JUMP` | 跳转 | 跳转 |
| `5` | `RE_APPLY` | 重新提交 | 被退回发起人后重新提交 |
| `6` | `ROLLBACK_TO_OPERATOR` | 退回发起人 | 退回发起人 |
| `7` | `TRANSFER` | 转办 | `processTask/transfer`（不走 `execute`）|
| `20` | `COUNTERSIGN_DISAGREE` | 会签拒绝 | 不同意（会签节点）|

> **本仓实测差异警示**：`spec/07-metadata.md` §枚举字典 中 `wf_process_submit_type` **缺 `7` TRANSFER**（`metadata.py:34 _DICTS` 字典实测只有 8 项）—— 详见 `ToT/docs/README.md` §3-1。这是上游字典与本仓枚举不同步问题，不影响引擎行为但影响设计器字典展示。

完整状态机见 `../spec/03-state-machine.md`。

---

## §3. 用接口自己验一遍

> **裁剪说明**：上游 §3 示例使用 mldong 框架 `sys/login` + `Authorization` token 流程——本仓 Python 引擎**不实现登录**（`sa-token` / JWT 等鉴权由集成方实现）。本节重写为本仓 Python 引擎实测 curl（不依赖登录态）。

界面之外，直接打门面接口更快定位是前端还是后端的问题。本仓 `:8101`（内存）或 `:8102`（PG）：

```bash
# 1. 我的待办
curl -s -X POST http://localhost:8101/wf/processTask/todoList \
  -H 'Content-Type: application/json' \
  -d '{"operator":"user1","pageNum":1,"pageSize":10}'
# → {"code":0, "msg":"成功", "data":{...}} 或 {"code":99999999, "msg":"...", "data":null}

# 2. 实例详情
curl -s -X POST http://localhost:8101/wf/processInstance/detail \
  -H 'Content-Type: application/json' \
  -d '{"id":"<实例ID>"}'

# 3. 流程图高亮
curl -s -X POST http://localhost:8101/wf/processInstance/highLight \
  -H 'Content-Type: application/json' \
  -d '{"id":"<实例ID>"}'

# 4. 审批记录
curl -s -X POST http://localhost:8101/wf/processInstance/approvalRecord \
  -H 'Content-Type: application/json' \
  -d '{"id":"<实例ID>"}'
```

**返回码速查**：

| 返回 code | 含义 | 处理 |
|---|---|---|
| `0` | 成功 | — |
| `99999999` | 业务失败 | 看 `msg` 字段 |
| `99990403` | 登录态失效 | 集成层负责（mldong 框架惯例）|
| `99990406` | 权限码不足 | 检查 `wf:{action}` 权限码分配 |

> **本仓实测统一响应**（`facade.py:79 _ok` + `:98 _ok_with_stringify_ids`）：所有 action 返回 `{code, msg, data}` 三字段结构；`code=0` 成功；`code=99999999` 业务失败；其他码由集成层框架（如 sa-token / Spring Security）返回。详见 `../spec/06-facade.md` §2.1。

**接口正常、界面异常** → 问题在前端；**接口就报错** → 问题在后端或数据。

---

## §4. 跨章排错总表（重写为本仓实测）

| 现象 | 最可能的原因 | 处理 / 跨章链接 |
|---|---|---|
| 部署按钮点不动 | 设计稿已是已部署状态 | [第 4 章 §6](04-design-and-publish.md) — 改画布并保存后重新点 |
| 改了流程但行为没变 | 只保存没部署；或在途实例仍走旧版本 | [第 4 章 §6](04-design-and-publish.md) — 重新部署；旧实例按发起时版本走 |
| 提交后没人收到待办 | 部门没配负责人 / 角色无成员 / 参与人填错 | [第 2 章](02-dept-user-role.md)、[第 5 章](05-participants.md) — 优先看 `OrgUserProvider` SPI 数据 |
| 审批页没有业务表单 | 节点没绑任务表单 | [第 3 章 §3.2](03-forms.md) — 选上 `properties.form` 再部署 |
| 发起抽屉是空的 | 没选实例启动表单 | [第 3 章 §3.1](03-forms.md) — 流程属性选「实例启动表单」 |
| 字段本该只读却能改 | 未启用字段权限，或该节点设成可编辑 | [第 3 章 §4](03-forms.md) — 启用 `PERMISSION_f_*` |
| 条件分支不按预期走 | 表达式变量名与字段名不一致 | [第 3 章 §5](03-forms.md) — 对齐 `f_<字段名>`（区分大小写） |
| 提示没有 `wf:xxx` 权限 | 角色未授权该按钮 | [第 1 章 §5](01-deploy-and-accounts.md) — 系统设置 → 角色管理 → 授权菜单 |
| 接口能通、页面报错 | 前端问题（非引擎）| 反馈给前端 / jeeflow-ui 维护者 |
| 审批完业务表里没数据 | 没配后置拦截器或关联业务表 | [第 8 章](08-persist.md) — 配置 `relTableName` + `persistMode` + `postInterceptors` |
| **本仓实测补充**：deploy 失败报 `节点 id 含非法字符` | 节点 `id` 不符合 `^[A-Za-z0-9_]+$` | 改纯字母数字下划线（FIX-T34 §93）|
| **本仓实测补充**：deploy 失败报 `handler 未注册: ...` | `assignmentHandler` / `decisionHandler` / `interceptor` 未在 `main_common.py:build_*_handlers` 注册 | 注册实例或检查 `register_builtin_assignments` 12 个 key |
| **本仓实测补充**：业务表 `value` 字段类型不匹配 | 大整数 userId（如雪花）落入 `VARCHAR create_user` 列失败 | 配 `JdbcDynamicTableWriter.primary_key_generator` 或调整列类型 |

---

## §5. 还是没解决（保留原文）

带上这三样去反馈，定位会快很多：

1. 流程定义的 JSON（设计器右上角 **查看数据** 可看）
2. 复现步骤（谁发起、谁办理、点了哪个按钮）
3. 后端日志片段（`docker logs boot4j-api`）与浏览器控制台的报错

> **本仓实测补强**：
> - 流程 JSON：`facade.py:1220 processDefine_getLastByName` 取最新定义 → `data.jsonObject`
> - 后端日志：本仓 Python `main.py` / `main_pg.py` 启动时输出 SQL / 异常 trace；调试时可用 `logging.basicConfig(level=DEBUG)` 看详细
> - 合规基线：`ToT/sop/ea-compliance.py`（44 项 EA 合规）+ `ToT/sop/flow_completeness.py <flow>.json`（0-100% 评分）作为标准验收

---

## 跨文档交叉引用

- 状态机全集（InstanceState 7 + TaskState 6）：`../spec/03-state-machine.md`
- Facade 60+ action 完整契约：`../spec/06-facade.md`
- 流程图高亮 + 节点成员进度：`../spec/06-facade.md` §4.6
- 字段权限 + 任务表单绑定：`manual/03-forms.md`
- 部门 / 角色数据前提：`manual/02-dept-user-role.md`
- 参与人解析 4 优先级 + 7 handler：`manual/05-participants.md`
- 业务落库（relTableName + persistMode + postInterceptors）：`manual/08-persist.md` + `../spec/09-persist.md`
- 27 合规测试场景：`../spec/08-compliance.md`
- 部署 / 环境 / 端口：`ToT/sop/engine-deploy.md` + `ToT/sop/env-config.md`