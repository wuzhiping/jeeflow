# 09 · 业务数据通用入库（persist 契约）

> **来源**：https://jeeflow-doc.mldong.com/spec/09-persist
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**业务数据持久化权威契约**——理解 ARCHIVE / SYNC 双模式时机、`relTableName` / `persistMode` 顶层字段、字段权限双兼容、幂等双层防护是设计正确落库流程的前提。
>
> **本仓实现版本**：`vendor/jeeflow/persist.py`（**已完整实现** v1.8.0 全契约）：`DynamicTableWriter`(ABC) + `JdbcDynamicTableWriter`(具体实现) + `PersistPostInterceptor`(ARCHIVE + SYNC 双模式) + `register_persist_meta`(元注册助手)。
>
> **裁剪记录**：§1 / §2 / §3 / §4 / §5 / §6 保留 + 加本仓实测注解；§7 版本与发布裁掉（属部署者职责）。

---

## §1. 组件分层

```
流程设计器配置（Java postInterceptors 类名 / 其余语言全局注册拦截器）
        │
        ▼
PersistPostInterceptor（引擎适配层，~100 行/语言）
  时机判断 / f_ 字段提取 / 表名解析 / 幂等键 / 流程上下文字段
        │
        ▼
DynamicTableWriter（引擎无关核心，~150 行/语言）
  列过滤 → 参数化 INSERT → 系统字段 → 幂等 exists
```

- **DynamicTableWriter 不依赖工作流引擎**：任何「给表名 + 字段 Map 安全写业务表」的需求都可直接使用
- **PersistPostInterceptor 只做流程语义适配**：把「何时写、写什么、写哪张表」翻译成组件调用

---

## §2. DynamicTableWriter 接口（本仓 Python 实测）

> **本仓实现**：`vendor/jeeflow/persist.py:28 DynamicTableWriter(ABC)`，5 个 `@abstractmethod` 完整对齐上游契约。

```python
# vendor/jeeflow/persist.py:28
class DynamicTableWriter(ABC):
    @abstractmethod
    def filter_columns(self, table_name: str, columns: Sequence[str]) -> list[str]: ...

    @abstractmethod
    def insert(self, table_name: str, data: dict[str, Any]) -> Any: ...

    @abstractmethod
    def update(self, table_name: str, data: dict[str, Any],
               where_column: str, where_value: Any) -> int: ...

    @abstractmethod
    def exists(self, table_name: str, biz_key: str, biz_key_value: Any) -> bool: ...

    @abstractmethod
    def fill_system_fields(self, data: dict[str, Any], is_insert: bool) -> None: ...
```

> **本仓实测补充**：`update` 在上游契约**默认抛 `UnsupportedOperationException`**（缺省 writer 不支持）；本仓 `JdbcDynamicTableWriter:205 update()` 是**完整实现**（SYNC 同步演进需要，issues/24）。

---

## §3. 默认实现 JdbcDynamicTableWriter

> **本仓实现**：`vendor/jeeflow/persist.py:66 JdbcDynamicTableWriter(DynamicTableWriter)`，**8 项通用行为完整对齐上游契约**。

| # | 通用行为 | 本仓实测位置 |
|---|---|---|
| 1 | **表名安全**：`sys_` 前缀拒绝（框架保留）；非法字符（非字母数字下划线）拒绝 | `persist.py:283 _check_table_name` |
| 2 | **列过滤**：按目标表实际列过滤，多传的字段自动丢弃 | `persist.py:163 filter_columns` |
| 3 | **参数化 INSERT**：占位符 + 参数化 SET；值注入不生效 | `persist.py:168 insert`（占位符走 `_placeholder()`） |
| 4 | **列匹配**（v1.8.0，issues/20）：默认宽松（驼峰↔下划线归一匹配）；`set_strict_column_match(True)` 严格 | `persist.py:258 _find_table_column` + `:100 strict_column_match` |
| 5 | **系统字段**：`create_time` / `create_user` / `update_time` / `update_user` / `is_deleted`（可配置列名，`null` 禁用） | `persist.py:231 fill_system_fields` |
| 6 | **用户列默认值**（v1.8.0，issues/19）：`create_user`/`update_user` 优先取 `apply_user_id`（= 流程 operator）；无 operator 回落配置（缺省 `"system"`） | `persist.py:250 _resolve_default_user` + `:97 default_user_value` |
| 7 | **主键生成**（v1.8.0，issues/21）：自增检测 + 可配置生成器 `set_primary_key_generator(表名→主键值)`；data 已有主键用之 → 自增不生成 → 非自增未配置生成器抛清晰错误 | `persist.py:101 primary_key_generator` + `:183 raise ValueError` |
| 8 | **schema 限定**（v1.8.0，issues/22）：information_schema 探测限定当前 schema（MySQL `DATABASE()`；PG/H2 `CURRENT_SCHEMA()`）| `persist.py:130 MySQL` + `:140 PG/H2` |

