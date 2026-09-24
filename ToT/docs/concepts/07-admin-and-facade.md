# 设计原理 07 · 管理扩展与统一门面——v1.1.0 的两个关键决策

> **来源**：https://jeeflow-doc.mldong.com/concepts/07-admin-and-facade
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**v1.1.0 两个关键决策原理参考**——理解「管理扩展走扩展仓储 SPI 而非核心仓储」+「统一门面 `flow(action, args)`」的设计动机，是理解委托 / 抄送 / 设计器 CRUD / **57 个 `/wf/` 端点（47 唯一 action）**的基础。
>
> **本仓实测**：`vendor/jeeflow/spi.py:190 ProcessExtRepository(ABC)` + `vendor/jeeflow/facade.py:63 JeeflowFacade.flow(action, args)` + `engine.py` 内置 `SurrogateInterceptor`（v1.9.0+ 默认开启，issues/116）。
>
> **裁剪记录**：§1-§4 全部保留 + 加本仓实测。

---

## §1. 背景：集成反馈暴露的两个缺口

v1.0.0 发布后，首个真实集成方（boot4）反馈了两类问题：

1. **设计器数据没有统一读写通道**——流程设计稿、设计历史、委托代理这三类"周边管理数据"各有各的存法，集成方各自实现 CRUD，与引擎的"统一 SPI"风格割裂
2. **接口风格与框架生态不匹配**——mldong 框架的接口风格是"POST + JSON body"，每个端点一个 controller 方法。集成方要用引擎能力就得为每个能力写一个转发，controller 层越来越厚

---

## §2. 决策一：管理扩展走"扩展仓储 SPI"，而不是进核心仓储

### 备选方案

- **A. 并入 `IProcessRepository`**：三类表直接进核心仓储接口 → **拒绝**：核心仓储是"引擎运行时依赖"，设计稿 / 委托引擎核心根本不读——强绑会让所有集成方（包括只用引擎不做管理端的人）被迫实现 15 个多余方法
- **B. 独立扩展仓储 `IProcessExtRepository`（采纳）**：与核心仓储并列，引擎核心不引用，门面按需使用 → **收益**：核心保持最小；管理能力按"可选 SPI"演进，与 `IUserProvider` 等可选 SPI 同构；集成方不需要管理端功能时零成本

> **本仓实测**（`vendor/jeeflow/spi.py:190 ProcessExtRepository(ABC)`）：
>
> ```python
> class ProcessExtRepository(ABC):
>     """扩展仓储 SPI（v1.1.0，可选）——流程设计 / 设计历史 / 委托代理
>
>     引擎核心不依赖本接口；门面（Facade）与委托参考实现使用。
>     """
>     # 流程设计（wf_process_design）
>     @abstractmethod
>     async def find_design_by_id(self, id: int) -> Optional[ProcessDesign]: ...
>     @abstractmethod
>     async def save_design(self, d: ProcessDesign) -> None: ...
>     @abstractmethod
>     async def update_design(self, d: ProcessDesign) -> None: ...
>     @abstractmethod
>     async def remove_design(self, id: int) -> None: ...
>     @abstractmethod
>     async def page_designs(self, page_num, page_size, conditions) -> tuple[list[DesignRow], int]: ...
>
>     # 设计历史（wf_process_design_his）
>     @abstractmethod
>     async def save_design_his(self, his: ProcessDesignHis) -> None: ...
>     @abstractmethod
>     async def list_design_his(self, design_id: int) -> list[ProcessDesignHis]: ...
>
>     # 委托代理（wf_process_surrogate）
>     @abstractmethod
>     async def find_surrogate_by_id(self, id: int) -> Optional[ProcessSurrogate]: ...
>     @abstractmethod
>     async def save_surrogate(self, s: ProcessSurrogate) -> None: ...
>     @abstractmethod
>     async def update_surrogate(self, s: ProcessSurrogate) -> None: ...
>     @abstractmethod
>     async def remove_surrogate(self, id: int) -> None: ...
>     @abstractmethod
>     async def page_surrogates(self, page_num, page_size, conditions) -> tuple[list[SurrogateRow], int]: ...
>     @abstractmethod
>     async def get_surrogate(self, operator: str, process_name: str, time) -> Optional[ProcessSurrogate]: ...
> ```
>
> 12 方法完整对应上游契约；本仓实测本接口为**可选**（未配置时 `processDesign/*` / `processSurrogate/*` 报错）。
>
> 详见 `../spec/05-spi.md` §扩展仓储。

