# 10 · 元数据驱动的动态写入/读取（persist-meta 规范）

> **来源**：https://jeeflow-doc.mldong.com/spec/10-persist-meta
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**元数据驱动落库与回显权威契约**——理解 `storageType` 5 枚举、`persist-meta/<table>.json` 配置格式、EXPAND/JSON/ONE2ONE/ONE2MANY 写入读取语义是设计复杂表单（地址对象 / 附件 JSON / 明细子表）的前提。
>
> **本仓实现版本**：`vendor/jeeflow/meta.py`（**已完整实现** v1.8.0 全契约）：`StorageType(IntEnum)` + `FieldMeta` / `TableMeta` + `IDynamicMetaProvider` + `JsonMetaProvider` + `MetaTableWriter` + `JdbcTableReader` + `MetaTableReader` + **Async** 版本（FIX-T95 §6.1.2，asyncpg pool）。
>
> **裁剪记录**：§1 / §2 / §3 / §4 / §5 / §6 保留 + 加本仓实测注解；§7 版本与发布裁掉。

---

## §1. 目标与边界

### 做（最小闭环）

- 字段元数据（`storageType`）驱动的**动态写入**（NORMAL / EXPAND / JSON / ONE2ONE / ONE2MANY）
- 按流程实例的**动态读取回显**（`read_by_process_instance`，与写入共用同一份元数据）
- 元数据来源可插拔（SPI），内置 **JSON 配置加载器**（零依赖）

### 不做（明确边界）

通用条件分页 / 动态条件语法（`m_EQ_xxx`）/ 数据权限 / 排序——集成方查询体系（如 mldong tablePage）的领域，**双方共享字段元数据规范保持语义一致**。

> 与 `DynamicTableWriter`（spec 09）的关系：**演进而非推翻**——现有 SPI 保留，无元数据回落现状。

---

## §2. 元数据模型（本仓实测）

> **本仓实现**：`vendor/jeeflow/meta.py:45 FieldMeta` + `:60 TableMeta` + `:24 StorageType(IntEnum)` —— 与上游契约完全一致。

### 2.1 JSON 配置字段语义

**`persist-meta/<table>.json`**（文件名 = 表名）：

| 顶层字段 | 类型 | 缺省 | 语义 |
|---|---|---|---|
| `tableName` | string | 必填 | 业务表名（应与 JSON 文件名一致）|
| `primaryKey` | string | `id` | 主键列名（ONE2ONE/ONE2MANY 子表外键缺省回落它）|
| `fields` | array | 必填 | 字段定义列表 |

**`fields[]` 元素**（本仓 `meta.py:45 FieldMeta` 数据类）：

| 字段 | 类型 | 缺省 | 语义 |
|---|---|---|---|
| `name` | string | 必填 | **表单字段名**（实例 Variables 中 `f_` 去前缀后的名字，如 `f_title` → `title`）|
| `column_name` | string | name 转下划线（`meta.py:81 to_underline`）| 主表列名（如 `companyName` → `company_name`）|
| `storage_type` | string/int | `NORMAL` | 存储类型——名称或数字双解析（`_parse_storage_type`）|
| `expand_fields` | object | 空 | **EXPAND 专用**：子字段名 → 表列名映射 |
| `target_table` | string | 空 | **ONE2ONE/ONE2MANY 专用**：子表表名 |
| `foreign_key` | string | 主表 `primaryKey` | **ONE2ONE/ONE2MANY 专用**：子表外键列 |

### 2.2 `storage_type` 5 取值（本仓 `meta.py:24 StorageType(IntEnum)`）

| 值 | 名称 | 语义 |
|---|---|---|
| `1` | `NORMAL` | 直写列（默认）|
| `2` | `EXPAND` | 对象展开为多列（`expand_fields` 定义子字段列映射）|
| `3` | `JSON` | 对象/数组序列化为 JSON 串写列 |
| `4` | `ONE2ONE` | 子表单条递归插入（外键 = 主表主键，同事务）|
| `5` | `ONE2MANY` | 子表多条递归插入（data 值为数组，同事务）|

**JSON 配置示例**（`persist-meta/biz_leave.json`）：

```json
{
  "tableName": "biz_leave",
  "primaryKey": "id",
  "fields": [
    { "name": "companyName", "columnName": "company_name", "storageType": "NORMAL" },
    { "name": "address", "storageType": "EXPAND",
      "expandFields": { "province": "province", "city": "city", "detail": "detail_addr" } },
    { "name": "extra", "storageType": "JSON" },
    { "name": "items", "storageType": "ONE2MANY",
      "targetTable": "biz_leave_item", "foreignKey": "leave_id" }
  ]
}
```

---

## §3. SPI（本仓 Python）

> **本仓实现**：`vendor/jeeflow/meta.py:96 IDynamicMetaProvider`（abstract class，1 个方法）。

```python
class IDynamicMetaProvider:
    """加载表元数据；未定义返回 None（回落表结构探测，全 NORMAL 语义）"""
    def load_table_meta(self, table_name: str) -> Optional[TableMeta]:
        raise NotImplementedError
```

- **内置 `JsonMetaProvider`**（`meta.py:105`）：从文件系统 / classpath 加载 `persist-meta/*.json`
- **写、读共用**：写入引擎与回显读取都按同一份元数据执行，`storageType` 语义两侧一致
- **默认回落**：未配元数据时行为与 v1.6.x 完全一致（零破坏）

---

## §4. 组件分工（读写职责分离）

