# BDD Task 45: 流程实例查询 + m_ 多条件过滤（已知行为）

- **时间**：2026-09-17 14:54:00（TS=20260917145400）
- **JSON 定义**：`./bdd/bdd-instance-query_20260917145400.json`
- **服务**：main.py（PID 3450059）

## 1. 场景设计

启动 3 个不同 operator 的实例，测试查询过滤。

## 2. 测试结果

| 过滤方式 | 记录数 |
|---|---|
| 全量 | 5（受 pageSize 限制） |
| `operator=user1` | 5 |
| `operator=userA` | 6 |
| `m_state=10 + operator=userA` | 6 |
| `m_state=20 + operator=userA` | 6 |
| `m_processDefineId=$PDID` | 5 |
| `m_title=t45` | 5 |

## 3. 关键发现（§57）

1. **`operator` 是硬编码过滤参数**：`page_instances(page, size, operator, conditions)`
2. **`m_state` / `m_title` 等 m_ query**：条件查询（来自 `_parse_m_query`）
3. **m_state=10 / m_state=20 都返回相同**：state=10/20/45 都是合法值，但过滤不严格
4. **m_title 不工作**：模糊匹配不生效
5. **`m_processDefineId` 有效**：按 processDefineId 过滤

## 4. 引擎实际行为

`facade.py:_processInstance_page`:
```python
operator = str(args.get("operator", "user1"))  # 必填
rows, total = await self._repo.page_instances(page_num, page_size, operator, m_query)
```

**`m_operator` 不生效**：operator 是顶层参数，不是 m_ query。

## 5. 文档改进

- docs/known-issues.md §57 新增：page operator 过滤与 m_ query 区别
- docs/flow.md §4 增强：实例查询 API 参数说明

## 6. 建议

- 测试 operator 过滤用 `operator=userA` 顶层参数
- 测试 state/processDefineId 过滤用 `m_state=10` / `m_processDefineId=$PDID`
- m_title 模糊匹配可能不生效
