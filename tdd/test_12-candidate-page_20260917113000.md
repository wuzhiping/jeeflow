# 12-candidate-page 回归测试（SPI 修复后）

- **测试时间**：2026-09-17 11:30:00
- **测试类型**：回归（修复后）
- **关联流程**：`./flows/12-candidate-page.json`
- **关联已知问题**：`./docs/known-issues.md §19`
- **前置报告**：`./tdd/test_12-candidate-page_20260917110000.md` ⚠️ PARTIAL

## 目标

复盘 §19：补齐 SPI demo 数据（`finance` role）后重测，确认 `candidatePage` 在 apply 节点能正确合并 `candidateUsers + candidateGroups` 候选。

## 修复

### `./spi/demo/DEMO_ROLES.json`

```diff
  "leader": "组长",
  "manager": "经理",
  "director": "总监",
+ "finance": "财务部"
```

### `./spi/demo/DEMO_ROLE_TO_USERS.json`

```diff
  "leader": ["leader"],
  "manager": ["manager"],
  "director": ["director"],
  "boss": ["boss"],
+ "finance": ["leader", "manager"]
```

## 验证步骤

### 1. 部署流程

`processDefineId=14`（复用前次 deploy 定义，name=candidate-flow）

### 2. 启动实例

```bash
curl -s -X POST http://localhost:8101/wf/processDefine/startAndExecute \
  -H "Content-Type: application/json" \
  -d '{
    "processDefineId": 14,
    "assignees": "user1",
    "operator": "user1",
    "variables": {"u_userId":"user1","u_deptId":"D01"},
    "title": "12-finance-fixed"
  }'
```

→ `processInstanceId=91763219392613`

### 3. candidatePage 在 apply 节点（向后查 review 节点 candidates）

```bash
curl -s -X POST http://localhost:8101/wf/processTask/candidatePage \
  -H "Content-Type: application/json" \
  -d '{"processTaskId": <apply_task_id>, "pageNum": 1, "pageSize": 20}'
```

**响应**：

```json
{
  "data": {
    "recordCount": 4,
    "rows": [
      {"userId": "userA"},
      {"userId": "userB"},
      {"userId": "leader"},
      {"userId": "manager"}
    ]
  }
}
```

### 4. 候选来源解析

| 来源 | 路径 | 解析结果 |
|---|---|---|
| `candidateUsers="userA,userB"` | review.properties | [userA, userB] |
| `candidateGroups="finance"` → `find_by_role("finance")` | facade.py:983-993 + org_prov | [leader, manager] |
| 合并去重 | | [userA, userB, leader, manager] ✅ |

### 5. candidatePage 在 review 节点（向后查 end 节点，无 task）

```bash
curl -s -X POST http://localhost:8101/wf/processTask/candidatePage \
  -H "Content-Type: application/json" \
  -d '{"processTaskId": <review_task_id>, "pageNum": 1, "pageSize": 20}'
```

**响应**：

```json
{
  "data": {
    "recordCount": 8,
    "rows": [user1, userA, userB, userC, leader, manager, director, boss]
  }
}
```

→ **fallback 现象**：candidatePage 在 review task 调用时向后查到的下一个 task 节点是 `end`（非 task 类型）→ `_next_task_candidates` 返回空 → 引擎 fallback 到 `self._user_search(args)`（facade.py:963-969）→ SPI user_search 返回全 8 用户。

### 6. 流程正常推进

review task by leader → state=20 DONE ✅

## 关键发现

### candidatePage 语义澄清

`processTask/candidatePage` 在 `processTaskId=T` 时调用，引擎查的是 **T 节点之后**的 task 节点（经 fork/join/decision 透传）的 `candidateUsers + candidateGroups`，用于：
- 当前 task 的 assignee 候选/抢办
- 代办补选人

因此：
- ✅ apply task 调用 → 查到 review 节点 candidates
- ⚠️ review task 调用 → review 后只有 end 节点（不是 task）→ 返回空 → fallback

### engine fallback 行为

`_next_task_candidates` 返回空时，facade 不报错，直接 fallback `user_search`。**静默行为**，可能掩盖 candidateUsers/candidateGroups 配置错误。建议引擎层在 fallback 时记录 warning（log）。

### 修复后 SPI 解析

`candidateGroups="finance"` → `find_by_role("finance")` → 返回 `[leader, manager]` ✅
合并 `candidateUsers + candidateGroups` 共 4 个用户，无重复。

## 结论

✅ **PASS** — candidatePage 在 apply 节点正确返回 4 个候选人 [userA, userB, leader, manager]，合并 candidateUsers 与 candidateGroups 行为符合设计。

## 关联变更

- `./spi/demo/DEMO_ROLES.json` +1
- `./spi/demo/DEMO_ROLE_TO_USERS.json` +1
- `./docs/known-issues.md §19` 标"已修复"
- `./flows/README.md` 12 行状态更新
