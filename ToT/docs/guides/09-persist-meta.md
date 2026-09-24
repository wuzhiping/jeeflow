# 09 · 元数据驱动入库（复杂表单落库与回显）

> **来源**：https://jeeflow-doc.mldong.com/guides/09-persist-meta
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**复杂表单（对象 / JSON / 子表）落库与回显设计指南**。
>
> **本仓实现版本**：基于 `vendor/jeeflow/meta.py`（**已完整实现**）：`StorageType` 5 枚举（NORMAL/EXPAND/JSON/ONE2ONE/ONE2MANY）+ `FieldMeta` / `TableMeta` 元数据模型 + `IDynamicMetaProvider` SPI + `JsonMetaProvider`（内置 JSON 加载器）+ `MetaTableWriter`（元数据驱动写）+ `JdbcTableReader`（读侧底层）+ `MetaTableReader`（流程回显）+ **Async** 版本（FIX-T95 §6.1.2，asyncpg pool）。
>
> **裁剪记录**：§1 / §2.① / §2.③ / §3 保留 + 加本仓实现注解；§2.② Java/Go/Node 裁掉仅留 Python 重写；§4 SQL 重写为本仓 PG 后端验证。

---

## 1. 适用场景

| 场景 | 说明 |
|---|---|
| 复杂表单落库 | 对象字段展开为多列（EXPAND）、JSON 字段序列化（JSON）、子表明细（ONE2ONE / ONE2MANY）|
| 流程详情回显 | 按流程实例 ID 读回完整业务数据（对象 / JSON / 子表自动组装）|
| 元数据驱动 | 集成方只配 JSON（或实现 SPI），不再写插入/反序列化逻辑 |
| 简单表 + 复杂表共存 | 简单表（全 NORMAL 字段）用 `08-persist.md` 的 `JdbcDynamicTableWriter`；复杂表用 `MetaTableWriter` + 元数据；**两者可共存**（无元数据回落基础 writer）|

> **本仓 StorageType 5 枚举**（`vendor/jeeflow/meta.py:24`，IntEnum 数字 / 名称双兼容）：
>
> | 值 | 名称 | 语义 |
> |---|---|---|
> | `1` | `NORMAL` | 直写列（默认）|
> | `2` | `EXPAND` | 对象展开为多列（`expand_fields` 定义子字段列映射）|
> | `3` | `JSON` | 对象 / 数组序列化为 JSON 串写列 |
> | `4` | `ONE2ONE` | 子表单条（外键 = 主表主键，同事务）|
> | `5` | `ONE2MANY` | 子表多条（外键 = 主表主键，同事务）|

---

## 2. 三步接入

### ① 编写元数据 JSON

`persist-meta/biz_leave.json`（文件系统或 classpath，文件名 = 表名）：

```json
{
  "tableName": "biz_leave",
  "primaryKey": "id",
  "fields": [
    { "name": "companyName", "columnName": "company_name" },
    { "name": "address", "storageType": "EXPAND",
      "expandFields": { "province": "province", "city": "city", "detail": "detail_addr" } },
    { "name": "extra", "storageType": "JSON" },
    { "name": "items", "storageType": "ONE2MANY",
      "targetTable": "biz_leave_item", "foreignKey": "leave_id" }
  ]
}
```

> **本仓元数据模型**（`vendor/jeeflow/meta.py:44 FieldMeta` + `:59 TableMeta`）：
>
> | `FieldMeta` 字段 | 含义 |
> |---|---|
> | `name` | 表单字段名（`f_` 去前缀）|
> | `column_name` | 主表列名（缺省 = `name` 转下划线，`meta.py:81 to_underline`）|
> | `storage_type` | 见上表 StorageType 5 枚举（`meta.py:24`）|
> | `expand_fields` | EXPAND 子字段名 → 表列名映射 |
> | `target_table` | ONE2ONE / ONE2MANY 子表表名 |
> | `foreign_key` | 子表外键列（缺省 = 主表主键列名）|
>
> 规则：
> - `columnName` 缺省 = `name` 转下划线（`companyName` → `company_name`）
> - 子表字段（ONE2ONE / ONE2MANY）需 `targetTable`；`foreignKey` 缺省 = 主表主键列名
> - storageType 支持名称（`"EXPAND"`）或数字（`2`）——`_parse_storage_type` 行 33

