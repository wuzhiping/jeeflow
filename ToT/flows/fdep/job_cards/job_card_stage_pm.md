# Job Card · stage_pm

> **节点定义**：[../../fdep.json](../../fdep.json) `nodes[id=stage_pm]`
> **节点手册**：[../NODES.md#stage_pm](../NODES.md#stage_pmsnaker-task)
> **Decision Mem 协议**：[../RESPONSES.md §0](../RESPONSES.md)
> **执行者**：`u_fdp_pm`
> **角色**：R3 / `fdep_rml` / u_fdp_pm
> **触发**：decision_intake 完成后 → 引擎自动加入 todoList（operator=u_fdp_pm）

---

## 1. 你的身份

```yaml
- node: stage_pm
- type: snaker:task
- assignee: u_fdp_pm
- stage: 1. RML 立项
- form: rml-template
- trigger: 拾起 todoList 中 taskName="stage_pm" 且 operator=u_fdp_pm
```

## 2. 你的输入

读这些才能干活：

| 来源 | 必读 | 用途 |
|------|------|------|
| 前任务：decision_intake | ✅ | 切入点信息 |
| 流程定义：[../../fdep.json](../../fdep.json) 本节点 props | ✅ | 节点结构 + assignee + artifact：RML 文档 |
| NODES.md 本节点 | ✅ | 读《工作步骤》与《注意事项》 |

## 3. 你的目标

```yaml
- produce: RML 文档
- storage: ToT/pm/rml/
- form: rml-template
- exit_criteria: RML 通过 R3 自审并指派下一阶段
```

> 说明：RML 立项。PM 编写 RML（Requirements Markup Language）文档。

## 4. 你的 checklist

按顺序执行：

- [ ] **Step 1**：阅读 stage_intake 登记的请求。
- [ ] **Step 2**：编写 RML：背景 / 目标 / 用户故事 / 验收标准 / 范围。
- [ ] **Step 3**：RML 自审通过。
- [ ] **Step 4**：落档到 `ToT/pm/rml/<date>/<id>.md`。
- [ ] **Step 5**：指派下一阶段（架构师）。

> 注意事项（从 NODES.md 拉取）：
> - RML 必须可独立阅读（包含完整上下文）。
> - RML 通过后才推 stage_design，不要"未完成即推"。

## 5. 你的产出（execute body）

调用 `processTask/execute` 时，body 必须包含：

```json
{
  "processTaskId": "<从 todoList 拿>",
  "operator": "u_fdp_pm",
  "submitType": 1,

  "decision_reason": "RML 完整：<背景/目标/用户故事/AC/范围 5 段齐全>",
    "decision_memo": {
      "rml_path": "ToT/pm/rml/<YYYY-MM-DD>/<taskId>.md",
      "rml_length_lines": "<N>",
      "key_requirements": ["req1", "req2"]
    },
    "context": {
      "rml_drafted_by": "AI | human",
      "draft_duration_min": "<N>"
    },

  "next_handoff": {
    "next_node": "stage_design",
    "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_design.md",
    "input_files": ["ToT/pm/rml/<date>/<taskId>/<本节点产出>"]
  },

  "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_pm.md"
}
```

> 以上是《RESPONSES.md §X.2.1 Decision Mem 模板》原始字段 + 本节点的 `next_handoff` 字段。请替换为实际值。
## 6. 你的 handoff

下一节点：**stage_design**

他们需要的输入：
- 你的产出（RML 文档）在 `ToT/pm/rml/`
- 他们的执行卡 → [../job_cards/job_card_stage_design.md](../job_cards/job_card_stage_design.md)

你提交 execute 后，引擎自动创建下一节点的 task。该 next_handoff 字段已在 §5 例中给出。


---

## 7. 关联文档 + SOP

| 文档 | 用途 |
|------|------|
| [../NODES.md#stage_pm](../NODES.md#stage_pmsnaker-task) | 节点的纯文本工作手册 |
| [../RESPONSES.md](../RESPONSES.md) | AI 起草响应时的模板 + Decision Mem 协议 §0 |
| [../../../sop/node-execution.md](../../../sop/node-execution.md) | 使用 Job Card 的 6 步通用 SOP（待写） |
| [../../../mapping.md](../../../mapping.md) | R 角色 ↔ SPI ↔ 用户 三层映射 |
| [../README.md §5](../README.md#5-job-card-模板-v10) | 卡片结构与命名规则 |

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 由 `gen-job-cards.py` 自动生成（基于 fdep.json + NODES.md + RESPONSES.md §X.2.1） |
