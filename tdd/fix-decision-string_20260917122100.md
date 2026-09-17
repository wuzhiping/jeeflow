# FIX-T1: decision expr 字符串值比较修复测试报告

- **测试时间**：2026-09-17 14:21:00（TS=20260917122100）
- **修复对象**：错误 1 — decision expr 字符串值比较
- **JSON 定义**：`./tdd/fix-decision-string_20260917122100.json`
- **状态**：✅ 修复完成（v1.5.1 main.py SimpleExprEvaluator 加 try/except）

## 1. 测试设计

3 个数字编码 case + 1 个字符串值边界 case：

| 测试 | f_category 值 | 期望分支 | 实际分支（修复前） | 结果 |
|---|---|---|---|---|
| 1 数字=1 | 1 | branch_travel | branch_travel (leader) | ✅ |
| 2 数字=2 | 2 | branch_office | branch_office (manager) | ✅ |
| 3 数字=3 | 3 | branch_other | branch_other (director) | ✅ |
| 4 字符串 | "travel" | 兜底首边 | **startAndExecute 抛错 99999999** | ⚠ 修复 |

## 2. 关键发现

SimpleExprEvaluator 有 2 种异常路径：
1. **expr 用字符串** → regex 不匹配 → 返回 False → 走首边
2. **expr 数字 + value 字符串** → regex 匹配 → float() 抛错 → 整个流程失败

## 3. 修复（v1.5.1，FIX-T1）

`main.py:54` SimpleExprEvaluator 增加 try/except：
```python
try:
    actual = float(actual)
except (ValueError, TypeError):
    return False  # 与 regex 不匹配、value 为 None 行为一致：走兜底首边
```

## 4. 验证

### 4.1 本地 Python 验证（修复前）
- 数字 1: True ✓
- 数字 2: True ✓
- 字符串 travel: **ValueError 抛出** ✗
- 字符串 expr (f_category==travel): False ✓（regex 不匹配）

### 4.2 本地 Python 验证（修复后 v1.5.1）
- 数字 1: True ✓
- 数字 2: True ✓
- 字符串 travel: False ✓（**修复后不抛错**）
- 字符串 expr (f_category==travel): False ✓

### 4.3 端到端验证（uvicorn --reload 重启后）

| 测试 | f_category | 期望分支 | 实际分支 | 结果 |
|---|---|---|---|---|
| 1 | 1 | branch_travel | branch_travel (leader) | ✅ |
| 2 | 2 | branch_office | branch_office (manager) | ✅ |
| 3 | 3 | branch_other | branch_other (director) | ✅ |
| 4 修复 | "travel" | 兜底首边 | branch_travel (leader) | ✅ 修复 |

服务启动命令：`uvicorn main:app --host 0.0.0.0 --port 8101 --reload`，PID 3413887

## 5. 部署要点

修复涉及 main.py 修改（已授权范围内），通过 uvicorn --reload 自动加载，无需重启服务。后续修改 main.py 自动 reload。

## 5. 关联

- `./bdd/bdd-expense-by-category_20260917115100.md` Task 7（首次发现此错误模式）
- `./bdd/fix-20260917122008.md` 错误 1（已更新 2 种异常路径）
- `./docs/known-issues.md §28` FIX-T1 已修复记录
- `./docs/flow.md §3.4` decision 节点属性（待补充"expr + value 类型须一致（数字）"约束）
