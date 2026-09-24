# 第 8 章 · 让审批结果落到业务表

> **来源**：https://jeeflow-doc.mldong.com/manual/08-persist
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**操作手册第 8 章**——界面上要开哪三个开关；机制与字段级配置见 [用户指南 08 · 业务数据入库](../guides/08-persist.md)、[09 · 元数据驱动入库](../guides/09-persist-meta.md)、[规范 09 · 业务数据通用入库](../spec/09-persist.md)、[规范 10 · 元数据驱动的动态写入/读取](../spec/10-persist-meta.md)。
>
> **本仓实测**：基于 `vendor/jeeflow/persist.py:307 PersistPostInterceptor`（v1.8.0+ 完整实现）+ `facade.py:1076 processInstance_bizData`。
>
> **裁剪记录**：§1 三个开关 + §2 表从哪来 + §4 字段权限与落库**保留**+ 加本仓实测；§3 落库后在哪看**重写**为本仓 SQL；§5 卡住了**重写**为本仓 6 排错。

---

## §1. 三个开关

全在 **流程属性** 抽屉里（设计器画布空白处右键打开）：

| 字段 | 选什么 | 不填会怎样 |
|---|---|---|
| **后置拦截器** | **业务数据自动入库** | 办理与定稿**不会持久化业务数据**，流程照样跑完，但业务表里没有记录 |
| **关联业务表** | 目标表名，如 `biz_leave` | 不知道往哪张表写 |
| **持久化模式** | 归档 / 同步 | 决定是终态一次性落，还是每次办理都同步 |

演示数据里的 **请假申请** 三项分别是：

- **后置拦截器**：`业务数据自动入库`
- **关联业务表**：`biz_leave`
- **持久化模式**：`归档`

> **本仓实测**（`facade.py:347 processDefine_deploy` + `persist.py:307 PersistPostInterceptor`）：
>
> ```json
> {
>   "name": "leave",
>   "type": "approval",
>   "relTableName": "biz_leave",
>   "persistMode": "ARCHIVE",
>   "postInterceptors": "persistPost",
>   "nodes": [...]
> }
> ```
>
> - `relTableName` → 落库目标表（缺省回落流程 `name`）
> - `persistMode` → `ARCHIVE`（缺省）/ `SYNC`（非 SYNC 一律回落 ARCHIVE）
> - `postInterceptors` → 字符串 key "persistPost"，引擎按名从 `interceptor_registry` 解析
> - **未注册时** → `engine.py:1071` 抛 `ValueError(拦截器未注册: persistPost)`
>
> 详见 `../spec/09-persist.md` §4.0 + `../ToT/guides/08-persist.md` §3。

---

## §2. 表从哪来

关联业务表就是 [manual/03-forms.md](03-forms.md) §2 的**数据模型**。**在线开发 → 数据模型** 里建好表和字段，流程这边填表名即可。

引擎按字段名对应写入：表单字段 `days` → 列 `days`，同时补上 3 个**流程侧字段**：

| 流程侧字段 | 来源 | 建议 |
|---|---|---|
| `process_instance_id` | `instance.id`（雪花 / 自增）| 表里建该列，回显时关联实例 |
| `apply_user_id` | `instance.operator`（发起人 userId）| BIGINT 存 userId，开箱即用 |
| `apply_dept_id` | `instance.variables["u_deptId"]` | 申请人所在部门 ID |

> **本仓实测**（`persist.py:476 _fill_context`）：
>
> ```python
> def _fill_context(self, data, instance):
>     data.setdefault("process_instance_id", instance.id)
>     data.setdefault("apply_user_id", instance.operator)
>     data.setdefault("apply_dept_id", instance.variables.get(KEY_DEPT_ID))
> ```
>
> - `KEY_DEPT_ID = "u_deptId"`（`engine.py` 常量）
> - 3 个字段**总是写入**（即表里没建这 3 列也会被 `filter_columns` 列探测过滤掉）
> - **建议在数据模型里就建好**这 3 列（VARCHAR / BIGINT 适配 userId）—— 否则回显（`processInstance/bizData`）时关联不上
>
> 详见 `../spec/09-persist.md` §4.3。

