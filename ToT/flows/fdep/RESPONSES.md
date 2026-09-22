# FDEP · 节点响应详情（RESPONSES）

> **目的**：每个节点的 API 响应 + 业务输出详情
> **视角**：双视角 —— **API 视角**（AI agent 调用）+ **业务视角**（人类审计）
> **依据**：FDEP v0.6.1（部署在 https://abc.feg.cn/jeeflow/）
> **对应流程文件**：`../fdep.json`（9 节点 / 10 边）

---

## 0. Decision Mem 协议（v1.0 lite）

**发现**：引擎 `facade.py:713` 把 `processTask/execute` body 中除 `processTaskId` 和 `operator` 外的**所有字段**都透传到 `wf_process_task.variable`。

**协议字段**（每节点 execute 时附带）：

| 字段 | 类型 | 必填 | 用途 | 落点 |
|------|------|------|------|------|
| `decision_reason` | str | ✅ | "为什么做这个决策" | `wf_process_task.variable.decision_reason` |
| `decision_memo` | dict | ❌ | 节点特定的决策细节（自由 dict） | `wf_process_task.variable.decision_memo` |
| `context` | dict | ❌ | 上下文（天气/团队/外部信息） | `wf_process_task.variable.context` |

**v1.2 lite+**（2026-09-22 加 `job_card_url` 字段，用于审计 executor 实际用的卡）：

| 字段 | 类型 | 必填 | 用途 | 落点 |
|------|------|------|------|------|
| `job_card_url` | str | ❌ | executor 实际用的 Job Card（本地路径） | `wf_process_task.variable.job_card_url` |
| `next_handoff.job_card_url` | str | ❌ | 给下一 executor 的卡（链路接力） | `wf_process_task.variable.next_handoff.job_card_url` |

**审计链验证**：对任意 task T：

```
T.job_card_url                        == job_card_<T>.md 真实存在
T.next_handoff.job_card_url           == job_card_<next(T)>.md 真实存在
next(T).job_card_url                  == T.next_handoff.job_card_url
```

**示例 execute body**：

```json
{
  "processTaskId": "<id>",
  "operator": "u_fdp_pm",
  "submitType": 1,
  "decision_reason": "立项：业务诉求清晰，无重复",
  "decision_memo": {
    "businessNo": "REQ-2026-001",
    "priority": "high",
    "estimated_days": 5
  },
  "context": {"weather": "sunny", "team": "fdep-core"},
  "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_intake.md",
  "next_handoff": {
    "next_node": "stage_pm",
    "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_pm.md",
    "input_files": ["..."]
  }
}
```

**审计回查**：

```bash
# 查任意 instance 的所有节点决策（含 job_card_url 审计）
curl -s -X POST $TARGET/wf/processInstance/detail \
    -H "Content-Type: application/json" \
    -d '{"id":"<processInstanceId>"}' | python3 -c "
import sys, json
d = json.load(sys.stdin)['data']
for t in d['tasks']:
    v = json.loads(t['variable'])
    jcu = v.get('job_card_url', 'MISSING')
    nh = v.get('next_handoff') or {}
    njcu = nh.get('job_card_url', 'terminal')
    print(f'{t[\"taskName\"]:18s} used={jcu}  next={njcu}')"
```

---

## 1. start（snaker:start）

### 1.1 API 视角

| 项 | 值 |
|----|-----|
| 节点类型 | `snaker:start`（流程起点） |
| 直接 API | **无**（start 节点不能直接 execute，由引擎在创建 instance 时自动激活） |
| 触发 API | `POST /wf/processDefine/startAndExecute` 或 `POST /wf/processInstance/start` |
| 触发 body | `{"processDefineId":"1790042780958000","operator":"u_fdp_pm"}` |
| 触发后行为 | 引擎自动激活 `stage_intake`（next node，无决策） |

### 1.2 Decision 详情

| 项 | 值 |
|----|-----|
| 决策点 | **无**（start 是入口节点，无 routing 决策） |
| 自动路由 | **start → stage_intake**（唯一下一节点） |
| 引擎判断 | 是否存在下一节点；如有则激活 task；如无则引擎报错 |
| 失败模式 | JSON 中无 edges → 引擎不会激活 stage_intake（不会启动任何 task） |

### 1.3 Trace 信息（用于 issue 排查）

**请求级 trace**（每个 API 调用产生 1 个 trace_id，含多 span）：

```bash
# 获取最近 200 个 span（引擎启动后所有请求）
curl -s https://abc.feg.cn/jeeflow/api/admin/trace | python3 -c "
import sys, json
spans = json.load(sys.stdin)['spans']
# 过滤 startAndExecute 相关
for s in spans:
    if 'start' in s['name'].lower():
        print(f'  {s[\"name\"]:50s} duration={s[\"duration_ms\"]}ms status={s[\"status\"]} trace_id={s[\"trace_id\"]}')
"
```

**单个 trace 的 span 链**：

```bash
curl -s https://abc.feg.cn/jeeflow/api/admin/trace/spans/<trace_id> | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'  trace_id: {d[\"trace_id\"]}')
print(f'  span count: {len(d[\"spans\"])}')
for s in d['spans']:
    parent = s.get('parent_span_id') or '-'
    print(f'    {s[\"span_id\"]:18s} parent={parent:18s} {s[\"name\"]} ({s[\"duration_ms\"]}ms)')
"
```

**startAndExecute 实际 trace 示例**（从 jeeflow 拉的）：

```
trace_id  : 2ad8c4d403cb4670b563b16bd27cb9ad  (示例)
spans     : [
  facade.processDefine/startAndExecute  (5ms, status=ok)
    ├─ engine.start (2ms)
    │   ├─ resolve_actors (1ms)
    │   └─ activate_first_task (1ms)
    └─ facade return (0ms)
]
```

### 1.4 业务视角（人类审计）

| 项 | 值 |
|----|-----|
| **触发者** | **任意来源**（人类 / AI Agent / 外部用户，无角色限制） |
| **触发位置** | 客户服务器入口 https://abc.feg.cn/jeeflow/，或本地 `127.0.0.1:8101/8102` |
| **审计字段** | `wf_process_instance.operator`（发起人 uid）+ `wf_process_instance.create_time` + `wf_process_instance.businessNo`（外部业务单号，可选） |
| **不做** | 不写代码 / 不修改任何文件 / 不裁决内容 / 不限提交者角色 |
| **FDEP 永久约束** | `start ≠ R3`（PM 是后续接收窗口，不是入口） |

### 1.5 触发后引擎响应示例

```json
{
  "code": 0,
  "msg": "成功",
  "data": {
    "processInstanceId": "92203808007179",
    "taskName": "stage_intake"
  }
}
```

### 1.6 异常 / 错误

| 情况 | 响应 | 处置 |
|------|------|------|
| 流程未部署 | `{"code": 99999999, "msg": "流程定义不存在: fdep"}` | 先调用 `POST /wf/processDefine/deploy` |
| operator 不在 SPI | 引擎注入 `u_userId/u_realName/u_deptId` 占位变量 | 建议 operator 用真实 SPI uid |
| 客户服务器不可达 | curl connection refused / timeout | 走 `customer-checks/YYYY-MM-DD_ready.md` 8 项检查 |
| **start 后无下一节点** | 引擎不报错但卡死：state=DONE、activeTaskList=空 | 检查 FDEP.json 的 edges；正常应至少有 1 条 from=start |

