# 12-candidate-page 测试日志

**日期**：2026-09-17 11:00
**测试文件**：`./flows/12-candidate-page.json`
**结论**：✅ **PASS**（流程完整通过；candidateUsers/candidateGroups 用于 candidatePage 接口，不影响 actor 解析）

---

## 1. 流程结构（4 节点 / 3 边）

```
start → apply(applicant) → review(assignee=leader, candidateUsers=userA,userB, candidateGroups=finance) → end
```

## 2. 关键字段语义

| 字段 | 用途 | 实测影响 |
|---|---|---|
| `assignee=leader` | task 创建时的 actor | actorIds=['leader'] |
| `candidateUsers=userA,userB` | candidatePage 接口候选 | 仅出现在 processTask/candidatePage 响应 |
| `candidateGroups=finance` | candidatePage 接口按角色查 SPI | SPI 无 "finance" role，无效果 |

## 3. 引擎处理路径

`engine.py:377-413` `_create_task`：
- 仅读 `properties.assignee` / `properties.assignmentHandler` 解析 actors
- **不读** `properties.candidateUsers` / `properties.candidateGroups`
- 这些字段在 task 创建时被忽略

`facade.py:938-970` `_processTask_candidatePage`：
- 读 `node.properties.candidateUsers`（逗号分隔）
- 读 `node.properties.candidateGroups`（逗号分隔，按 roleCode 查 SPI_ROLE_TO_USERS）
- 合并后返回候选用户列表

**结论**：`candidateUsers` / `candidateGroups` 是**前端转交/委派时选人用**，不影响 task actor。

## 4. 测试详情

### 4.1 启动 + 流程跑通

```
state=10 activeTasks=1
apply    → user1     DONE
review   → DOING     actorIds=['leader']
```

### 4.2 candidatePage 实测

```bash
curl -X POST /wf/processTask/candidatePage -d '{"processTaskId":"...","pageNum":1,"pageSize":20}'
```

返回 8 条候选用户（**包含 userA、userB**）：
- 来自 candidateUsers 解析
- userA: 孙俪, userB: 周明 等
- candidateGroups="finance" SPI 无此 role，无额外结果

### 4.3 review leader agree → state=20

```
review  → leader  DONE
state=20  activeTasks=0
```

## 5. 关键发现

### 5.1 candidateUsers / candidateGroups 双重角色

| 接口 | 是否读这两个字段 |
|---|---|
| processTask/execute / detail | ❌ 不读 |
| processTask/todoList | ❌ 不读 |
| **processTask/candidatePage** | ✅ 读 |

### 5.2 actor 解析优先级

`_resolve_actors` 顺序（engine.py:415-451）：

```python
1. KEY_NEXT_NODE_OPERATOR (vars_["tf_nextNodeOperator"])
2. properties.assignee (逗号分隔)
3. properties.assignmentHandler (FQCN 注册)
4. ext.assignment_handler (legacy)
```

`candidateUsers` 不在以上任一路径，**不参与 actor 解析**。

### 5.3 candidateGroups 依赖 SPI 数据

`facade.py:983-993`：
```python
g = (node.get("properties") or {}).get("candidateGroups", "")
if g and self._org_prov is not None:
    for rc in str(g).split(","):
        ids = await self._org_prov.find_by_role(rc) or []
```

当前 SPI `DEMO_ROLE_TO_USERS.json`：`leader/manager/director/boss`，**没有 "finance"**。

`candidateGroups="finance"` → find_by_role("finance") → [] → 静默无结果。

**fallback**：如果 model candidates 为空，candidatePage 调 `self._user_search(args)` 返回全用户（SPI user_search 钩子）。

## 6. 文档同步

- `docs/flow.md §3.3`：candidateUsers/candidateGroups 已说明用途（候选分页）
- `docs/AGENTS.md §4` 自检表 12 行：候选人分页 ✅
- `docs/known-issues.md §19` 新增：candidateGroups="finance" SPI 缺失，静默无效果

## 7. 结论

| 项 | 状态 |
|---|---|
| 流程部署 | ✅ |
| 启动实例 | ✅ |
| actor 解析（assignee=leader） | ✅ actorIds=['leader'] |
| candidatePage 返回候选 | ✅ 8 条含 userA/userB |
| candidateGroups 角色扩展 | ❌ SPI 无 "finance" role |
| 流程完整跑通 | ✅ state=20 DONE |

**整体**：✅ PASS（流程正常，candidate 字段按预期工作）

## 8. 服务

PID 3365271 在 8101 运行中，healthz UP。
