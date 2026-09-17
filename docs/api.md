# API 端点参考

本文档集中登记所有可调用的 HTTP 端点。引擎统一通过 `/wf/{action:path}` 单入口门面路由（`./main.py:180`），转发到 `Facade._<action>` 方法。

---

## 1. 端点清单

### 1.1 流程设计（processDesign）

| 方法 | 路径 | 用途 | 必填入参 | 出参 |
| --- | --- | --- | --- | --- |
| POST | `/wf/processDesign/page` | 分页查询流程设计 | `pageNo` / `pageSize` | `{rows: [...], total: N}` |
| POST | `/wf/processDesign/detail` | 详情（含 `content` JSON） | `id` | `{id, name, displayName, content, ...}` |
| POST | `/wf/processDesign/save` | **UPSERT** 设计（按 `name` 唯一） | `name` + `content` (JSON 字符串) | `{id: <processDesignId>}` |
| POST | `/wf/processDesign/update` | 更新设计 | `id` / `content` | `{id}` |
| POST | `/wf/processDesign/updateDefine` | 更新定义（同步到 wf_process_define） | `id` | `{id}` |
| POST | `/wf/processDesign/deploy` | 部署（生成 processDefine） | `id` | `{id, processDefineId}` |
| POST | `/wf/processDesign/redeploy` | 重新部署 | `id` | `{processDefineId}` |
| POST | `/wf/processDesign/getLastByName` | 按 name 查最新设计 | `name` | `{id, content, ...}` |

### 1.2 流程定义（processDefine）

| 方法 | 路径 | 用途 | 必填入参 | 出参 |
| --- | --- | --- | --- | --- |
| POST | `/wf/processDefine/page` | 分页查询流程定义 | `pageNo` / `pageSize` | `{rows: [...], total: N}` |
| POST | `/wf/processDefine/detail` | 详情 | `id` | `{id, name, version, content, ...}` |
| POST | `/wf/processDefine/startAndExecute` | 启动实例并执行第一步 | `processDefineId` / `operator` / `assignees` / `variables` | `{processInstanceId, processTaskId, ...}` |
| POST | `/wf/processDefine/deploy` | 同 `processDesign/deploy` 别名 | `id` | `{processDefineId}` |
| POST | `/wf/processDefine/redeploy` | 同 `processDesign/redeploy` 别名 | `id` | `{processDefineId}` |
| POST | `/wf/processDefine/remove` | 删除定义 | `id` | `{id}` |
| POST | `/wf/processDefine/upAndDown` | 上线/下线 | `id` / `action` | `{id, status}` |

### 1.3 流程实例（processInstance）

| 方法 | 路径 | 用途 | 必填入参 | 出参 |
| --- | --- | --- | --- | --- |
| POST | `/wf/processInstance/startAndExecute` | 同 `processDefine/startAndExecute` 别名 | 同上 | 同上 |
| POST | `/wf/processInstance/execute` | 执行任务（提交下一步） | `processTaskId` / `submitType` / `operator` / `assignees?` / `variables?` | `{processTaskId, nextProcessTaskId, state, ...}` |
| POST | `/wf/processInstance/detail` | 实例详情（含 state） | `id` (`processInstanceId`) | `{id, state, variables, tasks, ...}` |
| POST | `/wf/processInstance/page` | 分页查询实例 | `pageNo` / `pageSize` | `{rows: [...], total: N}` |
| POST | `/wf/processInstance/stats/overview` | 实例统计概览 | — | `{doing, done, reject, ...}` |

### 1.4 运维端点（旁路）

| 方法 | 路径 | 用途 | 来源 |
| --- | --- | --- | --- |
| GET | `/healthz` | 健康检查 | `./main.py:180` |
| POST | `/api/reset` | 重置内存中所有实例 / 设计 / 定义 | `./main_pg.py:526` |
| GET | `/api/stats/users` | 列出用户 | `./main_pg.py` |
| GET | `/api/stats/roles` | 列出角色 | `./main_pg.py` |
| GET | `/api/stats/dicts` | 字典项 | `./main_pg.py` |

---

## 2. submitType 取值（processInstance/execute）

详见 `./docs/state.md` §2 SubmitType 枚举：

| 取值 | 含义 | 备注 |
| --- | --- | --- |
| 0 | APPLY | 仅 `startAndExecute` 内部注入；外部传 0 会被强制改为 1（`facade.py:300` bug） |
| 1 | AGREE | 同意 |
| 2 | REJECT | 驳回 |
| 3 | RETURN | 回退（重新激活上一节点） |
| 5 | FORWARD | 转交 |
| 6 | DELEGATE | 委派 |
| 20 | SUBMIT | 与 AGREE 等价 |

完整路由矩阵见 `./docs/flow.md` §7a。

---

## 3. 字段命名约定

| 场景 | 字段名 | 来源 |
| --- | --- | --- |
| 启动实例 | `processDefineId`（顶层入参） | `/wf/processInstance/startAndExecute` |
| 启动响应 | `processInstanceId` / `processTaskId` | 同上 |
| 执行任务 | `processTaskId` | `/wf/processInstance/execute` |
| 详情查询 | `id`（顶层入参，值是 processInstanceId） | `/wf/processInstance/detail` |
| 详情响应 | `state`（顶层，`InstanceState` 枚举值 10/20/45） | 同上 |

