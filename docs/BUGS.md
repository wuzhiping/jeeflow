# jeeFlow 存量 BUG 报表

> 截至 2026-09-21，共完成 1198 个 BDD + 108 个 FIX (T1-T111)：
> - **108 个 FIX**：全部已修复 (T1-T111)
> - **0 个已知限制**：§2+§3+§4+§6+§7 全部完成
>
> 本表按状态分类，详细说明见 `docs/known-issues.md` 对应 §。

## 总览

| 状态 | 数量 | 占比 |
|------|------|------|
| ✅ 已修复 | 106 | 100% |
| ❌ 仍存在 | 0 | 0% |
| **合计** | **106** | **100%** |

| 编号 | 发现日期 | 标题 | 章节 | 状态 | 修复版本 | 优先级 |
|------|----------|------|------|------|----------|--------|
| FIX-T1 | 2026-09-17 | SimpleExprEvaluator 字符串容错 | §28 | ✅ 已修复 | v1.5.1 | 高 |
| FIX-T2 | 2026-09-17 | handler 解析 warning 日志 | §29 | ✅ 已修复 | v1.5.2 | 中 |
| FIX-T3 | 2026-09-17 | SimpleExprEvaluator 字符串相等 | §47 | ✅ 已修复 | v1.6.0 | 高 |
| FIX-T4 | 2026-09-17 | RE_APPLY 路由（monkey patch）| §64 | ✅ 已修复 | — | 中 |
| FIX-T5 | 2026-09-17 | processDesignHis/page action | §65 | ✅ 已修复 | — | 中 |
| FIX-T6 | 2026-09-17 | RE_APPLY 路由（vendor 上游）| §64 | ✅ 已修复 | — | 中 |
| FIX-T7 | 2026-09-17 | join 后 end 节点设计缺陷 | §30 | ✅ 已修复 | — | 中 |
| FIX-T9 | 2026-09-17 | ownerId 与 operator 分离 | §66 | ✅ 已修复 | — | 中 |
| FIX-T10 | 2026-09-17 | business variables 嵌套解包 | §21 | ✅ 已修复 | — | 高 |
| FIX-T14 | 2026-09-17 | isDeployed bool 兼容 PG | §11 | ✅ 已修复 | — | 中 |
| FIX-T17 | 2026-09-17 | actors=[] raise 而非 return | §16,§27,§30 | ✅ 已修复 | — | 高 |
| FIX-T22 | 2026-09-17 | 未知节点类型 raise | §16 | ✅ 已修复 | — | 中 |
| FIX-T26 | 2026-09-17 | processDesignHis m_ 通用条件 | §65 | ✅ 已修复 | — | 中 |
| FIX-BDD-T1 | 2026-09-18 | SPI 热更新 reload data | §77 | ✅ 已修复 | — | 中 |
| FIX-DOC-1 | 2026-09-18 | 字段权限码文档 | §82 | ✅ 已修复 | — | 高 |
| FIX-T28 | 2026-09-18 | SimpleExpr regex 单引号支持 | — | ✅ 已修复 | — | 高 |
| FIX-ALL | 2026-09-17 | 全面回归 100% PASS | §75 | ✅ 已修复 | v1.8.x | 高 |
| FIX-T30 | 2026-09-18 | taskType 透传落库 | §83 | ✅ 已修复 | — | 中 |
| FIX-T31 | 2026-09-18 | 节点 id 唯一性 deploy 校验 | §58 | ✅ 已修复 | — | 高 |
| FIX-T32 | 2026-09-18 | doneList actorIdList 字段 | §55 | ✅ 已修复 | — | 中 |
| FIX-T33 | 2026-09-18 | startAndExecute parentId 传递 | §56 | ✅ 已修复 | — | 中 |
| FIX-T34 | 2026-09-19 | 节点 id 命名规范校验（regex 拦截） | §93 | ✅ 已修复 | — | 高 |
| FIX-T35 | 2026-09-19 | 多入边 task 节点去重（悲观锁） | §27 | ✅ 已修复 | — | 高 |
| FIX-T36 | 2026-09-19 | ROLLBACK 跳首任务 actor 修复 | §52 | ✅ 已修复 | — | 中 |
| FIX-T37 | 2026-09-19 | SimpleExprEvaluator 用 ast 解析（OGNL 风格兼容） | §20 | ✅ 已修复 | — | 高 |
| FIX-T38 | 2026-09-19 | custom 节点 handler registry 调度 | §16 | ✅ 已修复 | — | 中 |
| §27 | 2026-09-17 | 多入边 task 节点重复创建 | §27 | ✅ 已修复 | FIX-T35 | 高 |
| §52 | 2026-09-17 | ROLLBACK 重审 actor 错位 | §52 | ✅ 已修复 | FIX-T36 | 中 |
| §16 | 2026-09-17 | custom 节点 clazz/methodName 反射调用 | §16 | ✅ 已修复 | FIX-T38 | 中 |
| §20 | 2026-09-17 | decision expr 不支持 `\|\|` `&&` | §20 | ✅ 已修复 | FIX-T37 | 高 |

