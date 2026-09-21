# docs/flow.md §5.3 修订方案 (FIX-DOC-3)

> **当前**: §5.3 只讲 surrogate (全局委托), 没讲 task 级 delegate
> **修订后**: 新增 §5.3.1 task 级 delegate + 字段说明 (含 targetUserId)

---

## 修订 1 · line 386 后插入 §5.3.1

### 当前 (line 386-397)

```markdown
### 5.3 委托代理（surrogate）

> ⚠️ 当前实现缺自动展开：委托关系**不影响** `processTask/todoList` 的 actor 过滤，需手动 `processTask/surrogate` addCandidate。

**API**：
- 创建委托：`/wf/processSurrogate/save` `{operator, surrogate, processName, startTime, endTime, enabled}`
- 我的委托：`/wf/processSurrogate/page` `{operator, pageNum, pageSize}`
- 委托 addCandidate：`/wf/processTask/surrogate` `{processTaskId, actorIds}`（与 `addCandidate` 等价）

**委托 ≠ 自动代办**：userA 委托给 userB 后，userB 仍需调用 surrogate addCandidate 才能在 todoList 看到 userA 的任务。

详细测试见 `./known-issues.md §82`。
```

### 修订后 (在 line 397 后插入新章节)

```markdown
### 5.3.1 任务级委托（delegate · per-task 临时）

> 🆕 FIX-T69 v1.9.0+ 新增端点. 单任务一次性转交, 不影响其他任务.

**API**: `/wf/processTask/delegate`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `processTaskId` | string | 是 | 当前任务 ID (雪花 ID, 字符串) |
| `operator` | string | 是 | 委托人 userId (实际操作人, 必须在 actorIds 里) |
| `targetUserId` | string | 是 | 受托人 userId (**注意: 不是 `assignee`**) |
| `comment` | string | 否 | 委托备注 |

> ⚠️ **FB-0009 关键提示 (2026-09-21 flowuser 反馈)**:
> - 字段名是 **`targetUserId`**, 不是 `assignee`
> - 用户首次调用按 `assignee` 传 → `[ValueError] targetUserId 缺失` (code=99999999)
> - 修正后立即生效

**当前行为 (v1.9.0+ 实测)**:
- delegate 后 `actorIds` = `[operator, targetUserId]` (双方都在 actorIds 里)
- 双方都可在 `processTask/todoList` 看到该 task
- 任何一方都可执行 `processTask/execute`
- `processTask/delegateHistory` 端点可查委托历史

**委托 ≠ 转交**:
- v1.9.0+ 当前是"协助"语义 (双方可见), 不是"移交"语义
- 详见 `docs/known-issues.md §114` + `feedback/inbox/FB-0010` (设计缺陷候选, 等 Phase 9 修复)

**示例**:
```bash
curl -X POST http://127.0.0.1:8101/wf/processTask/delegate \
  -H 'Content-Type: application/json' \
  -d '{
    "processTaskId": "92111791452258",
    "operator": "deptLeader",
    "targetUserId": "leader",
    "comment": "我出差 1 周, 请 leader 帮我审批"
  }'
```

详细测试见 `docs/known-issues.md §114`。
```

---

## 修订理由 (给 bro review)

1. **当前 §5.3 只讲 surrogate**: 没有 task 级 delegate 章节, 用户找不到
2. **字段名错位没人写**: `targetUserId` vs `assignee` 错位导致首次调用失败
3. **行为不写**: "双方都在 actorIds" 这个设计需要明确告知
4. **加 FB-0009/0010 来源**: 实证案例, 不是凭空想象

---

## 风险评估

- **风险**: 低 (仅文档新增章节)
- **兼容性**: 0 影响
- **回滚**: 易

⏱️ Last updated: 2026-09-21 · FB-0009 / FIX-DOC-3