> 字段名不可缩写（如 `pid` 不可，必须写完整 `processInstanceId`）。

### 3.1 `processInstance/detail` 响应关键字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `data.id` | string | processInstanceId |
| `data.state` | int | InstanceState 枚举（10/20/30/40/45/50/99） |
| `data.finish_state` | any | **恒为 null**（历史遗留字段，忽略） |
| `data.tasks[]` | array | 全部 task（含已完成 + 活跃），含 `id/taskName/taskState/operator/taskActorIdList/variable` |
| `data.tasks[].taskState` | int | TaskState 枚举（10=DOING / 20=DONE） |
| `data.tasks[].taskActorIdList` | array | 候选执行人列表（来自 JSON `assignee` / `assignmentHandler`） |
| `data.tasks[].variable` | string | JSON 字符串（**需 `JSON.parse`**），含 `submitType/u_*/f_*` 等 |
| `data.activeTaskList[]` | array | 仅 taskState=10 的活跃 task（**测试 runner 直接读这里取 taskId，不必扫 tasks[]**） |
| `data.activeTaskList[].formKey` | string | 表单 key（来自 JSON `form` 字段） |
| `data.activeTaskList[].taskActorIdList` | array | 候选执行人 |

**示例**（截取 `02-multi-task` 启动后 detail）：
```json
{
  "state": 10,
  "tasks": [
    {"id":"...","taskName":"apply","taskState":20,"operator":"applicant",...},
    {"id":"...","taskName":"task1","taskState":10,"operator":"","taskActorIdList":["leader"],...}
  ],
  "activeTaskList": [
    {
      "id":"<taskId>",
      "taskName":"task1",
      "taskState":10,
      "operator":"",
      "taskActorIdList":["leader"],
      "formKey":"leave-form"
    }
  ]
}
```

### 3.2 `processInstance/highLight` 响应

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `data.activeNodeNames` | array | 当前活跃节点名；空数组 `[]` = 实例已结束 |
| `data.historyNodeNames` | array | 已走过节点名（含 `end`） |
| `data.historyEdgeNames` | array | 已走过边名 |
| `data.nodeProgress.<nodeName>.members[]` | array | 该节点参与人 `{id, name, done}` |

**示例**（02-multi-task 完成态）：
```json
{
  "activeNodeNames": [],
  "historyNodeNames": ["apply","task1","task2","task3","end"],
  "historyEdgeNames": ["e0","e_apply_1","e2","e3","e4"],
  "nodeProgress": {
    "apply":   {"members":[{"id":"applicant","name":"用户applicant","done":true}]},
    "task1":   {"members":[{"id":"leader","name":"李四","done":true}]},
    "task2":   {"members":[{"id":"manager","name":"...","done":true}]},
    "task3":   {"members":[{"id":"boss","name":"...","done":true}]}
  }
}
```



---

## 4. 典型调用链

### 4.1 部署新流程

```text
1. POST /wf/processDesign/save
   body: {"content": "<JSON 字符串>"}
   resp: {id: <processDesignId>}

2. POST /wf/processDesign/deploy
   body: {"id": <processDesignId>}
   resp: {id, processDefineId: <id>}
```

### 4.2 发起并完成审批

```text
1. POST /wf/processInstance/startAndExecute
   body: {
     "processDefineId": <id>,
     "operator": "user1",
     "assignees": {"apply": "user1"},
     "variables": {"amount": 5000}
   }
   resp: {processInstanceId, processTaskId}

2. POST /wf/processInstance/execute
   body: {
     "processTaskId": <id>,
     "submitType": 1,
     "operator": "user2"
   }
   resp: {state: <7|10|45>, nextProcessTaskId?, ...}

3. POST /wf/processInstance/detail
   body: {"id": <processInstanceId>}
   resp: {id, state, ...}
```

### 4.3 回归测试（自动）

```bash
python ./tdd/regression_runner.py \
  --define 145 \
  --cases 0,1,2,3,5,6,20 \
  --base http://localhost:8101
```

详见 `./tdd/README.md` "测试脚本索引与使用" 段。

---

## 5. 错误处理

| HTTP 状态 | 含义 | 排查路径 |
| --- | --- | --- |
| 200 + `code != 0` | 业务错误（如 submitType 非法） | 查响应 `msg` 字段 |
| 404 | action 名拼错 | 对照 §1 端点表 |
| 500 | 引擎异常 | 服务 stdout 走 `/dev/pts/42`（详见 `./docs/known-issues.md` §4），离线查不到 |

---

## 6. 跨参考

- 引擎行为约束：`./docs/known-issues.md`
- 状态码双义：`./docs/state.md` §3
- SubmitType 路由矩阵：`./docs/flow.md` §7a
- 测试基建：`./tdd/README.md`
- 示例流程索引：`./flows/README.md`
