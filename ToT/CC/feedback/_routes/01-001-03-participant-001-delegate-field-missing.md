# Route: 01-engine-developer ← 03-participant-001-delegate-field-missing.md

> **From**: 03 · 2026-09-25 · 王组长 (leader1)
> **Severity**: P1
> **Tags**: bug
> **Routed at**: 2026-09-25T03:47:56.424724+00:00

## 来源反馈

**delegate 后 task 表 delegatedTo 字段未写**

我委派 task 12345 给副组长赵 (leader2)，但事后查 task 表发现 `delegatedTo` 字段还是 NULL。
后续 `delegateHistory` 也没正确写入 targetUserId。



## 行动（待 plan owner 填写）

- [ ] 接收并确认
- [ ] 排期 / 优先级
- [ ] 修复 / 加 doc
- [ ] 闭环：回写 `feedback/03-participant-001-delegate-field-missing.md` 加 `状态: 已闭环`
- [ ] release + 同步到 03-participant.md FAQ

## 状态

**状态**: open
