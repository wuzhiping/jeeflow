# AGENTS.md — 流程设计与测试协作指南

本指南面向「流程设计 Agent」与「流程测试 Agent」。所有动作以仓库内已有文档为准，不得自由发挥。

---

## 1. 角色与边界

| 角色 | 目标 | 主要产物 |
| --- | --- | --- |
| 设计 Agent | 根据业务需求产出可被引擎解析的流程 JSON | `./tdd/<name>.json`（WIP；测试通过后可晋升为 `./flows/<name>.json`） |
| 测试 Agent | 把 JSON 部署到引擎、启动实例、走完审批流并核验 | `./tdd/test_<name>_<YYYYMMDDHHMMSS>.md`（curl 脚本 + 请求/响应日志）+ 测试中发现的字段语义补充到 `./docs/flow.md` |

**TDD 闭环**：每次新增 / 修改流程都必须经过 `设计 → ./tdd/ 落地 → 校验 → 部署测试 → 写 docs` 五步；缺一步视为未完成。

**硬约束**：

- 流程开发**不修改** `main.py` / `main_pg.py` 之外的业务代码；`vendor/jeeflow/` 在**用户授权下可修改并改进**（2026-09-17 起开放）
- 不得安装依赖；不得访问项目目录外
- 进度仅在当前会话维护不得落盘
- 所有 action 调用必须来自 `./docs/actions.md` 已登记的清单（参见 §5 速查表），**禁止**臆造 action 名
- `vendor/jeeflow/` 修改前必须：
  1. 同步修改 `docs/known-issues.md` 相关章节（标记 FIX 编号）
  2. 在 `bdd/` 或 `tdd/` 写测试报告验证
  3. 同步 `main.py` / `main_pg.py`（如有兼容性问题）
- 所有文件路径引用一律使用 `./` 开头的相对路径，**禁止**使用绝对路径 `/opt/jupyter/...`

### vendor/jeeflow 改进工作流

```bash
# 1. 直接编辑 vendor/jeeflow/*.py
# 2. 记录到 docs/known-issues.md §XX（FIX-Tn + 实测）
# 3. 重启 main.py 验证（无需重装依赖，sys.path 优先用 vendor）
# 4. 同步到 main_pg.py 兼容（如 PG 后端）
```

**vendor/jeeflow 优先级**：main.py + main_pg.py + spi/__init__.py 顶部已加
`sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vendor"))`，
启动时**优先使用 vendor/jeeflow**，不依赖 `.venv/site-packages/jeeflow`。

`.venv/site-packages/jeeflow` 保留作为参考对照（不删除），但实际运行用 vendor。

---

## 2. 必读文件清单

| 文件 | 内容 | 何时读 |
| --- | --- | --- |
| `./docs/flow.md` | 流程 JSON 完整规范（10 节 + 速查） | 设计前读全文；测试中遇到歧义回查 §3-§7 |
| `./docs/actions.md` | 47 action + 路由解析 + curl 模板（端口 8101） | 测试时按 action 名查表 |
| **`./docs/BUGS.md`** | **27 BUG（已修 27+仍存 0）+ 5 已知限制 + 16 项自检清单（v1.9.0 2026-09-19 更新）** | **设计前必读，避开引擎能力边界** |
| `./flows/*.json` | 15 个真实样例（01-13） | 设计时挑最相似的样例 fork（**只读模板，不得改写**） |
| `./tdd/*.json` | WIP 流程 JSON | 当前会话要开发的新流程；测试通过后再决定是否晋升到 `./flows/` |
| `./tdd/README.md` | TDD 目录使用约定 | 写新流程前必读 |
| `./docs/pg_schema.sql` | 真实 PostgreSQL 表 DDL（仅参考） | 查字段含义 |
| `./docs/known-issues.md` | 87 个章节详细问题（§1-§86） | 测试中遇到具体问题时按 §X 索引 |

---

## 3. 设计 Agent 工作流

### 3.1 输入约束

调用方必须明确：

1. 流程 key（顶层 `name`）—— 全局唯一、字母数字下划线
2. 流程类型（`approval` / `business`）
3. 节点列表（顺序 + 类型 + 处理人 + 表单）
4. 分支条件（若用决策）
5. 是否需要会签 / 驳回 / 自定义节点

