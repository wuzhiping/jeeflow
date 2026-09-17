# BDD Task 48: business 业务流 + 拦截器（PASS）

- **时间**：2026-09-17 15:00:00（TS=20260917150000）
- **JSON 定义**：`./bdd/bdd-business-interceptor_20260917150000.json`
- **服务**：main.py（PID 3453209）

## 1. 场景设计

```mermaid
flowchart LR
    A([开始]) --> B[apply]
    B --> C[audit_review boss]
    C --> D([结束])
```

`type=business` + `postInterceptors=com.example.MockAuditInterceptor`

## 2. 测试结果

| 步骤 | 结果 |
|---|---|
| save | OK（postInterceptors 已存） |
| deploy | OK |
| startAndExecute | inst=91778423649471 |
| audit_review.execute (boss) | OK → state=20 |

### 拦截器日志

```
POST com.example.MockAuditInterceptor node=apply inst=91778423649471 state=10
POST com.example.MockAuditInterceptor node=audit_review inst=91778423649471 state=10
PRE  com.example.MockAuditInterceptor node=end inst=91778423649471
POST com.example.MockAuditInterceptor node=end inst=91778423649471 state=20
```

## 3. 关键发现

1. **`type=business` 不影响业务逻辑**：仅文档分类标记
2. **拦截器 FQCN 注册生效**：每个 task 节点 enter/exit 触发 POST/PRE 拦截器
3. **拦截器抛异常会中断流程**：本次未抛，全部成功
4. **`postInterceptors` 字段必须严格匹配 FQCN**：`interceptor_registry` 找不到会 §36 抛 ValueError
