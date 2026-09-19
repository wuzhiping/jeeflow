# jeeFlow 后端集成指南 (BDD #1209 FIX-T87 §4.3.3)

> **生成时间**: 2026-09-20
> **版本**: v1.9.0+ (Phase 1+2+3 完成)
> **依据**: `roadmap.md §4.3.3` - 后端集成指南 (私用定位, 嵌入已有业务系统)

---

## 1. 集成方式

jeeFlow 是**纯后端引擎**, 通过 HTTP API 集成. 不输出 SDK / 前端 / 客户端代码.

### 1.1 嵌入模式

| 模式 | 适用场景 | 端点 |
|------|----------|------|
| **同进程嵌入** | 小规模 (单进程足够) | 直接 `import vendor.jeeflow` |
| **HTTP 调用** (推荐) | 生产 (多节点 / PG 后端) | `POST /wf/{action}` |
| **OpenAPI 客户端** | 自动生成 SDK (业务方工具) | `GET /openapi.json` + openapi-generator |

### 1.2 部署形态

| 形态 | 启动命令 | 用途 |
|------|----------|------|
| **MEM** | `python main.py` | dev/test, 进程内 dict |
| **PG** | `JEEFLOW_PG_DSN=... python main_pg.py` | 生产, 持久化 |
| **多节点** | 多个 main_pg 进程 + lb | HA |

## 2. 部署流程定义 (3 步)

```bash
# 步骤 1: 保存设计 (含 content JSON)
DESIGN_ID=$(curl -s -X POST http://jeeFlow:8101/wf/processDesign/save \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg c "$(cat flows/01-simple.json)" '{name:"simple",displayName:"简单审批",content:$c}')" \
  | jq -r '.data.id')

# 步骤 2: 部署 (生成 wf_process_define)
DEF_ID=$(curl -s -X POST http://jeeFlow:8101/wf/processDesign/deploy \
  -H "Content-Type: application/json" -d "{\"id\": $DESIGN_ID}" \
  | jq -r '.data.processDefineId')

# 步骤 3: 启动实例
INST_ID=$(curl -s -X POST http://jeeFlow:8101/wf/processInstance/startAndExecute \
  -H "Content-Type: application/json" \
  -d "{\"processDefineId\": $DEF_ID, \"operator\": \"user1\", \"variables\": {\"f_amount\": 5000}}" \
  | jq -r '.data.processInstanceId')
```

注意:
- `processDesign/save` 是 UPSERT (按 name 唯一), 返回的是本轮 `id`
- `processDesign/deploy` 按 name `version+1` 插新行 (PG) / 覆盖 (MEM)
- **必须用本轮 deploy 返回的 `processDefineId`, 不要硬编码历史 id**

## 3. 调用 action (核心 API)

所有业务通过 `POST /wf/{action:path}` + JSON body 调用:

### 3.1 请求结构

```json
{
  "processDefineId": 12345,
  "operator": "user1",
  "assignees": {
    "apply": "user1",
    "task1": "leader"
  },
  "variables": {
    "submitType": 1,
    "f_leaveType": "事假",
    "f_days": 3,
    "u_userId": "user1",
    "u_realName": "用户1"
  },
  "f_ccActors": "observer1,observer2",
  "parentId": "91970000000001",
  "comment": "已审批",
  "targetUserId": "boss"
}
```

### 3.2 响应结构

```json
{
  "code": 0,
  "msg": "成功",
  "data": {
    "processInstanceId": "91975865463809",
    "processTaskId": "91975865472463",
    "state": 10,
    "tasks": [...]
  }
}
```

- `code = 0` 成功, `code = 99999999` 失败
- `data` 字段由 action 决定 (id / 列表 / 详情)

### 3.3 48 个核心 action

| 分类 | 数量 | 常用 |
|------|------|------|
| 流程设计 (processDesign) | 7 | save / deploy / update / page |
| 流程定义 (processDefine) | 6 | page / detail / getLastByName |
| 流程实例 (processInstance) | 13 | startAndExecute / execute / detail / suspend / resume |
| 流程任务 (processTask) | 17 | todoList / execute / delegate / transferAndAdd |
| 委派 (processSurrogate) | 3 | save / update / page |
| 统计 (stats) | 3 | overview / trend / group |

详见 `docs/api.md` + `docs/openapi.json` (FIX-T85 自动生成).

## 4. 端到端调用示例 (请假审批)