### 1.7 Audit Log 查 Bug（核心：3 处数据源）

**数据源 1：`wf_process_instance` 表（业务层）**

```sql
SELECT id, process_define_id, state, operator, create_time, business_no
FROM wf_process_instance
WHERE id = '<processInstanceId>';
```

| 字段 | 含义 | 异常排查 |
|------|------|----------|
| `state` | 实例状态（10=DOING / 20=DONE / 45=REJECT） | state=10 但没 task → start 后无下一节点 |
| `operator` | 发起人 | 与 SPI users 对照确认 |
| `create_time` | 创建时间 | 看时区/延迟 |

**数据源 2：`wf_process_task` 表（任务层）**

```sql
SELECT id, task_name, task_state, operator, create_time, finish_time, variable
FROM wf_process_task
WHERE process_instance_id = '<processInstanceId>'
ORDER BY create_time;
```

| 字段 | 含义 | 异常排查 |
|------|------|----------|
| `task_state` | 任务状态（10=DOING / 20=DONE） | start 后应有 stage_intake=DONE + stage_pm=DOING |
| `operator` | task 执行人 | 与 stage_intake assignee 比对 |
| `task_actor_id_list` | 候选人列表 | 确认 R3 + u_fdp_pm 都在 |

**数据源 3：`/api/admin/trace`（请求层）**

```bash
curl -s "https://abc.feg.cn/jeeflow/api/admin/trace/spans/<trace_id>"
```

返回该请求的完整 span 链，每个 span 含：
- `name`：端点名（如 `facade.processDefine/startAndExecute`）
- `status`：ok / error
- `duration_ms`：耗时
- `attributes`：args_keys / code / 错误详情

### 1.8 审计检查清单（人类）

- [ ] `wf_process_instance.operator` 是否为期望的发起人？
- [ ] `wf_process_instance.create_time` 是否在预期时间窗口？
- [ ] `wf_process_task` 中有 `stage_intake`（task_state=DONE）+ `stage_pm`（task_state=DOING）？
- [ ] `/wf/processInstance/highLight` 的 `historyNodeNames` 包含 `stage_intake`？
- [ ] trace span 链完整无 error？

### 1.9 已知 Bug & 限制

| Bug | 影响 | 处置 |
|-----|------|------|
| `u_deptName="默认部"`（P1） | 引擎 dept 解析走 fallback，不阻塞 | v0.7+ 修 |
| 引擎无 `start` 节点的"单独查看"接口 | 审计时需通过 instance / task 间接看 | 已知 |
| trace 只在内存中，重启丢失 | 重启后无法查历史 trace | `/api/admin/trace/purge` 已知有 trace persistence（待启用） |

---

## 2. stage_intake（snaker:task）

### 2.1 API 视角

| 项 | 值 |
|----|-----|
| 节点类型 | `snaker:task` |
| 触发方式 | 由 `start` 自动激活；或 `processTask/execute` 推进 |
| **执行 API** | `POST /wf/processTask/execute` |
| **执行 body（lite v1.0）** | `{"processTaskId":"<id>","operator":"u_fdp_pm","submitType":1,"decision_reason":"...","decision_memo":{...},"context":{...}}` |
| **替代**：手动推进 | `POST /wf/processInstance/advance`（批量推进） |

**实测 task 数据（reset #2 后的 instance 92203808007179）**：

```json
{
  "id": "92203808009228",
  "taskName": "stage_intake",
  "displayName": "0. 接收/登记 (u_fdp_pm 直接...)",
  "formKey": "intake-template",
  "taskActorIdList": ["u_fdp_pm"],
  "taskState": 20,
  "operator": "u_fdp_pm",
  "createTime": "2026-09-22T10:06:21.259624",
  "finishTime": "2026-09-22T10:06:21.266825",
  "variable": {
    "u_userId": "u_fdp_pm",
    "u_realName": "占位·待分配",
    "u_deptId": "DFDEP",
    "u_deptName": "默认部",
    "u_postId": "P5",
    "u_postName": "FDEP 流程占位",
    "autoGenTitle": "占位·待分配的jeeFlow 协作主流程...-2026-09-22 10:06",
    "submitType": 0
  }
}
```

### 2.2 Decision Mem 详情（v1.0 lite）

**本节点决策 mem 模板**：

```json
{
  "decision_reason": "立项：<业务诉求清晰，无重复>",
  "decision_memo": {
    "businessNo": "<外部业务单号>",
    "priority": "high | normal | low",
    "estimated_days": <N>
  },
  "context": {
    "requester": "<uid>",
    "submitted_via": "API | UI | other"
  }
}
```

**实际透传示例**（实测 instance 92207715661852）：

```json
{
  "decision_reason": "演示测试：验证业务变量能否存到 task.variable",
  "decision_memo": {
    "rml_drafted_by": "AI",
    "priority": "high",
    "target_release": "v0.7"
  },
  "context": {
    "weather": "sunny",
    "team": "fdep-core"
  }
}
```

### 2.3 Decision 详情（提交类型）

**PM 决策点**（人类审计的核心环节）：

| 决策项 | 选项 | 引擎行为 |
|--------|------|----------|
| **立项 / 驳回** | submitType=1 (AGREE) → 走 `e_decision_approve` → stage_pm | ✅ 正常 |
| | submitType=2 (REJECT) → 走 `e_decision_reject` → end_rejected | ✅ 正常 |
| | submitType=0/3/4/5/6/20 → 走 `e_decision_default`（兜底）→ stage_pm | ⚠️ 等同于 AGREE，需 PM 注意 |

**决策依据**（决策树示例）：

```
请求在系统范围内？
├─ 否 → submitType=2 → 驳回，写理由
└─ 是 → 是否重复？
    ├─ 是 → submitType=2 → 驳回，引用重复 ID
    └─ 否 → 是否紧急？
        ├─ 是 → submitType=1 → 立项，标记优先级高
        └─ 否 → submitType=1 → 立项，正常优先级
```

**未来扩展（Q8）**：决策可读 `wf_process_instance` 历史 mems + flows log（如 `wf_process_surrogate` / `wf_process_cc_instance`）做更复杂判断。

### 2.3 Trace 信息

**execute 阶段典型 trace**：

```
trace_id : <request-id>
spans    : [
  facade.processTask/execute (3ms, status=ok)
    ├─ engine.execute_task (2ms)
    │   ├─ resolve_actors (1ms)
    │   ├─ capture_vars (0.5ms)
    │   └─ next_node_dispatch (1ms)  ← 这里路由到 stage_pm
    └─ facade return (0ms)
]
```

### 2.4 业务视角（人类审计，lite 版本）

| 项 | 值 |
|----|-----|
| **执行人** | u_fdp_pm（R3 PM 角色，占位用户） |
| **决策时机** | 收到 start 触发的 stage_intake DOING 通知后 |
| **决策产物** | **submitType (1=立项 / 2=驳回)** + 透传上游变量（mems way） |
| **form** | v0.6.2 暂为空 formKey `intake-template`（lite：直接透传 `wf_process_task.variable`） |

**Lite 数据流**（v0.6.x 简化版）：

```
start.variable → stage_intake.variable → decision_intake.expr
                  (透传, mems way)
```