### 委托为什么选"拦截器 + 参与者注入"而不是"引擎原生支持"？

委托（surrogate）本质是**业务策略**而非引擎语义：不同集成方的委托规则（时间窗、多级委托、委托链）差异很大。如果引擎原生实现，会变成"引擎猜测业务"。

参考实现（`SurrogateInterceptor`）展示的路径：**任务创建后拦截 → `get_surrogate` 命中 → `add_task_actor` 把代理人加入参与者**。授权人与代理人"任一可办"，完全复用引擎已有的参与者机制（`is_allowed`），引擎零改动。集成方有自己的委托规则时，替换拦截器即可。

> **本仓实测**（`engine.py` 内置 `SurrogateInterceptor`，**v1.9.0+ 默认开启**，issues/116）：
>
> - 触发时机：任务参与者解析完成后、参与者落库前，对**每个** actor 查一次生效委托
> - 动作：命中 → 把 `surrogate` **追加**为该任务参与人（**不**摘原人，**不**级联 A→B→C）
> - 失败兜底：未配置 `IProcessExtRepository` 时静默跳过，**不**打断建单流程
> - 跨栈一致性：4 条件（空 processName 兜底 / 时间窗 / 自委托过滤 / `enabled` 只认 1）内存仓与 SQL 仓必须同答案
>
> 详见 `../spec/06-facade.md` §4.5 + `../ToT/guides/05-scenarios.md` 场景五 + `../ToT/guides/04-extensions.md` §3。

---

## §3. 决策二：统一门面 `JeeflowFacade.flow(action, map)`

### 要解决的问题

boot2/boot3 有 40+ 个流程端点。集成方如果每个端点写一个转发，controller 层与框架生态重复劳动；而且端点行为分散在多个 service 里，语义难对齐。

### 设计

```
flow(action, map) → { code, msg, data }
```

- **action = boot2/boot3 端点短名**（`processTask/execute` / `processDesign/save`…），对齐天然：集成方前端调用的路径不变，只改后端转发目标
- **args 显式携带 operator**——门面不感知登录态，集成方决定从哪注入当前用户
- **返回统一结构**对齐 mldong `CommonResult`，controller 一行转发

> **本仓实测**（`vendor/jeeflow/facade.py:63`）：
>
> ```python
> async def flow(self, action: str, args: Optional[dict] = None) -> dict:
>     """统一入口：57 个 `/wf/` 端点全覆盖
>
>     API 兼容性：新增 endpoint（走 /wf/{action:path} 路由）
>     """
>     # 路由分发：action → 私有方法
>     # 返回统一结构：{code, msg, data} 或 {code, msg, data, ...}
> ```
>
> - **57 个 `/wf/` 端点（47 唯一 action）**完整覆盖上游 demo + 本仓新增（详见 `../spec/06-facade.md` §3 清单）
> - **HTTP 入口**：`main.py` / `main_pg.py` 注册 `POST /wf/{action:path}` 路由
> - **统一响应**：`{code, msg, data}` 三字段；`code=0` 成功 / `code=99999999` 业务失败（详细见 `../spec/06-facade.md` §2.1）

### 为什么"路由在门面内"而不是"每个 action 一个接口方法"？

- 40+ 个 action 的签名如果逐个声明，接口膨胀且与 boot3 端点绑定死
- 门面内 switch 分发（各语言 dispatch），新增 action 只加一个 case + 一个私有方法
- 集成方视角：一个 bean、一个方法，转发 controller 从"40 个方法"变成"1 个方法"

