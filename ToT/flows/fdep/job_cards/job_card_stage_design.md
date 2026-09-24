# Job Card · stage_design

> **节点定义**：[../../fdep.json](../../fdep.json) `nodes[id=stage_design]`
> **节点手册**：[../NODES.md#stage_design](../NODES.md#stage_designsnaker-task)
> **Decision Mem 协议**：[../RESPONSES.md §0](../RESPONSES.md)
> **执行者**：`u_fdp_pm`
> **角色**：R7 / `fdep_arch` / u_fdp_pm
> **触发**：stage_pm 完成后 → 引擎自动加入 todoList（operator=u_fdp_pm）

---

## 1. 你的身份

```yaml
- node: stage_design
- type: snaker:task
- assignee: u_fdp_pm
- stage: 2. 架构 / 接口设计
- form: arch-template
- trigger: 拾起 todoList 中 taskName="stage_design" 且 operator=u_fdp_pm
```

## 2. 你的输入

读这些才能干活：

| 来源 | 必读 | 用途 |
|------|------|------|
| 前任务：stage_pm 的 `variable.decision_memo.next_handoff` | ✅ | 前节点留给你的动态信息 |
| 流程定义：[../../fdep.json](../../fdep.json) 本节点 props | ✅ | 节点结构 + assignee + artifact：架构文档 + 接口设计 + Mock 数据 |
| NODES.md 本节点 | ✅ | 读《工作步骤》与《注意事项》 |

## 3. 你的目标

```yaml
- produce: 架构文档 + 接口设计 + Mock 数据
- storage: ToT/design/
- form: arch-template
- exit_criteria: 接口编号连续、Mock 数据覆盖正常/异常场景
```

> 说明：架构 / 接口设计。架构师输出架构文档 + 接口设计 + Mock 数据。

## 4. 你的 checklist

按顺序执行：

- [ ] **Step 1**：阅读 RML。
- [ ] **Step 2**：编写架构文档（模块划分、数据流、关键决策）。
- [ ] **Step 3**：接口设计：URL / method / request / response / 状态码。
- [ ] **Step 4**：**接口编号必须连续**（API 接口规范 §8 要求）。
- [ ] **Step 5**：Mock 数据：覆盖正常响应 + 异常场景。
- [ ] **Step 6**：落档到 `ToT/design/<date>/<id>.md`。

> 注意事项（从 NODES.md 拉取）：
> - 接口编号从 1 起递增、不可跳号、不可重复。
> - Mock 数据必须有正常 + 异常两种。
> - 不要直接进入开发（必须 R6 评审通过）。

## 5. 你的产出（execute body）

调用 `processTask/execute` 时，body 必须包含：

```json
{
  "processTaskId": "<从 todoList 拿>",
  "operator": "u_fdp_pm",
  "submitType": 1,

  "decision_reason": "架构清晰：<模块划分清晰，接口编号连续，关键决策有理由>",
    "decision_memo": {
      "arch_path": "ToT/design/<YYYY-MM-DD>/<taskId>.md",
      "api_count": "<N>",
      "key_decisions": ["decision1", "decision2"]
    },
    "context": {
      "architect": "AI | human",
      "design_duration_hours": "<N>"
    },

  "next_handoff": {
    "next_node": "stage_dev",
    "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_dev.md",
    "input_files": ["ToT/design/<date>/<taskId>/<本节点产出>"]
  },

  "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_design.md"
}
```

> 以上是《RESPONSES.md §X.2.1 Decision Mem 模板》原始字段 + 本节点的 `next_handoff` 字段。请替换为实际值。
## 6. 你的 handoff

下一节点：**stage_dev**

他们需要的输入：
- 你的产出（架构文档 + 接口设计 + Mock 数据）在 `ToT/design/`
- 他们的执行卡 → [../job_cards/job_card_stage_dev.md](../job_cards/job_card_stage_dev.md)

你提交 execute 后，引擎自动创建下一节点的 task。该 next_handoff 字段已在 §5 例中给出。


---

## 7. 关联文档 + SOP

| 文档 | 用途 |
|------|------|
| [../NODES.md#stage_design](../NODES.md#stage_designsnaker-task) | 节点的纯文本工作手册 |
| [../RESPONSES.md](../RESPONSES.md) | AI 起草响应时的模板 + Decision Mem 协议 §0 |
| [../../../sop/node-execution.md](../../../sop/node-execution.md) | 使用 Job Card 的 6 步通用 SOP（待写） |
| [../../../mapping.md](../../../mapping.md) | R 角色 ↔ SPI ↔ 用户 三层映射 |
| [../README.md §5](../README.md#5-job-card-模板-v10) | 卡片结构与命名规则 |

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 由 `gen-job-cards.py` 自动生成（基于 fdep.json + NODES.md + RESPONSES.md §X.2.1） |
