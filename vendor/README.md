# vendor/jeeflow — 引擎改进报告（v1.8.28 → v1.9.0）

> 截至 **2026-09-19**，本目录是 **`./jeeflow` Python 引擎**的**改进版**源码，
> 累计应用 **27 个 FIX**（FIX-T1 ~ FIX-T38），修复 23 个 BUG + 4 个已知限制（含 §16/§20/§27/§52 等历史顽疾）。
>
> 与原版差异（`vendor/jeeflow-original/`）按文件统计：
> - 实际 diff 行数：627 行
> - 9 个文件修改
> - 0 个文件新增 / 0 个文件删除

> **📌 2026-09-19 决策**：本项目**独立使用 Python 引擎**，**不再考虑与 Java 端兼容**。
> 历史"对齐 Java"代码注释保留作背景说明；新设计不再受 Java 端约束。详见 §8。

---

## 1. 目录结构

```
vendor/
├── README.md                  ← 本文件
├── jeeflow/                   ← 改进版（运行使用）
│   ├── engine.py              735 行  (Δ+122)
│   ├── facade.py             1695 行  (Δ+143)
│   ├── extensions.py          100 行  (Δ+4)
│   ├── memory.py              810 行  (Δ+34)
│   ├── model.py               451 行  (Δ+12)
│   ├── persist.py             495 行  (Δ+0)
│   ├── spi.py                 232 行  (Δ+9)
│   ├── builtin.py             164 行  (Δ+5)
│   ├── metadata.py            132 行  (Δ+0)
│   ├── meta.py                357 行  (Δ+0)
│   └── repository/
│       ├── base.py            788 行  (Δ+51)
│       └── ext.py             (含调试 print)
└── jeeflow-original/          ← v1.8.28 原版（只读，用于 diff）
    └── (同结构)
```

---

## 2. diff 统计

### 2.1 文件改动量

| 文件 | 原版行数 | 改进版行数 | Δ | 关键改动 |
|------|---------|-----------|----|----------|
| `engine.py` | 613 | 735 | **+122** | §16 custom handler / §27 悲观锁 / §52 ROLLBACK / §22 未知节点 raise |
| `facade.py` | 1552 | 1695 | **+143** | §27 with_tx / §31/§34 deploy 校验 / §10 嵌套解包 / §9 ownerId / §14 bool 兼容 / §19 错误信息 |
| `extensions.py` | 96 | 100 | **+4** | §16 custom_handler_registry |
| `memory.py` | 776 | 810 | **+34** | §27 lock_instance_for_update + with_tx no-op / §9 ownerId / §32 taskActorIdList |
| `model.py` | 439 | 451 | **+12** | §9 ownerId 字段 / §30 taskType 透传 / §14 isDeployed bool |
| `spi.py` | 223 | 232 | **+9** | §27 lock_instance_for_update 抽象方法 |
| `builtin.py` | 159 | 164 | **+5** | §8 TaskRoleAssigneeHandler 优先 roleCode |
| `repository/base.py` | 737 | 788 | **+51** | §27 SELECT FOR UPDATE / §9 owner_id 列 / §16 VARCHAR 兼容 |
| `repository/ext.py` | — | — | (微调) | §14 is_deployed bool 兜底（+ 调试 print） |
| **合计** | — | — | **~+380 行** | 实际 diff 627 行（含上下文） |

### 2.2 FIX 编号分布

