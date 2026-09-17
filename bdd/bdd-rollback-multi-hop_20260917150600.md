# BDD Task 51: 跨多节点 ROLLBACK（PASS）

- **时间**：2026-09-17 15:06:00（TS=20260917150600）
- **JSON 定义**：`./bdd/bdd-rollback-multi-hop_20260917150600.json`

## 1. 场景设计

```mermaid
flowchart LR
    A([开始]) --> B[apply]
    B --> C[leader]
    C --> D[manager]
    D --> E([结束])
```

manager 用 `submitType=3 + taskName=leader` ROLLBACK 到 leader

## 2. 测试结果

| 步骤 | 操作 | 状态 |
|---|---|---|
| 1 | apply AGREE | leader DOING actor=leader |
| 2 | leader AGREE | manager DOING actor=manager |
| 3 | manager ROLLBACK(3, leader) | **leader DOING actor=manager** |
| 4 | leader AGREE | manager DOING actor=manager |
| 5 | manager AGREE | state=20 |

### 历史轨迹

```
apply state=20 actors=['user1']
leader state=20 actors=['leader']    # 第 1 次
manager state=20 actors=['manager']
leader state=20 actors=['manager']   # 第 2 次（回退后）
manager state=20 actors=['manager']
```

### 关键发现

1. **ROLLBACK 在 manager→leader 之间成功**：state=10 不变
2. **回退后 task actor 继承发起 actor**：leader 第 2 次 actor=manager（而不是 leader）
3. **第 2 次走完流程**：再次 AGREE → manager → end，state=20
4. **history 累积**：每个 task 节点每次进入都产生新记录（id 不同）
5. **多次来回 ROLLBACK 不破坏流程图**：状态机支持多次回退