**未来扩展**（v0.7+ 改进）：
- 加 form template `intake-template`（业务字段：业务单号 / 优先级 / 预期完成时间）
- 决策树依据 `wf_process_surrogate` 历史 + formData 综合判断
- 业务 mems 写到 `ToT/pm/intake/<date>/<id>.md` 作为留档（v0.7+）



### 2.5 异常 / 错误

| 情况 | 响应 | 处置 |
|------|------|------|
| operator 不在 taskActorIdList | `{"code": 99999999, "msg": "操作人无权处理此任务"}` | 检查 SPI roles |
| task 已是 DONE | `{"code": 99999999, "msg": "task state=20 不可执行"}` | 跳过 |
| 决策节点缺 default edge | 触发 FIX-T112 兜底走第一边 | 加 `e_decision_default` |
| formKey 模板不存在 | UI 渲染失败但 API 仍可调用 | 配置 form template |

### 2.6 Audit Log 查 Bug（3 处数据源）

**数据源 1：`wf_process_task` 表**

```sql
SELECT id, task_name, task_state, operator, finish_time, variable, form_key
FROM wf_process_task
WHERE process_instance_id = '<id>' AND task_name = 'stage_intake';
```

**数据源 2：task 变量解析**

```bash
# variable 字段是 JSON 字符串，需解析
curl -s -X POST "$TARGET/wf/processInstance/detail" \
    -H "Content-Type: application/json" \
    -d '{"id":"<processInstanceId>"}' | python3 -c "
import sys, json
d = json.load(sys.stdin)['data']
for t in d['tasks']:
    if t['taskName'] == 'stage_intake':
        v = json.loads(t['variable'])
        print(json.dumps(v, ensure_ascii=False, indent=2))
        break
"
```

**数据源 3：`/wf/processTask/doneList` 查历史**

```bash
curl -s -X POST "$TARGET/wf/processTask/doneList" \
    -H "Content-Type: application/json" \
    -d '{"operator":"u_fdp_pm","limit":50}' | python3 -c "
import sys, json
d = json.load(sys.stdin)['data']
print(f'  total: {d.get(\"total\", 0)}')
for r in d['rows']:
    if r['taskName'] == 'stage_intake':
        print(f'  instance={r[\"processInstanceId\"]} finishTime={r.get(\"finishTime\")}')
"
```

### 2.7 审计检查清单

- [ ] `task_actor_id_list` 含 `u_fdp_pm`（或当前 assignee）？
- [ ] `submitType` 是否符合决策预期（1=立项 / 2=驳回）？
- [ ] `finish_time - create_time` 在合理时长（业务约定）？
- [ ] 下一个 task `stage_pm` 是否被激活（DOING）？
- [ ] 业务 mems（理由）是否记录在 formKey 或变量？

### 2.8 已知 Bug & 限制

| Bug | 影响 | 处置 |
|-----|------|------|
| `isFirstTaskNode: false`（实测） | stage_intake 实际是首 task，但引擎标 false | 不影响流程（仅 info 字段） |
| formKey `intake-template` 无模板 | UI 渲染空表单，但 API 正常 | v0.7+ 配 form 模板 |
| 决策仅靠 submitType，无业务字段 | lite 版本够用，业务字段下版本加 | v0.7+ 用 formData |

---

## 3. decision_intake（snaker:decision）

### 3.1 API 视角

| 项 | 值 |
|----|-----|
| 节点类型 | `snaker:decision`（决策路由，无 task / 无 operator） |
| 直接 API | **无**（decision 节点不能 execute，由引擎在 stage_intake 完成后自动评估） |
| 触发 | stage_intake execute 后，引擎自动激活 decision_intake，**瞬时评估出边** |
| 评估依据 | 当前 task 的 `variable.submitType` |
| 评估时间 | < 1ms |

### 3.2 Decision 详情（核心）

**3 条出边的 expr + 路由**（从 FDEP.json 实测）：

| 出边 ID | expr | 匹配 submitType | 路由目标 |
|---------|------|-----------------|----------|
| `e_decision_approve` | `submitType==1` | AGREE | → `stage_pm` |
| `e_decision_reject` | `submitType==2` | REJECT | → `end_rejected` |
| `e_decision_default` | `expr=""`（空） | 其他（含 0/3/4/5/6/20） | → `stage_pm`（兜底） |

**引擎评估顺序**：

```
1. 遍历出边（按 edges 数组顺序）
2. 评估每条 expr（基于当前 task 的 variable）
3. 第一条 expr 评估为 true 的边 → 路由到 target
4. 都没匹配 → FIX-T112 兜底走第一条出边
5. ⚠️ decision_default edge 存在则不会触发 FIX-T112 兜底（因为空 expr 视为 true）
```

**实测（reset #2 instance 92203808007179）**：

- stage_intake 完成时 `submitType=0`（默认 APPLY）
- decision_intake 评估：`submitType==1` false / `submitType==2` false / expr="" true → 走 `e_decision_default` → stage_pm
- 历史边：`e0, e_intake_decision, e_decision_default, e2, e3, e4, e5, e6`（含 default edge）

### 3.3 Trace 信息

```
trace_id : <request-id-of-stage_intake-execute>
spans    : [
  facade.processTask/execute (3ms, status=ok)  ← stage_intake execute
    ├─ engine.execute_task (2ms)
    │   ├─ capture_vars (0.5ms)
    │   ├─ next_node_dispatch (1ms)
    │   │   └─ decision.evaluate (0.1ms)  ← decision_intake 评估
    │   └─ activate_next_task (0.5ms)  ← 激活 stage_pm
    └─ facade return (0ms)
]
```

### 3.4 业务视角（人类审计，lite）

| 项 | 值 |
|----|-----|
| **触发** | stage_intake execute 后自动 |
| **依据** | `wf_process_task.variable.submitType`（上游透传） |
| **路由** | 1 → stage_pm；2 → end_rejected；其他 → stage_pm（兜底） |
| **业务** | 不需要人工操作；纯引擎路由 |
| **mems 扩展** | v0.7+：可读 wf_process_surrogate 历史 + formData 做更智能路由 |

**Lite 数据流**：

```
stage_intake.variable.submitType → decision_intake.expr 评估 → 路由
```

### 3.5 异常 / 错误

| 情况 | 引擎行为 | 处置 |
|------|----------|------|
| expr 语法错 | FIX-T112 兜底走第一条边 | 修 JSON expr |
| 所有 expr 都不匹配 + 无 default edge | FIX-T112 兜底走第一条边 | 加 default edge（**W013 警告**） |
| decision 节点无出边 | 引擎报错，instance 卡住 | 检查 FDEP.json edges |
| FIX-T113 §117 BUG | `_cleanup_orphan_decision_tasks` 可能抛 TypeError | 部署后必跑 TDD 实跑（W014） |

### 3.6 Audit Log 查 Bug

**核心数据源：`wf_process_task.variable`（路由依据）**

```sql
-- 查 submitType 是怎么决定的
SELECT task_name, variable, finish_time
FROM wf_process_task
WHERE process_instance_id = '<id>' AND task_name = 'stage_intake';
```

**关键字段**：`variable.submitType`（0=APPLY / 1=AGREE / 2=REJECT / 3=ROLLBACK / 4=JUMP / 5=RE_APPLY / 6=ROLLBACK_TO_OPERATOR / 20=COUNTERSIGN_DISAGREE）

