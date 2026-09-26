# 08 · 业务数据入库（流程结束自动落表）

> **来源**：https://jeeflow-doc.mldong.com/guides/08-persist
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**业务数据自动落表设计指南**。
>
> **本仓实现版本**：基于 `vendor/jeeflow/persist.py`（**已完整实现**）：`DynamicTableWriter`（引擎无关写入器）+ `JdbcDynamicTableWriter`（sqlite/mysql/postgres/h2 实现）+ `PersistPostInterceptor`（ARCHIVE / SYNC 双模式）+ `register_persist_meta()`（元注册助手）。
>
> **裁剪记录**：§1 / §2.③ / §3 / §2.1 / §4 保留 + 加本仓实现注解；§2.① / §2.② Java/Go/Node 裁掉仅留 Python 重写；§5 SQL 重写为本仓 PG 后端验证。

---

## 1. 适用场景

| 场景 | 说明 |
|---|---|
| 审批通过落库 | 流程结束 + 同意（`submitType=AGREE`）时，表单数据写入业务表 |
| 业务数据独立存储 | 流程数据在 jeeflow 表，业务数据在自有业务表（推荐架构）|
| 无引擎场景 | `DynamicTableWriter` 组件本身引擎无关，任意「表名 + 字段 Map」安全写表 |
| 同步演进（SYNC）| 流程发起即入库 → 节点推进更新 → 结束定稿，全程留痕（v1.8.0+）|

> **不适用**：不同意/退回也要落库（ARCHIVE 模式仅同意落库；不同意需自行扩展拦截器或改用 SYNC 模式）。

---

## 2. 三步接入

### ① 引入组件（本仓 Python）

> **上游原文 4 语言 Maven/Go/Python/Node 依赖整段裁剪，仅保留 Python**。

本仓 Python 模块已**随主包内置**于 `vendor/jeeflow/persist.py`，无需额外依赖：

```python
from jeeflow.persist import (
    DynamicTableWriter,
    JdbcDynamicTableWriter,
    PersistPostInterceptor,
    register_persist_meta,    # 元注册助手（issues/60）
    PERSIST_MODE_ARCHIVE,     # "ARCHIVE"
    PERSIST_MODE_SYNC,        # "SYNC"
)
```

### ② 注册写入器（本仓 Python）

> **上游 4 语言示例整段裁剪，仅保留 Python**。

```python
# main_common.py:build_persist_components()
import sqlite3  # 或 pymysql / psycopg2
from jeeflow.persist import JdbcDynamicTableWriter, PersistPostInterceptor

def build_persist_components(repo):
    """构建业务数据落库组件（动态表写入器 + 入库拦截器）"""
    # 业务数据库连接（独立于引擎 PG 库）
    conn = sqlite3.connect("biz.db")

    # 动态表写入器（DB-API 2.0；自动探测 sqlite3 vs 其他）
    writer = JdbcDynamicTableWriter(
        conn,
        # 可选：自定义系统字段列名
        create_time_column="create_time",
        create_user_column="create_user",
        update_time_column="update_time",
        update_user_column="update_user",
        is_deleted_column="is_deleted",
        # 可选：主键生成器（非自增主键表必备，issues/21）
        # primary_key_generator=lambda t: snowflake_id_worker(),
        # 可选：列匹配（False 宽松=驼峰↔下划线归一；True 严格）
        strict_column_match=False,
    )

    # 入库拦截器（v1.8.0 起 ARCHIVE + SYNC 双模式）
    interceptor = PersistPostInterceptor(
        writer=writer,
        loader=repo.find_define_by_id,   # async loader(define_id) -> ProcessDefine
    )

    return writer, interceptor
```

