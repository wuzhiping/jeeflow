# AGENTS.md — 流程设计与测试协作指南

本指南面向「流程设计 Agent」与「流程测试 Agent」。所有动作以仓库内已有文档为准，不得自由发挥。

---

## 1. 角色与边界

| 角色 | 目标 | 主要产物 |
| --- | --- | --- |
| 设计 Agent | 根据业务需求产出可被引擎解析的流程 JSON | `flows/<name>.json`（可新建） |
| 测试 Agent | 把 JSON 部署到引擎、启动实例、走完审批流并核验 | `docs/test_<name>.md`（curl 脚本与日志）或临时脚本 |

**硬约束（来自 `AGENTS.md` §2.6）**：

- 仅修改 `/opt/jupyter/src/RD/projects/jeeFlow/main_pg.py`（其余代码视为只读）
- 不得安装依赖；不得访问项目目录外
- 进度仅在当前会话维护，不得落盘

---

## 2. 必读文件清单

| 文件 | 内容 | 何时读 |
| --- | --- | --- |
| `docs/flow.md` | 流程 JSON 完整规范（9 节 + 速查） | 设计前读全文；测试中遇到歧义回查 §4-§6 |
| `docs/actions.md` | 47 action + 路由解析 + 47 条 curl 模板（端口 8101） | 测试时按 action 名查表 |
| `flows/*.json` | 15 个真实样例（01-13） | 设计时挑最相似的样例 fork |
| `main_pg.py` | 唯一可变文件（含 lifespan、wrap、helpers） | 仅当修改代码时读 |
| `seed_business.py` | 演示数据生成（不写 flow JSON） | 仅当需要重建业务表数据时 |
| `docs/pg_schema.sql` | 真实 PostgreSQL 表 DDL | 查字段含义 |

**测试 Agent 还需读**：

- `/opt/jupyter/src/RD/projects/jeeFlow/.venv/lib/python3.12/site-packages/jeeflow/engine.py`（常量、execute_task、decision 评估）
- `/opt/jupyter/src/RD/projects/jeeFlow/.venv/lib/python3.12/site-packages/jeeflow/facade.py`（deploy、start、completeTask 等方法）

---

## 3. 设计 Agent 工作流

### 3.1 输入约束

调用方必须明确：

1. 流程 key（顶层 `name`）—— 全局唯一、字母数字下划线
2. 流程类型（`approval` / `business`）
3. 节点列表（顺序 + 类型 + 处理人 + 表单）
4. 分支条件（若用决策）
5. 是否需要会签 / 驳回 / 自定义节点

### 3.2 设计步骤

```
1) 列出节点序列（含 start / end）
2) 选择节点类型（start / task / decision / fork / join / custom / end）
3) 写 properties（按 docs/flow.md §3.3-§3.5）
4) 写边 properties（decision 出边 expr / 其他边可空）
5) 文件落地到 flows/<key>.json
6) python -c "import json; json.load(open('flows/<key>.json'))"  语法校验
7) （可选）人工对照 §4 模板逐行核对
```

### 3.3 节点 id / 边 id 命名

参见 `docs/flow.md §4a`。**禁止**节点 id 含空格 / `-` / 中文（引擎底层有部分宽限，但跨语言 Java 端会触发键映射问题）。

---

## 4. 设计模板（基于 15 个样例）

| 业务场景 | 推荐样板 | 关键字段 |
| --- | --- | --- |
| 申请人→上级→结束 | `flows/01-simple.json` | apply=`applicant`、task1=`leader`、`field.PERMISSION_*` |
| 多层审批 | `flows/02-multi-task.json` | 三个 task 节点串行 |
| 金额分支 | `flows/03-decision-expr.json` | decision1 + 两出边 expr `amount>1000` / `amount<=1000` |
| 并行审批 + 汇合 | `flows/04-fork-join.json` | fork1→taskA/taskB→join1；taskB `taskType:1` |
| 并行会签（多人同时审） | `flows/05-countersign-parallel.json` | `performType=1, countersignType=PARALLEL`，assignee 多值 |
| 串行会签（按顺序审） | `flows/06-countersign-sequential.json` | `countersignType=SEQUENTIAL` |
| 比例会签 | `flows/07-countersign-ratio.json` | `countersignCompletionCondition: "#nrOfCompletedInstances==2"`（放 field 内） |
| 一票否决会签 | `flows/13-countersign-one-vote-veto.json` | `countersignCompletionCondition: "ONE_VOTE_VETO"` |
| 自定义节点 | `flows/08-custom-node.json` | `clazz + methodName + args + val` |
| 驳回路径 | `flows/09-with-reject.json` | submitType=Reject 走 reject 边 |
| 业务流 + 拦截器 | `flows/10-mixed-mode.json` | 顶层 `preInterceptors/postInterceptors`；`type: "business"` |
| 处理人为变量 | `flows/11-assignee-vars.json` | `assignee: "deptLeader"` / `"userA,userB"` |
| 内置 handler 全部列示 | `flows/11-assignment-handler.json` | 7 个 FQCN（见 `docs/flow.md §6`） |
| 候选人分页 | `flows/12-candidate-page.json` | 节点级 `candidateUsers/candidateGroups`（properties 根下） |

