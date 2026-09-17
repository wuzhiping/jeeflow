# BDD Task 46: 节点 id 重复边界测试（已知行为）

- **时间**：2026-09-17 14:56:00（TS=20260917145600）
- **JSON 定义**：`./bdd/bdd-duplicate-node-id_20260917145600.json`
- **服务**：main.py（PID 3450059）

## 1. 场景设计

两个节点都用 `id='apply'`（重复）：
- node[1].id='apply' (apply 节点)
- node[2].id='apply' (重复 id)

## 2. 测试结果

| 步骤 | 结果 |
|---|---|
| save | ✅ 成功 |
| deploy | ✅ 成功 |
| startAndExecute | ✅ 启动 |
| state | **20** (直接结束) |

重复 id 的 JSON 部署后，引擎行为不可预期：实例直接 state=20（结束），没有创建 task。

## 3. 关键发现（§58）

1. **节点 id 重复**：save/deploy 不报错（仅 schema 验证）
2. **引擎行为**：实例直接结束（state=20），无 task 创建
3. **重复 id 后 _find_node 行为**：取第一个匹配（字典序）
4. **JSON save 不验证**：重复 id 不阻止部署
5. **启动时 _execute_node**：从 start 流转，遇到重复节点时退化
6. **AGENTS.md §3.3 命名约束**：禁止重复 id（Java 端兼容性），但 Python 引擎未强制

## 4. 引擎行为

`_find_node` 在重复 id 时行为：
```python
# engine.py:_find_node - 字典序第一个匹配
return next((n for n in flow.nodes if n.id == node_id), None)
```

启动 start → apply (apply_task_node) → 边 e1 指向 end (因为 apply 重复 id 可能解析为第二个 node 而跳过 review)。

## 5. 文档改进

- docs/known-issues.md §58 新增：节点 id 重复边界
- docs/flow.md §3 增强：节点 id 唯一性约束

## 6. 测试报告