```bash
# 步骤 1: 用户发起请假 (3 天事假)
INST_ID=$(curl -s -X POST /wf/processInstance/startAndExecute \
  -H "Content-Type: application/json" \
  -d '{
    "processDefineId": 12345,
    "operator": "user1",
    "variables": {
      "f_leaveType": "事假",
      "f_days": 3,
      "f_reason": "家中有事"
    }
  }' | jq -r '.data.processInstanceId')

# 步骤 2: 领导查待办
TASK=$(curl -s -X POST /wf/processTask/todoList \
  -H "Content-Type: application/json" \
  -d '{"operator": "leader"}' | jq -r '.data.rows[0].id')

# 步骤 3: 领导审批
curl -s -X POST /wf/processTask/execute \
  -H "Content-Type: application/json" \
  -d "{
    \"processTaskId\": \"$TASK\",
    \"operator\": \"leader\",
    \"submitType\": 1,
    \"comment\": \"同意\"
  }"

# 步骤 4: 经理继续审批
TASK=$(curl -s -X POST /wf/processTask/todoList \
  -H "Content-Type: application/json" \
  -d '{"operator": "manager"}' | jq -r '.data.rows[0].id')

curl -s -X POST /wf/processTask/execute \
  -H "Content-Type: application/json" \
  -d "{
    \"processTaskId\": \"$TASK\",
    \"operator\": \"manager\",
    \"submitType\": 1
  }"

# 步骤 5: 用户查流程详情
curl -s -X POST /wf/processInstance/detail \
  -H "Content-Type: application/json" \
  -d "{\"id\": \"$INST_ID\"}"
```

## 5. 集成 SPI (用户/角色/部门)

`spi/` 目录是用户/角色/部门数据源, 业务方需要适配自己的业务系统.

### 5.1 用户查找

```python
# spi/__init__.py:SimpleUserProvider
class SimpleUserProvider:
    async def get_user(self, user_id: str) -> UserInfo:
        # 业务方实现: 从业务系统查 user 信息
        # 默认返回 mock 数据
        return UserInfo(userId=user_id, realName="张三", deptId="D01", deptName="研发部", ...)
```

### 5.2 角色映射

```json
// spi/demo/DEMO_ROLE_TO_USERS.json
{
  "leader": ["user1", "user2"],
  "manager": ["user3", "user4"],
  "hr": ["user5"],
  "engineer": ["user6", "user7"],
  "manager_approve": ["user8"]
}
```

handler `TaskRoleAssigneeHandler` 用 `node.id` 作为 role_code 查这张表.

### 5.3 自定义 SPI 适配

```python
# 业务方实现: 替换 SimpleUserProvider
class MyUserProvider:
    async def get_user(self, user_id: str) -> UserInfo:
        # 从你的业务系统 (HR / CRM) 查用户
        return await call_internal_api("/users/" + user_id)

# main.py:
user_prov = MyUserProvider()  # 替换 SimpleUserProvider
```

## 6. 自定义 handler (§6.3)

### 6.1 参与者解析

```python
# main_common.py:build_ic_registry (FIX-T38)
# 已注册 handler:
# - TaskRoleAssigneeHandler: 用 node.id 作为 role_code
# - FormFieldAssigneeHandler: 用字段值作为 actor
# - DeptLeaderAssigneeHandler: 用部门负责人

# 业务方自定义:
class MyCustomAssigneeHandler(IAssignmentHandler):
    async def assign(self, node, instance, operator: str) -> list[str]:
        # 你的逻辑: 从 instance.variables 读参数, 查业务系统
        amount = instance.variables.get("f_amount", 0)
        if amount > 100000:
            return ["ceo"]
        return ["manager"]

# 注册到 HandlerRegistry
_registry.register_assignment("my.handler", MyCustomAssigneeHandler())
```

### 6.2 决策路由

```python
# main_common.py:build_decision_handlers (FIX-T46)
class MyDecisionHandler(IDecisionHandler):
    async def decide(self, node, instance, vars: dict) -> str:
        # 返回目标节点 id
        if vars.get("amount", 0) > 5000:
            return "high_amount_task"
        return "low_amount_task"

_registry.register_decision("my.decision", MyDecisionHandler())

# 节点 properties:
{
  "id": "d1",
  "type": "snaker:decision",
  "properties": {"decisionHandler": "my.decision"}
}
```

### 6.3 Custom 节点 (§16 FIX-T38)

```python
# main_common.py:build_custom_handlers
class MyCustomHandler:
    async def __call__(self, node, instance, vars_, args):
        # args 是字符串 (从节点 properties.args 读)
        # 返回值写回 vars_[properties.val]
        return {"result": "ok", "ts": datetime.now().isoformat()}

# 注册
custom_handlers["my.custom"] = MyCustomHandler()

# 节点:
{
  "id": "c1",
  "type": "snaker:custom",
  "properties": {
    "clazz": "my.custom",
    "args": "{\"param\": 1}",
    "val": "customResult"
  }
}
```

## 7. 监控告警 (§4.1)

### 7.1 健康检查

```bash
# 简版
curl http://jeeFlow:8101/healthz
# → {"status":"UP","backend":"python","pg":"ok"}

# 详细 (FIX-T79)
curl http://jeeFlow:8101/api/admin/health
# → {status, backend, version, checks: {pg: {size,idle_size}, repo: ok, engine_cache: {size, max}, process: {active_instances}}}
```

### 7.2 Prometheus 抓取

```yaml
# prometheus.yml
scrape_configs:
  - job_name: jeeflow
    scrape_interval: 15s
    static_configs:
      - targets: ['jeeFlow:8101']
```