### 3.2 TDD 设计步骤（必须按顺序）

```
1) 列出节点序列（含 start / end）
2) 选择节点类型（start / task / decision / fork / join / custom / end）
3) 写 properties（按 ./docs/flow.md §3.3-§3.5）
4) 写边 properties（decision 出边 expr / 其他边可空）
5) 文件落地到 ./tdd/<key>.json          ← WIP，**不要写到 ./flows/**
6) python -c "import json; json.load(open('./tdd/<key>.json'))"  语法校验
7) 【TDD】部署 + 启动 + 跑通（curl 见 §5），过程中记录每次请求/响应
8) 【TDD】写 ./tdd/test_<key>_<YYYYMMDDHHMMSS>.md（测试日志 + 校验结果）
9) 【TDD】若发现新字段语义 / 边界条件 → 同步更新 ./docs/flow.md 对应节
10) （可选）人工对照 §4 模板逐行核对
11) （可选）测试稳定后把 ./tdd/<key>.json 晋升为 ./flows/<key>.json（须在
    ./tdd/test_<key>_<YYYYMMDDHHMMSS>.md 顶部标注「已晋升」+ 提交号）
```

### 3.3 节点 id / 边 id 命名

参见 `./docs/flow.md §4a`。**禁止**节点 id 含空格 / `-` / 中文（引擎底层有部分宽限，但跨语言 Java 端会触发键映射问题）。

---

## 4. 设计模板（基于 15 个样例）

| 业务场景 | 推荐样板 | 关键字段 |
| --- | --- | --- |
| 申请人→上级→结束 | `./flows/01-simple.json` | apply=`applicant`、task1=`leader`、`field.PERMISSION_*` |
| 多层审批 | `./flows/02-multi-task.json` | 三个 task 节点串行 |
| 金额分支 | `./flows/03-decision-expr.json` | decision1 + 两出边 expr `amount>1000` / `amount<=1000` |
| 并行审批 + 汇合 | `./flows/04-fork-join.json` | fork1→taskA/taskB→join1；taskB `taskType:1` |
| 并行会签（多人同时审） | `./flows/05-countersign-parallel.json` | `performType=1, countersignType=PARALLEL`，assignee 多值 |
| 串行会签（按顺序审） | `./flows/06-countersign-sequential.json` | `countersignType=SEQUENTIAL` |
| 比例会签（✅ 已实现，RatioCapableEngine 扩展） | `./flows/07-countersign-ratio.json` | `countersignCompletionCondition: "#nrOfCompletedInstances==2"`（OGNL 表达式，`nrOfCompletedInstances`/`nrOfInstances` 自动注入） |
| 一票否决会签 | `./flows/13-countersign-one-vote-veto.json` | `countersignCompletionCondition: "ONE_VOTE_VETO"` |
| 自定义节点 | `./flows/08-custom-node.json` | `clazz + args + val` ✅ **v1.9.0 FIX-T38 已实现**：`clazz` 查 `EngineExtensions.custom_handler_registry`，handler 签名 `async def(node, inst, vars_, args) -> Any`，结果写回 `vars_[val]`（详见 `known-issues.md §16`） |
| 驳回路径 | `./flows/09-with-reject.json` | submitType=Reject 走 reject 边 |
| 业务流 + 拦截器 | `./flows/10-mixed-mode.json` | 顶层 `preInterceptors/postInterceptors`；`type: "business"` |
| 处理人为变量 | `./flows/11-assignee-vars.json` | `assignee: "deptLeader"` / `"userA,userB"` |
| 内置 handler 全部列示 | `./flows/11-assignment-handler.json` | 7 个 FQCN（见 `./docs/flow.md §6`） |
| 候选人分页 | `./flows/12-candidate-page.json` | 节点级 `candidateUsers/candidateGroups`（properties 根下） |

**复合场景**：`./flows/08-countersign-sequential-approve.json`（串行会签后并联 approve）。

---

## 5. 测试 Agent 工作流

### 5.1 启动 uvicorn

端口：**8101**（参见 `./docs/actions.md §1`）。

外部 launcher 已固化（PPID=1，`setsid nohup & disown`，详见先前 `/tmp/opencode/start_uvicorn.sh` 经验）。**禁止**用 inline `nohup &` —— watchdog 会 SIGKILL 连带进程。

