# 规范 01 · 数据模型

> **来源**：https://jeeflow-doc.mldong.com/spec/01-data-model
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**数据模型参考**——设计者需知道有哪些表、表内有哪些字段、各字段作用。
>
> **本仓实现版本**：PG 方言（`docs/pg_schema.sql`，2026-09-20 更新）；**9 张表**（5 核心 + 3 扩展 + 1 本仓独有 `wf_trace_span` 链路追踪表，FIX-T99 / v1.9.0 起；`§6.4.1` 为 issues 域章节号）；DDL 已含本仓实测补充字段（`owner_id` / `parent_status` / `version`）。
>
> **裁剪记录**：header 通用约定 + 5 张核心表 + 3 张扩展表全部重写为本仓 PG 方言 DDL + 加本仓实测字段注解。

---

## 通用约定（本仓 PG 方言）

> **本仓 DDL 完整 SQL**：`../docs/pg_schema.sql`（`psql -f docs/pg_schema.sql` 应用一次；幂等 `CREATE TABLE IF NOT EXISTS`）。

| 字段类型 | 本仓 PG 方言 | 上游 MySQL 参考 | 备注 |
|---|---|---|---|
| 主键 `id` | `BIGINT PRIMARY KEY` | `BIGINT PRIMARY KEY` | 一致（雪花或自增）|
| `name` 编码 | `VARCHAR(128)` | `VARCHAR(100)` | 长度略不同（PG 无影响）|
| `display_name` | `VARCHAR(255)` | `VARCHAR(200)` | 长度略不同 |
| 时间字段 | `TIMESTAMP` | `DATETIME` | PG / MySQL 语义等价 |
| `variable` JSON | `TEXT` | `TEXT` | 一致 |
| `content` 流程 JSON | `TEXT` | `BLOB` | PG 用 TEXT 存大对象（BLOB 不通用）|
| `create_user` / `update_user` | `VARCHAR(64)` | `VARCHAR(64)` | 一致 |
| 索引 | `CREATE INDEX IF NOT EXISTS` | `CREATE INDEX` | PG 幂等 |

> **本仓实测补充字段**（不在上游通用约定中）：
> - `wf_process_instance.owner_id`：流程发起人 userId（FIX-T9 §66），业务方按 `owner_id` 查"我发起的"
> - `wf_process_instance.parent_status`：主子状态联动（FIX-T72 §3.1.1），取值 `CHILD_DONE` / `CHILD_REJECT`
> - `wf_process_instance.version`：乐观锁（FIX-T87 §4.4.2），并发更新防丢失

---

## 核心表（5 张）

### `wf_process_define`（流程定义部署版本）

```sql
CREATE TABLE IF NOT EXISTS wf_process_define (
    id              BIGINT PRIMARY KEY,
    name            VARCHAR(128),
    display_name    VARCHAR(255),
    type            VARCHAR(64),
    state           INT,
    content         TEXT,
    version         INT,
    create_time     TIMESTAMP,
    create_user     VARCHAR(64),
    update_time     TIMESTAMP,
    update_user     VARCHAR(64)
);
```

| 字段 | 含义 | 设计者只读 |
|---|---|---|
| `id` | 主键 | ✅ |
| `name` | 流程编码（唯一）| ✅ |
| `display_name` | 显示名 | ✅ |
| `type` | 流程类型（`approval` / `business`）| ✅ |
| `state` | 启用状态（1=启用 / 0=停用）| ✅ |
| `content` | 流程定义 JSON（LogicFlow 格式）| ✅ |
| `version` | 版本号（deploy 自动 +1）| ✅ |

> **设计者唯一写入**：`POST /wf/processDesign/save` + `/wf/processDesign/deploy`（详见 `../ToT/guides/06-deployment.md` §5.2）。

### `wf_process_instance`（流程实例）

```sql
CREATE TABLE IF NOT EXISTS wf_process_instance (
    id                  BIGINT PRIMARY KEY,
    parent_id           BIGINT,
    process_define_id   BIGINT,
    state               INT,
    parent_node_name    VARCHAR(255),
    business_no         VARCHAR(128),
    operator            VARCHAR(64),
    owner_id            VARCHAR(64),       -- FIX-T9 §66 实例所有者（流程发起人 userId）
    expire_time         TIMESTAMP,
    variable            TEXT,
    parent_status       VARCHAR(32),       -- FIX-T72 §3.1.1 主子联动 (CHILD_DONE/CHILD_REJECT)
    version             BIGINT DEFAULT 0,  -- FIX-T87 §4.4.2 乐观锁
    create_time         TIMESTAMP,
    create_user         VARCHAR(64),
    update_time         TIMESTAMP,
    update_user         VARCHAR(64)
);
CREATE INDEX IF NOT EXISTS idx_wf_process_instance_version ON wf_process_instance(version);
CREATE INDEX IF NOT EXISTS idx_wf_process_instance_owner  ON wf_process_instance(owner_id);
```

