# BDD-DEV-011 dev-candidate-page (20260921231000)

## 流程设计

```mermaid
flowchart LR
    start([开始]) --> apply[提交任务]
    apply --> delegate_pick[委派选人<br/>u_rd_dir]
    delegate_pick --> executor[被委派人执行<br/>candidateUsers: 5 人<br/>candidateGroups: engineer+senior_engineer]
    executor --> end([结束])
```

## 场景

任务委派 - 候选人分页。`delegate_pick` 完成时调用 candidatePage API 查 `executor` 节点的候选人列表。

## 用到的能力

- task 节点 `candidateUsers/candidateGroups` 在 `properties` 根声明（FIX: 也能放 `field`）
- `processTask/candidatePage` API（行为：查当前任务**后继** task/custom 节点的候选人）
- candidateGroups 按 SPI 角色自动展开为用户列表（v1.6.0 §FIX）

## 执行脚本

```bash
# 1. 取当前任务 id
T1=$(curl ... todoList -d '{"operator":"u_rd_dir"}' | jq -r .data.rows[0].id)

# 2. candidatePage: 查 delegate_pick 后继 (executor) 的候选
curl -X POST http://127.0.0.1:8101/wf/processTask/candidatePage \
  -d "{\"processTaskId\":\"$T1\",\"pageNum\":1,\"pageSize\":20}"

# 返回示例（去重后共 6 个用户）:
# {
#   "data": {
#     "pageNum": 1, "pageSize": 20,
#     "recordCount": 6,        # ← 注意: 是 recordCount, 不是 total
#     "totalPage": 1,
#     "rows": [6 个 {id, userId, realName} dict]
#   }
# }

# 3. 完成 delegate_pick → executor 流转 → 完成
```

## 校验

| 项 | 期望 | 实际 | 结果 |
|---|---|---|---|
| candidatePage 返回 recordCount | 6 (5 candidates + 1 group extra) | 6 | ✅ |
| candidateUsers 来源 | u_be_eng, u_fe_eng, u_qa_eng, u_be_senior1, u_fe_senior | ✅ 5 | ✅ |
| candidateGroups 展开 (senior_engineer) | + u_be_senior2 (去重 6) | ✅ | ✅ |
| 流程最终 state | 20 (DONE) | 20 | ✅ |

## BUG 发现（误报 → 文档说明）

### ~~BUG-4 candidatePage 响应缺 total 字段~~
- **实际情况**: candidatePage 返回**五键分页格式**（`recordCount/totalPage/pageNum/pageSize/rows`），对齐 mldong Java/Go 分页约定（`facade.py:1715-1728`）。这是约定，**不是 bug**。
- **文档位置**: `docs/known-issues.md:2387` (BDD #140 记录过)
- **教训**: 前端若按 `.total` 取会拿到 null（jq 显示），应按 `.recordCount` 取

## 结果

- memory (8101): ✅ **PASS**（候选人分页 API + 角色展开）
- pg (8102): skipped