---

## §4. PersistPostInterceptor 语义契约

### 4.0 流程定义配置字段（集成方只声明这两个）

**行为契约四语言统一**：持久化由**流程定义 JSON 顶层**的两个字段驱动：

| 字段 | 取值 | 语义 |
|---|---|---|
| `relTableName` | 表名 | **业务表名**——拦截器把流程数据写入哪张表；**缺省回落流程 `name`**。表名解析出来后表不存在 = 配置错误显性报错 |
| `persistMode` | `ARCHIVE` / `SYNC`（**缺省 `ARCHIVE`**）| **持久化模式**——`ARCHIVE`：流程结束且同意时落库一次（归档快照）；`SYNC`：提交申请即入库 → 任务节点推进更新 → 结束定稿，全程留痕 |

```json
{
  "name": "leave",
  "type": "approval",
  "relTableName": "biz_leave",
  "persistMode": "SYNC",
  "nodes": []
}
```

**拦截器挂载机制（1.8.4 起四语言统一「定义级声明」）**：

| 语言 | 定义级挂载（1.8.4 起）| 引擎级挂载（向后兼容）|
|---|---|---|
| Java | 流程定义顶层 `postInterceptors` 声明拦截器类名，引擎**反射实例化**（模型级） | `ServiceContext` 注册 |
| Go / Python / Node | 流程定义顶层 `postInterceptors` 声明名字，引擎**按名从注册表解析** | 引擎级 `Extensions.Interceptors` 列表 |

> **本仓实测**（`persist.py:307 PersistPostInterceptor`）：post_handle 钩子按定义级声明过滤——流程定义声明了 `postInterceptors` 才生效；未声明的流程不触发。

### 4.1 ARCHIVE 时机（缺省）

仅**流程正常结束**时入库：

| 条件 | 判定 |
|---|---|
| 节点 | 结束节点（`snaker:end`） |
| 实例状态 | FINISHED（Python enum `InstanceState.DONE`） |
| submitType | `AGREE(1)` —— 不同意 / 退回不入库 |

> **引擎对齐**（v1.6.2 起）：结束节点统一走节点执行链，**后置拦截器在流程结束时完整触发**——老版本 Go/Python/Node 任务完成路径内联 finish 不触发拦截器，已修复。

### 4.2 SYNC 时机（v1.8.0 同步演进）

按节点类型三态路由（`exists` 先查后插/更）：

| 节点 | 动作 | 写入内容 |
|---|---|---|
| **开始节点（发起）** | `INSERT` 全量 | `f_*` 全部表单字段 + 上下文 + 系统字段（插入组） |
| **任务节点（推进）** | `UPDATE` | `f_*` **按节点字段权限过滤** + `tf_*` 冗余（有列则写）+ 状态字段 = DOING(10) |
| **结束节点（定稿）** | `UPDATE` | 仅状态字段 = 实例最终态（FINISHED=20 / REJECT=45）+ 上下文 |

**字段权限**（SYNC 任务节点，vben5-wf 机制）：任务节点 `properties.field` 声明该节点对表单字段的编辑权限。

**键格式双兼容**（v1.8.1+ issues/25）：

| 键格式 | 示例 | 优先级 |
|---|---|---|
| `PERMISSION_f_{表单字段全名}` | `"PERMISSION_f_title": 1` | **优先**（前端 vben5-wf 设计器约定）|
| `PERMISSION_{去前缀名}` | `"PERMISSION_title": 1` | 兼容（v1.8.0 首版格式）|