| 字段 | 含义 | 设计者只读 |
|---|---|---|
| `id` | 实例主键 | ✅ |
| `parent_id` | 父实例 ID（子流程用）| ✅ |
| `process_define_id` | 流程定义 ID | ✅ |
| `state` | 实例状态：10 进行中 / 20 已完成 / 30 已撤回 / 40 强行终止 / 45 已拒绝 / 50 挂起 / 99 已废弃 | ✅ |
| `parent_node_name` | 父流程节点名（子流程用）| ✅ |
| `business_no` | 业务流水号 | ✅ |
| `operator` | 发起人（与 `owner_id` 等价但语义不同：`operator` = 流程实例字段，`owner_id` = 业务索引字段）| ✅ |
| `owner_id` | **本仓实测补充**：流程发起人 userId（FIX-T9 §66），按此查"我发起的" | ✅ |
| `parent_status` | **本仓实测补充**：主子状态联动值（`CHILD_DONE` / `CHILD_REJECT`，FIX-T72 §3.1.1）| ✅ |
| `version` | **本仓实测补充**：乐观锁（FIX-T87 §4.4.2）| ✅ |
| `variable` | 流程变量 JSON（含 `f_*` 业务变量 + `tf_*` 任务变量 + `u_*` 操作人）| ⚠️ 业务方只读 |

### `wf_process_task`（流程任务行）

```sql
CREATE TABLE IF NOT EXISTS wf_process_task (
    id                  BIGINT PRIMARY KEY,
    process_instance_id BIGINT,
    task_name           VARCHAR(128),
    display_name        VARCHAR(255),
    task_type           VARCHAR(64),
    perform_type        VARCHAR(64),
    task_state          INT,
    operator            VARCHAR(64),
    finish_time         TIMESTAMP,
    expire_time         TIMESTAMP,
    form_key            VARCHAR(255),
    task_parent_id      BIGINT,
    variable            TEXT,
    create_time         TIMESTAMP,
    create_user         VARCHAR(64),
    update_time         TIMESTAMP,
    update_user         VARCHAR(64)
);
```

| 字段 | 含义 | 设计者只读 |
|---|---|---|
| `id` | 任务主键 | ✅ |
| `process_instance_id` | 实例 ID | ✅ |
| `task_name` | 任务节点编码（对应流程 JSON `node.id`）| ✅ |
| `display_name` | 任务节点显示名 | ✅ |
| `task_type` | 0=主办 / 1=协办 / 2=记录（FIX-T30 透传落库）| ✅ |
| `perform_type` | 0=普通 / 1=会签 | ✅ |
| `task_state` | 10 进行中 / 20 已完成 / 30 已撤回 / 40 强行终止 / 50 挂起 / 99 已废弃 | ✅ |
| `operator` | 实际操作人 | ✅ |
| `finish_time` | 完成时间 | ✅ |
| `expire_time` | 期望完成时间 | ✅ |
| `form_key` | 表单标识（`node.properties.form`）| ✅ |
| `task_parent_id` | 上一步任务 ID（退回用；发起无当前任务时写 `0`）| ✅ |
| `variable` | 任务变量 JSON（会签计数等）| ✅ |

### `wf_process_task_actor`（任务参与者，多对多）

```sql
CREATE TABLE IF NOT EXISTS wf_process_task_actor (
    id              BIGINT PRIMARY KEY,
    process_task_id BIGINT,
    actor_id        VARCHAR(64),
    create_time     TIMESTAMP,
    create_user     VARCHAR(64)
);
CREATE INDEX IF NOT EXISTS idx_wf_process_task_instance     ON wf_process_task(process_instance_id);
CREATE INDEX IF NOT EXISTS idx_wf_process_task_actor_task   ON wf_process_task_actor(process_task_id);
```

> 一个任务多个参与者（会签 P=1 / 转交后多参与者）走多行存储。设计者无需直接读写，由 `processTask/todoList` + `processTask/execute` 维护。

### `wf_process_cc_instance`（抄送实例）

```sql
CREATE TABLE IF NOT EXISTS wf_process_cc_instance (
    id                  BIGINT PRIMARY KEY,
    process_instance_id BIGINT,
    actor_id            VARCHAR(64),
    state               INT,
    create_time         TIMESTAMP,
    create_user         VARCHAR(64),
    update_time         TIMESTAMP,
    update_user         VARCHAR(64)
);
CREATE INDEX IF NOT EXISTS idx_wf_process_cc_instance_inst  ON wf_process_cc_instance(process_instance_id);
```

| `state` 值 | 含义 |
|---|---|
| 0 | 未读 |
| 1 | 已读 |

> **本仓实测**：本仓 facade **已提供** `processInstance/createCCInstance` / `updateCCStatus` / `ccList` 端点（`facade.py:1436/1449/1457`）；但「我的抄送」UI 与「已读回执」业务逻辑仍由集成方实现（详见 `../ToT/guides/05-scenarios.md` 场景五抄送）。

---

