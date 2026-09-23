# Job Card · stage_feedback

> **节点定义**：[../../fdep.json](../../fdep.json) `nodes[id=stage_feedback]`
> **节点手册**：[../NODES.md#stage_feedback](../NODES.md#stage_feedbacksnaker-task)
> **Decision Mem 协议**：[../RESPONSES.md §0](../RESPONSES.md)
> **执行者**：`u_fdp_pm` (SPI 角色 R5)
> **角色**：R5（知识） / `fdep_kb` / u_fdp_pm（R3 反馈收集待 fork-join）
> **触发**：stage_review 完成后 → 引擎自动加入 todoList（operator=u_fdp_pm）

---

## 1. 你的身份

```yaml
- node: stage_feedback
- type: snaker:task
- assignee: u_fdp_pm
- spi_role: R5
- stage: 5. 反馈 / 知识沉淀
- form: kb-template
- trigger: 拾起 todoList 中 taskName="stage_feedback" 且 operator=u_fdp_pm
```

## 2. 你的输入

读这些才能干活：

| 来源 | 必读 | 用途 |
|------|------|------|
| 前任务：stage_review 的 `variable.decision_memo.next_handoff` | ✅ | 前节点留给你的动态信息 |
| 流程定义：[../../fdep.json](../../fdep.json) 本节点 props | ✅ | 节点结构 + assignee + artifact：Issue 追踪记录 + 知识库条目 |
| NODES.md 本节点 | ✅ | 读《工作步骤》与《注意事项》 |

## 3. 你的目标

```yaml
- produce: Issue 追踪记录 + 知识库条目
- storage: ToT/issues/ + ToT/kb/
- form: kb-template
- exit_criteria: 每条反馈关联到 Task 或 Issue；无孤立文档
```

> 说明：反馈 / 知识沉淀。R3 收集反馈 + R5 入库知识。

## 4. 你的 checklist

按顺序执行：

- [ ] **Step 1**：收集用户/Agent 反馈（issues/ 反馈渠道）。
- [ ] **Step 2**：R5 把有价值的反馈入库到知识库。
- [ ] **Step 3**：每条反馈关联到 Task 或 Issue（不允许孤立文档）。
- [ ] **Step 4**：落档到 `ToT/issues/<date>/<id>.md` + `ToT/kb/<topic>.md`。

> 注意事项（从 NODES.md 拉取）：
> - **每条反馈必须关联到 Task 或 Issue**（无孤立文档是 R5 的硬约束）。
> - 反馈内容必须可执行（具体问题 / 复现步骤 / 期望行为）。
> - 知识库条目必须是经过提炼的通用知识，不是原始聊天记录。

## 5. 你的产出（execute body）

调用 `processTask/execute` 时，body 必须包含：

```json
{
  "processTaskId": "<从 todoList 拿>",
  "operator": "u_fdp_pm",
  "submitType": 1,

  "decision_reason": "反馈沉淀完成：<每条反馈关联 Task/Issue，知识库条目落档>",
    "decision_memo": {
      "issues_path": "ToT/issues/<YYYY-MM-DD>/<taskId>.md",
      "kb_entries": ["ToT/kb/<taskId>.md"],
      "feedback_count": "<N>"
    },
    "context": {
      "knowledge_admin": "u_fdp_pm",
      "knowledge_owner": "R5"
    },

  "next_handoff": {
    "next_node": "end",
    "is_terminal": true
  },

  "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_feedback.md"
}
```

> 以上是《RESPONSES.md §X.2.1 Decision Mem 模板》原始字段 + 本节点的 `next_handoff` 字段。请替换为实际值。
## 6. 你的 handoff

下一节点：**end**

他们是终点节点（end），无需 handoff 体。


---

## 7. 关联文档 + SOP

| 文档 | 用途 |
|------|------|
| [../NODES.md#stage_feedback](../NODES.md#stage_feedbacksnaker-task) | 节点的纯文本工作手册 |
| [../RESPONSES.md](../RESPONSES.md) | AI 起草响应时的模板 + Decision Mem 协议 §0 |
| [../../../sop/node-execution.md](../../../sop/node-execution.md) | 使用 Job Card 的 6 步通用 SOP（待写） |
| [../../../mapping.md](../../../mapping.md) | R 角色 ↔ SPI ↔ 用户 三层映射 |
| [../README.md §5](../README.md#5-job-card-模板-v10) | 卡片结构与命名规则 |

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 由 `gen-job-cards.py` 自动生成（基于 fdep.json + NODES.md + RESPONSES.md §X.2.1） |