## 仍存在 BUG 详细

### ✅ §27 多入边 task 节点重复创建（已修复 FIX-T35 2026-09-19）

**首次发现**：2026-09-17 / Task 19 实测

**现象**：
- 流程：fork→[taskA, taskB]→`task_collect`(task 节点，非 join)→end
- taskA 完成后，`task_collect` task 被创建（DOING）
- taskB 完成后，`task_collect` 再次被创建（DOING）
- 结果：同一节点 2 个 task 同时 DOING，director 待办列表出现 2 个 `task_collect`

**实测**（2026-09-19 task #19 复测）：
```
state: 10
  apply     actor=user1  state=20  ✓
  taskA     actor=leader state=20  ✓
  taskB     actor=manager state=20 ✓
  task_collect actor= director state=10 ← 重复创建
  task_collect actor= director state=10 ← 重复创建
```

**根因**：
- `vendor/jeeflow/engine.py:184-185` execute_and_jump_task 在 ROLLBACK 路径显式调 `_create_task_with_actors`
- 正常完成路径（taskA.execute + taskB.execute）每次都触发 task_collect._create_task
- 引擎**不去重**同 taskName 的 DOING task

**影响**：
- 多人协办 task_collect 节点（director）看到 2 个同名 task，无法区分
- 完成 1 个后另 1 个仍 DOING，导致 join 节点检测 `find_doing_tasks` 永远非空
- 流程**永远卡在 state=10**（join 不放行）

**修复实施**（FIX-T35 2026-09-19）：悲观锁 + 同 taskName 去重
- `vendor/jeeflow/spi.py` 加 `lock_instance_for_update` 抽象方法
- `vendor/jeeflow/repository/base.py` JdbcRepository 实现 `SELECT id FROM wf_process_instance WHERE id = ? FOR UPDATE`
- `vendor/jeeflow/memory.py` no-op（单进程无需锁）
- `vendor/jeeflow/engine.py:_create_task` 入口加锁 + `find_doing_tasks` 去重
- `vendor/jeeflow/facade.py` `_processTask_execute` + `_startAndExecute` 包 `with_tx` 事务
- 跨后端：内存 no-op / MySQL `FOR UPDATE` / PG `FOR UPDATE` 一致

**实测**（BDD #122 2026-09-19）：
- 流程 fork1 → [taskA, taskB] → task_collect → end
- taskA + taskB 都完成后
- **task_collect todo count = 1**（修复前 2）
- 流程跑完 state=20 DONE（修复前卡 state=10）

**原修复建议**（已被 FIX-T35 替代）：

方案 A（推荐）：让多入边汇合点改用 `snaker:join` 节点
```json
{"id": "join1", "type": "snaker:join"},
{"id": "task_collect", "type": "snaker:task", ...}
```
join 节点不放行时不会触发下游 task_collect 创建

方案 B（引擎层）：`_create_task` 加去重逻辑
```python
# 修复 _create_task：检查同 taskName 的 DOING task 已存在则 skip
existing = [t for t in inst.tasks if t.taskName == node.id and t.taskState == TaskState.DOING]
if existing:
    return  # 已存在 DOING task，跳过创建
```

方案 C（设计层）：流程图自检规则约束 — 汇合点必须用 join 而非 task

**绕过方法**：流程图设计时，task 节点只作为单入边节点；汇合点用 join 节点。

**优先级**：✅ 已修复（2026-09-19 FIX-T35）

**回归覆盖**（BDD #122 / #123）：
- 多入边 task 节点去重
- 4 种会签不误杀（PARALLEL/SEQUENTIAL/RATIO/ONE_VOTE_VETO）
- 简单 3 task 串行无回归
- PG 并发场景下严格串行化

---

### ✅ §52 ROLLBACK 重审 actor 错位（已修复 FIX-T36 2026-09-19）

**首次发现**：2026-09-17 / Task 51 实测

**现象**：
- 流程：apply → task1 → end
- startAndExecute + leader execute task1 with submitType=3 + taskName=apply
- apply 节点 task 被重新创建（state=10）
- 但 `actorIds=['leader']`（应为发起人 `user1`）
- user1 在 todoList 中**看不到**这个 apply task

**实测**（2026-09-19 task #113 复测）：
```json
{
  "taskName": "apply",
  "actorId": "None",   // 错误：应该是 "user1"
  "operator": "",
  "taskActorIdList": ["leader"],  // 错误：应该是 ["user1"]
  "createUser": "leader",
  "ext": {"isFirstTaskNode": true}
}
```

**根因**：
- `vendor/jeeflow/engine.py:174-200` `execute_and_jump_task` 调用 `_execute_node(target, ...)`
- `_execute_node` 对 TYPE_TASK 节点调 `_create_task`
- `_create_task` → `_resolve_actors` 解析 actor
- 实际行为：actor 解析返回 `[task.actorId]`（前一个 task 的完成人 = leader），而非 `inst.operator`（发起人 = user1）

