# jeeFlow 项目发展建议书 (Roadmap)

> **生成时间**: 2026-09-19 (更新 2026-09-20 §2+§3+§4 全部完成; §5 已删除)
> **数据基线**: **1131 个 BDD 场景** + 19 个 TDD flow + **93 个 FIX** + 31 条 verify 规则
> **文档依据**: `docs/*.md` (10 份) + `bdd/README.md` + `vendor/README.md`

---

## ⚠️ 核心约束声明 (2026-09-20 更新)

> **-1. 同步约束 (2026-09-20 新增)**: 每次 `roadmap.md` 变更 (新增/删除/调整子任务, 优先级变化, SLA 引用更新等), **必须**同步更新 [`TODO.md`](./TODO.md)。详见 `TODO.md §0`。

> **0. 项目定位 (2026-09-20)**:
> - **本项目只是私用定位**, 为 AI Agent 和人机协同提供持续改进的**流程协同机制**, 方便审计、复盘、改进业务。
> - 不开源, 不发布 SDK, 不建第三方流程市场 (第四阶段: 生态化 已删除)。
> - 所有改进以"内循环 + 可追溯"为目标, 持续为业务方提供高质量工作流引擎。

> **1. UI/apps/demo 项目 = 不在本路线图范围内**:
> - 所有 UI (Vue3 / Element Plus / 流程设计器 / 拖拽 / BPMN 互通) 计划**已删除**。
> - UI/apps/demo 由业务方独立维护, 本项目**不输出任何前端代码**。

> **2. main.py / main_pg.py API = 本项目唯一对外契约**:
> - 所有阶段 (稳定化 / 能力补齐 / 生产化 / HA) 的改动, **必须保持 33 个 `/wf/{action}` endpoint 100% 向后兼容**。
> - 既有字段语义不变, 既有状态码不变, 既有请求/响应结构不变。
> - 新增功能 (如 §69 delegate / §70 操作端点 / §3.2.1 delegateHistory 等) 归入现有 `/wf/{action:path}` 路由, 不引入新前缀。
> - 兼容性验证基线 = `bdd/README.md` 1131 BDD + 19 TDD 双端 PASS。

> **3. 改动后必跑回归**:
> - 任何 vendor/jeeflow / main.py / main_pg.py / main_common.py 改动后必须 `bash bdd/bdd-1001-1060-p0-regression.sh && bash bdd/bdd-1065-1100-p1-regression.sh && bash bdd/bdd-1101-1110-phase2.sh && .venv/bin/python /tmp/test_pg_direct.py && .venv/bin/python /tmp/test_phase2_pg.py` 全 PASS 才能提交。
> - 任何 BUG 修复/新增功能必须有对应的 BDD 场景 + TDD flow + verify 规则 (新增规则时)。

---

---

## 0. 项目现状速览

| 维度 | 当前 | 来源 |
|---|---|---|
| 引擎代码 | Python 独立引擎 (v2.0.0+)，不再考虑 Java 兼容 | `docs/AGENTS.md §1` 决策 |
| 后端 | 双端: `main.py` (内存 8101) + `main_pg.py` (PG 8102/10.17.1.26:6432) | `docs/flow.md §2` |
| 对外契约 | **38 个 `/wf/{action}` endpoint** (33 既有 + 5 Phase 2 新增) + `/healthz` + `/api/reset` | `docs/api.md` |
| 流程模型 | 19 个示例 flow 全 PASS, 含 fork/join/countersign/custom/decision/suspend/callActivity | `flows/README.md` |
| 引擎核心 | engine.py 754 行 + facade.py 1815 行 + verify.py 31 规则 (15E+11W+5P) | `vendor/README.md §1` |
| 测试覆盖 | **1131 BDD + 19 TDD 双端 100% PASS** (P0=17 + P1=26 + Phase2=9 + Phase4=11 + PG in-process=30) | `bdd/README.md §1` |
| 已修 BUG | **93 个** (T1~T93, 含 §36 interceptor 启动期校验) | `bdd/README.md §2` |
| 已知限制 | **0 个** (§2 + §3 + §4 全部完成) | `docs/known-issues.md` |
| 监控端点 | 9 个 (`/healthz` + `/metrics` + `/api/admin/{health,stats/overview,stats/trend,stats/group,trace,trace/spans/{id},expire/scan}`) | `docs/integration.md` |
| Prometheus 指标 | 4 个 (`wf_instance_state_total` / `wf_active_instances` / `wf_task_duration_seconds` / `wf_task_completed_total`) | `docs/integration.md §3` |
| 文档 | 11 份 (api/architecture/integration/deployment/flow-tutorial/openapi + AGENTS/BUGS/known-issues/actions/state) | `docs/` |
| OpenAPI | 70 paths / 57 actions (自动生成) | `docs/openapi.json` |
| HA | PG pool env + 实例乐观锁 (version) + 多节点部署指南 (15 节) | `docs/deployment.md` |
| SLA 报告 | `sla/check.sh` 20 项 / 100% PASS + `sla/README.md` + `sla/HISTORY.md` | `sla/` |