```bash
curl http://jeeFlow:8101/metrics
# → text/plain; version=0.0.4
# wf_instance_state_total{state="DOING"} 3
# wf_active_instances 3
# wf_task_duration_seconds_bucket{taskName="task1",le="10.0"} 100
# wf_task_completed_total{taskName="apply"} 1
```

### 7.3 告警规则示例

```yaml
# /wf_instance_state_total{state="DOING"} > 1000 持续 30min → 拥堵告警
# wf_active_instances 突然下降 → 服务异常告警
# wf_task_duration_seconds 95 分位数 > 24h → 流程卡点告警
```

### 7.4 链路追踪 (§4.1.4)

```bash
# 最近 200 个 span
curl http://jeeFlow:8101/api/admin/trace?limit=200
# → {spans: [{span_id, trace_id, name, duration_ms, attributes}], total}

# 按 trace_id 查完整链路
curl http://jeeFlow:8101/api/admin/trace/spans/abc123
# → {trace_id, spans: [...]}
```

## 8. 多节点 HA (§4.4)

### 8.1 部署架构

```
┌────────────┐  ┌────────────┐  ┌────────────┐
│ main_pg #1 │  │ main_pg #2 │  │ main_pg #3 │
│ (8102)     │  │ (8102)     │  │ (8102)     │
└─────┬──────┘  └─────┬──────┘  └─────┬──────┘
      │               │               │
      └───────────────┴───────────────┘
                      │
              ┌───────▼────────┐
              │ asyncpg pool    │
              │ (10 conn/node)  │
              └───────┬────────┘
                      │
              ┌───────▼────────┐
              │ PostgreSQL 17.4 │
              │ (10.17.1.26:6432)│
              └──────────────────┘
```

### 8.2 部署命令

```bash
# 每个节点
export JEEFLOW_PG_DSN="postgresql://user:pass@pg-host:6432/db"
nohup python main_pg.py > /tmp/jeeflow-$HOSTNAME.log 2>&1 &
```

### 8.3 lb 配置 (nginx)

```nginx
upstream jeeflow {
    least_conn;
    server jeeflow-1.internal:8102;
    server jeeflow-2.internal:8102;
    server jeeflow-3.internal:8102;
    keepalive 32;
}

server {
    listen 80;
    location / {
        proxy_pass http://jeeflow;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_read_timeout 300s;
    }
}
```

### 8.4 并发安全 (§4.4.2)

- 同一 instance 同一时间只允许 1 个 task.execute 推进 (悲观锁)
- 多 instance 并发安全 (FIX-T35 §27 + FIX-T87 §4.4.2 乐观锁)
- 推荐主流程跑在同一节点, task.execute 自动转发到对应 instance owner

## 9. 测试集成

### 9.1 BDD 基线

```bash
# 项目自带 1119 BDD 场景, 每次集成后跑回归
bash bdd/bdd-1001-1060-p0-regression.sh   # 17 PASS
bash bdd/bdd-1065-1100-p1-regression.sh   # 26 PASS
bash bdd/bdd-1101-1110-phase2.sh          # 9 PASS

# 双 DB (PG 端)
.venv/bin/python /tmp/test_pg_direct.py      # 14 PASS
.venv/bin/python /tmp/test_phase2_pg.py      # 10 PASS
```

### 9.2 自定义测试

```python
# 用 vendor 直接调用 (绕开 HTTP)
import sys
sys.path.insert(0, "vendor")
from jeeflow import JeeflowFacade
from jeeflow.engine import EngineImpl

repo = MemoryRepository()  # 或 JdbcRepository(adapter)
engine = EngineImpl(repo, SimpleUserProvider(), SimpleExprEvaluator())
facade = JeeflowFacade(engine, repo, ...)

# 调 startAndExecute
result = await facade.flow("processInstance/startAndExecute", {
    "processDefineId": 12345, "operator": "user1"
})
```

## 10. 常见集成问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `unknown action` | action 名错或未注册 | 查 `docs/actions.md` 速查表 |
| `code 99999999` ValueError | 参数缺失 | 查对应 action 必填入参 |
| `processInstance/start` 404 | 不在清单 | 用 `startAndExecute` |
| `handler not registered` | SPI 角色未映射 | 改 `DEMO_ROLE_TO_USERS.json` 或实现自定义 |
| 流程卡死 state=10 | actor 解析不到 | 查 `processDesign/detail` 看节点 assignment |
| `instance.state=50 PENDING` | 流程挂起 | 调 `processInstance/resume` |
| 性能: 100 并发慢 | 缺 connection pool | 调大 `max_size` (PG 端 asyncpg) |
| API 兼容性破坏 | 改了字段名 | 不允许改字段; 新增字段 OK; 查 BDD 基线 |

## 11. 联系

私用项目, 无对外支持. 内部问题通过:
- `docs/known-issues.md` (106 章节, 包含 0 已知限制 + 历史修复)
- `bdd/README.md` (1119 场景基线)
- `roadmap.md` (私用定位 + 三阶段路线图)
- `vendor/README.md` (引擎改进报告 78 FIX)
