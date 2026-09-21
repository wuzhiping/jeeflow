# BDD Regression Test: 03-decision-expr

- **流程**：`./flows/03-decision-expr.json`（金额决策）
- **服务**：8101 + 8102
- **结果**：✅ PASS（amount 未传，走 fallback 第一条 → task2 manager）
- **改进**：runner 应支持传 amount 验证 expr 行为
- **文档改进**：v1.6.0 FIX-T3 支持字符串 expr；SimpleExprEvaluator 在 main.py:54
