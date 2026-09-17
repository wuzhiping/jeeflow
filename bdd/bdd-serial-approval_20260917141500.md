# BDD Task 28: 串行多级审批 (PASS)

- **时间**：2026-09-17 14:15:00（TS=20260917141500）
- **JSON 定义**：`./bdd/bdd-serial-approval_20260917141500.json`
- **服务**：main.py（PID 3440125）

## 1. 场景设计

简单 4 级串行审批：

```mermaid
flowchart LR
    A([开始]) --> B[apply]
    B --> C[manager_review]
    C --> D[director_review]
    D --> E[boss_review]
    E --> F[notify]
    F --> G([结束])
```

## 2. 测试结果

### Case A — 全程同意

| 步骤 | 操作 | state | 当前节点 |
|---|---|---|---|
| startAndExecute | user1 发起 | 10 | manager_review |
| manager agree | manager_review | 10 | director_review |
| director agree | director_review | 10 | boss_review |
| boss agree | boss_review | 10 | notify |
| user1 agree | notify | **20** | end |

历史：`['apply', 'manager_review', 'director_review', 'boss_review', 'notify', 'end']` ✅

### Case B — 总监驳回（submitType=2）

| 步骤 | 操作 | state |
|---|---|---|
| startAndExecute | user1 发起 | 10 |
| manager agree | manager_review | 10 |
| director REJECT | director_review | **45** |

state=45 表示流程驳回结束（InstanceState.REJECT）✅

## 3. 关键发现

1. **submitType 枚举**：
   - 1=AGREE → 推进到下一节点
   - 2=REJECT → 实例 state=45 REJECT
   - 3=ROLLBACK → 驳回到任意已处理节点（需额外参数）
   - 4=JUMP → 跳到指定节点（需 taskName 参数）
   - 5=RE_APPLY → 重新提交
   - 6=ROLLBACK_TO_OPERATOR → 驳回到发起人重提
2. **state=45 REJECT**：director 驳回 → 实例直接 REJECT 状态（无 task 创建）
3. **historyNodeNames**：包含后续未访问节点（§31 已知问题）

## 4. 文档改进

- docs/known-issues.md §43 新增：submitType=2 REJECT → state=45
- docs/flow.md §3.4 增强：submitType 路由矩阵（已在前面 BDD 中记录）
