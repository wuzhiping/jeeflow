# 此项目由OpenCode, 协同Hermes Agent共同开发完成
 * 续迭代中

<img width="1821" height="1073" alt="dc2e55f9-3d28-4fb8-ab35-19ca517870aa" src="https://github.com/user-attachments/assets/28b457fc-8761-4f7b-9341-8054542903b7" />

# UI (可以略过)
* cd ui
* pnpm install
* pnpm dev
* pnpm build:demo

# API (aio)
* uv run main.py

# http://localhost:8101/jeeflow/ui/

# [SPI](https://jeeflow-doc.mldong.com/languages/python/spi-guide)
```
# sqlite:Memory for DEV
from jeeflow import MemoryRepository
repo = MemoryRepository()

# PostgreSQL（pip install jeeflow[postgres]）
import asyncpg
from jeeflow import JdbcRepository, PostgresAdapter
pool = await asyncpg.create_pool("postgresql://root:pwd@127.0.0.1/jeeflow")
repo = JdbcRepository(PostgresAdapter(pool))
```

```
docker build -t shawoo/jeeflow .
docker run --rm -p 8101:8101 shawoo/jeeflow
```

---

# docs

> 本项目文档全集. **最近更新**: 2026-09-26 — ToT/docs/ v2 体系建立 (51 .md / 10,161 行) + ToT/CC/ 客户中心 (15 文件) + 飞轮中枢 03-participant + SOP 工具链 22 个.

## 📋 核心路线图 / 状态

| 文件 | 用途 | 关联 |
|------|------|------|
| [`roadmap.md`](./roadmap.md) | 项目全阶段路线图 (Phase 1~6 + §7), 含已完成项 + 推荐方向 | ↔ `TODO.md` / `sla/HISTORY.md` |
| [`TODO.md`](./TODO.md) | 待办清单 + 各子任务状态/工作量/验收标准 | ↔ `roadmap.md §9.6` / `sla/HISTORY.md` |
| [`statics.json`](./statics.json) | 项目统计快照 (fix_total=106, bdd=1188, sla_score=100, section7=5/5) | ↔ 所有文档 |
| [`docs/BUGS.md`](./docs/BUGS.md) | BUG 修复总表 (T1-T106), 含 §7 段落 (FIX-T105~T109) | ↔ `vendor/jeeflow/*.py` |
| `SLA.md` | SLA 检测指导原则 (AI Agent 协作基线, 不含状态) | ↔ `sla/README.md` |

## 📊 SLA 与验证

| 文件 | 用途 | 关联 |
|------|------|------|
| [`sla/README.md`](./sla/README.md) | SLA v6 完整说明 (43 项检查, score=100) | ↔ `SLA.md` / `sla/check.sh` |
| [`sla/check.sh`](./sla/check.sh) | SLA 验证脚本 (43 项, 含双端 + flows) | ↔ `main.py` (8101) + `main_pg.py` (8102) |
| [`sla/check_flows_dual.sh`](./sla/check_flows_dual.sh) | 双端 flows 部署+执行验证 | ↔ `flows/*.json` |
| [`sla/check_bdds_dual.sh`](./sla/check_bdds_dual.sh) | 18 套 BDD 双端全量验证 | ↔ `bdd/*.sh` |
| [`sla/HISTORY.md`](./sla/HISTORY.md) | SLA 历史记录 (v1→v7, 2026-09-20 含 §7 完成) | ↔ `sla/last_check.json` |
| [`sla/POSTMORTEM.md`](./sla/POSTMORTEM.md) | SLA 作业复盘 (5 个错误 + 根因 + 防御, 防下次再犯) | ↔ `sla/check*.sh` |
| `sla/last_check.json` | 最新 SLA 检查结果 (44/44 PASS, score=100) | ↔ `sla/check.sh` |

## 🔧 引擎与 API 文档