### 5.2 健康检查

```bash
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/stats/overview \
  -H 'Content-Type: application/json' -d '{}' | jq
# 期望：{ "code": 0, "data": { ... }, "msg": "成功" }
```

### 5.2.5 重置测试环境（`/api/reset`，必要时调用）

`/api/reset` **不在** `./docs/actions.md §1-§7` 的 47 个工作流 action 清单里 —— 它是 main_pg.py:526 注册的旁路端点，用于一键清空 PG 表 + 重载流程定义种子（详见 main_pg.py:528 注释 `issues/11`）。

```bash
curl -s -X POST http://127.0.0.1:8101/api/reset | jq
# 期望：{ "code": 0, "data": { "reloadedDefines": <N> }, "msg": "成功" }
```

**用途**：跑完一组用例想从干净状态开始下一组、或数据被前序测试污染时调用。会清空所有 identity / 实例 / 任务，重载 seed 中的流程定义。

> ⚠️ **实测补充（2026-09-17 复测 `01-simple`）**：`/api/reset` **不清空 `processDesign` 与 `processDefine` 两张表**。designId 和 processDefineId 是**累积自增**的，每次 deploy 会创建新版本（同名流程 `version+1`），旧版本保留。
> - 测试时**必须**用本次 deploy 返回的 `processDefineId`，**不可硬编码**为 `1`/`16` 等历史值。
> - seed 流程（如 `simple` v1=id 1）与本次部署 v2（实测 id=113）共存，`processDefine/page` 能看到全部历史版本。
> - 清除设计缓存可用 `/wf/processDesign/delete`（未在 §5.1 速查表，谨慎使用）。

> ⚠️ **2026-09-17 PG 后端实测补充（17 个 flow 全量回归）**：
> - PG 后端 `processDesign.id` 和 `processDefine.id` 是 **19 位雪花 ID**（time-ordered bigint），非 sqlite 自增格式（如 1-17 或累积 113）
> - 本轮 17 个 flow PG 回归实测：design_id 形如 `1789614853725000`，processDefineId 形如 `1789614853782000`
> - runner **必须**从 `processDesign/save` 响应取 `data.id`，从 `processDesign/deploy` 响应取 `data.processDefineId`；**不可假设任何固定值**
> - 17 个流程 PG 行为与 sqlite 完全一致（除 ID 格式）；v1.9.0 起 `08-custom-node` + `14-decision-submitType` 已修复（FIX-T37/T38）

**约束**：
- **非工作流 action**，不走 `/wf/{action}` 门面，AGENTS.md §5.3-§5.8 的 action 替换规则对它无效。
- 调用前确认磁盘上没有未晋升的 `./tdd/<key>.json`（WIP 数据本身不会被清，因为 reset 只动 PG 表），但若该流程已部署到 PG，部署的副本会消失 —— 需要重新部署或从 `./flows/<key>.json` 再次启动。
- 幂等：可重复调用。
- 不计日志章节的常规 action —— `./tdd/test_<key>_<YYYYMMDDHHMMSS>.md` 里只记「调用前 X 次调用 / 调用后 Y 次」即可，不必详写每次 reset 的响应。

### 5.3 部署流程（设计器 → 定义）

```bash
# Step A：保存设计（含 content）
curl -s -X POST http://127.0.0.1:8101/wf/processDesign/save \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "test-simple",
    "displayName": "测试-简单审批",
    "type": "approval",
    "content": '"$(cat ./flows/01-simple.json | jq -c . | sed 's/"/\\"/g')"'
  }'

# Step B：取设计 id（返回 data.id）
DESIGN_ID=...

# Step C：部署（生成 wf_process_define）
curl -s -X POST http://127.0.0.1:8101/wf/processDesign/deploy \
  -H 'Content-Type: application/json' \
  -d "{\"id\": $DESIGN_ID}"
```

`processDesign/deploy` 按 `name` 自动 `+1` version（详见 `./docs/actions.md §2 #14`）。