| 值 | 语义 | 持久化 |
|---|---|---|
| 缺省 | 可编辑 | 更新 |
| `1` | 只读 | 不更新 |
| `2` | 可编辑 | 更新 |
| `3` | 隐藏 | 不更新 |

> **v1.8.2 起引擎办理入口过滤**（`persist.py:453 _is_editable` + `engine.py:filterFieldByPerm`）：值非 EDIT(2) 的 `f_*` 字段在入变量前即被剔除——被拒值无法经流程变量落到下游节点写入。1.8.0/1.8.1 只有拦截器写入侧过滤，上游只读可被下游绕过。

**状态字段**（SYNC）：值 = 实例状态码（10 / 20 / 45 / 50），列名优先 `{节点ID}_{状态码}`（如 `task1_10`），无该列回落 `{节点ID}`（如 `task1`）——列探测过滤，表无对应列则跳过。

**`tf_` 冗余**（SYNC）：任务节点提交的 `tf_` 前缀变量（如 `tf_opinion` 审批意见）去前缀冗余到业务表对应列（列过滤由 writer 做）。

### 4.3 字段契约

| 来源 | 规则 |
|---|---|
| 表单字段 | 实例 Variables 中 `f_` 前缀字段，**去前缀**（如 `f_title` → `title`） |
| 流程上下文 | `process_instance_id`（实例 ID）/ `apply_user_id`（发起人）/ `apply_dept_id`（`u_deptId`），**蛇形列名约定** |
| 系统字段 | writer 通用字段（见 §3），插入/更新模式 |

### 4.4 表名解析

1. 流程定义顶层 `relTableName`（`ProcessModel.relTableName`）
2. 缺省回落**流程 `name`**（流程唯一编码 = 业务表名约定）

> **本仓实测**（`persist.py:404 _resolve_define`）：从 `loader(instance.defineId)` 异步加载 ProcessDefine，`json.loads(define.content)` 解 JSON 后读 `meta["relTableName"]` / `meta["persistMode"]`。

### 4.5 幂等（双层防护，v1.8.0 改节点级）

> **本仓实测**（`persist.py:417 _mark_chain` + `:197 exists`）：

| 层 | 机制 | 作用域 | 说明 |
|---|---|---|---|
| ① **同链内存标记** | `__persist_executed_{instanceId}_{节点ID}` 写入执行链共享状态（Python `inst.variables`）| 同一次执行链 | **每个节点**触发一次（任务推进更新 + 结束定稿是不同节点，都要生效），同节点不重复 |
| ② **数据库幂等** | `exists(process_instance_id)` 先查后插/更 | 跨请求/重启 | 兜底（独立连接、事务提交后生效）|

> v1.8.0 把标记从「实例级」改为「节点级」：SYNC 下任务节点与结束节点都要各自生效，实例级标记会跳过任务节点的推进更新。

### 4.6 静默跳过 vs 显性报错

| 场景 | 行为 | 本仓实测 |
|---|---|---|
| 非结束节点（ARCHIVE）/ 非同意 / 实例非完成态 | 静默跳过 | `persist.py:357-363` |
| writer 未注入 | 静默跳过（挂载了但没配组件）| `persist.py:341` |
| 未配置表名（relTableName 与流程 name 皆空）| 静默跳过 | `persist.py:346` |
| **表名解析出来了但表不存在** | **显性报错**（配置错误快速失败）| `persist.py:157 raise ValueError("persist: table {table_name!r} not found")` |

---

## §5. 挂载方式（本仓 Python）

> **上游 4 语言示例整段裁 Java/Go/Node，仅保留 Python**。

```python
# main_common.py:build_persist_components()
from jeeflow.persist import JdbcDynamicTableWriter, PersistPostInterceptor

def build_persist_components(repo):
    conn = sqlite3.connect("biz.db")  # 或 pymysql / psycopg2
    writer = JdbcDynamicTableWriter(
        conn,
        create_time_column="create_time",
        create_user_column="create_user",
        update_time_column="update_time",
        update_user_column="update_user",
        is_deleted_column="is_deleted",
        # primary_key_generator=lambda t: snowflake_id_worker(),  # 非自增主键必备
        # strict_column_match=False,                              # 宽松匹配（默认）
    )
    interceptor = PersistPostInterceptor(
        writer=writer,
        loader=repo.find_define_by_id,
    )
    return writer, interceptor
```

