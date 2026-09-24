# 设计原理 08 · 引擎元数据——值漂移问题与注册式决策

> **来源**：https://jeeflow-doc.mldong.com/concepts/08-metadata
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**引擎元数据设计原理参考**——理解「枚举字典直接由引擎枚举生成」+「SPI 清单走注册式」两个 v1.4.0 关键决策的动机，是把握设计器下拉字典 / HandlerRegistry 行为的基础。
>
> **本仓实测**：`vendor/jeeflow/metadata.py:55 enum_dict_keys()` + `:60 enum_dict(key)` + `:102 HandlerRegistry` + `:77 BUILTIN_ASSIGNMENT_METAS`（7 个内置 assignment handler 元数据）。
>
> **裁剪记录**：§1-§4 全部保留 + 加本仓实测 + 字典差异警示。

---

## §1. 要解决的问题：只有引擎自己知道的数据

前端流程设计器（vben5-wf）的配置项依赖两类数据，它们**只存在于引擎内部**：

1. **SPI 实现清单**：可用的 AssignmentHandler / CandidateHandler / FlowInterceptor——设计器的下拉框要列出"有哪些处理器可选"，value 是运行时引擎用来加载的类名 / handlerName
2. **内置状态枚举**：流程定义 / 实例 / 任务状态、提交类型——设计器和列表页要渲染 code → label

在 boot3 时代，这些由 mldong 框架的"枚举注解 + classpath 扫描器 + 数据库字典"提供。jeeflow 引擎核心**零框架依赖**（不能打 mldong 注解），于是每个集成方都要自己重复实现：自己写扫描器、自己重新定义枚举。多语言联邦下，这个问题**逐语言放大**（四份重复实现），且每次引擎加一个状态 / 处理器，集成方不知道 → **值漂移**（枚举值、字典 label 与引擎不一致）。

> **本仓实测**：本仓 `vendor/jeeflow/metadata.py` 直接由引擎枚举生成字典，杜绝集成方重新定义。

---

## §2. 决策一：枚举字典直接由引擎枚举生成

### 为什么不用"集成方自行定义枚举"

集成方定义枚举 = 拷贝一份值表。引擎加状态（如 v1.4.0 给 `InstanceState` 补 `WITHDRAW` / `INTERRUPT` / `PENDING` / `ABANDON`）时，集成方不更新 → 字典缺项、前端渲染错。**事实已经发生**：Go / Python / Node 的 `InstanceState` 在 v1.4.0 前只有 3 个值，且命名与 Java 不同（`DONE` vs `FINISHED`）。

> **本仓实测警示**（`metadata.py:34 _DICTS["wf_process_submit_type"]`）：
>
> | 值 | label |
> |---|---|
> | 0 | 发起申请 |
> | 1 | 同意申请 |
> | 2 | 拒绝申请 |
> | 3 | 退回上一步 |
> | 4 | 跳转 |
> | 5 | 重新提交 |
> | 6 | 退回发起人 |
> | 20 | **拒绝申请** ← **与 `2` 重复** |
>
> **缺失 `7 转办（TRANSFER）** —— `model.py:70 SubmitType` 枚举含 `7`，但字典无该项。前端"转办"提交类型显示需绕开字典或自定义补充。**设计者实操**：调 `enum_dict("wf_process_submit_type")` 取字典做表单下拉时，**按 `value` 区分**，避免依赖 label 判别。
>
> 详见 `../spec/07-metadata.md` §枚举字典。

### 设计

```python
# vendor/jeeflow/metadata.py:60
def enum_dict(key: str) -> list[DictItem]:
    """按 key 取字典（[{value, label}]），未知 key 返回空列表"""
    return list(_DICTS.get(key, []))
```

- **key 约定 = boot3 字典 key**（`wf_` + 枚举名转下划线）：存量前端零改动，集成方的 CustomDictService 只做"key 透传"
- **枚举新增/变更自动反映到字典**——**值漂移在源头消除**
- 枚举本身已有 `code` / `message`（v1.0 就设计好的），注册表只是"把它们摆出来"，零额外声明

### 多语言形态

- **Java**：枚举统一实现 `IDictEnum`（`getCode` / `getMessage`），注册表泛型生成
- **Go / Python / Node**：没有 Java 式枚举，v1.4.0 **补齐完整枚举 + 显式字典表**（`value` / `label` 与 Java 逐项对齐，测试锁定）

> **本仓 Python 形态**（`metadata.py:25 _DICTS` 7 字典完整）：
>
> ```python
> _DICTS: dict[str, list[DictItem]] = {
>     "wf_process_define_state": [
>         DictItem("0", "禁用"), DictItem("1", "启用"),
>     ],
>     "wf_process_instance_state": [
>         DictItem("10", "进行中"), DictItem("20", "已完成"), DictItem("30", "已撤回"),
>         DictItem("40", "强行终止"), DictItem("45", "已拒绝"), DictItem("50", "挂起"),
>         DictItem("99", "已废弃"),
>     ],
>     "wf_process_submit_type": [...],   # 8 项（含 20 重复）
>     "wf_process_task_state": [...],     # 6 项
>     "wf_process_task_type": [...],      # 3 项
>     "wf_process_task_perform_type": [...],
>     "wf_countersign_type": [...],
> }
> ```

---

## §3. 决策二：SPI 清单走"注册式"，不用接口默认方法 / 注解

issue 提议过两种元数据形态：

- **方式 A：接口默认方法**（`default String getMessage()`）——Java 可行，但 Go 接口没有默认方法、Python ABC 默认方法语义不同、Node interface 没有——**多语言无法对齐**
- **方式 B：注解**（`@HandlerMeta`）——Java 可行，但 Go / Python / Node **没有注解概念**

### 为什么选"注册式"（HandlerRegistry）

关键洞察：**引擎是懒加载的，不是注册中心**——Java 按类名 `Class.forName`，Go / Python / Node 靠扩展点函数按 handlerName 分发。引擎自己也不知道"有哪些可用实现"，这些实现属于**集成方的选择**（每个集成方可用处理器集合不同）。

注册式 = 集成方在启动时把"自己可用的实现 + 元数据"登记进 HandlerRegistry：

```
集成方扫描器（Spring Bean 扫描 / 手动装配）
   → register(type, className/handlerName, displayName, order, group)
   → listHandlers(type) 生成设计器下拉字典