> ⚠️ **实测补充（2026-09-17 复测 `02-multi-task`）**：
> - `processDesign/save` 是 **UPSERT**：以 `name` 为唯一键，**复用现有行 id**。`/api/reset` 后 design 表仅 1 行 id=9；多次 save 不同 name 全部返回 id=9（**name 字段被覆盖**）。
> - `processDesign/deploy` 也复用 `processDefineId`（实测两次 deploy 都返回 113，但 `name`/内容随上次 save 而变）。
> - **结论**：runner 必须记录本轮 deploy 返回的 `processDefineId` + 用 `processDefine/page` 验证当前 `name` 与期望流程匹配，**不可硬编码 id**。

### 5.4 启动流程实例

`./docs/actions.md` 中**仅开放** `processInstance/startAndExecute`（及其别名 `startAndExecute`），该方法一次性完成「启动 + 跑第一步」。**禁止**使用 `/wf/processInstance/start`（不在清单中；同等处理见 §6 关键约束）。

```bash
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/startAndExecute \
  -H 'Content-Type: application/json' \
  -d '{
    "processDefineId": "<本轮 deploy 返回的 processDefineId>",
    "operator": "user1",
    "title": "测试-简单审批-001",
    "assignees": {"apply": "user1"},
    "variables": {
      "submitType": 0,
      "f_leaveType": "事假",
      "days": 3,
      "u_userId": "user1",
      "u_realName": "用户1"
    }
  }'
```

返回 `data.processInstanceId`（数字）。所有 id 字段出口会被 `_stringify_ids` 转字符串。

> ⚠️ **必传字段（实测）**：
> - `processDefineId` — 顶层，**非 `name` + `version` 组合**；本轮 deploy 响应 `data.processDefineId` 即得。
> - `operator` — 顶层；发起人 userId（与 `variables.u_userId` 一致）。
> - `assignees` — 顶层 dict `{<taskName>: <userId>}`；**不传则下游 task 处于 taskState=10 但 operator=空，runner 无法自动推进**。
> - `variables` — 顶层 dict；业务变量（`f_*`）+ 操作人（`u_*`）+ submitType。**`submitType` 顶层 variables 与顶层 `args.submitType` 等效，但 facade bug 会强制改值（见 `./docs/known-issues.md` §1）。

### 5.5 取待办 + 执行任务

`./docs/actions.md` 中**仅开放** `processTask/todoList`（列待办）和 `processTask/execute`（提交任务）。**禁止**使用 `/wf/task/page` 或 `/wf/processInstance/completeTask`（不在清单中）。

```bash
# 取 todo 列表
curl -s -X POST http://127.0.0.1:8101/wf/processTask/todoList \
  -H 'Content-Type: application/json' \
  -d '{"operator": "leader", "pageNum": 1, "pageSize": 20}'

# 取任务 id 后提交
curl -s -X POST http://127.0.0.1:8101/wf/processTask/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "processTaskId": <TASK_ID>,
    "submitType": 0,
    "operator": "leader"
  }'
```

> ⚠️ **字段名修正（2026-09-17 实测）**：请求字段是 **`processTaskId`**，**不是** `taskId`。runner v4 之前用错，导致 0/7 通过。
```

### 5.6 校验

```bash
# 实例详情
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/detail \
  -H 'Content-Type: application/json' -d '{"id": <INSTANCE_ID>}'

# 审批记录
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/approvalRecord \
  -H 'Content-Type: application/json' -d '{"id": <INSTANCE_ID>}'

# 节点高亮（流程图当前位置）
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/highLight \
  -H 'Content-Type: application/json' -d '{"id": <INSTANCE_ID>}'

# 实例变量（含发起人/操作人/流程变量）
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/bizData \
  -H 'Content-Type: application/json' -d '{"id": <INSTANCE_ID>}'

# 定义详情（查版本）
curl -s -X POST http://127.0.0.1:8101/wf/processDefine/getLastByName \
  -H 'Content-Type: application/json' -d '{"name": "simple"}'
