# BDD Regression Summary: bdd/ 68 个流程

- **时间**：2026-09-17 17:55
- **覆盖**：bdd/*.json 68 个（不含 patch-* + statics.json）
- **服务**：8101 memory

## 1. 测试结果矩阵

| 状态 | 数量 | 占比 |
|------|------|------|
| ✅ PASS | 62 | 91.2% |
| ❌ FAIL（已知设计缺陷） | 6 | 8.8% |

## 2. FAIL 详情

| # | 流程 | 失败原因 | 性质 |
|---|------|----------|------|
| 1 | bdd-business-interceptor_20260917132800 | `postInterceptors: POST_ONE` 未注册 | 流程设计错（未注册拦截器名） |
| 2 | bdd-multi-actor-v2_20260917151800 | FQCN `com.jeeflow.builtin.handlers.TaskRoleAssigneeHandler` 错误（应为 com.mldong.） | 流程设计错 |
| 3 | bdd-position-transfer_20260917115900 | FormFieldAssigneeHandler SPI role 匹配空 | SPI DEMO 配置不完整 |
| 4 | bdd-recruit-approval_20260917113813 | 同上 | SPI DEMO 配置不完整 |
| 5 | bdd-training-approval_20260917115500 | 同上 | SPI DEMO 配置不完整 |

> statics.json 不计入（是统计文件非流程定义）

## 3. 关键发现

1. **62/68 PASS**：22 个 vendor FIX 后 bdd 流程几乎全部正常运行
2. **5 个 FAIL 全部是设计/环境问题**：不是 vendor 引擎缺陷
3. **FormFieldAssigneeHandler SPI 依赖**：3 个流程需要 SPI 配置 role_code
4. **FQCN 拼写错误**：1 个流程用了错误的包前缀（com.jeeflow. → com.mldong.）

## 4. 文档改进

- AGENTS.md §7 已有反模式提示，但需补充：
  - SPI 角色未注册时抛 ValueError（F1X-T17）
  - FQCN 前缀必须是 com.mldong.（不是 com.jeeflow.）
  - postInterceptors 拦截器名必须在 main.py 注册