### ② 装配（本仓 Python）

> **上游 4 语言示例整段裁 Java/Go/Node，仅保留 Python**。

```python
# main_common.py:build_persist_meta_components()
from jeeflow.meta import (
    MetaTableWriter,
    MetaTableReader,
    JdbcTableReader,
    JsonMetaProvider,
)
from jeeflow.persist import JdbcDynamicTableWriter

def build_persist_meta_components(conn, persist_meta_dir="persist-meta"):
    """构建元数据驱动组件（写侧 + 读侧）"""
    base_writer = JdbcDynamicTableWriter(conn)
    meta_provider = JsonMetaProvider(persist_meta_dir)   # 加载 persist-meta/*.json

    # 写侧：替换默认 writer（MetaTableWriter 继承 DynamicTableWriter）
    meta_writer = MetaTableWriter(base_writer, meta_provider)

    # 读侧：流程详情接口用
    table_reader = JdbcTableReader(conn)
    meta_reader = MetaTableReader(table_reader, meta_provider)

    return meta_writer, meta_reader
```

```python
# 注入到 facade（facade.py:48 set_meta_reader）
from jeeflow import JeeflowFacade

facade = JeeflowFacade(engine)
facade.set_meta_reader(meta_reader)   # 流程详情接口（bizData 增强）启用
```

> **本仓 SPI 注册点**（`vendor/jeeflow/facade.py`）：
>
> | 方法 | 行号 | 用途 |
> |---|---|---|
> | `set_meta_reader(reader)` | :48 | 注入 `MetaTableReader` 实例（流程详情接口）|
> | `read_by_process_instance(table_name, instance_id)` | :1077 | 按流程实例回显完整业务数据 |
>
> **未注入时报错**（`facade.py:1090-1091`）：`ValueError("业务数据读取器未注册（facade.set_meta_reader(MetaTableReader(...))，需引入 jeeflow.meta）")` —— 清晰报错，**不静默跳过**。
>
> **Async 版本**（FIX-T95 §6.1.2，PG 后端专用）：`AsyncJdbcTableReader` + `AsyncMetaTableReader`，占位符 `$n`（PostgreSQL 风格），适配 asyncpg pool；同步版本（`JdbcTableReader` / `MetaTableReader`）走 `?` 占位符（sqlite 风格）。

### ③ 发起 / 回显（流程定义配置不变）

流程定义仍配 `relTableName` + `postInterceptors`，发起时提交表单变量：

```
f_companyName = "测试公司"
f_address     = { "province": "广东省", "city": "深圳市", "detail": "科技园路1号" }
f_extra       = { "tag": "vip", "level": 3 }
f_items       = [ { "name": "电脑", "qty": 2 }, { "name": "键盘", "qty": 3 } ]
```

流程结束同意后落库：

| 表 | 内容 |
|---|---|
| `biz_leave` | `company_name` / `province` / `city` / `detail_addr`（EXPAND 展开）/ `extra`（JSON 串）/ 流程上下文 + 系统字段 |
| `biz_leave_item` | 2 条明细（`leave_id` = 主表主键）|

回显（流程详情接口，本仓 Python 调用）：

```python
# 同步读侧（sqlite/mysql）
form = meta_reader.read_by_process_instance("biz_leave", instance_id)
# form.address = { province, city, detail }（EXPAND 反展开）
# form.extra   = { tag, level }（JSON 反序列化）
# form.items   = [ { name, qty }, ... ]（ONE2MANY 子表组装）
# form.process_instance_id / apply_user_id ... 原样带出

# 异步读侧（PG 后端，asyncpg pool）
from jeeflow.meta import AsyncMetaTableReader
form = await async_meta_reader.read_by_process_instance("biz_leave", instance_id)
```

```bash
# 或通过 facade API（统一门面）
curl -X POST http://localhost:8101/wf/processInstance/bizData \
  -H 'Content-Type: application/json' \
  -d '{"id": <instance_id>}'
# 内部走 facade.read_by_process_instance(table_name, instance_id)
# table_name 从 process_define.content["relTableName"] 解析
```

> **本仓 facade 解析**：bizData 增强接口在 `facade.py:1077+`，读侧必须先注入 `meta_reader`（即 `facade.set_meta_reader(...)`），否则清晰报错。

---

## 3. 注意事项（踩坑清单）