```

### 5.7 字段权限核验

启动实例时传 `PERMISSION_f_<field>=1`（只读）/`2`（编辑）/`3`（隐藏）。完成后查 `bizData`：
- 只读字段：值回传，但任务行不允许再写
- 隐藏字段：值丢弃，前端不可见

> ⚠️ **FIX-DOC-1（2026-09-18）**：原文档误写"2=隐藏"，实测 2=编辑，3=隐藏。详见 `known-issues.md §82` + `flow.md §5.1`。

### 5.8 会签测试

| 类型 | curl 操作 | 预期 `performType/countersignType` | 预期完成条件 |
| --- | --- | --- | --- |
| 并行 | 三用户按序 `processTask/execute` | `1 / PARALLEL` | **全员通过才流转**（剩余成员 taskState 仍 10，不自动废弃） |
| 串行 | 三个用户按顺序 `processTask/execute` | `1 / SEQUENTIAL` | 仅最后一个通过即流转 |
| 比例 | N 个用户中 K 个通过 | `1 / PARALLEL` | `countersignCompletionCondition` 在 field 下 |
| 一票否决 | 任一用户 reject（submitType=20） | `1 / PARALLEL` | `ONE_VOTE_VETO`（仅当配置时生效；剩余成员废弃） |

> ⚠️ **修正（2026-09-17 实测 05-countersign-parallel）**：原表写 PARALLEL "任一通过即流转"，实测**全员通过才流转**。`engine.py:121-123` 完成任务后检查 `find_doing_tasks`，有 doing 直接 return 不流转。剩下成员 taskState 仍 10 (DOING)，由后续完成者继续推进；最后一个完成时所有 doing 已清空才往下走。

---

## 6. 关键约束（设计时必检）

| # | 约束 | 出处 |
| --- | --- | --- |
| 1 | 顶层 `name` 全局唯一 | `./docs/flow.md §2` |
| 2 | 节点 id 不含空格 / `-` / 中文 | Java 端兼容性 |
| 3 | 流程图必须 `start` 开 / `end` 收 | `./docs/flow.md §3.1` |
| 4 | decision 出边按顺序评估，首个真值即流转 | `./docs/flow.md §3.4` |
| 5 | `performType=1` 必须配 `countersignType` | `./docs/flow.md §3.3` |
| 6 | `countersignCompletionCondition` 两位置：`properties` 根 或 `properties.field`（⚠️ 引擎仅识别 `ONE_VOTE_VETO` 字符串；其他条件由 `RatioCapableEngine` 扩展支持） | `./docs/flow.md §3.3` |
| 7 | `assignmentHandler` 与 `assignee` 互斥；同时写则 handler 优先 | `./docs/flow.md §6` |
| 8 | 操作人 `u_*` 只进执行上下文，不写回实例 | `./docs/flow.md §7` |
| 9 | 实例变量 `f_*`（发起时） vs `tf_*`（执行时）分工 | `./docs/flow.md §7` |
| 10 | 字段权限码 `1`=只读 `2`=编辑 `3`=隐藏 | `./docs/flow.md §5.1` |
| 11 | `instanceUrl` 用于前端发起跳转 | `./docs/flow.md §2` |
| 12 | 顶层 `type` 默认 `approval`，`business` 见样例 10 | `./docs/flow.md §2` |
| 13 | **节点 id 唯一**（FIX-T31 自动校验） | `./docs/BUGS.md §58` |
| 14 | **汇合点用 join 节点**（FIX-T35 修复后可选；join 仍推荐） | `./docs/BUGS.md §27,§30` |
| 15 | ~~决策 expr 单 key 单 op~~（v1.9.0 FIX-T37 已支持 `&&`/`\|\|`/复合条件，详见 `./docs/BUGS.md §20`） | `./docs/BUGS.md §20` |
| 16 | **`PERMISSION_*` 字段必须用 `PERMISSION_f_<name>` 前缀** | `./docs/BUGS.md FIX-DOC-1` |
| 17 | **`submitType=2/3/4/6` 走 facade 不走 decision** | `./docs/BUGS.md §20` |
| 18 | ~~不要依赖 custom 节点 clazz/methodName~~（v1.9.0 FIX-T38 已通过 `EngineExtensions.custom_handler_registry` 实现；handler 签名 `async def(node, inst, vars_, args) -> Any`） | `./docs/BUGS.md §16` |
| 19 | **`preInterceptors` 静默未生效，用 `postInterceptors`** | `./docs/BUGS.md §34` |
| 20 | **surrogate 不自动展开 todoList**（手动 addCandidate） | `./docs/BUGS.md §40` |
| 21 | **节点 id 命名规范**（FIX-T34 deploy 自动校验） | `./docs/BUGS.md §93` |

> ⚠️ 约束 #13-#20 来自 `./docs/BUGS.md`，是 BDD 实战中**反复踩坑**的约束。设计前**必读**。

---

## 7. 反模式与典型坑

| 坑 | 表现 | 修复 |
| --- | --- | --- |
| 决策节点所有 `expr` 都不满足 | 引擎兜底走第一条出边 | 加默认边 `expr=""` 或显式兜底分支 |
| ~~决策 `expr` 引用 `variables.amount` 失败~~ | **v1.6.0 FIX-T3 已修复**：Python SimpleExprEvaluator 直接读 vars_，OGNL `#var` 风格即可，**不需要 `#variables.xxx` 嵌套路径** | 用 `#amount>=5000`；如需 f_ 前缀，用 `#f_amount>=5000`（实测有效，详见 `known-issues.md §47 / §59`） |
| `performType` 字符串 "1" 但 `countersignType` 漏配 | 子任务生成但完成逻辑乱 | 引擎容错解析，但 `countersignType` 必须给 |
| `countersignCompletionCondition` 写 `field` 但 assignees 全是变量 | 条件永远不评估 | 改用根 `properties` 写，或确保 field.candidateUsers 非空 |
| `assignmentHandler` 拼写错（大小写） | 引擎走默认 handler = `inst.operator` | 严格照 `./docs/flow.md §6` FQCN |
| `assignmentHandler` 用 `com.jeeflow.*` 前缀 | **FQCN 错误**：Python 引擎 FQCN 实际为 `com.mldong.jeeflow.interceptor.impl.OrgUserAssignmentHandlers$TaskRoleAssigneeHandler`（注意 `$`） | 详见 `known-issues.md §67` |
| `TaskRoleAssigneeHandler` 配置 `properties.roleCode` | **字段被忽略**：handler 实际用 `node.id` 作为 role_code | 节点 id 必须等于 SPI `DEMO_ROLE_TO_USERS.json` 的 key，详见 `known-issues.md §68` |
| 节点 `form: ""` 但后续字段回写 | `args` 没字段 | 让 form 为 None 或省略，提交时也只给 `u_*` |
| 发起人 `u_realName` 想每次改 | 引擎恒以发起人为准 | 设计上不覆盖 |
| 测试中 operator 与 assignee 解析错 | `inst.operator` 取不到 | 启动时必传 `args.u_userId` |
| 会签串行下被中断 | `submitType != 0` 时引擎忽略完成条件 | 测试时保持 `submitType=0` 触发"通过" |
| 测试用 `/wf/processInstance/start` / `/wf/task/page` 等未登记 action | 404 或路由不命中 | 严格按 §5.1 速查表选用 action |
| WIP JSON 直接写到 `./flows/` | 与稳定样例混在一起，无法区分 | 先写 `./tdd/<key>.json`，测试稳定后再 cp 晋升 |
| 测试通过但没写 `./tdd/test_<key>_<YYYYMMDDHHMMSS>.md` | 复测 / 移交时无记录 | §3.2 step 8 是必做项 |
| `assignmentHandler` 用 SPI 角色但 `DEMO_ROLE_TO_USERS.json` 没装该 role | **v1.8.0 FIX-T17 改进**：原静默返回 []，现抛 `ValueError(... SPI 角色匹配为空)` 让 runner 立即定位 | 在 `properties.roleCode` 显式声明，或向 SPI 包补充 role 映射（详见 `known-issues.md §71`） |
| 流程顶层 `postInterceptors: "XXX"` 但 main.py 没注册 XXX | **vendor/jeeflow/engine.py:_resolve_interceptors** 抛 `ValueError(拦截器未注册: XXX)` | 在 `main.py` `EngineExtensions(interceptor_registry={...})` 注册（详见 `known-issues.md §72`） |
| custom 节点 handler 未注册 | **v1.9.0 FIX-T38 改进**：原 F1X-T17 静默 raise，现抛 `ValueError(handler 未注册: ...)` 让 runner 立即定位 | 在 `main_common.py:build_custom_handlers` 注册 `EngineExtensions.custom_handler_registry`（详见 `known-issues.md §16`） |
| `assignmentHandler` 用 `com.jeeflow.*` 前缀（应为 com.mldong.*） | 引擎未注册该 FQCN，raise `handler 未注册` | 严格使用 `com.mldong.jeeflow.interceptor.impl.*` 完整路径（详见 `known-issues.md §67`） |
| `decision` 所有出边 `expr` 都为 False | 兜底走第一条边 | 加默认边 `expr=""`（详见 §3.4） |
| 节点 id 含空格/`-`/中文 | **v1.9.0 FIX-T34 已修复**：deploy 时 regex 拒绝 `^[A-Za-z0-9_]+$` 以外的 id | 用纯字母/数字/下划线命名（详见 `known-issues.md §93`） |
| 测试中调用 `task/processInstance/start` 而非 `startAndExecute` | API 不在 §5.1 速查表，返回 404 | 严格按 §5.1 action 名调用 |