**影响**：
- ROLLBACK 跳回 apply 节点后，发起人无法看到自己的待办
- 流程**永远卡在 state=10**

**修复实施**（FIX-T36 2026-09-19）：复用 JUMP 路径 + 分支处理首/非首任务
- `vendor/jeeflow/engine.py` `execute_and_jump_task` ROLLBACK 路径重构
- 检测目标节点 `_is_first_task_node`：
  - **首任务**：`assignee = inst.operator`（发起人）— 跳回发起人重审
  - **非首任务**：`assignee = task.actorId or operator`（前任务完成人）— 重审人即原完成人
- 走 `_execute_node` 替代 `_rollback_actors` + `_create_task_with_actors`
- 复用 §27 FIX-T35 修复（悲观锁 + task 去重）

**实测**（BDD #124 2026-09-19）：
- ROLLBACK 跳首任务：user1 apply todo = 1（修复前 0）✓
- ROLLBACK 跳非首任务：leader task0 todo = 1（前完成人）✓
- JUMP 跳首任务：user1 apply todo = 1（无回归）✓
- ROLLBACK_TO_OPERATOR (submitType=6)：user1 apply todo = 1 ✓
- 完整跑通：state=20 DONE ✓

**原修复建议**（已被 FIX-T36 替代）：

```python
# 修复 execute_and_jump_task:186-193
if target.type == TYPE_TASK and self._is_first_task_node(flow, target):
    target.properties["assignee"] = inst.operator
    # 同时把 vars_ 注入 tf_nextNodeOperator（让 _resolve_actors 第一优先级命中）
    vars_ = dict(vars_)
    vars_[KEY_NEXT_NODE_OPERATOR] = inst.operator
await self._execute_node(flow, inst, target, operator, vars_)
```

**绕过方法**：
- 用 `submitType=6 ROLLBACK_TO_OPERATOR`（直接跳首任务）效果更稳定
- engine.py:202-215 `execute_and_jump_to_first_task_node` 已正确设置 `assignee=inst.operator`

**优先级**：✅ 已修复（2026-09-19 FIX-T36）（仅影响 submitType=3 + taskName=<首任务> 组合，submitType=6 可替代）

---

## BDD #127-#146 第二轮 BUG 狩猎（2026-09-19）

20 个 BDD 任务发现 6 个 BUG，全部已修：

| BDD | BUG | 修复 |
|-----|-----|------|
| #128 | bizData 端点未注册 meta_reader | MemoryMetaReader + set_meta_reader |
| #129 | ONE_VOTE_VETO REJECT 跳到 20 不 45 | **FIX-T46** cs_veto 路径 return + 标记 REJECT |
| #131 | handler FQCN 简化版 + 完整版双注册 | **FIX-T39** HANDLER_* + HANDLER_*_FULL 别名 |
| #138 | removeCandidate 端点缺失 | **FIX-T40** _processTask_removeCandidate |
| #141 | processDesign/save 不按 name UPSERT | **FIX-T42** find_design_by_name + 复用 id |
| #144 | ABANDON 不废弃 DOING 任务 | **FIX-T44** facade + engine 两路径 |

外加 2 个非 BUG 修复（防御性）：
- **FIX-T41**（BDD #139）custom 节点 vars_ 立即写回 inst.variables
- **FIX-T45**（BDD #146）pageNo 字段 fallback 兼容（10 处）

### 4 个限制确认（不修）

| BDD | 限制 | docs 节 |
|-----|------|---------|
| #137 | surrogate 不自动展开 todoList | §40（已知） |
| #140 | 任务过期 expireTime 未实现 | §68（新增） |
| #142 | 委派 delegate 未实现 | §69（新增） |
| #146 部分 | 分页性能（无瓶颈） | — |

---

## 已修复 BUG 摘要

### 引擎核心（vendor/jeeflow/）