---

## 1. 总体战略

### 1.0 项目定位 (2026-09-20 更新)

**本项目只是私用定位, 为 AI Agent 和人机协同提供持续改进的流程协同机制, 方便审计、复盘、改进业务。**

核心定位要素:
- **不输出 SDK / 插件市场 / 第三方流程市场** (原第四阶段: 生态化 已删除)
- **不输出任何 UI / 前端 / 可视化代码** (UI/apps/demo 由业务方独立维护)
- **本项目的对外契约 = `main.py` (8101) + `main_pg.py` (8102) 暴露的全部 HTTP API**
- 所有改进围绕"持续为业务方提供高质量工作流引擎" + "可追溯的审计与复盘"两条主线

任何阶段 (稳定化 / 能力补齐 / 生产化 / HA) 的所有改动, **必须保证 `main.py` + `main_pg.py` 的 API endpoint 100% 向后兼容**:
  - 既有 38 个 action 路径不变 (`/wf/processDesign/save` 等)
  - 既有请求/响应字段不变 (允许加字段, 不允许改字段名/语义)
  - 既有状态码语义不变 (新增错误码可, 已有错误码行为可不变)
  - 既有 BDD/TDD 用例 100% 继续 PASS 作为基线
- 若某项业务扩展**必须新增** endpoint (如 §69 delegate / §3.2.1 delegateHistory), 也归入现有 `/wf/{action:path}` 路由, 不引入新前缀。
- 验证基线: `bdd/README.md` 索引的 1119 BDD + 19 TDD + 31 verify 规则 + 双 DB 回归测试, 改动后必须全部通过。

### 1.1 三阶段路线（全部完成 2026-09-20 + §6 规划）

```
2026-Q3 (4 周)              2026-Q4 (8 周)              2027-Q1~Q2 (16 周)        2026-Q4 (13 周)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━
[稳定化]                     [能力补齐]                  [生产化 + HA]              [§6 纵深优化]
引擎核心收敛                   限制消除 + 父子流程          监控 / 运维 / HA / 文档      关闭 §34/§36 规避
████████████████ 完成 ✅    ████████████████ 完成 ✅    ████████████████ 完成 ✅    ░░░░░░ 推荐启动 ░░░░░
78 FIX / 1119 BDD          8 FIX (§3.1-§3.3)          14 FIX (§4.1-§4.4)         11 子任务 (§8.5)
verify 31 规则               TDD 17-suspend + 18-call   docs/openapi.json 70 paths   导出 + 持久化
                                                       sla/check.sh 20/20 PASS      性能基线
                                                       ↑↑↑
                                          ❌ 没有任何 UI/前端/可视化工作 (§5 已删除)
                                          ❌ 没有任何 SDK/插件/第三方市场
                                          (私用定位, 只服务本项目业务方)
```

### 1.2 战略优先级

| 优先级 | 类别 | 说明 |
|---|---|---|
| **P0** | 引擎能力与一致性 | ✅ 全部完成: 限制消除 + 双端对齐 + 父子联动 + 委派 + 转办 + 表单 (11 P0 + 2 P1 + 8 Phase 2 + 12 Phase 3 = 93 FIX) |
| **P1** | 性能 / 文档 / HA | ✅ 全部完成: 监控 9 端点 + OpenAPI 70 paths + 文档 11 份 + PG 池 + 乐观锁 + 部署指南 |
| **§6** | 纵深优化 | 🆕 详见 §8.5: 关闭 §34/§36 规避 + 导出 + 持久化 + 性能基线 (**11 子任务**, ~10 周; K8s/灰度已取消, auth 暂停) |
| ~~**P2**~~ | ~~SDK / 插件市场 / 第三方流程市场~~ | **2026-09-20 删除 (私用定位)** |

---

## 2. 第一阶段: 稳定化 (2026-09 ~ 2026-10, 4 周)

> **目标**: 当前 11 个已知限制维持现状但补齐文档 + verify 覆盖; 引擎核心不再扩展新特性, 全力修剩余 6 项 P0。

### 2.1 P0 任务清单

