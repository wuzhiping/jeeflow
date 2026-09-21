# FB-0009 补丁索引 (FIX-DOC-3)

> **FB**: FB-0009 (processTask/delegate 字段名错位)
> **修复编号**: FIX-DOC-3
> **来源**: flowuser 委托测试 (2026-09-21, 实例 #1 = 92111791451232)
> **目的**: 让 bro 一次性 review + apply, 闭环 FB-0009
> **执行人**: bro (按 `FREEZE.md §6` 例外条款, FB-0009 关联的文档修订)

---

## 1. 修订范围

3 个文件, 3 处变更:

| # | 文件 | 章节 | 变更类型 |
|---|------|------|----------|
| 1 | `docs/flow.md` | §5.3 (新增 §5.3.1 委托代理 - task 级) | **改 + 增** |
| 2 | `docs/actions.md` | §3 (processTask/delegate 完整字段表) | **改** |
| 3 | `docs/known-issues.md` | §114 (新增) | **增** |

---

## 2. 补丁文件清单

| 文件 | 内容 |
|------|------|
| `flow.md.patch.md` | docs/flow.md §5.3 修订方案 (新增 §5.3.1 task 级委托) |
| `actions.md.patch.md` | docs/actions.md §3 修订方案 (processTask/delegate 完整字段) |
| `known-issues-§114.md` | docs/known-issues.md §114 全文 (新增) |
| `README.md` | 补丁索引 (本文件) |

---

## 3. 核心改进 (一句话)

**文档应明确**: `processTask/delegate` API 字段名是 **`targetUserId`** (不是 `assignee`), 这个错位导致用户首次调用报 `[ValueError] targetUserId 缺失`.

---

## 4. 委托 API 完整字段表 (文档应明确)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `processTaskId` | string | 是 | 当前任务 ID (雪花 ID, 字符串) |
| `operator` | string | 是 | 委托人 userId (实际操作人, 必须在 actorIds 里) |
| `targetUserId` | string | 是 | 受托人 userId (**注意: 不是 `assignee`**) |
| `comment` | string | 否 | 委托备注 |

---

## 5. 申请流程 (给 bro)

```
1. bro review 三个 patch 文件
2. 如同意, 直接 apply 到 docs/ (按 FREEZE.md §6 例外条款, FB-0009 关联)
3. 跑 sla/check.sh 验证 (docs 章节应通过)
4. 通知 flowuser 闭环
5. 更新 FB-0009 status=closed + lessons_learned
6. 同步更新 README.md / weekly / metrics
```

---

## 6. 涉及文件位置

- `skills/feedback/attachments/FB-0009-patches/flow.md.patch.md`
- `skills/feedback/attachments/FB-0009-patches/actions.md.patch.md`
- `skills/feedback/attachments/FB-0009-patches/known-issues-§114.md`

⏱️ Last updated: 2026-09-21 · 周末起草, 等 bro apply