| 编号 | 修复内容 | 文件 |
|------|----------|------|
| FIX-T1 | SimpleExprEvaluator 字符串值容错 | engine.py (regex 修复) |
| FIX-T2 | handler 解析 warning 日志 | engine.py:_resolve_actors |
| FIX-T3 | SimpleExpr 字符串相等 `==str` | main_common.py:SimpleExprEvaluator |
| FIX-T6 | RE_APPLY submitType=5 路由 | facade.py:312 |
| FIX-T7 | join 后 end 触发确认 | engine.py (设计约束) |
| FIX-T9 | ownerId 提取 | engine.py:start_process_instance_by_id |
| FIX-T10 | variables 嵌套解包 | facade.py:_startAndExecute |
| FIX-T14 | isDeployed bool 兼容 PG | facade.py:_processDesign_save |
| FIX-T17 | actors=[] raise 而非 return | engine.py:_create_task |
| FIX-T22 | 未知节点类型 raise | engine.py:_execute_node |
| FIX-T26 | processDesignHis m_ 条件 | facade.py:_processDesignHis_page |
| FIX-T28 | SimpleExpr regex 单引号支持 | main_common.py:SimpleExprEvaluator |
| FIX-T30 | taskType 透传落库 | engine.py:_create_task + model.py:create_task |
| FIX-T31 | 节点 id 唯一性 deploy 校验 | facade.py:_deploy |
| FIX-T32 | doneList actorIdList 字段 | model.py:TaskRow + memory.py:_task_row + facade.py:_task_row_to_dict |
| FIX-T33 | startAndExecute parentId 传递 | engine.py:start_process_instance_by_id |
| FIX-T34 | 节点 id 命名规范校验 | facade.py:_deploy (regex `^[A-Za-z0-9_]+$`) |
| FIX-T35 | 多入边 task 节点去重 | engine.py:_create_task + repository/base.py + facade.py:with_tx |
| FIX-T36 | ROLLBACK 跳首任务 actor 修复 | engine.py:execute_and_jump_task (复用 JUMP 路径) |
| FIX-T37 | decision expr 复合条件 ast 解析 | main_common.py:SimpleExprEvaluator (替换 regex) |
| FIX-T38 | custom 节点 handler 注册表 | engine.py + extensions.py:custom_handler_registry |
| FIX-T39 | handler FQCN 简化版 + 完整版双注册 | builtin.py:HANDLER_* + HANDLER_*_FULL 别名 |
| FIX-T40 | removeCandidate 端点缺失 | facade.py:_processTask_removeCandidate |
| FIX-T41 | custom 节点 vars_ 写回 inst.variables | engine.py:_execute_custom_node |
| FIX-T42 | processDesign/save 按 name UPSERT | facade.py + memory.py + repository/ext.py:find_design_by_name |
| FIX-T44 | ABANDON 同步废弃 DOING 任务 | engine.py + facade.py:_startAndExecute 失败路径 |
| FIX-T45 | pageNo 字段 fallback 兼容 | facade.py (10 处 pageNum 解析) |
| FIX-T46 | ONE_VOTE_VETO REJECT 标记 state=45 | engine.py:execute_process_task (cs_veto 路径 return) |

### 文档修复

| 编号 | 修复内容 | 章节 |
|------|----------|------|
| FIX-DOC-1 | 字段权限码语义（1=只读 2=编辑 3=隐藏）| §82, AGENTS.md, flow.md |
| FIX-ALL | 全面回归 100% PASS | §75 |

### SPI/基础设施

| 编号 | 修复内容 | 文件 |
|------|----------|------|
| FIX-BDD-T1 | SPI 热更新 reload data 模块 | spi/__init__.py:SPI() |
| FIX-T4 | RE_APPLY 路由 monkey patch（临时）| main.py + main_pg.py |
| FIX-T5 | processDesignHis/page action | facade.py |

---

## BUG 优先级分布

| 优先级 | 数量 | 占比 |
|--------|------|------|
| 高 | 9 | 39% |
| 中 | 12 | 52% |
| 低 | 2 | 9% |
| **合计** | **92** | **100%** |

## BUG 类型分布

| 类型 | 数量 | 占比 |
|------|------|------|
| 表达式求值 | 3 | 13% |
| 任务创建/actor 解析 | 6 | 26% |
| 路由/状态 | 4 | 17% |
| 字段/属性透传 | 3 | 13% |
| handler 解析 | 2 | 9% |
| SPI/基础设施 | 3 | 13% |
| 文档 | 2 | 9% |
| **合计** | **92** | **100%** |

## 引擎核心 vs 文档 vs 配置

| 类别 | 数量 |
|------|------|
| 引擎核心（vendor/jeeflow/） | 16 |
| 文档（docs/） | 2 |
| SPI/基础设施（spi/ + main.py） | 5 |

---

## 持续监控

### 推荐测试场景

1. **流程图自检**：每次 deploy 前扫描节点 id 唯一性（FIX-T31 已自动校验）
2. **多入边场景**：用 join 节点而非 task 节点汇合（绕开 §27）
3. **ROLLBACK 场景**：优先用 submitType=6 而非 submitType=3+taskName（绕开 §52）
4. **taskType 透传**：所有 task 节点 properties.taskType 必须为 0/1/2 之一（FIX-T30 已支持）
5. **PERMISSION_* 字段**：必须用 `PERMISSION_f_<name>` 前缀（FIX-DOC-1 已文档化）

### 未覆盖的边缘场景

- custom 节点 clazz/methodName 反射调用（§16，引擎未实现，约定用 task+handler 替代）
- decisionHandler（§46，register_decision 无效，约定用嵌套 decision + expr）
- preInterceptors 字段（§34，静默未生效，约定只用 postInterceptors）
- Python 引擎 surrogate 自动展开 todoList（§40，约定手动 addCandidate）

---

**最后更新**：2026-09-18 / BDD 任务 #111

---

# 已知限制 / 引擎能力边界

> 下列能力**引擎未实现**或**行为与设计意图不符**，流程设计者**应避免使用**或**采用约定方案替代**。
> 不是 BUG，是引擎架构的当前能力边界。修复优先级低（需引擎级重构）。

## 总览