```python
# 应用到 engine（main_common.py:apply_extensions）
from jeeflow import EngineExtensions
from jeeflow.persist import register_persist_meta
from main_common import apply_extensions

# 元数据注册（issues/60：保证"字典项 ⟺ 实例"同步）
registry = EngineExtensions.registry or HandlerRegistry()
register_persist_meta(registry)

# 拦截器挂全局
ext = EngineExtensions(
    registry=registry,
    interceptor_registry={
        "persistPost": interceptor,    # 流程定义中可声明 postInterceptors: "persistPost"
    },
)
engine.set_extensions(ext)
```

> **本仓 SPI 依赖**：
> - `repo.find_define_by_id` 必须返回 `ProcessDefine` 对象，含 `id` / `content`（JSON 字符串）
> - `conn` 必须是 DB-API 2.0 连接：`sqlite3.Connection` / `pymysql.connections.Connection` / `psycopg2.extensions.connection`
> - sqlite3 自动识别方言；其他需显式传 `dialect="mysql"` / `"postgres"` / `"h2"`

### ③ 流程定义声明落库（4 语言契约一致）

持久化行为由**流程定义 JSON 顶层**的字段驱动（与 `name` / `nodes` 同层）：

| 字段 | 取值 | 语义 |
|---|---|---|
| `relTableName` | 表名 | **业务表名**——数据写入哪张表；**缺省回落流程 `name`**（流程唯一编码 = 表名约定）。表不存在 = 配置错误，流程执行失败（快速失败）|
| `persistMode` | `ARCHIVE` / `SYNC`（**缺省 `ARCHIVE`**）| **持久化模式**——`ARCHIVE`：流程结束且同意时落库一次；`SYNC`：发起即入库 → 节点推进 → 结束定稿，全程留痕。非 `SYNC` 值一律回落 `ARCHIVE` |

```json
{
  "name": "leave",
  "displayName": "请假审批",
  "type": "approval",
  "relTableName": "biz_leave",
  "persistMode": "ARCHIVE",
  "postInterceptors": "persistPost",
  "nodes": []
}
```

> **本仓解析实现**（`vendor/jeeflow/persist.py:404 PersistPostInterceptor._resolve_define`）：
> 1. `loader(instance.defineId)` 异步加载 `ProcessDefine`
> 2. `json.loads(define.content)` 解 JSON
> 3. 读 `meta["relTableName"]`（缺省回落 `meta["name"]`）+ `meta["persistMode"]`
>
> **拦截器挂载机制**：本仓 `postInterceptors` 字段为字符串 key（按名从 `interceptor_registry` 取实例）；未注册时 `engine.py:1054 _resolve_interceptors` 抛 `ValueError(拦截器未注册: persistPost)`。

---

## 3. 落库字段

以请假流程为例，发起时提交表单变量：

```
f_title = "年假申请"
f_amount = 800
u_deptId = "D01"
```

流程结束同意后写入 `biz_leave` 表：

| 列 | 值 | 来源 |
|---|---|---|
| `title` | 年假申请 | `f_title` 去前缀（`_extract_fields` 行 427）|
| `amount` | 800 | `f_amount` 去前缀 |
| `process_instance_id` | 123 | 流程上下文（幂等键，`_fill_context` 行 476）|
| `apply_user_id` | user1 | 发起人 |
| `apply_dept_id` | D01 | 发起部门 |
| `create_time` / `create_user` | 2026-08-04 10:00:00 / user1（operator）| writer 系统字段（`fill_system_fields` 行 231）|
| `update_time` / `update_user` | 同上 | writer 系统字段 |
| `is_deleted` | 0 | writer 系统字段 |

**规则**：

- **业务表只需建你关心的列**——多余的 `f_` 字段自动过滤（`filter_columns` 列探测，行 163）
- **非自增主键表**（v1.8.0+ issues/21）：雪花 / 应用生成主键需注册 `set_primary_key_generator(...)`；data 已有主键值用之；未配置生成器时抛清晰错误（`persist.py:183`）
- **列名宽松匹配**（v1.8.0+ issues/20，默认 `strict_column_match=False`）：驼峰表单字段（`companyName`）自动落到下划线表列（`company_name`），写入用表列原名；需要精确控制时 `set_strict_column_match(True)`
- 流程上下文字段与系统字段为**蛇形列名约定**：`process_instance_id` / `apply_user_id` / `apply_dept_id` / `create_time` / `create_user` / `update_time` / `update_user` / `is_deleted`
- `tf_` 任务字段（如审批意见）在 ARCHIVE 模式不入库；**SYNC 模式**下冗余到业务表对应列（见 §2.1）

