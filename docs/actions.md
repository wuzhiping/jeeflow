# `/wf/{action:path}` 动作清单

所有请求走 `POST /wf/{action:path}`（见 `main_pg.py:519`、`main.py:180`），
由 `state["facade"].flow(action, body)` 转发到 `Facade._<action.replace("/", "_")>` 方法。
action 命名约定：`{实体}/{动作}`，统一驼峰、不带前缀下划线。

源：`vendor/jeeflow/facade.py`（grep `^\s+async def _\w+\(self`）。`.venv/site-packages/jeeflow/` 保留作参考。

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
| 28 | `processInstance/ccList` | `_processInstance_ccList` | 868 | 抄送列表 |
| 29 | `processInstance/stats/overview` | `_processInstance_stats_overview` | 1209 | 看板总览（Round 3 修复入口） |
| 30 | `processInstance/stats/trend` | `_processInstance_stats_trend` | 1247 | 趋势 |
| 31 | `processInstance/stats/group` | `_processInstance_stats_group` | 1282 | 分组聚合 |

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