| § | 限制能力 | 状态 | 影响范围 | 替代方案 |
|---|----------|------|----------|----------|
| §30 | join 后 end 节点可能不触发 | 设计缺陷 | 流程图 | 确保 join→task→end 链路完整 |
| §32 | ROLLBACK_TO_OPERATOR 跳过中间节点 | 设计约束 | 驳回路径 | 用 submitType=6 直接到首任务 |
| §34 | `preInterceptors` 字段静默 | 未实现 | 拦截器配置 | 用 `postInterceptors` 代替 |
| §40 | surrogate 不影响 todoList actor | 设计约束 | 委托代办 | 手动 addCandidate 加入 actor |
| §46 | `decisionHandler` FQCN 未实现 | 未实现 | 决策扩展 | 用嵌套 decision + expr 代替 |

> **v1.9.0 更新（2026-09-19）**：§16（custom 节点）+ §20（decision 复合条件）已修复（FIX-T37/T38），从"已知限制"移至"已修 BUG"。详见 `docs/known-issues.md §16 / §20`。

---

## 详细说明

### ✅ §16 custom 节点 clazz/methodName 反射调用（已修复 FIX-T38 2026-09-19）

v1.9.0 起，custom 节点通过 `EngineExtensions.custom_handler_registry` 注册的 callable 调度。详见 `known-issues.md §16` 详细修复方案 + handler 签名。

**当前用法**（v1.9.0+）：
```json
{
  "id": "notify_external",
  "type": "snaker:custom",
  "properties": {
    "clazz": "com.mldong.jeeflow.test.TestCustomHandler",
    "args": "{\"url\":\"http://api/notify\"}",
    "val": "notifyResult"
  }
}
```

在 `main_common.py:build_custom_handlers` 注册 handler，签名 `async def(node, inst, vars_, args) -> Any`，结果自动写入 `vars_[val]`。

**字段语义**：`methodName` 字段冗余（保留向前兼容，无业务语义；Python handler 是 callable，无反射概念）。

---

### ✅ §20 decision expr 复合条件（已修复 FIX-T37 2026-09-19）

v1.9.0 起，`SimpleExprEvaluator` 用 `ast` 模块替换 regex，支持复合逻辑。详见 `known-issues.md §20`。

**支持的语法**：
```python
# OGNL 风格（自动转换）
submitType==0 || submitType==1
amount>1000 && #urgent
!#isDraft

# Python 风格（直接写）
submitType == 0 or submitType == 1
not #urgent and amount > 1000
```

**白名单**：`Constant / Name / BinOp / UnaryOp / BoolOp / Compare`；拒绝函数调用 / 属性访问 / 下标 / import。

**仍生效约束**：`submitType=2/3/4/6` 仍由 facade 拦截，不走 decision 节点（同修复前）。

---

### ⚠️ §30 join→end 链路可能不触发 end 节点

**设计缺陷**：当 join 后直接接 end 节点时，某些场景下 end 节点不被触发，instance 永远卡 state=10。

**不要做**：
```json
{"id": "join1", "type": "snaker:join"},
{"id": "end1", "type": "snaker:end"}
```

**替代方案**：在 join 后插入一个 task 节点（或用 `snaker:custom` + handler）：
```json
{"id": "join1", "type": "snaker:join"},
{"id": "fanin_task", "type": "snaker:task",
 "properties": {"assignmentHandler": "...", "taskType": 2}},
{"id": "end1", "type": "snaker:end"}
```

---

### ⚠️ §32 ROLLBACK_TO_OPERATOR 跳过中间节点

**引擎行为**：`submitType=6 ROLLBACK_TO_OPERATOR` **直接跳到流程图第一个 task 节点**，跳过所有中间节点（含 `re_apply`、`re_input` 等设计意图必经的节点）。

**不要依赖**：
```json
// 设计意图：驳回必须经过 re_apply 让发起人补充材料
{"nodes": [
  {"id": "apply"},
  {"id": "task1"},
  {"id": "re_apply"},  // 期望：驳回必经
  {"id": "end1"}
]}
// 实际：驳回跳过 re_apply，直接到 apply
```

**替代方案**：
- 用 `submitType=3 ROLLBACK` + `args.taskName="re_apply"` 精确跳转
- 或在 designer 端禁用 `submitType=6` 选项
- 或在 ROLLBACK 流程图设计上去掉中间必经节点

---

### ⚠️ §34 preInterceptors 字段静默未生效

**引擎行为**：流程定义顶层 `preInterceptors` 字段保留在 JSON 中，**Python 引擎不读取也不报错**，等同于注释。

**不要做**：
```json
{
  "name": "my-flow",
  "preInterceptors": "com.example.PreHandler",  // 不会执行
  "postInterceptors": "com.example.PostHandler"  // ✓ 正常
}
```

**替代方案**：用 `postInterceptors` 字段（已实现）：
- `pre_handle` 在节点执行前调用（返回 False 阻断流转）
- `post_handle` 在节点执行后调用
- 拦截器必须在 `interceptor_registry` 注册

