# 10 · mldong 快速开发框架集成 jeeflow 指南

> **来源**：https://jeeflow-doc.mldong.com/guides/10-mldong-integration
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**设计视角集成契约参考**。
>
> **本仓不输出 SDK/import info/UI**（PRD.md §3「不做什么」），**不引入其他语言后端**（私用项目定位）。上游面向「框架集成者」的 6 语言 controller / 依赖坐标 / SPI 注册清单与设计者职责**正交**，整段裁剪。
>
> **裁剪记录**：header / §1 / §2 / §3 / §4 / §6 / §7 / §8 整段裁剪（属集成者职责）；§5 仅保留 5.3（id 字符串契约）+ 补充本仓 `_stringify_ids` 实现注解；§5.1 / §5.2 / §5.4 整段裁剪（属框架层校验 / controller 层职责 / boot3 前端约定）。
>
> **若读者属框架集成岗**：参见 `../docs/integration.md`（本仓后端集成指南）+ 上游 §3 六框架代码示例。

---

## 5.3 id 字符串契约（设计者必知）

> **上游 §5 共性要点仅保留 5.3 id 字符串契约**——此为设计者调用 facade API 时**直接影响字段类型**的契约。

**引擎统一约束**：所有 facade API 出口的 id 类字段（`id` / `processDefineId` / `processInstanceId` / `processTaskId` / `processDesignId` / `parentId` / ...）一律为**字符串**。

**为什么**：

- 内存后端（`main.py`）：id 是整数自增（`1, 2, ...`），丢精度风险低
- PG 后端（`main_pg.py`）：id 是 **19 位雪花 ID**（time-ordered bigint，如 `1789614853725000`），超 JS `2^53` 安全整数（`9007199254740992`）
- 前端 JS Number 类型 `>2^53` 丢精度（`...4290` → `...4288`），雪花 ID 跨进程必须按字符串处理

> **本仓实现**（`vendor/jeeflow/facade.py:2444 _stringify_ids`，issues/38 E9）：
>
> ```python
> def _is_id_key(k: str) -> bool:
>     """id 类字段判定：key == 'id' 或 endswith 'Id'"""
>     return k == "id" or k.endswith("Id")
>
> def _stringify_ids(v):
>     """递归处理 dict/list/dataclass；id 类字段 int → str，None 保持 None"""
>     # 命中 _is_id_key + int 值 → 转 str
>     # 其他值直通（dict / list 递归；dataclass asdict 后递归）
>     # dataclass 分支（issues/76 FIX）收口「嵌套 dataclass 列表整表外泄 int id」
> ```
>
> 应用点（`facade.py:79` / `:98`）：所有 facade 出口统一过 `_stringify_ids`，**无需业务方自行处理**。
>
> 与上游其他语言对齐：
>
> | 语言 | 处理位置 |
> |---|---|
> | Java | 集成层 `ToStringSerializer`（全局序列化）|
> | Node | 引擎全链路 string，无需额外处理 |
> | Python | **引擎出口 `_stringify_ids`**（本仓）|
> | Go | 引擎出口 `stringifyIDs` + 集成层 `idToString` 兜底（结构体切片）|
> | Rust | facade 出口已 stringify；`serde_json` u64 不丢精度 |

**设计者实践**：

| 场景 | 实践 |
|---|---|
| curl 调用 API | 收到的 id 是字符串（如 `"1789614853725000"`），传递时也用字符串 |
| 设计流程 JSON | 节点 id 严格 `^[A-Za-z0-9_]+$`（FIX-T34 §93，与 id 数字串无关）|
| 启动参数 `processDefineId` | 从 `processDesign/deploy` 响应取 `data.processDefineId`（**字符串**），不要硬编码 |
| 待办 task id | 从 `processTask/todoList` 响应取 `data.rows[].id`（**字符串**）|
| 校验脚本 / 基线对比 | 统一按字符串处理；禁止 int → str 转换时丢失精度 |

> **本仓实测补充**（`docs/AGENTS.md §5.2.5`）：**禁止硬编码任何 id**——`processDesignId` / `processInstanceId` / `processTaskId` 都是**累积自增**（内存后端整数）或 **19 位雪花**（PG 后端）。每个测试实例必须从对应 API 响应**实时取**，跨测试不可复用。