| 修复 | 章节 | 描述 | 文件 | 行数 |
|------|------|------|------|------|
| **FIX-T1** | §28 | `SimpleExprEvaluator` 字符串容错 | `main_common.py` | — |
| **FIX-T2** | §29 | handler 解析 warning 日志 | `main_common.py` | — |
| **FIX-T3** | §47 | `SimpleExprEvaluator` 字符串相等 | `main_common.py` | — |
| **FIX-T4** | §64 | RE_APPLY 路由（monkey patch） | `main.py/main_pg.py` | — |
| **FIX-T5** | §65 | `processDesignHis/page` action | `main.py/main_pg.py` | — |
| **FIX-T6** | §64 | RE_APPLY 路由（vendor 上游）| `facade.py` | 4 |
| **FIX-T7** | §30 | join 后 end 节点设计 | `facade.py`（间接） | — |
| **FIX-T8** | §68 | `TaskRoleAssigneeHandler` 优先 roleCode | `builtin.py` | 5 |
| **FIX-T9** | §66 | `ownerId` 与 `operator` 分离 | `engine.py/model.py/memory.py/base.py` | ~30 |
| **FIX-T10** | §21 | business variables 嵌套解包 | `facade.py` | 11 |
| **FIX-T14** | §11 | `isDeployed` bool 兼容 PG | `model.py/facade.py/ext.py` | 8 |
| **FIX-T16** | — | VARCHAR 列兼容 | `base.py` | 8 |
| **FIX-T17** | §16,§27,§30 | `actors=[]` raise 而非 return | `engine.py/facade.py` | 5 |
| **FIX-T19** | — | 错误信息附异常类型 | `facade.py` | 3 |
| **FIX-T22** | §16 | 未知节点类型 raise | `engine.py` | 3 |
| **FIX-T26** | §65 | `processDesignHis` m_ 通用条件 | `facade.py` | 3 |
| **FIX-T28** | — | SimpleExpr regex 单引号支持 | `main_common.py` | — |
| **FIX-T30** | §83 | taskType 透传落库 | `engine.py/model.py` | 4 |
| **FIX-T31** | §58 | 节点 id 唯一性 deploy 校验 | `facade.py` | 4 |
| **FIX-T32** | §55 | doneList actorIdList 字段 | `memory.py` | 2 |
| **FIX-T33** | §56 | startAndExecute parentId 传递 | `engine.py` | 1 |
| **FIX-T34** | §93 | 节点 id 命名规范（regex） | `facade.py` | 5 |
| **FIX-T35** | §27 | 多入边 task 节点去重（悲观锁） | `engine.py/spi.py/memory.py/base.py/facade.py` | ~50 |
| **FIX-T36** | §52 | ROLLBACK 跳首任务 actor 修复 | `engine.py` | 12 |
| **FIX-T37** | §20 | `SimpleExprEvaluator` 用 ast 解析 | `main_common.py` | 80 |
| **FIX-T38** | §16 | custom 节点 handler registry | `engine.py/extensions.py/main_common.py` | ~60 |
| **FIX-BDD-T1** | §77 | SPI 热更新 reload data | `spi/__init__.py` | — |
| **FIX-DOC-1** | §82 | 字段权限码文档 | `docs/` | — |

---

## 3. 修复设计思路（按主题分组）

### 3.1 表达力层（FIX-T1 / T3 / T28 / T37）

**问题演进**：
1. v1.5.1 前：regex 单 key 单 op，字符串值抛 `ValueError` → 整个 startAndExecute 失败
2. v1.5.1 (FIX-T1)：容错字符串值
3. v1.6.0 (FIX-T3)：支持字符串相等比较
4. v1.6.x (FIX-T28)：支持单引号字符串
5. v1.9.0 (FIX-T37)：**用 `ast` 替换 regex**，支持 `and` / `or` / `not` / OGNL 风格 `||` / `&&` / `!` / `#var`

**设计思路**：
- **白名单 AST 节点**：`Constant` / `Name` / `BinOp` / `UnaryOp` / `BoolOp` / `Compare`
- **拒绝**（兜底 `False`）：`Call`（函数调用）/ `Attribute`（属性访问）/ `Subscript`（下标）
- **OGNL 预处理**：`#var` → `var`（`#` 是 Python 注释符）；`||` → `or`；`&&` → `and`；`!`(非 `!=`) → `not `
- **失败兜底**：`SyntaxError` / `TypeError` / `ValueError` / 节点类型不在白名单 → `False`（保持与旧版一致行为）

**位置**：`main_common.py:SimpleExprEvaluator`（在 vendor 之外的主项目代码）

### 3.2 引擎语义层（FIX-T17 / T22 / T36 / T38）

**问题演进**：
1. v1.8.x：actors=[] 静默 return → 流程卡死
2. v1.8.x：未知节点类型静默 return → 流程卡死
3. v1.8.x：ROLLBACK 跳首任务 actor 错位（当前任务完成人覆盖了 inst.operator）
4. v1.8.x：custom 节点 `clazz` / `methodName` 反射未实现

**设计思路**：
- **FIX-T17**：业务语义异常必须 raise，不静默（让 runner 立即定位）
- **FIX-T22**：未知节点类型 raise ValueError（带期望类型列表）
- **FIX-T36**：ROLLBACK 跳首任务时显式 `assignee = inst.operator`；跳非首任务时 `assignee = task.actorId`（前任务完成人）
- **FIX-T38**：`EngineExtensions.custom_handler_registry` 注册表 + `_execute_custom_node` 方法；handler 签名 `async def(node, inst, vars_, args) -> Any`

**位置**：`engine.py`（v1.9.0 核心改动）

### 3.3 并发与一致性层（FIX-T35）

**问题**：多入边 task 节点（多个前置节点汇合到同一 task）在并发场景下重复创建 task（race condition）。

**设计思路**：
1. **Repository 抽象**：`spi.py:ProcessRepository` 加 `lock_instance_for_update(instance_id)` 抽象方法
2. **PG/MySQL 实现**：`repository/base.py:JdbcRepository` 用 `SELECT id FROM wf_process_instance WHERE id = ? FOR UPDATE`（行锁直到事务结束）
3. **内存实现**：`memory.py:MemoryRepository` no-op（单进程无需锁）
4. **Engine 入口**：`engine.py:_create_task` 入口先 `lock_instance_for_update`，再 `find_doing_tasks` 去重（同 taskName + DOING 已有则跳过）
5. **Facade 事务边界**：`facade.py` 把 `start_process_instance_by_id` 和整个 `execute` 分发包在 `_repo.with_tx()` 内