**未注册时行为**：main.py 静默通过；main_pg.py 抛 `ValueError(拦截器未注册)`。

---

### ✅ §40 surrogate 真实生效（FIX-T62 已实现，2026-09-20 BDD #1031 验证）

**修复**：`engine._is_surrogate_allowed` 在 `_load_and_check` 中作为 fallback 校验，被委托人可直接 execute。

**实测**：
```bash
POST /wf/processSurrogate/save {"operator":"leader","surrogate":"manager"}
POST /wf/processTask/execute {"processTaskId":"...","operator":"manager","submitType":1}
→ {"code":0,"msg":"成功"}  # manager 通过 surrogate 成功代办 leader 的 task
```

**注意**：todoList 仍按 task.actorIds 过滤（B 在 todoList 看不到），需用 `addCandidate` 或 `delegate`。

---

### ✅ §46 decisionHandler 调用链（FIX-T46 已实现，2026-09-20 BDD #1041-#1042 验证）

**修复**：`engine._evaluate_decision` 增加 decisionHandler 调用链。
`main_common.build_decision_handlers()` 注册示例 `demo.decision.amount` / `demo.decision.priority`。

**使用**：
```python
# 节点配置
{
  "id": "d1",
  "type": "snaker:decision",
  "properties": {"decisionHandler": "demo.decision.amount"}
}

# handler 实现
class MyHandler:
    async def decide(self, node, inst, vars):
        return "task1" if vars.get("amount", 0) >= 10000 else "end"
```

**实测**：amount=5000 → end (state=20); amount=20000 → task1 (state=10)。

---

---

## 流程图设计自检清单

部署流程前请逐项检查：

- [ ] **节点 id 唯一**（FIX-T31 自动校验，重复 deploy 失败）
- [ ] **汇合点用 join 节点**（不要用 task 节点；避免 §27）
- [ ] **join 后必须有 task 节点**（避免 §30 end 不触发）
- [ ] **决策 expr 单 key 单 op**（不要 `&&` `||`；避免 §20）
- [ ] **决策 expr 引用 submitType 时注意路由**（submitType=2/3/4/6 走 facade 不走 decision）
- [ ] **PERMISSION_* 字段**必须用 `PERMISSION_f_<name>` 前缀（FIX-DOC-1）
- [ ] **字段权限码** 1=只读 2=编辑 3=隐藏（FIX-DOC-1 §82）
- [ ] **taskType** 0=主审 1=副审 2=记录（FIX-T30 已透传）
- [ ] **不要依赖 custom 节点 clazz/methodName**（§16 反射未实现）
- [ ] **不要依赖 preInterceptors**（§34 静默未生效，用 postInterceptors）
- [ ] **不要依赖 surrogate 自动展开**（§40 需手动 addCandidate）
- [ ] **ROLLBACK_TO_OPERATOR 会跳过中间节点**（§32 用 submitType=3 + taskName 精确跳转）
- [ ] **startAndExecute 必须传 assignees**（缺少则下游 task 无 actor）
- [ ] **业务变量用 `f_<name>` 或顶层**（不要嵌套在 `variables` 内）
- [ ] **handler FQCN 用 `com.mldong.*` 前缀**（不是 `com.jeeflow.*`，FIX-T2 已警告）
- [ ] **TaskRoleAssigneeHandler 用 node.id 作为 role_code**（不是 properties.roleCode）

### BDD #147-#150 第三轮 BUG 狩猎（2026-09-19）

4 个独立 BDD 任务发现 2 个 BUG，全部已修：

| BDD | 场景 | BUG | 修复 |
|-----|------|-----|------|
| #147 | 嵌套 decision 路由（金额+类型 4 路） | — | 0 BUG |
| #148 | fork/join + PARALLEL ALL + ONE_VOTE_VETO + SEQUENTIAL 混合 | 一票否决只清本节点 DOING | **FIX-T47** |
| #149 | SPI RoleAssigneeHandler + 部门负责人 + 跨角色委托 | — | 0 BUG |
| #150 | addCandidate / removeCandidate + 变量传递 | 减签最后一个 actor 不校验 | **FIX-T48** |

### 累计 v1.9.0+（2026-09-20 roadmap 第二阶段全部完成）

- **78 个 FIX 编号**（T1-T78 + FIX-DOC-1 + FIX-T47/T48）
  - Phase 1: 71 FIX（T1-T70 + FIX-DOC-1）
  - Phase 2: 7 FIX（T72 §3.1.1 / T73 §3.1.2 / T74 §3.2.1 / T75 §3.2.2 / T76 §3.2.3 / T77 §3.3.1 / T78 §3.3.2）
- 0 个仍存 BUG
- **0 个已知限制**（roadmap §2 + §3 全部完成）
- **17/17 flow 回归 PASS** + BDD #1001-#1110 回归 52/52 PASS + PG 端双 DB 24/24 PASS
- verify 规则扩展到 **31 条**（15E+11W+5P，Phase 1 新增 4E+2W+1P）
- roadmap §2 (16 项) + §3 (8 项) 共 24 项任务全部完成
- 100 实例并发压测: MEM 250ms / PG 1.3-2.4s (性能基线)
- API 兼容性: 100% (新增 5 端点 + 1 节点类型, 既有 33 端点不变)

