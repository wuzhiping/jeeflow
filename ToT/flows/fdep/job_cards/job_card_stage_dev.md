# Job Card · stage_dev

> **节点定义**：[../../fdep.json](../../fdep.json) `nodes[id=stage_dev]`
> **节点手册**：[../NODES.md#stage_dev](../NODES.md#stage_devsnaker-task)
> **Decision Mem 协议**：[../RESPONSES.md §0](../RESPONSES.md)
> **执行者**：`u_fdp_pm` (SPI 角色 R2)
> **角色**：R2 / `fdep_dev` / u_fdp_pm
> **触发**：stage_design 完成后 → 引擎自动加入 todoList（operator=u_fdp_pm）

---

## 1. 你的身份

```yaml
- node: stage_dev
- type: snaker:task
- assignee: u_fdp_pm
- spi_role: R2
- stage: 3. 开发实现
- form: code-template
- trigger: 拾起 todoList 中 taskName="stage_dev" 且 operator=u_fdp_pm
```

## 2. 你的输入

读这些才能干活：

| 来源 | 必读 | 用途 |
|------|------|------|
| 前任务：stage_design 的 `variable.decision_memo.next_handoff` | ✅ | 前节点留给你的动态信息 |
| 流程定义：[../../fdep.json](../../fdep.json) 本节点 props | ✅ | 节点结构 + assignee + artifact：源代码 + 单元测试 |
| NODES.md 本节点 | ✅ | 读《工作步骤》与《注意事项》 |

## 3. 你的目标

```yaml
- produce: 源代码 + 单元测试
- storage: ToT/src/ + ToT/tdd/
- form: code-template
- exit_criteria: 通过 R6 自动评审 + 自测通过
```

> 说明：开发实现。开发者 Agent 输出源代码 + 单元测试。

## 4. 你的 checklist

按顺序执行：

- [ ] **Step 1**：阅读架构文档 + 接口设计 + Mock 数据。
- [ ] **Step 2**：实现源代码（按接口规范）。
- [ ] **Step 3**：编写单元测试（覆盖正常 + 异常 + 边界）。
- [ ] **Step 4**：本地自测通过。
- [ ] **Step 5**：落档到 `ToT/src/<module>/` + `ToT/tdd/test_<module>.py`。

> 注意事项（从 NODES.md 拉取）：
> - **不修改 ToT/ 外的文件**（§1 边界规则），即使是"看起来无关"的修正。
> - 不擅自变更架构（需要回 stage_design）。
> - 单元测试覆盖率 ≥ 80%（项目基线）。

## 5. 你的产出（execute body）

调用 `processTask/execute` 时，body 必须包含：

```json
{
  "processTaskId": "<从 todoList 拿>",
  "operator": "u_fdp_pm",
  "submitType": 1,

  "decision_reason": "代码 + 单测完成：<覆盖率 ≥80%，lint 通过，编译通过>",
    "decision_memo": {
      "commit_hash": "<git sha>",
      "src_path": "ToT/src/<module>/",
      "test_path": "ToT/tdd/test_<module>.py",
      "test_coverage_pct": "<N>"
    },
    "context": {
      "developer": "AI | human",
      "lines_changed": "<N>"
    },

  "next_handoff": {
    "next_node": "stage_review",
    "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_review.md",
    "input_files": ["ToT/src/ + ToT/tdd/<date>/<taskId>/<本节点产出>"]
  },

  "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_dev.md"
}
```

> 以上是《RESPONSES.md §X.2.1 Decision Mem 模板》原始字段 + 本节点的 `next_handoff` 字段。请替换为实际值。
## 6. 你的 handoff

下一节点：**stage_review**

他们需要的输入：
- 你的产出（源代码 + 单元测试）在 `ToT/src/ + ToT/tdd/`
- 他们的执行卡 → [../job_cards/job_card_stage_review.md](../job_cards/job_card_stage_review.md)

你提交 execute 后，引擎自动创建下一节点的 task。该 next_handoff 字段已在 §5 例中给出。


---

## 7. 关联文档 + SOP

| 文档 | 用途 |
|------|------|
| [../NODES.md#stage_dev](../NODES.md#stage_devsnaker-task) | 节点的纯文本工作手册 |
| [../RESPONSES.md](../RESPONSES.md) | AI 起草响应时的模板 + Decision Mem 协议 §0 |
| [../../../sop/node-execution.md](../../../sop/node-execution.md) | 使用 Job Card 的 6 步通用 SOP（待写） |
| [../../../mapping.md](../../../mapping.md) | R 角色 ↔ SPI ↔ 用户 三层映射 |
| [../README.md §5](../README.md#5-job-card-模板-v10) | 卡片结构与命名规则 |

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 由 `gen-job-cards.py` 自动生成（基于 fdep.json + NODES.md + RESPONSES.md §X.2.1） |