**trace 查路由**：

```bash
curl -s "$TARGET/api/admin/trace/spans/<stage_intake-execute-trace_id>" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
for s in d['spans']:
    if 'decision' in s.get('name','').lower() or 'dispatch' in s.get('name','').lower():
        print(f'  {s[\"name\"]} attrs={s.get(\"attributes\",{})}')"
```

### 3.7 审计检查清单

- [ ] `submitType` 是否符合预期（1=AGREE → stage_pm / 2=REJECT → end_rejected）？
- [ ] 实际激活的下一 task 与决策匹配？
- [ ] historyEdges 包含 `e_decision_approve` / `e_decision_reject` / `e_decision_default` 中正确的那条？
- [ ] 高频兜底场景（如 submitType=0 大量出现）→ 需加 formData 让 submitType 显式

### 3.8 已知 Bug & 限制

| Bug | 影响 | 处置 |
|-----|------|------|
| submitType=0 频繁触发兜底 | 等同于 AGREE，但 PM 可能不是有意 | v0.7+ formData 显式化 |
| FIX-T112 兜底日志噪音 | WARN 但不影响 | 已知 |

---

## 4. stage_pm（snaker:task）

### 4.1 API 视角

| 项 | 值 |
|----|-----|
| 节点类型 | `snaker:task` |
| 触发 | 由 `decision_intake` 路由自动激活（submitType=1 或兜底） |
| **执行 API** | `POST /wf/processTask/execute` |
| **执行 body** | `{"processTaskId":"<id>","operator":"u_fdp_pm","submitType":1}` |
| formKey | `rml-template` |
| assignee (v0.6.2) | `u_fdp_pm`（直接） |
| SPI role (semantic) | `fdep_rml` |
| abstract R role | `R3` |

**实测 task 数据**（reset #2 instance 92203808007179）：

```json
{
  "id": "92203808020493",
  "taskName": "stage_pm",
  "formKey": "rml-template",
  "taskActorIdList": ["u_fdp_pm"],
  "taskState": 20,
  "operator": "u_fdp_pm",
  "createTime": "2026-09-22T10:06:21.270861",
  "finishTime": "2026-09-22T10:08:32.717528",
  "variable": { ... 透传自 stage_intake ... }
}
```

### 4.2 Decision 详情

| 决策项 | 选项 | 引擎行为 |
|--------|------|----------|
| **RML 编写** | 读 stage_intake 透传的变量 + 历史 mems | PM 编写 RML |
| **推进** | submitType=1 → stage_design | ✅ 正常 |
| **回退** | submitType=6 (ROLLBACK_TO_OPERATOR) → 回到 stage_intake | ✅ 可选 |
| **驳回** | submitType=2 (REJECT) → end_rejected | ⚠️ 跳过中间流程，不太推荐 |

**RML 决策依据**（lite）：

```
RML 完整度？
├─ 不完整 → 暂不推进，先补完
└─ 完整 → submitType=1 → stage_design
```

### 4.3 Trace 信息

```
trace_id : <stage_pm-execute-trace_id>
spans    : [
  facade.processTask/execute (5ms, status=ok)  ← stage_pm execute
    ├─ engine.execute_task (4ms)
    │   ├─ resolve_actors (1ms)
    │   ├─ capture_vars (0.5ms)
    │   └─ next_node_dispatch (2.5ms)  ← 路由到 stage_design
    └─ facade return (0ms)
]
```

### 4.4 业务视角（人类审计，lite）

| 项 | 值 |
|----|-----|
| **执行人** | u_fdp_pm（R3 PM 角色） |
| **决策时长** | 建议 ≤ 1-2 工作日（业务约定） |
| **决策产物** | submitType=1 + **RML 文档**（落档到 `ToT/pm/rml/<date>/<id>.md`） |
| **form** | `rml-template`（v0.6.x 暂为空 formKey） |

**RML 文档模板**（v0.7+ 用）：

```markdown
# RML · YYYYMMDD-NNN · <title>


### 4.2.1 Decision Mem 详情（v1.0 lite）

```json
{
  "decision_reason": "RML 完整：<背景/目标/用户故事/AC/范围 5 段齐全>",
  "decision_memo": {
    "rml_path": "ToT/pm/rml/<date>/<id>.md",
    "rml_length_lines": <N>,
    "key_requirements": ["req1", "req2"]
  },
  "context": {
    "rml_drafted_by": "AI | human",
    "draft_duration_min": <N>
  }
}
```

## 背景 (background)
<为什么做>

## 目标 (goals)
- [ ] 目标 1
- [ ] 目标 2

## 用户故事 (user_stories)
- 作为 <角色>，我想要 <功能>，以便 <价值>

## 验收标准 (acceptance_criteria)
- [ ] AC 1
- [ ] AC 2

## 范围 (scope)
- 包含: <...>
- 不包含: <...>

## 来源引用
- stage_intake id: <...>
- businessNo: <...>
```

**Lite 数据流**：

```
stage_intake.variable → stage_pm.variable → stage_design
   (透传)                (PM 写 RML)        (架构师读)
```

### 4.5 异常 / 错误

| 情况 | 响应 | 处置 |
|------|------|------|
| operator 不在 actors | `无权处理` | 用 u_fdp_pm 或 assignee |
| RML 未写完就推进 | 不报错但下节点缺上下文 | 流程约定：RML 完整才推进 |
| 误用 submitType=2 (驳回) | 跳过 stage_design/dev/review/feedback 直达 end_rejected | 不推荐，违反业务约定 |

### 4.6 Audit Log 查 Bug

**核心数据源：`wf_process_task`**：

```sql
SELECT id, task_name, task_state, operator, finish_time - create_time AS duration
FROM wf_process_task
WHERE process_instance_id = '<id>' AND task_name = 'stage_pm';
```

**查 stage_pm 是否有 RML 留档**（v0.7+）：

```bash
ls ToT/pm/rml/<date>/<processInstanceId>.md 2>/dev/null
```

### 4.7 审计检查清单

- [ ] `duration = finish_time - create_time` 在合理范围？
- [ ] RML 文档已落档（v0.7+）？
- [ ] 下一节点 `stage_design` 被激活？
- [ ] submitType=1（不应为 0/2 等意外值）？

### 4.8 已知 Bug & 限制

| Bug | 影响 | 处置 |
|-----|------|------|
| R3 同 R3（intake + pm 都 R3） | 自审自批嫌疑 | v0.7+ 拆 R3a/R3b（Q6） |
| formKey `rml-template` 无模板 | UI 渲染空 | v0.7+ 配 form |
| submitType=2 误用直达 end_rejected | 跳过中间环节 | 流程约定改用 submitType=6 (rollback) |

---

## 5. stage_design（snaker:task）

### 5.1 API 视角

| 项 | 值 |
|----|-----|
| 节点类型 | `snaker:task` |
| 触发 | 由 `stage_pm` execute 后自动激活 |
| **执行 API** | `POST /wf/processTask/execute` |
| **执行 body** | `{"processTaskId":"<id>","operator":"u_fdp_pm","submitType":1}` |
| formKey | `arch-template` |
| assignee (v0.6.2) | `u_fdp_pm`（直接） |
| SPI role (semantic) | `fdep_arch` |
| abstract R role | `R7`（架构师） |

**实测**（reset #2 instance 92203808007179）：

