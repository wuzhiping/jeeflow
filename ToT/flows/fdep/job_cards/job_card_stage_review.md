# Job Card · stage_review

> **节点定义**：[../../fdep.json](../../fdep.json) `nodes[id=stage_review]`
> **节点手册**：[../NODES.md#stage_review](../NODES.md#stage_reviewsnaker-task)
> **Decision Mem 协议**：[../RESPONSES.md §0](../RESPONSES.md)
> **执行者**：`u_fdp_pm`
> **角色**：R6（评审） / `fdep_review` / u_fdp_pm（R3 验收留待 fork-join）
> **触发**：stage_dev 完成后 → 引擎自动加入 todoList（operator=u_fdp_pm）

---

## 1. 你的身份

```yaml
- node: stage_review
- type: snaker:task
- assignee: u_fdp_pm
- stage: 4. 评审 / 验收 / 发布
- form: review-template
- trigger: 拾起 todoList 中 taskName="stage_review" 且 operator=u_fdp_pm
```

## 2. 你的输入

读这些才能干活：

| 来源 | 必读 | 用途 |
|------|------|------|
| 前任务：stage_dev 的 `variable.decision_memo.next_handoff` | ✅ | 前节点留给你的动态信息 |
| 流程定义：[../../fdep.json](../../fdep.json) 本节点 props | ✅ | 节点结构 + assignee + artifact：评审记录 + 发布说明 |
| NODES.md 本节点 | ✅ | 读《工作步骤》与《注意事项》 |

## 3. 你的目标

```yaml
- produce: 评审记录 + 发布说明
- storage: ToT/reviews/
- form: review-template
- exit_criteria: R6 评审通过 + R3 验收签字
```

> 说明：评审 / 验收 / 发布。R6 自动评审 + R3 验收签字。

## 4. 你的 checklist

按顺序执行：

- [ ] **Step 1**：R6 自动评审：lint / 编译 / 单元测试覆盖率 / 接口契约。
- [ ] **Step 2**：R3 验收：业务正确性 / 用户体验 / 文档完整性。
- [ ] **Step 3**：编写评审记录 + 发布说明。
- [ ] **Step 4**：落档到 `ToT/reviews/<date>/<id>.md`。

> 注意事项（从 NODES.md 拉取）：
> - **R6 评审通过 + R3 验收签字** 两者都需完成（v0.6.2 暂合并为一个 task，v0.7+ 拆 fork-join）。
> - 评审不通过 → 回到 stage_dev 重做（v0.7+ 引入回退边）。
> - 验收不通过 → 回到 stage_design 重做架构。

## 5. 你的产出（execute body）

调用 `processTask/execute` 时，body 必须包含：

```json
{
  "processTaskId": "<从 todoList 拿>",
  "operator": "u_fdp_pm",
  "submitType": 1,

  "decision_reason": "评审通过：<R6 自动评审通过 + R3 验收通过>",
    "decision_memo": {
      "review_path": "ToT/reviews/<YYYY-MM-DD>/<taskId>.md",
      "r6_auto_passed": true,
      "r3_human_signed": true,
      "issues_found": "<N>"
    },
    "context": {
      "reviewer": "u_fdp_pm",
      "review_duration_hours": "<N>"
    },

  "next_handoff": {
    "next_node": "stage_feedback",
    "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_feedback.md",
    "input_files": ["ToT/reviews/<date>/<taskId>/<本节点产出>"]
  },

  "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_review.md"
}
```

> 以上是《RESPONSES.md §X.2.1 Decision Mem 模板》原始字段 + 本节点的 `next_handoff` 字段。请替换为实际值。
## 6. 你的 handoff

下一节点：**stage_feedback**

他们需要的输入：
- 你的产出（评审记录 + 发布说明）在 `ToT/reviews/`
- 他们的执行卡 → [../job_cards/job_card_stage_feedback.md](../job_cards/job_card_stage_feedback.md)

你提交 execute 后，引擎自动创建下一节点的 task。该 next_handoff 字段已在 §5 例中给出。


---

## 7. 关联文档 + SOP

| 文档 | 用途 |
|------|------|
| [../NODES.md#stage_review](../NODES.md#stage_reviewsnaker-task) | 节点的纯文本工作手册 |
| [../RESPONSES.md](../RESPONSES.md) | AI 起草响应时的模板 + Decision Mem 协议 §0 |
| [../../../sop/node-execution.md](../../../sop/node-execution.md) | 使用 Job Card 的 6 步通用 SOP（待写） |
| [../../../mapping.md](../../../mapping.md) | R 角色 ↔ SPI ↔ 用户 三层映射 |
| [../README.md §5](../README.md#5-job-card-模板-v10) | 卡片结构与命名规则 |

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 由 `gen-job-cards.py` 自动生成（基于 fdep.json + NODES.md + RESPONSES.md §X.2.1） |