**复合场景**：`flows/08-countersign-sequential-approve.json`（串行会签后并联 approve）。

---

## 5. 测试 Agent 工作流

### 5.1 启动 uvicorn

端口：**8101**（参见 `docs/actions.md §1`）。

外部 launcher 已固化（PPID=1，`setsid nohup & disown`，详见先前 `/tmp/opencode/start_uvicorn.sh` 经验）。**禁止**用 inline `nohup &` —— watchdog 会 SIGKILL 连带进程。

### 5.2 健康检查

```bash
curl -s http://127.0.0.1:8101/wf/overview | jq
# 期望：{ "code": 0, "data": { ... }, "msg": "成功" }
```

### 5.3 部署流程（设计器 → 定义）

```bash
# Step A：保存设计（含 content）
curl -s -X POST http://127.0.0.1:8101/wf/processDesign/save \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "test-simple",
    "displayName": "测试-简单审批",
    "type": "approval",
    "content": '"$(cat flows/01-simple.json | jq -c . | sed 's/"/\\"/g')"'
  }'

# Step B：取设计 id（返回 data.id）
DESIGN_ID=...

# Step C：部署（生成 wf_process_define）
curl -s -X POST http://127.0.0.1:8101/wf/processDesign/deploy \
  -H 'Content-Type: application/json' \
  -d "{\"id\": $DESIGN_ID}"
```

`processDesign/deploy` 内部调用 `facade._deploy`（`facade.py:186-202`），按 `name` 自动 `+1` version。

### 5.4 启动流程实例

```bash
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/start \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "simple",
    "operator": "user1",
    "title": "测试-简单审批-001",
    "args": {
      "submitType": 0,
      "f_leaveType": "事假",
      "days": 3,
      "u_userId": "user1",
      "u_realName": "用户1"
    }
  }'
```

返回 `data.processInstanceId`（数字）。所有 id 字段出口会被 `_stringify_ids` 转字符串。

### 5.5 完成任务

```bash
# 取 todo 列表
curl -s -X POST http://127.0.0.1:8101/wf/task/page \
  -H 'Content-Type: application/json' \
  -d '{"pageNum": 1, "pageSize": 20}'

# 取任务 id 后提交
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/completeTask \
  -H 'Content-Type: application/json' \
  -d '{
    "taskId": <TASK_ID>,
    "submitType": 0,
    "operator": "leader",
    "args": { "submitType": 0, "u_userId": "leader" }
  }'
```

### 5.6 校验

```bash
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/detail \
  -H 'Content-Type: application/json' \
  -d '{"id": <INSTANCE_ID>}'

curl -s -X POST http://127.0.0.1:8101/wf/processInstance/approvalRecord \
  -H 'Content-Type: application/json' \
  -d '{"id": <INSTANCE_ID>}'

curl -s -X POST http://127.0.0.1:8101/wf/processInstance/highLight \
  -H 'Content-Type: application/json'  -d '{"id": <INSTANCE_ID>}'

# 流程图高亮（看当前节点位置）
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/highLight \
  -H 'Content-Type: application/json' \
  -d '{"id": <INSTANCE_ID>}'

# 实例变量（含发起人/操作人/流程变量）
curl -s -X POST http://127.0.0.1:8101/wf/processInstance/bizData \
  -H 'Content-Type: application/json' \
  -d '{"id": <INSTANCE_ID>}'
```

### 5.7 字段权限核验

启动实例时传 `PERMISSION_f_<field>=1`（只读）或 `2`（隐藏）。完成后查 `bizData`：
- 只读字段：值回传，但任务行不允许再写
- 隐藏字段：值丢弃，前端不可见

### 5.8 会签测试

| 类型 | curl 操作 | 预期 `performType/countersignType` | 预期完成条件 |
| --- | --- | --- | --- |
| 并行 | 三用户同时 `completeTask` | `1 / PARALLEL` | 任一通过即流转 |
| 串行 | 三个用户按顺序 `completeTask` | `1 / SEQUENTIAL` | 仅最后一个通过即流转 |
| 比例 | N 个用户中 K 个通过 | `1 / PARALLEL` | `countersignCompletionCondition` 在 field 下 |
| 一票否决 | 任一用户 reject | `1 / PARALLEL` | `ONE_VOTE_VETO` |

---

## 6. 关键约束（设计时必检）

