# docs/actions.md §3 修订方案 (FIX-DOC-3)

> **当前**: line 78 行只列 processTask/delegate 名字, 无字段说明
> **修订后**: 加字段表 + cross-link 到 flow.md §5.3.1

---

## 修订 · line 78 后加注解

### 当前 (line 78)

```
| 45 | `processTask/delegate` | `_processTask_delegate` | 1602 | 任务委派 (per-task 临时) |
```

### 修订后 (在 line 78 后追加)

```
| 45 | `processTask/delegate` | `_processTask_delegate` | 1602 | 任务委派 (per-task 临时, **字段名 `targetUserId` 不是 `assignee`**, 详见 `docs/flow.md §5.3.1` + `docs/known-issues.md §114` FB-0009) |
| 46 | `processTask/delegateHistory` | `_processTask_delegateHistory` | 1647 | delegate 历史查询 (BDD #1106, FIX-T74, 详见 `docs/flow.md §5.3.1`) |
```

### 字段说明 (建议加在 §3 末尾或 §X.XX 新增章节)

```markdown
### 3.1 processTask/delegate 完整字段表 (FIX-DOC-3 · FB-0009)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `processTaskId` | string | 是 | 当前任务 ID (雪花 ID, 字符串) |
| `operator` | string | 是 | 委托人 userId (实际操作人, 必须在 actorIds 里) |
| `targetUserId` | string | 是 | **受托人 userId** (注意: 不是 `assignee`, 这是 FB-0009 文档错位的修复点) |
| `comment` | string | 否 | 委托备注 |

**错误示例** (用户首次按 `assignee` 传):
```bash
POST /wf/processTask/delegate
{"processTaskId": "...", "operator": "...", "assignee": "leader"}  # ❌ 错
→ code: 99999999
→ msg: "[ValueError] targetUserId 缺失"
```

**正确示例**:
```bash
POST /wf/processTask/delegate
{"processTaskId": "...", "operator": "...", "targetUserId": "leader"}  # ✅ 对
→ code: 0
→ data: {taskId: "...", delegated: "operator", to: "leader", actors: [operator, "leader"]}
```

详见 `docs/flow.md §5.3.1` + `docs/known-issues.md §114`。
```

---

## 修订理由

1. **当前 actions.md 字段表缺失**: 用户查 action 但不知道字段名
2. **targetUserId vs assignee 错位必须明示**: FB-0009 直接证据
3. **错误示例 + 正确示例**: 让用户对照排查
4. **指向 flow.md + known-issues.md**: 单一信息源

---

## 风险评估

- **风险**: 低
- **兼容性**: 0 影响
- **回滚**: 易

⏱️ Last updated: 2026-09-21 · FB-0009 / FIX-DOC-3