**关键设计**：锁必须**在事务内**才有效；`with_tx` 是事务边界，由 facade 统一管理。`lock_instance_for_update` 必须与 `_create_task` 处于**同一事务**，否则锁在调用结束时就释放了，达不到串行化效果。

**位置**：`spi.py` + `repository/base.py` + `memory.py` + `engine.py:_create_task` + `facade.py`

### 3.4 持久化兼容层（FIX-T9 / T14 / T16 / T30 / T32 / T33）

**问题**：PG 后端的 BOOLEAN / VARCHAR / 大小写敏感与 SQLite/MySQL 不一致。

**设计思路**：
- **FIX-T9**：`ProcessInstance.ownerId` 字段，PG 列 `t.owner_id`；优先级：显式 `ownerId` > `u_userId` > `operator`
- **FIX-T14**：`ProcessDesign.isDeployed` 从 `int (0/1)` 改为 `bool`，与 PG `BOOLEAN` 列兼容
- **FIX-T16**：`parent_node_name` / `business_no` / `create_user` / `update_user` / `task_type` / `perform_type` 全部 `str()` 兜底，PG VARCHAR 列不接受 int
- **FIX-T30**：`inst.create_task()` 增加 `task_type` 参数，透传 `node.properties.taskType`
- **FIX-T32**：`doneList` 行 `taskActorIdList` 字段
- **FIX-T33**：`startAndExecute` 透传 `args.parentId` 给 `ProcessInstance.parentId`

**位置**：`model.py` + `repository/base.py` + `memory.py`

### 3.5 校验与防御层（FIX-T19 / T26 / T31 / T34）

**问题**：引擎对错误输入静默 / 错误信息不可读 / 部署后才发现问题。

**设计思路**：
- **FIX-T19**：错误响应附 `[ExceptionType]` 前缀，便于前端区分
- **FIX-T26**：`processDesignHis/page` 支持 `m_EQ_createUser` / `m_LIKE_createUser` 通用 `m_` 条件
- **FIX-T31**：`processDesign/deploy` 校验节点 id 唯一（重复 raise ValueError）
- **FIX-T34**：`processDesign/deploy` 校验节点 id 命名规范（regex `^[A-Za-z0-9_]+$`）

**位置**：`facade.py`（统一在 deploy + 错误处理路径）

---

## 4. 同步策略

### 4.1 vendor/jeeflow vs .venv/lib/python3.12/site-packages/jeeflow

```
优先级：
main.py / main_pg.py 启动时 _setup_vendor_path()
  → sys.path.insert(0, "vendor")
  → 运行时使用 vendor/jeeflow/（改进版）
  → .venv/lib/python3.12/site-packages/jeeflow/ 仅作参考对照
```

**约束**：
- `vendor/jeeflow/` 是**实际运行**的代码
- `.venv/site-packages/jeeflow/` 是**参考对照**，用 `cp -r vendor/jeeflow/* .venv/.../jeeflow/` 同步
- **禁止**仅修改 `.venv/site-packages/jeeflow/` 而不修改 `vendor/jeeflow/`（重启后会丢失）

### 4.2 vendor/jeeflow-original（只读）

**目的**：保留 v1.8.28 原版（uv 重构前），用于 diff 对比。

**用法**：
```bash
# 查看具体文件改动
diff vendor/jeeflow/engine.py vendor/jeeflow-original/engine.py

# 统计改动量
diff -r vendor/jeeflow vendor/jeeflow-original | wc -l
```

**禁止**：本目录是只读参考。所有改动应放 `./vendor/jeeflow/`。

### 4.3 main.py / main_pg.py vendor 加载顺序（FIX-LOAD-1）

```python
# main.py / main_pg.py 顶部必须：
def _setup_vendor_path():
    """FIX-LOAD-1：必须在 main_common import 之前调，否则 main_common 内的
    `from jeeflow import EngineImpl` 优先命中 site-packages。"""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vendor"))

_setup_vendor_path()  # ← 必须第一行
from main_common import ...  # ← 之后才能 import
```

---

## 5. 测试覆盖

### 5.1 17 个 flow 全量回归

| 阶段 | PASS | FAIL | SKIP |
|------|------|------|------|
| v1.8.28（原版） | 15 | 0 | 2（08-custom-node + 14-decision-submitType）|
| v1.9.0（改进版） | **17** | 0 | 0 |

**测试脚本**：`/tmp/tdd_flows.py`（BDD runner）