> **本仓实测差异**（issues/19）：`create_user` / `update_user` 默认值是 `operator`（流程发起人），不是字面量 `"system"`——因为 `_resolve_default_user` 优先取 `data["apply_user_id"]`。多数框架业务表 `create_user` 为 BIGINT 存 userId，开箱即用。

---

## 2.1 同步演进模式（SYNC，v1.8.0）

流程定义顶层加 `"persistMode": "SYNC"`，改为**全程留痕**——提交申请即入库，任务节点推进更新，结束定稿最终状态，不管成功失败都入库：

```json
{
  "name": "leave",
  "displayName": "请假审批",
  "type": "approval",
  "relTableName": "biz_leave",
  "persistMode": "SYNC",
  "postInterceptors": "persistPost",
  "nodes": []
}
```

（`persistMode` 缺省 `ARCHIVE`——保持 v1.6.2 起的"结束同意归档"行为不变）

### 执行时序（`vendor/jeeflow/persist.py:376 _handle_sync`）

| 时机 | 动作 | 表内数据 |
|---|---|---|
| 发起（start 节点）| INSERT | `f_*` 全量 + 上下文 + 系统字段 |
| 任务节点推进 | UPDATE | `f_*`（按节点字段权限过滤）+ `tf_*` 冗余 + 状态列 = 10（DOING）|
| 结束（同意）| UPDATE | 状态列 = 20（FINISHED）|
| 结束（驳回）| UPDATE | 状态列 = 45（REJECT），数据保留 |

### 状态字段（`_put_state_field` 行 468）

状态列名约定：值 = 流程实例状态码（`10` DOING / `20` FINISHED / `45` REJECT / `50` PENDING），列名优先 `{节点ID}_{状态码}`（如 `task1_10`），无该列回落 `{节点ID}`（如 `task1`）。

```sql
-- 业务表（SYNC 示例）
CREATE TABLE biz_leave (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(100),        -- f_title
  amount DECIMAL(10,2),      -- f_amount
  opinion VARCHAR(200),      -- tf_opinion（审批意见冗余，可选）
  apply INT,                 -- 状态列：节点 apply（发起申请）
  task1 INT,                 -- 状态列：节点 task1（上级审批）
  finish INT,                -- 状态列：结束节点（最终状态）
  process_instance_id BIGINT,
  apply_user_id VARCHAR(50),
  ...
);
```

### 字段权限（任务节点级，v1.8.0+）

任务节点 `properties.field` 声明该节点哪些表单字段可更新（vben5-wf 机制）。**键格式双兼容**（v1.8.1+ issues/25）：`PERMISSION_f_{表单字段全名}`（**前端设计器约定，优先**） 与 `PERMISSION_{去前缀名}`（v1.8.0 首版格式，兼容）——两者都匹配：

```json
{
  "id": "task1",
  "type": "snaker:task",
  "properties": {
    "assignee": "leader",
    "field": { "PERMISSION_f_title": 1, "PERMISSION_amount": 2 }
  }
}
```

> 上面示例：`title` 只读（前端格式 `PERMISSION_f_title`）、`amount` 可编辑（兼容格式 `PERMISSION_amount`）——两种键格式可混用。

| 值 | 语义 | 持久化 | 缺省 |
|---|---|---|---|
| 1 | 只读 | 不更新 | — |
| 2 | 可编辑 | 更新 | ✅ |
| 3 | 隐藏 | 不更新 | — |

