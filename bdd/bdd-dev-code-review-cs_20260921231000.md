# BDD-DEV-008 dev-code-review-cs (20260921231000)

## 流程设计

```mermaid
flowchart LR
    start([开始]) --> apply[提交 PR]
    apply --> reviewers[三人会签<br/>u_fe_lead+u_be_lead+u_arch<br/>PARALLEL 全员通过]
    reviewers --> merge[合并 PR<br/>u_cto]
    merge --> end([结束])
```

## 场景

代码评审 - 并行会签（全员通过）。3 个评审人同时审，全部 approve 后 CTO 合并。

## 用到的能力

- `performType=1` + `countersignType=PARALLEL` 并行会签
- `assignee="u_fe_lead,u_be_lead,u_arch"` 字面量多 actor
- `field.candidateUsers` 候选人过滤

## 关键观察

- 3 个 task 并行创建，actorId 各异
- 全部 submitType=1 (AGREE) 通过 → 流转到 merge 节点
- 不同于 ratio countersign (2/3)，此处要求**全员通过**才流转

## 校验

| 项 | 期望 | 实际 | 结果 |
|---|---|---|---|
| 3 个 reviewer 并行 active | reviewers.members=3 | 3 | ✅ |
| 全员 approve 后流转 | merge 待办 = u_cto | u_cto | ✅ |
| approvalRecord reviewers 出现 3 次 | 3 (3 actor) | 3 | ✅ |
| `state` | 20 (DONE) | 20 | ✅ |

## 结果

- memory (8101): ✅ **PASS**（并行会签全员通过）
- pg (8102): skipped