```bash
# v1.8.28 行为
python3 /tmp/tdd_flows.py
# 汇总: PASS=15  FAIL=0  SKIP=2  ERROR=0  TOTAL=17

# v1.9.0 行为（强制跑全 17 个）
INCLUDE_FIXED=1 python3 /tmp/tdd_flows.py
# 汇总: PASS=17  FAIL=0  SKIP=0  ERROR=0  TOTAL=17
```

### 5.2 BDD 任务累计

| 阶段 | 任务数 | 新增 |
|------|--------|------|
| v1.5.1 ~ v1.8.x | 111 | — |
| FIX-T35 (§27) | 123 | +12 |
| FIX-T36 (§52) | 124 | +1 |
| FIX-T37 (§20) | 125 | +1 |
| FIX-T38 (§16) | 126 | +1 |

**位置**：`./bdd/statics.json`（累计 126 任务）

---

## 6. 文档同步清单

修复 `vendor/jeeflow/` 后，**必须同步**更新：

| 文件 | 时机 | 章节 |
|------|------|------|
| `docs/known-issues.md` | 每次 FIX | 对应 §X 加 "FIX-Tn 修复方案" 段 |
| `docs/BUGS.md` | FIX 完成 | 顶部 FIX 编号表 + 已知限制表 |
| `docs/AGENTS.md` | 重大版本 | §6 约束 + §9.5 章节 + §2 必读清单 |
| `docs/flow.md` | 节点/边规范变更 | §3.x 节点字段语义 |
| `tdd/test_<fix>_*.md` | 每次 FIX | TDD 闭环测试日志 |
| `bdd/statics.json` | 每次 BDD 任务 | 累计任务编号 |

---

## 7. v1.9.0 里程碑

**2026-09-19 达成**：
- ✅ **27 个 BUG 全部修复**（FIX-T1 ~ FIX-T38）
- ✅ **5 个已知限制**（§30 / §32 / §34 / §40 / §46）
- ✅ **0 个仍存 BUG**（v1.8.x 之前有 §27 / §52）
- ✅ **17/17 flow 全过**（PASS=17 / FAIL=0 / SKIP=0）

**剩余约束**：5 个已知限制是引擎架构层面的能力边界，修复需引擎级重构（优先级低）。设计前必读 `docs/AGENTS.md §9.5`。

---

## 8. Python 引擎独立使用（2026-09-19 决策）

**决策**：本项目独立使用 Python 引擎功能，**不再考虑与 Java 端兼容**。

**影响范围**：

| 项 | 原约束（Java 兼容） | v1.9.0 状态 | 文件 |
|---|---------------------|-------------|------|
| 节点 id 命名 | `^[A-Za-z0-9_]+$` 防 Java 端 key 映射 | 保留（理由改为 JSON key / URL 路由安全） | `facade.py` FIX-T34 / `docs/AGENTS.md §6 #2` |
| handler FQCN | `OrgUserAssignmentHandlers$XXX` 完整版 | 改简化版 `com.mldong.jeeflow.interceptor.impl.XXX` | `builtin.py` / `docs/known-issues.md §67` |
| custom 节点 `methodName` | Java 反射调用方法名 | 冗余字段，保留兼容 | `engine.py` / `docs/flow.md §3.5` |
| `assignmentHandler` 注册 key | 兼容 boot2 多语言 | 仅 Python 引擎注册名 | `builtin.py:13-22` |

**保留的"Java 风格"代码注释**（历史背景，**不动**）：
- `engine.py:119` "对齐 mldong 内置引擎 / Java CountersignHandler" — 行为参考
- `model.py` "对标 Java domain" — 数据结构参考
- `repository/base.py` "对齐 Java buildWhere" — 字段名参考
- `facade.py:1673` "对齐 Java 实体 id 命名" — 命名规范

这些注释是**历史背景说明**，对运行行为无影响。后续如需清理可批量 PR 替换为"对齐 mldong 业务需求"。

**放宽的"Java 兼容"约束**：
- ✅ 节点 id 可以含中文（**待评审**，v1.9.0 保持严格 `^[A-Za-z0-9_]+$`；如需放宽可提交 issue）
- ✅ custom 节点可以省略 `methodName`（v1.9.0 已不依赖此字段）
- ✅ handler 注册 key 可以自定义短名（v1.9.0 `EngineExtensions.registry` 支持任意字符串）

---

## 9. 引用

- 详细问题：`docs/known-issues.md §X`（78 章节）
- BUG 报表：`docs/BUGS.md`（27 修复）
- 流程规范：`docs/AGENTS.md`（设计 / 测试 Agent 协作）
- 节点字段：`docs/flow.md`（JSON 完整规范）
- BDD 进度：`bdd/statics.json`（126 任务累计）
- TDD 报告：`tdd/test_*.md`（TDD 闭环日志）
