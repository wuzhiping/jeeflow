# Initiate Guide · fdep

> **目的**：拿到 fdep 流程怎么发起、何时发起、发起后预期路径
> **适用**：发起 fdep 前的"总览"

---

## 1. 何时发起

- **触发场景**：任何新需求 / 请求（人类 / AI Agent / 外部用户均可）
- **可发起者**：无角色限制（start ≠ R3，PM 是后续接收窗口 stage_intake）
- **发起动作**：`POST /wf/processDefine/startAndExecute`

## 2. 必填参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `processDefineId` | int | ✅ | 数字 ID（不是 processDefineName） |
| `operator` | str | ✅ | 发起人 uid（u_fdp_pm / 其他 SPI uid） |
| `businessNo` | str | ⛔ | 业务单号（建议填，便于审计） |
| `variables` | dict | ⛔ | 业务变量（顶层透传） |

## 3. 发起后预期路径

- **首 task**：`stage_intake`（PM 接收窗口，节点 ID：`stage_intake`）
- **后续流转**：stage_intake → decision_intake → stage_pm → stage_design → stage_dev → stage_review → stage_feedback → end
- **驳回分支**：decision_intake → end_rejected
- **终态**：`end`（协作闭环）/`end_rejected`（驳回闭环）

## 4. 注意事项

- ✅ 无角色限制（任何来源都能触发 start）
- ❌ start 不等于 R3（PM 是 stage_intake 的角色，不是入口）
- ✅ 一旦 stage_intake 被激活，引擎自动流转
- ⚠ 发起前确认 fdep 流程已 deploy 且 active（用 `processDesign/listByType` 看 active 列表）
- 💡 发起后建议立即读首 task 的 Job Card：`ToT/flows/fdep/job_cards/job_card_stage_intake.md`