```

- **字典与运行时天然一致**：字典的 value 就是节点配置里写的同一个字符串
- **零侵入**：现有处理器接口和实现零改动，不注册不影响引擎加载行为
- **多语言对齐**：每个语言一个 Map 注册表，Node 直接扩展既有 `HandlerRegistry`（引擎本来就用它做名称解析），Java / Go / Python 新增独立类 / 模块

> **本仓实测**（`vendor/jeeflow/metadata.py:102 HandlerRegistry` + `:68 HandlerMeta`）：
>
> ```python
> @dataclass
> class HandlerMeta:
>     type: str                                      # 处理器类型名
>     className: str                                 # 节点配置的 handlerName（与字典 value 一致）
>     displayName: str = ""                          # 显示名（字典 label）
>     order: int = 0                                 # 排序（小在前）
>     group: Optional[str] = None                    # 拦截器 pre/post 分组
>
> class HandlerRegistry:
>     def __init__(self):
>         self._handlers: dict[str, list[HandlerMeta]] = {}
>         self.register_all(BUILTIN_ASSIGNMENT_METAS)   # 构造即注册 7 项
>
>     def register(self, meta: HandlerMeta) -> None: ...
>     def register_all(self, metas: list[HandlerMeta]) -> None: ...
>     def list_handlers(self, type_name: str) -> list[HandlerMeta]:
>         """按处理器类型列出（按 order 升序）"""
>         return sorted(self._handlers.get(type_name, []), key=lambda m: m.order)
>     def list_handlers_group(self, type_name: str, group: str) -> list[HandlerMeta]: ...
>     def list_handler_types(self) -> list[str]: ...
> ```
>
> 6 API + 5 字段完整对齐上游契约；`BUILTIN_ASSIGNMENT_METAS` 7 项实测 + 本仓实测与 `builtin.py` 注册 key 部分不一致警示详见 `../spec/07-metadata.md` §SPI 实现清单。

---

## §4. 为什么这能终结"扫描器重复"

boot4 此前有 4 个扫描器（assignment / candidate / pre / post）各自扫 classpath 生成字典。重构后：**扫描结果 → 注册 → 字典来自注册表**，4 个扫描器塌缩为 1 个 `CustomDictService` 薄映射；多语言联邦下，各语言集成方共享同一套注册 API 心智模型，不再各自发明。

> **本仓实测路径**（`main_common.py:build_*_handlers` 系列）：
>
> 1. `build_assignment_handlers(user_prov, org_prov)` → `HandlerRegistry()` + `register_builtin_assignments(registry, user_prov, org_prov)`
> 2. `build_decision_handlers()` → 决策 handler 注册
> 3. `build_persist_components(repo)` → 持久化 writer + `PersistPostInterceptor`
> 4. `register_persist_meta(registry)` → 元数据注册助手（`persist.py:486`）自动注册 `PersistPostInterceptor` 到 registry
> 5. `apply_extensions(engine, registry=registry, ...)` → 注入引擎
>
> 5 步骤对应"扫描 → 注册 → 字典"流程；集成方 controller 只需**1 个 `/wf/{action}` 转发方法**，facade 自动 dispatch。
>
> 详见 `../concepts/07-admin-and-facade.md` + `../spec/07-metadata.md` + `../spec/06-facade.md`。

---

## 跨文档交叉引用

- 元数据能力规范（7 字典 + HandlerRegistry 6 API + 5 字段）：`../spec/07-metadata.md`
- 字典差异警示（缺 `7 转办` / `20 与 2 label 重复`）：`../spec/07-metadata.md` §枚举字典
- HandlerRegistry 与 builtin.py 注册 key 不一致警示：`../spec/07-metadata.md` §SPI 实现清单
- 集成方扫描 → 注册 → 字典流程 + 集成方 controller "40 → 1" 收益：`../concepts/07-admin-and-facade.md`
- Facade 60+ action 完整契约：`../spec/06-facade.md`
- v1.4.0 元数据能力合规测试场景 21-22：`../spec/08-compliance.md` §5