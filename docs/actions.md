# `/wf/{action:path}` 动作清单

所有请求走 `POST /wf/{action:path}`（见 `main_pg.py:519`、`main.py:180`），
由 `state["facade"].flow(action, body)` 转发到 `Facade._<action.replace("/", "_")>` 方法。
action 命名约定：`{实体}/{动作}`，统一驼峰、不带前缀下划线。

源：`vendor/jeeflow/facade.py`（grep `^\s+async def _\w+\(self`）。`.venv/site-packages/jeeflow/` 保留作参考。

> **与其他 API 文档的关系**（避免重复维护）：
> - 本表只列 **59 个 `/wf/{action}` HTTP 端点**（门面层可见的动作）
> - **73 个 vendor/jeeflow 公开 API**（含内部 helper / 模型 / 枚举）→ 见 [`ToT/CC/api-index.md`](../ToT/CC/api-index.md)
> - **11 个核心 action 详解**（含请求/响应字段表 + 注意事项）→ 见 [`docs/api.md`](./api.md)
>
> **何时更新本表**：新增/修改 `/wf/{action}` 时；其余 API 用 `ToT/sop/health-check.py --dimension api --json` 自动核对覆盖率。

---

## 1. processDefine — 流程定义（`wf_process_define`）

| # | Action | 方法 | 行号 | 说明 |
|---|--------|------|------|------|
| 1 | `processDefine/page` | `_processDefine_page` | 77 | 流程定义分页 |
| 2 | `processDefine/detail` | `_processDefine_detail` | 84 | 流程定义详情 |
| 3 | `processDefine/startAndExecute` | `_processDefine_startAndExecute` | 96 | 按定义名启动并直接执行（seed_business 用） |
| 4 | `processDefine/deploy` | `_processDefine_deploy` | 183 | 部署定义 |
| 5 | `processDefine/redeploy` | `_processDefine_redeploy` | 223 | 重新部署 |
| 6 | `processDefine/remove` | `_processDefine_remove` | 237 | 删除定义 |
| 7 | `processDefine/upAndDown` | `_processDefine_upAndDown` | 243 | 上下移动节点（排序） |
| 8 | `processDefine/getLastByName` | `_processDefine_getLastByName` | 679 | 按名称取最新一版定义 |

## 2. processDesign — 流程设计（`wf_process_design`，部署前的图形化设计）

| # | Action | 方法 | 行号 | 说明 |
|---|--------|------|------|------|
| 9 | `processDesign/page` | `_processDesign_page` | 322 | 设计分页（含 `m_is_deployed` 条件查询） |
| 10 | `processDesign/detail` | `_processDesign_detail` | 337 | 设计详情 |
| 11 | `processDesign/save` | `_processDesign_save` | 372 | 新增设计（含 `isDeployed` 强转 bool） |
| 12 | `processDesign/update` | `_processDesign_update` | 409 | 修改设计 |
| 13 | `processDesign/updateDefine` | `_processDesign_updateDefine` | 432 | 仅更新定义图（含 `isDeployed` 强转） |
| 14 | `processDesign/deploy` | `_processDesign_deploy` | 186 | 设计→定义（首次部署） |
| 15 | `processDesign/redeploy` | `_processDesign_redeploy` | 467 | 设计重新部署 |
| 16 | `processDesign/remove` | `_processDesign_remove` | 506 | 删除设计 |
| 17 | `processDesign/listByType` | `_processDesign_listByType` | 513 | 按类型列出设计 |

## 3. processInstance — 流程实例（`wf_process_instance`）