---

## §3. 落库后在哪看（重写为本仓实测）

> **裁剪说明**：上游示例用 `docker exec boot4j-mysql` + 净装镜像档案页（前端项目范围）——本仓不输出 UI、不接 mldong 框架。本节重写为本仓 Python 引擎实测 SQL + facade `bizData` 端点。

### 3.1 通过 `processInstance/bizData` 端点（推荐）

```bash
# 流程详情回显（自动走 facade → facade.set_meta_reader → MetaTableReader）
curl -s -X POST http://localhost:8101/wf/processInstance/bizData \
  -H 'Content-Type: application/json' \
  -d '{"processInstanceId":"<实例ID>"}'
# → {
#     "code": 0,
#     "msg": "成功",
#     "data": {
#       "title": "年假申请",
#       "amount": 800,
#       "process_instance_id": "123",
#       "apply_user_id": "user1",
#       "apply_dept_id": "D01",
#       "create_time": "2026-08-04 10:00:00",
#       ...
#     }
#   }
```

> **本仓实测**（`facade.py:1076 processInstance_bizData` + `meta.py:293 MetaTableReader`）：
>
> - **未注入 `meta_reader`** → 抛 `ValueError("业务数据读取器未注册（facade.set_meta_reader(MetaTableReader(...))，需引入 jeeflow.meta）")`
> - 注入 `facade.set_meta_reader(MetaTableReader(JdbcTableReader(conn), JsonMetaProvider("persist-meta")))` 后按 `persist-meta/<table>.json` 元数据驱动读
> - 详见 `../spec/10-persist-meta.md` §6 + `../ToT/guides/09-persist-meta.md` §6

### 3.2 通过 PG / SQLite 直接查库

```bash
# PG 后端（main_pg.py）
psql "postgresql://postgres:postgres@127.0.0.1:5432/biz" \
  -c "SELECT id, days, reason, apply_user_id, process_instance_id
      FROM biz_leave ORDER BY id DESC LIMIT 5;"

# SQLite / 内存后端（main.py）
# 内存后端无持久化，重启后数据丢失——仅用于 demo / 单测
```

> **本仓实测 DDL**（`docs/pg_schema.sql`）：PG 方言 CREATE TABLE IF NOT EXISTS 幂等；8 张表（5 核心 + 3 扩展）+ 1 张本仓独有 `wf_trace_span`（FIX-T99 §6.4.1）。详见 `../spec/01-data-model.md`。

---

## §4. 字段级权限与落库的关系

[manual/03-forms.md](03-forms.md) §4 的字段权限里设为 **不可见** 的字段，在该节点提交的载荷里**不会出现**。如果某个字段只在最后一个节点才可见，落库时它的值取决于最后一次写入——排查"某字段为空"时先看它在哪个节点可编辑。

> **本仓实测 v1.8.2 引擎办理入口过滤**（FIX-DOC-4 §115）：
>
> - v1.8.0 / v1.8.1 只有拦截器写入侧过滤（被拒值先入 `complete_task` 无条件 `putAll`）—— **下游无权限节点完成时全量提取写入业务表，上游只读可被绕过**
> - **v1.8.2 起** 引擎办理入口过滤（`filterFieldByPerm`）：值非 `EDIT(2)` 的 `f_*` 字段在入变量前即被剔除
> - 被拒值**无法经流程变量落到下游节点写入**
> - 拦截器写入侧过滤保留为**双保险**
>
> ```python
> # persist.py:453 _is_editable
> def _is_editable(self, field_perm, field_name):
>     if not field_perm:
>         return True
>     prefix = self.field_prefix or "f_"
>     perm = field_perm.get(f"PERMISSION_{prefix}{field_name}")  # 前端格式优先
>     if perm is None:
>         perm = field_perm.get(f"PERMISSION_{field_name}")       # 兼容格式
>     if perm is None:
>         return True                                            # 缺省 = 可编辑
>     return int(perm) == PERM_EDIT                              # 2 = 可编辑
> ```
>
> 详见 `../spec/09-persist.md` §4.2 + `../docs/known-issues.md §115`。