> **本仓实测入口**（`main_pg.py:84-105`）：
>
> ```python
> app.include_router(wf_router)   # POST /wf/{action:path}
> facade = JeeflowFacade(engine)
> # 转发 controller 只需：
> @router.post("/wf/{action:path}")
> async def wf_flow(action: str, body: dict = Body(default=None)):
>     return await facade.flow(action, body)
> ```
>
> 集成方转发 controller 实际只需**1 个方法**——这是门面最核心的收益。

### 边界：门面不是业务层

门面只做"能力路由"，不包含业务规则（如"驳回后订单状态怎么变"）。业务规则仍在集成方 service 层，与引擎通过"操作 → 引擎方法 → 仓储"协作。

> **设计者实操**：业务系统集成本仓时，**不要**把业务规则写进 facade 拦截器或事件监听器——那是引擎扩展点。业务规则走集成方 service 层，调引擎能力时用 `await facade.flow("processTask/execute", {...})` 即可。

---

## §4. 演进的结果

- 集成方 controller：**40 个端点 → 1 个 `/wf/**` 转发**
- 集成方 service：手写的视图端点（高亮、审批记录、候选人…）逐步被门面内置 action 取代（v1.2.0 补齐 13 个视图端点后，`WfViewController` 手写层可删除）
- 委托生效 = 挂一个拦截器，不碰引擎

> **演进记录**：
>
> | 版本 | 关键里程碑 | 本仓实测对应 |
> |---|---|---|
> | **v1.0.0** | 基础架构 + 27 引擎核心场景 | `flows/01-17`（**19 个 sample** + BDD 1131 + TDD 19；含 2 个同号 08/11）|
> | **v1.0.1** | 集成反馈：`save_define` / `update_instance` 级联契约 | `spi.py:25 save_define` + `:37 update_instance` |
> | **v1.1.0** | 管理扩展（`ProcessExtRepository`）+ 27 个 action | `spi.py:190 ProcessExtRepository` + `facade.py:83 个 _* 路由方法（57 公开 /wf/ 端点）` |
> | **v1.2.0** | 13 个视图端点补齐（highLight / approvalRecord / candidatePage / latest / 抄送）| `facade.py:1276 highLight` / `:1405 approvalRecord` / `:1535 candidatePage` 等 |
> | **v1.3.0** | `ccList` 分页（核心分页 SPI）+ `addTaskActor` 追加语义修复 | `spi.py:70 page_cc_instances` + `:53 add_task_actor` |
> | **v1.4.0** | 元数据能力（枚举字典 + HandlerRegistry 注册式清单）| `metadata.py:55 enum_dict_keys` + `:102 HandlerRegistry` |
> | **v1.6.0** | OrgUserProvider（8 handler → 1 SPI 简化）| `spi.py:161 OrgUserProvider` |
> | **v1.8.0** | 业务数据持久化（ARCHIVE/SYNC 双模式）+ 元数据驱动落库 | `persist.py:307 PersistPostInterceptor` + `meta.py:141 MetaTableWriter` |
> | **v1.9.0** | SurrogateInterceptor 内置默认开启 + 27 BUG 全部修复 | `engine.py:SurrogateInterceptor` + `docs/BUGS.md` 27/27 PASS |
>
> 详见 `../spec/06-facade.md` + `../roadmap.md` + `docs/BUGS.md`。

---

## 跨文档交叉引用

- 扩展仓储 12 方法完整契约：`../spec/05-spi.md` §扩展仓储
- Facade 57 个 `/wf/` 端点 + 83 个 _* 路由方法完整契约 + 响应结构 + 分页 + id 字符串化：`../spec/06-facade.md`
- SurrogateInterceptor 运行期 6 条语义 + 委托查询判据 4 条件：`../spec/06-facade.md` §4.5 + `../concepts/04-extensions.md`
- 27 合规测试场景 + 路线图：`../spec/08-compliance.md` + `../roadmap.md`
- mldong 集成视角（私用项目不引入）：`../ToT/guides/10-mldong-integration.md`