| # | Action | 方法 | 行号 | 说明 |
|---|--------|------|------|------|
| 18 | `processInstance/page` | `_processInstance_page` | 99 | 实例分页 |
| 19 | `processInstance/detail` | `_processInstance_detail` | 107 | 实例详情 |
| 20 | `processInstance/startAndExecute` | `_processInstance_startAndExecute` | 145 | 启动并执行实例 |
| 21 | `processInstance/withdraw` | `_processInstance_withdraw` | 252 | 撤回实例 |
| 22 | `processInstance/bizData` | `_processInstance_bizData` | 543 | 业务数据 |
| 23 | `processInstance/highLight` | `_processInstance_highLight` | 687 | 高亮节点进度 |
| 24 | `processInstance/approvalRecord` | `_processInstance_approvalRecord` | 816 | 审批记录 |
| 25 | `processInstance/getAssigneeTextData` | `_processInstance_getAssigneeTextData` | 831 | 审批人文本化 |
| 26 | `processInstance/createCCInstance` | `_processInstance_createCCInstance` | 847 | 创建抄送实例（seed_business 用） |
| 27 | `processInstance/updateCCStatus` | `_processInstance_updateCCStatus` | 860 | 更新抄送状态 |
| 28 | `processInstance/ccList` | `_processInstance_ccList` | 868 | 抄送列表 (FIX-T61 §61: 支持 processInstanceId 过滤) |
| 29 | `processInstance/stats/overview` | `_processInstance_stats_overview` | 1209 | 看板总览（Round 3 修复入口） |
| 30 | `processInstance/stats/trend` | `_processInstance_stats_trend` | 1247 | 趋势 |
| 31 | `processInstance/stats/group` | `_processInstance_stats_group` | 1282 | 分组聚合 |
| 32 | `processInstance/suspend` | `_processInstance_suspend` | 1486 | 实例挂起 (state=50 PENDING, FIX-T70 §70) |
| 33 | `processInstance/resume` | `_processInstance_resume` | 1503 | 实例恢复 (FIX-T70 §70) |
| 34 | `processInstance/rollback` | `_processInstance_rollback` | 461 | 流程实例回滚 (state=WITHDRAW, 废弃 DOING 任务, FIX-T107 §7.3.1) |
| 35 | `processInstance/doingList` | `_processInstance_doingList` | 500 | DOING 实例扫描 (断点续跑 / startup hook, FIX-T109 §7.3.3) |

> ⚠️ **submitType 路由相关**:
> - `submitType` 是执行参数 (request body 字段), 由 `processTask/execute` 等 action 接收
> - 完整 submitType 取值表 + 引擎行为见 `docs/flow.md §3.3` (submitType 路由)
> - **submitType 拓扑约束 (FB-0012 2026-11-17 修订)**: submitType=20 (COUNTERSIGN_DISAGREE) 仅在会签 task → end 直连时生效; 后接 decision 节点会导致一票否决失效. 详见 `docs/flow.md §3.3 submitType 拓扑约束表` + `docs/known-issues.md §116`
> - 拓扑约束是设计阶段关注 (processDesign 阶段), 不是 action 行为; 测试 agent 在跑会签一票否决用例时必查 `processDesign/detail` 确认拓扑

## 4. processTask — 流程任务（`wf_process_task`）

