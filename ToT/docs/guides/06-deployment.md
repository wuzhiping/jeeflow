# 用户指南 06 · 部署

> **来源**：https://jeeflow-doc.mldong.com/guides/06-deployment
> **定位**：给流程设计者（环境已部署 / 组织架构与用户已落地）使用的**设计视角部署边界参考**。
> **裁剪记录**：页面 header / §1 端口规划 / §2 后端部署 / §3 前端部署 / §4 CORS **整段裁剪** —— 背景预设「环境已部署」后无意义；§5 重写为本仓内存 vs PG 后端矩阵；§6 保留上游 2 条设计相关 + 重写本仓 5 条高频坑。
>
> **若读者属部署运维岗**：参见 `../docs/deployment.md`（本仓 15 节部署文档）+ `../ToT/sop/engine-deploy.md` + `../ToT/sop/env-config.md` + `../ToT/sop/env-pipeline.md`。

---

## 5. 生产接入（本仓双后端实现）

> **上游原文**：「demo 默认内存仓储，生产接入 ProcessRepository SPI」。本仓已实现**双后端**——按场景选其一即可。

### 5.1 后端选择矩阵

| 维度 | `main.py`（内存后端）| `main_pg.py`（PG 后端）| 何时选 |
|---|---|---|---|
| 监听端口 | `:8101` | `:8101`（同端口，绑不同进程）| — |
| 数据存储 | `MemoryRepository`（dict 内存）| `JdbcRepository`（PG 9 张表 = 5 核心 + 3 扩展 + 1 链路追踪）| 单机 demo / dev → main.py；生产 / 多节点 / HA → main_pg.py |
| 拦截器未注册 | **静默通过** `code=0`（历史行为；FIX-T34 后建议用 main_pg 排查）| **抛错** `code=99999999` | 拦截器 / handler 测试建议 main_pg.py |
| ID 格式 | 整数自增 1, 2, ...（UPSERT 累计）| 19 位雪花 ID（time-ordered bigint）| 均为引擎内部，**禁止硬编码** |
| reset 行为 | 清 instances / tasks / actors / cc | + TRUNCATE PG 表（含 design / design_his **保留**）| `POST /api/reset` 不在 57 个 `/wf/` 端点清单（旁路运维接口）|
| 引擎核心 | 共享 `vendor/jeeflow/engine.py` | 共享 `vendor/jeeflow/engine.py` | 行为差异仅在 `_resolve_interceptors` / `reset` 等少数点 |
| `v1.5.x` 修复 | 含 v1.5.1 / v1.5.2 / v1.5.3 | 含 v1.5.1-PG / v1.5.2-PG / v1.5.3-PG | 兼容矩阵见 `../docs/BUGS.md` |

> **设计者提醒**：流程 JSON 在两后端行为**完全一致**（除上表已列差异）。**不要**为「测试通过 main.py」就认为「PG 后端也通过」——拦截器/handler FQCN 相关必须用 main_pg.py 验证。

### 5.2 数据表清单（本仓 9 张）

> DDL 完整 SQL：`../docs/pg_schema.sql`（`psql -f docs/pg_schema.sql` 应用一次；幂等）。

| 表名 | 用途 | 设计者读写 |
|---|---|---|
| `wf_process_define` | 流程定义部署版本 | 读（pageByName） |
| `wf_process_design` | 流程设计层（save/deploy）| 间接读 |
| `wf_process_design_his` | 设计历史（每次内容变更）| 只读 |
| `wf_process_instance` | 流程实例（state/parentId/parentStatus）| 读 |
| `wf_process_task` | 任务行（taskState/operator）| 读 |
| `wf_process_task_actor` | 任务参与者（多对多）| 读 |
| `wf_process_cc_instance` | 抄送实例 | 读 |
| `wf_process_surrogate` | 全局委派（surrogate）| 读 |
| `wf_trace_span` | 链路追踪（FIX-T99 §6.4.1）| 只读（运维）|

