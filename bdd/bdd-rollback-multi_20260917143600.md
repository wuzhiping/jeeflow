# BDD Task 36: 驳回重审多轮（PASS）

- **时间**：2026-09-17 14:36:00（TS=20260917143600）
- **JSON 定义**：`./bdd/bdd-rollback-multi_20260917143600.json`
- **服务**：main.py（PID 3444317）

## 1. 场景设计

```mermaid
flowchart LR
    A([开始]) --> B[apply]
    B --> C[leader_review]
    C --> D[manager_review]
    D --> E[director_review]
    E --> F([结束])
```

驳回 + 重审多轮。

## 2. 测试结果

### Round 1: REJECT 终止流程

| 步骤 | 操作 | state |
|---|---|---|
| startAndExecute | user1 | 10 |
| leader agree | leader_review | 10 |
| manager REJECT (submitType=2) | manager_review | **45** |

state=45 REJECT ❌ 不可继续（§43）

### Round 2: ROLLBACK 重审

| 步骤 | 操作 | active | state |
|---|---|---|---|
| startAndExecute (new inst) | user1 | leader_review | 10 |
| leader agree | leader_review | manager_review | 10 |
| **manager ROLLBACK** (submitType=3, taskName=leader_review) | manager_review | **leader_review (manager)** | 10 |
| manager agree (re-review) | leader_review | manager_review (新) | 10 |
| manager agree | manager_review | director_review | 10 |
| director agree | director_review | 0 | **20** |

历史：`['apply', 'leader_review', 'manager_review', 'director_review', 'end']` ✅

## 3. 关键发现

1. **REJECT vs ROLLBACK**：
   - REJECT (submitType=2) → 终止流程 (state=45)
   - ROLLBACK (submitType=3) → 驳回到任意已处理节点 (需 taskName 参数)
2. **ROLLBACK 后 actors**：驳回后由原驳回人处理被驳回节点（**重审机制**）
3. **taskName 参数**：指定驳回目标节点
4. **重审 task 新建**：每轮 ROLLBACK 创建新 task 实例
5. **rollback 后的 leader_review 由 manager 处理**：actor=['manager'] 是驳回者
6. **state=20**：所有 ROLLBACK 完成后流程正常结束

## 4. submitType 路由矩阵（完整版）

| submitType | 路由 | 参数 |
|---|---|---|
| 1=AGREE | 推进下一节点 | — |
| 2=REJECT | 终止 (state=45) | — |
| 3=ROLLBACK | 驳回任意已处理节点 | **taskName** |
| 4=JUMP | 跳到任意节点 | taskName |
| 6=ROLLBACK_TO_OPERATOR | 驳回发起人 | — |

## 5. 文档改进

- docs/known-issues.md §52 新增：ROLLBACK 重审机制（驳回人处理被驳回节点）
- docs/flow.md §3.4 增强：submitType 完整路由矩阵