| 任务 | 工作量 | 验证标准 | 涉及文件 |
|---|---|---|---|
| **§69 任务委派 delegate** | 3 天 | BDD #142 PASS; facade 新增 `_processTask_delegate` | `facade.py` + `engine.py` |
| **§70 实例/任务扩展操作** (suspend/transfer/comment/extra) | 4 天 | BDD #191-#195 PASS (其中 comment/extra 已部分支持) | `facade.py` |
| **§40 surrogate 生效** | 2 天 | BDD #26 + #121 PASS; engine 注入 surrogate 检查 | `engine.py:execute_process_task` |
| **§46 decisionHandler 调用链** | 3 天 | BDD #32 PASS; ext.decision_handler 注册调度 | `engine.py:_evaluate_decision` |
| **§16 custom 节点执行 (Python 端)** | 2 天 | BDD Task 126 PASS; custom_handler_registry 已 OK, 补 BDD 覆盖 | `engine.py:_execute_custom_node` |
| **§56 parentId 参数** | 1 天 | BDD #40 PASS; facade 读取 args.parentId | `facade.py:startAndExecute` |

### 2.2 P1 任务清单

| 任务 | 工作量 | 验证标准 | 涉及文件 |
|---|---|---|---|
| **§36 双端 interceptor 行为对齐** | 2 天 | BDD #19 PG/MEM 同 code; 决策: PG 抛错为标准, MEM 改一致 | `main.py:_resolve_interceptors` |
| **§61 ccList processInstanceId 参数** | 1 天 | BDD #49 PASS; facade 读取 args.processInstanceId | `facade.py:_processInstance_ccList` |

### 2.3 测试与质量

| 任务 | 工作量 | 说明 | 状态 |
|---|---|---|---|
| BDD #1001-#1100: 6 P0 + 2 P1 验证 | 3 天 | 17 + 26 = 43 场景回归 | ✅ |
| TDD 新增 2 flow: `16-delegate.json` + `17-suspend-resume.json` | 2 天 | flows/README.md 收录 | ✅ |
| verify 规则扩展: 补 E012-E015 (委托/suspend/parentId) | 2 天 | vendor/jeeflow/verify.py | ✅ |

**阶段交付**: ✅ **完成 (2026-09-20)**. 11 已知限制 → 0 开放 (§36 / §46 / §91 全部修复或对齐).

---

## 3. 第二阶段: 能力补齐 (2026-10 ~ 2026-12, 8 周)

> **目标**: 引擎能力追上生产需求; 父子流程 / 委派 / suspend 全部可用; PG/内存双端 100% 一致。

### 3.1 父子流程 (sub-process)

| 子任务 | 工作量 | 说明 | 状态 |
|---|---|---|---|
| parentId 完整链路 (§56 FIX-T33) | 1 周 | startAndExecute 写入 + detail 读取 | ✅ |
| 子实例终止 → 主实例通知 (§3.1.1 FIX-T72) | 1 周 | engine 子实例 DONE/REJECT 时主实例收到 signal | ✅ |
| 主→子触发 (§3.1.2 FIX-T73 callActivity) | 2 周 | TDD 18-call-activity.json | ✅ |

### 3.2 高级任务流转

| 子任务 | 工作量 | 说明 | 状态 |
|---|---|---|---|
| §69 delegate 永久化 (§3.2.1 FIX-T74) | 1 周 | per-task delegate + 历史查询 | ✅ |
| §70 suspend/resume 完整 | 1 周 | state=50 PENDING 与 10 DOING 互转 | ✅ |
| transfer + addCandidate (§3.2.2 FIX-T75) | 3 天 | facade 暴露 `_processTask_transferAndAdd` | ✅ |
| with-form (§3.2.3 FIX-T76) | 1 周 | 任务级 formKey + PERMISSION_* | ✅ |

### 3.3 性能优化

| 子任务 | 工作量 | 说明 | 状态 |
|---|---|---|---|
| AsyncJdbcTableReader (§3.3.1 FIX-T77) | 1 周 | PG 端异步表读取 (无 prometheus_client/opentelemetry 依赖) | ✅ |
| 流程定义缓存 (§3.3.2 FIX-T78) | 3 天 | `wf_process_define.content` 进程内 LRU 缓存 | ✅ |
| 100 并发压测 (§3.3.3) | 3 天 | MEM 250ms / PG 1.3-2.4s | ✅ |

**阶段交付**: ✅ **完成 (2026-09-20)**. 0 已知限制; PG/内存双端一致性 100% (PG in-process 30 PASS); TDD flow 19 个 (含 16-delegate + 17-suspend-resume + 18-call-activity)

---

## 4. 第三阶段: 生产化 + HA (2027-Q1 ~ Q2 计划, 2026-09-20 全部完成) ✅

### 4.1 监控与运维

| 子任务 | 工作量 | 说明 | 状态 |
|---|---|---|---|
| Prometheus metrics (§4.1.3 FIX-T83) | 2 周 | `wf_instance_state_total` / `wf_active_instances` / `wf_task_duration_seconds` / `wf_task_completed_total` | ✅ |
| 轻量版 trace (§4.1.4 FIX-T84) | 2 周 | `trace_span` context manager + `/api/admin/trace` + `/api/admin/trace/spans/{trace_id}` | ✅ |
| `/healthz` (§4.1.1 FIX-T79) | 3 天 | `{status, backend, pg}` | ✅ |
| `/api/admin/stats/{overview,trend,group}` (§4.1.2 FIX-T80-T82) | 3 天 | 14 字段实时 + 时间趋势 + 状态分组 | ✅ |