### BDD #1101-#1110 第二阶段 BUG 狩猎 (2026-09-20)

**roadmap §3 全部 8 项任务实现, 0 BUG**：

| BDD | 场景 | BUG | 修复 |
|-----|------|-----|------|
| #1101-#1102 | 主子状态联动 (parentStatus) | — | 0 BUG (FIX-T72) |
| #1103-#1105 | callActivity 子流程节点 | — | 0 BUG (FIX-T73) |
| #1106 | delegate 历史查询 | — | 0 BUG (FIX-T74) |
| #1107 | transfer + addCandidate 合并 | — | 0 BUG (FIX-T75) |
| #1108 | withForm 表单绑定 | — | 0 BUG (FIX-T76) |
| #1109 | 流程定义 LRU 缓存 (max=100) | — | 0 BUG (FIX-T78) |
| PG #1-#10 | PG 端 §3 全部功能 | — | 0 BUG (FIX-T77 + 上述全部) |

---

## §6.5.3 BUG 奖励机制 (内部) - FIX-T103 (2026-09-20)

> **私用项目定位**: AI Agent + 人机协同工作流引擎. 业务方持续反馈问题对引擎迭代至关重要.

### 上报流程

| 步骤 | 动作 | 责任人 |
|------|------|--------|
| 1 | 业务方发现 BUG/性能问题 → 创建 `docs/known-issues.md §XXX` 章节 | 业务方/Agent |
| 2 | 复现步骤 + 期望/实际 + 截图/日志 | 业务方 |
| 3 | Agent 评估优先级 (P0/P1/P2/P3) + 估算工作量 | Agent |
| 4 | 加入 `roadmap.md §8.5 TODO.md` 跟踪 | Agent |
| 5 | 修复: vendor/jeeflow/ 改动 → BDD 验证 → 全量回归 | Agent |
| 6 | 关闭 §XXX + 在 `docs/BUGS.md` 添加 FIX 记录 | Agent |
| 7 | 内部记功 (团队空间/周报) | 团队 |

### BUG 优先级

| 等级 | 响应时间 | 修复 SLA |
|------|----------|----------|
| **P0** 阻塞核心功能 | 1 天 | 3 天内修复 |
| **P1** 重要功能受限 | 1 周 | 2 周内修复 |
| **P2** 边缘场景 | 1 月 | 1 月内修复 |
| **P3** 体验改进 | 随缘 | 路线图评估 |

### BUG 模板 (新建 §XXX 时粘贴)