| # | 约束 | 出处 |
| --- | --- | --- |
| 1 | 顶层 `name` 全局唯一 | `facade._deploy` 校验 |
| 2 | 节点 id 不含空格 / `-` / 中文 | Java 端兼容性 |
| 3 | 流程图必须 `start` 开 / `end` 收 | 引擎拓扑检查 |
| 4 | decision 出边按顺序评估，首个真值即流转 | `engine.py:355-375` |
| 5 | `performType=1` 必须配 `countersignType` | `engine.py:282, 387` |
| 6 | `countersignCompletionCondition` 两位置：`properties` 根 或 `properties.field` | 引擎双路径解析 |
| 7 | `assignmentHandler` 与 `assignee` 互斥；同时写则 handler 优先 | `builtin.py` |
| 8 | 操作人 `u_*` 只进执行上下文，不写回实例（issues/97） | `engine.py:200-220` |
| 9 | 实例变量 `f_*`（发起时） vs `tf_*`（执行时）分工 | `engine.py:8-40` |
| 10 | 字段权限码 `1`=只读 `2`=隐藏 | `engine.py:200-220` |
| 11 | `instanceUrl` 用于前端发起跳转 | 顶层可选 |
| 12 | 顶层 `type` 默认 `approval`，`business` 见样例 10 | `facade.py:204-220` |

---

## 7. 反模式与典型坑

| 坑 | 表现 | 修复 |
| --- | --- | --- |
| 决策节点所有 `expr` 都不满足 | 引擎兜底走第一条出边 | 加默认边 `expr=""` 或显式兜底分支 |
| `performType` 字符串 "1" 但 `countersignType` 漏配 | 子任务生成但完成逻辑乱 | 引擎容错解析，但 `countersignType` 必须给 |
| `countersignCompletionCondition` 写 `field` 但 assignees 全是变量 | 条件永远不评估 | 改用根 `properties` 写，或确保 field.candidateUsers 非空 |
| `assignmentHandler` 拼写错（大小写） | 引擎走默认 handler = `inst.operator` | 严格照 `docs/flow.md §6` FQCN |
| 节点 `form: ""` 但后续字段回写 | `args` 没字段 | 让 form 为 None 或省略，提交时也只给 `u_*` |
| 发起人 `u_realName` 想每次改 | 引擎恒以发起人为准 | 设计上不覆盖 |
| 测试中 operator 与 assignee 解析错 | `inst.operator` 取不到 | 启动时必传 `args.u_userId` |
| 会签串行下被中断 | `submitType != 0` 时引擎忽略完成条件 | 测试时保持 `submitType=0` 触发"通过" |

---

## 8. 调试流程

1. **先复现** — 重复设计 Agent 给的 JSON，部署、启动、走完
2. **对照预期** — `approvalRecord` 期望节点顺序 vs 实际
3. **看 `highLight`** — 当前节点是否预期
4. **查 `bizData`** — 实例变量是否注入；`u_*` 是否非持久化
5. **回查引擎源码** — `engine.py` 内对应方法（如 `_evaluate_decision` / `execute_task` / `_previous_task_name`）

必要时重启 uvicorn：

```bash
pkill -f 'main_pg\.py' 2>/dev/null
sleep 1
# 重新拉起（参考 /tmp/opencode/start_uvicorn.sh 模式）
```

---

## 9. 速查引用

| 问题 | 章节 |
| --- | --- |
| 顶层 JSON 怎么写 | `docs/flow.md §2` |
| 任务节点 properties 全字段 | `docs/flow.md §3.3` |
| 决策节点 properties | `docs/flow.md §3.4` |
| custom 节点 properties | `docs/flow.md §3.5` |
| 边 properties 怎么写 | `docs/flow.md §4` |
| 节点 / 边命名约定 | `docs/flow.md §4a` |
| 字段权限 | `docs/flow.md §5` |
| 7 个内置 handler | `docs/flow.md §6` |
| 引擎变量 KEY | `docs/flow.md §7` |
| 15 个样例索引 | `docs/flow.md §8` |
| 47 个 action 路由 + curl | `docs/actions.md §X` |

---

## 10. 完成定义

设计 Agent 自检清单：

- [ ] JSON 通过 `python -m json.tool` 校验
- [ ] 节点 id / 边 id 符合命名约定
- [ ] 会签配齐 `performType + countersignType + countersignCompletionCondition`（按放置位置）
- [ ] 候选人 / 字段权限 / 表单 key 已声明
- [ ] 与最近一个相似样例做了 diff，确认改动点正确

测试 Agent 自检清单：

- [ ] uvicorn 起在 8101，`/wf/overview` 返回 `code:0`
- [ ] `processDesign/deploy` 返回 `code:0`，版本号 +1
- [ ] `processInstance/start` 返回 `processInstanceId`
- [ ] 走完所有 task，`processInstance/detail` 显示 `state==7`（已完成）
- [ ] `approvalRecord` 节点顺序与设计一致
- [ ] `bizData` 实例变量符合预期（`u_*` 仅启动时写，`f_*` 持久化）
