# CC · 01 · 流程引擎开发升级

> **Persona**：流程引擎开发者（vendor/jeeflow 维护者 + 升级对接上游 jeeflow 的工程师）
> **时间预算**：半天/周（异步）+ 1-2 天/升级事件
> **典型任务**：改 EngineImpl 不破坏 API 契约 / 升级 vendor/jeeflow/ 与上游同步 / 加新的 SPI 实现 / 修 bug

---

## 1. Persona Profile

| 维度 | 内容 |
|---|---|
| 角色 | 后端 Python 工程师，负责 vendor/jeeflow/*.py 维护 |
| 工具 | `python3 -m uvicorn main:app --port 8101`、`pytest`、`vendor/jeeflow/verify.py` |
| 痛点 | 改一处打破 134 处 doc 引用 / 升级上游后契约变化 / 不知道哪些 API 是公开契约 |
| 期望 | 升级前知道改动面 / 改完后自动校验 / 不破坏 `/wf/*` 端点契约 |
| 成功标志 | `ToT/sop/release.sh` 通过 + `/healthz` 返回新 version |

---

## 2. Evidence（事实现状）

| 维度 | 数据 | 来源 |
|---|---|---|
| 引擎代码量 | **8681 行** | `find vendor/jeeflow -name '*.py' -exec cat {} +` |
| 公开 API 数 | **73 个**（class/def/async def，不含 `_`） | `grep -hE '^(class\|def\|async def)' vendor/jeeflow/*.py` |
| 内部 .py 文件 | 12 个 | `ls vendor/jeeflow/*.py \| wc -l` |
| 上游引用 | 13 个（已应用 27 FIX-T + 11 本仓独有） | `ToT/docs/diffs.md` |
| 文档引用 | **139 处** 全部对齐 | `ToT/sop/doc-link-checker.py` |
| 健康度 | 100/100 🟢 | `ToT/sop/health-check.py` |
| 升级迁移文档 | ❌ 无 | 缺失 |
| API surface doc | ⚠️ 仅在 concepts/09-core-types.md 列了 16 个核心类型 | 缺口 57 个 |

---

## 3. 当前缺口（Gaps）

1. **升级迁移路径缺失**：上游 v0.x → v1.x → v1.10.x 的 breaking change 无文档，下次升级时只能靠 git blame + 跑测试
2. **公开 API 总览不集中**：73 个 API 散落在 12 个文件，没有 single source of truth 的索引页
3. **verify.py 缺算法说明**：`vendor/jeeflow/verify.py`（699 行）有 3 个公开函数 + 1 个类，没有算法说明
4. **SPI 实现矩阵缺失**：4 个 SPI 接口 × 2 实现（Memory/PG）的差异表未沉淀
5. **Extension Hook 未索引**：engine_extensions.py 的 EventType 6 事件 + FlowInterceptor 拦截点未集中列表

---

## 4. 短期行动计划（4 周）

### A1. API Surface Reference（API 索引页）
- **位置**：`ToT/CC/api-index.md`（新建）
- **内容**：73 个公开 API，按文件分组，每项：签名 + 一行用途 + 行号 + 关联 spec doc
- **数据源**：`health-check.py --dimension api --json` 的 API 名单 + `vendor/jeeflow/*.py` 行号
- **ETA**：W1 末
- **成功标准**：`health-check.py` API Coverage 维度仍 100，新 doc 被 doc-link-checker 收录

### A2. Upgrade Migration Guide（升级迁移指南）
- **位置**：`ToT/CC/upgrade-migration.md`（新建）
- **内容**：
  - v0.x → v1.0 breaking change 清单（需 git log 提炼）
  - v1.0 → v1.10 字段演进（`taskType` int→str、`processDesign` JSON 结构变化等）
  - 升级 checklist：先跑 `pytest` → 再跑 `ToT/sop/release.sh` → 再观察 `/healthz`
- **ETA**：W2 末
- **成功标准**：下次升级按此文档 0 breaking surprise

### A3. verify.py 算法说明
- **位置**：`ToT/docs/spec/verify-algorithm.md`（新建，归属 spec/）
- **内容**：
  - `verify_flow(flow, variables)` 三段返回（errors / warnings / infos）的判定逻辑
  - 12 个 checker 函数列表（如 `_check_cycle`、`_check_orphan_node`）
  - severity 判定矩阵（哪些错会让发布失败）
- **ETA**：W2 末
- **成功标准**：bug 排查时间从 30 分钟降到 5 分钟

### A4. SPI 实现矩阵
- **位置**：`ToT/docs/spec/spi-matrix.md`（新建）
- **内容**：
  - 4 个 SPI（ProcessRepository / UserProvider / IDGenerator / ExpressionEvaluator）× 2 实现（Memory / PG / FDEP）
  - 差异表：哪些方法只 Memory 有 / 哪些 PG 限制 / FDEP 走 SPI 协议
- **ETA**：W3 末
- **成功标准**：新人 onboard 不用问「这 API 内存能用吗」

### A5. Engine Extension Hook Reference
- **位置**：`ToT/docs/spec/extension-hooks.md`（新建）
- **内容**：
  - EventType 6 个事件 + 触发时机（`extensions.py:8`）
  - FlowInterceptor 拦截点（pre / post / on_error）
  - EngineExtensions 注册 API（interceptor_registry / event_listener / decision_handler）
- **ETA**：W3 末
- **成功标准**：扩展点开发零咨询

### A6. CI 门禁加固
- **位置**：`ToT/sop/release.sh` Step 0
- **动作**：把 `health-check.py --json` 加进 release 流水线，综合分 <100 阻断
- **ETA**：W4 末 — ✅ 已完成 2026-09-25
- **成功标准**：retro 测试一次「故意改坏」会被卡 — ✅ 测试通过

---

## 5. 反馈闭环（Feedback Loop）

| 渠道 | 内容 | 频率 |
|---|---|---|
| `feedback/01-engine-developer-<seq>.md` | 文档 gap / API 误用 / 升级问题 | 随时 |
| `feedback/_routes/01-*.md`（来自 **03-participant**）| 参与者反馈中带 `bug` 标签的 | 每周自动分流 |
| `vendor/jeeflow/*.py:行注释` ` # CC: <seq>` | 锚定 doc 与代码 | 写代码时 |
| release.sh 后健康度变化 | 自动检测 doc drift | 每 release |

**反馈处理 SLA**：
- P0（升级卡住）：24h 内回复
- P1（API 不清楚）：1 周内加 doc
- P2（建议）：季度评审
- **来自 03-participant 的 P1**：48h 内（飞轮优先级高）

---

## 5.5 ★ 来自参与者反馈的接收（飞轮下游）

本 plan 是飞轮的 3 个下游之一。参与者反馈中带以下标签的会自动路由到本 plan：

| 反馈标签 | 触发行动 | 路由工具 |
|---|---|---|
| `bug` + 涉及 `vendor/jeeflow/*.py` | A6 修复 + 加注释 `# CC: <seq>` | `feedback-triage.py` |
| `bug` + 涉及 `main_*.py` 或端点 500 | A1/A3 加 API 索引或 verify 算法 | `feedback-triage.py` |
| `system-perf`（虽然最终归 04，但代码层优化归 01）| A4 SPI 矩阵更新 | `feedback-triage.py` |

**闭环要求**：
- 修完代码后必须在 `feedback/_routes/01-<seq>.md` 标注 `状态: 已闭环`
- 自动同步到 `feedback/03-participant-<seq>.md` 的 `## 闭环` 字段
- 同步更新 `ToT/CC/faq.md`（如有相关 FAQ）

---

## 6. Success Metrics（量化）

| 指标 | 当前 | 目标（4 周末） |
|---|---|---|
| `health-check.py` 综合分 | 100/100 | ≥ 100 |
| `doc-link-checker.py` drift | 0/139 | 0 |
| `verify.py` bug 平均定位时间 | 30 分钟 | 5 分钟 |
| 升级事件平均回归缺陷数 | 未知（基线） | ≤ 1 |
| 新 API 文档覆盖率 | 73/73 = 100% | 持续 100% |

---

## 7. 跨 Persona 引用

- → 02-process-designer：Engine 改动了哪些影响设计者？需在 release notes 注明
- → 04-ops-audit：API 升级时 `/version` + `/healthz` 必须先回退兼容
- → ToT/docs/concepts/09-core-types.md：API 索引的源材料
- → ToT/docs/spec/04-engine-ops.md：引擎操作 API 完整签名