```
formKey     : arch-template
taskState   : 20 (DONE)
createTime  : 2026-09-22T10:08:32.720127
finishTime  : 2026-09-22T10:08:33.468152   ← 耗时 ~0.7s（冒烟快推进）
displayName : 2. 架构/接口设计 (u_fdp_pm 直接, ...)
```

### 5.2 Decision 详情

| 决策项 | 选项 | 引擎行为 |
|--------|------|----------|
| **架构完成** | submitType=1 → stage_dev | ✅ 正常 |
| **回退 RML** | submitType=6 (ROLLBACK_TO_OPERATOR) → 回到 stage_pm | ✅ 推荐 |
| **驳回** | submitType=2 → end_rejected | ⚠️ 跳过 dev/review/feedback |

**架构决策依据**（lite）：

```
RML 完整性 + 现有架构约束？
├─ RML 缺信息 → submitType=6 → 回到 stage_pm 补 RML
├─ 架构与现有冲突 → submitType=6 → 协商
└─ 架构清晰 → submitType=1 → stage_dev
```

### 5.3 Trace 信息

```
trace_id : <stage_design-execute-trace_id>
spans    : [
  facade.processTask/execute (~1ms, status=ok)
    ├─ engine.execute_task
    │   ├─ next_node_dispatch → stage_dev
    └─ facade return
]
```

### 5.4 业务视角（人类审计，lite）

| 项 | 值 |
|----|-----|
| **执行人** | u_fdp_pm（R7 架构师角色，占位） |
| **决策时长** | 建议 ≤ 2-5 工作日（业务约定） |
| **决策产物** | submitType=1 + **架构文档**（落档到 `ToT/design/<date>/<id>.md`） |
| **form** | `arch-template`（v0.6.x 暂为空） |

**架构文档模板**（v0.7+）：

```markdown
# 架构 · YYYYMMDD-NNN · <title>


### 5.2.1 Decision Mem 详情（v1.0 lite）

```json
{
  "decision_reason": "架构清晰：<模块划分清晰，接口编号连续，关键决策有理由>",
  "decision_memo": {
    "arch_path": "ToT/design/<date>/<id>.md",
    "api_count": <N>,
    "key_decisions": ["decision1", "decision2"]
  },
  "context": {
    "architect": "AI | human",
    "design_duration_hours": <N>
  }
}
```

## 模块划分
- 模块 A: <职责>
- 模块 B: <职责>

## 数据流
<ASCII 图 或 描述>

## 接口设计（编号连续 1, 2, 3...）
### API 1. <name>
- URL: <method> <path>
- request: <schema>
- response: <schema>

## Mock 数据
- 正常响应: <example>
- 异常响应: <example>

## 关键决策
- 选 X 而非 Y 的理由: <...>

## 来源引用
- RML id: <...>
- stage_pm id: <...>
```

**Lite 数据流**：

```
stage_pm.variable → stage_design.variable → stage_dev
   (PM RML)          (架构师读 RML + 写架构)   (开发者读架构)
```

### 5.5 异常 / 错误

| 情况 | 响应 | 处置 |
|------|------|------|
| 接口编号跳号 / 重复 | 静态校验失败（不在引擎，开发者自查） | 跑 `tdd-flow.py` 静态检查 |
| 架构与现有冲突 | 不自动检测 | 走 review 流程（stage_review） |
| 误回退到错误节点 | 引擎按 submitType 路由 | 用 submitType=6 (rollback) 显式回退 |

### 5.6 Audit Log 查 Bug

```sql
-- 查 stage_design 是否按预期推进
SELECT task_name, finish_time - create_time AS duration, variable
FROM wf_process_task
WHERE process_instance_id = '<id>' AND task_name = 'stage_design';
```

**查架构文档**：

```bash
ls ToT/design/<date>/<id>.md 2>/dev/null
```

### 5.7 审计检查清单

- [ ] 架构文档落档（v0.7+）？
- [ ] 接口编号连续、无跳号、无重复？
- [ ] 下一节点 `stage_dev` 被激活？
- [ ] 架构与 RML 一致（背景/目标对应）？

### 5.8 已知 Bug & 限制

| Bug | 影响 | 处置 |
|-----|------|------|
| formKey `arch-template` 无模板 | UI 渲染空 | v0.7+ 配 form |
| 接口编号无强校验 | 可能跳号/重复 | v0.7+ 加 schema 校验 |
| 没有"架构 review"环节 | 架构师独立决策，无 review | Q3：考虑加 design review 子节点 |

---

## 6. stage_dev（snaker:task）

### 6.1 API 视角

| 项 | 值 |
|----|-----|
| 节点类型 | `snaker:task` |
| 触发 | 由 `stage_design` execute 后自动激活 |
| **执行 API** | `POST /wf/processTask/execute` |
| **执行 body** | `{"processTaskId":"<id>","operator":"u_fdp_pm","submitType":1}` |
| formKey | `code-template` |
| assignee (v0.6.2) | `u_fdp_pm`（直接） |
| SPI role (semantic) | `fdep_dev` |
| abstract R role | `R2`（开发者 Agent） |

**实测**：

```
formKey     : code-template
duration    : ~0.7s (2026-09-22T10:08:33.47 → 10:08:34.22)
displayName : 3. 开发实现 (u_fdp_pm 直接, ...)
```

### 6.2 Decision 详情

| 决策项 | 选项 | 引擎行为 |
|--------|------|----------|
| **代码完成** | submitType=1 → stage_review | ✅ 正常 |
| **回退架构** | submitType=6 → 回到 stage_design | ✅ 可选 |
| **回退 RML** | submitType=6 多次 → 逐级回到 stage_pm | ✅ 可选 |
| **驳回** | submitType=2 → end_rejected | ⚠️ 不推荐 |

**开发决策依据**（lite）：

```
代码 + 单测完成？
├─ 单元测试覆盖率 < 80% → 不推进，先补测试
├─ 编译/lint 失败 → 不推进
└─ 都通过 → submitType=1 → stage_review
```

### 6.3 Trace 信息

```
trace_id : <stage_dev-execute-trace_id>
spans    : [
  facade.processTask/execute (~1ms)
    ├─ engine.execute_task
    └─ next_node_dispatch → stage_review
]
```

### 6.4 业务视角（人类审计，lite）

| 项 | 值 |
|----|-----|
| **执行人** | u_fdp_pm（R2 开发者 Agent） |
| **决策时长** | 建议 ≤ 3-10 工作日（业务约定） |
| **决策产物** | submitType=1 + **源代码 + 单元测试**（落档到 `ToT/src/<module>/` + `ToT/tdd/test_<module>.py`） |
| **form** | `code-template`（v0.6.x 暂为空） |

**Lite 数据流**：

```
stage_design.架构文档 → stage_dev.源代码 + 单测 → stage_review
   (架构)                (开发者读架构)             (评审)
```

### 6.5 异常 / 错误

| 情况 | 响应 | 处置 |
|------|------|------|
| 代码改动越界（写 ToT/ 外文件） | §1 边界违规 | 回滚，保留 ToT/ 内 |
| 测试覆盖率不足 | 流程约定：补到 ≥80% 再推进 | 跑 `tdd-flow.py` |
| 引擎版本升级导致 API 不兼容 | 引擎调用失败 | 走 engine-deploy SOP |

### 6.6 Audit Log 查 Bug