| 文件 | 用途 | 关联 |
|------|------|------|
| [`docs/architecture.md`](./docs/architecture.md) | 引擎整体架构 (MEM/PG 双后端, vendor/jeeflow/) | ↔ `vendor/jeeflow/*.py` |
| [`docs/api.md`](./docs/api.md) | API 端点详解 (单入口 `/wf/{action:path}`) | ↔ `docs/actions.md` |
| [`docs/actions.md`](./docs/actions.md) | 59 个 action 清单 (§3 processInstance 含 §7.3.1 rollback + §7.3.3 doingList) | ↔ `vendor/jeeflow/facade.py` |
| [`docs/openapi.json`](./docs/openapi.json) | OpenAPI 3.1 规范 (59 endpoints, catch-all `/wf/{action}`) | ↔ `main.py` + `main_pg.py` |
| [`docs/flow.md`](./docs/flow.md) | 流程 JSON 完整规范 (10 节) | ↔ `docs/flow-tutorial.md` |
| [`docs/state.md`](./docs/state.md) | 状态机枚举 (InstanceState 7 种 + SubmitType + TaskState) | ↔ `vendor/jeeflow/model.py` |
| [`docs/pg_schema.sql`](./docs/pg_schema.sql) | PostgreSQL DDL (9 张表) | ↔ `vendor/jeeflow/repository/{base,postgres,ext}.py` |
| `docs/deployment.md` | 部署指南 (Docker, 端口 8101/8102) | ↔ `Dockerfile` |
| `docs/integration.md` | 集成指南 (SPI, 业务嵌入) | ↔ `spi.py` |

## 🧪 测试与样例

| 文件 | 用途 | 关联 |
|------|------|------|
| `bdd/*.sh` | BDD 验证脚本 (1188 个 BDD, 18 套含 §7) | ↔ `sla/check_bdds_dual.sh` |
| `bdd/*.json` `bdd/*.md` | BDD 场景描述 (业务方运维场景) | ↔ `bdd/*.sh` |
| `tdd/flows-*.py` | TDD 流程验证 (19 个, 含断点续跑 / suspend-resume) | ↔ `flows/*.json` |
| `flows/*.json` | 19 个生产流程定义 (P0/P1/P2 业务场景) | ↔ `sla/check_flows_dual.sh` + `tdd/flows-*.py` |
| `seed_business.py` | 业务数据种子 (16 进行中 + 9 已完成 + 8 委托) | ↔ `main.py` `run_seed_business` |

## 📖 设计 / 协作指南

| 文件 | 用途 | 关联 |
|------|------|------|
| [`docs/AGENTS.md`](./docs/AGENTS.md) | AI Agent 协作指南 (流程设计 + 流程测试 Agent) | ↔ `../AGENTS.md`（项目根，唯一全局行为准则）|
| [`docs/known-issues.md`](./docs/known-issues.md) | 已知问题登记 (§1~§78, 引擎行为约束) | ↔ `vendor/jeeflow/*.py` |
| `docs/flow-tutorial.md` | 流程设计教程 (从入门到进阶) | ↔ `docs/flow.md` |

## 🆕 ToT 知识体系（v2，2026-09-18 之后建立）

> **新入口**：从单一来源 jeeflow 文档裁剪出本仓设计契约 + 客户中心 + 工具链；客户系统版本自动同步。

