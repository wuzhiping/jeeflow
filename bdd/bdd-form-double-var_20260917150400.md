# BDD Task 50: f_xxx 与 xxx 双重变量（PASS）

- **时间**：2026-09-17 15:04:00（TS=20260917150400）
- **JSON 定义**：`./bdd/bdd-form-double-var_20260917150400.json`

## 1. 测试结果

启动传 `score=95` + `f_score=95`：

| 字段 | instance.variables | formData |
|---|---|---|
| score | 95 | 95 |
| f_score | 95 | 95 |

### 关键发现

1. **`f_xxx` 与 `xxx` 是同一份数据**：formData 解包时同时保留原始 f_ 和解包后字段
2. **`variables` 字段**同时存 `f_score` 和 `score` 两个 key
3. **任意字段都可在 decision expr 中访问**：`#score>=60` 和 `#f_score>=60` 都生效
