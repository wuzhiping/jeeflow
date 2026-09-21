# BDD #127 复合 decision 表达式边界 (20260919 150000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[申请]
    apply --> decision1{决策}
    decision1 -->|#amount > 10000||#amount>5000 && #urgent==1| high_review[高额]
    decision1 -->|#urgent==1 && #amount <= 5000| emergency_review[紧急]
    decision1 -->|#amount > 0| low_review[低额]
    high_review --> end([结束])
    emergency_review --> end
    low_review --> end
```

## 场景
测试 FIX-T37 (ast 解析器) 在嵌套优先级 (`||` `&&` `()`)、OGNL 风格 (`#var`)、
字符串/数字混合等场景下的行为。

## 用例
| Case | amount | urgent | 期望节点 | 实测节点 | 结果 |
|------|--------|--------|----------|----------|------|
| 1 | 15000 | 0 | high_review | high_review | ✅ |
| 2 | 4000 | 1 | emergency_review | emergency_review | ✅ |
| 3 | 6000 | 1 | high_review | high_review | ✅ |
| 4 | 2000 | 0 | low_review | low_review | ✅ |

## 决策表达式
- e2: `#amount > 10000 || (#amount > 5000 && #urgent == 1)` — 嵌套优先级
- e3: `#urgent == 1 && #amount <= 5000` — 复合 and
- e4: `#amount > 0` — 单 key

## 结果
- memory (8101): ✅ 4/4 PASS
- pg (8102): ⏭️ 暂未跑（PG 服务未起）

## 发现
- ✅ 嵌套 `||` + `&&` + 括号正确求值（FIX-T37 工作正常）
- ✅ 决策 expr 可用 OGNL `#var` 风格
- ✅ 决策出边按顺序评估，首个真值即流转（case 3: 6000 urgent=1 → e2 true 先命中）
- ✅ fallback 行为：e2 False → e3 False → e4 True（兜底）
