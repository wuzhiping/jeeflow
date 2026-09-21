# BDD 全面回归最终报告

## 1. 流程覆盖

| 来源 | 总数 | PASS | FAIL | 通过率 |
|------|------|------|------|--------|
| flows/ (标准样例) | 16 | 14 | 2 | 87.5% |
| bdd/ (历史测试) | 68 | 62 | 6 | 91.2% |
| **合计** | **84** | **76** | **8** | **90.5%** |

## 2. vendor/jeeflow 改进（22 个 FIX）

| ID | 范围 | 摘要 |
|----|------|------|
| FIX-T6 | facade.submitType=5 | RE_APPLY 重新申请流程 |
| FIX-T7 | facade.processDesignHis | 设计历史双端兼容 |
| FIX-T8 | builtin.TaskRoleAssigneeHandler | roleCode 字段 |
| FIX-T9 | model.ownerId + repo | 业务归属字段贯穿 |
| FIX-T10 | facade._startAndExecute | business variables 嵌套解包 |
| FIX-T11 | repo.stats_avg_dur | timedelta 自动秒数 |
| FIX-T12 | repo.stats_task_aggregate | perform_type 字面量 |
| FIX-T13 | model.surrogate.enabled | bool 兜底（PG） |
| FIX-T14 | model.design.isDeployed | bool 兜底（PG） |
| FIX-T15 | ext._build_ext_where | BOOLEAN 列自动 bool |
| FIX-T16 | repo.save_task/instance | str 兜底 |
| FIX-T17 | engine.empty_actors | raise + ABANDON |
| FIX-T18 | engine._add_auto_gen_title | title 优先级 |
| FIX-T19 | facade.flow | 异常类型前缀 |
| FIX-T20 | ext._build_ext_where | NE/GT/GE/LT/LE/NIN |
| FIX-T21 | facade._stats_group | state label 映射 |
| FIX-T22 | engine._execute_node | 未知节点类型 raise |
| FIX-T23 | memory+ext IN/NIN | 字符串逗号分隔 |
| FIX-T24 | memory.page_designs | 分页切片 |
| FIX-T25 | memory.page_surrogates | 分页切片 |
| FIX-T26 | facade._processDesignHis | 通用 m_ 过滤 |
| FIX-T27 | repo.stats_active_users | 活跃用户统计 |

## 3. 8 个 FAIL 原因分类

| 类别 | 数量 | 详情 |
|------|------|------|
| 流程设计：拦截器名未注册 | 1 | bdd-business-interceptor (POST_ONE) |
| 流程设计：FQCN 拼写错误 | 1 | bdd-multi-actor-v2 (com.jeeflow. → com.mldong.) |
| SPI 配置不完整 | 3 | FormFieldAssigneeHandler role_code 缺失 |
| 已知引擎缺陷 | 2 | 08-custom-node, 11-assignment-handler |
| 非流程文件 | 1 | statics.json（统计文件，跳过） |

## 4. 改进 docs 清单

- `docs/AGENTS.md` §7 反模式补充（FQCN 前缀、interceptor 注册、SPI role_code）
- `docs/known-issues.md` 22 个章节标记 FIX-Tn
- `tdd/regression-202609171735/` 17 份回归报告

## 5. 双后端一致性

- **8101 memory**：PASS
- **8102 PG**：PASS（ID 格式差异：雪花 vs 自增）
- 行为完全一致（除 ID 类型）

## 6. 后续

- 5 个 SPI/设计 FAIL：可在 SPI 数据包补充 role_code 或修订 FQCN
- 2 个已知引擎缺陷：custom 节点未实现、custom 节点 FIX-T17 改进 raise
- 建议：vendor/jeeflow/ 改进完成度高，进入生产稳定阶段