1. **主键**：子表外键 = 主表主键——非自增表（雪花）必须配 `set_primary_key_generator(...)`，生成器返回的主键自动注入子表外键；主表主键缺失时子表插入报错
2. **EXPAND 列**：展开列必须在主表存在（元数据与 DDL 对齐），多传的子字段自动忽略；回显时展开列不重复平铺带出（v1.8.0，对象形式已消费）
3. **子表元数据**：ONE2ONE / ONE2MANY 的子表也要有自己的 JSON 配置（没有则按 NORMAL 直写 + 原始行回显）
4. **JSON 列**：业务表 JSON 列建议 VARCHAR / TEXT 存串（H2 原生 JSON 类型 JDBC 读取为字节数组，见 spec 09 踩坑）
5. **子表系统用户字段**（v1.8.0）：子表递归插入继承主表 `apply_user_id`（= 流程 operator）——子表 `create_user` / `update_user` 为 BIGINT 时不会回落 `"system"` 导致严格模式报错
6. **中途更新**（v1.8.0）：SYNC 模式下任务推进走 `update`——NORMAL / JSON / EXPAND 参与更新，**ONE2ONE / ONE2MANY 子表不参与中途更新**（子表数据变动走重新提交）
7. **边界**：通用分页 / 条件 / 权限不在本组件——集成方查询体系按同一份元数据规范扩展
8. **回落**：未配元数据的表行为与 v1.6.x 完全一致（零破坏）

> **本仓补充 4 条**：
>
> | 坑 | 表现 | 修复 |
> |---|---|---|
> | **`meta_reader` 未注入** | 调用 `read_by_process_instance` 时抛 `ValueError("业务数据读取器未注册（facade.set_meta_reader(MetaTableReader(...))，需引入 jeeflow.meta）")` | 在 facade 装配时 `facade.set_meta_reader(meta_reader)`（facade.py:48）|
> | **同步 vs Async 选错** | PG 后端用同步 `JdbcTableReader` + 同步 placeholder `?` 报 `syntax error`（PG 期望 `$n`）| PG 后端用 `AsyncJdbcTableReader` + `AsyncMetaTableReader`（FIX-T95 §6.1.2）；或显式 `JdbcDynamicTableWriter(conn, dialect="postgres")` 改占位符 |
> | **`JsonMetaProvider` 路径错** | `FileNotFoundError: persist-meta/biz_xxx.json not found` | `JsonMetaProvider(root_dir)` 的 `root_dir` 必须是**绝对路径**或相对 cwd 的目录；流程 JSON 字段 `tableName` 与文件名严格一致 |
> | **主子表系统字段冲突** | 子表 `create_user` 为 BIGINT 但 writer 写入 `"system"` 字符串 → 类型错误 | 子表递归继承主表 `apply_user_id`（v1.8.0+ `_fill_subtable_context`）；或子表元数据显式 `column_name` 映射 |

---

## 4. 验证（本仓 PG 后端）

> **上游 SQL 验证整段重写为本仓 PG 后端验证语句**。

```sql
-- 跑完一条含明细的审批流（同意）后
psql "postgresql://postgres:postgres@127.0.0.1:5432/biz" -c "
  SELECT * FROM biz_leave WHERE process_instance_id = 123;
"           -- EXPAND 列展开、extra 为 JSON 串、仅 1 条
psql "postgresql://postgres:postgres@127.0.0.1:5432/biz" -c "
  SELECT * FROM biz_leave_item WHERE leave_id = 1;
"           -- 明细多条，leave_id = 主表主键

-- 流程详情接口（facade.read_by_process_instance）
-- 返回对象：address = { province, city, detail }（EXPAND 反展开）
--         extra   = { tag, level }（JSON 反序列化）
--         items   = [ { name, qty }, ... ]（ONE2MANY 子表组装）
```

```bash
# 验证回显
curl -X POST http://localhost:8101/wf/processInstance/bizData \
  -H 'Content-Type: application/json' \
  -d '{"id": <instance_id>}'
# 期望：返回 form 对象，含 EXPAND / JSON / 子表 反序列化结果
```

> **四语言合规测试**见 [上游规范 10 · 元数据驱动的动态写入/读取](https://jeeflow-doc.mldong.com/spec/10-persist-meta)。本仓 Python 实现已通过该矩阵全部用例（issues/23 关闭）。