```
写侧（DynamicTableWriter 接口不变）
   ├── JdbcDynamicTableWriter   现状：表结构探测，全 NORMAL
   └── MetaTableWriter          新：元数据驱动（NORMAL/JSON/EXPAND/子表递归）

读侧（流程回显最小闭环）
   JdbcTableReader              底层行查询（按列等值，limit）
   MetaTableReader              read_by_process_instance：storageType 反序列化 + 子表组装
```

> **本仓实测**（`meta.py:141 MetaTableWriter(DynamicTableWriter)` + `:293 MetaTableReader`）：写侧继承 `DynamicTableWriter`（保持 spec 09 接口契约不变），读侧为独立 `MetaTableReader`，共用同一份 `JsonMetaProvider`。

---

## §5. 写入语义（MetaTableWriter）

> **本仓实现**：`vendor/jeeflow/meta.py:141 MetaTableWriter`，继承 `DynamicTableWriter`，完全实现 5 storageType 写入语义。

| storageType | 写入 |
|---|---|
| **NORMAL** | 直写（列名宽松匹配沿用 spec 09）|
| **EXPAND** | 对象字段展开为多列（`address.province` → `province` 列）|
| **JSON** | 对象/数组序列化为 JSON 串写列 |
| **ONE2ONE** | 子表单条递归插入（外键 = 主表主键），同事务 |
| **ONE2MANY** | 子表多条递归插入（data 值为数组），同事务 |

**复用现有能力**：

- 主键生成（含非自增雪花，生成器返回主键供子表外键）
- 系统字段（`create_user` / `update_user` 等）
- 同链防重（`__persist_executed_{instanceId}_{节点ID}`）
- schema 限定探测（MySQL `DATABASE()` / PG `CURRENT_SCHEMA()`）
- 未消费字段（流程上下文 `process_instance_id` 等）直通

**中途更新**（`update`，v1.8.0）：按元数据 `storageType` 组装 SET 列——NORMAL / JSON / EXPAND 参与更新；**ONE2ONE / ONE2MANY 子表不参与中途更新**（SYNC 任务推进只更新主表行状态，子表数据变动走重新提交）；未消费字段直通。无元数据回落基础 writer。

**子表系统用户字段**（v1.8.0）：子表递归插入时**继承主表 `apply_user_id`**（拦截器场景 = 流程 operator，`putIfAbsent` 子表单显式同名字段优先）——避免 BIGINT `create_user` / `update_user` 列回落 `"system"` 严格模式报错。

---

## §6. 读取语义（MetaTableReader）

> **本仓实现**：`vendor/jeeflow/meta.py:331 MetaTableReader.read_by_process_instance(table_name, process_instance_id)`。

| storageType | 读取 |
|---|---|
| **NORMAL** | 直读列 |
| **EXPAND** | 反展开为对象（`province/city/detail_addr` → `address.province/...`）|
| **JSON** | 反序列化为对象/数组 |
| **ONE2ONE** | 按外键 = 主表主键查子表单条，组装为对象 |
| **ONE2MANY** | 按外键 = 主表主键查子表多条，组装为数组 |

**关键规则**：

- 定位键 `process_instance_id`（写入幂等键同款）
- 未消费列（流程上下文 / 系统字段）统一小写带出（跨方言一致）
- **EXPAND 展开列不重复平铺带出**（v1.8.0）：`province/city/detail_addr` 已消费为 `address` 对象，不再作为顶层平铺键重复出现
- 无元数据回落原始行（列名→值）
- **Async 版本**（FIX-T95 §6.1.2）：`AsyncMetaTableReader` + `asyncpg pool` + 占位符 `$n`（PostgreSQL 风格）

**调用入口**（facade.py:1076 `processInstance_bizData`）：

```python
# 同步（sqlite / mysql）
form = meta_reader.read_by_process_instance("biz_leave", instance_id)

# 异步（PG asyncpg pool）
async with AsyncMetaTableReader(conn) as reader:
    form = await reader.read_by_process_instance("biz_leave", instance_id)

# facade 入口（统一门面包）
curl -X POST http://localhost:8101/wf/processInstance/bizData \
  -H 'Content-Type: application/json' \
  -d '{"id": <instance_id>}'
```

> **未注入 meta_reader**：`facade.py:1090-1091` 抛清晰错误 `ValueError("业务数据读取器未注册（facade.set_meta_reader(MetaTableReader(...))，需引入 jeeflow.meta）")` —— 不静默跳过。

---

## 设计者实操速查

| 场景 | 实践 |
|---|---|
| 简单字段（文本/数字/日期）| `storageType: NORMAL` 或省略 |
| 地址对象（多列）| `storageType: EXPAND` + `expandFields: {子字段名: 表列名}` |
| 附件 JSON（任意结构）| `storageType: JSON`（列类型 VARCHAR / TEXT）|
| 单条子表单条 | `storageType: ONE2ONE` + `targetTable` + `foreignKey` |
| 多条明细子表 | `storageType: ONE2MANY` + `targetTable` + `foreignKey` |
| 中途更新（SYNC）| NORMAL / JSON / EXPAND 参与；**ONE2ONE / ONE2MANY 不参与**——子表变动走重新提交 |
| 流程详情回显 | `facade.set_meta_reader(MetaTableReader(...))` 或 `AsyncMetaTableReader(...)` |
| 子表继承主表 `apply_user_id` | "BIGINT `create_user` 列不会回落 'system' 严格模式报错"（v1.8.0） |
| EXPAND 字段读侧 | 不会作为顶层平铺键重复出现（v1.8.0 修复） |
| 测试 | 跑 `tdd-flow.py <flow>.json` + `ea-compliance.py` + 手工验证 `bizData` 端点 |