```sql
SELECT task_name, finish_time - create_time AS duration, variable
FROM wf_process_task
WHERE process_instance_id = '<id>' AND task_name = 'stage_dev';
```

**查代码改动范围**：

```bash
git log --oneline --since "<stage_dev.createTime>" --until "<stage_dev.finishTime>"
git diff --stat <commit_before> <commit_after>
```

### 6.7 审计检查清单

- [ ] 代码改动是否全在 `ToT/` 内（§1 边界规则）？
- [ ] 单元测试覆盖率 ≥ 80%？
- [ ] 架构文档与代码一致（接口编号、字段名）？
- [ ] 下一节点 `stage_review` 被激活？

### 6.8 已知 Bug & 限制

| Bug | 影响 | 处置 |
|-----|------|------|
| formKey `code-template` 无模板 | UI 渲染空 | v0.7+ 配 form |
| 无代码 review 子节点 | 直达 stage_review | 当前 OK（stage_review 涵盖） |
| 无 lint/编译自动门禁 | 依赖开发者自查 | v0.7+ 加 CI |

---


### 6.2.1 Decision Mem 详情（v1.0 lite）

```json
{
  "decision_reason": "代码 + 单测完成：<覆盖率 ≥80%，lint 通过，编译通过>",
  "decision_memo": {
    "commit_hash": "<git sha>",
    "src_path": "ToT/src/<module>/",
    "test_path": "ToT/tdd/test_<module>.py",
    "test_coverage_pct": <N>
  },
  "context": {
    "developer": "AI | human",
    "lines_changed": <N>
  }
}
```

## 7. stage_review（snaker:task）

### 7.1 API 视角

| 项 | 值 |
|----|-----|
| 节点类型 | `snaker:task` |
| 触发 | 由 `stage_dev` execute 后自动激活 |
| **执行 API** | `POST /wf/processTask/execute` |
| **执行 body** | `{"processTaskId":"<id>","operator":"u_fdp_pm","submitType":1}` |
| formKey | `review-template` |
| assignee (v0.6.2) | `u_fdp_pm`（直接） |
| SPI role (semantic) | `fdep_review` |
| abstract R role | `R6`（评审 Agent） + **R3 验收**（v0.7+ 拆） |

**实测**：

```
formKey     : review-template
displayName : 4. 评审/验收/发布 (u_fdp_pm 直接, ...)
```

### 7.2 Decision 详情

| 决策项 | 选项 | 引擎行为 |
|--------|------|----------|
| **评审通过** | submitType=1 → stage_feedback | ✅ 正常 |
| **回退开发** | submitType=6 → 回到 stage_dev | ✅ 推荐 |
| **回退架构** | submitType=6 多次 → 逐级回退 | ✅ 可选 |
| **驳回** | submitType=2 → end_rejected | ⚠️ 不推荐 |

**v0.6.2 现状**（lite）：
- R6（自动评审）+ R3（人工验收）**合并到同一个 task**（u_fdp_pm 一人）
- v0.7+ 拆为 fork-join（Q2）：R6 自动评审 + R3 人工验收并行

**评审决策依据**：

```
评审 + 验收都通过？
├─ R6 自动评审不通过 → submitType=6 → 回退
├─ R3 验收不通过 → submitType=6 → 回退
└─ 都通过 → submitType=1 → stage_feedback
```

### 7.3 Trace 信息

```
trace_id : <stage_review-execute-trace_id>
spans    : [
  facade.processTask/execute (~1ms)
    ├─ engine.execute_task
    └─ next_node_dispatch → stage_feedback
]
```

### 7.4 业务视角（人类审计，lite）

| 项 | 值 |
|----|-----|
| **执行人** | u_fdp_pm（R6 评审 + R3 验收 占位） |
| **决策时长** | 建议 ≤ 1-3 工作日 |
| **决策产物** | submitType=1 + **评审记录 + 发布说明**（落档 `ToT/reviews/<date>/<id>.md`） |
| **form** | `review-template`（v0.6.x 暂为空） |

**Lite 数据流**：

```
stage_dev.代码+单测 → stage_review.评审记录 → stage_feedback
   (开发者)              (R6+R3 占位)            (知识沉淀)
```

### 7.5 异常 / 错误

| 情况 | 响应 | 处置 |
|------|------|------|
| R6 评审通过但 R3 验收不通过 | 当前无法分别处理（合并 task） | v0.7+ 拆 fork-join |
| 误驳回 | submitType=2 直达 end_rejected | 业务约定改用 submitType=6 |
| 评审通过但代码实际有 bug | 后续 stage_feedback 抓 | v0.7+ 加 CI 自动扫描 |

### 7.6 Audit Log 查 Bug

```sql
SELECT task_name, finish_time - create_time AS duration, variable
FROM wf_process_task
WHERE process_instance_id = '<id>' AND task_name = 'stage_review';
```

**查评审记录**：

```bash
ls ToT/reviews/<date>/<id>.md 2>/dev/null
```

### 7.7 审计检查清单

- [ ] 评审记录 + 发布说明已落档？
- [ ] R6 自动评审是否真跑了（v0.7+）？
- [ ] R3 验收是否签字（v0.7+）？
- [ ] 下一节点 `stage_feedback` 被激活？

### 7.8 已知 Bug & 限制

| Bug | 影响 | 处置 |
|-----|------|------|
| R6+R3 合并 task | 无法独立审核 | **v0.7+ 拆 fork-join（Q2）** |
| formKey `review-template` 无模板 | UI 渲染空 | v0.7+ 配 form |
| 无 CI 自动 lint/test | 评审依赖人 | v0.7+ 加 CI |

---


### 7.2.1 Decision Mem 详情（v1.0 lite）

```json
{
  "decision_reason": "评审通过：<R6 自动评审通过 + R3 验收通过>",
  "decision_memo": {
    "review_path": "ToT/reviews/<date>/<id>.md",
    "r6_auto_passed": true,
    "r3_human_signed": true,
    "issues_found": <N>
  },
  "context": {
    "reviewer": "u_fdp_pm",
    "review_duration_hours": <N>
  }
}
```

## 8. stage_feedback（snaker:task）

### 8.1 API 视角

| 项 | 值 |
|----|-----|
| 节点类型 | `snaker:task` |
| 触发 | 由 `stage_review` execute 后自动激活 |
| **执行 API** | `POST /wf/processTask/execute` |
| **执行 body** | `{"processTaskId":"<id>","operator":"u_fdp_pm","submitType":1}` |
| formKey | `kb-template` |
| assignee (v0.6.2) | `u_fdp_pm`（直接） |
| SPI role (semantic) | `fdep_kb` |
| abstract R role | `R5`（知识管理） + **R3 反馈收集**（v0.7+ 拆） |

**实测**：

```
formKey     : kb-template
displayName : 5. 反馈/知识沉淀 (u_fdp_pm 直接, ...)
```

### 8.2 Decision 详情

| 决策项 | 选项 | 引擎行为 |
|--------|------|----------|
| **知识入库** | submitType=1 → end（流程闭环） | ✅ 正常 |
| **回退评审** | submitType=6 → 回到 stage_review | ✅ 极少用 |
| **驳回** | submitType=2 → end_rejected | ⚠️ 不推荐 |

**v0.6.2 现状**：
- R5（知识入库）+ R3（反馈收集）**合并到同一 task**
- v0.7+ 拆为 fork-join 或串行（R3 收 R5 入库）