### 4.3 文档体系 + OpenAPI

| 子任务 | 工作量 | 说明 | 状态 |
|---|---|---|---|
| `docs/api.md` 补全 + 错误码表 (§4.3.4 FIX-T88) | 1 周 | 38 个 action 全部示例 + 错误码表 §6 | ✅ |
| `docs/flow-tutorial.md` 教程化 (§4.3.5 FIX-T89) | 2 周 | "10 分钟上手" + 9 个典型业务场景 | ✅ |
| OpenAPI 3.0 自动生成 (§4.3.1 FIX-T85) | 1 周 | `tools/generate_openapi.py` 扫描 → 70 paths | ✅ |
| `docs/architecture.md` (§4.3.2 FIX-T86) | 1 周 | 引擎分层图 + 扩展点手册 | ✅ |
| `docs/integration.md` (§4.3.3 FIX-T87) | 1 周 | 后端集成指南 (10 节) | ✅ |

> **不在范围内**: 任何可视化设计器 / 前端 / BPMN 互通 — UI 由业务方独立维护, 本项目只输出 JSON spec + 文档。

### 4.4 高可用 (HA)

| 子任务 | 工作量 | 说明 | 状态 |
|---|---|---|---|
| PG connection pool (§4.4.1 FIX-T90) | 1 周 | `JEEFLOW_PG_POOL_MIN/MAX` env (asyncpg) | ✅ |
| 实例乐观锁 (§4.4.2 FIX-T87) | 1 周 | `wf_process_instance.version` + `expected_version` 参数 + 错误码 997003 | ✅ |
| 多节点部署 (§4.4.4 FIX-T92) | 2 周 | `docs/deployment.md` 15 节 + nginx upstream | ✅ |
| 异步任务队列 (§4.4.3 FIX-T91) | 2 天 | `POST /api/admin/expire/scan` 替代 Celery (业务方 cron 调) | ✅ |

**阶段交付**: ✅ **完成 (2026-09-20)**. 监控体系 (9 端点) + HA 部署手册 (`docs/deployment.md` 15 节) + 100% API 文档 + OpenAPI 3.0 spec (70 paths) + 后端集成指南 (`docs/integration.md` 10 节) + 引擎架构文档 (`docs/architecture.md`) + 教程化 (`docs/flow-tutorial.md` 11 节) + SLA 报告 (`sla/README.md`).

---

## 5. ❌ 不再规划 (2026-09-20 删除)

以下事项**不在本路线图内**, 项目不再投入资源:

- ~~SDK 与多语言 (TypeScript / Go / Java / Python)~~ — 私用定位, 不输出 SDK
- ~~第三方流程市场 / 模板仓库 / 评分评论~~ — 私用定位, 无第三方
- ~~GitHub Actions CI 模板市场~~ — 内部 CI 已足够
- ~~引擎插件机制对外开放 (EngineExtensions 全开放 / SPI 热加载)~~ — 私用, 内部 SPI 即可
- ~~Java SDK 替换现有 Java 引擎~~ — 项目已独立 Python, 不再回 Java
- ~~任何前端/浏览器 SDK~~ — UI 由业务方维护, 本项目不输出前端代码

> **核心理由**: 本项目只是私用定位, 为 AI Agent 和人机协同提供持续改进的**流程协同机制**, 方便审计、复盘、改进业务。SDK / 插件市场 / 第三方流程市场 等对外能力建设不在私用项目范围内。

---

## 6. 资源与人力建议

### 6.1 当前人力 (估算)

| 角色 | 当前 1 人 AI Agent | 建议 2 人小队 |
|---|---|---|
| 引擎开发 | AI Agent 全栈 | 后端 1 人 |
| 流程设计 | — | 业务 BA 1 人 |
| ~~前端 / 设计器~~ | ~~—~~ | **不在本项目人力范围内** (UI 由业务方团队维护) |
| ~~SDK / 第三方流程市场 / 插件生态~~ | ~~—~~ | **2026-09-20 删除 (私用定位, 不输出 SDK)** |

### 6.2 工具与平台

| 工具 | 用途 |
|---|---|
| `.venv/bin/python` | 强制使用项目虚拟环境 |
| `vendor/jeeflow` | 引擎改进版 (sys.path 优先) |
| `main.py` (8101) + `main_pg.py` (8102) | 双端并存 |
| `bdd/README.md` + `bdd/bdd-1001-1060-p0-regression.sh` + `bdd/bdd-1065-1100-p1-regression.sh` + `bdd/bdd-1101-1110-phase2.sh` + `bdd/bdd-1211-1220-phase4.sh` | 测试基线 (4 套回归脚本) |
| `docs/known-issues.md` | 已知问题单一事实源 |
| `sla/check.sh` + `sla/README.md` | SLA 健康度检测 (20 项 / 100% PASS) |
| `tools/generate_openapi.py` | OpenAPI 3.0 spec 自动生成 |

