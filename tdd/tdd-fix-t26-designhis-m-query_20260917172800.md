# FIX-T26 TDD 报告

## 目标
designHis/page 支持通用 m_ 条件（m_EQ_createUser / m_LIKE_content）

## 改动
- **vendor/jeeflow/facade.py:_processDesignHis_page**（FIX-T26，2026-09-17）
  - 新增 `_filter_rows_by_m_query` 后置过滤（白名单：t.id/t.process_design_id/t.content/t.create_time/t.create_user）
- **vendor/jeeflow/facade.py:_filter_rows_by_m_query**（新增）
  - 通用 m_ 条件对累积行过滤（EQ/NE/LIKE/LLIKE/RLIKE）

## TDD 用例
| ID | 场景 | 期望 | 实际 |
|----|------|------|------|
| 1 | designHis/page 无过滤 | recordCount=3 | ✅ |
| 2 | designHis/page m_EQ_createUser=user1 | recordCount=3（默认 operator） | ✅ |
| 3 | designHis/page m_EQ_createUser=ghost | recordCount=0 | ✅ |
| 4 | designHis/page m_LIKE_content=apply | recordCount=3（内容都含 apply） | ✅ |

## 端到端验证
- 8101 memory 后端：✅
- 8102 PG 后端：✅（PG 设计历史已用 SQL 过滤，memory 累积路径补充）

## 复盘
- facade 累积读 list_design_his 走 in-memory 过滤
- 之前只能 filter designId；现在可过滤 content/createUser
- 后续：PG list_design_his 累积可下沉到 SQL 一次过滤
