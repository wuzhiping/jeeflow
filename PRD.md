# jeeFlow 工作流引擎

> **私用项目**: 为 AI Agent 和人机协同提供持续改进的工作流协同机制。
> **当前阶段**: 2026-09-20 完成 §2 + §3 + §4 全部任务 (引擎稳定化 + 能力补齐 + 监控/HA)。
> **API 契约**: 38 个 `/wf/{action}` 端点 + 9 个监控端点, 100% 向后兼容。
> **测试覆盖**: 1131 BDD + 19 TDD 双端 PASS。

---

## 快速开始

```bash
# 内存后端 (开发 / 单机)
.venv/bin/python main.py             # 监听 :8101

# PG 后端 (生产 / 多节点)
JEEFLOW_PG_DSN=postgresql://... \
JEEFLOW_PG_POOL_MIN=5 JEEFLOW_PG_POOL_MAX=20 \
.venv/bin/python main_pg.py          # 监听 :8101
```

## 核心端点

| 类别 | 路径 | 说明 |
|------|------|------|
| 流程定义 | `POST /wf/processDesign/{save,deploy,page,...}` | 流程定义 CRUD + 部署 |
| 流程实例 | `POST /wf/processInstance/{start,startAndExecute,approve,reject,...}` | 实例生命周期 |
| 任务操作 | `POST /wf/task/{approve,reject,delegate,transfer,...}` | 用户任务处理 |
| 监控 | `GET /healthz` `GET /metrics` `GET /api/admin/stats/overview` `GET /api/admin/trace` | 监控端点 |
| 异步 | `POST /api/admin/expire/scan` | 过期任务扫描 (替代 Celery) |

详见 `docs/api.md`。

## 文档

- [`docs/api.md`](docs/api.md) — 38 个 action 完整规范
- [`docs/architecture.md`](docs/architecture.md) — 引擎分层 + 扩展点
- [`docs/integration.md`](docs/integration.md) — 后端集成指南
- [`docs/deployment.md`](docs/deployment.md) — 多节点生产部署
- [`docs/flow-tutorial.md`](docs/flow-tutorial.md) — 10 分钟上手教程
- [`docs/openapi.json`](docs/openapi.json) — OpenAPI 3.0 spec (70 paths)
- [`roadmap.md`](roadmap.md) — 路线图与定位说明
- [`statics.json`](statics.json) — 项目统计基线

## 测试

```bash
# BDD 回归
bash bdd/bdd-1001-1060-p0-regression.sh      # Phase 1 P0 (17)
bash bdd/bdd-1065-1100-p1-regression.sh      # Phase 1 P1 (26)
bash bdd/bdd-1101-1110-phase2.sh             # Phase 2 (9)
bash bdd/bdd-1211-1220-phase4.sh             # Phase 4 (11)

# PG 端 in-process 验证
.venv/bin/python /tmp/test_pg_direct.py      # 14
.venv/bin/python /tmp/test_phase2_pg.py      # 10
.venv/bin/python /tmp/test_phase4_pg.py      # 6
```

## 状态

| 指标 | 数值 |
|------|------|
| BDD | 1131 |
| TDD | 19 |
| FIX | 92 |
| verify 规则 | 31 |
| 监控端点 | 9 |
| 部署文档 | 1 份 (15 节) |

## 不做什么

- ❌ 不开源 / 不发 SDK
- ❌ 不输出 UI (Vue3 / Element Plus / 流程设计器)
- ❌ 不建第三方流程市场 / 插件生态
- ✅ 持续为 AI Agent + 人机协同提供工作流引擎
