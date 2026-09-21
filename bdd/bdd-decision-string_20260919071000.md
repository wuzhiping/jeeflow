# BDD 任务 #108: decision 字符串比较 3-分支

## 目标
验证 SimpleExprEvaluator 字符串比较 + 3-分支决策 + 兜底默认边

## 流程
apply → dec1 → [f_type=='leave' → path_a(leader) | f_type=='reimburse' → path_b(manager) | default → path_c(director)] → end

## 实测（3 个实例）

| 实例 | f_type | 期望 task | 实测 task | 结果 |
|------|--------|-----------|-----------|------|
| 91843355030532 | leave | path_a (leader) | path_a | ✓ |
| 91843355560967 | reimburse | path_b (manager) | path_b | ✓ |
| 91843356091402 | other | path_c (director, 兜底) | path_c | ✓ |

## 结论
✅ **PASS**：字符串比较 + 3-分支决策 + 兜底默认边全部正常工作

## 设计要点
- 字符串字面量**必须双引号**：`f_type=='leave'`
- 变量必须以 `f_` 前缀（业务变量）或不带前缀（顶层变量）
- 兜底边 `expr=""` 应作为第一条或最后一条出边
- 引擎按出边顺序评估，首个 true 即流转

## 与 docs §3.4 对齐
- ✅ expr 支持 `f_type=='str'` (FIX-T3 v1.6.0)
- ✅ 兜底走第一条无 expr 边
- ✅ SimpleExpr regex 支持单/双引号字符串
