# FIX-T27 TDD 报告

## 目标
stats/overview 增加 activeUserCount（窗口内不同操作人数）

## 改动
- **vendor/jeeflow/repository/base.py:JdbcProcessRepository.stats_active_users_count**（FIX-T27，2026-09-17）
  - `SELECT COUNT(DISTINCT operator)` + 窗口过滤
- **vendor/jeeflow/memory.py:MemoryRepository.stats_active_users_count**（FIX-T27，2026-09-17）
  - 集合遍历过滤 + set 去重
- **vendor/jeeflow/facade.py:_processInstance_stats_overview**（FIX-T27，2026-09-17）
  - 返回增加 `activeUserCount` 字段

## TDD 用例
| ID | 场景 | 期望 | 实际 |
|----|------|------|------|
| 1 | 8101 memory overview | activeUserCount=8 | ✅ |
| 2 | 8102 PG overview | activeUserCount=N | ✅ |
| 3 | 窗口过滤（start/end） | 仅窗口内 user | ✅ |

## 端到端验证
- 8101 memory：✅ activeUserCount: 8
- 8102 PG：✅ JDBC SQL 生效

## 复盘
- 前端看板需要「活跃用户」指标
- 复用 stats 系列入口，无需新 API
- 后续：可加 stats_active_users_top（top 5 user 排行）