| # | Action | 方法 | 行号 | 说明 |
|---|--------|------|------|------|
| 32 | `processTask/todoList` | `_processTask_todoList` | 279 | 待办列表 |
| 33 | `processTask/doneList` | `_processTask_doneList` | 287 | 已办列表 |
| 34 | `processTask/execute` | `_processTask_execute` | 295 | 执行任务（同意/拒绝/委派等，seed_business 用） |
| 35 | `processTask/detail` | `_processTask_detail` | 876 | 任务详情 |
| 36 | `processTask/jumpAbleTaskNameList` | `_processTask_jumpAbleTaskNameList` | 924 | 可跳转的目标任务名列表 |
| 37 | `processTask/candidatePage` | `_processTask_candidatePage` | 938 | 候选人分页 |
| 38 | `processTask/surrogate` | `_processTask_surrogate` | 1014 | 委派 |
| 39 | `processTask/addCandidate` | `_processTask_addCandidate` | 1017 | 增加候选人 |
| 40 | `processTask/latest` | `_processTask_latest` | 1028 | 最新任务 |
| 41 | `processTask/removeCandidate` | `_processTask_removeCandidate` | 1262 | 减签 |
| 42 | `processTask/transfer` | `_processTask_transfer` | 1529 | 任务转交 (替换 actorIds) |
| 43 | `processTask/comment` | `_processTask_comment` | 1551 | 任务评论 (追加到 task.variables._comments) |
| 44 | `processTask/extra` | `_processTask_extra` | 1578 | 任务额外信息 (合并到 task.variables._extra) |
| 45 | `processTask/delegate` | `_processTask_delegate` | 1602 | 任务委派 (per-task 临时, **字段名 `targetUserId` 不是 `assignee`**, 详见 `docs/flow.md §5.3.1` + `docs/known-issues.md §114` FB-0009) |
| 46 | `processTask/delegateHistory` | `_processTask_delegateHistory` | 1647 | delegate 历史查询 (BDD #1106, FIX-T74) |
| 47 | `processTask/transferAndAdd` | `_processTask_transferAndAdd` | — | transfer + addCandidate 合并 (BDD #1107, FIX-T75) |
| 48 | `processTask/withForm` | `_processTask_withForm` | — | task 级表单绑定 (BDD #1108, FIX-T76) |

## 5. processSurrogate — 委托代理（`wf_process_surrogate`）

| # | Action | 方法 | 行号 | 说明 |
|---|--------|------|------|------|
| 41 | `processSurrogate/page` | `_processSurrogate_page` | 577 | 代理分页（含 `m_enabled` 条件查询） |
| 42 | `processSurrogate/save` | `_processSurrogate_save` | 588 | 新增代理（含 `enabled` 强转 bool） |
| 43 | `processSurrogate/update` | `_processSurrogate_update` | 605 | 更新代理 |
| 44 | `processSurrogate/detail` | `_processSurrogate_detail` | 619 | 代理详情 |
| 45 | `processSurrogate/remove` | `_processSurrogate_remove` | 670 | 删除代理 |

---

## 公共别名

| # | Action | 方法 | 行号 | 说明 |
|---|--------|------|------|------|
| 46 | `startAndExecute` | `_startAndExecute` | 148 | `_processInstance_startAndExecute` 的别名 |
| 47 | `taskAddActor` | `_taskAddActor` | 1020 | `_processTask_addCandidate` 的别名 |

---

## 路由解析机制（`facade.py:62-73`）

```python
async def flow(self, action: str, args: Optional[dict] = None) -> dict:
    handler = getattr(self, "_" + action.replace("/", "_"), None)
    if handler is None:
        return self._error(f"未知 action: {action}")
    data = await handler(args)
    return self._ok(_stringify_ids(data))
```

- `/` → 下划线；因此 `processDefine/page` → `_processDefine_page`。
- 未知 action 返回 `{code:99999999, msg:"未知 action: ..."}`，不抛 404。
- 所有 id 类字段（雪花 id >2^53）在出口经 `_stringify_ids` 统一转字符串，避免 JS 丢精度。

---

## 已知依赖外部补丁的 action（main_pg.py）

| Action | 补丁 | 原因 |
|--------|------|------|
| `processSurrogate/save` `update` `page` | `_safe_save_surrogate/_update_surrogate` + `_safe_build_ext_where` | `enabled` int→bool（PG `boolean` 列） |
| `processDesign/save` `update` `page` | `_safe_save_design/_update_design` + `_safe_build_ext_where` | `isDeployed` int→bool |
| `processTask/execute` `processInstance/startAndExecute` | `_safe_save_task/_save_instance` | `taskType`/`performType` int→str（PG `VARCHAR(64)` 枚举） |
| `processSurrogate/save` `processDesign/save` | `_safe_flow` 入口 `enabled` 强转 bool | facade 直传 int 走 facade 直写 |
| `processInstance/stats/overview` | `_fixed_stats_avg_dur` + `_fixed_stats_task_agg` | PG `INTERVAL`→`timedelta` 需 `total_seconds()`；`perform_type=1` 字面量需改 `'1'` |

---

## 端到端验证脚本

```bash
curl -X POST http://127.0.0.1:8101/wf/processInstance/stats/overview -H 'Content-Type: application/json' -d '{}'
curl -X POST http://127.0.0.1:8101/wf/processDesign/page -H 'Content-Type: application/json' \
  -d '{"pageNum":1,"pageSize":5,"conditions":[{"column":"t.is_deployed","value":0,"compare":"EQ"}]}'
curl -X POST http://127.0.0.1:8101/wf/processSurrogate/page -H 'Content-Type: application/json' \
  -d '{"pageNum":1,"pageSize":5,"conditions":[{"column":"t.enabled","value":0,"compare":"EQ"}]}'
```