> **本仓实现关键**（`_is_editable` 行 453）：只有**任务节点**按权限过滤更新；结束/网关等非任务节点不覆盖业务字段（只定稿状态），避免全量覆盖任务节点的只读/隐藏限制。

---

## 4. 注意事项（踩坑清单）

1. **表不存在会报错**：`relTableName` 解析出来后表不存在 = 配置错误，流程执行失败（`persist.py:157 raise ValueError("persist: table {table_name!r} not found")`）
2. **幂等是双层防护**（`persist.py:417 _mark_chain` + `:197 exists`）：
   - ① 同链节点级内存标记 `__persist_executed_{instanceId}_{节点ID}`（v1.8.0+ 按节点放行——任务推进与结束定稿是不同节点都要生效）
   - ② `process_instance_id` 先查后插/更（跨请求/重启兜底）
3. **`sys_` 前缀表拒绝写入**：`persist.py:287` 防误写框架保留表空间
4. **ARCHIVE 只同意落库**：不同意/退回（`submitType=2`）不入库；**SYNC 驳回也入库**（发起已落库，结束定稿 REJECT 状态）
5. **拦截器必须注册**：未注册时 `engine.py:1071` 抛 `ValueError(拦截器未注册: persistPost)`（**不静默跳过**）；`writer is None` 或 `loader is None` 才静默跳过（`persist.py:341`）
6. **SYNC 状态列**：状态字段按当前节点探测（`{节点ID}_{状态码}` → `{节点ID}`），表无对应列则跳过不报错（`filter_columns` 兜底）

> **本仓补充 2 条**：
>
> | 坑 | 表现 | 修复 |
> |---|---|---|
> | **非自增主键未配置生成器** | `ValueError("persist: table {t!r} primary key {c!r} is not auto-increment and no primary key generator configured")` | `writer.primary_key_generator = lambda t: snowflake_id_worker()`（persist.py:101）|
> | **方言占位符不匹配**（pymysql / psycopg2） | `pymysql.err.ProgrammingError: syntax error`（`?` vs `%s`）| `_placeholder` 自动选（sqlite/h2 用 `?`，mysql/postgres 用 `%s`，persist.py:116）；旧 `exists` / `update` 内部走 `_placeholder`，但要注意传入连接必须是 DB-API 2.0 标准 |

---

## 5. 验证（本仓 PG 后端）

> **上游 SQL 验证整段重写为本仓 PG 后端验证语句**。

```sql
-- ARCHIVE：跑完一条审批流（同意）后
psql "postgresql://postgres:postgres@127.0.0.1:5432/biz" -c "
  SELECT * FROM biz_leave WHERE process_instance_id = 123;
"
-- 应恰好 1 条记录，且 process_instance_id = 流程实例 ID
-- 重复触发同一实例的结束（如重放请求）：记录数仍为 1（writer.exists 兜底幂等）

-- SYNC：发起后即有记录（状态列 = apply 未动），推进后状态更新，结束后定稿
psql "postgresql://postgres:postgres@127.0.0.1:5432/biz" -c "
  SELECT title, apply, task1, finish
  FROM biz_leave
  WHERE process_instance_id = 123;
"
-- 同意 → finish = 20；驳回 → finish = 45（记录保留，不删除）
```

```bash
# 验证幂等（手工触发两次结束）
curl -X POST http://localhost:8101/wf/processInstance/startAndExecute \
  -H 'Content-Type: application/json' \
  -d '{"processDefineId": <id>, "operator": "user1", "f_title": "重复测试", "f_amount": 100}'
# 走完所有 task 后再手动 POST 一次结束动作（重放）
# psql 查 biz_leave 应仍 1 条记录
```

> **四语言合规测试矩阵**见 [上游规范 09 · 业务数据通用入库](https://jeeflow-doc.mldong.com/spec/09-persist)。本仓 Python 实现已通过该矩阵全部用例（issues/18 关闭）。