> **设计者唯一写入入口**：`POST /wf/processDesign/save` + `/wf/processDesign/deploy`（仅 design / define 两层），**严禁**直接 SQL 写实例 / 任务表。
> 字段语义：`owner_id` = 流程发起人 userId（FIX-T9 §66）；`parent_status` = 主子状态联动（FIX-T72 §3.1.1 取值 `CHILD_DONE` / `CHILD_REJECT`）；`version` = 乐观锁（FIX-T87 §4.4.2）。

---

## 6. 故障排查（设计者视角）

> **上游原文 6 行中仅 2 条与设计相关**；其余 4 条（前端加载失败 / CORS / 改了定义不生效）属部署运维，本节不展开。

### 6.1 设计者必查表（保留上游 + 本仓补充）

| 症状 | 检查项 | 来源 |
|---|---|---|
| 决策分支走错 | 检查变量名是否与 `expr` 一致（如 `amount` vs `finalAmount`）| 上游 §6 |
| 驳回后没人收到待办 | 确认流程有 `apply` 节点且 `assignee="applicant"` | 上游 §6 |

### 6.2 本仓高频坑（设计者必查 7 项）

| 症状 | 排查 | 详见 |
|---|---|---|
| **deploy 失败：节点 id 含 `-` / 空格 / 中文** | 节点 id 严格 `^[A-Za-z0-9_]+$` | FIX-T34 §93 |
| **deploy 失败：节点 id 重复** | 同一流程内 id 唯一（deploy 自动校验）| FIX-T31 §58 |
| **deploy 警告 W012：task 节点多条无条件出边** | 用 decision 节点分隔，或 fork+join | FIX-T110 §111 |
| **deploy 警告 W013：decision 节点无默认边** | 加显式默认边 `properties.expr=""` | FIX-T112 §113 |
| **运行时 `code=99999999` + ValueError `handler 未注册`** | `assignmentHandler` / `decisionHandler` / `interceptor` FQCN 必须先在 `main_common.py:build_*_handlers` 注册 | FIX-T67/§67 + FIX-T38 §16 |
| **会签流转错：比例模式 + 一票否决互斥** | `countersignCompletionCondition` 二选一：表达式 / `"ONE_VOTE_VETO"` | FB-0008 §113 |
| **会签后 decision 截断一票否决** | submitType=20 仅 task → end 直连时生效；接 decision 即截断 | FB-0012 §116 |
| **决策 expr 评估失败但仍流转** | 兜底走第一条边可能创建孤儿 DOING task；加默认边 | BUG-2 / FIX-T112 §113 |
| **变量读不到：决策 expr 看不到 `tf_*`** | 启动传 `f_*`（持久化）或重启动时传 `f_<name>` | FB-0011 / FIX-DOC-4 §115 |
| **submitType=3/4 默认 ROLLBACK 覆写 assignee** | 不传 taskName 时引擎覆写 `assignee=前任务完成人 or operator`；原 assignee 失 re-process 能力，需显式传 taskName | FIX-T114 §118 |

> **设计者自检 SOP**：写完流程 JSON 跑 `../ToT/sop/flow_completeness.py <flow>.json` 看 0-100% 评分 + 下一步建议；跑 `../ToT/sop/tdd-flow.py <flow>.json` 生成 baseline + scenarios；跑 `../ToT/sop/ea-compliance.py` 看 **44/44** PASS（2026-09-23 snapshot；详见 `ToT/docs/README.md §3-5`）。

---

> **本节末尾（原页声明）**：「**用户指南完**」—— `01-06` 已归档完毕。
>
> 后续将进入 `07-assignment-handlers`（参与者解析内置清单）+ `08-persist`（业务数据入库）+ `09-persist-meta`（元数据驱动入库）+ `10-mldong-integration`（框架集成）+ `11-designer`（流程设计器）+ `12-designer-customize`（设计器二次开发）+ `13-jeeflow-ui`（前端接入）+ `14-uni-jeeflow-app`（移动审批端）等。