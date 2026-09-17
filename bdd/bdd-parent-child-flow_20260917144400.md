# BDD Task 40: 父子流程 parentId（部分 PASS + 已知问题）

- **时间**：2026-09-17 14:44:00（TS=20260917144400）
- **JSON 定义**：`./bdd/bdd-parent-child-flow_20260917144400.json`
- **服务**：main.py（PID 3446706）

## 1. 场景设计

启动 2 个实例，子实例通过 `parentId` 字段关联到父实例。

## 2. 测试结果

| 实例 | parentId 参数 | 实际 parentId |
|---|---|---|
| parent | 无 | None ✅ |
| child | $PARENT_INST | **None** ❌ |

子实例流程可正常流转（state=20），但 `parentId` 字段未关联。

## 3. 关键发现（已知问题 §56）

1. **startAndExecute parentId 参数**：Python 引擎 facade 未读取该参数
2. **`ProcessInstance.parentId` 字段**：模型支持，但启动路径未注入
3. **Java boot2 行为**：支持子流程参数 `parentId`
4. **Python 引擎当前**：parentId 参数被忽略，子实例 parentId=None

## 4. 文档改进

- docs/known-issues.md §56 新增：Python 引擎 startAndExecute parentId 参数未生效

## 5. 修复建议

修改 `facade.py:startAndExecute` 入参解析增加 `parentId` 字段：

```python
parent_id = args.get("parentId")
# 注入到 inst.parentId
inst.parentId = parent_id
```

（不在本会话修复 — 用户规则限制 main.py 修改建议）