**知识沉淀决策依据**：

```
每条反馈关联到 Task/Issue？
├─ 否 → 不入库，要求关联
└─ 是 → submitType=1 → end（完成）
```

### 8.3 Trace 信息

```
trace_id : <stage_feedback-execute-trace_id>
spans    : [
  facade.processTask/execute (~1ms)
    ├─ engine.execute_task
    └─ next_node_dispatch → end (snaker:end)
]
```

### 8.4 业务视角（人类审计，lite）

| 项 | 值 |
|----|-----|
| **执行人** | u_fdp_pm（R5 + R3 占位） |
| **决策时长** | 建议 ≤ 1-2 工作日 |
| **决策产物** | submitType=1 + **Issue 追踪 + 知识库条目**（落档 `ToT/issues/<date>/<id>.md` + `ToT/kb/<topic>.md`） |
| **form** | `kb-template`（v0.6.x 暂为空） |

**Lite 数据流**：

```
stage_review.评审记录 → stage_feedback.反馈+知识 → end（流程闭环）
   (评审)                  (R5+R3 占位)          (state=DONE)
```

### 8.5 异常 / 错误

| 情况 | 响应 | 处置 |
|------|------|------|
| 反馈无 Task/Issue 关联 | §1 边界：拒绝孤立文档 | 业务约定：每条必须关联 |
| 知识库条目质量低 | 不自动检测 | R5 人工审查 |
| 误回退到评审 | 走 submitType=6 | 极少用 |

### 8.6 Audit Log 查 Bug

```sql
SELECT task_name, finish_time - create_time AS duration
FROM wf_process_task
WHERE process_instance_id = '<id>' AND task_name = 'stage_feedback';
```

**查知识沉淀**：

```bash
ls ToT/issues/<date>/<id>.md 2>/dev/null
ls ToT/kb/<topic>.md 2>/dev/null
```

### 8.7 审计检查清单

- [ ] 每条反馈都关联到 Task/Issue？
- [ ] 知识库条目已落档？
- [ ] 流程即将进入 end（state=20）？
- [ ] instance 状态从 DOING → DONE？

### 8.8 已知 Bug & 限制

| Bug | 影响 | 处置 |
|-----|------|------|
| R5+R3 合并 task | 无法独立审核反馈 | v0.7+ 拆 |
| formKey `kb-template` 无模板 | UI 渲染空 | v0.7+ 配 form |
| 无孤立文档自动检测 | 靠 R5 人工 | v0.7+ 加 schema |

---


### 8.2.1 Decision Mem 详情（v1.0 lite）

```json
{
  "decision_reason": "反馈沉淀完成：<每条反馈关联 Task/Issue，知识库条目落档>",
  "decision_memo": {
    "issues_path": "ToT/issues/<date>/<id>.md",
    "kb_entries": ["ToT/kb/<id>.md"],
    "feedback_count": <N>
  },
  "context": {
    "knowledge_admin": "u_fdp_pm",
    "knowledge_owner": "R5"
  }
}
```

## 9. end（snaker:end）

### 9.1 API 视角

| 项 | 值 |
|----|-----|
| 节点类型 | `snaker:end`（流程正常终点） |
| 直接 API | **无**（end 节点不能 execute，由 stage_feedback execute 后自动触发） |
| 触发 | stage_feedback execute 完成后，引擎自动激活 end（无 task 创建） |
| 实例终态 | `state = 20 (DONE)` |

### 9.2 Decision 详情

| 决策项 | 选项 | 引擎行为 |
|--------|------|----------|
| **无** | end 节点无 expr / 无 task | 引擎设 state=DONE |

**终态判定**：所有上游 task 都 DONE + 当前 edge `e6` 触发 → end 节点激活 → state 转 DONE。

### 9.3 Trace 信息

```
trace_id : <stage_feedback-execute-trace_id>（end 与 stage_feedback 共享）
spans    : [
  facade.processTask/execute (stage_feedback)
    ├─ engine.execute_task
    │   └─ next_node_dispatch → end (snaker:end)
    └─ facade return
  (后续 state 转 DONE 由 engine 异步处理)
]
```

### 9.4 业务视角（人类审计，lite）

| 项 | 值 |
|----|-----|
| **触发** | stage_feedback 完成后自动 |
| **业务含义** | 协作闭环：全流程完成 |
| **业务审计** | 流程已结束 |
| **后续动作** | fmem 推送 / 用户通知 / 数据归档（v0.7+） |

**Lite 终态流程图**：

```
start → intake → decision → pm → design → dev → review → feedback → [end] ✓
                                                                  DONE
```

### 9.5 异常 / 错误

| 情况 | 响应 | 处置 |
|------|------|------|
| instance 卡在 end 节点但 state≠20 | 引擎异步处理延迟 | 等几秒后查 state |
| end 节点被 skip | state=20 但 historyNodes 不含 end | 引擎 BUG，待排查 |
| 多余的 outgoing edge | W008 警告已在 v0.6.2 处理 | 加 default edge |

### 9.6 Audit Log 查 Bug

**核心数据源**：`wf_process_instance.state`

```sql
SELECT id, state, finish_time, variables
FROM wf_process_instance
WHERE id = '<processInstanceId>';
```

**state 含义**：
- 10（DOING）：至少 1 个 task 在 DOING
- 20（DONE）：所有 task DONE + 到达 end 节点
- 45（REJECT）：到达 end_rejected 节点

**查全任务完成时间线**：

```bash
curl -s -X POST "$TARGET/wf/processInstance/detail" \
    -H "Content-Type: application/json" \
    -d '{"id":"<processInstanceId>"}' | python3 -c "
import sys, json
d = json.load(sys.stdin)['data']
state = d['state']
state_name = state.name if hasattr(state,'name') else state
print(f'  state: {state_name}')
for t in d['tasks']:
    tstate = t.get('taskState')
    tstate_name = tstate.name if hasattr(tstate,'name') else tstate
    print(f'  {t[\"taskName\"]:20s} {tstate_name} {t.get(\"finishTime\")}')"
```

### 9.7 审计检查清单

- [ ] `state = 20 (DONE)`？
- [ ] 所有 task `taskState = 20 (DONE)`？
- [ ] historyNodes 包含 `end`？
- [ ] total duration 合理（业务约定）？

### 9.8 已知 Bug & 限制

| Bug | 影响 | 处置 |
|-----|------|------|
| end 节点异步 state 转换 | 调用 execute 后立即查可能 state=10 | 已知，加 0.5s sleep |
| 无 end 节点"业务总结"API | 审计需看完整 task 链 | v0.7+ 加 `/processInstance/summary` |

---

## 10. end_rejected（snaker:end）

### 10.1 API 视角

| 项 | 值 |
|----|-----|
| 节点类型 | `snaker:end`（驳回闭环终点） |
| 直接 API | **无**（由 decision_intake 路由自动触发） |
| 触发 | decision_intake 评估 `submitType==2` → 路由 `e_decision_reject` → end_rejected |
| 实例终态 | `state = 45 (REJECT)` |

### 10.2 Decision 详情

| 决策项 | 选项 | 引擎行为 |
|--------|------|----------|
| **驳回闭环** | submitType=2 from stage_intake | ✅ 走 `e_decision_reject` → end_rejected |
| **驳回跳过** | submitType=2 from stage_pm/design/dev/review/feedback | ⚠️ 跳过中间环节，不推荐 |

