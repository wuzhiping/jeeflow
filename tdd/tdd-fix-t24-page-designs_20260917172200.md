# FIX-T24 TDD 报告

## 目标
processDesign/page 分页返全集 bug（rows 不分页，前端分页混乱）

## 改动
- **vendor/jeeflow/memory.py:MemoryExtRepository.page_designs**（FIX-T24，2026-09-17）
  - 补齐 `_slice(rows, page_num, page_size)` 切片（之前返 (rows_all, total)，违反分页契约）

## TDD 用例
| ID | 场景 | 期望 | 实际 |
|----|------|------|------|
| 1 | 5 个 design, pageNum=1, pageSize=2 | recordCount=5, totalPage=3, rows=2 | ✅ |
| 2 | 5 个 design, pageNum=2, pageSize=2 | recordCount=5, totalPage=3, rows=2 | ✅ |
| 3 | 5 个 design, pageNum=3, pageSize=2 | recordCount=5, totalPage=3, rows=1 | ✅ |

## 端到端验证
- 8101 memory 后端：✅ 分页正常
- 8102 PG 后端：✅ JdbcProcessExtRepository 用 SQL LIMIT/OFFSET，本就正常

## 复盘
- 之前 design/page rows 总是返全集，前端表格显示所有行
- 修后 recordCount/totalPage/rows 三键对齐 mldong 分页契约
- 后续：ext_repo.page_surrogates 也应同样检查
