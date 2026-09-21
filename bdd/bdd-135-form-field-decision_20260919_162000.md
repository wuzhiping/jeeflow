# BDD #135 表单字段 f_xxx 在 decision expr (20260919 162000)

## 流程设计
```mermaid
flowchart LR
    start([开始]) --> apply[申请<br/>f_amount=业务字段]
    apply --> dec{决策}
    dec -->|#f_amount > 10000| big[大额 boss]
    dec -->|#f_amount > 0| small[小额 leader]
    big --> end([结束])
    small --> end
```

## 场景
- decision expr 引用 `f_xxx` 业务字段（不只是普通变量）
- `f_amount` 是表单字段，存在 inst.variables["f_amount"]

## 测试结果

| Case | f_amount | 期望 | 实测 | 结论 |
|------|----------|------|------|------|
| 1 | 15000 | big | big | ✅ |
| 2 | 500 | small | small | ✅ |
| 3 | 11000 | big | big | ✅ |

## 观察
- `#f_xxx` 在 expr 中可正确解析（FIX-T37 ast 替换 regex 支持 OGNL 风格）
- 业务字段存储在 `inst.variables["f_amount"]` 即可被 decision 读到
- 实际机制：ast 解析时 `#f_amount` → `f_amount` 变量名（去掉 #），然后从 vars dict 读

## 结果
- memory (8101): ✅ 3/3 PASS
- pg (8102): ⏭️ 暂未跑
