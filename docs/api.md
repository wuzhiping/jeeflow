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
| GET | `/healthz` | 健康检查 + 版本号（`version` / `version_full` / `git_sha` / `build_time`，来自 `vendor/jeeflow/__init__.py:__version__` 等；release 时由 `ToT/sop/release.sh` 自动更新） | `./main.py:180` / `./main_common.py:829` |
| GET | `/version` | 版本元数据查询（仅 `version` / `version_full` / `git_sha` / `build_time` 4 字段，无 status/pg；客户支持场景专用）| `./main_common.py:848` |
| POST | `/api/reset` | 重置内存中所有实例 / 设计 / 定义 | `./main_pg.py:526` |
| GET | `/api/stats/users` | 列出用户 | `./main_pg.py` |
| GET | `/api/stats/roles` | 列出角色 | `./main_pg.py` |
| GET | `/api/stats/dicts` | 字典项 | `./main_pg.py` |

### 1.5 SPI 数据端点（v26-v29, dispatcher 层, 双端共用）

> **架构**: 路由注册在 `spi/api.py` (dispatcher 层), `main_common.register_spi_routes(app)` 双端调用. 数据源由环境变量 `SPI_FOLDER` 动态决定 (demo/dev/fdep). **默认 SPI_FOLDER = dev** (本地开发/测试推荐, 13 用户 5 部门 + 22 DictProxy + 2 helpers + verify()). 详见 `spi/SPEC.md §8` 和 `skills/RML.md §SPI 能力`.

| 方法 | 路径 | 用途 | SPI_FOLDER |
| --- | --- | --- | --- |
| GET | `/api/spi/verify` | 数据完整性验证 (4 类检查) | dev/demo |
| GET | `/api/spi/status` | SPI 数据概况 | dev/demo |
| GET | `/api/spi/users` | 列出所有用户 (uid, name, post, level, dept_id, roles) | dev/demo |
| GET | `/api/spi/users/{uid}` | 用户完整档案 (13 字段集成视图 SPI_USERS_FULL) | dev/demo |
| GET | `/api/spi/depts` | 列出所有部门 (dept_id, name, size, leader, main_leader) | dev/demo |
| GET | `/api/spi/depts/{dept_id}` | 部门详情 + 成员 (info + members) | dev/demo |

**请求示例**:

```bash
# 启动 main.py (8101, MEM backend, 默认 SPI_FOLDER=dev)
export SPI_FOLDER=dev
python main.py

# 或 main_pg.py (8102, PG backend)
export SPI_FOLDER=dev
python main_pg.py

# 验证数据
curl http://localhost:8101/api/spi/verify
# {"ok": true, "errors": [], "warnings": [], "summary": {...}}

# 查周磊完整档案
curl http://localhost:8101/api/spi/users/u_fe_eng
# {"userId": "u_fe_eng", "name": "周磊", "dept_name": "前端组", ...}

# 查 D02 部门详情
curl http://localhost:8101/api/spi/depts/D02
# {"info": {...}, "members": [...]}
```

**错误码**:

| 状态码 | 含义 | 触发条件 |
| --- | --- | --- |
| 200 | OK | 数据查询成功 (含 verify 失败的情况, 仍可查) |
| 404 Not Found | uid/dept_id 不存在 | `{"detail": "User not found: xxx"}` |
| 404 Not Found | SPI_FOLDER=xxx 无 cli/api | `{"detail": "SPI_FOLDER=xxx 不支持 API (缺少 api 模块)"}` |

**对应 CLI 命令** (`python -m spi.cli`):

```bash
SPI_FOLDER=dev python -m spi.cli verify
SPI_FOLDER=dev python -m spi.cli list-users
SPI_FOLDER=dev python -m spi.cli show-user u_fe_eng
SPI_FOLDER=dev python -m spi.cli list-depts
SPI_FOLDER=dev python -m spi.cli show-dept D02
SPI_FOLDER=demo python -m spi.cli list-users  # 同一命令, 切换数据源
```

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
| `data.parentId` | string\|null | 父实例 id (FIX-T33 §56，主子流程联动) |
| `data.parentStatus` | string\|null | 主子状态 (FIX-T72 §3.1.1，CHILD_DONE/CHILD_REJECT) |
| `data.variables.<node.id>_childInstanceId` | string | callActivity 子实例 id (FIX-T73 §3.1.2) |
| `data.finish_state` | any | **恒为 null**（历史遗留字段，忽略） |
| `data.tasks[]` | array | 全部 task（含已完成 + 活跃），含 `id/taskName/taskState/operator/taskActorIdList/variable` |
| `data.tasks[].taskState` | int | TaskState 枚举（10=DOING / 20=DONE） |
| `data.tasks[].taskActorIdList` | array | 候选执行人列表（来自 JSON `assignee` / `assignmentHandler`） |
| `data.tasks[].variable` | string | JSON 字符串（**需 `JSON.parse`**），含 `submitType/u_*/f_*` 等 |
| `data.tasks[].variable._delegate_of` | object | delegate 历史 (FIX-T69 §69) |
| `data.tasks[].variable._comments` | array | comment 历史 (FIX-T70 §70) |
| `data.tasks[].variable._extra` | object | 额外信息 (FIX-T70 §70) |
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

---

## 5. Phase 2 新增端点 (2026-09-20, FIX-T72-T78)

### 5.1 processTask/delegateHistory
返回 task 的委派历史 (按 delegate 顺序)