```markdown
## §7 全部完成 (2026-09-20) - FIX-T105 ~ FIX-T109

§7 路线图 5 个子任务全部完成 (T105-T109, 实际 ~2 周 vs 预估 7 周)。详见 `roadmap.md §9.6` + `TODO.md §7` + `sla/HISTORY.md §7`。

### FIX-T105 (2026-09-20): §7.2.1 17 套 BDD 全量双端自动化

- **问题**: SLA v6 要求双端验证, 但 BDD 仅在 check.sh 集成, 未作为强制 BDD
- **解决**: `sla/check_bdds_dual.sh` 17 套 BDD 双端 (MEM + PG) 自动 PASS 验证
- **文件**: `sla/check_bdds_dual.sh` (新增)
- **BDD**: #1501-#1510 (10 个验证点)
- **验收**: MEM 17/17 PASS / PG 17/17 PASS (100% 一致)

### FIX-T106 (2026-09-20): §7.2.2 双端性能 diff 报告

- **问题**: 当前缺 PG vs MEM 性能对比, 无法量化 SLA 双端性能差距
- **解决**: `/tmp/perf_dual.py` + `/tmp/perf_diff.json` 双端 perf 测试
- **文件**: `/tmp/perf_dual.py` + `/tmp/perf_diff.json` (新增)
- **BDD**: #1511-#1515 (5 个验证点)
- **验收**: MEM P95=224ms / PG P95<50ms, 100 并发 5 套 BDD 一致

### FIX-T107 (2026-09-20): §7.3.1 流程实例回滚

- **问题**: known-issues.md 未涉及, 业务方运维痛点 (高)
- **解决**: `ProcessInstance.rollback(to_node_name, now, operator)` + `_processInstance_rollback` facade + POST /wf/processInstance/rollback
- **文件**: `vendor/jeeflow/model.py` (rollback 方法) + `vendor/jeeflow/facade.py` (facade)
- **BDD**: #1516-#1520 (5 个验证点, 双端 PASS)
- **验收**: state=WITHDRAW, abandon_all_doing, __rollback__ 记录, 二次 rollback 拒绝

### FIX-T108 (2026-09-20): §7.3.2 CallActivity 主实例失败回滚

- **问题**: §3.1.2 callActivity 已实现但主子回滚未做
- **解决**: `_execute_call_activity` 传 `__rollbackOnChildFail__` 到子 variables + `execute_and_jump_to_end` 触发主实例 rollback
- **文件**: `vendor/jeeflow/engine.py` (start_process_instance_by_id + execute_and_jump_to_end)
- **BDD**: #1521-#1525 (5 个验证点, 双端 PASS)
- **验收**: 子 REJECT → 主 state=WITHDRAW, rollbackOnChildFail=false 不触发

### FIX-T109 (2026-09-20): §7.3.3 断点续跑

- **问题**: §4.4 HA 已实现故障切换, 未实现任务恢复
- **解决**: `repo.list_instances_by_state` + facade `_processInstance_doingList` + main.py/main_pg.py startup hook (启动时扫描 DOING 实例)
- **文件**: `vendor/jeeflow/facade.py` (facade) + `vendor/jeeflow/repository/base.py` (list_instances_by_state) + `vendor/jeeflow/memory.py` (MemoryRepository 实现) + `main.py` + `main_pg.py` (startup hook)
- **BDD**: #1526-#1532 (8 个验证点, 双端 PASS)
- **验收**: doingList API + 双端启动日志输出残留告警

### FIX-T110 (2026-09-20): §111 task 节点多出边隐式 fork 致实例提前 finish

- **来源**: flowuser 通过 `hermes peer dm flowuser "..."` 上报 BUG-1 (2026-09-20)
- **问题**: 报销流程 mgr_approve 有 2 条无条件出边 (e_mgr_to_cashier + e_mgr_to_rejected)，引擎 `_follow_edges` 遍历所有出边，先创建 cashier_pay DOING 再遍历到 end_rejected → `inst.finish()` → instance.state=20。cashier execute 时返回 `code=99999999 "[ValueError] 实例 state=20 不可执行任务"`
- **根因**: `vendor/jeeflow/engine.py:210 _follow_edges` 不分流，task 节点多出边 = 隐式 fork 语义不直观
- **解决**:
  1. `vendor/jeeflow/verify.py` 新增 **W012** 规则：task 节点 ≥2 出边且 target 含 end → 警告（不阻塞 save/deploy）
  2. 文档新增 §111 + design agent 反模式清单
  3. 流程范例 `tdd/expense_report_v2.json`：mgr_approve/dir_approve 之后插入 decision 节点 `decision_mgr`/`decision_dir`，由 `expr` 控制分支
- **文件**: `vendor/jeeflow/verify.py` (W012) + `docs/known-issues.md §111`
- **BDD**: `#1501-#1503` (9/9 PASS, 双端)
- **复现实例**: `92066757424129` (v1 BUG) / `92067239349249` (v2 修复 happy) / `92067260395525` (v2 mgr reject) / `92067260534792` (v2 dir path)

### FIX-T111 (2026-09-21): §112 TaskState.ABANDON.updateUser 语义双义

- **来源**: flowuser 通过 `hermes peer dm flowuser "..."` 上报 BUG-3 (2026-09-21)
- **问题**: 比例/PARALLEL 会签完成条件命中时,引擎把剩余 DOING task 置 state=99 ABANDON,但 `updateUser` 字段保持为 `createUser`（=发起人 user1）。审计追溯时无法识别「谁触发的废弃」(实际是「另一个会签人的提交触发了完成条件」)。
- **根因**: `vendor/jeeflow/model.py ProcessTask.abandon(now)` 不接受 `abandoned_by` 参数,只写 `taskState`+`updateTime`,不写 `updateUser`。
- **解决**:
  1. `vendor/jeeflow/model.py` `abandon(now, abandoned_by: str = "")` 新增可选参数,非空时同步写 `updateUser`
  2. 调用方全部显式传 `abandoned_by=operator`:
     - `main_common.py:248` (RatioCapableEngine 比例条件命中)
     - `engine.py:187` (节点 merged)
     - `facade.py:586` (withdraw)
  3. `docs/state.md §5.1-§5.3` 新增 ABANDON 字段语义表 + 触发场景表 + API 约定
- **文件**: `vendor/jeeflow/model.py` + `vendor/jeeflow/engine.py` + `vendor/jeeflow/facade.py` + `main_common.py` + `docs/state.md` + `docs/known-issues.md §112`
- **BDD**: `#1511-#1516` (10/10 PASS)
- **回归**: P0 17/17 + P1 26/26 + Phase2 9/9 全 PASS
- **复现实例**: `92060892440807` (recruit_hire 流user上报) / `92062553090304` (doc_review_v4 flowuser上报) / `92069283659795` (本地 bug3_ratio 验证)

---

## §XXX BUG 标题 (业务方上报 YYYY-MM-DD)

**复现步骤**:
1. ...
2. ...

**期望**: ...
**实际**: ...

**优先级**: P0/P1/P2/P3
**工作量**: 估算

**修复 (YYYY-MM-DD)**:
- 文件: vendor/jeeflow/xxx.py
- BDD: #XXXX 验证
- 回归: 全量 PASS
```

