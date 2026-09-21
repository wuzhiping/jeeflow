# BDD 任务 #112: 决策节点所有 expr 都为空

## 目标
验证 decision 节点 3 条出边 expr 全为空时的行为

## 流程
apply → dec1 → [path_a(空) | path_b(空) | path_c(空)] → end

## 实测
- 启动后 state=10 (DOING)
- leader 看到 path_a (兜底第一条)

## 结论
✅ **PASS**：决策 expr 全空时按 §33 走第一条出边 path_a

## 设计要点
- 决策节点至少需要 1 条 expr="" 出边作为兜底
- 引擎 `_evaluate_decision` 按 edges 顺序评估，首个 true 即流转
- 全 False 时按文档"fallback 到第一条无 expr 边"