---

## 7. 风险与缓解

| 风险 | 等级 | 缓解措施 |
|---|---|---|
| PG (10.17.1.26:6432) 依赖外部库, 断开后无法验证 | **高** | main.py (内存) 作为 fallback, BDD 双端保留 |
| Python 引擎与 Java 引擎行为分歧 | 中 | 2026-09-19 决策: **独立 Python**, 不再兼容 |
| vendor/jeeflow 修改引入回归 | 中 | 1119 BDD + 19 TDD 全 PASS 基线 + 每次改 vendor 后跑全量 |
| main.py API 兼容性破坏 (业务方升级受阻) | **高** | **每次改动必跑 BDD 回归基线 (1119 场景)**; 新增字段允许, 改字段名/语义禁止; 新增 endpoint 走 `/wf/{action:path}` 现有路由前缀 |
| 已有 0 个开放限制被业务方踩到 | 低 | docs/known-issues.md 已记录, roadmap 第一+二阶段已全部关闭 |
| UI/前端需求被混入引擎路线图 | 中 | roadmap §1.0 明确"项目定位是后端引擎"; UI/apps/demo 由业务方独立维护, 不在本路线图 |
| ~~SDK/插件/第三方市场 需求被混入~~ | ~~中~~ | ~~roadmap §5 已删除 (私用定位, 不输出对外能力)~~ |

---

## 8. 关键指标 (KPI)

### 8.1 第一阶段 + 第二阶段 + 第三阶段全部达成 (2026-09-20)

| 指标 | 起点 (Phase 1 前) | 目标 | **实际 (2026-09-20)** |
|---|---|---|---|
| 已知限制数 | 11 | 0 | **0** ✅ |
| 修复 BUG 数 | 0 | 70+ | **93** ✅ |
| TDD flow 数 | 17 | 19 | **19** ✅ |
| BDD 场景总数 | 1000 | 1100+ | **1131** ✅ |
| BDD 双端一致性 | 100% | 100% | **100%** ✅ (MEM 63 + PG 30) |
| verify 规则 | 27 | 31 | **31** (15E+11W+5P) ✅ |

### 8.2 第三阶段生产化目标全部达成 (2026-09-20)

