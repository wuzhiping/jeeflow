# BDD Task 33: 请假流程 + 字段权限 PERMISSION（PASS）

- **时间**：2026-09-17 14:30:00（TS=20260917143000）
- **JSON 定义**：`./bdd/bdd-leave-form-permission_20260917143000.json`
- **服务**：main.py（PID 3444317）

## 1. 场景设计

```mermaid
flowchart LR
    A([开始]) --> B[apply]
    B --> C[leader_review]
    C --> D[manager_review]
    D --> E[notify]
    E --> F([结束])
```

每个节点的 `field.PERMISSION_xxx` 字段控制字段权限（1=只读，2=隐藏）。

## 2. 测试结果

| 步骤 | 状态 |
|---|---|
| user1 申请年假 3 天 | state=10 |
| leader 审批 | state=10 |
| manager 审批 | state=10 |
| user1 确认通知 | **state=20** |

历史：`['apply', 'leader_review', 'manager_review', 'notify', 'end']` ✅

## 3. 关键发现

1. **字段权限字段命名**：`PERMISSION_<字段名>`，例如 `PERMISSION_f_days=2` 隐藏 `f_days`
2. **值含义**：
   - 1 = 只读
   - 2 = 隐藏
   - 缺省/0 = 可编辑
3. **每个 task 独立配置**：节点的 `field.PERMISSION_xxx` 仅作用于该 task
4. **apply 节点 PERMISSION_f_days=2**：发起人不能修改 days
5. **leader/manager 节点 PERMISSION_f_opinion=2**：审批意见对发起人隐藏
6. **engine 行为**：字段权限仅作为元数据透传，前端按此渲染
7. **formData 实际数据**：详情 API 返回 formData 字段（apply 任务后 formData.f_days=3）
8. **formKey 字段**：节点 properties.form 传给前端作为表单 key

## 4. 文档改进

- docs/flow.md §3.3 增强：PERMISSION 字段权限表
- docs/known-issues.md §49 新增：PERMISSION 字段是元数据，前端控制