```bash
POST /wf/processTask/delegateHistory
{"processTaskId": "91981833944067"}

→ {
  "code": 0,
  "data": {
    "taskId": "91981833944067",
    "delegateHistory": [
      {"from": "leader", "to": "boss2", "at": "2026-09-19T21:53:29.779423"}
    ],
    "delegateAt": "2026-09-19T21:53:29.779423",
    "actorIds": ["leader", "boss1", "boss2"]
  }
}
```

### 5.2 processTask/transferAndAdd
transfer + addCandidate 合并 (保留原 actor, 新增 targetUser)

```bash
POST /wf/processTask/transferAndAdd
{"processTaskId": "...", "operator": "leader", "targetUserId": "leader2"}

→ {
  "code": 0,
  "data": {
    "taskId": "...",
    "oldActors": ["leader", "leader2"],
    "newActors": ["leader", "leader2"]
  }
}
```

业务场景: A 转给 B 后, A 仍需看流程后续动态 (审计场景)。

### 5.3 processTask/withForm
task 级表单绑定 (运行时动态, 与节点级 field.PERMISSION_* 区别)

```bash
POST /wf/processTask/withForm
{
  "processTaskId": "...",
  "operator": "leader",
  "formKey": "leave-form-v2",
  "fields": {
    "f_leaveType": {"type": "select", "required": true, "perm": 2},
    "f_secret": {"type": "string", "required": false, "perm": 3}
  }
}

→ {"code": 0, "data": {"taskId": "...", "formKey": "leave-form-v2", "fieldCount": 2}}
```

字段权限码: 1=只读 / 2=编辑 / 3=隐藏 (与节点级 PERMISSION_* 一致).

### 5.4 processInstance/suspend / resume
实例挂起/恢复 (FIX-T70)

```bash
POST /wf/processInstance/suspend {"id": "91975865463809"}
→ {"code": 0, "data": {"id": "...", "state": 50}}

POST /wf/processInstance/resume {"id": "91975865463809"}
→ {"code": 0, "data": {"id": "...", "state": 10}}
```

suspended 实例不能 execute task (FIX-T56, 99999999 抛错).

---

## 6. 错误码表 (BDD #1210 FIX-T88 §4.3.4)

所有 action 响应统一格式 `{code, msg, data}`:
- `code = 0`: 成功
- `code = 99999999`: 失败 (msg 含错误类型 + 详情)

| 触发场景 | msg 前缀 | 触发条件 | 解决方案 |
|---------|---------|----------|----------|
| 必填参数缺失 | `[ValueError] xxx 缺失或非法` | body 缺关键字段 | 补全必填字段 (查 `docs/actions.md`) |
| 未知 action | `未知 action: xxx` | action 名错或未注册 | 查 §1-§5 端点清单 |
| 流程节点 actorIds 空 | `[ValueError] 节点[xxx]actorIds 为空` | 流程设计缺 assignee | 节点 properties 加 assignee / assignmentHandler |
| handler 未注册 | `[ValueError] handler 'xxx' 未注册` | SPI 没装该 role | 注册 handler 或修改 DEMO_ROLE_TO_USERS.json |
| SPI 角色匹配空 | `[ValueError] 节点[xxx] handler 'xxx' SPI 角色匹配为空` | role_code 无映射 | 补充 SPI 映射或修正 node.id |
| postInterceptors 未注册 | `[ValueError] postInterceptors 声明的拦截器未注册: xxx` | 流程顶层 interceptor 未注册 | 在 main_common.py 注册 |
| 流程未部署 | `[ValueError] define not found: xxx` | 用错 processDefineId | 重 deploy 取新 id |
| operator 无权限 | `[ValueError] operator xxx not allowed` | 操作人不在 actorIds | 用 addCandidate 加权限 |
| PENDING 实例 | `[ValueError] 实例 state=50 不可执行任务` | 挂起实例直接 execute | 先 resume |
| decisionHandler 未注册 | `[ValueError] decisionHandler xxx 调用失败` | handler 名错或未注册 | 在 build_decision_handlers 注册 |
| verify 校验失败 | `[ValueError] 流程 verify 失败 (N 个错误)` | 流程设计违规 | 修 verify 报错字段 |

### 6.1 错误排查流程

```bash
# 1. 查响应 msg 字段
RESP=$(curl -X POST /wf/xxx -d '...')
echo "$RESP" | jq '.code, .msg'

# 2. 查已知问题
grep "msg 包含的关键词" docs/known-issues.md
# 例: "postInterceptors" → §36
# 例: "节点[] actorIds 为空" → §16
# 例: "operator xxx not allowed" → §40/§69

# 3. 启用 trace
curl http://jeeFlow:8101/api/admin/trace?limit=10
# 找到出错的 span, 看 attributes 字段

# 4. 启用 Prometheus
curl http://jeeFlow:8101/metrics | grep wf_task_completed
# 看任务执行统计
```

### 6.2 默认错误码补充

引擎实现中可能抛出的错误码 (不限于 0/99999999):

| 场景 | 引擎行为 | 说明 |
|------|----------|------|
| custom node clazz 缺失 | 99999999 `[ValueError] custom 节点[x]缺少 properties.clazz` | §16 FIX-T38 |
| custom handler 未注册 | 99999999 `[ValueError] custom 节点[x] handler='xxx' 未注册 (已注册: [...])` | §16 |
| decisionHandler 返回未知节点 | 99999999 `[ValueError] decisionHandler xxx 返回未知节点: xxx` | §46 FIX-T46 |
| callActivity 子流程未部署 | 99999999 `[ValueError] callActivity 节点[x]子流程 'xxx' 未部署` | §3.1.2 FIX-T73 |