```python
# 应用到 engine（main_common.py:apply_extensions）
from jeeflow import EngineExtensions, HandlerRegistry
from jeeflow.persist import register_persist_meta
from main_common import apply_extensions

registry = HandlerRegistry()
register_persist_meta(registry)  # 注册 PersistPostInterceptor 元数据

ext = EngineExtensions(
    registry=registry,
    interceptor_registry={"persistPost": interceptor},
)
engine.set_extensions(ext)
```

---

## §6. 合规测试矩阵（18 用例）

> **本仓实测状态**：`docs/BUGS.md` 声明 27 个已修复 BUG（FIX-T1~T38），含 persist 相关 FIX（T3 比例会签、T37 复合表达式、T38 custom handler 等），**全 PASS**。

| # | 用例 | 本仓实测位置 |
|---|---|---|
| 1 | 流程结束同意 → 落库（ARCHIVE）| `_handle_archive:355` |
| 2 | 拒绝（submitType=2，ARCHIVE）→ 不入库 | `submitType != AGREE:362` |
| 3 | 不同意（submitType=0，ARCHIVE）→ 不入库 | 同上 |
| 4 | writer 未注入 → 静默跳过 | `:341` |
| 5 | **表不存在 → 显性报错** | `:157 raise ValueError` |
| 6 | 幂等（跨请求）| `exists:197` 先查后插 |
| 7 | 幂等（同链节点级）| `_mark_chain:417` |
| 8 | 用户列默认值 → `create_user` 取 operator | `_resolve_default_user:250` |
| 9 | BIGINT 用户列 → operator 数字插入 | 同上 |
| 10 | **SYNC 全链路**（发起 INSERT → 任务推进 UPDATE → 结束定稿 UPDATE）| `_handle_sync:376` |
| 11 | **SYNC 驳回** → 结束节点定稿 REJECT=45，数据不丢 | `:389 state_code` 走实例 state |
| 12 | **SYNC 字段权限**（双键格式）| `_is_editable:453` |
| 13 | writer 全字段插入 | `insert:168` |
| 14 | **缺列过滤** | `filter_columns:163` |
| 15 | 类型 null → 显式 null 正常入库 | `insert:174 if key is not None` |
| 16 | **防注入** | 参数化占位符（`_execute:107`） |
| 17 | 宽松列匹配（驼峰↔下划线）| `_normalize:278` |
| 18 | 严格列匹配 → `set_strict_column_match(True)` 显式开启 | `_find_table_column:258` |
| 19 | 非自增主键生成 → 雪花/应用生成主键表配生成器 | `:181-187 raise ValueError` |
| 20 | 未配置生成器 → 清晰报错 | 同上 |
| 21 | 多 schema 同名表 → 不混入 | `_table_columns:120 schema 限定` |
| 22 | `sys_` 前缀 / 非法字符表名 → 拒绝 | `_check_table_name:283` |

---

## 设计者实操速查

| 场景 | 实践 |
|---|---|
| 写流程 JSON | 顶层加 `"relTableName": "biz_xxx"` + `"persistMode": "ARCHIVE"` 或 `"SYNC"` |
| 字段权限 | 任务节点 `properties.field` 加 `PERMISSION_f_<name>: 1/2/3`（**前端格式优先**） |
| 状态字段 | 建表时建 `{节点ID}_{状态码}` 列（如 `task1_10`） |
| 测试 | 跑 `tdd-flow.py <flow>.json` + `ea-compliance.py`（含 §9.4 persist 配置检查）|
| 业务表 schema 探测 | JdbcDynamicTableWriter 自动按方言探测（sqlite PRAGMA / MySQL/PG/H2 information_schema）|
| 多 schema 部署 | MySQL 限定 `DATABASE()`；PG/H2 限定 `CURRENT_SCHEMA()` |