**v0.6.2 局限：**
- **仅 stage_intake 有驳回路径**（Q5）
- 其他阶段用 submitType=2 也会直达 end_rejected（跳过中间），但业务上不推荐
- v0.7+ 给其他 stage 也加驳回路径 + Q7 resurrect（驳回后能否再激活）

### 10.3 Trace 信息

```
trace_id : <stage_intake-execute-trace_id>
spans    : [
  facade.processTask/execute (stage_intake)
    ├─ engine.execute_task
    │   ├─ decision.evaluate (0.1ms)
    │   │   └─ submitType==2 → 路由 e_decision_reject → end_rejected
    │   └─ next_node_dispatch → end_rejected (snaker:end)
    └─ facade return
]
```

### 10.4 业务视角（人类审计，lite）

| 项 | 值 |
|----|-----|
| **触发** | stage_intake 主动 REJECT |
| **业务含义** | 请求被拒绝，流程终止 |
| **业务审计** | 必查驳回理由（否则误操作） |
| **后续动作** | **驳回记录必落档**（`ToT/pm/intake/rejected/<date>/<id>.md`）+ 用户反馈原因 |

**驳回记录模板**（lite）：

```markdown
# Rejected · YYYYMMDD-NNN · <brief>

## 请求来源
- 发起人: <uid>
- 触发方式: <API / UI>
- businessNo: <...>

## 驳回原因
- <具体原因，必填>
- 涉及范围: <...>
- 建议下一步: <...>

## 决策
- 审批人: <uid> (u_fdp_pm)
- 决策时间: <timestamp>

## 来源引用
- stage_intake id: <...>
- original request: <...>
```

### 10.5 异常 / 错误

| 情况 | 响应 | 处置 |
|------|------|------|
| 驳回理由未记录 | 业务约定：必填 | 流程约束（v0.7+） |
| 误驳回（应是 submitType=1） | 不可恢复（end_rejected 是终态） | v0.7+ 加 Q7 resurrect |
| 从其他 stage 误驳回（跳过中间） | state=45 但无中间过程记录 | 业务约定：驳回只能在 stage_intake |

### 10.6 Audit Log 查 Bug

```sql
SELECT id, state, variables
FROM wf_process_instance
WHERE id = '<processInstanceId>';
-- state = 45 (REJECT)
```

**查驳回理由**（lite）：
- 当前只能在 stage_intake 的 `wf_process_task.variable` 中查找（无 reject_reason 字段）
- v0.7+ 加专用 reject_reason 字段

**查驳回记录**：

```bash
ls ToT/pm/intake/rejected/<date>/<id>.md 2>/dev/null
```

### 10.7 审计检查清单

- [ ] `state = 45 (REJECT)`？
- [ ] historyNodes 含 `stage_intake` + `end_rejected`？
- [ ] 驳回理由已记录？
- [ ] 驳回记录已落档 `ToT/pm/intake/rejected/`？

### 10.8 已知 Bug & 限制

| Bug | 影响 | 处置 |
|-----|------|------|
| end_rejected 是终态，驳回后不可恢复 | 误驳回无补救 | v0.7+ Q7 resurrect |
| 仅 stage_intake 有驳回路径 | 其他 stage 误用跳过中间 | v0.7+ Q5 全阶段驳回 |
| 无 reject_reason 字段 | 驳回理由靠业务 mems | v0.7+ 加 schema |

---

## 11. 全流程速查表

| 节点 | 类型 | formKey | assignee | SPI role | abstract R | 路由出口 |
|------|------|---------|-----------|----------|-------------|----------|
| start | start | — | — | — | — | → stage_intake |
| stage_intake | task | intake-template | R3 | fdep_intake | R3 | → decision_intake |
| decision_intake | decision | — | — | — | — | submitType 路由 |
| stage_pm | task | rml-template | R3 | fdep_rml | R3 | → stage_design |
| stage_design | task | arch-template | R7 | fdep_arch | R7 | → stage_dev |
| stage_dev | task | code-template | R2 | fdep_dev | R2 | → stage_review |
| stage_review | task | review-template | R6 | fdep_review | R6 + R3 | → stage_feedback |
| stage_feedback | task | kb-template | R5 | fdep_kb | R5 + R3 | → end |
| end | end | — | — | — | — | state=20 DONE |
| end_rejected | end | — | — | — | — | state=45 REJECT |

## 12. Lite 数据透传链（mems way）

```
stage_intake.variable ←── start.variable + u_userId/u_realName/u_deptId/u_deptName/u_postId/u_postName + autoGenTitle + submitType
   ↓ 透传
stage_pm.variable (同 stage_intake) + RML
   ↓ 透传
stage_design.variable (同) + 架构
   ↓ 透传
stage_dev.variable (同) + 代码
   ↓ 透传
stage_review.variable (同) + 评审
   ↓ 透传
stage_feedback.variable (同) + 反馈
   ↓ 路由
end / end_rejected
```

## 13. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 初稿：start 节点 9 节 |
| v0.2 | 2026-09-22 | start 调整为含 Trace / Decision / Audit 3 数据源的完整结构 |
| v0.3 | 2026-09-22 | stage_intake lite 版（去掉详细业务产出模板，只透传 mems） |
| v0.4 | 2026-09-22 | decision_intake lite 版（核心是路由规则表 + FIX-T112 兜底） |
| v0.5 | 2026-09-22 | stage_pm lite（加 RML 文档模板） |
| v0.6 | 2026-09-22 | stage_design lite（加架构文档模板） |
| v0.7 | 2026-09-22 | stage_dev lite（强调 §1 边界检查） |
| v0.8 | 2026-09-22 | stage_review lite（R6+R3 合并 → v0.7+ 拆 fork-join） |
| v0.9 | 2026-09-22 | stage_feedback lite（无孤立文档自动检测） |
| v1.0 | 2026-09-22 | end + end_rejected 终态 + 全流程速查表 + 数据透传链 + 变更日志 |
| **v1.1** | **2026-09-22** | **Decision Mem 协议 v1.0 lite**（用户口头指令"can't seed decision mem data for each node ... i always need test report"驱动）：① §0 新增全局协议（3 字段：decision_reason / decision_memo / context；引擎透传机制见 `facade.py:713`）；② §2.2-§8.2 每个 task 节点新增 "Decision Mem 详情" 节，给出该节点专属的 mem 模板；③ demo cycle v2 实测：5/6 task 含完整 decision mems；④ `ToT/tdd/test_fdep_baseline_v1decision_mems.{md,json}` 作为新基线。 |
| **v1.2** | **2026-09-22** | **Decision Mem 协议 v1.2 lite+**（用户口头指令"when record the mem log, recod the job_card_url also, that need be auditing also with log"驱动）：① §0 协议新增 `decision_memo.job_card_url` 字段（记录 executor 实际用的 Job Card），与已有 `decision_memo.next_handoff.job_card_url` 共同构成审计链；② §0 加"审计链验证"规则：T.used == next(T).used-prev.handoff；③ demo cycle v4 实测：5/5 task 提交带 job_card_url，5/5 审计链匹配，文件全部真实存在；④ `ToT/tdd/test_fdep_baseline_v3audit.{md,json}` 作为新基线。 |