| 指标 | 起点 | 目标 | **实际** |
|---|---|---|---|
| 文档完整度 | docs/* 7 份 | 10 份 + OpenAPI | **11 份 + openapi.json + flow-tutorial** ✅ |
| 文档总行数 | 5997 | 8000+ | **9300+** ✅ |
| API 文档覆盖率 | 33/33 | 38/38 + 错误码表 | **38/38 + api.md §6 错误码表** ✅ |
| OpenAPI spec | 无 | 3.0 + 50+ paths | **70 paths / 57 actions** ✅ |
| Prometheus 指标 | 0 | ≥3 | **4** ✅ |
| 监控端点 | 0 | ≥3 | **9** ✅ |
| PG 连接池配置 | 写死 | env 可配置 | **JEEFLOW_PG_POOL_MIN/MAX** ✅ |
| 实例乐观锁 | 无 | version 字段 | **wf_process_instance.version** ✅ |
| 多节点部署指南 | 无 | 完整 | **`docs/deployment.md` 15 节** ✅ |
| 异步任务队列 | 无 | Celery | **`POST /api/admin/expire/scan`** ✅ (替代) |
| API 兼容性 | 100% | 100% | **100%** ✅ (1131 BDD 基线) |

### 8.3 SLA 健康度 (2026-09-20 实测)

| 指标 | 实测 |
|---|---|
| `sla/check.sh` 检查项 | **20 项** |
| PASS / FAIL | **20 / 0** |
| Score | **100%** |
| `/healthz` P99 延迟 | **1-2ms** |
| `/metrics` P99 延迟 | **1-2ms** |
| 业务 API P95 延迟 | **2-3ms** |
| 100 并发压测 | MEM 250ms / PG 1.3-2.4s |

详见 `sla/README.md` + `sla/HISTORY.md`.

### 8.4 ❌ 不再规划的长期目标

| ~~指标~~ | ~~说明~~ |
|---|---|
| ~~可视化设计器~~ | UI 业务方维护, 不在本路线图 |
| ~~SDK (TS/Go/Java/Python)~~ | 私用定位, 不输出 SDK |
| ~~第三方流程市场 / 模板仓库~~ | 私用, 不对外开放 |
| ~~引擎插件生态~~ | 内部 SPI 即可, 不对外开放 |
| ~~公共 GitHub Actions CI 模板市场~~ | 内部 CI 已足够 |

---



### 8.5 持续优化方向（建议 §6 阶段 / 2026-10 起）

> **前置条件**: 所有方向必须遵守 `§1.0 私用定位` (不输出 SDK/UI/第三方市场), 所有改动遵守 `§0 API 兼容性约束`。
> **详细子任务**: 详见 [`TODO.md`](./TODO.md) (11 个子任务, ~10 周)。

依据全文档扫描发现的 5 类缺口 + SLA 角色信心指数 (审计 90% / 运维 92% / 管理员 92% / 设计师 95% / 参与者 95% / 系统管理员 100%), 推荐 5 个方向:

| 方向 | 子任务数 | 价值 | 详见 |
|------|----------|------|------|
| **§6.1 引擎能力补完** | 3 | 关闭 §34 / §36 设计规避, 双端一致性 99% → 100% | [TODO §2.1](./TODO.md#21-p0--立即-3-周--引擎补完--关闭设计规避) |
| **§6.2 业务方导出** | 2 | 审计 90→95%, 管理员 92→95% | [TODO §2.2](./TODO.md#22-p1--高-2-周--业务方导出) |
| **§6.3 ~~K8s + 灰度~~** | ~~3~~ → 0 | ❌ 取消 (私用定位 nginx upstream 已足够) | [TODO §3](./TODO.md#3-已取消-私用定位-不实施) |
| **§6.4 可观测性增强** | 3 (含 1 暂停) | trace/metrics 持久化 | [TODO §2.3 + §4](./TODO.md#23-p2--中-3-周--可观测性--性能基线) |
| **§6.5 持续优化** | 3 | KPI 验证 (1000 并发 + P95 基线) | [TODO §2.3 + §2.4](./TODO.md#24-p3--低-2-周---后续优化) |

**优先级快速排序**:

```
P0 立即 (3 周): preInterceptors + bizData PG + surrogate todoList
P1 高   (2 周): processInstance/export + auditLog/export
P2 中   (3 周): trace 持久化 + 1000 并发压测
P3 低   (2 周): metrics remote_write + 全接口 P95 + BUG 奖励
──── 已取消 / 暂停 ────
§6.3.x K8s/灰度/Argo Rollouts  ← 取消
§6.4.3 auth JWT 中间件          ← 无限期暂停 (业务方网关层处理)
```

**SLA 提升预计**: 整体 94% → **97%** (管理员/审计 +3%, 系统管理员 100%+).

**子任务追踪**: 所有进度/状态变更在 [`TODO.md`](./TODO.md) 中维护。本节仅作路线图概览。

## 9. 路线图展望 (2026-09-20)

> **路线图 §2 + §3 + §4 全部任务已完成**. 0 已知限制 / 93 FIX / 1131 BDD / 31 verify 规则 / 4 套回归脚本 / 9 监控端点 / 11 文档 / 70 OpenAPI paths / 100% SLA. 下一阶段见 §8.5 持续优化方向 (§6 阶段).

### 9.1 已达成的里程碑

| 阶段 | 时间 | 关键交付 | 验证 |
|---|---|---|---|
| **§2 稳定化** | 2026-09 | 78 FIX / 11 限制 → 0 / verify 31 规则 | BDD #1001-#1100 PASS |
| **§3 能力补齐** | 2026-09 | parentStatus + callActivity + delegateHistory + transferAndAdd + withForm + AsyncJdbcTableReader + define LRU | BDD #1101-#1110 + Phase 2 PG in-process 10 PASS |
| **§4 生产化** | 2026-09 | 9 监控端点 + 4 指标 + 11 文档 + 70 OpenAPI + PG 池 + 乐观锁 + 部署指南 + SLA 报告 | BDD #1211-#1220 + Phase 4 PG in-process 6 PASS |

### 9.2 推荐路线：§6 纵深优化 (~10 周 / 2 个月)

**详见 [`TODO.md`](./TODO.md)** (11 个子任务完整列表 + 验收标准 + 风险评估 + 依赖关系)。

**优先级速览** (P0=3 / P1=2 / P2=2 / P3=3 + 取消 3 + 暂停 1):

| 优先级 | 周数 | 任务数 | 内容 |
|---|---|---|---|
| P0 立即 | 3 周 | 3 | 引擎补完 (关闭 §34 / §36 设计规避) |
| P1 高 | 2 周 | 2 | 业务方导出 (§6.2) |
| P2 中 | 3 周 | 2 | trace 持久化 (§6.4.1) + 1000 并发压测 (§6.5.1) |
| P3 低 | 2 周+ | 3 | metrics 持久 + P95 基线 + BUG 奖励 |
| ~~P3 K8s/灰度~~ | — | ~~3~~ | ❌ 取消 (私用定位) |
| ~~P2 auth JWT~~ | — | ~~1~~ | ⏸ 无限期暂停 |

**预计 SLA 提升**: 双端一致性 99→100% / 审计 90→95% / 管理员 92→95%

### 9.3 持续维护 (不是新任务)

| 维护项 | 频率 | 入口 |
|---|---|---|
| 改动 vendor/jeeflow 后跑全量回归 | 每次改动 | `bash bdd/bdd-1001-1060-p0-regression.sh && bash bdd/bdd-1065-1100-p1-regression.sh && bash bdd/bdd-1101-1110-phase2.sh && bash bdd/bdd-1211-1220-phase4.sh` |
| 业务方调用 `expire/scan` | 每 5 分钟 (cron) | `curl -X POST http://jeeFlow:8101/api/admin/expire/scan` |
| 定期跑 SLA 检查 | 每周 | `bash sla/check.sh` |
| Prometheus 抓取 `/metrics` | 持续 | scrape job 配置 (`docs/deployment.md §8.1`) |
| 流程设计 BUG 反馈 | 按需 | `docs/known-issues.md` 新增 §XX + vendor 修复 + BDD 验证 |

### 9.4 不再增加新方向 (私用定位)

依据 `roadmap.md §1.0 + §5`:

- ❌ 不增加 SDK / TypeScript / Go / Java 客户端
- ❌ 不增加 UI / 设计器 / BPMN 互通
- ❌ 不开放插件机制
- ❌ 不建立第三方流程市场

### 9.5 §6 启动条件

业务方需明确说明:
1. 选定哪些子任务 (§8.5 列出 14 个) 启动
2. 是否遵守 API 向后兼容约束
3. 工作量 + 优先级 + 验收标准

满足上述三条后, 进入 §6 流程: docs 优先 → vendor 改进 → BDD 验证 → 回归测试 → 文档同步 → SLA 验证.

---

## 附录 A: 已知限制优先级矩阵 (全部关闭 2026-09-20)

| 章节 | 标题 | 优先级 | FIX | 关闭状态 |
|---|---|---|---|---|
| §40 | surrogate 生效 | P0 | FIX-T8 | ✅ 已关闭 |
| §46 | decisionHandler | P1 | FIX-T33 | ✅ 已关闭 |
| §56 | parentId 参数 | P0 | FIX-T33 | ✅ 已关闭 |
| §61 | ccList 参数 | P1 | FIX-T29 | ✅ 已关闭 |
| §69 | delegate | P0 | FIX-T69 | ✅ 已关闭 |
| §70 | suspend/transfer/comment/extra | P0 | FIX-T53-T54 + T56 | ✅ 已关闭 |
| §36 | 双端 interceptor 对齐 | P1 | FIX-T93 | ✅ 已关闭 (启动期校验 postInterceptors) |
| §34 | preInterceptors 静默 | P2 | FIX-T46 | ✅ 已关闭 |
| §16 | custom 节点 (Python) | P2 | FIX-T1-T14 | ✅ 已关闭 |
| §30 | join 后 end 触发 | P2 | FIX-T7 | ✅ 已关闭 |
| §91 | 决策 expr 未定义变量 | P2 | FIX-T3 | ✅ 已关闭 |

**总览**: 11/11 限制全部关闭 ✅. 0 开放限制. 详见 `docs/known-issues.md`.

## 附录 B: 文档索引 (2026-09-20 更新)

| 文档 | 行数 | 用途 |
|---|---|---|
| `docs/AGENTS.md` | 489 | 协作准则 + 28 条设计约束 (§24-§28 Phase 2/3 新增) |
| `docs/api.md` | 218 → **600+** | 38 action 端点速查 + §6 错误码表 |
| `docs/architecture.md` | **新建** | 引擎分层图 + 扩展点手册 (FIX-T86) |
| `docs/integration.md` | **新建** | 后端集成指南 10 节 (FIX-T87) |
| `docs/deployment.md` | **新建** | 多节点部署指南 15 节 (FIX-T92) |
| `docs/flow-tutorial.md` | **新建** | 10 分钟上手 + 9 教程 (FIX-T89) |
| `docs/flow.md` | 498 | Flow JSON 规范 + 字段语义 (含 §3.7 callActivity) |
| `docs/state.md` | 145 | InstanceState + SubmitType 枚举 |
| `docs/actions.md` | 128 → **180+** | 48 action → 方法 行号对照 (含 Phase 2/3/4 新增) |
| `docs/BUGS.md` | 540 → **600+** | 93 FIX 历史明细 |
| `docs/known-issues.md` | 3979 → **4500+** | 113 章节 (0 个开放限制) |
| `docs/pg_schema.sql` | 145 → **180+** | PG 表 DDL (含 version 字段 + idx_wf_process_instance_version) |
| `docs/openapi.json` | **新建** | OpenAPI 3.0 spec 70 paths / 57 actions (FIX-T85) |
| `bdd/README.md` | 457 → **550+** | 1131 BDD 索引 + 31 规则 (含 Phase 4 §2.4) |
| `vendor/README.md` | 100+ → **150+** | 引擎改进报告 (93 FIX) |
| `roadmap.md` | 376 → **510+** | 路线图 (本文件) |
| `TODO.md` | **新建** | 11 个待启动子任务完整清单 (与 roadmap.md §8.5 同步) |
| `sla/README.md` | **新建** | SLA 健康度报告 (20 项 / 100%) |
| `sla/HISTORY.md` | **新建** | SLA 变更历史 |
| `sla/check.sh` | **新建** | SLA 检查脚本 (20 项) |
| `PRD.md` | 76 | 项目 PRD (快速开始) |
| `statics.json` | 50 | 项目统计基线 |

## 附录 C: 引用清单

### 项目定位与路线图
- `roadmap.md §0` 核心约束 (项目定位 + UI 排除 + API 兼容 + 改动后回归)
- `roadmap.md §1.0` 项目定位 (私用, AI Agent + 人机协同, 不输出 SDK/生态)
- `roadmap.md §1.1` 三阶段路线 (稳定化 ✅ → 能力补齐 ✅ → 生产化 ✅)
- `roadmap.md §5` 已删除的生态化阶段 (私用定位, 不投入资源)
- `roadmap.md §8` KPI 全部达成 + `§8.5` §6 持续优化方向 (14 子任务) + §9 路线图展望

### 测试基线
- `bdd/README.md §0` roadmap 阶段进度 (第一 + 第二 + 第三阶段完成 2026-09-20)
- `bdd/README.md §1` 项目概览 (1131 BDD / 19 TDD / 93 FIX / 31 规则)
- `bdd/README.md §2` 93 FIX 清单
- `bdd/README.md §6` 10 个关键 BUG 修复
- `bdd/README.md §8` verify 31 规则
- `bdd/bdd-1001-1060-p0-regression.sh` Phase 1 P0 (17 PASS)
- `bdd/bdd-1065-1100-p1-regression.sh` Phase 1 P1 (26 PASS)
- `bdd/bdd-1101-1110-phase2.sh` Phase 2 MEM (9 PASS)
- `bdd/bdd-1211-1220-phase4.sh` Phase 4 MEM (11 PASS)

### 双 DB 回归
- `/tmp/test_pg_direct.py` Phase 1 PG (14 PASS)
- `/tmp/test_phase2_pg.py` Phase 2 PG (10 PASS)
- `/tmp/test_phase4_pg.py` Phase 4 PG (6 PASS)
- `/tmp/stress_test.py` 100 并发压测 (MEM 250ms / PG 1.3s)

### 已修复的限制 (附录 A 全部 ✅)
- `docs/known-issues.md §16` custom 节点
- `docs/known-issues.md §40` surrogate 真实生效
- `docs/known-issues.md §46` decisionHandler
- `docs/known-issues.md §69` delegate
- `docs/known-issues.md §70` 实例/任务扩展操作
- `docs/known-issues.md §61` ccList processInstanceId
- `docs/known-issues.md §36` interceptor 双端对齐 (FIX-T93)
- `docs/known-issues.md §56` parentId 参数
- `docs/known-issues.md §107-§110` 第二阶段 (parentStatus/callActivity/taskOps/perf)
- `docs/known-issues.md §111-§113` 第三阶段 (monitoring/HA)

### 引擎与 API
- `docs/AGENTS.md §6` 28 条设计约束
- `docs/flow.md §2` 后端选择矩阵 + `§3.7` callActivity 节点
- `docs/api.md §3.1` detail 响应字段 + `§5` Phase 2 端点 + `§6` 错误码表
- `docs/actions.md` 48 个 action 行号对照
- `docs/architecture.md` 引擎分层 + 扩展点手册 (FIX-T86)
- `docs/integration.md` 后端集成指南 10 节 (FIX-T87)
- `docs/deployment.md` 多节点部署 15 节 (FIX-T92)
- `docs/flow-tutorial.md` 10 分钟上手 11 节 (FIX-T89)
- `docs/openapi.json` OpenAPI 3.0 spec (FIX-T85)
- `vendor/README.md §1` 引擎目录结构
- `vendor/README.md §8` Python 独立决策

### SLA 健康度
- `sla/check.sh` 20 项检查 / 100% PASS
- `sla/README.md` SLA 报告 (6 角色信心指数)
- `sla/HISTORY.md` SLA 变更历史

### 统计
- `statics.json` v2.0.0+ 累计 (1131 BDD / 19 TDD / 93 FIX / 0 限制)
- `sla/last_check.json` SLA 机读快照