---

## 8. 调试流程

1. **先复现** — 重复设计 Agent 给的 JSON，部署、启动、走完
2. **对照预期** — `approvalRecord` 期望节点顺序 vs 实际
3. **看 `highLight`** — 当前节点是否预期
4. **查 `bizData`** — 实例变量是否注入；`u_*` 是否非持久化
5. **回查文档** — `./docs/flow.md §3.3-§3.5` 节点字段语义、`./docs/actions.md §X` action 行为；如需查 jeeflow 内部行为，可读 `vendor/jeeflow/*.py`（项目内嵌，**可修改**）

必要时重启 uvicorn（不改代码）：

```bash
pkill -f 'main_pg\.py' 2>/dev/null
sleep 1
# 重新拉起（参考 /tmp/opencode/start_uvicorn.sh 模式，PPID=1）
# /tmp/opencode/start_uvicorn.sh 是项目外的 launcher 脚本（先前会话固化），
# 不属于项目目录；本约束不要求把它的路径改成相对形式。
```

---

## 9. 速查引用

| 问题 | 章节 |
| --- | --- |
| 顶层 JSON 怎么写 | `./docs/flow.md §2` |
| 任务节点 properties 全字段 | `./docs/flow.md §3.3` |
| 决策节点 properties | `./docs/flow.md §3.4` |
| custom 节点 properties | `./docs/flow.md §3.5` |
| 边 properties 怎么写 | `./docs/flow.md §4` |
| 节点 / 边命名约定 | `./docs/flow.md §4a` |
| 字段权限 | `./docs/flow.md §5` |
| 7 个内置 handler | `./docs/flow.md §6` |
| 引擎变量 KEY | `./docs/flow.md §7` |
| 15 个样例索引 | `./docs/flow.md §8` |
| TDD 目录使用约定 | `./tdd/README.md` |
| 47 个 action 路由 + curl | `./docs/actions.md §X` |
| 一键重置测试环境 | §5.2.5（`/api/reset`，不在 action 清单） |
| **存量 BUG + 已知限制** | **`./docs/BUGS.md`（设计前必读！）** |
| **流程图自检清单** | **`./docs/BUGS.md` 末尾（部署前逐项检查）** |
| **节点 id 命名规范** | **`./docs/known-issues.md §93`（FIX-T34）** |
| 已知问题详细说明 | `./docs/known-issues.md §X` |