## 扩展表（3 张，v1.1.0 管理扩展）

> 设计稿 / 历史 / 委托是"周边管理能力"，引擎核心不依赖。

### `wf_process_design`（流程设计层）

> 设计器保存的设计稿（流程 JSON 草稿）。**发布（deploy）**后生成 `wf_process_define` 记录。

```sql
CREATE TABLE IF NOT EXISTS wf_process_design (
    id              BIGINT PRIMARY KEY,
    name            VARCHAR(128),
    display_name    VARCHAR(255),
    type            VARCHAR(64),
    icon            VARCHAR(255),
    is_deployed     BOOLEAN,
    remark          VARCHAR(500),
    create_time     TIMESTAMP,
    create_user     VARCHAR(64),
    update_time     TIMESTAMP,
    update_user     VARCHAR(64)
);
CREATE INDEX IF NOT EXISTS idx_wf_process_design_name ON wf_process_design(name);
```

> **与上游差异**：本仓 `is_deployed` 为 `BOOLEAN`（上游 `INT DEFAULT 0`）；`remark` 为 `VARCHAR(500)`（上游 `TEXT`）。本仓**不采用逻辑删除**（无 `is_deleted`），删除即物理删除。

### `wf_process_design_his`（设计历史快照）

> 每次保存设计的 content 快照，支持设计器"历史版本"回看。

```sql
CREATE TABLE IF NOT EXISTS wf_process_design_his (
    id                  BIGINT PRIMARY KEY,
    process_design_id   BIGINT,
    content             TEXT,
    create_time         TIMESTAMP,
    create_user         VARCHAR(64)
);
CREATE INDEX IF NOT EXISTS idx_wf_process_design_his_design ON wf_process_design_his(process_design_id);
```

> **本仓实测**（`docs/AGENTS.md §5.2.5`）：`/api/reset` **不清空** `processDesign` 与 `processDesign_his` 两张表，但 **`processDesign/save` 是 UPSERT** —— 以 `name` 为唯一键，**复用现有行 id**；`/api/reset` 后 design 表仅 1 行；多次 save 不同 `name` 全部返回同一 id（**name 字段被覆盖**）。设计者测试时**禁止**硬编码 `design_id`，必须从响应实时取。

### `wf_process_surrogate`（流程委托代理）

> 授权人（`operator`）在时间窗内把某流程（`process_name`）的待办委托给代理人（`surrogate`）。引擎侧通过 `SurrogateInterceptor`（内置、默认开启、可显式关闭）在任务创建后把代理人加入参与者。

```sql
CREATE TABLE IF NOT EXISTS wf_process_surrogate (
    id            BIGINT PRIMARY KEY,
    process_name  VARCHAR(128),
    operator      VARCHAR(64),
    surrogate     VARCHAR(64),
    start_time    TIMESTAMP,
    end_time      TIMESTAMP,
    enabled       BOOLEAN,
    create_time   TIMESTAMP,
    create_user   VARCHAR(64),
    update_time   TIMESTAMP,
    update_user   VARCHAR(64)
);
```

| 字段 | 含义 |
|---|---|
| `process_name` | 流程编码（**为空 = 全部流程**）|
| `enabled` | 是否启用（PG `BOOLEAN`，上游 `INT DEFAULT 1`）|

> **生效判据**（上游 05-spi + 06-facade §4.5）：
> - 时间窗：`start_time <= now <= end_time`
> - `process_name` 为空 = 兜底全部流程
> - 自委托过滤：`operator != surrogate`
> - `enabled` 仅认 `1` / `true`

---

## 本仓补充表（1 张，FIX-T99 / v1.9.0 起）

### `wf_trace_span`（链路追踪 span）

> **本仓额外**——上游未列。链路追踪 span 持久化（FIX-T99 / v1.9.0 起；`§6.4.1` 为 issues 域章节号，2026-09-20）。

```sql
CREATE TABLE IF NOT EXISTS wf_trace_span (
    id BIGSERIAL PRIMARY KEY,
    trace_id VARCHAR(64) NOT NULL,
    span_id VARCHAR(64) NOT NULL,
    parent_span_id VARCHAR(64),
    name VARCHAR(128) NOT NULL,
    start_time DOUBLE PRECISION NOT NULL,
    end_time DOUBLE PRECISION,
    duration_ms INTEGER,
    status VARCHAR(16) DEFAULT 'ok',
    error TEXT,
    attributes JSONB,
    events JSONB,
    create_time TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_wf_trace_span_trace_id    ON wf_trace_span(trace_id);
CREATE INDEX IF NOT EXISTS idx_wf_trace_span_create_time ON wf_trace_span(create_time);
CREATE INDEX IF NOT EXISTS idx_wf_trace_span_name        ON wf_trace_span(name);
```

> **设计者只读**——本表由引擎在每次节点执行时自动写入 trace span；可通过 `GET /api/admin/trace?limit=20` 查询（详见 `../ToT/guides/06-deployment.md` §5.1）。