---

## §5. 卡住了看这里（重写为本仓实测）

| 现象 | 原因 | 处理 |
|---|---|---|
| 流程已完成，业务表没数据 | 没配后置拦截器 | §1 选 **业务数据自动入库** 后重新部署，再发起一条新的（架构生效仅对新发起实例） |
| 数据落了，但前端档案页看不到 | 档案页面未配置，或查询条件把新数据过滤了 | §3.1 用 `processInstance/bizData` 直查；§3.2 用 SQL 直查 |
| **本仓实测补充**：每次办理都写一条重复记录 | 持久化模式 `ARCHIVE` 时拦截器挂在任务节点上（非 end）| **只挂在 end 节点**——`ARCHIVE` 模式仅 end 节点落库（`persist.py:357-363`）；中途挂任务节点会触发落库但因 `_mark_chain` 节点级防重可能仍写 |
| **本仓实测补充**：ARCHIVE 模式下驳回触发落库 | `submitType=2 REJECT` 走 `execute_and_jump_to_end`（非 end 节点）—— 但 `ARCHIVE` 模式 `_handle_archive:362` 要求 `submitType == AGREE` | 驳回路径**不**落库；这是 ARCHIVE 默认行为 |
| 申请人、申请部门为空 | 表里没有 `apply_user_id` / `apply_dept_id` 列 | §2 补列 + `filter_columns` 自动适配（VARCHAR / BIGINT 适配 userId）|
| 改了表单字段但落库报错 | 数据模型列与表单字段不一致 | 数据模型 → 模型字段 对齐后重新部署 |
| **本仓实测补充**：落库报 `biz_xxx table not found` | `relTableName` 配置错误或表未创建 | 检查 `relTableName`；用 `docs/pg_schema.sql` + 数据模型 CREATE TABLE 同步建表 |
| **本仓实测补充**：落库报 `sys_ prefix not allowed` 或 `contains illegal characters` | `relTableName` 表名含 `sys_` 前缀或非字母数字下划线 | 改表名（`persist.py:283 _check_table_name` 校验）|

---

## 跨文档交叉引用

- 三大开关详解（`relTableName` / `persistMode` / `postInterceptors`）：`../spec/09-persist.md` §4.0 + `../ToT/guides/08-persist.md` §3
- ARCHIVE / SYNC 双模式完整契约：`../spec/09-persist.md` §4.1 / §4.2 + `../ToT/guides/08-persist.md` §3
- 字段权限双兼容（PERMISSION_f_* 优先）+ v1.8.2 引擎入口过滤：`../spec/09-persist.md` §4.2 + `../docs/known-issues.md §115`
- 元数据驱动落库（地址对象 / JSON / 子表）：`../spec/10-persist-meta.md` + `../ToT/guides/09-persist-meta.md`
- `processInstance/bizData` 端点 + 复杂表单回显：`../spec/06-facade.md` §4.2 + `../spec/10-persist-meta.md` §6
- PG 后端 DDL（8 张表 + 1 张本仓独有 `wf_trace_span`）：`../spec/01-data-model.md`
- 9 submitType 路由 + 失败 msg 字面量：`../spec/06-facade.md` §2.8
- 数据模型建表 + 字段定义：`manual/03-forms.md` §2 + `../ToT/guides/08-persist.md` §3
- 27 合规测试场景（落库部分）：`../spec/08-compliance.md` §6（18 用例）