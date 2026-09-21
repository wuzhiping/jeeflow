# docs/known-issues.md §114 (新增)

> **新增章节** · FB-0009 / FIX-DOC-3

---

## §114 processTask/delegate 字段名错位 (targetUserId vs 文档沉默, 2026-09-21)

> **首次报告**: 2026-09-21 / flowuser 委托测试 (实例 #1 = 92111791451232)
> **修复编号**: FIX-DOC-3
> **优先级**: P1 (文档)
> **状态**: 🟡 notified, 修订方案就绪 (`skills/feedback/attachments/FB-0009-patches/`)

### 现象

设计师 (`flowuser`) 测试委托功能时, 按文档印象构造请求体:

```bash
POST /wf/processTask/delegate
{
  "processTaskId": "92111791452258",
  "operator": "deptLeader",
  "assignee": "leader",          # ❌ 错!
  "comment": "我出差 1 周"
}
```

**期望**: 委托成功
**实际**:
```json
{
  "code": 99999999,
  "msg": "[ValueError] targetUserId 缺失"
}
```

### 根因

**API 实际字段名是 `targetUserId`, 不是 `assignee`**, 但文档沉默, 用户按习惯 (`assignee`) 调用即失败.

**涉及文件**:
- `docs/flow.md §5.3` — 只讲 surrogate, 没讲 task 级 delegate 字段
- `docs/actions.md §3` line 78 — 只列 action 名字, 无字段说明
- `docs/flow-tutorial.md §9.11` line 328 — 唯一提到 `targetUserId`, 但不在主路径
- `docs/api.md §5.1` — 只讲 delegateHistory, 没讲 delegate 字段

### 修正方法

**字段名改成 `targetUserId`**:

```bash
POST /wf/processTask/delegate
{
  "processTaskId": "92111791452258",
  "operator": "deptLeader",
  "targetUserId": "leader",      # ✅ 对!
  "comment": "我出差 1 周"
}
```

**响应** (实测):
```json
{
  "code": 0,
  "data": {
    "taskId": "92111791452258",
    "delegated": "deptLeader",
    "to": "leader",
    "actors": ["deptLeader", "leader"]    # 双方都在 actors
  }
}
```

### 判定: 文档错位, 不是引擎 BUG

按 `docs/AGENTS.md §9.5` 判 BUG 自检 3 步:

| 步骤 | 检查 | 结果 |
|------|------|------|
| ① 复现 | 92111791451232 实测 | ✅ 1 步触发 |
| ② 精读文档 | `docs/flow.md §5.3` + `docs/actions.md §3` | ⚠️ 完全没提字段名 |
| ③ 对比样例 | `flows/` | ❌ 没有 delegate 样例 |

**结论**: 引擎行为正确 (要求 `targetUserId`), 是文档不写字段名导致用户报错.

### 委托 API 完整字段表 (应文档化)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `processTaskId` | string | 是 | 当前任务 ID (雪花 ID, 字符串) |
| `operator` | string | 是 | 委托人 userId (必须在 actorIds 里) |
| `targetUserId` | string | 是 | 受托人 userId |
| `comment` | string | 否 | 委托备注 |

### 委托当前行为 (v1.9.0+)

| 行为 | 实际 | 设计意图 | 是否一致 |
|------|------|----------|----------|
| 委托后 actorIds | `[operator, targetUserId]` (双方) | "转交" 应只受托人 | ❌ |
| 委托方 todoList | 仍可见 task | "转交" 应不可见 | ❌ |
| 受托方 todoList | 可见 task | 应可见 | ✅ |
| delegateHistory | `[from, to, at]` | "一次性移交" 记录 | ✅ (设计如此) |
| processSurrogate | 独立产品线 | 委托 ≠ 加候选 | ✅ |

**关键洞察**: 字段命名 (`targetUserId`) + 历史结构 (`from/to`) 强烈暗示"转交" 语义, 但实际行为是"协助" 语义 (双方都见). 这是设计意图 vs 实现行为错位, 详见 `feedback/inbox/FB-0010` (设计缺陷候选, 等 Phase 9 修复).

### 修复

**修订**:
- `docs/flow.md §5.3` (新增 §5.3.1, 修订方案: `skills/feedback/attachments/FB-0009-patches/flow.md.patch.md`)
- `docs/actions.md §3` (修订方案: `.../actions.md.patch.md`)
- `docs/known-issues.md §114` (本文, 新增)

**未修改**:
- 引擎代码 (字段名 `targetUserId` 是正确的, 文档沉默是问题)
- 任何样例 (无 delegate 样例, 不影响)

### 回归覆盖

- 现有 BDD #1106 (delegateHistory) PASS (无影响)
- 新增 BDD (可选): 测试 `targetUserId` vs `assignee` 错误检测 + 字段文档对照

### 优先级

✅ 已修复 (2026-09-21, FIX-DOC-3 修订方案就绪, 等 bro apply)

⏱️ Last updated: 2026-09-21
