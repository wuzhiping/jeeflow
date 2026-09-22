# Job Card · stage_intake

> **节点定义**：[../../fdep.json](../../fdep.json) `nodes[id=stage_intake]`
> **节点手册**：[../NODES.md#stage_intake](../NODES.md#stage_intakesnaker-task)
> **Decision Mem 协议**：[../RESPONSES.md §0](../RESPONSES.md)
> **执行者**：`u_fdp_pm` (SPI 角色 R3)
> **角色**：R3 / `fdep_intake` / u_fdp_pm
> **触发**：start 完成后 → 引擎自动加入 todoList（operator=u_fdp_pm）

---

## 1. 你的身份

```yaml
- node: stage_intake
- type: snaker:task
- assignee: u_fdp_pm
- spi_role: R3
- stage: 0. PM 接收窗口（登记）
- form: intake-template
- trigger: 拾起 todoList 中 taskName="stage_intake" 且 operator=u_fdp_pm
```

## 2. 你的输入

读这些才能干活：

| 来源 | 必读 | 用途 |
|------|------|------|
| 前任务：start | ✅ | 切入点信息 |
| 流程定义：[../../fdep.json](../../fdep.json) 本节点 props | ✅ | 节点结构 + assignee + artifact：原始请求登记记录 |
| NODES.md 本节点 | ✅ | 读《工作步骤》与《注意事项》 |

## 3. 你的目标

```yaml
- produce: 原始请求登记记录
- storage: ToT/pm/intake/
- form: intake-template
- exit_criteria: 登记完成 + 决定（立项 submitType=1 / 驳回 submitType=2）
```

> 说明：PM 接收窗口（登记原始请求，决定立项或驳回）。

## 4. 你的 checklist

按顺序执行：

- [ ] **Step 1**：读取请求内容。
- [ ] **Step 2**：评估：是否在本系统范围？是否重复请求？是否优先级合理？
- [ ] **Step 3**：决定：
- [ ] **Step 4**：登记原始请求到 `ToT/pm/intake/<date>/<id>.md`。

> 注意事项（从 NODES.md 拉取）：
> - 决策结果必须显式记录（立项/驳回 + 理由）。
> - 驳回必须写理由（归档到 `ToT/pm/intake/rejected/`）。
> - 不要直接进入"接收 + 立项"两件事，decision_intake 节点负责分流。

## 5. 你的产出（execute body）

调用 `processTask/execute` 时，body 必须包含：

```json
{
  "processTaskId": "<从 todoList 拿>",
  "operator": "u_fdp_pm",
  "submitType": 1,
  "decision_reason": "<本节点决策理由>",
  "decision_memo": {},
  "context": {},

  "job_card_url": "ToT/flows/fdep/job_cards/job_card_stage_intake.md"
}
```

## 6. 你的 handoff

下一节点：**decision_intake**

他们是终点节点（decision_intake），无需 handoff 体。


---

## 7. 关联文档 + SOP

| 文档 | 用途 |
|------|------|
| [../NODES.md#stage_intake](../NODES.md#stage_intakesnaker-task) | 节点的纯文本工作手册 |
| [../RESPONSES.md](../RESPONSES.md) | AI 起草响应时的模板 + Decision Mem 协议 §0 |
| [../../../sop/node-execution.md](../../../sop/node-execution.md) | 使用 Job Card 的 6 步通用 SOP（待写） |
| [../../../mapping.md](../../../mapping.md) | R 角色 ↔ SPI ↔ 用户 三层映射 |
| [../README.md §5](../README.md#5-job-card-模板-v10) | 卡片结构与命名规则 |

---

## 8. 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-09-22 | 由 `gen-job-cards.py` 自动生成（基于 fdep.json + NODES.md + RESPONSES.md §X.2.1） |