| 文件 / 目录 | 用途 | 受众 |
|---|---|---|
| [`ToT/docs/`](./ToT/docs/) | 设计契约 + 用户手册底层知识库 (51 .md / 10,161 行) | 全员（基础知识层）|
| [`ToT/docs/README.md`](./ToT/docs/README.md) | ToT/docs/ 文档地图 + 工具链索引 | 找任何 doc 之前先看 |
| [`ToT/docs/REPORT.html`](./ToT/docs/REPORT.html) | 健康度可视化报告（自动生成）| 看整体质量 |
| [`ToT/CC/`](./ToT/CC/) | 客户中心 + 4 类 persona 计划（15 文件）| 按角色查 |
| [`ToT/CC/README.md`](./ToT/CC/README.md) | CC 飞轮架构图 + 入口 | 找 persona plan |
| [`ToT/sop/`](./ToT/sop/) | 工具链（22 .py + 1 .sh）| 跑命令 |
| [`ToT/sop/health-check.py`](./ToT/sop/health-check.py) | 5 维度健康度评分 | CI 门禁 |
| [`ToT/sop/release.sh`](./ToT/sop/release.sh) | 发版流水线（含 drift gate + 健康度门禁 + 版本注入）| 发版时 |
| [`ToT/skills/flow-operator/`](./ToT/skills/flow-operator/) | AI Agent 技能：流程执行层 | AI 加载 |
| [`ToT/GETTING_STARTED.md`](./ToT/GETTING_STARTED.md) | 5 分钟入门（角色路由）| **新人第一份** |
| [`ToT/HANDBOOK.md`](./ToT/HANDBOOK.md) | 知识手册（架构 + 环境 + 任务）| 工作深度参考 |

## 🗂️ 文档关联拓扑

```
roadmap.md (路线图)
  └─→ TODO.md (待办 + 状态)
  └─→ sla/HISTORY.md (SLA 历史)
       └─→ sla/README.md (SLA 当前)
            └─→ sla/check.sh (SLA 验证工具)
                 ├─→ main.py (8101 MEM)
                 ├─→ main_pg.py (8102 PG)
                 ├─→ flows/*.json (流程定义)
                 ├─→ tdd/flows-*.py (TDD)
                 ├─→ bdd/*.sh (BDD 脚本, 18 套双端)
                 │   └─→ bdd/*.json + bdd/*.md (场景描述)
                 └─→ vendor/jeeflow/*.py (引擎实现)
                      └─→ docs/architecture.md
                      └─→ docs/actions.md (50 endpoints)
                      └─→ docs/api.md (API 详解)
                      └─→ docs/openapi.json (OpenAPI 规范)
                      └─→ docs/state.md (状态机)
                      └─→ docs/flow.md (流程 JSON 规范)
                      └─→ docs/pg_schema.sql (PG DDL)
                      └─→ docs/known-issues.md (§1~§78)
                      └─→ docs/BUGS.md (FIX-T1~T106)
                           └─→ statics.json (项目统计快照)
```

## 📈 当前关键数据 (2026-09-26)

- **fix_total**: 106 (T1-T106, §6 10 + §7 5)
- **bdd**: 1188 / 1188 PASS (含 §7 28 个)
- **SLA**: 43 / 43 PASS, score=100
- **路线图**: Phase 1~6 + §7 (5/5, T105-T109) 全部完成
- **取消/暂停**: §7.1 (性能) / §7.4 (安全) / §7.6 (可观测) 取消, §7.5 (SPI) 暂停 (私用定位)
- **双端一致性**: MEM + PG 100% 一致 (11-assignment-handler 唯一差异, 业务方生产用真实角色)
- **ToT 健康度** (5 维度): 100/100 🟢 — drift 0/146 · API 73/73 · 飞轮 1 RPM（首次 E2E 演示）
- **客户系统版本**: v1.11.8+b4d7308（`/version` 自动同步）
- **公开 API 数**: 73（已 100% 索引）

## 🔍 快速检索

- **找 BUG 修复**: `docs/BUGS.md` (按 FIX-T 编号) 或 `grep "FIX-T10" docs/`
- **找 SLA 检查**: `sla/check.sh` + `sla/last_check.json`
- **找 API 端点**: `docs/actions.md` (列表) / `docs/api.md` (详解) / `docs/openapi.json` (规范)
- **找流程定义**: `flows/*.json` (生产) / `docs/flow.md` (规范)
- **找 BDD 验证**: `bdd/*.sh` (脚本) / `bdd/*.md` (场景)
- **找引擎实现**: `vendor/jeeflow/*.py` (source of truth)
- **找路线图状态**: `roadmap.md §9.6` / `TODO.md §7` / `sla/HISTORY.md §7`
