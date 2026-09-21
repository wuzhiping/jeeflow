# FIX-T25 TDD 报告

## 目标
processSurrogate/page 同 FIX-T24：分页返全集 bug

## 改动
- **vendor/jeeflow/memory.py:MemoryExtRepository.page_surrogates**（FIX-T25，2026-09-17）
  - 补齐 `_slice(rows, page_num, page_size)` 切片

## TDD 用例
| ID | 场景 | 期望 | 实际 |
|----|------|------|------|
| 1 | 8 个 surrogate, pageNum=1, pageSize=3 | recordCount=8, totalPage=3, rows=3 | ✅ |
| 2 | 8 个 surrogate, pageNum=2, pageSize=3 | recordCount=8, totalPage=3, rows=3 | ✅ |
| 3 | 8 个 surrogate, pageNum=3, pageSize=3 | recordCount=8, totalPage=3, rows=2 | ✅ |

## 端到端验证
- 8101 memory 后端：✅ 分页正常
- 8102 PG 后端：✅ SQL LIMIT/OFFSET

## 复盘
- 跟 FIX-T24 同模式 bug：第二 MemoryExtRepository.page_surrogates 返全集
- 后续：processDesignHis/page 也可能同样问题