---

## 9.5 BUGS.md 使用指南

`./docs/BUGS.md` 是**流程设计者的必读文档**，分三部分：

### 第一部分：27 个 BUG 报表

| 内容 | 用途 |
|------|------|
| **27 个已修复 BUG**（FIX-T1~T38） | 知道引擎已支持的能力 + 修复时间 |
| **0 个仍存 BUG**（v1.9.0 2026-09-19 起） | — |

> **v1.9.0 里程碑（2026-09-19）**：27 个 BUG 全部修复，包含 §16 / §20 / §27 / §52 等历史顽疾。

### 第二部分：5 个已知限制

**不是 BUG，但**引擎能力边界**，设计时必须避开：

| § | 限制 | 必看理由 |
|---|------|----------|
| §30 | join→end 链路可能不触发 | join 后必须接 task 节点 |
| §32 | ROLLBACK_TO_OPERATOR 跳首任务 | 不要依赖"驳回必经中间节点" |
| §34 | preInterceptors 静默 | 用 postInterceptors 代替 |
| §40 | surrogate 不展开 todoList | 委托后手动 addCandidate |
| §46 | decisionHandler FQCN 未实现 | 嵌套 decision 代替 |

> v1.9.0 之前 §16（custom 节点）+ §20（decision 复合条件）属已知限制；FIX-T37/T38 后已升级为已修 BUG。

**每个限制都附"不要做"反例 + "替代方案"正例**，照搬正例即可安全设计。

### 第三部分：16 项流程图设计自检清单

部署前**逐项勾选**：
- 节点 id 唯一（FIX-T31 deploy 自动校验，但有错先报）
- 汇合点用 join 节点（避免 §30）
- 决策 expr 可写 `&&`/`||`/复合条件（v1.9.0+ FIX-T37）
- PERMISSION_* 前缀
- 字段权限码 1/2/3
- handler FQCN 用 `com.mldong.*`
- TaskRoleAssigneeHandler 用 node.id 作为 role_code
- 等等

### 使用时机

| 阶段 | 必读章节 |
|------|----------|
| **设计前** | 已知限制（§30-§46）+ 自检清单 |
| **写 JSON 时** | 自检清单 16 项 |
| **测试中遇 BUG** | 存量 BUG 报表（找类似 FIX-T 编号） |
| **测试仍失败** | 详细 `./docs/known-issues.md §X` |

### 错误用法（禁止）

- ❌ **不读 BUGS.md 直接写流程**：必然撞到 §30 等限制
- ❌ **遇到 BUG 不查 BUGS.md**：可能用已修复的旧 workaround 重新踩坑
- ❌ **自检清单不勾选就 deploy**：可能因节点 id 重复/权限 key 错等问题被拒

---

---

## 10. 完成定义

设计 Agent 自检清单（提交前必检）：

- [ ] **已读 `./docs/BUGS.md`**：避开了 5 个已知限制（§30/§32/§34/§40/§46）
- [ ] **已勾选 BUGS.md 自检清单 16 项**：节点 id 唯一 / 汇合点用 join / 决策 expr 可用 `&&`/`||`（v1.9.0+）/ PERMISSION_* 前缀 / handler FQCN `com.mldong.*` 等
- [ ] JSON 文件落在 `./tdd/<key>.json`（**不是** `./flows/`）
- [ ] JSON 通过 `python -m json.tool` 校验
- [ ] 节点 id / 边 id 符合命名约定
- [ ] 会签配齐 `performType + countersignType + countersignCompletionCondition`（按放置位置）
- [ ] 候选人 / 字段权限 / 表单 key 已声明
- [ ] 与最近一个相似样例做了 diff，确认改动点正确

测试 Agent 自检清单（TDD 闭环）：

- [ ] **WIP 文件位置**：JSON 在 `./tdd/<key>.json`（不是 `./flows/`）
- [ ] uvicorn 起在 8101，`/wf/processInstance/stats/overview` 返回 `code:0`
- [ ] `processDesign/save` + `processDesign/deploy` 返回 `code:0`，版本号 +1
- [ ] `processInstance/startAndExecute` 返回 `processInstanceId`
- [ ] 走完所有 task（用 `processTask/todoList` + `processTask/execute`），`processInstance/detail` 显示 `state==20`（`InstanceState.DONE`）
- [ ] `approvalRecord` 节点顺序与设计一致
- [ ] `bizData` 实例变量符合预期（`u_*` 仅启动时写，`f_*` 持久化）
- [ ] 所有调用 action 名均在 §5.1 速查表内（不得使用未登记的 action）
- [ ] **测试日志落盘**：写了 `./tdd/test_<key>_<YYYYMMDDHHMMSS>.md`，含 curl 命令 + 每次请求/响应片段 + 校验结论
- [ ] **环境重置**：必要时调用过 `/api/reset` 且响应 `code:0`（按需，非强制）
- [ ] **文档同步**：若发现新字段语义 / 边界条件，已追加到 `./docs/flow.md` 对应节
- [ ] **晋升决策**：稳定样例 cp 到 `./flows/<key>.json` 并在 `./tdd/test_<key>_<YYYYMMDDHHMMSS>.md` 顶部标注「已晋升」
